#!/usr/bin/env python3
"""Agent context packet builder (TASK-084).

Builds a deterministic, role-scoped context packet for an agent that the
orchestrator wants to spawn or call. Output is markdown (default) or JSON.

Reads:
  - agents/roles.yml         role registry (canonical)
  - agents/project/*         host-owned project context overlay, if present
  - agents/lead_engineer/STATUS.md  current state
  - agents/lead_engineer/tasks/TASK-NNN-*.md (when --task is given)
  - related BTC/BUG (later — out of TASK-084 scope, follow-up)

Usage:
  python scripts/agent_context_packet.py --role qa --task TASK-085
  python scripts/agent_context_packet.py --role lead-engineer --task TASK-090 --format json
  python scripts/agent_context_packet.py --role-list
  python scripts/agent_context_packet.py --role audit --task TASK-086 --check-only

The packet is intentionally minimal — it lists the documents the role
*must* read and *must not* read, plus the active TASK summary and
verification commands. It does NOT inline the documents themselves
(file paths are stable, the receiving LLM reads them itself).

This is the canonical answer to "what does role X need to start working
on TASK-NNN?" — same input always yields the same packet.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
ROLES_YML = ROOT / "agents" / "roles.yml"
TASKS_DIR = ROOT / "agents" / "lead_engineer" / "tasks"
PROJECT_CONTEXT_README = "agents/project/README.md"
PROJECT_CONTEXT_EXAMPLE = "agents/project/PROJECT-CONTEXT.example.yml"
PROJECT_CONTEXT_FILES = (
    "agents/project/PROJECT-CONTEXT.yml",
    "agents/project/PROJECT-CONTEXT.yaml",
    "agents/project/PROJECT-CONTEXT.md",
    "agents/project/CONTEXT-SOURCES.yml",
    "agents/project/CONTEXT-SOURCES.yaml",
    "agents/project/DATASET-CATALOG.yml",
    "agents/project/DATASET-CATALOG.yaml",
    "agents/project/EVAL-POLICY.yml",
    "agents/project/EVAL-POLICY.yaml",
    "agents/project/SKILL-GOVERNANCE.md",
    "agents/project/VISION.md",
    "agents/project/ROADMAP.md",
    "agents/project/ORG.md",
    "agents/project/TEAMS.md",
    "agents/project/LINKS.md",
)
CONTEXT_SOURCE_CANDIDATES = (
    "agents/project/CONTEXT-SOURCES.yml",
    "agents/project/CONTEXT-SOURCES.yaml",
)
CONTEXT_SOURCE_REQUIRED_FIELDS = (
    "source_tier",
    "id",
    "owner",
    "access_level",
    "lineage",
    "freshness_sla",
)
CONTEXT_SOURCE_REQUIRED_METADATA = (
    "owner",
    "updated_at",
    "source_tier",
    "access_level",
    "lineage",
    "confidence",
)
CONTEXT_QUERY_REQUIRED_FIELDS = (
    "question",
    "business_scope",
    "source_tier",
    "time_window",
    "tolerance",
    "ambiguity_level",
    "access_check",
    "query_tolerance",
    "tradeoff_preference",
)
CONTEXT_SOURCE_FOOTER_FIELDS = (
    "source_tier",
    "source",
    "confidence",
    "access_level",
    "ambiguity_score",
    "freshness_sla",
    "reviewer_verdict",
    "lineage",
)
CONTEXT_ROUTING_OUTCOMES = (
    "clarify_required",
    "reviewer_review",
    "hold_for_query_contract",
    "correction_path",
)
CONTEXT_SCORING_FIELDS = (
    "ambiguity_score",
    "ssot_alignment_score",
)


# ---------- minimal yaml loader ----------
# We avoid pulling pyyaml — the schema is small and stable.

def _strip_yaml_comment(line: str) -> str:
    """Strip trailing # comment unless inside quotes (naive)."""
    in_s = False
    in_d = False
    out = []
    for ch in line:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        if ch == "#" and not in_s and not in_d:
            break
        out.append(ch)
    return "".join(out).rstrip()


