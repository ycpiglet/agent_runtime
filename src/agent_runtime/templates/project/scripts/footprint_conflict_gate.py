"""Claim-time footprint conflict detection for parallel pane work.

Two agents editing the same files in different worktrees produce merge
conflicts that are only discovered at integration time. This gate moves the
discovery to claim time: every claim may declare its file footprint
(`target_files`), and a new claim whose footprint intersects an active
claim's footprint must be rejected before any work starts.

Usage:
  --check                  pairwise-verify all ACTIVE claims' declared
                           footprints; overlapping declarations fail.
                           Undeclared footprints are reported as watch
                           findings (cannot be verified) but do not fail.
  --probe --task-id T \
          --file F [...]   verify a PROPOSED footprint against all active
                           claims before creating a claim; exit 1 on
                           conflict with the conflicting claim ids.

Footprint entries are repo-relative paths. A trailing `/**` declares a
directory prefix (e.g. `scripts/**`); `*` patterns are matched with fnmatch
in both directions.

Dispatcher wiring (TASK-AR-500): `task_claim_dispatcher.py create` imports
`footprints_overlap` / `ACTIVE_CLAIM_STATUSES` from this module and refuses
a new claim whose declared footprint intersects an active claim's footprint.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

CLAIMS_REL = "agents/runtime/task_claims"
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


def _normalize(entry: str) -> str:
    entry = entry.replace("\\", "/").strip()
    return entry.removeprefix("./")


def _prefix_of(entry: str) -> str | None:
    if entry.endswith("/**"):
        return entry[:-3].rstrip("/")
    return None


def entries_overlap(a: str, b: str) -> bool:
    a, b = _normalize(a), _normalize(b)
    if not a or not b:
        return False
    if a == b:
        return True
    pa, pb = _prefix_of(a), _prefix_of(b)
    if pa is not None and pb is not None:
        return pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")
    if pa is not None:
        return b == pa or b.startswith(pa + "/")
    if pb is not None:
        return a == pb or a.startswith(pb + "/")
    return fnmatch(a, b) or fnmatch(b, a)


def footprints_overlap(left: list[str], right: list[str]) -> list[tuple[str, str]]:
    return [
        (a, b) for a in left for b in right if entries_overlap(a, b)
    ]


def _load_active_claims(root: Path) -> list[dict]:
    claims_dir = root / CLAIMS_REL
    if not claims_dir.exists():
        return []
    claims = []
    for path in sorted(claims_dir.glob("CLAIM-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"warning: skipping unreadable claim {path.name}: {exc}", file=sys.stderr)
            continue
        if data.get("status") in ACTIVE_CLAIM_STATUSES:
            claims.append(data)
    return claims


def cmd_check(root: Path) -> int:
    claims = _load_active_claims(root)
    declared = [c for c in claims if c.get("target_files")]
    undeclared = [c for c in claims if not c.get("target_files")]
    findings: list[str] = []
    watches: list[str] = []
    for i, left in enumerate(declared):
        for right in declared[i + 1 :]:
            pairs = footprints_overlap(left["target_files"], right["target_files"])
            for a, b in pairs:
                findings.append(
                    f"footprint-overlap:{left.get('claim_id')}:{a} <-> "
                    f"{right.get('claim_id')}:{b}"
                )
    for claim in undeclared:
        watches.append(f"undeclared-footprint:{claim.get('claim_id')}")
    status = "fail" if findings else "pass"
    print(f"footprint-conflict-gate: {status}")
    print(f"root={root}")
    print(f"active_claims={len(claims)}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- block {finding}")
    print(f"watch={len(watches)}")
    for watch in watches:
        print(f"- watch {watch}")
    return 1 if findings else 0


def cmd_probe(root: Path, task_id: str, files: list[str]) -> int:
    claims = _load_active_claims(root)
    findings: list[str] = []
    watches: list[str] = []
    for claim in claims:
        if claim.get("task_id") == task_id:
            continue
        target_files = claim.get("target_files") or []
        if not target_files:
            watches.append(f"undeclared-footprint:{claim.get('claim_id')}")
            continue
        pairs = footprints_overlap(files, target_files)
        for a, b in pairs:
            findings.append(
                f"footprint-overlap:{a} <-> {claim.get('claim_id')}:{b}"
            )
    status = "fail" if findings else "pass"
    print(f"footprint-conflict-gate: {status}")
    print(f"root={root}")
    print(f"probe_task={task_id}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- block {finding}")
    print(f"watch={len(watches)}")
    for watch in watches:
        print(f"- watch {watch}")
    if findings:
        print("action=footprint conflicts with active claims; narrow the unit's target_files, wait for the conflicting claim to release, or replan the wave")
    return 1 if findings else 0


def _covered(actual: str, declared: list[str]) -> bool:
    """Is an actually-changed file covered by ANY declared footprint entry?"""
    return any(entries_overlap(actual, entry) for entry in declared)


def _git_changed_files(root: Path, base: str) -> list[str]:
    """Files changed on HEAD since diverging from ``base`` (merge-base diff).

    Uses ``git diff --name-only <base>...HEAD`` so the actual footprint is the
    wave's net change, NOT an empty worktree-vs-HEAD diff (a worker commits as it
    goes, so a plain ``git diff`` would be empty and the check would no-op).
    """
    result = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def cmd_postverify(
    root: Path,
    task_id: str,
    *,
    base: str,
    actual_files: list[str] | None,
    enforce: bool,
) -> int:
    """Post-hoc actual-vs-declared footprint check (TASK-AR-529, GH #125).

    After a unit completes, compare the ACTUAL changed files to the claim's
    DECLARED ``target_files``. ``actual not subset of declared`` means the unit
    touched files it never declared -- the exact hole that lets a 'disjoint' wave
    collide undetected. Watch by default; ``--enforce-undeclared`` makes it block.
    """
    claims = _load_active_claims(root)
    claim = next((c for c in claims if c.get("task_id") == task_id), None)
    if claim is None:
        # Fall back to any claim file for the task (may be released at closeout).
        for path in sorted((root / CLAIMS_REL).glob("CLAIM-*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("task_id") == task_id:
                claim = data
                break
    declared = list((claim or {}).get("target_files") or [])
    actual = actual_files if actual_files is not None else _git_changed_files(root, base)

    undeclared = [path for path in actual if not _covered(path, declared)]
    severity = "block" if enforce else "watch"
    print(f"task_id={task_id}")
    print(f"declared={len(declared)} actual={len(actual)} undeclared={len(undeclared)}")
    if not declared and actual:
        print(f"- {severity} undeclared-footprint:claim-declares-nothing:{task_id}")
    for path in undeclared:
        print(f"- {severity} actual-not-declared:{path}")
    if undeclared:
        print("action=add the touched files to the unit target_files, or split the unit; the worktree backstop degrades an undeclared collision to a merge conflict, not live corruption")
    if enforce and (undeclared or (not declared and actual)):
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect file-footprint conflicts between parallel claims"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true", help="Verify active claims pairwise")
    parser.add_argument("--probe", action="store_true", help="Verify a proposed footprint")
    parser.add_argument("--postverify", action="store_true", help="Post-hoc actual-vs-declared footprint check for a completed task (TASK-AR-529)")
    parser.add_argument("--task-id", default=None)
    parser.add_argument("--file", action="append", default=[], help="Proposed footprint entry (repeatable)")
    parser.add_argument("--base", default="origin/main", help="Merge-base ref for --postverify actual-file diff (default origin/main)")
    parser.add_argument("--actual-file", action="append", default=None, help="Explicit actual changed file for --postverify (repeatable; bypasses git)")
    parser.add_argument("--enforce-undeclared", action="store_true", help="Make --postverify BLOCK (exit 1) on undeclared footprint instead of watch (default off, deferred per council)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.probe:
        if not args.task_id or not args.file:
            parser.error("--probe requires --task-id and at least one --file")
        return cmd_probe(root, args.task_id, args.file)
    if args.postverify:
        if not args.task_id:
            parser.error("--postverify requires --task-id")
        return cmd_postverify(
            root,
            args.task_id,
            base=args.base,
            actual_files=args.actual_file,
            enforce=args.enforce_undeclared,
        )
    if args.check:
        return cmd_check(root)
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
