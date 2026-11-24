#!/usr/bin/env python3
"""Exercise the bundled linepick package against a chosen Mk compiler."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


EXAMPLE = Path(__file__).resolve().parents[1] / "assets" / "linepick"


def verify(binary, directory, args, status, output="", error=None):
    result = subprocess.run(
        [binary, *args],
        cwd=directory,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
    )
    if error is None:
        matches_error = result.stderr == ""
        expected_error = "empty"
    else:
        matches_error = error in result.stderr
        expected_error = f"containing {error!r}"
    if result.returncode != status or result.stdout != output or not matches_error:
        raise SystemExit(
            f"{args!r}: expected exit {status}, stdout {output!r}, "
            f"stderr {expected_error}\n"
            f"got exit {result.returncode}, stdout {result.stdout!r}, "
            f"stderr {result.stderr!r}"
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mk", default="mk", help="Mk executable name or path")
    args = parser.parse_args()
    compiler = shutil.which(args.mk)
    if compiler is None:
        parser.error(f"cannot find {args.mk!r}, supply --mk /path/to/mk")
    compiler = Path(compiler).resolve()
    with tempfile.TemporaryDirectory(prefix="mk-linepick-") as tmp:
        work = Path(tmp)
        package = work / "linepick"
        shutil.copytree(EXAMPLE, package)
        for command in (["version"], ["fmt", "--check"], ["check"], ["test"]):
            subprocess.run([compiler, *command], cwd=package, check=True)
        (work / "sample.txt").write_bytes("before\r\ncafé\r\ncafé noir".encode("utf-8"))
        (work / "invalid.txt").write_bytes(b"\xff")
        for profile, options in (("dev", []), ("release", ["--release"])):
            binary = work / (profile + (".exe" if os.name == "nt" else ""))
            subprocess.run([compiler, "build", *options, "-o", binary], cwd=package, check=True)
            verify(binary, work, ["fé", "sample.txt"], 0, "2: café\n3: café noir\n")
            verify(binary, work, ["absent", "sample.txt"], 1)
            verify(binary, work, [], 2, error="usage: linepick")
            verify(binary, work, ["x", "missing.txt"], 2, error="missing.txt")
            verify(binary, work, ["x", "invalid.txt"], 2, error="Utf8Error")
            print(f"{profile}: 5 executable cases passed", flush=True)


if __name__ == "__main__":
    main()
