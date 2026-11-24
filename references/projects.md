# Packages and native builds

## Select the compiler

Run `mk version` first. Record the Mk release, build ID, host and selected LLVM directory when investigating behavior across machines. The signed release bundle includes Mk, its tested clang and lld, and documentation. A source build of the baseline requires Go 1.27 or newer and LLVM 21 or newer. Check `go.mod` and the README for the revision being built. [Upstream build and installation instructions](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/README.md#getting-started)

From a checkout of `zerodayokay/Mk-Lang` on a Unix-like host:

```sh
go build -o mk ./cmd/mk
./mk version
```

On Windows build `mk.exe`. Use the resulting executable by absolute path or put its directory on `PATH`. `--llvm DIR` on a compiling command, or `MK_LLVM`, points at the directory containing clang and the target's linker. A source-built Mk embeds its matching standard library. Set `MK_STD` only when deliberately testing another std tree. If cache writes fail in a restricted environment, point `MK_CACHE` at a writable directory.

## Grow a package

`mk new ledger` creates `ledger/pkg.mk` and `ledger/src/main.mk`. Choose one identifier for the package name, e.g. `daily_ledger`. A hyphen in a new package name is a usage error. The generated manifest's `mk` minimum declares the oldest supported compiler. For an existing application, preserve the declared minimum or verify a deliberate change. The [linepick manifest](../assets/linepick/pkg.mk) is a complete single-bin example.

- The `root` of each `pkg.Bin` names a module directory. An executable needs an `export Main` there. Hosted `Main(sys: &System)` can return `void`, `int`, `E!void` or `E!int`. Keep argument validation and user-facing messages here. `sys.args[0]` is the executable and user arguments begin at index 1.
- Each directory of source files is one module. Files in the same directory can call private declarations across files. Imports apply to the individual file. For `src/search/search.mk`, write `import src.search` and call `search.Find(...)`. Two modules with the same final segment can be disambiguated with `import alias = path`.
- Import the module and qualify its exports. A directory segment named `internal` restricts use to the package. Keep dependencies acyclic. Multiple executables can have distinct bin roots and share a domain module. A library for other Mk code can export functions without a `Main`. Native static/dynamic library outputs use the manifest's bin `kind` and C ABI exports.
- Inside the `deps` array, `pkg.Dep(name: "ledgerlib", path: "../ledgerlib")` selects a local package. Import its root as `ledgerlib` or its submodule by a qualified path. For a tagged remote use the `source` and `version` fields. The selected versions follow the reachable minimum requirements. Commit the generated `pkg.sum` for fetched dependencies. It records integrity hashes. `mk tree` and `mk why NAME` explain selection.
- In a workspace, list member directories in the root manifest's `members`. From the workspace root, `mk check ./...`, `mk test ./...` and `mk build ./...` address all members. Use `--locked` for existing sums and `--offline` when dependencies are already cached or vendored.

## Verify an application through its entry point

From the [linepick package](../assets/linepick/pkg.mk), a POSIX shell session can exercise the complete program:

```sh
mk fmt --check
mk check
mk test
printf 'pear\napple\npear tart\n' > sample.txt
mk run -- pear sample.txt
mk build --release -o linepick-release
./linepick-release pear sample.txt
```

Both executions should print `1: pear` and `3: pear tart` on separate lines and return 0. A search for `plum` should produce empty stdout and status 1. Running without arguments prints usage on stderr and returns 2. To run these checks without writing into the package, use the [example checker](../scripts/check-example.py), which copies the package to a temporary directory.

`mk check` stops before native code generation. `mk test` executes named test blocks in their own processes. `mk run -- ARGS` builds and invokes the bin and returns its exit status. Use `mk build --bin NAME` for a particular bin, and `-o PATH` to control the output. When investigating optimized behavior use `--release` and, for optimized code with runtime contracts enabled, `--profile checked`. A successful cross-target check establishes front-end acceptance for that target. A native artifact and a run on the target establish different facts.

## Find implementations with the right dependencies

Start from the installed compiler. `mk query modules` lists the modules, `mk query sig Name` shows flows and errors, and `mk doc std.MOD` prints a module's public surface. Queries accept `--root DIR`. For larger tasks the following paths in the checked-out repository give complete call sites and their tests.

| Application need | Starting point |
| --- | --- |
| CLI flags and usage | `std.cli`, `gen cli.Args(Options)`, and `Dogfoods/mgrep`. Use `sys.args[1..]` when calling a generated option parser. |
| Parsing and serialization | `std.text`, `std.csv`, `std.json`, and the “Parse JSON into a struct” recipe in `doc/cookbook.md`. `gen json.Codec(T)` generates typed conversions. |
| Network and services | `std.net`, `std.http`, `std.websocket`, or the first-party package under `kits/web`. `Dogfoods/chat` contains task and channel lifetimes. Check each package's manifest for dependencies. |
| Storage and crash recovery | `std.fs`, `std.sim`, and `Dogfoods/kvd` for file operations, fault injection and replay. |
| Larger parsers and interpreters | `Dogfoods/lox` has a parser, arena-backed syntax tree and bytecode VM with executable cases. |

Use the nearest example's manifest, import lines and tests together when adapting it. Upstream's [package guide](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/doc/packages.md), [standard-library index](https://github.com/zerodayokay/Mk-Lang/blob/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/doc/std/README.md) and [complete applications](https://github.com/zerodayokay/Mk-Lang/tree/559c14cd1f84f67b1c7a6082a4d57989a2d564e1/Dogfoods) cover the surrounding APIs and platform requirements.
