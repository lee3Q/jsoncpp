#!/usr/bin/env python3
"""Regression test for jsontestrunner handling of non-seekable input paths."""

import os
import subprocess
import sys
import tempfile
import threading


def main() -> int:
    if not hasattr(os, "mkfifo"):
        print("SKIP: this platform does not provide FIFOs")
        return 0

    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} JSONTESTRUNNER", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as temp_dir:
        fifo_path = os.path.join(temp_dir, "input.json")
        os.mkfifo(fifo_path)

        def write_input() -> None:
            try:
                with open(fifo_path, "wb") as fifo:
                    fifo.write(b'{"value": 1}')
            except BrokenPipeError:
                pass

        writer = threading.Thread(target=write_input)
        writer.start()
        result = subprocess.run(
            [sys.argv[1], "--parse-only", fifo_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        writer.join(timeout=10)

    if writer.is_alive():
        print("FIFO writer did not finish", file=sys.stderr)
        return 1
    if result.returncode != 3:
        print(f"unexpected exit code: {result.returncode}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return 1
    expected = "Failed to seek input file: " + fifo_path
    if expected not in result.stderr:
        print("missing seek failure diagnostic", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
