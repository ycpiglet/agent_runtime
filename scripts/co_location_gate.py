"""Skill/data co-location enforcement gate for agent_runtime.

This gate turns TASK-AR-204 governance rules into an executable release check:
skill, data, migration, source, and overlay mappings must carry owner,
approval, expiry, justification, and release-routing metadata. Missing fields
are treated as block, not warn.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SKILL_MAP = Path("agents/project/SKILL-DATA-MAP.yml")
DEFAULT_MIGRATION_MAP = Path("agents/project/MIGRATION-COMPAT-MAP.yml")
DEFAULT_CONTEXT_SOURCES = Path("agents/project/CONTEXT-SOURCES.yml")
DEFAULT_DATASET_CATALOG = Path("agents/project/DATASET-CATALOG.yml")
DEFAULT_OUT = Path("reviews/CO-LOCATION-GATE-2026-06-09-task-ar-204.json")

REQUIRED_SKILL_FIELDS = ["skill_id", "owner", "scope", "criticality", "change_policy"]
REQUIRED_ARTIFACT_FIELDS = ["path", "kind"]
REQUIRED_MIGRATION_APPROVAL_FIELDS = ["owner", "approved_by", "decision_date", "justification", "expiry"]
REQUIRED_CONTEXT_FIELDS = ["id", "owner", "access_level", "freshness_sla", "lineage", "confidence_weight"]
REQUIRED_DATASET_FIELDS = ["id", "owner", "source_tier", "location", "minimum_score"]


def _read(path: Path) -> tuple[list[str], list[str]]:
    if not path.exists():
        return [], [f"missing:{path.as_posix()}"]
    return path.read_text(encoding="utf-8").splitlines(), []


def _value(raw: str) -> str:
    return raw.split(":", 1)[1].strip().strip('"').strip("'")


def _parse_top_level_items(lines: list[str], start_marker: str = "- ") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_list: str | None = None
    current_artifact: dict[str, str] | None = None
    in_artifacts = False

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if indent == 0 and stripped.startswith(start_marker) and ":" in stripped:
            if current_artifact and current is not None:
                current.setdefault("artifacts", []).append(current_artifact)
                current_artifact = None
            if current:
                items.append(current)
            key, value = stripped[len(start_marker) :].split(":", 1)
            current = {key.strip(): value.strip()}
            current_list = None
            in_artifacts = False
            continue
        if current is None:
            continue
        if indent <= 2 and stripped.endswith(":"):
            key = stripped[:-1]
            current_list = key
            in_artifacts = key == "artifacts"
            if key in {"artifacts", "required_when", "linked_tasks"}:
                current.setdefault(key, [])
            continue
        if indent <= 2 and ":" in stripped and not stripped.startswith("-"):
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()
            current_list = None
            in_artifacts = False
            continue
        if current_list in {"required_when", "linked_tasks"} and stripped.startswith("-"):
            current.setdefault(current_list, []).append(stripped[1:].strip())
            continue
        if in_artifacts and stripped.startswith("- path:"):
            if current_artifact:
                current.setdefault("artifacts", []).append(current_artifact)
            current_artifact = {"path": _value(stripped)}
            continue
        if in_artifacts and current_artifact is not None and stripped.startswith("kind:"):
            current_artifact["kind"] = _value(stripped)
            continue

    if current_artifact and current is not None:
        current.setdefault("artifacts", []).append(current_artifact)
    if current:
        items.append(current)
    return items


def _parse_section_items(lines: list[str], section: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    in_section = False
    active_list: str | None = None
    section_indent = 0

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        if stripped == f"{section}:":
            in_section = True
            section_indent = indent
            continue
        if not in_section:
            continue
        if indent <= section_indent and not stripped.startswith("-"):
            break
        if stripped.startswith("- id:"):
            if current:
                items.append(current)
            current = {"id": _value(stripped), "metrics": [], "tags": []}
            active_list = None
            continue
        if current is None:
            continue
        if stripped.endswith(":") and not stripped.startswith("-"):
            active_list = stripped[:-1]
            current.setdefault(active_list, [])
            continue
        if stripped.startswith("-") and active_list:
            current.setdefault(active_list, []).append(stripped[1:].strip())
            continue
        if ":" in stripped and not stripped.startswith("-"):
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()
            active_list = None
    if current:
        items.append(current)
    return items


def _missing_fields(item: dict[str, Any], fields: list[str]) -> list[str]:
    missing: list[str] = []
    for field in fields:
        value = item.get(field)
        if value is None or str(value).strip() in {"", "TBD", "none"}:
            missing.append(field)
    return missing


def _check_skill_map(path: Path) -> dict[str, Any]:
    lines, findings = _read(path)
    items = _parse_top_level_items(lines)
    item_results: list[dict[str, Any]] = []
    if not items:
        findings.append("skill-map:no-items")
    for item in items:
        skill_id = str(item.get("skill_id") or "unknown")
        item_findings = [f"missing:{field}" for field in _missing_fields(item, REQUIRED_SKILL_FIELDS)]
        if item.get("change_policy") != "hard":
            item_findings.append("change_policy:not-hard")
        linked = item.get("linked_tasks")
        if not isinstance(linked, list) or "TASK-AR-204" not in linked:
            item_findings.append("linked_tasks:missing-TASK-AR-204")
        artifacts = item.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            item_findings.append("artifacts:missing")
        else:
            for idx, artifact in enumerate(artifacts, start=1):
                item_findings.extend(
                    f"artifacts:{idx}:missing:{field}" for field in _missing_fields(artifact, REQUIRED_ARTIFACT_FIELDS)
                )
                artifact_path = artifact.get("path")
                if artifact_path and artifact_path != "none" and not Path(str(artifact_path)).exists():
                    item_findings.append(f"artifacts:{idx}:path-not-found:{artifact_path}")
        if item_findings:
            findings.extend(f"{skill_id}:{finding}" for finding in item_findings)
        item_results.append({"id": skill_id, "findings": item_findings})
    return {"items": len(items), "findings": findings, "item_results": item_results}


def _check_migration_map(path: Path) -> dict[str, Any]:
    lines, findings = _read(path)
    items = _parse_section_items(lines, "items")
    item_results: list[dict[str, Any]] = []
    if not items:
        findings.append("migration-map:no-items")
    for item in items:
        item_id = str(item.get("id") or "unknown")
        item_findings = [f"missing:{field}" for field in _missing_fields(item, REQUIRED_MIGRATION_APPROVAL_FIELDS)]
        status = str(item.get("status") or "")
        if status in {"missing", "deprecated", "changed"} and not item.get("target_state") and item.get("release_blocking") == "false":
            item_findings.append("release_blocking_false_without_target_state")
        if str(item.get("approved_by") or "").upper() == "TBD":
            item_findings.append("approved_by:TBD")
        if item_findings:
            findings.extend(f"{item_id}:{finding}" for finding in item_findings)
        item_results.append({"id": item_id, "status": status, "findings": item_findings})
    return {"items": len(items), "findings": findings, "item_results": item_results}


def _check_context_sources(path: Path) -> dict[str, Any]:
    lines, findings = _read(path)
    tiers = _parse_section_items(lines, "source_tiers")
    tier_results: list[dict[str, Any]] = []
    if not tiers:
        findings.append("context-sources:no-source-tiers")
    for tier in tiers:
        tier_id = str(tier.get("id") or "unknown")
        tier_findings = [f"missing:{field}" for field in _missing_fields(tier, REQUIRED_CONTEXT_FIELDS)]
        if tier_findings:
            findings.extend(f"{tier_id}:{finding}" for finding in tier_findings)
        tier_results.append({"id": tier_id, "findings": tier_findings})
    text = "\n".join(lines)
    for required in ["definition_policy:", "query_policy:", "required_metadata:", "required_fields:"]:
        if required not in text:
            findings.append(f"context-sources:missing:{required.rstrip(':')}")
    return {"items": len(tiers), "findings": findings, "item_results": tier_results}


def _check_dataset_catalog(path: Path) -> dict[str, Any]:
    lines, findings = _read(path)
    datasets = _parse_section_items(lines, "datasets")
    dataset_results: list[dict[str, Any]] = []
    if not datasets:
        findings.append("dataset-catalog:no-datasets")
    for dataset in datasets:
        dataset_id = str(dataset.get("id") or "unknown")
        dataset_findings = [f"missing:{field}" for field in _missing_fields(dataset, REQUIRED_DATASET_FIELDS)]
        location = dataset.get("location")
        if location and not Path(str(location)).exists():
            dataset_findings.append(f"location:not-found:{location}")
        try:
            if float(str(dataset.get("minimum_score", "0"))) < 0.90:
                dataset_findings.append("minimum_score:below-0.90")
        except ValueError:
            dataset_findings.append("minimum_score:not-number")
        if dataset_findings:
            findings.extend(f"{dataset_id}:{finding}" for finding in dataset_findings)
        dataset_results.append({"id": dataset_id, "findings": dataset_findings})
    return {"items": len(datasets), "findings": findings, "item_results": dataset_results}


def evaluate(
    skill_map: Path,
    migration_map: Path,
    context_sources: Path,
    dataset_catalog: Path,
) -> dict[str, Any]:
    sections = {
        "skill_data_map": _check_skill_map(skill_map),
        "migration_compat_map": _check_migration_map(migration_map),
        "context_sources": _check_context_sources(context_sources),
        "dataset_catalog": _check_dataset_catalog(dataset_catalog),
    }
    findings: list[str] = []
    for section, result in sections.items():
        findings.extend(f"{section}:{finding}" for finding in result["findings"])
    return {
        "schema": "agent-runtime-co-location-gate/v1",
        "evaluation_mode": "skill_data_code_colocation",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if not findings else "block",
        "release_route": "ready_for_release_redecision" if not findings else "hold_for_data",
        "blocked_task": None if not findings else "TASK-AR-204",
        "inputs": {
            "skill_map": skill_map.as_posix(),
            "migration_map": migration_map.as_posix(),
            "context_sources": context_sources.as_posix(),
            "dataset_catalog": dataset_catalog.as_posix(),
        },
        "findings": findings,
        "sections": sections,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-map", type=Path, default=DEFAULT_SKILL_MAP)
    parser.add_argument("--migration-map", type=Path, default=DEFAULT_MIGRATION_MAP)
    parser.add_argument("--context-sources", type=Path, default=DEFAULT_CONTEXT_SOURCES)
    parser.add_argument("--dataset-catalog", type=Path, default=DEFAULT_DATASET_CATALOG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.skill_map, args.migration_map, args.context_sources, args.dataset_catalog)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"status={report['status']} route={report['release_route']} "
        f"findings={len(report['findings'])} out={args.out.as_posix()}"
    )
    for section, result in report["sections"].items():
        print(f"{section} items={result['items']} findings={len(result['findings'])}")
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
