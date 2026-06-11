"""Validate TASKSET-AR-CONTEXT-KNOWLEDGE contracts.

This gate closes the context knowledge task set by checking the durable
contracts instead of relying on prose-only task notes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CONTEXT_SOURCE_FILES = (
    Path("agents/project/CONTEXT-SOURCES.yml"),
    Path("src/agent_runtime/templates/project/agents/project/CONTEXT-SOURCES.example.yml"),
)
SKILL_GOVERNANCE_FILES = (
    Path("agents/project/SKILL-GOVERNANCE.md"),
    Path("src/agent_runtime/templates/project/agents/project/SKILL-GOVERNANCE.md"),
)
WAREHOUSE_TEMPLATE_FILES = (
    Path("agents/project/AGENT-KNOWLEDGE-WAREHOUSE.md"),
    Path("src/agent_runtime/templates/project/agents/project/AGENT-KNOWLEDGE-WAREHOUSE.md"),
)
EVAL_FILES = (
    Path("agents/project/evals/overlay-routing-v1.jsonl"),
    Path("agents/project/evals/gov-metadata-v1.jsonl"),
)
OVERLAY_SIMULATION_INPUT = Path(
    "agents/project/overlays/simulations/mvp-client-2026-06-09/context-packet-simulation.json"
)
PACKET_BUILDER = Path("src/agent_runtime/templates/project/scripts/agent_context_packet.py")

REQUIRED_SOURCE_TIER_FIELDS = (
    "id",
    "source_tier",
    "owner",
    "access_level",
    "freshness_sla",
    "lineage",
    "confidence_weight",
)
REQUIRED_METADATA = (
    "owner",
    "updated_at",
    "source_tier",
    "access_level",
    "lineage",
    "confidence",
    "ambiguity_level",
)
REQUIRED_QUERY_FIELDS = (
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
REQUIRED_SOURCE_FOOTER_FIELDS = (
    "source_tier",
    "source",
    "confidence",
    "access_level",
    "ambiguity_score",
    "freshness_sla",
    "reviewer_verdict",
    "lineage",
)
REQUIRED_RUNBOOK_EVIDENCE = (
    "clarify",
    "retrieve",
    "execute",
    "review",
    "verify",
    "record",
    "source_footer",
    "review_verdict",
    "evidence",
    "verified_pattern",
    "correction_path",
)
REQUIRED_WAREHOUSE_SECTIONS = (
    "빠른 참조",
    "차원설명",
    "핵심 테이블",
    "주의사항/패턴",
    "연결고리",
)
REQUIRED_WAREHOUSE_TERMS = (
    "source tier",
    "lineage",
    "history",
    "context knowledge",
    "freshness_sla",
)
REQUIRED_OVERLAY_DIMENSIONS = (
    "vision",
    "roadmap",
    "organization",
    "team",
    "links",
    "communication",
)


def _read_text(root: Path, rel: Path) -> tuple[str, list[str]]:
    path = root / rel
    if not path.exists():
        return "", [f"{rel.as_posix()}:missing"]
    return path.read_text(encoding="utf-8"), []


def _read_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    if not path.exists():
        return None, [f"{path.as_posix()}:missing"]
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"{path.as_posix()}:json-invalid:{exc.msg}"]
    if not isinstance(value, dict):
        return None, [f"{path.as_posix()}:json-not-object"]
    return value, []


def _indent(raw: str) -> int:
    return len(raw) - len(raw.lstrip(" "))


def _section_blocks(text: str, section: str) -> list[list[str]]:
    lines = text.splitlines()
    in_section = False
    section_indent = 0
    blocks: list[list[str]] = []
    current: list[str] = []
    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = _indent(raw)
        if not in_section:
            if stripped == f"{section}:":
                in_section = True
                section_indent = indent
            continue
        if indent <= section_indent and not stripped.startswith("- "):
            break
        if indent == section_indent + 2 and stripped.startswith("- "):
            if current:
                blocks.append(current)
            current = [raw]
            continue
        if current:
            current.append(raw)
    if current:
        blocks.append(current)
    return blocks


def _block_has_field(block: list[str], field: str) -> bool:
    prefix = f"{field}:"
    item_prefix = f"- {field}:"
    return any(raw.strip().startswith(prefix) or raw.strip().startswith(item_prefix) for raw in block)


def _missing_tokens(text: str, tokens: tuple[str, ...] | list[str]) -> list[str]:
    return [token for token in tokens if token not in text]


def _check_context_sources(root: Path) -> dict[str, Any]:
    findings: list[str] = []
    file_results: list[dict[str, Any]] = []
    for rel in CONTEXT_SOURCE_FILES:
        text, file_findings = _read_text(root, rel)
        local = list(file_findings)
        if text:
            for required in (
                "single_source_of_truth:",
                "source_tiers:",
                "definition_policy:",
                "query_policy:",
                "required_metadata:",
                "required_fields:",
                "required_blocks:",
                "routing_outcomes:",
                "scoring:",
                "clarify_required",
                "reviewer_review",
                "hold_for_query_contract",
                "correction_path",
                "ambiguity_score",
                "ssot_alignment_score",
            ):
                if required not in text:
                    local.append(f"missing-token:{required}")
            for token in (
                *REQUIRED_METADATA,
                *REQUIRED_QUERY_FIELDS,
                *REQUIRED_SOURCE_FOOTER_FIELDS,
            ):
                if token not in text:
                    local.append(f"missing-contract-field:{token}")
            blocks = _section_blocks(text, "source_tiers")
            if len(blocks) < 4:
                local.append(f"source_tiers:insufficient:{len(blocks)}<4")
            for index, block in enumerate(blocks, start=1):
                for field in REQUIRED_SOURCE_TIER_FIELDS:
                    if not _block_has_field(block, field):
                        local.append(f"source_tiers:{index}:missing:{field}")
        findings.extend(f"{rel.as_posix()}:{finding}" for finding in local)
        file_results.append({"path": rel.as_posix(), "findings": local})
    return {"findings": findings, "files": file_results}


def _check_packet_builder(root: Path) -> dict[str, Any]:
    text, findings = _read_text(root, PACKET_BUILDER)
    local = list(findings)
    if text:
        tokens = [
            "CONTEXT_SOURCE_FOOTER_FIELDS",
            "CONTEXT_ROUTING_OUTCOMES",
            "CONTEXT_SCORING_FIELDS",
            "source_footer_fields",
            "routing_outcomes",
            "scoring_fields",
            "Source footer contract",
            "Routing outcomes",
            "Routing scores",
            *REQUIRED_QUERY_FIELDS,
            *REQUIRED_SOURCE_FOOTER_FIELDS,
        ]
        local.extend(f"missing-token:{token}" for token in _missing_tokens(text, tokens))
    return {"findings": [f"{PACKET_BUILDER.as_posix()}:{finding}" for finding in local]}


def _check_skill_governance(root: Path) -> dict[str, Any]:
    findings: list[str] = []
    file_results: list[dict[str, Any]] = []
    for rel in SKILL_GOVERNANCE_FILES:
        text, file_findings = _read_text(root, rel)
        local = list(file_findings)
        if text:
            local.extend(f"missing-runbook-evidence:{token}" for token in _missing_tokens(text, REQUIRED_RUNBOOK_EVIDENCE))
            local.extend(f"missing-warehouse-section:{token}" for token in _missing_tokens(text, REQUIRED_WAREHOUSE_SECTIONS))
            lowered = text.lower()
            for token in (
                "query contract",
                "hold_for_query_contract",
                "clarify_required",
                "reviewer_review",
                "TASK-AR-204",
            ):
                haystack = lowered if token == "query contract" else text
                needle = token.lower() if token == "query contract" else token
                if needle not in haystack:
                    local.append(f"missing-routing-token:{token}")
        findings.extend(f"{rel.as_posix()}:{finding}" for finding in local)
        file_results.append({"path": rel.as_posix(), "findings": local})
    return {"findings": findings, "files": file_results}


def _check_warehouse_docs(root: Path) -> dict[str, Any]:
    findings: list[str] = []
    checked_files: list[str] = []
    for rel in WAREHOUSE_TEMPLATE_FILES:
        text, file_findings = _read_text(root, rel)
        local = list(file_findings)
        if text:
            local.extend(f"missing-section:{token}" for token in _missing_tokens(text, REQUIRED_WAREHOUSE_SECTIONS))
            local.extend(f"missing-term:{token}" for token in _missing_tokens(text, REQUIRED_WAREHOUSE_TERMS))
        findings.extend(f"{rel.as_posix()}:{finding}" for finding in local)
        checked_files.append(rel.as_posix())

    role_dir = root / "agents" / "project" / "knowledge"
    role_docs = sorted(role_dir.glob("*.md")) if role_dir.exists() else []
    valid_role_docs = 0
    for path in role_docs:
        text = path.read_text(encoding="utf-8")
        missing = [
            f"missing-section:{token}" for token in _missing_tokens(text, REQUIRED_WAREHOUSE_SECTIONS)
        ]
        missing.extend(f"missing-term:{token}" for token in _missing_tokens(text, REQUIRED_WAREHOUSE_TERMS))
        role_name = path.stem
        if f"role: {role_name}" not in text:
            missing.append(f"role-path-mismatch:{role_name}")
        if missing:
            rel = path.relative_to(root).as_posix()
            findings.extend(f"{rel}:{finding}" for finding in missing)
        else:
            valid_role_docs += 1
        checked_files.append(path.relative_to(root).as_posix())
    if valid_role_docs < 1:
        findings.append("agents/project/knowledge:missing-valid-role-warehouse-doc")
    return {"findings": findings, "checked_files": checked_files, "valid_role_docs": valid_role_docs}


def _jsonl_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    findings: list[str] = []
    if not path.exists():
        return rows, [f"{path.as_posix()}:missing"]
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            findings.append(f"{path.as_posix()}:{line_no}:json-invalid:{exc.msg}")
            continue
        if isinstance(row, dict):
            rows.append(row)
        else:
            findings.append(f"{path.as_posix()}:{line_no}:json-not-object")
    return rows, findings


def _check_ambiguous_eval_file(path: Path) -> list[str]:
    rows, findings = _jsonl_rows(path)
    ambiguous_rows = [row for row in rows if row.get("case_type") == "ambiguous"]
    if not ambiguous_rows:
        findings.append(f"{path.as_posix()}:missing-ambiguous-case")
    for row in ambiguous_rows:
        row_id = str(row.get("id") or "unknown")
        contract = row.get("query_contract")
        if not isinstance(contract, dict):
            findings.append(f"{path.as_posix()}:{row_id}:missing-query_contract")
            continue
        for field in REQUIRED_QUERY_FIELDS:
            if field == "access_check":
                if not (contract.get("access_check") or contract.get("access_level")):
                    findings.append(f"{path.as_posix()}:{row_id}:query_contract:missing:{field}")
                continue
            if not contract.get(field):
                findings.append(f"{path.as_posix()}:{row_id}:query_contract:missing:{field}")
        if not row.get("expected_outcome"):
            findings.append(f"{path.as_posix()}:{row_id}:missing-expected_outcome")
    return findings


def _check_eval_ambiguity(root: Path) -> dict[str, Any]:
    findings: list[str] = []
    for rel in EVAL_FILES:
        findings.extend(_check_ambiguous_eval_file(root / rel))
    return {"findings": findings}


def _check_overlay_simulation(root: Path) -> dict[str, Any]:
    path = root / OVERLAY_SIMULATION_INPUT
    data, findings = _read_json(path)
    local = list(findings)
    if data:
        cases = data.get("cases")
        if not isinstance(cases, list) or len(cases) < 2:
            local.append("cases:insufficient-for-two-project-scenarios")
        else:
            routes = {case.get("expected_route") for case in cases if isinstance(case, dict)}
            if "ready_for_overlay_use" not in routes:
                local.append("cases:missing-ready_for_overlay_use")
            if "hold_for_overlay" not in routes:
                local.append("cases:missing-hold_for_overlay")
            for case in cases:
                if not isinstance(case, dict):
                    local.append("case:not-object")
                    continue
                output = case.get("query_routing_output")
                if not isinstance(output, dict):
                    local.append(f"{case.get('name', 'unknown')}:query_routing_output:missing")
                    continue
                for dimension in REQUIRED_OVERLAY_DIMENSIONS:
                    if dimension not in output or not output.get(dimension):
                        local.append(f"{case.get('name', 'unknown')}:missing-output-dimension:{dimension}")
    return {"findings": [f"{OVERLAY_SIMULATION_INPUT.as_posix()}:{finding}" for finding in local]}


def check_root(root: Path) -> list[str]:
    report = evaluate(root)
    return list(report["findings"])


def evaluate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    sections = {
        "context_sources": _check_context_sources(root),
        "packet_builder": _check_packet_builder(root),
        "skill_governance": _check_skill_governance(root),
        "warehouse_docs": _check_warehouse_docs(root),
        "eval_ambiguity": _check_eval_ambiguity(root),
        "overlay_simulation": _check_overlay_simulation(root),
    }
    findings: list[str] = []
    for section, result in sections.items():
        findings.extend(f"{section}:{finding}" for finding in result["findings"])
    return {
        "schema": "agent-runtime-context-knowledge-gate/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": root.as_posix(),
        "status": "pass" if not findings else "block",
        "blocked_task_set": None if not findings else "TASKSET-AR-CONTEXT-KNOWLEDGE",
        "findings": findings,
        "sections": sections,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Context knowledge task-set gate")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    report = evaluate(args.root)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"context-knowledge-gate: {report['status']}")
    print(f"root={report['root']}")
    print(f"findings={len(report['findings'])}")
    for finding in report["findings"]:
        print(f"- {finding}")
    if args.out is not None:
        print(f"out={args.out.as_posix()}")
    return 1 if args.check and report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
