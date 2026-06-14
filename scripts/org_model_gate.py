"""Org model gate: resolve work-item owner/team against agents/project/ORG-MODEL.yml.

Watch-level by default (exit 0); `--enforce` exits 1 on any unresolved owner/team.
Aliases absorb historical free-text owner drift (lead_engineer vs lead-engineer).
Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (Sec A).
"""
from __future__ import annotations
import argparse
import glob
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "agents" / "project" / "ORG-MODEL.yml"
DEFAULT_GLOB = "agents/lead_engineer/tasks/TASK-*.md"


def load_registry(path: Path = REGISTRY) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _alias_map(reg: dict) -> dict[str, dict]:
    m: dict[str, dict] = {}
    for role in reg["roles"]:
        for key in [role["id"], *role.get("aliases", [])]:
            m[str(key).strip().lower()] = role
    return m


def resolve_owner(value: str | None, reg: dict) -> dict | None:
    if not value:
        return None
    return _alias_map(reg).get(str(value).strip().lower())


def resolve_team(team_id: str | None, reg: dict) -> dict | None:
    if not team_id:
        return None
    target = str(team_id).strip().lower()
    for t in reg.get("teams", []):
        if t["id"] == target:
            return t
    return None


def _front_owner(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    fm = yaml.safe_load(text[3:end]) if end != -1 else {}
    return (fm or {}).get("owner")


def cmd_check(paths: list[str], *, enforce: bool) -> int:
    reg = load_registry()
    files: list[Path] = []
    for p in paths:
        if any(c in p for c in "*?"):
            files.extend(Path(x) for x in glob.glob(p))
        else:
            files.append(Path(p))
    unresolved = []
    for f in files:
        if not f.exists():
            continue
        owner = _front_owner(f)
        if owner is not None and resolve_owner(owner, reg) is None:
            unresolved.append((f, owner))
    for f, owner in unresolved:
        print(f"org-model: unresolved owner '{owner}' in {f}")
    level = "block" if enforce else "watch"
    print(f"org-model: {level} unresolved={len(unresolved)} checked={len(files)}")
    return 1 if (enforce and unresolved) else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--enforce", action="store_true")
    ap.add_argument("paths", nargs="*", default=[DEFAULT_GLOB])
    a = ap.parse_args(argv)
    paths = a.paths or [DEFAULT_GLOB]
    return cmd_check(paths, enforce=a.enforce)


if __name__ == "__main__":
    raise SystemExit(main())
