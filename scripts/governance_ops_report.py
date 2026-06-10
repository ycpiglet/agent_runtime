"""Generate an Owner-facing governance operations report."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GateSummary:
    name: str
    block: int
    watch: int
    waived: int = 0
    detail: str = ""


def _load_script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _count_findings(findings: list[Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for finding in findings:
        severity = getattr(finding, "effective_severity", None) or getattr(finding, "severity", "watch")
        counts[str(severity)] += 1
    return counts


def collect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    collab = _load_script("collaboration_governance_gate")
    usage = _load_script("runtime_asset_usage")
    sync = _load_script("state_sync_gate")

    collab_findings = collab.analyze(root, datetime.now(timezone.utc).astimezone())
    usage_findings, usage_metrics = usage.analyze(root)
    sync_findings = sync.analyze(root)

    collab_counts = _count_findings(collab_findings)
    usage_counts = _count_findings(usage_findings)
    sync_counts = _count_findings(sync_findings)

    metrics_by_kind = Counter(metric.kind for metric in usage_metrics)
    metrics_by_lifecycle = Counter(metric.lifecycle for metric in usage_metrics)
    low_reuse = [metric for metric in usage_metrics if metric.distinct_evidence_hits <= 1]

    return {
        "collaboration": GateSummary("collaboration-governance", collab_counts["block"], collab_counts["watch"], collab_counts["waived"]),
        "runtime_assets": GateSummary("runtime-asset-usage", usage_counts["block"], usage_counts["watch"], 0, f"assets={len(usage_metrics)} usage_total={sum(metric.usage_count for metric in usage_metrics)}"),
        "state_sync": GateSummary("state-sync", sync_counts["block"], sync_counts["watch"]),
        "asset_kind_counts": dict(sorted(metrics_by_kind.items())),
        "asset_lifecycle_counts": dict(sorted(metrics_by_lifecycle.items())),
        "low_reuse_assets": [metric.asset_id for metric in low_reuse],
        "asset_metrics": usage_metrics,
    }


def status_for(summary: dict[str, Any]) -> str:
    gates = [summary["collaboration"], summary["runtime_assets"], summary["state_sync"]]
    return "block" if any(gate.block for gate in gates) else ("watch" if any(gate.watch or gate.waived for gate in gates) else "pass")


def render(summary: dict[str, Any], *, generated_at: str) -> str:
    status = status_for(summary)
    gates = [summary["collaboration"], summary["runtime_assets"], summary["state_sync"]]
    lines = [
        "---",
        "type: governance_ops_report",
        "id: GOVERNANCE-OPS-REPORT-2026-06-10",
        "audience: owner",
        f"status: {status}",
        f"signal: {status}",
        "score: 90",
        "priority: P0",
        "tags: [governance, usage-metrics, lifecycle, waiver, state-sync]",
        f"generated_at: {generated_at}",
        "---",
        "",
        "# Governance Operations Report",
        "",
        "## Bottom Line",
        f"- Summary: governance operations signal is `{status}`.",
        "- Scope: collaboration governance, runtime asset usage/reuse, and active state sync.",
        "- Boundary: broad full-suite runtime remains separate under `TASK-AR-262`; this report uses focused gates.",
        "",
        "## Signal",
        "",
        "| Gate | Block | Watch | Waived | Detail |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for gate in gates:
        lines.append(f"| {gate.name} | {gate.block} | {gate.watch} | {gate.waived} | {gate.detail} |")

    lines.extend(
        [
            "",
            "## Insight",
            f"- Asset kinds: `{json.dumps(summary['asset_kind_counts'], sort_keys=True)}`.",
            f"- Lifecycle decisions: `{json.dumps(summary['asset_lifecycle_counts'], sort_keys=True)}`.",
            f"- Low-reuse candidates: `{', '.join(summary['low_reuse_assets']) or 'none'}`.",
            "- Remaining collaboration waiver is meaningful only if it points to real missing role evidence, not missing scripts.",
            "",
            "## Decision",
            "- Decision: keep runtime asset usage measurement in Owner governance.",
            "- Decision: keep `role-usage:scribe` visible until real scribe claim/log evidence exists.",
            "- Decision: default pytest collection is root tests only; template tests require explicit suite execution.",
            "",
            "## Action Board",
            "",
            "| Action | Owner | State | Evidence |",
            "| --- | --- | --- | --- |",
            "| Remove remaining scribe waiver after real claim/log evidence | lead-engineer | watch | `agents/project/waivers/WAIVER-2026-06-10-collaboration-runtime-promotion.json` |",
            "| Review monitored low-frequency roles | lead-engineer | watch | `scripts/collaboration_governance_gate.py --check` |",
            "| Keep runtime asset registry current when adding skills/hooks/triggers | agent-runtime-core | pass | `agents/project/RUNTIME-ASSET-REGISTRY.json` |",
            "| Keep state sync gate in Owner governance | lead-engineer | pass | `scripts/state_sync_gate.py --check` |",
            "",
            "## Asset Lifecycle Table",
            "",
            "| Asset | Kind | Lifecycle | Usage | Reuse | Decision |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for metric in summary["asset_metrics"]:
        decision = "review" if metric.asset_id in summary["low_reuse_assets"] else "keep"
        lines.append(
            f"| `{metric.asset_id}` | {metric.kind} | {metric.lifecycle} | {metric.usage_count} | {metric.distinct_evidence_hits} | {decision} |"
        )
    lines.extend(
        [
            "",
            "## Next",
            "- Add real scribe claim/log evidence in the next reporting cycle.",
            "- Promote recurring low-frequency role watches into tasks if they persist.",
            "- Run `python scripts/owner_governance_gate.py` before claiming governance closure.",
            "",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate governance operations report")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--out", type=Path, default=Path("reviews/GOVERNANCE-OPS-REPORT-2026-06-10.md"))
    parser.add_argument("--check", action="store_true", help="Fail when aggregate status is block")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = collect(args.root)
    generated_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    report = render(summary, generated_at=generated_at)
    output = args.root / args.out if not args.out.is_absolute() else args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"wrote={output}")
    print(f"status={status_for(summary)}")
    if args.check and status_for(summary) == "block":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
