# Ownership, allocation and I/O

## Read a signature as a resource contract

| Form | What to account for at the call site |
| --- | --- |
| `T` by value | A plain value copies. A unique value moves and may be dropped unused. A linear value moves and must be consumed exactly once on every path. Struct fields can make the containing type unique or linear. Ask `mk query kind T` when uncertain. |
| `&T` and `mut T` | Pass `&x` for shared access and `mut x` for exclusive access. `var x` permits the latter. Bare `var` in a by-value parameter permits local reassignment. `mut` in a reference parameter lets the callee change the caller's value. |
| `T from a, input` | A returned value may keep loans from these sources. Their storage must outlive the last use of every holder, including copies of a view. The compiler can infer a single unambiguous source. |
| `input: str into a` | The callee may retain a view of the argument in storage associated with `a`. This permission matters even if the call returns `void`. If the callee copies all bytes into fresh storage, describe the copy's actual source instead. |
| `defer release` / `onerr release` | `defer` runs when leaving its block, in reverse registration order. `onerr` runs on error exits. An ordinary `return` of a status integer takes the success path, even if that integer is nonzero. |

Read the [search function](../assets/linepick/src/search/search.mk). Its growable list needs the arena, and each stored line is a slice of `input`. Those facts explain both `from a, input` and `input: str into a`. The pattern participates in the comparison only, so the caller can stop retaining the pattern once the call returns.

A fallible call consumes a non-plain by-value argument on success. On failure the caller still owns it. In a function that accepts such an argument, do the work that can fail before the final transfer. This allows a caller to clean up on either edge.

## Choose storage with the required lifetime

- A short-lived CLI can read text into `sys.arena`. For repeated requests or batches, use a local `var scratch := try Arena.New(sys.heap)` or a sub-arena from `try parent.Sub()`. Place `defer scratch.Free()` in the request's block. Release or reset an arena only after the last use of its borrowed data.
- To return independently stored text, accept the destination arena from the caller and use `try dest.Dup(text)` or `try dest.Fmt(...)`. The returned owned bytes live in that arena and the `str` is a view of them. Returning a slice of a local array or a local scratch arena would leave a dangling view.
- For an independently owned collection, take an allocator from `sys.heap.Alloc()`. For example, `HeapList[int].New(alloc)` gives a linear owner. Growth takes the allocator (`try list.Push(alloc, x)`), and the eventual owner calls `list.Free(alloc)`. A function constructing and returning the list can register `onerr list.Free(alloc)` while building it.
- Storing a linear resource such as an open file in an arena `List` or with `Arena.Put` is E0701. Use a `HeapList` for owned handles. Drain and release them before calling `FreeEmpty`, or supply a release callback to `FreeEach`. A generic helper that copies elements into an arena list can require `T: Plain`.
- A mutable borrow includes accesses through holders such as list element views and references returned by map lookups. Copy a needed number before growing or mutating its container. Distinct fields can be borrowed separately. For two mutable elements in one slice, obtain disjoint references with `GetPair` or split the slice using its `SplitAt` method.

## Handle I/O and release on both paths

Take `Io` in functions that open files, read, write or wait. `fs.ReadText(a, io, path)` reads and validates a whole UTF-8 file, returns a view from the arena, and can fail with `fs.Error|OutOfMemory`. Use `ReadBytes` for binary input. For large inputs, use a fixed buffer with `File.Read` and process `buf[..n]` until the count is zero. To read lines use `file.Reader(io, mut buf[..])` and `for line := try reader.Line(a)`. Pick an arena lifetime appropriate for each returned line.

This function writes a complete report. A failed write or close reaches the caller, and the error path releases the file. `Close` on a Mk file consumes it on success. Its failure leaves the handle available to `Abandon`.

```mk
import std.fs

WriteReport(io: Io, path: str, lines: []str): fs.Error!void {
    var file := try fs.Create(io, path)
    onerr file.Abandon()
    for line in lines {
        try file.WriteAll(io, line.AsBytes())
        try file.WriteAll(io, b"\n")
    }
    try file.Close(io)
}
```

Use `WriteAll` when the caller requires every byte to be sent. A single low-level write may be partial. For disk durability, the file API also exposes fallible `Sync(io)`. A caller that needs atomic replacement must also account for its commit protocol. For terminal output, `sys.Print` and `sys.PrintErr` return `WriteError!void`. A component that should work with a different output destination can accept a `mut Writer`.

## Structured tasks

Use `scope group := io.Scope()` and `group.go F(args)`. The scope joins its children before exit. Pass shareable reads or distinct writable results, then read the results after the join. This test uses two independent counters.

```mk
CountMarks(text: str, count: mut int) {
    for c in text.Scalars() {
        if c == '#' {
            *count += 1
        }
    }
}

test "counts from two joined tasks" (sys: &System) {
    var left := 0
    var right := 0
    scope group := sys.io.Scope() {
        group.go CountMarks("##a", mut left)
        group.go CountMarks("b#c", mut right)
    }
    Assert(left == 2 && right == 1)
}
```

For tasks returning `E!void`, use `try scope group := io.ScopeOf[E]() { ... }` when one failure should cancel siblings and propagate. To report independent failures, give each task a separate parent-owned `?E`, initially `none`. Handle the fallible call inside a `void` task with `else e { *failed = some(e) }` and read the slots after the join.

For field-specific flows, linear containers, and more complex tasks, consult the upstream [memory rules](https://github.com/zerodayokay/Mk-Lang/blob/7d05aef3821b5f1349fbb18b136ea18ade445810/doc/memory.md) and [worked I/O and task recipes](https://github.com/zerodayokay/Mk-Lang/blob/7d05aef3821b5f1349fbb18b136ea18ade445810/doc/cookbook.md).
