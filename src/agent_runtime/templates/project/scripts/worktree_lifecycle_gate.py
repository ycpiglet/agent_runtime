"""Lifecycle stage W5: detect and clean zombie worktrees/branches after integration.

A worktree under `.worktrees/` is a zombie when all of the following hold:

- its branch is fully contained in the integration base (ahead of
  origin/main == 0);
- the corresponding claim in `agents/runtime/task_claims/` is
  released/completed (matched by worktree_path or by the
  `.worktrees/TASK-AR-NNN` naming convention);
- `git status --short` inside the worktree is empty (no dirty or
  untracked files).

Retention policy exempts a zombie from cleanup when:

- a `PRESERVE` marker file exists in the worktree root; or
- a matching claim carries the tag `preserve`; or
- the zombie became eligible less than the retention window ago
  (default 7 days, `--retention-days`; the claim's released/updated
  timestamp is the eligibility time).

Modes:

- `--check`: watch-only report. Prints zombies and stale claims
  (active claims whose lease expiry is in the past) as `watch` lines.
  Never blocks: exits 0 unless an internal error occurs.
- `--clean`: after reporting, removes eligible zombie worktrees
  (`git worktree remove`) and deletes their branches when merged
  (`git branch -d`). Exempt, ahead>0, or dirty worktrees are never
  removed. Every action is printed.

Output is ASCII-only so cp949 consoles render it safely.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CLAIMS_REL = Path("agents/runtime/task_claims")
WORKTREES_DIRNAME = ".worktrees"
PRESERVE_MARKER = "PRESERVE"
DEFAULT_RETENTION_DAYS = 7.0
BASE_REF_CANDIDATES = ("origin/main", "origin/master", "main", "master")

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
RELEASED_CLAIM_STATUSES = {"released", "completed", "done", "closed"}


@dataclass
class WorktreeInfo:
    path: Path
    branch: str  # short branch name; "" when detached
    rel: str  # repo-relative posix path, e.g. ".worktrees/TASK-AR-505"


@dataclass
class ZombieVerdict:
    worktree: WorktreeInfo
    zombie: bool = False
    skip_reason: str = ""
    claim_id: str = ""
    eligible_since: datetime | None = None
    exempt_reason: str = ""  # preserve-marker | preserve-tag | retention-window
    age_days: float | None = None

    @property
    def cleanable(self) -> bool:
        return self.zombie and not self.exempt_reason


def _git(root: Path, *args: str) -> tuple[int, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        return 1, str(exc)
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode, output.strip()


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _norm_path(path: Path) -> str:
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    return resolved.as_posix().lower()


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


def list_worktrees(root: Path) -> list[WorktreeInfo]:
    """Return worktrees located under `<root>/.worktrees/`."""
    rc, output = _git(root, "worktree", "list", "--porcelain")
    if rc != 0:
        raise RuntimeError(f"git worktree list failed: {output}")
    container = _norm_path(root / WORKTREES_DIRNAME)
    entries: list[WorktreeInfo] = []
    current_path: Path | None = None
    current_branch = ""

    def flush() -> None:
        nonlocal current_path, current_branch
        if current_path is not None:
            normed = _norm_path(current_path)
            if normed.startswith(container + "/"):
                entries.append(
                    WorktreeInfo(
                        path=current_path,
                        branch=current_branch,
                        rel=_rel(root, current_path),
                    )
                )
        current_path = None
        current_branch = ""

    for line in output.splitlines():
        line = line.strip()
        if line.startswith("worktree "):
            flush()
            current_path = Path(line[len("worktree "):])
        elif line.startswith("branch "):
            ref = line[len("branch "):]
            current_branch = ref.removeprefix("refs/heads/")
        elif not line:
            flush()
    flush()
    return entries


def load_claims(root: Path) -> list[dict[str, Any]]:
    claims_dir = root / CLAIMS_REL
    if not claims_dir.is_dir():
        return []
    claims: list[dict[str, Any]] = []
    for path in sorted(claims_dir.glob("*.json"), key=lambda p: p.name.lower()):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, dict):
            claims.append(payload)
    return claims


def _claims_for_worktree(
    root: Path, worktree: WorktreeInfo, claims: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    target = _norm_path(worktree.path)
    task_token = worktree.path.name.strip().lower()
    matched: list[dict[str, Any]] = []
    for claim in claims:
        claim_path = str(claim.get("worktree_path", "")).strip()
        if claim_path:
            candidate = Path(claim_path)
            if not candidate.is_absolute():
                candidate = root / candidate
            if _norm_path(candidate) == target:
                matched.append(claim)
                continue
        task_id = str(claim.get("task_id", "")).strip().lower()
        if task_id and task_id == task_token:
            matched.append(claim)
    return matched


def _claim_status(claim: dict[str, Any]) -> str:
    return str(claim.get("status", "")).strip().lower()


def _claim_tags(claim: dict[str, Any]) -> set[str]:
    tags = claim.get("tags")
    if not isinstance(tags, list):
        return set()
    return {str(tag).strip().lower() for tag in tags}


def _claim_eligibility_time(claim: dict[str, Any]) -> datetime | None:
    for key in ("released_at", "updated_at", "last_heartbeat", "expires_at"):
        parsed = _parse_timestamp(claim.get(key))
        if parsed is not None:
            return parsed
    return None


def _claim_lease_expiry(claim: dict[str, Any]) -> datetime | None:
    for key in ("lease_expires_at", "expires_at"):
        parsed = _parse_timestamp(claim.get(key))
        if parsed is not None:
            return parsed
    lease = claim.get("lease")
    if isinstance(lease, dict):
        return _parse_timestamp(lease.get("expires_at"))
    return None


def resolve_base_ref(root: Path, preferred: str = "") -> str:
    candidates = [preferred] if preferred else list(BASE_REF_CANDIDATES)
    for candidate in candidates:
        if not candidate:
            continue
        rc, _ = _git(root, "rev-parse", "--verify", "--quiet", f"{candidate}^{{commit}}")
        if rc == 0:
            return candidate
    return ""


def _ahead_count(root: Path, base_ref: str, branch: str) -> int | None:
    rc, output = _git(root, "rev-list", "--count", f"{base_ref}..{branch}")
    if rc != 0:
        return None
    try:
        return int(output.strip())
    except ValueError:
        return None


def _is_dirty(worktree_path: Path) -> bool | None:
    rc, output = _git(worktree_path, "status", "--short")
    if rc != 0:
        return None
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # The untracked PRESERVE marker is part of the retention policy and
        # must not count as dirt; anything else does.
        if line.startswith("??") and line[2:].strip().strip('"') == PRESERVE_MARKER:
            continue
        return True
    return False


def evaluate_worktree(
    root: Path,
    worktree: WorktreeInfo,
    claims: list[dict[str, Any]],
    base_ref: str,
    retention_days: float,
    now: datetime,
) -> ZombieVerdict:
    verdict = ZombieVerdict(worktree=worktree)

    if not worktree.branch:
        verdict.skip_reason = "detached-head"
        return verdict
    if not base_ref:
        verdict.skip_reason = "no-base-ref"
        return verdict

    ahead = _ahead_count(root, base_ref, worktree.branch)
    if ahead is None:
        verdict.skip_reason = "ahead-unknown"
        return verdict
    if ahead > 0:
        verdict.skip_reason = f"ahead={ahead}"
        return verdict

    matched = _claims_for_worktree(root, worktree, claims)
    if not matched:
        verdict.skip_reason = "no-claim"
        return verdict
    active = [claim for claim in matched if _claim_status(claim) in ACTIVE_CLAIM_STATUSES]
    if active:
        verdict.skip_reason = f"claim-active:{active[0].get('claim_id', 'unknown')}"
        return verdict
    released = [claim for claim in matched if _claim_status(claim) in RELEASED_CLAIM_STATUSES]
    if not released:
        verdict.skip_reason = "claim-not-released"
        return verdict

    dirty = _is_dirty(worktree.path)
    if dirty is None:
        verdict.skip_reason = "status-unknown"
        return verdict
    if dirty:
        verdict.skip_reason = "dirty"
        return verdict

    verdict.zombie = True
    newest = max(released, key=lambda c: _claim_eligibility_time(c) or datetime.min.replace(tzinfo=timezone.utc))
    verdict.claim_id = str(newest.get("claim_id", "")).strip() or "unknown"
    verdict.eligible_since = _claim_eligibility_time(newest)

    if (worktree.path / PRESERVE_MARKER).exists():
        verdict.exempt_reason = "preserve-marker"
        return verdict
    if any("preserve" in _claim_tags(claim) for claim in matched):
        verdict.exempt_reason = "preserve-tag"
        return verdict

    if verdict.eligible_since is None:
        # Unknown eligibility time: be conservative, treat as just eligible.
        verdict.exempt_reason = "retention-window"
        verdict.age_days = 0.0
        return verdict
    age_days = (now - verdict.eligible_since).total_seconds() / 86400.0
    verdict.age_days = round(age_days, 2)
    if age_days < retention_days:
        verdict.exempt_reason = "retention-window"
    return verdict


def find_stale_claims(claims: list[dict[str, Any]], now: datetime) -> list[str]:
    lines: list[str] = []
    for claim in claims:
        if _claim_status(claim) not in ACTIVE_CLAIM_STATUSES:
            continue
        expiry = _claim_lease_expiry(claim)
        if expiry is None or expiry >= now:
            continue
        claim_id = str(claim.get("claim_id", "")).strip() or "unknown"
        task_id = str(claim.get("task_id", "")).strip() or "unknown"
        lines.append(
            f"stale-claim:{claim_id} task={task_id} "
            f"status={_claim_status(claim)} lease_expired={expiry.isoformat()}"
        )
    return lines


def _zombie_line(verdict: ZombieVerdict) -> str:
    worktree = verdict.worktree
    eligible = verdict.eligible_since.isoformat() if verdict.eligible_since else "unknown"
    base = (
        f"zombie:{worktree.rel} branch={worktree.branch or 'detached'} "
        f"ahead=0 claim={verdict.claim_id} eligible_since={eligible}"
    )
    if verdict.exempt_reason:
        age = "unknown" if verdict.age_days is None else f"{verdict.age_days}"
        return f"{base} exempt={verdict.exempt_reason} age_days={age}"
    return base


def clean_zombies(root: Path, verdicts: list[ZombieVerdict]) -> tuple[list[str], int]:
    """Remove cleanable zombies. Returns (action lines, failure count)."""
    actions: list[str] = []
    failures = 0
    for verdict in verdicts:
        worktree = verdict.worktree
        if not verdict.zombie:
            continue
        if verdict.exempt_reason:
            actions.append(f"skip {worktree.rel} reason={verdict.exempt_reason}")
            continue
        # Final safety guard: never remove a dirty worktree even if state
        # changed between scan and clean. An unknown dirty state (git status
        # failed) is skipped too, mirroring evaluate_worktree's status-unknown
        # handling, instead of being treated as clean.
        dirty = _is_dirty(worktree.path)
        if dirty is None:
            actions.append(f"skip {worktree.rel} reason=dirty-recheck-unknown")
            continue
        if dirty:
            actions.append(f"skip {worktree.rel} reason=dirty-recheck")
            continue
        rc, output = _git(root, "worktree", "remove", str(worktree.path))
        if rc != 0:
            failures += 1
            actions.append(f"error remove-worktree {worktree.rel}: {output}")
            continue
        actions.append(f"removed-worktree {worktree.rel}")
        if worktree.branch:
            rc, output = _git(root, "branch", "-d", worktree.branch)
            if rc != 0:
                actions.append(f"warn branch-not-deleted {worktree.branch}: {output}")
            else:
                actions.append(f"deleted-branch {worktree.branch}")
    return actions, failures


def run(root: Path, *, clean: bool, retention_days: float, base_ref_arg: str) -> int:
    now = datetime.now(timezone.utc)
    try:
        worktrees = list_worktrees(root)
    except RuntimeError as exc:
        print("worktree-lifecycle-gate: error")
        print(f"root={root}")
        print(f"- error {exc}")
        return 1

    claims = load_claims(root)
    base_ref = resolve_base_ref(root, base_ref_arg)
    verdicts = [
        evaluate_worktree(root, worktree, claims, base_ref, retention_days, now)
        for worktree in worktrees
    ]
    zombies = [v for v in verdicts if v.zombie]
    cleanable = [v for v in zombies if v.cleanable]
    exempt = [v for v in zombies if v.exempt_reason]
    stale = find_stale_claims(claims, now)

    print("worktree-lifecycle-gate: pass")
    print(f"root={root}")
    print(f"mode={'clean' if clean else 'check'}")
    print(f"base_ref={base_ref or 'unresolved'}")
    print(f"retention_days={retention_days}")
    print(f"worktrees={len(worktrees)}")
    print(f"zombies={len(zombies)}")
    print(f"zombies_cleanable={len(cleanable)}")
    print(f"zombies_exempt={len(exempt)}")
    print(f"stale_claims={len(stale)}")
    for verdict in zombies:
        print(f"- watch {_zombie_line(verdict)}")
    for line in stale:
        print(f"- watch {line}")

    if not clean:
        return 0

    actions, failures = clean_zombies(root, verdicts)
    print(f"clean_actions={len(actions)}")
    for action in actions:
        print(f"- clean {action}")
    if failures:
        print(f"clean_failures={failures}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect (and optionally clean) zombie worktrees/branches"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument(
        "--check", action="store_true", help="Watch-only report; always exits 0 unless internal error"
    )
    parser.add_argument(
        "--clean", action="store_true", help="Remove eligible zombie worktrees and merged branches"
    )
    parser.add_argument(
        "--retention-days",
        type=float,
        default=DEFAULT_RETENTION_DAYS,
        help="Retention window in days before an eligible zombie may be cleaned",
    )
    parser.add_argument(
        "--base-ref",
        default="",
        help="Integration base ref (default: first of origin/main, origin/master, main, master)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.check and not args.clean:
        parser.print_help()
        return 2
    root = args.root.resolve()
    return run(
        root,
        clean=args.clean,
        retention_days=args.retention_days,
        base_ref_arg=args.base_ref,
    )


if __name__ == "__main__":
    sys.exit(main())
