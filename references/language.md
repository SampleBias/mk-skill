# Writing Mk source

## Declarations and types

| Intent | Mk spelling and behavior |
| --- | --- |
| Declare a function | `Twice(n: int): int { return n * 2 }`. Omit the result for `void`. A value-returning function needs an explicit return on each reachable path. Ordinary call arguments are positional. |
| Bind a local | `limit := 10` is fixed. Use `var total := 0` to reassign or borrow the local for writing. `limit: i32 = 10` gives a type. A declared local needs an assignment on every path to its first read. |
| Name declarations | Use PascalCase for functions, types, constants and methods. Use snake_case for fields, locals and parameters. Shadowing and unused locals/imports produce diagnostics. Write `_ = expr` to discard an ordinary value. A fallible expression still needs error handling. |
| Carry structured data | Construct a struct by naming all fields, e.g. `Hit(number: 1, line: "ok")`. Prefix a declaration and each externally visible field or method with `export`. A record such as `(total: 4, used: 2)` can also serve as a function result. |
| Define a method | Write `Counter.Add(mut self, n: int) { self.total += n }` in the type's module. `&self` reads, `mut self` writes, and `self` takes a value. A call such as `counter.Add(1)` borrows the receiver automatically. |
| Choose a number type | `int` is pointer-sized and is used for indexes and lengths. `u8` is a byte. Integer overflow is checked in release too. `*%`, `+%` and `-%` request wrapping. Use `T(x)` for a lossless conversion, `Cast[T](x)` for a checked conversion, and `Trunc[T](x)` when discarding high bits is intended. |
| Access text | `str` is a shared UTF-8 view. `s.Len()` and slice offsets count bytes. `s.Byte(i)` reads a byte. Use `s.Scalars()` for Unicode scalar values. Slice text at UTF-8 boundaries. `'a'` is a `char`, `b'a'` a `u8`, and `b"abc"` a byte slice. |
| Format output | `try sys.Print("{used}/{max}\n", (used: count, max: limit))`. A hole names a field of the record passed to the formatter. For literal output pass only the string. Use `PrintErr` for stderr. |

A newline ends a statement when the grammar permits. Use braces for control flow, `//` for comments and `///` directly above a declaration for generated API docs. A top-level `const` can evaluate Mk code at compile time.

## Loops, arrays and collections

- `[4]int` is an inline array. `var a: [4]int = [0; 4]` initializes it. `a[lo..hi]` is a half-open shared slice, `a[..]` views the whole array, and `mut a[..]` gives a writable slice of a mutable array. Indexing checks bounds. Use `Get` for a lookup that can miss.
- `for i in 0..n` counts, `for x in xs` visits elements by value, and `for i, x in xs` includes the index for arrays, slices and lists. For an iterator such as `s.Lines()`, use `for line in s.Lines()` and keep an explicit counter if needed.
- Use `for x in &xs` to borrow elements and `for x in mut xs` to mutate through each reference. `for condition { ... }` and `for { ... }` cover conditional and indefinite loops. `if` and `match` can yield values. Ranges exclude their upper bound.
- `var xs := List[int].New(a)` makes an arena-backed growable list. `try xs.Push(value)` can exhaust the arena. For a counter table, `var counts := Map[str, int].New(a)`, then `entry := try counts.Ensure(word, 0)` and `*entry += 1`. Retaining a text key retains its source. When output order matters, explicitly order the keys or entries.

## Optionals and generics

Use `?T` for absence. A caller can bind `if value := lookup { ... }`, choose a default with `lookup else { fallback }`, or match `some(value)` and `none`. This complete unit can be run with `mk test last.mk`.

```mk
Last[T: Plain](items: []T): ?T {
    if items.Len() == 0 {
        return none
    }
    return some(items[items.Len() - 1])
}

test "last element or caller default" {
    items := [4, 9]
    Assert((Last(items[..]) else { 0 }) == 9)
    Assert((Last(items[..0]) else { 0 }) == 0)
}
```

The `Plain` bound lets `Last` copy an element out of a shared slice. To compare generic values, use the operation's interface bound, e.g. `T: Ord`. Define `interface` and `impl Interface for Type` for shared behavior. Function types use `fn(...): T`. An escaping function value carries no implicit capture environment. Pass its state explicitly. A literal passed directly to an appropriate `const fn` parameter can access surrounding state on this compiler.

## Domain errors and exhaustive decisions

Use `error` for failures the caller can distinguish. Payloads can carry plain, reference-free facts such as an offset or a rejected number. Combine errors with `|`. `E!T` is a result, `fail` constructs its error path, and `try` propagates that path. A caller can recover with `operation() else e { ... }` or inspect both branches with `match`. Reserve `.Must()` for an established invariant, since a missing or failed value panics.

```mk
enum Band {
    Low
    High
}

error Outside(value: int)

Classify(value: int): Outside!Band {
    if value < 0 || value > 100 {
        fail Outside(value: value)
    }
    return if value < 50 { Band.Low } else { Band.High }
}

Label(band: Band): str {
    return match band {
        .Low { "low" }
        .High { "high" }
    }
}

test "boundary and rejected input" {
    Assert(Label(try Classify(50)) == "high")
    _ = Classify(101) else e {
        match e {
            Outside(value) { Assert(value == 101) }
        }
        return
    }
    Assert(false)
}
```

In the negative test, `Outside(value)` binds the error's payload field. Use `Outside(value: _)` when only the kind matters. The test fails if the invalid input unexpectedly succeeds.

A test can use `try`. An error that escapes it fails the test. An error that escapes hosted `Main` prints a diagnostic and gives status 1. Return `int` or `E!int` when the command has an exit-status contract. A module can export its own `type Error` union for its public API. For a public error set marked `open`, include the required fallback when matching it from another package.

For remaining syntax, consult the matching checkout's [language reference](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/doc/reference.md) and [grammar](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/doc/grammar.md).
