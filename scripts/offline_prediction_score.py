"""Score offline eval predictions against agent_runtime goldsets.

This is the second offline-eval lane after goldset readiness. It compares
actual prediction records to expected labels and blocks release if any dataset
falls below its minimum score.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CATALOG = Path("agents/project/DATASET-CATALOG.yml")
DEFAULT_PREDICTIONS = Path("agents/project/evals/predictions/contract-baseline-2026-06-09.jsonl")
DEFAULT_OUT = Path("reviews/OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217.json")


@dataclass
class DatasetSpec:
    id: str
    location: Path
    minimum_score: float


def _parse_catalog(path: Path) -> list[DatasetSpec]:
    lines = path.read_text(encoding="utf-8").splitlines()
    datasets: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("- id:"):
            if current:
                datasets.append(current)
            current = {"id": stripped.split(":", 1)[1].strip()}
            continue
        if current is None:
            continue
        if stripped.startswith("location:"):
            current["location"] = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("minimum_score:"):
            current["minimum_score"] = float(stripped.split(":", 1)[1].strip())
    if current:
        datasets.append(current)
    return [
        DatasetSpec(
            id=str(item["id"]),
            location=Path(str(item["location"])),
            minimum_score=float(item.get("minimum_score", 0.90)),
        )
        for item in datasets
        if "location" in item
    ]


def _load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return rows, [f"missing:{path.as_posix()}"]
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


def _as_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, list):
        return {str(item) for item in value}
    return {str(value)}


def _has_nested_dict(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


def _prediction_index(predictions: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    index: dict[str, dict[str, Any]] = {}
    findings: list[str] = []
    for row in predictions:
        case_id = str(row.get("case_id") or row.get("id") or "")
        if not case_id:
            findings.append("prediction-missing-case-id")
            continue
        if case_id in index:
            findings.append(f"{case_id}:duplicate-prediction")
            continue
        index[case_id] = row
    return index, findings


def _score_case(gold: dict[str, Any], prediction: dict[str, Any] | None) -> dict[str, Any]:
    if prediction is None:
        return {"score": 0.0, "passed": 0, "total": 1, "findings": ["missing-prediction"]}

    checks: list[tuple[str, bool]] = []
    findings: list[str] = []

    required_prediction_meta = ["case_id", "generated_by", "trace_id", "answer", "source_footer"]
    for field in required_prediction_meta:
        ok = bool(prediction.get(field))
        checks.append((f"prediction_meta:{field}", ok))
        if not ok:
            findings.append(f"missing:{field}")

    if gold.get("expected_source_tier"):
        ok = prediction.get("predicted_source_tier") == gold.get("expected_source_tier")
        checks.append(("expected_source_tier", ok))
        if not ok:
            findings.append("mismatch:expected_source_tier")

    expected_overlay = _as_set(gold.get("expected_overlay_files"))
    if expected_overlay:
        predicted_overlay = _as_set(prediction.get("selected_overlay_files"))
        ok = expected_overlay.issubset(predicted_overlay)
        checks.append(("expected_overlay_files", ok))
        if not ok:
            findings.append("mismatch:expected_overlay_files")

    expected_footer = _as_set(gold.get("expected_footer_tags"))
    if expected_footer:
        predicted_footer = _as_set(prediction.get("footer_tags"))
        ok = expected_footer.issubset(predicted_footer)
        checks.append(("expected_footer_tags", ok))
        if not ok:
            findings.append("mismatch:expected_footer_tags")

    expected_metadata = _as_set(gold.get("expected_required_metadata"))
    if expected_metadata:
        predicted_metadata = _as_set(prediction.get("reported_metadata"))
        ok = expected_metadata.issubset(predicted_metadata)
        checks.append(("expected_required_metadata", ok))
        if not ok:
            findings.append("mismatch:expected_required_metadata")

    expected_fields = _as_set(gold.get("expected_required_fields"))
    if expected_fields:
        predicted_fields = _as_set(prediction.get("clarification_fields"))
        ok = expected_fields.issubset(predicted_fields)
        checks.append(("expected_required_fields", ok))
        if not ok:
            findings.append("mismatch:expected_required_fields")

    if gold.get("expected_outcome"):
        ok = prediction.get("predicted_outcome") == gold.get("expected_outcome")
        checks.append(("expected_outcome", ok))
        if not ok:
            findings.append("mismatch:expected_outcome")

    expected_refs = _as_set(gold.get("source_refs"))
    predicted_refs = _as_set(prediction.get("source_refs"))
    ok = bool(expected_refs) and expected_refs.issubset(predicted_refs)
    checks.append(("source_refs", ok))
    if not ok:
        findings.append("mismatch:source_refs")

    ok = _has_nested_dict(prediction.get("query_contract"))
    checks.append(("query_contract", ok))
    if not ok:
        findings.append("missing:query_contract")

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    score = passed / total if total else 0.0
    return {
        "score": round(score, 4),
        "passed": passed,
        "total": total,
        "findings": findings,
    }


def evaluate(catalog: Path, predictions_path: Path) -> dict[str, Any]:
    specs = _parse_catalog(catalog)
    predictions, prediction_errors = _load_jsonl(predictions_path)
    prediction_by_id, index_findings = _prediction_index(predictions)
    blocked = bool(prediction_errors or index_findings)
    datasets: list[dict[str, Any]] = []

    for spec in specs:
        gold_rows, load_errors = _load_jsonl(spec.location)
        case_results: list[dict[str, Any]] = []
        findings = list(load_errors)
        scores: list[float] = []
        for gold in gold_rows:
            case_id = str(gold.get("id", "unknown"))
            result = _score_case(gold, prediction_by_id.get(case_id))
            scores.append(float(result["score"]))
            if result["findings"]:
                findings.extend(f"{case_id}:{finding}" for finding in result["findings"])
            case_results.append({"id": case_id, **result})
        score = sum(scores) / len(scores) if scores else 0.0
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
                "cases": len(gold_rows),
                "findings": findings,
                "case_results": case_results,
            }
        )

    return {
        "schema": "agent-runtime-offline-prediction-score/v1",
        "evaluation_mode": "prediction_scoring",
        "accuracy_claim": "contract_baseline_output_accuracy",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "catalog": catalog.as_posix(),
        "predictions": predictions_path.as_posix(),
        "status": "block" if blocked else "pass",
        "prediction_file_findings": prediction_errors + index_findings,
        "datasets": datasets,
        "correction_proposals": [
            {
                "type": "offline_prediction_failure",
                "owner": "lead_engineer",
                "route": "TASK-AR-207",
                "next_action": "create correction event for failed case and rerun prediction scoring",
            }
        ]
        if blocked
        else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    report = evaluate(args.catalog, args.predictions)
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