def load_roles() -> dict:
    """Tiny YAML reader tailored to agents/roles.yml structure.

    Supports: top-level scalars, top-level `roles:` list of mappings with
    scalar / inline-list / block-list / `|`-block values. Nothing else.
    """
    if not ROLES_YML.exists():
        raise SystemExit(f"missing role registry: {ROLES_YML.relative_to(ROOT)}")
    raw = ROLES_YML.read_text(encoding="utf-8").splitlines()

    out: dict = {"roles": []}
    i = 0
    current_role: dict | None = None
    current_key: str | None = None
    block_indent: int | None = None
    block_acc: list[str] | None = None

    def flush_block() -> None:
        nonlocal block_acc, current_key, block_indent
        if current_role is not None and current_key is not None and block_acc is not None:
            current_role[current_key] = "\n".join(block_acc).rstrip()
        block_acc = None
        current_key = None
        block_indent = None

    while i < len(raw):
        line = raw[i]
        stripped = _strip_yaml_comment(line)
        if block_acc is not None:
            if not stripped.strip():
                block_acc.append("")
                i += 1
                continue
            indent = len(line) - len(line.lstrip(" "))
            if block_indent is None:
                block_indent = indent
            if indent < block_indent:
                flush_block()
                continue  # reprocess this line
            block_acc.append(line[block_indent:])
            i += 1
            continue

        if not stripped.strip():
            i += 1
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        text = stripped.strip()

        # Top-level scalar (version: 1, schema: ..., updated_at: ...)
        if indent == 0 and ":" in text and not text.startswith("-"):
            key, _, val = text.partition(":")
            key = key.strip()
            val = val.strip()
            if key == "roles" and val == "":
                # start of list
                i += 1
                continue
            out[key] = _parse_scalar(val)
            i += 1
            continue

        # role list item: `  - id: lead-engineer`
        if indent == 2 and text.startswith("- "):
            current_role = {}
            out["roles"].append(current_role)
            tail = text[2:]
            if ":" in tail:
                k, _, v = tail.partition(":")
                current_role[k.strip()] = _parse_scalar(v.strip())
            i += 1
            continue

        # role property: `    aliases: [...]` or `    required_inputs:`
        if current_role is not None and indent == 4 and ":" in text:
            k, _, v = text.partition(":")
            k = k.strip()
            v = v.strip()
            if v == "":
                # could be a list or a `|` block on next lines
                # peek next non-blank
                j = i + 1
                while j < len(raw) and not raw[j].strip():
                    j += 1
                if j < len(raw):
                    nxt = raw[j]
                    nxt_indent = len(nxt) - len(nxt.lstrip(" "))
                    nxt_text = nxt.lstrip(" ")
                    if nxt_indent >= 6 and nxt_text.startswith("- "):
                        # block list
                        items: list[str] = []
                        i = j
                        while i < len(raw):
                            ln = raw[i]
                            if not ln.strip():
                                i += 1
                                continue
                            ind = len(ln) - len(ln.lstrip(" "))
                            t = ln.lstrip(" ")
                            if ind < 6 or not t.startswith("- "):
                                break
                            items.append(_parse_scalar(t[2:].strip()))
                            i += 1
                        current_role[k] = items
                        continue
                    if nxt_indent >= 6 and v == "" and False:
                        pass  # placeholder — block scalar handled below
                # empty list (no children)
                current_role[k] = []
                i += 1
                continue
            if v == "|":
                current_key = k
                block_acc = []
                block_indent = None
                i += 1
                continue
            current_role[k] = _parse_scalar(v)
            i += 1
            continue

        i += 1

    if block_acc is not None:
        flush_block()

    return out


def _parse_scalar(v: str):
    v = v.strip()
    if not v:
        return ""
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(s) for s in _split_inline_list(inner)]
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1]
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1]
    if v in {"true", "True"}:
        return True
    if v in {"false", "False"}:
        return False
    try:
        if "." in v:
            return float(v)
        return int(v)
    except ValueError:
        return v


def _split_inline_list(s: str) -> list[str]:
    """Split `a, b, c` honoring nothing fancier."""
    return [p.strip() for p in s.split(",") if p.strip()]


# ---------- packet builder ----------

