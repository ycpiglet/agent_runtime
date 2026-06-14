"""Idempotent console auto-start (for a SessionStart hook).

Starts the Agent Runtime console in the background when a work session begins,
UNLESS it is already serving on the target port -- so repeated sessions never
spawn duplicate servers. Wire this as a Claude Code SessionStart hook so the UI
is always up while you work.

    python scripts/console_autostart.py            # start if not already up
    python scripts/console_autostart.py --check     # report status only, no start
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / ".console-autostart.log"


def _is_up(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex((host, port)) == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Idempotent Agent Runtime console auto-start")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--check", action="store_true", help="report status only; never start")
    args = parser.parse_args()

    if _is_up(args.host, args.port):
        print(f"console-autostart: already serving http://{args.host}:{args.port}/")
        return 0
    if args.check:
        print(f"console-autostart: not running on {args.host}:{args.port}")
        return 0

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | getattr(subprocess, "DETACHED_PROCESS", 0)
    with open(LOG, "ab") as fh:
        subprocess.Popen(
            [sys.executable, str(ROOT / "scripts" / "run_console.py"),
             "--host", args.host, "--port", str(args.port)],
            cwd=str(ROOT),
            stdout=fh,
            stderr=fh,
            creationflags=creationflags,
            close_fds=True,
        )
    print(f"console-autostart: launched http://{args.host}:{args.port}/ in the background")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
