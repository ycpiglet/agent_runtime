"""Org model gate: resolve work-item owner/team against agents/project/ORG-MODEL.yml.

Watch-level by default (exit 0); `--enforce` exits 1 on any unresolved owner/team.
Aliases absorb historical free-text owner drift (lead_engineer vs lead-engineer).
Spec: docs/superpowers/specs/2026-06-14-agent-org-delegation-model-design.md (Sec A).
"""
from __future__ import annotations
import argparse
import glob
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "agents" / "project" / "ORG-MODEL.yml"
DEFAULT_GLOB = "agents/lead_engineer/tasks/TASK-*.md"


def _coerce(v: str):
    v = v.strip().strip("'\"")
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def parse_frontmatter(text: str) -> dict:
    """Stdlib frontmatter parser (the repo + CI run PyYAML-free; gates parse by hand)."""
    meta: dict = {}
    if not text.startswith("---"):
        return meta
    current_list = None
    for raw in text.splitlines()[1:]:
        line = raw.rstrip()
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") and current_list:
            meta.setdefault(current_list, []).append(_coerce(line[4:]))
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val == "":
            meta[key] = []
            current_list = key
        elif val.startswith("[") and val.endswith("]"):
            meta[key] = [_coerce(x) for x in val[1:-1].split(",") if x.strip()]
            current_list = None
        else:
            meta[key] = _coerce(val)
            current_list = None
    return meta


def _coerce_om(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        return [x.strip() for x in v[1:-1].split(",") if x.strip()]
    return v.strip("'\"")


def parse_org_model(text: str) -> dict:
    """Stdlib parser for ORG-MODEL.yml's fixed structure (no PyYAML)."""
    reg: dict = {"teams": [], "roles": [], "tiers": []}
    section = None
    cur = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()   # ORG-MODEL values contain no '#'
        if not line.strip():
            continue
        if not line[0].isspace():              # top-level key
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            section = cur = None
            if key in ("teams", "roles"):
                section = key
            elif val.startswith("[") and val.endswith("]"):
                reg[key] = [x.strip() for x in val[1:-1].split(",") if x.strip()]
            elif val:
                reg[key] = val
        elif section and line.lstrip().startswith("- "):
            cur = {}
            reg[section].append(cur)
            rest = line.lstrip()[2:]
            if ":" in rest:
                k, _, v = rest.partition(":")
                cur[k.strip()] = _coerce_om(v)
        elif section and cur is not None and ":" in line:
            k, _, v = line.strip().partition(":")
            cur[k.strip()] = _coerce_om(v)
    return reg


def load_registry(path: Path = REGISTRY) -> dict:
    return parse_org_model(path.read_text(encoding="utf-8"))


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
    return parse_frontmatter(path.read_text(encoding="utf-8", errors="replace")).get("owner")


def cmd_check(paths: list[str], *, enforce: bool) -> int:
    try:
        reg = load_registry()
    except Exception as exc:  # fail-soft: a watch check must never block governance
        level = "block" if enforce else "watch"
        print(f"org-model: {level} registry-load-error: {exc}")
        return 1 if enforce else 0
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