@dataclass
class Packet:
    role_id: str
    aliases: list[str]
    task_id: str | None
    task_summary: dict | None
    project_context: list[str]
    required_inputs: list[str]
    forbidden_inputs: list[str]
    output_contract: list[str]
    audit_gate: bool
    bootstrap_doc: str
    skill_file: str
    verification_commands: list[str]
    notes: str
    context_source_metadata: list[str]
    context_source_warnings: list[str]
    required_routing_fields: list[str]
    definition_policy: str | None
    source_footer_fields: list[str]
    routing_outcomes: list[str]
    scoring_fields: list[str]

    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "aliases": self.aliases,
            "task_id": self.task_id,
            "task_summary": self.task_summary,
            "project_context": self.project_context,
            "required_inputs": self.required_inputs,
            "forbidden_inputs": self.forbidden_inputs,
            "output_contract": self.output_contract,
            "audit_gate": self.audit_gate,
            "bootstrap_doc": self.bootstrap_doc,
            "skill_file": self.skill_file,
            "verification_commands": self.verification_commands,
            "context_source_metadata": self.context_source_metadata,
            "context_source_warnings": self.context_source_warnings,
            "required_routing_fields": self.required_routing_fields,
            "definition_policy": self.definition_policy,
            "source_footer_fields": self.source_footer_fields,
            "routing_outcomes": self.routing_outcomes,
            "scoring_fields": self.scoring_fields,
            "notes": self.notes,
        }


def resolve_role(roles_doc: dict, role_arg: str) -> dict:
    needle = role_arg.strip()
    # Defensive: Git Bash / MSYS on Windows can rewrite `/qa` to
    # `C:/Program Files/Git/qa` before the script even sees the arg.
    # Recover by taking the last path component.
    if "/" in needle or "\\" in needle:
        needle = re.split(r"[\\/]", needle)[-1]
    needle = needle.lower()
    for role in roles_doc["roles"]:
        if role.get("id") == needle:
            return role
        aliases = role.get("aliases") or []
        if needle in aliases:
            return role
    known = ", ".join(r["id"] for r in roles_doc["roles"])
    raise SystemExit(f"unknown role '{role_arg}'. known: {known}")


def discover_project_context_files(root: Path = ROOT) -> list[str]:
    """Return host-owned context docs that should frame every role packet.

    The managed upstream role files stay generic. Host projects put product
    vision, roadmap, organization, team topology, and external links under
    agents/project/ so role behavior changes through context, not by editing
    upstream SKILL.md files.
    """
    found: list[str] = []
    if (root / PROJECT_CONTEXT_README).exists():
        found.append(PROJECT_CONTEXT_README)

    actual = [rel for rel in PROJECT_CONTEXT_FILES if (root / rel).exists()]
    teams_dir = root / "agents" / "project" / "teams"
    if teams_dir.is_dir():
        actual.extend(
            path.relative_to(root).as_posix()
            for path in sorted(teams_dir.glob("*.md"), key=lambda p: p.name.lower())
        )

    if actual:
        found.extend(actual)
    elif (root / PROJECT_CONTEXT_EXAMPLE).exists():
        found.append(PROJECT_CONTEXT_EXAMPLE)
    return found


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _load_context_policy_fields(root: Path = ROOT) -> tuple[list[str], str | None]:
    source_file: Path | None = None
    for rel in CONTEXT_SOURCE_CANDIDATES:
        candidate = root / rel
        if candidate.exists():
            source_file = candidate
            break
    if source_file is None:
        return list(CONTEXT_QUERY_REQUIRED_FIELDS), None

    lines = source_file.read_text(encoding="utf-8").splitlines()
    section: str | None = None
    section_indent = 0
    list_indent = -1
    required_fields: list[str] = []
    definition_rule: str | None = None

    for raw in lines:
        text = _strip_yaml_comment(raw).rstrip("\n")
        if not text.strip() or text.lstrip().startswith("#"):
            continue
        indent = _indent_of(text)
        stripped = text.strip()

        if indent == 0 and stripped.endswith(":"):
            section = stripped[:-1]
            section_indent = indent
            list_indent = -1
            if section not in {"definition_policy", "query_policy"}:
                section = None
                section_indent = 0
            continue

        if section is None or indent <= section_indent:
            continue

        if section == "definition_policy":
            if stripped.startswith("rule:") and not definition_rule:
                definition_rule = stripped.partition(":")[2].strip().strip('"')
                continue
            if stripped.startswith("required_metadata:"):
                list_indent = indent
                continue
            if list_indent != -1 and indent > list_indent and stripped.startswith("- "):
                required_fields.append(stripped[2:].strip())
            elif list_indent != -1 and indent <= list_indent:
                list_indent = -1
            continue

        if section == "query_policy":
            if stripped.startswith("required_fields:"):
                list_indent = indent
                continue
            if list_indent != -1 and indent > list_indent and stripped.startswith("- "):
                required_fields.append(stripped[2:].strip())
            elif list_indent != -1 and indent <= list_indent:
                list_indent = -1

    if not required_fields:
        return list(CONTEXT_QUERY_REQUIRED_FIELDS), definition_rule
    return required_fields, definition_rule


