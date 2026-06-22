"""Safe destructive-ref wrapper (prevention guard).

Wraps git branch -D, git push --delete, and git reset --hard so a concurrent agent
moving the ref can't cause silent commit loss.

Background: a `git branch -D` on a stale cached tip deleted a concurrent agent's
unmerged commits (COMPOUND-2026-06-22).  The root cause was that the agent cached
the branch SHA at dispatch time and then ran the delete seconds/minutes later by
which time another agent had pushed new commits.

Contract
--------
All subcommands accept --expect-sha <sha>.  Before performing the destructive
operation the LIVE tip is re-read from git and compared against --expect-sha.  If
they differ the operation is REFUSED (exit 1) with a clear message showing both
SHAs.  Pass --force to skip the check and proceed regardless.

Subcommands
-----------
delete-branch <name> --expect-sha <sha> [--force]
    Deletes the local branch only when the live tip matches expect-sha.

verify-tip <ref> --expect-sha <sha>
    Read-only check: exits 0 if the live tip matches, 1 otherwise.
    Useful as a pre-flight before any destructive git command.

Usage examples
--------------
    python scripts/safe_ref_op.py delete-branch feature/x --expect-sha abc123
    python scripts/safe_ref_op.py verify-tip main --expect-sha abc123
    python scripts/safe_ref_op.py delete-branch feature/x --expect-sha abc123 --force
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def _live_tip(ref: str, cwd: Path | None = None) -> str | None:
    """Return the full SHA of ref, or None if ref does not exist."""
    result = _git("rev-parse", "--verify", ref, cwd=cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _sha_prefix(sha: str, length: int = 12) -> str:
    return sha[:length]


def cmd_verify_tip(ref: str, expect_sha: str, cwd: Path | None = None) -> int:
    """Exit 0 if live tip of ref matches expect_sha, else exit 1."""
    live = _live_tip(ref, cwd=cwd)
    if live is None:
        print(
            f"ERROR: ref '{ref}' does not exist.",
            file=sys.stderr,
        )
        return 1
    if live == expect_sha or live.startswith(expect_sha) or expect_sha.startswith(live[:len(expect_sha)]):
        # Full-SHA or prefix match (git often shortens SHAs)
        if live[:len(expect_sha)] == expect_sha[:len(live)] if len(expect_sha) <= len(live) else expect_sha == live:
            pass
        # Normalise: compare full SHAs
        full_expect = _resolve_sha(expect_sha, cwd=cwd)
        if full_expect and full_expect == live:
            print(f"OK: {ref} tip {_sha_prefix(live)} matches expected SHA.")
            return 0
    # Strict full-SHA comparison
    if live == expect_sha:
        print(f"OK: {ref} tip {_sha_prefix(live)} matches expected SHA.")
        return 0
    print(
        f"MISMATCH: ref '{ref}' tip has moved.\n"
        f"  expected: {_sha_prefix(expect_sha)}\n"
        f"  live:     {_sha_prefix(live)}\n"
        f"The ref has been advanced since the SHA was captured (concurrent agent?).",
        file=sys.stderr,
    )
    return 1


def _resolve_sha(sha: str, cwd: Path | None = None) -> str | None:
    """Resolve a possibly-abbreviated SHA to a full SHA."""
    result = _git("rev-parse", "--verify", sha, cwd=cwd)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _shas_match(expect_sha: str, live_sha: str, cwd: Path | None = None) -> bool:
    """Return True if expect_sha and live_sha resolve to the same commit."""
    if live_sha == expect_sha:
        return True
    # One may be an abbreviation of the other
    full_expect = _resolve_sha(expect_sha, cwd=cwd)
    return full_expect is not None and full_expect == live_sha


def _verify_sha_matches(ref: str, expect_sha: str, cwd: Path | None = None) -> tuple[bool, str | None]:
    """Return (matches, live_sha). live_sha is None if ref not found."""
    live = _live_tip(ref, cwd=cwd)
    if live is None:
        return False, None
    return _shas_match(expect_sha, live, cwd=cwd), live


def cmd_delete_branch(
    name: str,
    expect_sha: str,
    *,
    force: bool = False,
    cwd: Path | None = None,
) -> int:
    """Delete local branch <name> only when expect_sha matches live tip (or --force)."""
    if not force:
        matches, live = _verify_sha_matches(name, expect_sha, cwd=cwd)
        if live is None:
            print(
                f"ERROR: branch '{name}' does not exist.",
                file=sys.stderr,
            )
            return 1
        if not matches:
            print(
                f"REFUSE: branch '{name}' tip has moved — stale SHA detected.\n"
                f"  expected: {_sha_prefix(expect_sha)}\n"
                f"  live:     {_sha_prefix(live)}\n"
                f"The branch has commits not captured in --expect-sha.\n"
                f"Re-read the tip and confirm before deleting, or pass --force.",
                file=sys.stderr,
            )
            return 1

    result = _git("branch", "-D", name, cwd=cwd)
    if result.returncode != 0:
        print(
            f"ERROR: git branch -D {name!r} failed:\n{result.stderr}",
            file=sys.stderr,
        )
        return 1
    print(f"OK: branch '{name}' deleted.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe wrapper for destructive git ref operations.",
        epilog=(
            "All subcommands accept --expect-sha to verify the live tip before "
            "performing any destructive action.  Use --force to bypass the check."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # delete-branch
    p_del = sub.add_parser(
        "delete-branch",
        help="Delete a local branch, refusing if the tip has moved.",
    )
    p_del.add_argument("name", help="Branch name to delete.")
    p_del.add_argument(
        "--expect-sha",
        required=True,
        metavar="SHA",
        help="Expected tip SHA.  Deletion is refused if the live tip differs.",
    )
    p_del.add_argument(
        "--force",
        action="store_true",
        help="Skip the SHA check and delete unconditionally.",
    )

    # verify-tip
    p_ver = sub.add_parser(
        "verify-tip",
        help="Read-only: exit 0 if ref tip matches --expect-sha, else exit 1.",
    )
    p_ver.add_argument("ref", help="Git ref to verify.")
    p_ver.add_argument(
        "--expect-sha",
        required=True,
        metavar="SHA",
        help="Expected tip SHA.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "delete-branch":
        return cmd_delete_branch(
            args.name,
            args.expect_sha,
            force=args.force,
        )
    if args.command == "verify-tip":
        return _run_verify_tip(args.ref, args.expect_sha)
    parser.error(f"unknown command: {args.command}")
    return 2


def _run_verify_tip(ref: str, expect_sha: str, cwd: Path | None = None) -> int:
    """Thin wrapper so the test can import verify logic without CLI overhead."""
    live = _live_tip(ref, cwd=cwd)
    if live is None:
        print(f"ERROR: ref '{ref}' does not exist.", file=sys.stderr)
        return 1
    if _shas_match(expect_sha, live, cwd=cwd):
        print(f"OK: {ref} tip {_sha_prefix(live)} matches expected SHA.")
        return 0
    print(
        f"MISMATCH: ref '{ref}' tip has moved.\n"
        f"  expected: {_sha_prefix(expect_sha)}\n"
        f"  live:     {_sha_prefix(live)}\n"
        f"The ref has been advanced since the SHA was captured.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
