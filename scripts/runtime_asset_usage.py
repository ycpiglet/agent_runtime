"""Measure runtime asset usage, reuse, and lifecycle decisions.

The registry turns skills, hooks, triggers, gates, and scripts into explicit
assets. This gate verifies that active assets exist, have evidence surfaces, and
carry lifecycle decisions. Missing required assets or invalid deprecation
metadata block; low or absent usage is reported as watch so it can be reviewed
without hiding drift.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REGISTRY_PATH = Path("agents/project/RUNTIME-ASSET-REGISTRY.json")
VALID_SCHEMA = "agent-runtime-asset-registry/v1"
VALID_STATUSES = {"active", "watch", "deprecated", "removed"}
VALID_LIFECYCLES = {"keep", "modify", "deprecate", "remove", "observe"}


@dataclass(frozen=True)
class Finding:
    severity: str
    subject: str
    path: str
    detail: str


@dataclass(frozen=True)
class AssetMetric:
    asset_id: str
    kind: str
    status: str
    lifecycle: str
    path_count: int
    evidence_count: int
    usage_count: int
    distinct_evidence_hits: int


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _token_hits(text: str, tokens: list[str]) -> int:
    lowered = text.lower()
    return sum(lowered.count(token.lower()) for token in tokens if token.strip())


def _asset_tokens(asset: dict[str, Any]) -> list[str]:
    tokens = _as_list(asset.get("tokens"))
    tokens.extend(_as_list(asset.get("paths")))
    asset_id = str(asset.get("id") or "").strip()
    if asset_id:
        tokens.append(asset_id)
    return sorted(set(tokens))


def _validate_registry(root: Path, findings: list[Finding]) -> dict[str, Any]:
    path = root / REGISTRY_PATH
    registry = _read_json(path)
    if registry is None:
        findings.append(Finding("block", "registry:missing-or-invalid", REGISTRY_PATH.as_posix(), "runtime asset registry must be valid JSON"))
        return {}
    if registry.get("schema") != VALID_SCHEMA:
        findings.append(Finding("block", "registry:schema", REGISTRY_PATH.as_posix(), f"schema must be {VALID_SCHEMA}"))
    assets = registry.get("assets")
    if not isinstance(assets, list):
        findings.append(Finding("block", "registry:assets", REGISTRY_PATH.as_posix(), "assets must be a list"))
    return registry


def _analyze_asset(root: Path, asset: dict[str, Any], findings: list[Finding]) -> AssetMetric:
    asset_id = str(asset.get("id") or "").strip() or "asset:missing-id"
    kind = str(asset.get("kind") or "unknown").strip()
    status = str(asset.get("status") or "watch").strip()
    lifecycle = str(asset.get("lifecycle") or "observe").strip()
    paths = _as_list(asset.get("paths"))
    evidence_paths = _as_list(asset.get("evidence_paths"))
    tokens = _asset_tokens(asset)
    min_uses = int(asset.get("min_recent_uses") or 0)

    if status not in VALID_STATUSES:
        findings.append(Finding("block", f"asset-status:{asset_id}", REGISTRY_PATH.as_posix(), f"invalid status {status!r}"))
    if lifecycle not in VALID_LIFECYCLES:
        findings.append(Finding("block", f"asset-lifecycle:{asset_id}", REGISTRY_PATH.as_posix(), f"invalid lifecycle {lifecycle!r}"))
    if not paths:
        findings.append(Finding("block", f"asset-paths:{asset_id}", REGISTRY_PATH.as_posix(), "asset must list at least one path"))

    existing_paths = 0
    for raw_path in paths:
        path = root / raw_path
        if path.exists():
            existing_paths += 1
        elif status in {"active", "watch"}:
            findings.append(Finding("block", f"asset-missing:{asset_id}", raw_path, "registered active asset path is missing"))

    evidence_count = 0
    usage_count = 0
    distinct_hits = 0
    for raw_path in evidence_paths:
        path = root / raw_path
        text = _read_text(path)
        if not text:
            findings.append(Finding("watch", f"asset-evidence-missing:{asset_id}", raw_path, "evidence path is missing or empty"))
            continue
        evidence_count += 1
        hits = _token_hits(text, tokens)
        usage_count += hits
        if hits:
            distinct_hits += 1

    if min_uses and usage_count < min_uses and status == "active":
        findings.append(
            Finding(
                "watch",
                f"asset-usage-low:{asset_id}",
                REGISTRY_PATH.as_posix(),
                f"usage_count={usage_count}, expected at least {min_uses}",
            )
        )

    if lifecycle in {"deprecate", "remove"}:
        replacement = str(asset.get("replacement") or "").strip()
        rationale = str(asset.get("rationale") or "").strip()
        if not replacement and not rationale:
            findings.append(
                Finding(
                    "block",
                    f"asset-decision-incomplete:{asset_id}",
                    REGISTRY_PATH.as_posix(),
                    "deprecate/remove assets require replacement or rationale",
                )
            )

    return AssetMetric(asset_id, kind, status, lifecycle, existing_paths, evidence_count, usage_count, distinct_hits)


def analyze(root: Path) -> tuple[list[Finding], list[AssetMetric]]:
    root = root.resolve()
    findings: list[Finding] = []
    metrics: list[AssetMetric] = []
    registry = _validate_registry(root, findings)
    assets = registry.get("assets") if registry else []
    if isinstance(assets, list):
        for asset in assets:
            if isinstance(asset, dict):
                metrics.append(_analyze_asset(root, asset, findings))
            else:
                findings.append(Finding("block", "asset:not-object", REGISTRY_PATH.as_posix(), "asset entries must be JSON objects"))
    return findings, metrics


def render(root: Path, findings: list[Finding], metrics: list[AssetMetric]) -> str:
    counts = Counter(f.severity for f in findings)
    by_kind = Counter(metric.kind for metric in metrics)
    by_lifecycle = Counter(metric.lifecycle for metric in metrics)
    usage_total = sum(metric.usage_count for metric in metrics)
    status = "fail" if counts.get("block", 0) else "pass"
    lines = [
        f"runtime-asset-usage: {status}",
        f"root={root.resolve()}",
        f"assets={len(metrics)}",
        f"usage_total={usage_total}",
        f"block={counts.get('block', 0)}",
        f"watch={counts.get('watch', 0)}",
        "by_kind=" + json.dumps(dict(sorted(by_kind.items())), sort_keys=True),
        "by_lifecycle=" + json.dumps(dict(sorted(by_lifecycle.items())), sort_keys=True),
    ]
    for metric in metrics:
        lines.append(
            "- metric "
            f"{metric.asset_id} kind={metric.kind} status={metric.status} lifecycle={metric.lifecycle} "
            f"paths={metric.path_count} evidence={metric.evidence_count} usage={metric.usage_count} "
            f"reuse={metric.distinct_evidence_hits}"
        )
    for finding in findings:
        lines.append(f"- {finding.severity} {finding.subject} {finding.path}: {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Runtime asset usage and lifecycle gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Fail on block findings")
    parser.add_argument("--json", action="store_true", help="Emit JSON payload")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings, metrics = analyze(args.root)
    if args.json:
        print(
            json.dumps(
                {
                    "status": "fail" if any(f.severity == "block" for f in findings) else "pass",
                    "findings": [finding.__dict__ for finding in findings],
                    "metrics": [metric.__dict__ for metric in metrics],
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(render(args.root, findings, metrics))
    if args.check and any(finding.severity == "block" for finding in findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
