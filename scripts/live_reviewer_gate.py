"""Live reviewer footer gate for agent_runtime evidence.

Validates reviewer verdict records for high-risk/live verification lanes. The
gate fails when a reviewer verdict, evidence, footer, or required risk metadata
is missing.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_INPUT = Path("agents/project/live_review/live-review-baseline-2026-06-09.jsonl")
DEFAULT_OUT = Path("reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json")

REQUIRED_FIELDS = [
    "id",
    "task_id",
    "reviewer_agent",
    "verdict",
    "evidence",
    "confidence",
    "source_tier",
    "risk",
    "ambiguity",
    "source_footer",
    "footer_tags",
    "recommend_action",
    "trace_id",
]

REQUIRED_FOOTER_TAGS = {
    "source_footer",
    "confidence",
    "source_tier",
    "risk",
    "ambiguity",
}

HIGH_RISK_VALUES = {"high", "critical"}
ALLOWED_HIGH_RISK_ACTIONS = {"owner_review", "independent_auditor_review", "block", "escalate"}


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


def _score_record(row: dict[str, Any]) -> dict[str, Any]:
    findings: list[str] = []
    checks: list[tuple[str, bool]] = []

    for field in REQUIRED_FIELDS:
        ok = bool(row.get(field))
        checks.append((f"field:{field}", ok))
        if not ok:
            findings.append(f"missing:{field}")

    footer_tags = _as_set(row.get("footer_tags"))
    ok = REQUIRED_FOOTER_TAGS.issubset(footer_tags)
    checks.append(("required_footer_tags", ok))
    if not ok:
        missing = sorted(REQUIRED_FOOTER_TAGS - footer_tags)
        findings.append("missing_footer_tags:" + ",".join(missing))

    risk = str(row.get("risk", "")).lower()
    if risk in HIGH_RISK_VALUES:
        action = str(row.get("recommend_action", ""))
        ok = action in ALLOWED_HIGH_RISK_ACTIONS
        checks.append(("high_risk_action", ok))
        if not ok:
            findings.append("high_risk_requires_owner_or_auditor_route")
        ok = bool(row.get("approved_by") or row.get("escalation_owner"))
        checks.append(("high_risk_owner_or_auditor", ok))
        if not ok:
            findings.append("high_risk_missing_approved_by_or_escalation_owner")

    verdict = str(row.get("verdict", "")).lower()
    ok = verdict in {"accept", "reviewer_review", "block", "escalate"}
    checks.append(("valid_verdict", ok))
    if not ok:
        findings.append("invalid_verdict")

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    return {
        "id": row.get("id", "unknown"),
        "task_id": row.get("task_id"),
        "score": round(passed / total if total else 0.0, 4),
        "passed": passed,
        "total": total,
        "findings": findings,
    }


def evaluate(input_path: Path) -> dict[str, Any]:
    rows, load_errors = _load_jsonl(input_path)
    record_results = [_score_record(row) for row in rows]
    findings = list(load_errors)
    for result in record_results:
        findings.extend(f"{result['id']}:{finding}" for finding in result["findings"])
    score = sum(float(item["score"]) for item in record_results) / len(record_results) if record_results else 0.0
    status = "pass" if score >= 1.0 and not findings else "block"
    return {
        "schema": "agent-runtime-live-reviewer-gate/v1",
        "evaluation_mode": "live_reviewer_footer",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": input_path.as_posix(),
        "status": status,
        "score": round(score, 4),
        "records": len(rows),
        "findings": findings,
        "record_results": record_results,
        "correction_proposals": [
            {
                "type": "reviewer_footer_failure",
                "owner": "independent_auditor",
                "route": "TASK-AR-207",
                "next_action": "create correction proposal for missing reviewer/footer metadata",
            }
        ]
        if status == "block"
        else [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    report = evaluate(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={report['status']} score={report['score']} out={args.out.as_posix()}")
    for item in report["record_results"]:
        print(f"{item['id']} score={item['score']} findings={len(item['findings'])}")
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
