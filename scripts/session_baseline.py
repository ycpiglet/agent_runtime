"""Capture read-only session baseline snapshots for closeout comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "agent-runtime-session-baseline/v1"


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return result.stdout


def status_fingerprint(status: str) -> str:
    normalized = "\n".join(sorted(line.rstrip() for line in status.splitlines() if line.strip()))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _parse_worktrees(raw: str) -> list[dict[str, str]]:
    worktrees: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            if current:
                worktrees.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree" and current:
            worktrees.append(current)
            current = {}
        if key == "worktree":
            current["path"] = value.strip()
        elif key == "branch":
            current["branch"] = value.strip().replace("refs/heads/", "")
        else:
            current[key] = value.strip()
    if current:
        worktrees.append(current)
    return worktrees


def parse_worktrees(raw: str) -> list[dict[str, str]]:
    return _parse_worktrees(raw)


AGENT_BRANCH_PREFIXES = ("codex/", "claude/")
AGENT_BRANCH_PATTERNS = tuple(f"{prefix}*" for prefix in AGENT_BRANCH_PREFIXES)


def is_agent_branch(branch: str) -> bool:
    return branch.startswith(AGENT_BRANCH_PREFIXES)


def parse_codex_branches(raw: str) -> list[str]:
    return [line.strip().lstrip("* ").strip() for line in raw.splitlines() if line.strip()]


def capture(root: Path) -> dict[str, object]:
    root = root.resolve()
    status = run_git(["git", "status", "--porcelain=v1"], root)
    stashes = [line for line in run_git(["git", "stash", "list", "--format=%H"], root).splitlines() if line.strip()]
    branches = parse_codex_branches(run_git(["git", "branch", "--list", *AGENT_BRANCH_PATTERNS], root))
    return {
        "schema": SCHEMA,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "cwd": str(root),
        "head": run_git(["git", "rev-parse", "--short", "HEAD"], root).strip(),
        "branch": run_git(["git", "branch", "--show-current"], root).strip(),
        "status_fingerprint": status_fingerprint(status),
        "stash_count": len(stashes),
        "worktrees": _parse_worktrees(run_git(["git", "worktree", "list", "--porcelain"], root)),
        "active_codex_branches": branches,
    }


def write_baseline(root: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = capture(root)
    stamp = str(data["captured_at"]).replace(":", "").replace("+", "Z")
    path = output_dir / f"session-baseline-{stamp}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture session baseline")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output-dir", type=Path, default=Path("agents/runtime/session_baselines"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    path = write_baseline(args.root.resolve(), args.output_dir)
    payload = {"status": "captured", "baseline": path.as_posix()}
    print(json.dumps(payload, ensure_ascii=False) if args.json else f"baseline={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
