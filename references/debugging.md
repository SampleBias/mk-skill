# Diagnosing and stabilizing Mk programs

## Find the first failing stage

Run the command that failed, from the same package or workspace root, with the same compiler, target, profile and input. Preserve its status and stderr. For source diagnostics use `mk check --json`. It emits one document on stdout. The `root` field is the one-based index of the diagnostic causing this one. Start with that cause and recheck. The compiler reports diagnostics from the earliest failing phase, so the next phase can uncover another issue. Some queries need a checked body. If a query reports a partial answer, the diagnostic document still gives the facts for the failing expression.

| Observation | Next check |
| --- | --- |
| Parser rejects code that looks familiar | Read `mk explain CODE`. Common translations are `var n := 0`, `mut x`, `for condition`, explicit `return` and `try call()`. Compare the spelling with an accepted Mk unit. |
| A name, module or method cannot be resolved | Check the file's imports, directory-relative module path, receiver type and visibility. Try `mk query find WORD`, `mk query import NAME`, or `mk query members TYPE`. A package loader E0202 includes a `reason` such as `not-found` or `sum-missing`. |
| A `try` yields E0801 | Inspect the callee's error set with `mk query sig NAME`. Either handle the relevant failure locally or include it in the caller's contract. E0802 means a result was dropped without handling its error. |
| Mk reports E0401 or E0402 | Mark the move or acquisition and follow both the success and error edges. E0401 indicates use after move. E0402 identifies a linear value still owned on some path. Look at cleanup, ownership transfer and early returns. |
| Mk reports E0501–E0505 or E0601–E0604 | Read the loan's place, holder, last use and callee signature. Query `mk query flows NAME` or `mk query why-live NAME LINE` where available. End the holder's use earlier, copy a small value, move ownership outward, or state the actual result/storage relationship. |
| Source checks but native build fails | With E0001, inspect the failing clang/lld invocation, its stderr, target, output path and `mk version`. Compare with a same-target hello program. Check the package's native libraries/objects if only this bin fails. |
| Build succeeds but exit, bytes, or state differ | Run the built executable directly and capture stdout, stderr and status separately. Compare dev, `--profile checked` and `--release` on exactly the same input. For a stateful failure, record the starting files or simulation seed. |
| E0000 or a compiler crash | Preserve the smallest input that triggers it and the toolchain identifiers. A normal rejection should yield a source diagnostic. Keep the compiler failure distinct from a panic in a program that successfully built. |

`mk fix --dry-run` previews the compiler's proven edits. Review their effect on the program, especially its error handling and public APIs. A suggested edit classified as `compiles` or `alternatives` still leaves a design choice to the author.

## Work a borrow diagnostic backwards

Save this deliberately rejected unit as `pair.mk` and run `mk check --json pair.mk`.

```mk
Change(): int {
    var pair := [4, 8]
    first := &pair[0]
    pair[1] = 12
    return *first + pair[1]
}
```

On the baseline compiler, the assignment conflicts with the shared loan and produces E0502. Mk treats indexed elements of the array as one place for this check. `first` keeps the loan live through the later dereference. The function only needs the old integer. Change the binding to `first := pair[0]` and the return to `return first + pair[1]`. The copied integer can outlive the write. Add `test "preserves first" { Assert(Change() == 16) }` and run `mk test pair.mk`. If the algorithm actually needs two independently writable elements, use the slice API for disjoint elements.

## Reduce a suspected compiler or library issue

1. Freeze an observable case. Keep the exact source, small input, commands, expected and actual results, `mk version`, and any deliberate `MK_STD` override. For a source-built compiler record the Git revision. For a failing test save its name and, if relevant, the simulation seed.
2. Work on a copy. Reduce to one `.mk` file if the failure persists there. Retain `pkg.mk`, a second module, a dependency, or the bin profile when removing it changes the failure. Keep the same diagnostic code and source construct, or the same wrong runtime result, after each reduction.
3. Change one variable. Try `--no-cache` on the failing compile command for a cache-sensitive case. Compare a known-working compiler and the candidate on the same input. For regression comparisons each compiler should use its own bundled standard library unless the std override is the variable under test. `mk test --run SUBSTRING` narrows a test run and `mk test --sim 42` can reproduce a recorded seed of 42 in simulated I/O.
4. Keep an executable witness. For application behavior, assert the actual value in an Mk test or capture the real bin's output, error and status. For an upstream rejection, compare the expected diagnostic code. Re-run the witness after the fix and also exercise the original program with its normal entry point.

When working on Mk itself, `internal/syntax` handles parsing, `internal/check` handles types, `internal/borrow` handles moves and loans, and `internal/codegen` and `internal/llvm` handle native lowering and emission. Consult `std/<module>` for a library behavior difference. From the compiler checkout, select the nearest existing regression harness:

| Change | Focused evidence |
| --- | --- |
| Borrow checker rule | `go test ./internal/borrow` and the matching accept/reject unit under `tests/conformance`. Check a single existing unit with `go run ./cmd/mk corpus --all --only 'tests/conformance/codes/E0502.mk'`. |
| Documented language behavior | `go run ./cmd/mk corpus --only 'doc/memory.md:*'` judges that document's examples according to their verdicts. Some upstream examples intentionally reject or exercise parsing only. |
| Runtime or std result | Use a neighboring `tests/programs` input/output fixture or a focused test in `std`. `mk test --std std.fs` runs Mk test blocks for the filesystem module. Preserve both the observed failure and a normal case. |

Keep upstream edits in scope for compiler or library work. For an application task, a compatible workaround, a regression test and a minimal local reproducer can be sufficient. Upstream's [diagnostic catalog](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/doc/errors.md), [command reference](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/doc/tools.md), and [contributor guide](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/CONTRIBUTING.md) describe the matching tests and tools.
