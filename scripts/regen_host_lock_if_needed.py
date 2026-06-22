"""Template-to-lock drift catcher (prevention guard).

Detects when the committed host lock is stale with respect to the current template
tree WITHOUT writing anything (--check), or regenerates it in place (--write).

Use case: after editing any file under src/agent_runtime/templates/ the developer
must regenerate tests/fixtures/host/agent_runtime.lock.json.  If they forget, the
test_lock_merge_driver.test_regenerate_noop_when_current test reds in CI.  This
script makes the drift visible pre-CI with a clear actionable message.

Strategy for dry-run comparison
--------------------------------
lock_merge_driver.regenerate() writes to disk.  We need a non-destructive variant.
Approach: copy the host root to a tmp dir, regenerate there, then diff the
would-be content against the committed lock.  This avoids modifying the repo and
avoids adding a dry_run parameter to lock_merge_driver (which would change its
public contract).

Usage
-----
    python scripts/regen_host_lock_if_needed.py --check
    python scripts/regen_host_lock_if_needed.py --check --host-root path/to/host
    python scripts/regen_host_lock_if_needed.py --write
    python scripts/regen_host_lock_if_needed.py --write --host-root path/to/host
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

LOCK_NAME = "agent_runtime.lock.json"
DEFAULT_HOST_ROOT = REPO_ROOT / "tests" / "fixtures" / "host"


def _compute_would_be_lock(host_root: Path) -> str:
    """Return what the lock content WOULD be if regenerated, without touching disk."""
    import lock_merge_driver as lmd

    with tempfile.TemporaryDirectory() as tmp:
        tmp_host = Path(tmp) / "host"
        shutil.copytree(host_root, tmp_host)
        lmd.regenerate(tmp_host)
        return (tmp_host / LOCK_NAME).read_text(encoding="utf-8")


def check(host_root: Path) -> int:
    """Return 0 if the lock is current, 1 if stale."""
    lock_path = host_root / LOCK_NAME

    if not lock_path.exists():
        print(
            f"ERROR: {lock_path} does not exist.\n"
            f"Run: python scripts/regen_host_lock_if_needed.py --write",
            file=sys.stderr,
        )
        return 1

    committed = lock_path.read_text(encoding="utf-8")
    would_be = _compute_would_be_lock(host_root)

    if committed == would_be:
        print(f"OK: {lock_path} is up to date.")
        return 0

    # Show a minimal diff hint (keys that differ at top level).
    try:
        committed_obj = json.loads(committed)
        would_be_obj = json.loads(would_be)
        if committed_obj.get("installed", {}).get("template_digest") != would_be_obj.get(
            "installed", {}
        ).get("template_digest"):
            print(
                f"STALE: template_digest mismatch in {lock_path}",
                file=sys.stderr,
            )
    except json.JSONDecodeError:
        pass

    print(
        f"STALE: {lock_path} is out of date with the current template tree.\n"
        f"Run: python scripts/regen_host_lock_if_needed.py --write",
        file=sys.stderr,
    )
    return 1


def write(host_root: Path) -> int:
    """Regenerate the committed host lock in place. Returns 0 on success."""
    import lock_merge_driver as lmd

    changed = lmd.regenerate(host_root)
    if changed:
        print(f"UPDATED: {host_root / LOCK_NAME} regenerated.")
    else:
        print(f"OK: {host_root / LOCK_NAME} was already up to date.")
    return 0


def main(argv: list[str] | None = None) -> int:
    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    parser = argparse.ArgumentParser(
        description="Detect or fix template->lock drift in the committed host fixture."
    )
    parser.add_argument(
        "--host-root",
        type=Path,
        default=DEFAULT_HOST_ROOT,
        help=f"Path to the host root containing {LOCK_NAME} (default: {DEFAULT_HOST_ROOT})",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help=f"Exit 1 if {LOCK_NAME} is stale; print --write hint.",
    )
    mode.add_argument(
        "--write",
        action="store_true",
        help=f"Regenerate {LOCK_NAME} from the current template tree.",
    )

    args = parser.parse_args(argv)
    if args.check:
        return check(args.host_root)
    return write(args.host_root)


if __name__ == "__main__":
    raise SystemExit(main())
