"""Auto-resolve the derived host lock on merge (RETRO-2026-06-14 forward action #1).

`agent_runtime.lock.json` is a digest over every template file, so concurrent template
branches always collide on it (COMPOUND-2026-06-14-003 — PR #135 went DIRTY three times
during the knowledge-stack wave, each needing a manual re-merge + `lock --write`).

Why not regenerate *inside* a merge driver: git runs merge drivers while it holds the
merge in progress, and the lock can only be rebuilt from the *fully merged* template
tree — which mid-merge is neither in the working tree nor reachable without spawning git
(which deadlocks against the in-progress merge, as testing on Windows confirmed). So this
splits the job:

  1. a trivial `true` merge driver keeps "ours" and suppresses the lock conflict — the
     merge completes with no markers and no subprocess, so it cannot deadlock; and
  2. a `post-merge` hook regenerates the authoritative lock afterwards, when the working
     tree is fully materialised, and stages it.

Net: `git merge origin/main` completes cleanly and leaves the correct, staged lock to
fold into the commit — no conflict markers, no manual `lock --write`.

The post-merge regenerator ships as the committed `.githooks/post-merge`; `--install`
sets the merge driver and `core.hooksPath=.githooks` to activate it (alongside the
existing pre-commit hook).

Usage (one-time setup):   python scripts/lock_merge_driver.py --install
Usage (run by the hook):  python scripts/lock_merge_driver.py post-merge
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

DRIVER_NAME = "arlock-keepours"
LOCK_NAME = "agent_runtime.lock.json"
PRE_COMMIT_HOOK = Path(".githooks") / "pre-commit"


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd or REPO_ROOT), capture_output=True, text=True)


def _host_roots() -> list[Path]:
    """Every tracked agent_runtime.lock.json maps to a host root (its parent dir)."""
    out = _git("ls-files", f"*{LOCK_NAME}")
    return [REPO_ROOT / Path(p).parent for p in out.stdout.split() if p.strip()]


def _uses_posix_modes(posix: bool | None) -> bool:
    return os.name != "nt" if posix is None else posix


def _open_pre_commit_fd(repo_root: Path) -> tuple[int, os.stat_result] | None:
    """Securely open the hook without following its directory or final entry."""
    if not all(
        hasattr(os, name)
        for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK", "fchmod")
    ):
        return None
    close_on_exec = getattr(os, "O_CLOEXEC", 0)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | close_on_exec
    hook_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | close_on_exec
    try:
        hooks_fd = os.open(str(Path(repo_root) / PRE_COMMIT_HOOK.parent), directory_flags)
    except (OSError, TypeError, NotImplementedError):
        return None
    try:
        try:
            hook_fd = os.open(PRE_COMMIT_HOOK.name, hook_flags, dir_fd=hooks_fd)
        except (OSError, TypeError, NotImplementedError):
            return None
    finally:
        os.close(hooks_fd)
    try:
        metadata = os.fstat(hook_fd)
    except OSError:
        os.close(hook_fd)
        return None
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        os.close(hook_fd)
        return None
    return hook_fd, metadata


def is_pre_commit_executable(
    repo_root: Path | None = None,
    *,
    posix: bool | None = None,
) -> bool:
    """Return whether the configured hook is ready for POSIX Git execution.

    Windows does not use POSIX execute bits, so it is ready without chmod.
    Symlinks and other non-regular entries are rejected to avoid chmod outside
    the checkout through a crafted hook path.
    """
    if not _uses_posix_modes(posix):
        return True
    opened = _open_pre_commit_fd(Path(repo_root or REPO_ROOT))
    if opened is None:
        return False
    hook_fd, metadata = opened
    try:
        return bool(metadata.st_mode & stat.S_IXUSR)
    finally:
        os.close(hook_fd)


def repair_pre_commit_executable(
    repo_root: Path | None = None,
    *,
    posix: bool | None = None,
) -> bool:
    """Idempotently add execute bits to a regular POSIX pre-commit hook.

    Returns True only when the mode changed. Missing hooks and non-regular
    entries are left untouched; chmod errors propagate to installer callers.
    """
    if not _uses_posix_modes(posix):
        return False
    opened = _open_pre_commit_fd(Path(repo_root or REPO_ROOT))
    if opened is None:
        return False
    hook_fd, metadata = opened
    try:
        current = stat.S_IMODE(metadata.st_mode)
        desired = current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        if current == desired:
            return False
        os.fchmod(hook_fd, desired)
        return True
    finally:
        os.close(hook_fd)


def regenerate(host_root: Path) -> bool:
    """Rewrite host_root/agent_runtime.lock.json from the current template tree.
    Returns True if the file changed. Pure filesystem — no git, so no deadlock."""
    from agent_runtime import lock

    lock_path = Path(host_root) / LOCK_NAME
    before = lock_path.read_text(encoding="utf-8") if lock_path.exists() else None
    plan = lock.build_lock_plan(Path(host_root))
    content = json.dumps(plan.record, indent=2, sort_keys=True) + "\n"
    if content == before:
        return False
    lock_path.write_text(content, encoding="utf-8")
    return True


TEMPLATE_PREFIX = "src/agent_runtime/templates/"


def pre_commit() -> int:
    """Regenerate + stage host locks, but only when a template file is staged.

    The host lock digests the template tree, so any template commit that does
    not regenerate it fails test_regenerate_noop_when_current one CI round-trip
    later (casebook: template-stale-host-lock). Gating on staged template paths
    keeps ordinary commits fast. Best-effort by design: with partial staging
    the regen reads the working tree, and CI remains the authority.
    """
    out = _git("diff", "--cached", "--name-only")
    staged = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    if not any(path.startswith(TEMPLATE_PREFIX) for path in staged):
        return 0
    return post_merge()


def post_merge() -> int:
    """Regenerate every host lock and stage the ones that changed. Runs after the merge
    has completed, so the working tree is fully materialised and `git add` is safe."""
    changed: list[Path] = []
    for root in _host_roots():
        try:
            if regenerate(root):
                changed.append(root / LOCK_NAME)
        except Exception as exc:  # never let a hook break the user's merge
            print(f"lock post-merge: skipped {root}: {type(exc).__name__}: {exc}")
    for path in changed:
        _git("add", "--", str(path))
        print(f"lock post-merge: regenerated + staged {path.relative_to(REPO_ROOT).as_posix()}")
    if not changed:
        print("lock post-merge: locks already current")
    return 0


def install(repo_root: Path | None = None, *, posix: bool | None = None) -> int:
    """Register the keep-ours merge driver and activate the committed .githooks
    (which carry the post-merge regenerator). Idempotent."""
    cwd = repo_root or REPO_ROOT

    if _uses_posix_modes(posix):
        try:
            repaired = repair_pre_commit_executable(cwd, posix=posix)
        except OSError as exc:
            print(
                f"lock-merge-driver: not installed: pre-commit chmod failed:"
                f" {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return 1
        if not is_pre_commit_executable(cwd, posix=posix):
            print(
                "lock-merge-driver: not installed: POSIX pre-commit hook is"
                " missing, linked, non-regular, or not executable",
                file=sys.stderr,
            )
            return 1
        hook_state = "pre-commit executable" + (" (repaired)" if repaired else "")
    else:
        hook_state = "pre-commit POSIX mode not required"

    def _cfg(key: str, value: str) -> None:
        subprocess.run(["git", "config", key, value], cwd=str(cwd), check=True)

    _cfg(f"merge.{DRIVER_NAME}.name", "Keep ours; the post-merge hook regenerates the lock")
    _cfg(f"merge.{DRIVER_NAME}.driver", "true")
    _cfg("core.hooksPath", ".githooks")
    print(
        f"lock-merge-driver: installed merge.{DRIVER_NAME}=true"
        f" + core.hooksPath=.githooks; {hook_state}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Runtime host-lock merge automation")
    parser.add_argument("--install", action="store_true", help="register the merge driver + post-merge hook")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("post-merge", help="(run by the hook) regenerate + stage host locks")
    sub.add_parser("pre-commit", help="(run by the hook) regenerate + stage host locks when templates are staged")

    args = parser.parse_args(argv)
    if args.install:
        return install()
    if args.command == "post-merge":
        return post_merge()
    if args.command == "pre-commit":
        return pre_commit()
    parser.error("nothing to do: pass --install or `post-merge`")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
