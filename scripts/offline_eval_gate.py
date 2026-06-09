"""Offline eval gate for agent_runtime project goldsets.

This gate checks whether committed project eval datasets are ready to support
the 90% release gate. It intentionally blocks when the goldset is too small or
missing required policy metadata, instead of treating absent predictions as a
pass.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CATALOG = Path("agents/project/DATASET-CATALOG.yml")
DEFAULT_POLICY = Path("agents/project/EVAL-POLICY.yml")
DEFAULT_OUT = Path("reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json")


@dataclass
class DatasetSpec:
    id: str
    location: Path
    minimum_score: float
    metrics: list[str]
    tags: list[str]


def _parse_list_block(lines: list[str], start_key: str) -> list[str]:
    values: list[str] = []
    in_block = False
    base_indent = 0
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith(f"{start_key}:"):
            in_block = True
            base_indent = len(raw) - len(raw.lstrip())
            continue
        if not in_block:
            continue
        indent = len(raw) - len(raw.lstrip())
        if stripped and indent <= base_indent and not stripped.startswith("-"):
            break
        if stripped.startswith("-"):
            values.append(stripped[1:].strip())
    return values


def _parse_policy(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    minimum = 0.90
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("minimum_score_by_domain:"):
            minimum = float(stripped.split(":", 1)[1].strip())
            break
    return {
        "minimum_score_by_domain": minimum,
        "required_case_types": _parse_list_block(lines, "required_case_types"),
        "required_metrics": _parse_list_block(lines, "required_metrics"),
        "required_tradeoff_fields": _parse_list_block(lines, "required_tradeoff_fields"),
    }


def _parse_catalog(path: Path) -> list[DatasetSpec]:
    lines = path.read_text(encoding="utf-8").splitlines()
    datasets: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    active_list: str | None = None
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("- id:"):
            if current:
                datasets.append(current)
            current = {"id": stripped.split(":", 1)[1].strip(), "metrics": [], "tags": []}
            active_list = None
            continue
        if current is None:
            continue
        if stripped.startswith("location:"):
            current["location"] = stripped.split(":", 1)[1].strip()
            active_list = None
        elif stripped.startswith("minimum_score:"):
            current["minimum_score"] = float(stripped.split(":", 1)[1].strip())
            active_list = None
        elif stripped.startswith("metrics:"):
            active_list = "metrics"
        elif stripped.startswith("tags:"):
            active_list = "tags"
        elif stripped.startswith("-") and active_list:
            current[active_list].append(stripped[1:].strip())
        elif stripped and not stripped.startswith("#"):
            active_list = None
    if current:
        datasets.append(current)

    specs: list[DatasetSpec] = []
    for item in datasets:
        if "location" not in item:
            continue
        specs.append(
            DatasetSpec(
                id=str(item["id"]),
                location=Path(str(item["location"])),
                minimum_score=float(item.get("minimum_score", 0.90)),
                metrics=list(item.get("metrics", [])),
                tags=list(item.get("tags", [])),
            )
        )
    return specs


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows, [f"dataset-missing:{path.as_posix()}"]
    for idx, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"json-invalid:{path.as_posix()}:{idx}:{exc.msg}")
            continue
        if not isinstance(value, dict):
            errors.append(f"json-not-object:{path.as_posix()}:{idx}")
            continue
        rows.append(value)
    return rows, errors


def _case_score(row: dict[str, Any]) -> tuple[float, list[str]]:
    required = ["id", "domain", "question", "difficulty", "label"]
    expected_any = [
        "expected_source_tier",
        "expected_overlay_files",
        "expected_footer_tags",
        "expected_required_metadata",
        "expected_required_fields",
        "expected_outcome",
    ]
    missing = [name for name in required if not row.get(name)]
    if not any(row.get(name) for name in expected_any):
        missing.append("expected_*")
    if not row.get("case_type"):
        missing.append("case_type")
    if not row.get("source_refs"):
        missing.append("source_refs")
    if not row.get("query_contract"):
        missing.append("query_contract")
    denominator = len(required) + 4
    score = max(0.0, (denominator - len(missing)) / denominator)
    return score, missing


def evaluate(catalog: Path, policy_path: Path) -> dict[str, Any]:
    policy = _parse_policy(policy_path)
    specs = _parse_catalog(catalog)
    datasets: list[dict[str, Any]] = []
    blocked = False
    for spec in specs:
        rows, load_errors = _load_jsonl(spec.location)
        case_scores: list[float] = []
        findings = list(load_errors)
        case_types = set()
        domains = set()
        for row in rows:
            score, missing = _case_score(row)
            case_scores.append(score)
            if row.get("case_type"):
                case_types.add(str(row["case_type"]))
            if row.get("domain"):
                domains.add(str(row["domain"]))
            if missing:
                findings.append(f"{row.get('id', 'unknown')}:missing:{','.join(missing)}")
        required_case_types = set(policy["required_case_types"])
        missing_case_types = sorted(required_case_types - case_types)
        if missing_case_types:
            findings.append("missing_case_types:" + ",".join(missing_case_types))
        if len(rows) < len(required_case_types):
            findings.append(f"insufficient_cases:{len(rows)}<{len(required_case_types)}")
        score = sum(case_scores) / len(case_scores) if case_scores else 0.0
        status = "pass" if score >= spec.minimum_score and not findings else "block"
        if status == "block":
            blocked = True
        datasets.append(
            {
                "id": spec.id,
                "location": spec.location.as_posix(),
                "minimum_score": spec.minimum_score,
                "score": round(score, 4),
                "status": status,
                "cases": len(rows),
                "domains": sorted(domains),
                "missing_case_types": missing_case_types,
                "findings": findings,
            }
        )
    return {
        "schema": "agent-runtime-offline-eval-report/v1",
        "evaluation_mode": "goldset_readiness",
        "accuracy_claim": "not_model_output_accuracy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog": catalog.as_posix(),
        "policy": policy_path.as_posix(),
        "minimum_score_by_domain": policy["minimum_score_by_domain"],
        "status": "block" if blocked else "pass",
        "datasets": datasets,
        "correction_proposals": [
            {
                "type": "goldset_metadata_completion",
                "owner": "lead_engineer",
                "route": "TASK-AR-205",
                "next_action": "add case_type, source_refs, query_contract, and required case coverage before release readiness can pass",
            }
        ]
        if blocked
        else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    report = evaluate(args.catalog, args.policy)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={report['status']} out={args.out.as_posix()}")
    for dataset in report["datasets"]:
        print(
            f"{dataset['id']} status={dataset['status']} "
            f"score={dataset['score']} cases={dataset['cases']} findings={len(dataset['findings'])}"
        )
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
