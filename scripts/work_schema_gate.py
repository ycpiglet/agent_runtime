"""Validate the work item metadata schema SSoT."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_SCHEMA_PATH = Path("agents/project/WORK-SCHEMA.yml")
SCHEMA_VERSION = "agent-runtime-work-schema/v1"
REQUIRED_KINDS = {"initiative", "taskset", "task", "unit", "routine", "spike"}
REQUIRED_FIELD_METADATA = ("type", "required_for", "populated_by", "consumed_by", "query_use")
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
    "parent_id",
    "resolution",
    "completed_at",
    "verification_status",
    "created_by_instance",
    "last_actor_instance",
    "team",
    "summary",
    "tags",
    "area",
    "component",
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
    "actual_tokens",
    "budget_cap",
    "rework_count",
    "gate_failure_count",
    "verified_at",
    "verified_by",
}
REQUIRED_RESOLUTIONS = {"done", "wontfix", "duplicate", "superseded", "moved_to_vault"}
COMPUTED_ONLY_FIELDS = {"progress_pct", "age", "lead_time", "est_actual_delta", "rollup_progress_pct"}


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
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Work schema SSoT gate")
    parser.add_argument("--path", type=Path, default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    findings = check_path(args.path)
    status = "fail" if findings else "pass"
    print(f"work-schema-gate: {status}")
    print(f"path={args.path}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
