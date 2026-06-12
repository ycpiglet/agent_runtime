"""Validate the work item metadata schema SSoT."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_SCHEMA_PATH = Path("agents/project/WORK-SCHEMA.yml")
SCHEMA_VERSION = "agent-runtime-work-schema/v1"
WORK_ITEM_SCHEMA_VERSION = "agent-runtime-work-item/v1"
REQUIRED_KINDS = {"initiative", "taskset", "task", "unit", "routine", "spike"}
REQUIRED_FIELD_METADATA = ("type", "required_for", "source", "populated_by", "consumed_by", "query_use")
FIELD_SOURCE_VALUES = {"generator", "gate", "human", "runtime", "derived"}
COUNTER_FIELDS = ("gate_failure_count", "reopened_count", "rework_count")
REQUIRED_CORE_FIELDS = {
    "schema_version",
    "work_id",
    "work_uid",
    "kind",
    "status",
    "owner",
    "created_at",
    "updated_at",
    "origin_type",
    "origin_ref",
    "created_by",
}
REQUIRED_CATALOG_FIELDS = REQUIRED_CORE_FIELDS | {
    "id",
    "display_id",
    "task_uid",
    "parent_id",
    "registered_at",
    "resolution",
    "completed_at",
    "closed_by",
    "verification_status",
    "created_by_instance",
    "last_actor_instance",
    "team",
    "title",
    "summary",
    "tags",
    "area",
    "component",
    "priority",
    "difficulty",
    "initiative_id",
    "project_id",
    "task_set_id",
    "task_id",
    "unit_id",
    "unit_spec",
    "reservation_id",
    "horizon",
    "model_tier",
    "escalation_triggers",
    "planner_model_tier",
    "worker_model_tier",
    "reviewer_model_tier",
    "risk_tier",
    "approval_required",
    "security_sensitive",
    "evidence_refs",
    "review_refs",
    "commit_refs",
    "pr_refs",
    "a2a_context_id",
    "claim_refs",
    "est_tokens",
    "est_hours",
    "verification",
    "context",
    "inputs",
    "target_files",
    "scope",
    "acceptance",
    "handoff",
    "stop_condition",
    "actual_tokens",
    "actual_hours",
    "est_cost",
    "actual_cost",
    "budget_cap",
    "rework_count",
    "gate_failure_count",
    "verified_at",
    "verified_by",
    "started_at",
    "split_from",
    "merged_into",
    "supersedes",
    "superseded_by",
    "duplicate_of",
    "reopened_count",
    "blocks",
    "blocked_by",
    "relates_to",
    "stakeholders",
    "watchers",
    "due_date",
    "blocked_since",
    "xp_value",
}
REQUIRED_RESOLUTIONS = {"done", "wontfix", "duplicate", "superseded", "moved_to_vault"}
COMPUTED_ONLY_FIELDS = {"progress_pct", "age", "lead_time", "est_actual_delta", "variance", "rollup_progress_pct"}
WORK_ITEM_PATTERNS = (
    "agents/project/initiatives/*.md",
    "docs/superpowers/plans/*.md",
    "agents/lead_engineer/tasks/TASK-*.md",
    "agents/lead_engineer/tasks/units/**/*.md",
)
CLOSED_STATUSES = {"completed", "closed", "done"}


def _list_block_items(text: str, label: str) -> set[str]:
    match = re.search(rf"^{re.escape(label)}:\s*\n(?P<body>(?:  - .+\n)+)", text, flags=re.MULTILINE)
    if not match:
        return set()
    return {
        line.split("-", 1)[1].strip()
        for line in match.group("body").splitlines()
        if line.strip().startswith("- ")
    }


def _mapping_block(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*\n(?P<body>.*?)(?=^[A-Za-z0-9_-]+:|\Z)", text, flags=re.MULTILINE | re.DOTALL)
    return match.group("body") if match else ""


def _named_blocks(mapping_body: str) -> dict[str, str]:
    matches = list(re.finditer(r"^  ([A-Za-z0-9_]+):\s*$", mapping_body, flags=re.MULTILINE))
    blocks: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(mapping_body)
        blocks[match.group(1)] = mapping_body[start:end]
    return blocks


def _minimum_required_by_kind(text: str) -> dict[str, set[str]]:
    body = _mapping_block(text, "minimum_required_by_kind")
    result: dict[str, set[str]] = {}
    for kind, block in _named_blocks(body).items():
        result[kind] = {
            line.split("-", 1)[1].strip()
            for line in block.splitlines()
            if line.strip().startswith("- ")
        }
    return result


def _parse_inline_list(value: str) -> list[str]:
    inner = value.strip()[1:-1].strip()
    if not inner:
        return []
    return [item.strip().strip('"').strip("'") for item in inner.split(",") if item.strip()]


def _clean_scalar(value: str) -> str | list[str]:
    stripped = value.strip()
    if stripped.startswith("[") and stripped.endswith("]"):
        return _parse_inline_list(stripped)
    if (stripped.startswith('"') and stripped.endswith('"')) or (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1]
    return stripped


def _frontmatter(text: str) -> dict[str, object]:
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    end = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = index
            break
    if end is None:
        return {}

    meta: dict[str, object] = {}
    current_key: str | None = None
    for line in lines[1:end]:
        if not line.strip():
            continue
        item_match = re.match(r"^\s*-\s+(?P<value>.+?)\s*$", line)
        if item_match and current_key:
            current = meta.setdefault(current_key, [])
            if isinstance(current, list):
                current.append(_clean_scalar(item_match.group("value")))
            continue
        key_match = re.match(r"^(?P<key>[A-Za-z0-9_]+):(?:\s*(?P<value>.*))?$", line)
        if not key_match:
            current_key = None
            continue
        key = key_match.group("key")
        value = key_match.group("value") or ""
        if value.strip():
            meta[key] = _clean_scalar(value)
            current_key = None
        else:
            meta[key] = []
            current_key = key
    return meta


def _iter_work_item_paths(root: Path) -> list[Path]:
    paths: dict[Path, None] = {}
    for pattern in WORK_ITEM_PATTERNS:
        for path in root.glob(pattern):
            if path.is_file():
                paths[path] = None
    return sorted(paths)


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return len(value) == 0
    return False


def check_items(root: Path, schema_path: Path) -> tuple[list[str], list[str]]:
    findings: list[str] = []
    warnings: list[str] = []
    text = schema_path.read_text(encoding="utf-8")
    catalog_fields = set(_named_blocks(_mapping_block(text, "fields")))
    computed_fields = set(_named_blocks(_mapping_block(text, "computed_only_fields")))
    required_by_kind = _minimum_required_by_kind(text)
    closed_required = _list_block_items(text, "required_when_closed")
    closed_resolutions = _list_block_items(text, "closed_resolution_values")

    for path in _iter_work_item_paths(root):
        meta = _frontmatter(path.read_text(encoding="utf-8"))
        if meta.get("schema_version") != WORK_ITEM_SCHEMA_VERSION:
            continue
        rel_path = _rel(root, path)
        kind = str(meta.get("kind") or "").strip()
        if kind not in REQUIRED_KINDS:
            findings.append(f"{rel_path}: work-item:invalid-kind:{kind or 'missing'}")
            continue

        for field in sorted(required_by_kind.get(kind, set())):
            if _missing(meta.get(field)):
                findings.append(f"{rel_path}: work-item:missing-required:{field}")

        is_closed = str(meta.get("status") or "").strip() in CLOSED_STATUSES or not _missing(meta.get("resolution"))
        if is_closed:
            for field in sorted(closed_required):
                if _missing(meta.get(field)):
                    findings.append(f"{rel_path}: work-item:closed-missing-required:{field}")

        resolution = meta.get("resolution")
        if not _missing(resolution) and str(resolution).strip() not in closed_resolutions:
            findings.append(f"{rel_path}: work-item:invalid-resolution:{resolution}")

        for field in COUNTER_FIELDS:
            if field not in meta:
                continue
            value = meta.get(field)
            if _missing(value):
                continue
            if not re.fullmatch(r"\d+", str(value).strip()):
                findings.append(f"{rel_path}: work-item:invalid-counter:{field}:{value}")

        for field in sorted(computed_fields):
            if field in meta:
                findings.append(f"{rel_path}: work-item:computed-field-stored:{field}")

        for field in sorted(meta):
            if field not in catalog_fields and field not in computed_fields:
                warnings.append(f"{rel_path}: work-item:unknown-field:{field}")
    return findings, warnings


def check_path(path: Path) -> list[str]:
    findings: list[str] = []
    if not path.exists():
        return [f"{path.as_posix()}: work-schema:missing"]
    text = path.read_text(encoding="utf-8")

    if f"schema_version: {SCHEMA_VERSION}" not in text:
        findings.append(f"{path.as_posix()}: work-schema:invalid-schema-version")
    if "unknown_field_policy: watch" not in text:
        findings.append(f"{path.as_posix()}: work-schema:unknown-field-policy-not-watch")
    if "derived_field_policy: computed_only" not in text:
        findings.append(f"{path.as_posix()}: work-schema:derived-field-policy-not-computed-only")

    kinds = _list_block_items(text, "work_kinds")
    for kind in sorted(REQUIRED_KINDS - kinds):
        findings.append(f"{path.as_posix()}: work-schema:missing-kind:{kind}")

    resolutions = _list_block_items(text, "closed_resolution_values")
    for value in sorted(REQUIRED_RESOLUTIONS - resolutions):
        findings.append(f"{path.as_posix()}: work-schema:missing-resolution:{value}")

    core_fields = _list_block_items(text, "required_core_fields")
    for field in sorted(REQUIRED_CORE_FIELDS - core_fields):
        findings.append(f"{path.as_posix()}: work-schema:missing-required-core-field:{field}")

    matrix = _minimum_required_by_kind(text)
    for kind in sorted(REQUIRED_KINDS):
        if kind not in matrix:
            findings.append(f"{path.as_posix()}: work-schema:missing-kind-required-matrix:{kind}")
            continue
        required_for_kind = REQUIRED_CORE_FIELDS | ({"parent_id"} if kind in {"taskset", "task", "unit", "spike"} else set())
        for field in sorted(required_for_kind - matrix[kind]):
            findings.append(f"{path.as_posix()}: work-schema:kind-required-missing:{kind}:{field}")

    closed_required = _list_block_items(text, "required_when_closed")
    for field in ("resolution", "completed_at", "verification_status"):
        if field not in closed_required:
            findings.append(f"{path.as_posix()}: work-schema:closed-required-missing:{field}")

    promotion = _mapping_block(text, "field_promotion_policy")
    if not promotion.strip():
        findings.append(f"{path.as_posix()}: work-schema:missing-promotion-policy")
    else:
        if not re.search(r"^\s{2}default_entry:\s*optional\s*$", promotion, flags=re.MULTILINE):
            findings.append(f"{path.as_posix()}: work-schema:promotion-policy-default-not-optional")
        if not re.search(r"^\s{2}promote_to_required_when:\s*consuming_tool_exists\s*$", promotion, flags=re.MULTILINE):
            findings.append(f"{path.as_posix()}: work-schema:promotion-policy-missing-promotion-rule")

    computed_blocks = _named_blocks(_mapping_block(text, "computed_only_fields"))
    for field in sorted(COMPUTED_ONLY_FIELDS):
        block = computed_blocks.get(field, "")
        if not block:
            findings.append(f"{path.as_posix()}: work-schema:missing-computed-field:{field}")
        elif "storage_policy: computed_only" not in block:
            findings.append(f"{path.as_posix()}: work-schema:computed-field-stored:{field}")

    field_blocks = _named_blocks(_mapping_block(text, "fields"))
    for field in sorted(REQUIRED_CATALOG_FIELDS):
        block = field_blocks.get(field, "")
        if not block:
            findings.append(f"{path.as_posix()}: work-schema:missing-field-catalog:{field}")
            continue
        for meta_key in REQUIRED_FIELD_METADATA:
            if not re.search(rf"^\s{{4}}{re.escape(meta_key)}:\s*.+$", block, flags=re.MULTILINE):
                findings.append(f"{path.as_posix()}: work-schema:field-missing-metadata:{field}:{meta_key}")
        source_match = re.search(r"^\s{4}source:\s*(?P<value>\S+)\s*$", block, flags=re.MULTILINE)
        if source_match and source_match.group("value") not in FIELD_SOURCE_VALUES:
            findings.append(
                f"{path.as_posix()}: work-schema:field-invalid-source:{field}:{source_match.group('value')}"
            )
        if re.search(r"^\s{4}type:\s*enum\s*$", block, flags=re.MULTILINE) and not re.search(
            r"^\s{4}allowed_values:\s*\[.+\]\s*$", block, flags=re.MULTILINE
        ):
            findings.append(f"{path.as_posix()}: work-schema:enum-missing-allowed-values:{field}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Work schema SSoT gate")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--path", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--items", action="store_true", help="Validate v1 work item frontmatter against the catalog")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    schema_path = args.path if args.path.is_absolute() else args.root / args.path
    findings = check_path(schema_path)
    warnings: list[str] = []
    if args.items and not findings:
        item_findings, item_warnings = check_items(args.root, schema_path)
        findings.extend(item_findings)
        warnings.extend(item_warnings)

    status = "fail" if findings else "watch" if warnings else "pass"
    print(f"work-schema-gate: {status}")
    print(f"path={schema_path}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print(f"- {warning}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