def _load_context_source_metadata(root: Path = ROOT) -> tuple[list[str], list[str]]:
    source_file: Path | None = None
    for rel in CONTEXT_SOURCE_CANDIDATES:
        candidate = root / rel
        if candidate.exists():
            source_file = candidate
            break

    if source_file is None:
        return [], []

    text = source_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    source_text = "\n".join(lines)

    records: list[dict[str, object]] = []
    current: dict[str, object] = {}
    in_source_tiers = False
    section_indent: int | None = None
    entries_indent: int | None = None

    def emit_current() -> None:
        nonlocal current
        if current:
            records.append(current)
            current = {}

    for raw in lines:
        stripped = raw.rstrip()
        if not stripped.strip() or stripped.lstrip().startswith("#"):
            continue
        indent = _indent_of(stripped)
        text_line = stripped.strip()

        if not in_source_tiers:
            if text_line.startswith("source_tiers:"):
                in_source_tiers = True
                section_indent = indent
            continue

        if in_source_tiers and section_indent is not None:
            if text_line.startswith("query_policy:"):
                emit_current()
                break
            if indent <= section_indent:
                emit_current()
                break
            if indent == section_indent + 2 and text_line.startswith("- "):
                emit_current()
                entries_indent = section_indent + 2
                _, _, tail = text_line.partition("- ")
                key, sep, value = tail.partition(":")
                if sep:
                    current[key.strip()] = _parse_scalar(value.strip())
                continue
            if entries_indent is not None and indent >= entries_indent + 2 and ":" in text_line:
                key, _, value = text_line.partition(":")
                current[key.strip()] = _parse_scalar(value.strip())

    emit_current()

    summaries: list[str] = []
    warnings: list[str] = []
    for index, row in enumerate(records, start=1):
        source_tier = row.get("source_tier", row.get("tier"))
        if isinstance(source_tier, (int, float)):
            source_tier = str(source_tier)

        row_id = row.get("id", "(missing)")
        row_owner = row.get("owner", "(missing)")
        access = row.get("access_level", "(missing)")
        freshness = row.get("freshness_sla", "(missing)")
        lineage = row.get("lineage", "(missing)")

        for field in CONTEXT_SOURCE_REQUIRED_FIELDS:
            if field == "source_tier":
                if "source_tier" not in row and "tier" not in row:
                    warnings.append(
                        f"{source_file.as_posix()}: entry #{index} missing required field '{field}'"
                    )
                continue
            value = row.get(field)
            if value is None or value in ("", None):
                warnings.append(f"{source_file.as_posix()}: entry #{index} missing required field '{field}'")

        summaries.append(
            f"#{index}: id={row_id} tier={source_tier or '(missing)'} owner={row_owner} "
            f"access={access} freshness={freshness} lineage={lineage}"
        )

    if "definition_policy" not in source_text:
        warnings.append(f"{source_file.as_posix()}: missing definition_policy section")
    if "query_policy" not in source_text:
        warnings.append(f"{source_file.as_posix()}: missing query_policy section")
    if not records:
        warnings.append(f"{source_file.as_posix()}: no source_tiers entries found")
    return summaries, warnings


TASK_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TASK_FIELDS = ("id", "status", "owner", "priority", "difficulty",
               "est_hours", "est_tokens", "tags", "audit_log",
               "trigger_meeting", "created", "started_at", "completed_at")


