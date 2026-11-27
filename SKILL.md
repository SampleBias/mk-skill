---
name: mk-lang
description: Write, build, test, and debug programs in the Mk systems programming language from zerodayokay/Mk-Lang. Use for Mk source, pkg.mk packages, the Mk standard library, ownership and flow diagnostics, or reducing a suspected Mk compiler regression.
---

# Programming in Mk

Start with the project's `pkg.mk`, nearby `.mk` files, and `mk version`. The latter should identify the Mk compiler and its LLVM tools. Follow the project's declared minimum and check unfamiliar calls against the compiler that will build the program. This skill covers Mk 0.7.1 at [upstream commit 7d05aef](https://github.com/zerodayokay/Mk-Lang/tree/7d05aef3821b5f1349fbb18b136ea18ade445810).

## Start a program

A standalone `main.mk` can be as small as this argument-counting CLI. The format record supplies the value for the named hole.

```mk
export Main(sys: &System): WriteError!void {
    try sys.Print("{count} arguments\n", (count: sys.args.Len() - 1))
}
```

Run `mk run main.mk -- red green` and expect `2 arguments`. For a multi-file application, `mk new NAME` creates the manifest and bin root. Open the [complete linepick package](assets/linepick/pkg.mk) for a working boundary between a [CLI with file I/O](assets/linepick/src/main.mk) and a [search module with tests](assets/linepick/src/search/search.mk). It uses only the embedded standard library and runs on Mk 0.6.0 and 0.7.1. To exercise it with a particular compiler, run `python3 scripts/check-example.py --mk /path/to/mk` from this skill's directory.

## Work from compiler evidence

1. Give each function the capabilities it needs. A parser can take `str`, a collector can take `&Arena`, and a file operation takes `Io`. Decide which input backs each returned view and which failures the caller should handle.
2. Look up an unfamiliar operation before writing around it. From the package root, use `mk query find append`, `mk query members List`, `mk query import ReadText`, or `mk doc std.fs`. Read the signature for the receiver, allocator, error set and result sources.
3. Run `mk check` after connecting modules. For a diagnostic, use `mk explain CODE` and follow the reported source location and facts. Keep a regression case when a real input exposes a defect.
4. Format the edited Mk source with `mk fmt`. Run the relevant `mk test` blocks, build the actual bin, then exercise it with representative input and an expected failure. Check output and exit status. Use the requested profile and target when validating a deliverable.

## References

- [Language and data](references/language.md) covers bindings, data types, functions, generics, branching, optionals, errors and tests.
- [Ownership, allocation and I/O](references/ownership-io.md) covers moves, result and storage flows, fallible cleanup, files and structured tasks.
- [Packages and native builds](references/projects.md) covers obtaining a compiler, modules, dependency resolution, profiles, library discovery and running a full application.
- [Diagnostics and regression testing](references/debugging.md) covers diagnostic roots, fixing borrow errors, reducing a failing package and finding the corresponding upstream tests.
