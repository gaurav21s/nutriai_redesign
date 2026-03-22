#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 5:
        print("usage: spawn_daemon.py <cwd> <log_path> <pid_path> <command...>", file=sys.stderr)
        return 1

    cwd = Path(sys.argv[1])
    log_path = Path(sys.argv[2])
    pid_path = Path(sys.argv[3])
    command = sys.argv[4:]

    cwd.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("ab") as log_file, open(os.devnull, "rb") as devnull:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdin=devnull,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )

    pid_path.write_text(f"{process.pid}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