def load_task_summary(task_id: str) -> dict:
    candidates = sorted(TASKS_DIR.glob(f"{task_id}-*.md"))
    if not candidates:
        direct = TASKS_DIR / f"{task_id}.md"
        if direct.exists():
            candidates = [direct]
    if not candidates:
        raise SystemExit(f"TASK file not found for {task_id}")
    path = candidates[0]
    text = path.read_text(encoding="utf-8")
    m = TASK_FRONTMATTER_RE.match(text)
    fm: dict = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                inner = v[1:-1]
                fm[k] = [p.strip() for p in inner.split(",") if p.strip()]
            else:
                fm[k] = v
    summary = {k: fm.get(k) for k in TASK_FIELDS if fm.get(k) not in (None, "")}
    summary["path"] = str(path.relative_to(ROOT))

    # extract first ## 목표 paragraph for human context
    body = text[m.end():] if m else text
    goal_match = re.search(r"\n## 목표\s*\n+(.*?)(?:\n##|\Z)", body, re.DOTALL)
    if goal_match:
        summary["goal_excerpt"] = goal_match.group(1).strip().splitlines()[0][:300]
    return summary


def detect_bootstrap_doc(role_id: str) -> str:
    """Heuristic — Claude-family unless caller overrides at orchestrator level."""
    return "docs/agent_bootstrap/claude.md"


def verification_commands(role_id: str, task_id: str | None) -> list[str]:
    base = [
        "python scripts/now.py",
        "python scripts/env_check.py",
        "python scripts/check_agent_docs.py",
    ]
    extras = {
        "uiux": ["pytest scripts/test_e2e.py -v -m smoke"],
        "backend": ["python scripts/test_connect.py"],
        "ci-cd": ["python scripts/check_deployment.py"],
        "qa": ["pytest scripts/test_e2e.py -v"],
    }
    out = list(base) + extras.get(role_id, [])
    if task_id:
        out.append(f"# review TASK at agents/lead_engineer/tasks/{task_id}-*.md")
    return out


def build_packet(roles_doc: dict, role_arg: str, task_arg: str | None) -> Packet:
    role = resolve_role(roles_doc, role_arg)
    task_summary = load_task_summary(task_arg) if task_arg else None
    context_metadata, context_warnings = _load_context_source_metadata(ROOT)
    required_routing_fields, definition_policy = _load_context_policy_fields(ROOT)
    if required_routing_fields == []:
        context_warnings.append(
            "CONTEXT-SOURCES.yml: query_policy.required_fields is missing or empty; routing schema weak."
        )
    if not definition_policy:
        context_warnings.append(
            "CONTEXT-SOURCES.yml: definition_policy.rule is missing; define policy first."
        )
    return Packet(
        role_id=role["id"],
        aliases=role.get("aliases") or [],
        task_id=task_arg,
        task_summary=task_summary,
        project_context=discover_project_context_files(ROOT),
        required_inputs=role.get("required_inputs") or [],
        forbidden_inputs=role.get("forbidden_inputs") or [],
        output_contract=role.get("output_contract") or [],
        audit_gate=bool(role.get("audit_gate")),
        bootstrap_doc=detect_bootstrap_doc(role["id"]),
        skill_file=role["skill_file"],
        verification_commands=verification_commands(role["id"], task_arg),
        notes=(role.get("notes") or "").strip(),
        context_source_metadata=context_metadata,
        context_source_warnings=context_warnings,
        required_routing_fields=required_routing_fields,
        definition_policy=definition_policy,
        source_footer_fields=list(CONTEXT_SOURCE_FOOTER_FIELDS),
        routing_outcomes=list(CONTEXT_ROUTING_OUTCOMES),
        scoring_fields=list(CONTEXT_SCORING_FIELDS),
    )


# ---------- render ----------

