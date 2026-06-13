"""SessionStart hook: auto-recover provably-dead claims (best-effort, non-blocking).

Runs ``claim_reaper`` at session start so a deadlock left by a dead worker is
cleared before new work begins. Auto-apply (recover provably-dead claims) is ON
by default and can be tuned via environment variables:

  AGENT_RUNTIME_REAPER_DISABLE=1        skip the hook entirely
  AGENT_RUNTIME_REAPER_AUTO_APPLY=0     detect+report only (no state change)
  AGENT_RUNTIME_REAPER_GRACE_SECONDS=N  override grace seconds (default 600)

Always exits 0: a reaper failure must never block a session from starting.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def _truthy(value: str | None, default: bool) -> bool:
    if value is None or value == "":
        return default
    return str(value).strip().lower() not in ("0", "false", "no", "off")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SessionStart claim reaper (best-effort)")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args, _unknown = parser.parse_known_args(argv)
    try:
        if _truthy(os.environ.get("AGENT_RUNTIME_REAPER_DISABLE"), False):
            return 0
        import claim_reaper

        apply = _truthy(os.environ.get("AGENT_RUNTIME_REAPER_AUTO_APPLY"), True)
        report = claim_reaper.sweep(args.root, apply=apply)
        acted = report["reaped"] if apply else report["would_reap"]
        if acted:
            verb = "reaped" if apply else "would-reap (set AGENT_RUNTIME_REAPER_AUTO_APPLY=1 to recover)"
            ids = ", ".join(entry["claim_id"] for entry in acted)
            print(f"claim-reaper: {verb} {len(acted)} dead claim(s): {ids}")
        # Silent when there is nothing to do, to avoid SessionStart noise.
    except Exception as exc:  # noqa: BLE001 - best-effort: never block session start
        print(f"claim-reaper: skipped ({exc!r})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
