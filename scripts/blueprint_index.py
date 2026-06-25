"""Pipeline status board over agents/project/blueprints/.

For each blueprint, report which artifacts exist (INTAKE / BLUEPRINT /
VISION-DIRECTION / ENABLEMENT / assets) and the next step in the
grill -> enable -> scaffold -> register-taskset flow. This is the connective
tissue that tells the Owner where each program sits and what command comes next.

Usage:
  python scripts/blueprint_index.py            # human-readable table
  python scripts/blueprint_index.py --json     # machine-readable index
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if sys.platform == "win32":  # let any non-ASCII print on a Windows console
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

SCHEMA = "agent-runtime-blueprint-index/v1"
BLUEPRINTS_REL = Path("agents/project/blueprints")


def _artifacts(slug_dir: Path) -> dict[str, bool]:
    return {
        "intake": (slug_dir / "INTAKE.md").exists(),
        "blueprint": (slug_dir / "BLUEPRINT.md").exists(),
        "vision": (slug_dir / "VISION-DIRECTION.md").exists(),
        "enablement": (slug_dir / "ENABLEMENT.md").exists(),
        "assets": (slug_dir / "assets").is_dir(),
    }


def _next_step(artifacts: dict[str, bool], slug: str) -> str:
    if not artifacts["vision"]:
        return f"run /grill to finish blueprint '{slug}'"
    if not artifacts["enablement"]:
        return f"run /enable {slug}"
    if not artifacts["assets"]:
        return f"run /scaffold {slug}"
    return "register the first taskset: python scripts/work.py new ... (Owner approves)"


def build_index(root: Path) -> dict[str, Any]:
    base = Path(root) / BLUEPRINTS_REL
    blueprints: list[dict[str, Any]] = []
    if base.is_dir():
        for entry in sorted(base.iterdir()):
            if not entry.is_dir():
                continue  # ignore README.md and other files
            artifacts = _artifacts(entry)
            blueprints.append(
                {
                    "slug": entry.name,
                    "artifacts": artifacts,
                    "next_step": _next_step(artifacts, entry.name),
                }
            )
    return {"schema": SCHEMA, "blueprints": blueprints}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Blueprint pipeline status board")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    index = build_index(args.root.resolve())
    if args.json:
        print(json.dumps(index, ensure_ascii=False, indent=2))
    else:
        if not index["blueprints"]:
            print("no blueprints yet - run /grill to create one")
        for bp in index["blueprints"]:
            have = "".join(k[0].upper() if v else "-" for k, v in bp["artifacts"].items())
            print(f"{bp['slug']:30} [{have}]  next: {bp['next_step']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
