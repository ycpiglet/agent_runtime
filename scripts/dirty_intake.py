"""Classify closeout dirty state before any cleanup side effect."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

try:
    from scripts.session_baseline import parse_codex_branches, parse_worktrees
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from session_baseline import parse_codex_branches, parse_worktrees


LOG_PREFIXES = ("agents/runtime/hook-logs/", "agents/runtime/session_baselines/")


@dataclass(frozen=True)
class DirtyRoute:
    route: str
    side_effect: str
    files: tuple[str, ...]


def _path_from_status(line: str) -> str:
    text = line.strip("\n")
    if len(text) > 3 and text[2] == " ":
        return text[3:].strip()
    return text[3:].strip() if text.startswith("?? ") else text.strip()


def classify_status(lines: list[str], declared_paths: set[str] | None = None) -> DirtyRoute:
    declared_paths = declared_paths or set()
    files = tuple(_path_from_status(line).replace("\\", "/") for line in lines if line.strip())
    if not files:
        return DirtyRoute("clean", "none", files)
    if all(path.startswith(LOG_PREFIXES) for path in files):
        return DirtyRoute("log_only", "drop_allowed_after_owner_policy", files)
    if set(files) <= {path.replace("\\", "/") for path in declared_paths}:
        return DirtyRoute("in_scope", "commit_path", files)
    return DirtyRoute("archive_required", "stash_push_issue_pointer", files)


def _git_status(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def _git_output(root: Path, args: list[str]) -> str:
    result = subprocess.run(args, cwd=root, check=True, capture_output=True, text=True)
    return result.stdout


def _git_stash_count(root: Path) -> int:
    return len([line for line in _git_output(root, ["git", "stash", "list", "--format=%H"]).splitlines() if line.strip()])


def _git_codex_branches(root: Path) -> list[str]:
    return parse_codex_branches(_git_output(root, ["git", "branch", "--list", "codex/*"]))


def _git_extra_worktrees(root: Path) -> list[dict[str, str]]:
    root_text = root.resolve().as_posix().rstrip("/")
    worktrees = parse_worktrees(_git_output(root, ["git", "worktree", "list", "--porcelain"]))
    return [item for item in worktrees if item.get("path", "").replace("\\", "/").rstrip("/") != root_text]


def _archive_slug(files: Iterable[str]) -> str:
    parts = [Path(path).stem.lower().replace("_", "-") for path in files if path]
    slug = "-".join(part for part in parts if part)[:48].strip("-")
    return slug or "late-dirty-work"


def _decision(route: str, residue: dict[str, object]) -> str:
    if route == "archive_required":
        return "block"
    if residue["branches"] or residue["worktrees"] or residue["stashes"]:
        return "block"
    if route in {"log_only", "in_scope"}:
        return "watch"
    return "pass"


def build_plan(
    route_or_lines: DirtyRoute | list[str],
    declared_paths: set[str] | None = None,
    active_codex_branches: list[str] | None = None,
    extra_worktrees: list[dict[str, str]] | None = None,
    stash_count: int = 0,
    stamp: str | None = None,
) -> dict[str, object]:
    stamp = stamp or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    route = (
        route_or_lines
        if isinstance(route_or_lines, DirtyRoute)
        else classify_status(route_or_lines, declared_paths=declared_paths)
    )
    payload = asdict(route)
    payload["files"] = list(route.files)
    residue = {
        "branches": active_codex_branches or [],
        "worktrees": [item.get("path", "") for item in (extra_worktrees or []) if item.get("path")],
        "stashes": stash_count,
    }
    payload["residue"] = residue
    payload["commands"] = []
    if route.route == "archive_required":
        date_part = stamp[:8]
        slug = _archive_slug(route.files)
        payload["commands"] = [
            f'git stash push -u -m "archive late dirty work {stamp}"',
            f"git push origin <stash-sha>:refs/heads/archive/stashes/{date_part}/{slug}",
            "create or update GitHub issue with archive ref",
        ]
    payload["issue_handoff"] = "create or update GitHub issue with every archive ref"
    payload["decision"] = _decision(route.route, residue)
    payload["status"] = payload["decision"]
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify dirty state at closeout")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--declared-path", action="append", default=[])
    parser.add_argument("--status-line", action="append", default=[])
    parser.add_argument("--stamp")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    lines = args.status_line or _git_status(root)
    payload = build_plan(
        lines,
        declared_paths=set(args.declared_path),
        active_codex_branches=_git_codex_branches(root) if not args.status_line else [],
        extra_worktrees=_git_extra_worktrees(root) if not args.status_line else [],
        stash_count=_git_stash_count(root) if not args.status_line else 0,
        stamp=args.stamp,
    )
    if args.baseline:
        payload["baseline"] = args.baseline.as_posix()
    if args.json or args.check:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"dirty-intake: {payload['status']} route={payload['route']}")
    return 1 if args.check and payload["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
