"""Run Owner-facing governance gates used by hooks, CI, and release prep."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str]) -> int:
    return subprocess.call([sys.executable, *args], cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="Owner governance gate")
    parser.add_argument("--allow-empty-owner-docs", action="store_true")
    args = parser.parse_args()

    owner_doc_args = ["scripts/owner_doc_format_gate.py", "--manifest", "owner-docs.yml"]
    if args.allow_empty_owner_docs:
        owner_doc_args.append("--allow-empty")
    checks = [
        owner_doc_args,
        [
            "scripts/state_machine_gate.py",
            "--path",
            "agents/project/STATE-MACHINES.yml",
            "--path",
            "schemas/state-machines.schema.json",
        ],
        ["scripts/parallel_worktree_gate.py", "--check"],
    ]

    failed = 0
    for check in checks:
        rc = run(check)
        if rc:
            failed = rc
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