def render_markdown(p: Packet) -> str:
    lines: list[str] = []
    lines.append(f"# Context Packet — `{p.role_id}`" + (f" / `{p.task_id}`" if p.task_id else ""))
    lines.append("")
    lines.append(f"- Bootstrap: `{p.bootstrap_doc}` then `{p.skill_file}`")
    lines.append(f"- Aliases: {', '.join('/' + a for a in p.aliases) or '(none)'}")
    lines.append(f"- Audit gate: {'YES (High/Critical 완료 시 ## Independent Audit 필수)' if p.audit_gate else 'no (priority 따라감)'}")
    lines.append("")
    if p.project_context:
        lines.append("## Project context overlay (READ FIRST)")
        for x in p.project_context:
            lines.append(f"- {x}")
        lines.append("")
    if p.context_source_metadata:
        lines.append("## Context source ranking")
        for row in p.context_source_metadata:
            lines.append(f"- {row}")
        lines.append("")
    if p.context_source_warnings:
        lines.append("## Context source warnings (needs update)")
        for row in p.context_source_warnings:
            lines.append(f"- {row}")
        lines.append("")
    lines.append("## Routing policy (required fields + definitions)")
    lines.append(f"- definition_policy: {p.definition_policy or 'missing (block if policy absent)'}")
    lines.append("- required_routing_fields:")
    for row in p.required_routing_fields:
        lines.append(f"  - {row}")
    lines.append("")
    lines.append("## Source footer contract")
    for row in p.source_footer_fields:
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Routing outcomes")
    for row in p.routing_outcomes:
        lines.append(f"- {row}")
    lines.append("")
    lines.append("## Routing scores")
    for row in p.scoring_fields:
        lines.append(f"- {row}")
    lines.append("")
    if p.task_summary:
        lines.append("## Active TASK")
        for k in ("id", "status", "owner", "priority", "audit_log",
                  "started_at", "trigger_meeting", "path"):
            v = p.task_summary.get(k)
            if v:
                lines.append(f"- {k}: {v}")
        excerpt = p.task_summary.get("goal_excerpt")
        if excerpt:
            lines.append("")
            lines.append(f"  목표: {excerpt}")
        lines.append("")
    lines.append("## Required inputs (READ FIRST)")
    for x in p.required_inputs:
        lines.append(f"- {x}")
    if p.forbidden_inputs:
        lines.append("")
        lines.append("## Forbidden inputs (DO NOT READ)")
        for x in p.forbidden_inputs:
            lines.append(f"- {x}")
    lines.append("")
    lines.append("## Output contract")
    for x in p.output_contract:
        lines.append(f"- {x}")
    lines.append("")
    lines.append("## Verification commands")
    for cmd in p.verification_commands:
        lines.append(f"- `{cmd}`")
    if p.notes:
        lines.append("")
        lines.append("## Notes")
        for line in p.notes.splitlines():
            lines.append(f"> {line}")
    lines.append("")
    return "\n".join(lines)


# ---------- CLI ----------

def main() -> int:
    parser = argparse.ArgumentParser(description="Build an agent context packet (TASK-084).")
    parser.add_argument("--role", help="role id or alias (e.g. qa, lead-engineer, /backend)")
    parser.add_argument("--task", help="TASK-NNN to summarize (optional)")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--role-list", action="store_true",
                        help="list known roles and aliases, then exit")
    parser.add_argument("--check-only", action="store_true",
                        help="validate registry + resolve, exit 0/1 without packet output")
    args = parser.parse_args()

    roles_doc = load_roles()

    if args.role_list:
        for role in roles_doc["roles"]:
            aliases = ", ".join("/" + a for a in (role.get("aliases") or []))
            print(f"{role['id']:<22} aliases: {aliases}")
            print(f"  skill_file: {role.get('skill_file')}")
            print(f"  audit_gate: {role.get('audit_gate')}")
        return 0

    if not args.role:
        parser.error("--role is required (or use --role-list)")
        return 2  # unreachable; argparse exits

    if args.check_only:
        try:
            resolve_role(roles_doc, args.role)
            if args.task:
                load_task_summary(args.task)
            _, warnings = _load_context_source_metadata(ROOT)
            if warnings:
                print("WARN: context source metadata quality issues:")
                for warning in warnings:
                    print(f"- {warning}")
            print(f"OK: role '{args.role}' and task '{args.task or '(none)'}' resolve cleanly")
            return 0
        except SystemExit as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1

    packet = build_packet(roles_doc, args.role, args.task)
    if args.format == "json":
        print(json.dumps(packet.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(packet))
    return 0


if __name__ == "__main__":
    sys.exit(main())
