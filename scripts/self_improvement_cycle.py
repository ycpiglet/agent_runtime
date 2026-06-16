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
import runtime_asset_usage  # noqa: E402


SCHEMA = "agent-runtime-self-improvement-assessment/v1"
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
        },
        "next": _next_actions(score["maturity_level"], roles, assets, advisory),
    }


def _next_actions(
    maturity_level: str,
    role_gaps: list[dict[str, Any]],
    asset_gaps: list[dict[str, Any]],
    advisory: dict[str, dict[str, Any]],
) -> list[str]:
    actions: list[str] = []
    if maturity_level not in {"mature", "improving"}:
        actions.append("Run the cycle unit to record review/meeting/seminar/retro evidence from this baseline.")
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Self-improvement cycle baseline")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--now", help="ISO timestamp for deterministic output")
    sub = parser.add_subparsers(dest="command", required=True)
    assess_parser = sub.add_parser("assess", help="assess current self-improvement signals")
    assess_parser.add_argument("--json", action="store_true", help="emit JSON")
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
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
