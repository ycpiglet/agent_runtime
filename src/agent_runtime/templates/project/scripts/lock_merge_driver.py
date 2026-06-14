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
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

DRIVER_NAME = "arlock-keepours"
LOCK_NAME = "agent_runtime.lock.json"


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd or REPO_ROOT), capture_output=True, text=True)


def _host_roots() -> list[Path]:
    """Every tracked agent_runtime.lock.json maps to a host root (its parent dir)."""
    out = _git("ls-files", f"*{LOCK_NAME}")
    return [REPO_ROOT / Path(p).parent for p in out.stdout.split() if p.strip()]


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


def install(repo_root: Path | None = None) -> int:
    """Register the keep-ours merge driver and activate the committed .githooks
    (which carry the post-merge regenerator). Idempotent."""
    cwd = repo_root or REPO_ROOT

    def _cfg(key: str, value: str) -> None:
        subprocess.run(["git", "config", key, value], cwd=str(cwd), check=True)

    _cfg(f"merge.{DRIVER_NAME}.name", "Keep ours; the post-merge hook regenerates the lock")
    _cfg(f"merge.{DRIVER_NAME}.driver", "true")
    _cfg("core.hooksPath", ".githooks")
    print(f"lock-merge-driver: installed merge.{DRIVER_NAME}=true + core.hooksPath=.githooks")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agent Runtime host-lock merge automation")
    parser.add_argument("--install", action="store_true", help="register the merge driver + post-merge hook")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("post-merge", help="(run by the hook) regenerate + stage host locks")

    args = parser.parse_args(argv)
    if args.install:
        return install()
    if args.command == "post-merge":
        return post_merge()
    parser.error("nothing to do: pass --install or `post-merge`")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
