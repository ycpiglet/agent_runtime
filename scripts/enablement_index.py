"""Build a machine-readable index of skills for the /enable skill.

Scans `skills/*/SKILL.md` and extracts each skill's frontmatter (name, description,
triggers) so `/enable` can recommend skills by exact name + description instead of
eyeballing the directory. Generated at runtime (printed to stdout) — there is no
committed snapshot, so the index can never go stale.

Usage:
  python scripts/enablement_index.py --json        # print the index as JSON
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "agent-runtime-enablement-index/v1"


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Minimal YAML-frontmatter parse (no external deps): name/description/version
    scalars and the ``triggers:`` list."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    data: dict[str, Any] = {"triggers": []}
    in_triggers = False
    for line in text[3:end].splitlines():
        if line.startswith("name:"):
            data["name"] = line.split(":", 1)[1].strip()
            in_triggers = False
        elif line.startswith("description:"):
            data["description"] = line.split(":", 1)[1].strip()
            in_triggers = False
        elif line.startswith("version:"):
            data["version"] = line.split(":", 1)[1].strip()
            in_triggers = False
        elif line.startswith("triggers:"):
            in_triggers = True
        elif in_triggers and line.lstrip().startswith("- "):
            data["triggers"].append(line.lstrip()[2:].strip())
        elif line and not line.startswith((" ", "\t")):
            in_triggers = False
    return data


def build_index(root: Path) -> dict[str, Any]:
    skills_dir = Path(root) / "skills"
    skills: list[dict[str, Any]] = []
    if skills_dir.is_dir():
        for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
            fm = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            if not fm.get("name"):
                continue
            skills.append(
                {
                    "name": fm["name"],
                    "description": fm.get("description", ""),
                    "triggers": fm.get("triggers", []),
                    "path": skill_md.parent.relative_to(Path(root)).as_posix(),
                }
            )
    return {"schema": SCHEMA, "skills": skills}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the enablement skill index")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", help="print the index as JSON")
    args = parser.parse_args(argv)

    index = build_index(args.root.resolve())
    if args.json:
        print(json.dumps(index, ensure_ascii=False, indent=2))
    else:
        for skill in index["skills"]:
            print(f"{skill['name']:20} {skill['description'][:80]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
