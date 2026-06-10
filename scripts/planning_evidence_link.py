"""Link eval, reviewer, correction, grader, and A2A evidence to planning proposals."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - evidence linker preserves load failures as findings.
        return None, str(exc)
    if not isinstance(value, dict):
        return None, "json-root-not-object"
    return value, None


def _proposal(
    *,
    source: Path,
    kind: str,
    severity: str,
    route: str,
    evidence_id: str,
    recommendation: str,
    trace_id: str = "",
) -> dict[str, Any]:
    return {
        "kind": kind,
        "severity": severity,
        "route": route,
        "source_report": source.as_posix(),
        "evidence_id": evidence_id,
        "trace_id": trace_id,
        "recommendation": recommendation,
        "approval_required": True,
    }


def _offline_eval(path: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for dataset in report.get("datasets") or []:
        if not isinstance(dataset, dict):
            continue
        status = str(dataset.get("status") or "")
        if status != "pass":
            proposals.append(
                _proposal(
                    source=path,
                    kind="eval_regression",
                    severity="block",
                    route="TASK-AR-205",
                    evidence_id=str(dataset.get("id") or "unknown-dataset"),
                    recommendation="route failed eval dataset to correction and block release readiness until rerun passes",
                )
            )
    return proposals


def _prediction_or_grader(path: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    records = report.get("case_results") or report.get("record_results") or report.get("grader_results") or []
    for record in records:
        if not isinstance(record, dict):
            continue
        findings = record.get("findings") or []
        score = record.get("score")
        passed = record.get("passed")
        failed = bool(findings) or passed is False
        try:
            failed = failed or float(score) < 0.9
        except (TypeError, ValueError):
            pass
        if failed:
            proposals.append(
                _proposal(
                    source=path,
                    kind="grader_regression",
                    severity="block",
                    route="TASK-AR-243",
                    evidence_id=str(record.get("case_id") or record.get("id") or record.get("trace_id") or "unknown-case"),
                    trace_id=str(record.get("trace_id") or ""),
                    recommendation="create planning proposal tied to failed trace/grader evidence and acceptance criteria",
                )
            )
    return proposals


def _live_review(path: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for record in report.get("record_results") or []:
        if not isinstance(record, dict):
            continue
        if record.get("findings"):
            proposals.append(
                _proposal(
                    source=path,
                    kind="live_review_correction",
                    severity="watch",
                    route="TASK-AR-207",
                    evidence_id=str(record.get("id") or "unknown-live-review"),
                    trace_id=str(record.get("trace_id") or ""),
                    recommendation="route reviewer findings to correction collector before acceptance",
                )
            )
    return proposals


def _correction(path: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for written in report.get("written") or []:
        proposals.append(
            _proposal(
                source=path,
                kind="correction_proposal",
                severity="watch",
                route="TASK-AR-207",
                evidence_id=str(written),
                recommendation="track correction proposal through owner approval before applying definitions",
            )
        )
    return proposals


def _a2a(path: Path, report: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    chains = report.get("chain_results") or []
    if not chains:
        proposals.append(
            _proposal(
                source=path,
                kind="missing_trace_chain",
                severity="block",
                route="TASK-AR-208",
                evidence_id="missing-a2a-chain",
                recommendation="add reconstructable request/review/decision/correction A2A trace before planning acceptance",
            )
        )
    for chain in chains:
        if not isinstance(chain, dict):
            continue
        evidence_id = "/".join(
            str(chain.get(key) or "")
            for key in ("contextId", "taskId", "decision_cycle_id")
        )
        if chain.get("findings"):
            proposals.append(
                _proposal(
                    source=path,
                    kind="a2a_trace_gap",
                    severity="block",
                    route="TASK-AR-208",
                    evidence_id=evidence_id,
                    recommendation="repair A2A trace continuity before accepting multi-cycle planning proposal",
                )
            )
    return proposals


HANDLERS = {
    "offline_eval": _offline_eval,
    "prediction": _prediction_or_grader,
    "grader": _prediction_or_grader,
    "live_review": _live_review,
    "correction": _correction,
    "a2a": _a2a,
}


def build_report(inputs: list[tuple[str, Path]]) -> dict[str, Any]:
    findings: list[str] = []
    proposals: list[dict[str, Any]] = []
    scanned: list[dict[str, str]] = []

    for kind, path in inputs:
        scanned.append({"kind": kind, "path": path.as_posix()})
        report, error = _load_json(path)
        if error:
            findings.append(f"{kind}:{path.as_posix()}:{error}")
            proposals.append(
                _proposal(
                    source=path,
                    kind="missing_or_invalid_evidence",
                    severity="block",
                    route="TASK-AR-243",
                    evidence_id=path.as_posix(),
                    recommendation="provide valid evidence report before planning proposal acceptance",
                )
            )
            continue
        assert report is not None
        handler = HANDLERS[kind]
        proposals.extend(handler(path, report))

    status = "block" if any(item["severity"] == "block" for item in proposals) or findings else "pass"
    if status == "pass" and any(item["severity"] == "watch" for item in proposals):
        status = "watch"
    return {
        "schema": "agent-runtime-planning-evidence-link/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "scanned": scanned,
        "findings": findings,
        "proposal_count": len(proposals),
        "proposals": proposals,
    }


def _add_inputs(args: argparse.Namespace) -> list[tuple[str, Path]]:
    inputs: list[tuple[str, Path]] = []
    for kind in HANDLERS:
        for path in getattr(args, kind) or []:
            inputs.append((kind, path))
    return inputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Build planning proposals from eval/reviewer/correction/A2A evidence")
    for kind in HANDLERS:
        parser.add_argument(f"--{kind.replace('_', '-')}", action="append", type=Path, default=[])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    report = build_report(_add_inputs(args))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={report['status']} proposals={report['proposal_count']} out={args.out.as_posix()}")
    for proposal in report["proposals"]:
        print(f"{proposal['severity']} {proposal['kind']} {proposal['evidence_id']} -> {proposal['route']}")
    return 1 if report["status"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
