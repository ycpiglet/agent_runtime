"""Assess low-frequency agent and runtime-asset self-improvement signals.

This command is the read-only baseline for TASK-AR-570. It composes the existing
collaboration governance gate, runtime asset registry metric, and advisory
scribe/doc-steward checks into one measurable maturity snapshot.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import collaboration_governance_gate as collab_gate  # noqa: E402
import meeting_room  # noqa: E402
import runtime_asset_usage  # noqa: E402


SCHEMA = "agent-runtime-self-improvement-assessment/v1"
CYCLE_SCHEMA = "agent-runtime-self-improvement-cycle/v1"
REPORT_SCHEMA = "agent-runtime-self-improvement-report/v1"
SCRIBE_HOT_KEEP = 10
SCRIBE_DUE_AT = 13
SCRIBE_OVERDUE_AT = 16
DOC_STEWARD_DUE_AT = 1
DOC_STEWARD_OVERDUE_AT = 3


def _parse_now(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc).astimezone()
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc).astimezone()
    return parsed


def _effective_severity(finding: Any) -> str:
    return str(getattr(finding, "effective_severity", None) or getattr(finding, "severity", "watch"))


def _review_artifact_counts(root: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    reviews = root / "reviews"
    if reviews.is_dir():
        for path in reviews.iterdir():
            if path.is_file():
                counts[path.name.split("-", 1)[0].upper()] += 1
    compound_log = root / "agents" / "lead_engineer" / "compound_log.md"
    if compound_log.is_file():
        counts["COMPOUND"] = compound_log.read_text(encoding="utf-8", errors="replace").count("COMPOUND-")
    return dict(sorted(counts.items()))


def _role_from_subject(subject: str) -> str:
    if ":" not in subject:
        return subject
    return subject.split(":", 1)[1]


def _role_root_cause(subject: str, severity: str, waiver_id: str | None) -> str:
    if waiver_id or severity == "waived":
        return "waiver_debt"
    if subject.startswith("role-monitor:"):
        return "missing_claim_evidence"
    if subject.startswith("role-usage:"):
        return "missing_required_role_claim"
    return "collaboration_signal"


def _role_gaps(findings: list[Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for finding in findings:
        subject = str(getattr(finding, "subject", ""))
        if not (subject.startswith("role-usage:") or subject.startswith("role-monitor:")):
            continue
        waiver_id = getattr(finding, "waiver_id", None)
        severity = _effective_severity(finding)
        gaps.append(
            {
                "role": _role_from_subject(subject),
                "subject": subject,
                "severity": severity,
                "root_cause": _role_root_cause(subject, severity, waiver_id),
                "path": str(getattr(finding, "path", "")),
                "detail": str(getattr(finding, "detail", "")),
                "waiver_id": waiver_id,
            }
        )
    return gaps


def _asset_root_cause(metric: Any) -> str:
    usage = int(getattr(metric, "usage_count", 0))
    reuse = int(getattr(metric, "distinct_evidence_hits", 0))
    lifecycle = str(getattr(metric, "lifecycle", ""))
    if usage == 0:
        return "no_usage_evidence"
    if reuse <= 1:
        return "low_reuse_evidence"
    if lifecycle == "observe":
        return "watch_lifecycle"
    return "usage_finding"


def _asset_finding_root_cause(subject: str, detail: str) -> str:
    if subject.startswith("asset-usage-low:"):
        if "usage_count=0" in detail:
            return "no_usage_evidence"
        return "low_usage_below_threshold"
    if subject.startswith("asset-evidence-missing:"):
        return "missing_evidence_path"
    if subject.startswith("asset-missing:"):
        return "missing_registered_path"
    return "asset_gate_finding"


def _asset_gaps(findings: list[Any], metrics: list[Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    seen: set[str] = set()
    for finding in findings:
        subject = str(getattr(finding, "subject", ""))
        if not subject.startswith("asset-"):
            continue
        gaps.append(
            {
                "asset_id": subject.split(":", 1)[1] if ":" in subject else subject,
                "subject": subject,
                "severity": str(getattr(finding, "severity", "watch")),
                "root_cause": _asset_finding_root_cause(subject, str(getattr(finding, "detail", ""))),
                "path": str(getattr(finding, "path", "")),
                "detail": str(getattr(finding, "detail", "")),
            }
        )
        seen.add(subject.split(":", 1)[1] if ":" in subject else subject)
    for metric in metrics:
        asset_id = str(getattr(metric, "asset_id", ""))
        reuse = int(getattr(metric, "distinct_evidence_hits", 0))
        if reuse > 1 or asset_id in seen:
            continue
        gaps.append(
            {
                "asset_id": asset_id,
                "subject": f"asset-low-reuse:{asset_id}",
                "severity": "watch",
                "root_cause": _asset_root_cause(metric),
                "kind": str(getattr(metric, "kind", "")),
                "status": str(getattr(metric, "status", "")),
                "lifecycle": str(getattr(metric, "lifecycle", "")),
                "usage_count": int(getattr(metric, "usage_count", 0)),
                "reuse": reuse,
            }
        )
    return gaps


def _count_scribe_hot_entries(root: Path) -> int | None:
    status = root / "agents" / "lead_engineer" / "STATUS.md"
    if not status.is_file():
        status = root / "STATUS.md"
    if not status.is_file():
        return None
    in_section = False
    seen_section = False
    count = 0
    for line in status.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## 현재 한 줄 요약"
            seen_section = seen_section or in_section
            continue
        if in_section and re.match(r"^- ", line):
            count += 1
    return count if seen_section else None


def _scribe_state(count: int | None) -> str:
    if count is None:
        return "unknown"
    if count >= SCRIBE_OVERDUE_AT:
        return "overdue"
    if count >= SCRIBE_DUE_AT:
        return "due"
    return "ok"


def _newest_num(glob: str, base: Path) -> int:
    nums: list[int] = []
    if not base.is_dir():
        return -1
    for path in base.glob(glob):
        match = re.search(r"-(\d+)", path.stem)
        if match:
            nums.append(int(match.group(1)))
    return max(nums) if nums else -1


def _doc_steward_signal(root: Path) -> dict[str, Any]:
    agents_dir = root / "agents"
    skill_dirs = {path.parent.name for path in agents_dir.glob("*/SKILL.md")}
    non_orgchart_ok = {"lead_engineer"}
    claude = root / "CLAUDE.md"
    referenced: set[str] = set()
    if claude.is_file():
        referenced = set(re.findall(r"agents/([a-z_]+)/", claude.read_text(encoding="utf-8", errors="replace")))
    orphans = sorted(skill_dirs - referenced - non_orgchart_ok)

    lead = agents_dir / "lead_engineer"
    reviews = lead / "reviews"
    newest_cycle = max(_newest_num("CYCLE-*.md", lead), _newest_num("REVIEW-*.md", reviews))
    missing_review = newest_cycle if newest_cycle >= 0 and not (reviews / f"REVIEW-{newest_cycle:03d}.md").exists() else None
    drift = len(orphans) + (1 if missing_review is not None else 0)
    if drift >= DOC_STEWARD_OVERDUE_AT:
        state = "overdue"
    elif drift >= DOC_STEWARD_DUE_AT:
        state = "due"
    else:
        state = "ok"
    return {
        "state": state,
        "drift_count": drift,
        "orphan_role_docs": orphans,
        "missing_review": missing_review,
        "root_cause": "advisory_due" if state != "ok" else "cadence_ok",
    }


def _advisory_signals(root: Path) -> dict[str, dict[str, Any]]:
    hot_entries = _count_scribe_hot_entries(root)
    scribe_state = _scribe_state(hot_entries)
    return {
        "scribe": {
            "state": scribe_state,
            "hot_entries": hot_entries,
            "hot_keep": SCRIBE_HOT_KEEP,
            "root_cause": "source_missing" if scribe_state == "unknown" else ("advisory_due" if scribe_state in {"due", "overdue"} else "cadence_ok"),
        },
        "doc_steward": _doc_steward_signal(root),
    }


def _score(
    *,
    collab_findings: list[Any],
    role_gaps: list[dict[str, Any]],
    asset_gaps: list[dict[str, Any]],
    advisory: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    unwaived_blocks = sum(1 for finding in collab_findings if getattr(finding, "severity", "") == "block" and not getattr(finding, "waiver_id", None))
    waiver_debt = sum(1 for gap in role_gaps if gap["root_cause"] == "waiver_debt")
    monitored_role_gaps = sum(1 for gap in role_gaps if gap["subject"].startswith("role-monitor:"))
    low_reuse_assets = sum(1 for gap in asset_gaps if gap["subject"].startswith("asset-low-reuse:"))
    lifecycle_watch = sum(1 for finding in collab_findings if str(getattr(finding, "subject", "")).startswith("lifecycle:"))
    advisory_due = sum(1 for signal in advisory.values() if signal.get("state") == "due")
    advisory_overdue = sum(1 for signal in advisory.values() if signal.get("state") == "overdue")
    advisory_unknown = sum(1 for signal in advisory.values() if signal.get("state") == "unknown")

    deductions = {
        "unwaived_blocks": unwaived_blocks * 15,
        "waiver_debt": waiver_debt * 10,
        "monitored_role_gaps": monitored_role_gaps * 5,
        "low_reuse_assets": min(low_reuse_assets * 2, 20),
        "lifecycle_watch": min(lifecycle_watch, 10),
        "advisory_due": advisory_due * 5 + advisory_overdue * 10 + advisory_unknown * 3,
    }
    value = max(0, 100 - sum(deductions.values()))
    if unwaived_blocks:
        level = "blocked"
    elif value >= 90 and waiver_debt == 0 and monitored_role_gaps <= 1:
        level = "mature"
    elif value >= 65:
        level = "improving"
    else:
        level = "immature"
    return {
        "value": value,
        "maturity_level": level,
        "deductions": deductions,
        "inputs": {
            "unwaived_blocks": unwaived_blocks,
            "waiver_debt": waiver_debt,
            "monitored_role_gaps": monitored_role_gaps,
            "low_reuse_assets": low_reuse_assets,
            "lifecycle_watch": lifecycle_watch,
            "advisory_due": advisory_due,
            "advisory_overdue": advisory_overdue,
            "advisory_unknown": advisory_unknown,
        },
    }


def assess(root: Path, *, now: datetime) -> dict[str, Any]:
    root = root.resolve()
    collab_findings = collab_gate.analyze(root, now)
    asset_findings, asset_metrics = runtime_asset_usage.analyze(root)
    roles = _role_gaps(collab_findings)
    assets = _asset_gaps(asset_findings, asset_metrics)
    advisory = _advisory_signals(root)
    collab_counts = Counter(_effective_severity(finding) for finding in collab_findings)
    asset_counts = Counter(str(getattr(finding, "severity", "watch")) for finding in asset_findings)
    score = _score(collab_findings=collab_findings, role_gaps=roles, asset_gaps=assets, advisory=advisory)
    cycle_status = _cycle_artifact_status(root, now=now, requires_compound=_debt_requires_compound_from_parts(score, roles, assets, advisory))

    return {
        "schema": SCHEMA,
        "generated_at": now.isoformat(timespec="seconds"),
        "root": str(root),
        "status": "pass" if score["maturity_level"] in {"mature", "improving"} else "watch",
        "maturity_level": score["maturity_level"],
        "score": score,
        "collaboration": {
            "findings": len(collab_findings),
            "block": collab_counts.get("block", 0),
            "watch": collab_counts.get("watch", 0),
            "waived": collab_counts.get("waived", 0),
            "role_gaps": roles,
        },
        "runtime_assets": {
            "assets": len(asset_metrics),
            "findings": len(asset_findings),
            "block": asset_counts.get("block", 0),
            "watch": asset_counts.get("watch", 0),
            "usage_total": sum(int(getattr(metric, "usage_count", 0)) for metric in asset_metrics),
            "asset_gaps": assets,
        },
        "advisory_signals": advisory,
        "product_surfaces": {
            "artifact_counts": _review_artifact_counts(root),
            "required_cycle_surfaces": ["REVIEW", "MEETING", "SEMINAR", "RETRO", "COMPOUND"],
            "current_cycle": cycle_status,
        },
        "next": _next_actions(score["maturity_level"], roles, assets, advisory, cycle_recorded=cycle_status["recorded"]),
    }


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _today(now: datetime) -> str:
    return now.date().isoformat()


def _artifact_paths(today: str) -> dict[str, str]:
    return {
        "review": f"reviews/REVIEW-{today}-self-improvement-cycle.md",
        "meeting": f"reviews/MEETING-{today}-self-improvement-cycle-sync.md",
        "seminar": f"reviews/SEMINAR-{today}-self-improvement-cadence.md",
        "retro": f"reviews/RETRO-{today}-self-improvement-cycle.md",
        "compound": "agents/lead_engineer/compound_log.md",
        "casebook": "agents/project/casebooks/failure-and-compound-casebook.md",
    }


def _thresholds(payload: dict[str, Any]) -> list[dict[str, Any]]:
    score = payload["score"]
    inputs = score["inputs"]
    role_gaps = payload["collaboration"]["role_gaps"]
    asset_gaps = payload["runtime_assets"]["asset_gaps"]
    scribe_state = payload["advisory_signals"]["scribe"]["state"]
    return [
        {"metric": "score", "current": score["value"], "target_next": 65, "target_mature": 90},
        {"metric": "role_gaps", "current": len(role_gaps), "target_next": 3, "target_mature": 1},
        {"metric": "waiver_debt", "current": inputs["waiver_debt"], "target_next": 0, "target_mature": 0},
        {"metric": "asset_gaps", "current": len(asset_gaps), "target_next": 12, "target_mature": 5},
        {"metric": "low_reuse_assets", "current": inputs["low_reuse_assets"], "target_next": 8, "target_mature": 2},
        {"metric": "scribe_state", "current": scribe_state, "target_next": "known", "target_mature": "ok"},
    ]


def _debt_requires_compound(payload: dict[str, Any]) -> bool:
    inputs = payload["score"]["inputs"]
    return (
        inputs["waiver_debt"] > 0
        or inputs["monitored_role_gaps"] >= 3
        or inputs["low_reuse_assets"] >= 3
        or payload["advisory_signals"]["scribe"]["state"] in {"unknown", "due", "overdue"}
    )


def _debt_requires_compound_from_parts(
    score: dict[str, Any],
    role_gaps: list[dict[str, Any]],
    asset_gaps: list[dict[str, Any]],
    advisory: dict[str, dict[str, Any]],
) -> bool:
    inputs = score["inputs"]
    return (
        inputs["waiver_debt"] > 0
        or inputs["monitored_role_gaps"] >= 3
        or inputs["low_reuse_assets"] >= 3
        or advisory["scribe"]["state"] in {"unknown", "due", "overdue"}
        or bool(role_gaps and asset_gaps)
    )


def _cycle_artifact_status(root: Path, *, now: datetime, requires_compound: bool) -> dict[str, Any]:
    paths = _artifact_paths(_today(now))
    required = ["review", "meeting", "seminar", "retro"]
    if requires_compound:
        required.extend(["compound", "casebook"])
    artifacts: list[dict[str, Any]] = []
    for kind, rel_path in paths.items():
        if kind not in required:
            continue
        exists = (root / rel_path).exists()
        artifacts.append({"kind": kind, "path": rel_path, "exists": exists})
    present = sum(1 for artifact in artifacts if artifact["exists"])
    return {
        "date": _today(now),
        "recorded": present == len(artifacts),
        "present": present,
        "required": len(artifacts),
        "artifacts": artifacts,
    }


def _table(rows: list[dict[str, Any]], columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def _role_rows(payload: dict[str, Any], *, limit: int = 8) -> list[dict[str, Any]]:
    return [
        {
            "role": gap["role"],
            "root_cause": gap["root_cause"],
            "severity": gap["severity"],
            "evidence": gap.get("subject", ""),
        }
        for gap in payload["collaboration"]["role_gaps"][:limit]
    ] or [{"role": "none", "root_cause": "none", "severity": "pass", "evidence": "-"}]


def _asset_rows(payload: dict[str, Any], *, limit: int = 8) -> list[dict[str, Any]]:
    return [
        {
            "asset": gap["asset_id"],
            "root_cause": gap["root_cause"],
            "severity": gap["severity"],
            "evidence": gap.get("subject", ""),
        }
        for gap in payload["runtime_assets"]["asset_gaps"][:limit]
    ] or [{"asset": "none", "root_cause": "none", "severity": "pass", "evidence": "-"}]


def _render_review(payload: dict[str, Any], *, today: str, generated_at: str, paths: dict[str, str]) -> str:
    score = payload["score"]
    advisory = payload["advisory_signals"]
    next_actions = [
        action for action in payload["next"] if not action.startswith("Run the cycle unit to record")
    ] or ["Re-run assessment after the next cycle and compare against the thresholds below."]
    lines: list[str] = [
        "---",
        f"title: Self Improvement Cycle {today}",
        f"date: {today}",
        f"signal: {payload['status']}",
        f"score: {score['value']}",
        "tags: [self-improvement, review, task-ar-571]",
        "---",
        "",
        f"# Self Improvement Cycle {today}",
        "",
        "## Bottom Line",
        "",
        f"- Maturity: `{payload['maturity_level']}` at `{score['value']}/100`.",
        f"- Role gaps: `{len(payload['collaboration']['role_gaps'])}`.",
        f"- Asset gaps: `{len(payload['runtime_assets']['asset_gaps'])}`.",
        "- This record is generated from repository evidence; it does not claim live multi-agent dialogue.",
        "",
        "## Signal",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| generated_at | `{generated_at}` |",
        f"| scribe | `{advisory['scribe']['state']}` |",
        f"| doc_steward | `{advisory['doc_steward']['state']}` |",
        f"| collaboration_findings | `{payload['collaboration']['findings']}` |",
        f"| runtime_assets | `{payload['runtime_assets']['assets']}` |",
        f"| runtime_usage_total | `{payload['runtime_assets']['usage_total']}` |",
        "",
        "## Role Gaps",
        "",
        *_table(_role_rows(payload), ["role", "root_cause", "severity", "evidence"]),
        "",
        "## Runtime Asset Gaps",
        "",
        *_table(_asset_rows(payload), ["asset", "root_cause", "severity", "evidence"]),
        "",
        "## Cycle Artifacts",
        "",
        "| Surface | Path |",
        "| --- | --- |",
        f"| meeting | `{paths['meeting']}` |",
        f"| seminar | `{paths['seminar']}` |",
        f"| retro | `{paths['retro']}` |",
        f"| compound | `{paths['compound']}` |",
        f"| casebook | `{paths['casebook']}` |",
        "",
        "## Next-Cycle Thresholds",
        "",
        *_table(_thresholds(payload), ["metric", "current", "target_next", "target_mature"]),
        "",
        "## Next",
        "",
    ]
    lines.extend(f"- {action}" for action in next_actions)
    lines.append("")
    return "\n".join(lines)


def _render_meeting(*, today: str, generated_at: str) -> str:
    return meeting_room.render_skeleton(
        meeting_id=f"MEETING-{today}-self-improvement-cycle-sync",
        topic="Self Improvement Cycle Sync",
        participants=["lead-engineer", "scribe", "doc-steward", "reviewer"],
        meeting_type="meeting",
        rounds=3,
        task_id="TASK-AR-571",
        generated_at=generated_at,
    )


def _render_seminar(*, today: str, generated_at: str) -> str:
    return meeting_room.render_skeleton(
        meeting_id=f"SEMINAR-{today}-self-improvement-cadence",
        topic="Self Improvement Cadence Seminar",
        participants=["lead-engineer", "reviewer", "skeptic", "doc-steward"],
        meeting_type="seminar",
        rounds=2,
        task_id="TASK-AR-571",
        generated_at=generated_at,
    )


def _render_retro(payload: dict[str, Any], *, today: str, generated_at: str) -> str:
    advisory = payload["advisory_signals"]
    rows = [
        {
            "kind": "role",
            "proposal": "Create real scribe claim/log evidence before removing waiver debt.",
            "tier": "-",
            "priority": "P0",
            "owner_proposal": "No owner approval needed for local evidence recording.",
            "evidence": "role-usage:scribe",
        },
        {
            "kind": "role",
            "proposal": "Route monitored dormant roles into review/council cycle evidence.",
            "tier": "-",
            "priority": "P0",
            "owner_proposal": "Keep as watch until claims exist.",
            "evidence": "role-monitor:*",
        },
        {
            "kind": "asset",
            "proposal": "Exercise, modify, or deprecate low-reuse runtime assets.",
            "tier": "-",
            "priority": "P1",
            "owner_proposal": "Review after next assessment delta.",
            "evidence": "asset-low-reuse:*",
        },
        {
            "kind": "advisory",
            "proposal": "Record scribe/doc-steward advisory status in each cycle.",
            "tier": "-",
            "priority": "P1",
            "owner_proposal": "Automate when threshold is stable.",
            "evidence": f"scribe={advisory['scribe']['state']}; doc-steward={advisory['doc_steward']['state']}",
        },
    ]
    lines = [
        "---",
        "type: retro",
        "id: RETRO-" + today + "-self-improvement-cycle",
        "task_id: TASK-AR-571",
        f"period_end: {today}",
        f"recorded_at: {generated_at}",
        "trigger: self_improvement_cycle",
        "tags: [retro, self-improvement, task-ar-571]",
        "---",
        "",
        f"# RETRO {today} - Self Improvement Cycle",
        "",
        "## Section 1 Planned vs Actual",
        "",
        "- Planned: turn the baseline assessment into durable product-native records.",
        "- Actual: review, meeting, seminar, retro, compound, and casebook surfaces are planned from one assessment payload.",
        "- Boundary: no live participant quotes are fabricated.",
        "",
        "## Section 2 Root Cause",
        "",
        f"- Current maturity is `{payload['maturity_level']}` because role and asset evidence remains sparse.",
        f"- Score deductions: `{payload['score']['deductions']}`.",
        "",
        "## Section 3 Collaboration Health Check",
        "",
        *_table(_role_rows(payload), ["role", "root_cause", "severity", "evidence"]),
        "",
        "## Section 4 Feedforward",
        "",
        "- Re-run assessment after this cycle and compare score, role gaps, asset gaps, and advisory states.",
        "- Do not close the broader goal until maturity thresholds are explicitly reported.",
        "",
        "## Section 5 Forward Actions",
        "",
        *_table(rows, ["kind", "proposal", "tier", "priority", "owner_proposal", "evidence"]),
        "",
    ]
    return "\n".join(lines)


def _compound_id_for_cycle(root: Path, today: str) -> str:
    path = root / "agents" / "lead_engineer" / "compound_log.md"
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    existing = re.search(
        rf"(COMPOUND-{re.escape(today)}-\d+): Low-frequency role and runtime asset debt recurrence",
        text,
    )
    if existing:
        return existing.group(1)
    nums = [int(match.group(1)) for match in re.finditer(rf"COMPOUND-{re.escape(today)}-(\d+)", text)]
    return f"COMPOUND-{today}-{(max(nums) if nums else 0) + 1:03d}"


def _render_compound(payload: dict[str, Any], *, compound_id: str, review_path: str) -> str:
    return "\n".join(
        [
            "",
            f"## {compound_id}: Low-frequency role and runtime asset debt recurrence",
            "",
            "### Bottom Line",
            "- Self-improvement debt is recurring enough to require a searchable compound record.",
            f"- Baseline maturity: `{payload['maturity_level']}` at `{payload['score']['value']}/100`.",
            f"- Evidence review: `{review_path}`.",
            "",
            "### Cause",
            "- Role invocation text exists, but claim evidence is missing for monitored roles.",
            "- Runtime assets are registered, but several have low distinct evidence reuse.",
            "- Scribe status is not yet reliable enough to remove the existing waiver debt.",
            "",
            "### Preventive Action",
            "- Keep the cycle command as the repeatable path from assessment to review/meeting/seminar/retro evidence.",
            "- Route scribe, reviewer, skeptic, council, progress-scout, and release-steward gaps into the next cycle.",
            "- Reassess before claiming maturity improvement.",
            "",
            "### Status",
            "- Recorded by `scripts/self_improvement_cycle.py cycle`.",
            "",
        ]
    )


def _render_casebook_block(payload: dict[str, Any], *, compound_id: str, review_path: str) -> str:
    return "\n".join(
        [
            "",
            "### CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT",
            "",
            "| Field | Value |",
            "| --- | --- |",
            "| `case_id` | `CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT` |",
            "| `dedupe_key` | `self-improvement-low-frequency-debt` |",
            "| `symptom` | Low-frequency roles and runtime assets stay visible as watch debt. |",
            "| `trigger` | `scripts/self_improvement_cycle.py assess` reports immature/watch. |",
            "| `owner_boundary` | local |",
            "| `affected_gate` | `scripts/collaboration_governance_gate.py`, `scripts/runtime_asset_usage.py` |",
            f"| `recurrence_count` | role gaps `{len(payload['collaboration']['role_gaps'])}`; asset gaps `{len(payload['runtime_assets']['asset_gaps'])}` |",
            f"| `source_refs` | `{review_path}`, `{compound_id}` |",
            "| `reproduction` | Run `python scripts/self_improvement_cycle.py assess --json`. |",
            "| `linked_regression_fixture` | `tests/test_self_improvement_cycle.py` |",
            "| `task_proposal` | `TASK-AR-571`, then `TASK-AR-572` maturity reporting |",
            "| `prevention_status` | watch |",
            "",
        ]
    )


def _update_casebook_text(existing: str, block: str, *, review_path: str, compound_id: str) -> str:
    if "CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT" in existing:
        return existing
    seed = (
        "| Low-frequency self-improvement debt | `self-improvement-low-frequency-debt` | "
        f"`{review_path}`, `{compound_id}` | watch | route dormant roles and low-reuse assets into the next cycle |\n"
    )
    if "## Detailed Cases" in existing and "self-improvement-low-frequency-debt" not in existing:
        existing = existing.replace("\n## Detailed Cases", seed + "\n## Detailed Cases", 1)
    return existing.rstrip() + "\n" + block


def _write_text_artifact(
    root: Path,
    *,
    rel_path: str,
    content: str,
    kind: str,
    dry_run: bool,
    overwrite: bool,
) -> dict[str, Any]:
    path = root / rel_path
    if dry_run:
        status = "exists" if path.exists() else "planned"
        return {"kind": kind, "path": rel_path, "status": status, "bytes": len(content.encode("utf-8"))}
    if path.exists() and not overwrite:
        return {"kind": kind, "path": rel_path, "status": "exists", "bytes": path.stat().st_size}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return {"kind": kind, "path": rel_path, "status": "written", "bytes": path.stat().st_size}


def _append_compound(
    root: Path,
    *,
    content: str,
    compound_id: str,
    dry_run: bool,
) -> dict[str, Any]:
    rel_path = "agents/lead_engineer/compound_log.md"
    path = root / rel_path
    if dry_run:
        existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        status = "exists" if compound_id in existing else "planned"
        return {"kind": "compound", "path": rel_path, "status": status, "compound_id": compound_id}
    existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else "# Compound Log\n"
    if compound_id in existing:
        return {"kind": "compound", "path": rel_path, "status": "exists", "compound_id": compound_id}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(existing.rstrip() + "\n" + content.lstrip(), encoding="utf-8")
    return {"kind": "compound", "path": rel_path, "status": "written", "compound_id": compound_id}


def _write_casebook(
    root: Path,
    *,
    block: str,
    review_path: str,
    compound_id: str,
    dry_run: bool,
) -> dict[str, Any]:
    rel_path = "agents/project/casebooks/failure-and-compound-casebook.md"
    path = root / rel_path
    if dry_run:
        existing = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        status = "exists" if "CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT" in existing else "planned"
        return {"kind": "casebook", "path": rel_path, "status": status, "case_id": "CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT"}
    existing = (
        path.read_text(encoding="utf-8", errors="replace")
        if path.is_file()
        else "# Failure and Compound Casebook\n\n## Seed Cases\n\n| Case | Dedupe Key | Sources | Prevention Status | Next Route |\n| --- | --- | --- | --- | --- |\n\n## Detailed Cases\n"
    )
    updated = _update_casebook_text(existing, block, review_path=review_path, compound_id=compound_id)
    status = "exists" if updated == existing else "written"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")
    return {"kind": "casebook", "path": rel_path, "status": status, "case_id": "CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT"}


def cycle(root: Path, *, now: datetime, dry_run: bool = False, overwrite: bool = False) -> dict[str, Any]:
    root = root.resolve()
    payload = assess(root, now=now)
    today = _today(now)
    generated_at = now.isoformat(timespec="seconds")
    paths = _artifact_paths(today)
    compound_id = _compound_id_for_cycle(root, today)
    requires_compound = _debt_requires_compound(payload)

    artifacts: list[dict[str, Any]] = []
    artifacts.append(
        _write_text_artifact(
            root,
            rel_path=paths["review"],
            content=_render_review(payload, today=today, generated_at=generated_at, paths=paths),
            kind="review",
            dry_run=dry_run,
            overwrite=overwrite,
        )
    )
    artifacts.append(
        _write_text_artifact(
            root,
            rel_path=paths["meeting"],
            content=_render_meeting(today=today, generated_at=generated_at),
            kind="meeting",
            dry_run=dry_run,
            overwrite=overwrite,
        )
    )
    artifacts.append(
        _write_text_artifact(
            root,
            rel_path=paths["seminar"],
            content=_render_seminar(today=today, generated_at=generated_at),
            kind="seminar",
            dry_run=dry_run,
            overwrite=overwrite,
        )
    )
    artifacts.append(
        _write_text_artifact(
            root,
            rel_path=paths["retro"],
            content=_render_retro(payload, today=today, generated_at=generated_at),
            kind="retro",
            dry_run=dry_run,
            overwrite=overwrite,
        )
    )
    if requires_compound:
        artifacts.append(
            _append_compound(
                root,
                content=_render_compound(payload, compound_id=compound_id, review_path=paths["review"]),
                compound_id=compound_id,
                dry_run=dry_run,
            )
        )
        artifacts.append(
            _write_casebook(
                root,
                block=_render_casebook_block(payload, compound_id=compound_id, review_path=paths["review"]),
                review_path=paths["review"],
                compound_id=compound_id,
                dry_run=dry_run,
            )
        )

    return {
        "schema": CYCLE_SCHEMA,
        "generated_at": generated_at,
        "root": str(root),
        "status": "planned" if dry_run else "recorded",
        "dry_run": dry_run,
        "task_id": "TASK-AR-571",
        "unit_id": "UNIT-TASK-AR-571-001",
        "assessment": {
            "status": payload["status"],
            "maturity_level": payload["maturity_level"],
            "score": payload["score"],
            "role_gaps": len(payload["collaboration"]["role_gaps"]),
            "asset_gaps": len(payload["runtime_assets"]["asset_gaps"]),
            "scribe": payload["advisory_signals"]["scribe"],
            "doc_steward": payload["advisory_signals"]["doc_steward"],
        },
        "requires_compound": requires_compound,
        "compound_id": compound_id if requires_compound else None,
        "artifacts": artifacts,
        "next_cycle_thresholds": _thresholds(payload),
    }


def _maturity_gate_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    score = payload["score"]
    inputs = score["inputs"]
    cycle_status = payload["product_surfaces"]["current_cycle"]
    scribe_state = payload["advisory_signals"]["scribe"]["state"]
    return [
        {"gate": "score_improving", "current": score["value"], "target": ">=65", "pass": score["value"] >= 65},
        {"gate": "score_mature", "current": score["value"], "target": ">=90", "pass": score["value"] >= 90},
        {"gate": "unwaived_blocks", "current": inputs["unwaived_blocks"], "target": "0", "pass": inputs["unwaived_blocks"] == 0},
        {"gate": "waiver_debt", "current": inputs["waiver_debt"], "target": "0", "pass": inputs["waiver_debt"] == 0},
        {"gate": "monitored_role_gaps", "current": inputs["monitored_role_gaps"], "target": "<=1", "pass": inputs["monitored_role_gaps"] <= 1},
        {"gate": "low_reuse_assets", "current": inputs["low_reuse_assets"], "target": "<=2", "pass": inputs["low_reuse_assets"] <= 2},
        {"gate": "scribe_state", "current": scribe_state, "target": "ok", "pass": scribe_state == "ok"},
        {"gate": "cycle_artifacts", "current": f"{cycle_status['present']}/{cycle_status['required']}", "target": "all required", "pass": cycle_status["recorded"]},
    ]


def _goal_state(payload: dict[str, Any]) -> dict[str, Any]:
    gates = _maturity_gate_results(payload)
    blocking = [gate["gate"] for gate in gates if not gate["pass"] and gate["gate"] != "score_mature"]
    mature = payload["maturity_level"] == "mature" and not blocking
    cycle_recorded = payload["product_surfaces"]["current_cycle"]["recorded"]
    return {
        "complete": bool(mature),
        "evidence_maturity": payload["maturity_level"],
        "cycle_recorded": cycle_recorded,
        "operating_state": "mature" if mature else ("cycle_recorded_but_evidence_immature" if cycle_recorded else "needs_cycle_record"),
        "blocking_gates": blocking,
    }


def _render_report(payload: dict[str, Any], *, today: str, generated_at: str) -> str:
    score = payload["score"]
    cycle_status = payload["product_surfaces"]["current_cycle"]
    goal_state = _goal_state(payload)
    baseline_rows = [
        {"metric": "score", "baseline": 32, "current": score["value"], "delta": score["value"] - 32},
        {"metric": "role_gaps", "baseline": 6, "current": len(payload["collaboration"]["role_gaps"]), "delta": len(payload["collaboration"]["role_gaps"]) - 6},
        {"metric": "asset_gaps", "baseline": 17, "current": len(payload["runtime_assets"]["asset_gaps"]), "delta": len(payload["runtime_assets"]["asset_gaps"]) - 17},
        {"metric": "cycle_artifacts", "baseline": 0, "current": cycle_status["present"], "delta": cycle_status["present"]},
    ]
    lines = [
        "---",
        f"title: Self Improvement Maturity Report {today}",
        f"date: {today}",
        f"signal: {payload['status']}",
        f"score: {score['value']}",
        "tags: [self-improvement, maturity-report, task-ar-572]",
        "---",
        "",
        f"# Self Improvement Maturity Report {today}",
        "",
        "## Bottom Line",
        "",
        f"- Evidence maturity: `{payload['maturity_level']}` at `{score['value']}/100`.",
        f"- Cycle artifacts: `{cycle_status['present']}/{cycle_status['required']}` required records present.",
        f"- Persistent thread goal complete: `{str(goal_state['complete']).lower()}`.",
        "- The operating cycle is now recorded, but role/asset evidence has not yet improved enough to claim maturity.",
        "",
        "## Signal",
        "",
        "| Metric | Baseline | Current | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in baseline_rows:
        lines.append(f"| {row['metric']} | {row['baseline']} | {row['current']} | {row['delta']} |")
    lines.extend(
        [
            "",
            "## Maturity Gates",
            "",
            "| Gate | Current | Target | Pass |",
            "| --- | --- | --- | --- |",
        ]
    )
    for gate in _maturity_gate_results(payload):
        lines.append(f"| {gate['gate']} | `{gate['current']}` | `{gate['target']}` | `{str(gate['pass']).lower()}` |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Keep the active thread goal open.",
            "- Use the recorded cycle as the repeatable cadence baseline.",
            "- Do not remove the scribe waiver or claim monitored roles are exercised until real claim/log evidence exists.",
            "",
            "## Next",
            "",
        ]
    )
    for action in payload["next"]:
        lines.append(f"- {action}")
    lines.extend(["", f"_Generated at `{generated_at}`._", ""])
    return "\n".join(lines)


def report(root: Path, *, now: datetime, dry_run: bool = False, overwrite: bool = False) -> dict[str, Any]:
    root = root.resolve()
    payload = assess(root, now=now)
    today = _today(now)
    generated_at = now.isoformat(timespec="seconds")
    rel_path = f"reviews/REPORT-{today}-self-improvement-maturity.md"
    content = _render_report(payload, today=today, generated_at=generated_at)
    artifact = _write_text_artifact(
        root,
        rel_path=rel_path,
        content=content,
        kind="maturity_report",
        dry_run=dry_run,
        overwrite=overwrite,
    )
    return {
        "schema": REPORT_SCHEMA,
        "generated_at": generated_at,
        "root": str(root),
        "status": "planned" if dry_run else "recorded",
        "dry_run": dry_run,
        "task_id": "TASK-AR-572",
        "unit_id": "UNIT-TASK-AR-572-001",
        "assessment": {
            "status": payload["status"],
            "maturity_level": payload["maturity_level"],
            "score": payload["score"],
            "role_gaps": len(payload["collaboration"]["role_gaps"]),
            "asset_gaps": len(payload["runtime_assets"]["asset_gaps"]),
        },
        "goal_state": _goal_state(payload),
        "maturity_gates": _maturity_gate_results(payload),
        "next_cycle_thresholds": _thresholds(payload),
        "artifact": artifact,
    }


def _next_actions(
    maturity_level: str,
    role_gaps: list[dict[str, Any]],
    asset_gaps: list[dict[str, Any]],
    advisory: dict[str, dict[str, Any]],
    *,
    cycle_recorded: bool = False,
) -> list[str]:
    actions: list[str] = []
    if maturity_level not in {"mature", "improving"} and not cycle_recorded:
        actions.append("Run the cycle unit to record review/meeting/seminar/retro evidence from this baseline.")
    elif maturity_level not in {"mature", "improving"}:
        actions.append("Run the next remediation cycle after adding real role/asset evidence.")
    if any(gap["root_cause"] == "waiver_debt" for gap in role_gaps):
        actions.append("Create real scribe claim/log evidence before removing the scribe waiver.")
    if any(gap["subject"].startswith("role-monitor:") for gap in role_gaps):
        actions.append("Route monitored dormant roles into the next review or council cycle.")
    if asset_gaps:
        actions.append("Review low-reuse runtime assets and either exercise, modify, or deprecate them.")
    if any(signal.get("state") in {"due", "overdue", "unknown"} for signal in advisory.values()):
        actions.append("Run advisory scribe/doc-steward checks in the next cycle report.")
    return actions or ["Maintain cadence and re-run assessment after the next cycle."]


def render_text(payload: dict[str, Any]) -> str:
    role_gaps = payload["collaboration"]["role_gaps"]
    asset_gaps = payload["runtime_assets"]["asset_gaps"]
    lines = [
        "Self Improvement Assessment",
        f"- Status: {payload['status']}",
        f"- Maturity: {payload['maturity_level']} ({payload['score']['value']}/100)",
        f"- Role gaps: {len(role_gaps)}",
        f"- Asset gaps: {len(asset_gaps)}",
        f"- Scribe: {payload['advisory_signals']['scribe']['state']}",
        f"- Doc Steward: {payload['advisory_signals']['doc_steward']['state']}",
        "",
        "Top role gaps:",
    ]
    for gap in role_gaps[:8]:
        lines.append(f"- {gap['role']}: {gap['root_cause']} ({gap['severity']})")
    if not role_gaps:
        lines.append("- none")
    lines.extend(["", "Top asset gaps:"])
    for gap in asset_gaps[:8]:
        lines.append(f"- {gap['asset_id']}: {gap['root_cause']} ({gap['severity']})")
    if not asset_gaps:
        lines.append("- none")
    lines.extend(["", "Next:"])
    for action in payload["next"]:
        lines.append(f"- {action}")
    return "\n".join(lines)


def render_cycle_text(payload: dict[str, Any]) -> str:
    lines = [
        "Self Improvement Cycle",
        f"- Status: {payload['status']}",
        f"- Maturity: {payload['assessment']['maturity_level']} ({payload['assessment']['score']['value']}/100)",
        f"- Role gaps: {payload['assessment']['role_gaps']}",
        f"- Asset gaps: {payload['assessment']['asset_gaps']}",
        f"- Compound required: {payload['requires_compound']}",
        "",
        "Artifacts:",
    ]
    for artifact in payload["artifacts"]:
        lines.append(f"- {artifact['kind']}: {artifact['status']} -> {artifact['path']}")
    lines.extend(["", "Next-cycle thresholds:"])
    for row in payload["next_cycle_thresholds"]:
        lines.append(f"- {row['metric']}: current={row['current']} next={row['target_next']} mature={row['target_mature']}")
    return "\n".join(lines)


def render_report_text(payload: dict[str, Any]) -> str:
    lines = [
        "Self Improvement Maturity Report",
        f"- Status: {payload['status']}",
        f"- Evidence maturity: {payload['assessment']['maturity_level']} ({payload['assessment']['score']['value']}/100)",
        f"- Goal complete: {payload['goal_state']['complete']}",
        f"- Operating state: {payload['goal_state']['operating_state']}",
        f"- Report: {payload['artifact']['status']} -> {payload['artifact']['path']}",
        "",
        "Blocking gates:",
    ]
    blockers = payload["goal_state"]["blocking_gates"]
    lines.extend(f"- {gate}" for gate in blockers)
    if not blockers:
        lines.append("- none")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Self-improvement cycle baseline")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--now", help="ISO timestamp for deterministic output")
    sub = parser.add_subparsers(dest="command", required=True)
    assess_parser = sub.add_parser("assess", help="assess current self-improvement signals")
    assess_parser.add_argument("--json", action="store_true", help="emit JSON")
    cycle_parser = sub.add_parser("cycle", help="record product-native self-improvement cycle artifacts")
    cycle_parser.add_argument("--dry-run", action="store_true", help="show planned artifacts without writing")
    cycle_parser.add_argument("--overwrite", action="store_true", help="replace dated review/meeting/seminar/retro records")
    cycle_parser.add_argument("--json", action="store_true", help="emit JSON")
    report_parser = sub.add_parser("report", help="write maturity report and active-goal state")
    report_parser.add_argument("--dry-run", action="store_true", help="show planned report without writing")
    report_parser.add_argument("--overwrite", action="store_true", help="replace dated maturity report")
    report_parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = _parse_now(args.now)
    if args.command == "assess":
        payload = assess(args.root, now=now)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render_text(payload))
        return 0
    if args.command == "cycle":
        payload = cycle(args.root, now=now, dry_run=args.dry_run, overwrite=args.overwrite)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render_cycle_text(payload))
        return 0
    if args.command == "report":
        payload = report(args.root, now=now, dry_run=args.dry_run, overwrite=args.overwrite)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render_report_text(payload))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
