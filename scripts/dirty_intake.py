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
ACTIVE_CLAIM_STATUSES = {
    "active",
    "assigned",
    "claimed",
    "in_progress",
    "review",
    "running",
    "waiting_review",
    "working",
}


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
    files: list[str] = []
    seen: set[str] = set()
    for args in (
        ["git", "diff", "--name-only", "--cached"],
        ["git", "diff", "--name-only"],
    ):
        for path in _git_output(root, args).splitlines():
            normalized = path.strip().replace("\\", "/")
            if normalized and normalized not in seen:
                seen.add(normalized)
                files.append(f" M {normalized}")
    for path in _git_output(root, ["git", "ls-files", "--others", "--exclude-standard"]).splitlines():
        normalized = path.strip().replace("\\", "/")
        if normalized and normalized not in seen:
            seen.add(normalized)
            files.append(f"?? {normalized}")
    return files


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


def _norm_branch(value: str) -> str:
    return value.strip().lstrip("*+ ").strip().replace("refs/heads/", "")


def _norm_path(root: Path, value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve().as_posix().rstrip("/")


def _git_claim_roots(root: Path, extra_worktrees: list[dict[str, str]]) -> list[Path]:
    roots = [root]
    for item in extra_worktrees:
        path = str(item.get("path") or "").strip()
        if path:
            roots.append(Path(path))
    seen: set[str] = set()
    result: list[Path] = []
    for path in roots:
        try:
            resolved = path.resolve()
        except OSError:
            continue
        key = resolved.as_posix().rstrip("/")
        if key not in seen:
            seen.add(key)
            result.append(resolved)
    return result


def _git_active_claim_residue(root: Path, extra_worktrees: list[dict[str, str]] | None = None) -> dict[str, list[str]]:
    extra_worktrees = extra_worktrees or []
    branches: set[str] = set()
    worktrees: set[str] = set()
    root_text = root.resolve().as_posix().rstrip("/")
    branch_by_worktree = {
        Path(str(item.get("path") or "")).resolve().as_posix().rstrip("/"): _norm_branch(str(item.get("branch") or ""))
        for item in extra_worktrees
        if item.get("path")
    }
    for claim_root in _git_claim_roots(root, extra_worktrees):
        claims_dir = claim_root / "agents" / "runtime" / "task_claims"
        if not claims_dir.is_dir():
            continue
        root_has_active_claim = False
        for path in sorted(claims_dir.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if str(payload.get("status") or "").strip() not in ACTIVE_CLAIM_STATUSES:
                continue
            root_has_active_claim = True
            branch = str(payload.get("branch") or "").strip()
            worktree_path = str(payload.get("worktree_path") or "").strip()
            if branch:
                branches.add(_norm_branch(branch))
            if worktree_path:
                worktrees.add(_norm_path(claim_root, worktree_path))
        claim_root_text = claim_root.resolve().as_posix().rstrip("/")
        if root_has_active_claim and claim_root_text != root_text:
            worktrees.add(claim_root_text)
            branch = branch_by_worktree.get(claim_root_text, "")
            if branch.startswith("codex/"):
                branches.add(branch)
    return {"branches": sorted(branches), "worktrees": sorted(worktrees)}


def _git_remote_preserved_residue(root: Path, extra_worktrees: list[dict[str, str]] | None = None) -> dict[str, list[str]]:
    try:
        output = _git_output(
            root,
            ["git", "for-each-ref", "--format=%(refname:short)\t%(upstream:short)", "refs/heads/codex"],
        )
    except subprocess.CalledProcessError:
        return {"branches": [], "worktrees": []}
    branches = {
        _norm_branch(line.split("\t", 1)[0])
        for line in output.splitlines()
        if "\t" in line and line.split("\t", 1)[1].strip()
    }
    worktrees = {
        item.get("path", "").replace("\\", "/").rstrip("/")
        for item in (extra_worktrees or [])
        if _norm_branch(str(item.get("branch") or "")) in branches and item.get("path")
    }
    return {"branches": sorted(branches), "worktrees": sorted(worktrees)}


def _archive_slug(files: Iterable[str]) -> str:
    parts = [Path(path).stem.lower().replace("_", "-") for path in files if path]
    slug = "-".join(part for part in parts if part)[:48].strip("-")
    return slug or "late-dirty-work"


def _decision(route: str, residue: dict[str, object]) -> str:
    if route == "archive_required":
        return "block"
    unresolved = residue.get("unresolved", {})
    unresolved_branches = unresolved.get("branches", residue["branches"]) if isinstance(unresolved, dict) else residue["branches"]
    unresolved_worktrees = unresolved.get("worktrees", residue["worktrees"]) if isinstance(unresolved, dict) else residue["worktrees"]
    if unresolved_branches or unresolved_worktrees or residue["stashes"]:
        return "block"
    if route in {"log_only", "in_scope"}:
        return "watch"
    preserved = residue.get("preserved_active", {})
    if isinstance(preserved, dict) and (preserved.get("branches") or preserved.get("worktrees")):
        return "watch"
    preserved_remote = residue.get("preserved_remote", {})
    if isinstance(preserved_remote, dict) and (preserved_remote.get("branches") or preserved_remote.get("worktrees")):
        return "watch"
    return "pass"


def build_plan(
    route_or_lines: DirtyRoute | list[str],
    declared_paths: set[str] | None = None,
    active_codex_branches: list[str] | None = None,
    extra_worktrees: list[dict[str, str]] | None = None,
    preserved_active: dict[str, list[str]] | None = None,
    preserved_remote: dict[str, list[str]] | None = None,
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
    preserved_active = preserved_active or {"branches": [], "worktrees": []}
    preserved_remote = preserved_remote or {"branches": [], "worktrees": []}
    active_branches = {_norm_branch(item) for item in preserved_active.get("branches", [])}
    active_worktrees = {item.replace("\\", "/").rstrip("/") for item in preserved_active.get("worktrees", [])}
    remote_branches = {_norm_branch(item) for item in preserved_remote.get("branches", [])}
    remote_worktrees = {item.replace("\\", "/").rstrip("/") for item in preserved_remote.get("worktrees", [])}
    preserved_branches = active_branches | remote_branches
    preserved_worktrees = active_worktrees | remote_worktrees
    all_branches = [_norm_branch(item) for item in (active_codex_branches or [])]
    all_worktrees = [
        item.get("path", "").replace("\\", "/").rstrip("/")
        for item in (extra_worktrees or [])
        if item.get("path")
    ]
    unresolved_branches = [item for item in all_branches if item not in preserved_branches]
    unresolved_worktrees = [item for item in all_worktrees if item not in preserved_worktrees]
    residue = {
        "branches": all_branches,
        "worktrees": all_worktrees,
        "preserved_active": {
            "branches": [item for item in all_branches if item in active_branches],
            "worktrees": [item for item in all_worktrees if item in active_worktrees],
        },
        "preserved_remote": {
            "branches": [item for item in all_branches if item in remote_branches],
            "worktrees": [item for item in all_worktrees if item in remote_worktrees],
        },
        "unresolved": {
            "branches": unresolved_branches,
            "worktrees": unresolved_worktrees,
        },
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
    active_codex_branches = _git_codex_branches(root) if not args.status_line else []
    extra_worktrees = _git_extra_worktrees(root) if not args.status_line else []
    payload = build_plan(
        lines,
        declared_paths=set(args.declared_path),
        active_codex_branches=active_codex_branches,
        extra_worktrees=extra_worktrees,
        preserved_active=_git_active_claim_residue(root, extra_worktrees) if not args.status_line else {"branches": [], "worktrees": []},
        preserved_remote=_git_remote_preserved_residue(root, extra_worktrees) if not args.status_line else {"branches": [], "worktrees": []},
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
