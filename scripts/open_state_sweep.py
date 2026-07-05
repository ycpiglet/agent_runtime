"""Report open state that has drifted from merged reality (watch-only).

COMPOUND-2026-07-04 (`stale-open-state-debt`): under high merge velocity,
open GitHub issues drift from what main has already delivered — closing
keywords in auto-merged commits do not reliably auto-close issues, so
verified-done work sits open while the board loses trust as an attention
surface. The 2026-07-04 manual sweep closed 8 such issues by hand; this
tool makes that sweep repeatable.

What it checks:
1. Closing keywords (``fixes/closes/resolves #N``) in the merged history of
   ``--ref`` vs the currently OPEN issues -> ``stale-open-issue`` findings
   (the merged history claims the issue is done, but it is still open).
2. Untriaged dirty-work archive refs (``archive/stashes/*``) -> reported as
   a count so preserved-but-unlanded work stays visible (#162 was recovered
   from exactly such a stash three weeks after archiving).
3. Non-archive remote branches fully contained in ``--ref`` (ahead=0) and
   idle past an age floor -> ``merged-remote-branch`` findings (merge debris
   that the auto-delete flow missed; six 3-week-old ones found 2026-07-05).

Boundary: report tool only — NOT wired into the owner governance chain.
``--check`` exits 1 on findings for opt-in CI use; the default exit is 0.
Open issues come from ``gh`` when available or ``--issues-file`` (JSON list
of ``{number, title}``) for offline/deterministic use.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

CLOSING_RE = re.compile(
    r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s*:?\s+#(\d+)", re.IGNORECASE
)
ARCHIVE_STASH_PREFIX = "refs/remotes/origin/archive/stashes/"


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def closed_issue_numbers_in_history(root: Path, ref: str) -> set[int]:
    """Issue numbers referenced by closing keywords in the merged history of ref."""
    log = _run_git(root, "log", ref, "--format=%s%n%b")
    return {int(match.group(1)) for match in CLOSING_RE.finditer(log)}


def archive_stash_refs(root: Path) -> list[str]:
    try:
        out = _run_git(root, "for-each-ref", "--format=%(refname)", ARCHIVE_STASH_PREFIX)
    except RuntimeError:
        return []
    # Keep the resolvable short form (origin/...) so rev-list can use the names.
    return [line.removeprefix("refs/remotes/") for line in out.splitlines() if line.strip()]


def dangling_lane_findings(root: Path, ref: str, stashes: list[str], threshold: int) -> list[dict[str, Any]]:
    """Stash refs whose PARENT chain carries a whole unmerged lane.

    A dirty-work stash records its base commit as first parent. When that
    base is itself not on the mainline, everything below it is reachable
    ONLY through the stash ref — deleting the stash would garbage an entire
    lane. Found in the wild on 2026-07-04: 160 unmerged commits (11 taskset
    registrations, TASK-AR-618..620) hung off one stash parent (issue #250).
    """
    findings: list[dict[str, Any]] = []
    for stash in stashes:
        try:
            # "Dangling" means the stash ref is the ONLY tether: commits
            # reachable neither from the mainline ref nor from any pinned
            # archive/branches/* preservation ref count toward the lane.
            count = int(
                _run_git(
                    root,
                    "rev-list",
                    "--count",
                    f"{stash}^1",
                    "--not",
                    ref,
                    "--glob=refs/remotes/origin/archive/branches/*",
                ).strip()
            )
        except (RuntimeError, ValueError):
            continue  # plain snapshot commit without a stash parent chain
        if count >= threshold:
            findings.append(
                {
                    "kind": "dangling-lane",
                    "stash": stash,
                    "unmerged_commit_count": count,
                    "detail": (
                        f"stash parent chain carries {count} commits absent from {ref}; the lane "
                        "is preserved only by this stash ref — pin it under archive/branches/ "
                        "and route an integrate/defer/archive decision to the Owner"
                    ),
                }
            )
    return findings


REMOTE_BRANCH_PREFIX = "refs/remotes/origin/"
BRANCH_EXCLUDE = ("origin/HEAD", "origin/main")
DEFAULT_MERGED_BRANCH_AGE_DAYS = 7


def merged_branch_findings(
    root: Path, ref: str, *, age_days: int, now_ts: float | None = None
) -> list[dict[str, Any]]:
    """Non-archive remote branches fully contained in ref (ahead=0): merge debris.

    The auto-delete flow only removes the branch a PR merged from; lanes merged
    by other means survive indefinitely (2026-07-05 sweep: six branches, all
    fully merged for three weeks). The age floor keeps just-cut zero-ahead
    branches (work that has not started yet) out of the findings.
    """
    try:
        out = _run_git(
            root, "for-each-ref", "--format=%(refname:short) %(committerdate:unix)", REMOTE_BRANCH_PREFIX
        )
    except RuntimeError:
        return []
    now = now_ts if now_ts is not None else time.time()
    findings: list[dict[str, Any]] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        name, _, stamp = line.rpartition(" ")
        if name in BRANCH_EXCLUDE or name.startswith("origin/archive/"):
            continue
        try:
            age = (now - int(stamp)) / 86400.0
        except ValueError:
            continue
        if age < age_days:
            continue
        try:
            ahead = int(_run_git(root, "rev-list", "--count", f"{ref}..{name}").strip())
        except (RuntimeError, ValueError):
            continue
        if ahead == 0:
            findings.append(
                {
                    "kind": "merged-remote-branch",
                    "branch": name,
                    "age_days": round(age, 1),
                    "detail": (
                        f"fully contained in {ref} (ahead=0) and idle for {round(age)}d; "
                        "safe to delete the remote branch"
                    ),
                }
            )
    return findings


def load_open_issues(issues_file: Path | None) -> list[dict[str, Any]] | None:
    """Open issues from --issues-file, else from gh; None when unavailable."""
    if issues_file is not None:
        payload = json.loads(issues_file.read_text(encoding="utf-8"))
        return [dict(item) for item in payload]
    result = subprocess.run(
        ["gh", "issue", "list", "--state", "open", "--limit", "200", "--json", "number,title"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    return [dict(item) for item in json.loads(result.stdout or "[]")]


def sweep(
    root: Path,
    ref: str,
    issues_file: Path | None = None,
    dangling_threshold: int = 5,
    merged_branch_age_days: int = DEFAULT_MERGED_BRANCH_AGE_DAYS,
    now_ts: float | None = None,
) -> dict[str, Any]:
    closed_in_history = closed_issue_numbers_in_history(root, ref)
    open_issues = load_open_issues(issues_file)
    findings: list[dict[str, Any]] = []
    issues_source = "unavailable"
    if open_issues is not None:
        issues_source = "issues-file" if issues_file is not None else "gh"
        for issue in open_issues:
            number = int(issue.get("number", 0))
            if number in closed_in_history:
                findings.append(
                    {
                        "kind": "stale-open-issue",
                        "number": number,
                        "title": str(issue.get("title", "")),
                        "detail": (
                            f"merged history of {ref} contains a closing keyword for #{number} "
                            "but the issue is still open; verify against main and close with "
                            "evidence or reopen the work"
                        ),
                    }
                )
    stashes = archive_stash_refs(root)
    findings.sort(key=lambda item: item["number"])
    findings.extend(
        sorted(
            dangling_lane_findings(root, ref, stashes, dangling_threshold),
            key=lambda item: -item["unmerged_commit_count"],
        )
    )
    findings.extend(
        sorted(
            merged_branch_findings(root, ref, age_days=merged_branch_age_days, now_ts=now_ts),
            key=lambda item: -item["age_days"],
        )
    )
    return {
        "schema": "agent-runtime-open-state-sweep/v1",
        "ref": ref,
        "issues_source": issues_source,
        "closing_keyword_issue_count": len(closed_in_history),
        "findings": findings,
        "archive_stash_refs": stashes,
        "archive_stash_count": len(stashes),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report open state that drifted from merged reality")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--ref", default="origin/main", help="merged-history ref (default origin/main; falls back to HEAD)")
    parser.add_argument("--issues-file", type=Path, default=None, help="JSON [{number,title}] instead of gh")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--check", action="store_true", help="exit 1 when findings exist")
    parser.add_argument(
        "--dangling-threshold",
        type=int,
        default=5,
        help="report a stash as a dangling lane when its parent chain has at least this many unmerged commits (default 5)",
    )
    parser.add_argument(
        "--merged-branch-age-days",
        type=int,
        default=DEFAULT_MERGED_BRANCH_AGE_DAYS,
        help="report a fully-merged (ahead=0) non-archive remote branch only when idle at least this many days (default 7)",
    )
    args = parser.parse_args(argv)

    root = args.root.resolve()
    ref = args.ref
    try:
        _run_git(root, "rev-parse", "--verify", "--quiet", ref)
    except RuntimeError:
        ref = "HEAD"
    report = sweep(
        root,
        ref,
        issues_file=args.issues_file,
        dangling_threshold=args.dangling_threshold,
        merged_branch_age_days=args.merged_branch_age_days,
    )

    if args.as_json:
        print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print(f"open-state-sweep: ref={report['ref']} issues_source={report['issues_source']}")
        print(f"findings={len(report['findings'])}")
        for finding in report["findings"]:
            if finding["kind"] == "stale-open-issue":
                print(f"- {finding['kind']}: #{finding['number']} {finding['title']}")
            elif finding["kind"] == "merged-remote-branch":
                print(f"- {finding['kind']}: {finding['branch']} age_days={finding['age_days']}")
            else:
                print(f"- {finding['kind']}: {finding['stash']} unmerged_commits={finding['unmerged_commit_count']}")
        print(f"archive_stash_refs={report['archive_stash_count']}")
    if report["issues_source"] == "unavailable":
        print("note: open-issue source unavailable (no gh, no --issues-file); issue sweep skipped", file=sys.stderr)
    return 1 if args.check and report["findings"] else 0


if __name__ == "__main__":
    sys.exit(main())
