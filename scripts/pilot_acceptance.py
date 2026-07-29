#!/usr/bin/env python3
"""Validate sanitized, replayable consumer-pilot evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA = "agent-runtime-pilot-evidence/v1"
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
CLAIM_RE = re.compile(r"^CLAIM-[A-Za-z0-9._-]+$")
EXPECTED_EXTERNAL_EFFECTS = (
    "publish",
    "deploy",
    "origin_push",
    "host_commit",
    "credential_read",
    "network_delivery",
    "content_mutation",
)
ROUTING_FIELDS = (
    "requested_model_tier",
    "selected_model_tier",
    "resolved_provider_tier",
    "execution_surface",
    "actual_model_status",
    "savings_claim",
)


def _finding(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_relative(value: object) -> bool:
    text = str(value or "").strip().replace("\\", "/")
    return bool(
        text
        and not text.startswith("/")
        and not re.match(r"^[A-Za-z]:", text)
        and all(part not in {"", ".", ".."} for part in text.split("/"))
    )


def _valid_sha(value: object) -> bool:
    return bool(SHA256_RE.fullmatch(str(value or "").strip()))


def _count(record: dict[str, Any], key: str) -> int | None:
    value = record.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def validate_evidence(payload: object) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return [_finding("invalid-root", "$", "evidence must be a JSON object")]
    if payload.get("schema") != SCHEMA:
        findings.append(_finding("invalid-schema", "schema", f"expected {SCHEMA}"))

    baselines = _mapping(payload.get("baselines"))
    for key in ("host_commit", "runtime_commit"):
        value = str(baselines.get(key) or "")
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            findings.append(_finding("invalid-baseline", f"baselines.{key}", "expected a full git SHA"))

    adoption = _mapping(payload.get("adoption"))
    selected = _count(adoption, "selected_template_files")
    initial = _mapping(adoption.get("initial_reconcile"))
    immediate = _mapping(adoption.get("immediate_post_apply_reconcile"))
    if selected is None or selected <= 0:
        findings.append(_finding("invalid-selection-count", "adoption.selected_template_files", "must be positive"))
    elif sum(
        value or 0
        for value in (
            _count(initial, "safe_updates"),
            _count(initial, "preserved"),
            _count(initial, "excluded"),
            _count(initial, "conflicts"),
        )
    ) != selected:
        findings.append(_finding("reconcile-count-mismatch", "adoption.initial_reconcile", "counts must equal selected files"))
    if _count(initial, "conflicts") != 0:
        findings.append(_finding("initial-conflict", "adoption.initial_reconcile.conflicts", "initial adoption must have zero conflicts"))
    if _count(immediate, "safe_updates") != 0 or _count(immediate, "conflicts") != 0:
        findings.append(_finding("unstable-apply", "adoption.immediate_post_apply_reconcile", "safe apply must settle with zero updates and conflicts"))
    if adoption.get("web_content_incremental_files") != 0:
        findings.append(_finding("fixture-drift", "adoption.web_content_incremental_files", "Bean Wiki baseline measured zero profile-specific files"))

    preservation = _mapping(payload.get("preservation"))
    assets = _list(preservation.get("host_assets"))
    if preservation.get("host_asset_count") != len(assets) or not assets:
        findings.append(_finding("host-asset-count-mismatch", "preservation.host_assets", "declared count must match a non-empty list"))
    seen_paths: set[str] = set()
    for index, item in enumerate(assets):
        record = _mapping(item)
        prefix = f"preservation.host_assets[{index}]"
        path = str(record.get("path") or "")
        if not _safe_relative(path) or path in seen_paths:
            findings.append(_finding("invalid-host-asset-path", f"{prefix}.path", "path must be unique and safe relative"))
        seen_paths.add(path)
        before, after = record.get("before"), record.get("after")
        if not _valid_sha(before) or not _valid_sha(after):
            findings.append(_finding("invalid-host-asset-digest", prefix, "before and after must be SHA-256 values"))
        elif before != after:
            findings.append(_finding("host-asset-overwrite", prefix, f"preserved asset changed: {path}"))
    if preservation.get("unexpected_overwrite_count") != 0:
        findings.append(_finding("unexpected-overwrite", "preservation.unexpected_overwrite_count", "must be zero"))
    content = _mapping(preservation.get("content"))
    if not _valid_sha(content.get("before")) or not _valid_sha(content.get("after")):
        findings.append(_finding("invalid-content-digest", "preservation.content", "content manifests must be SHA-256 values"))
    elif content.get("before") != content.get("after"):
        findings.append(_finding("content-mutation", "preservation.content", "src/content manifest changed"))

    bootstrap = _mapping(payload.get("bootstrap"))
    if not CLAIM_RE.fullmatch(str(bootstrap.get("upstream_claim_id") or "")):
        findings.append(_finding("missing-bootstrap-claim", "bootstrap.upstream_claim_id", "bootstrap must map to a persisted upstream claim"))
    if bootstrap.get("unmapped_diff_count") != 0:
        findings.append(_finding("unmapped-diff", "bootstrap.unmapped_diff_count", "every pilot diff must have provenance"))

    expected_task_count = payload.get("expected_task_count")
    tasks = _list(payload.get("tasks"))
    if expected_task_count != len(tasks) or expected_task_count != 3:
        findings.append(_finding("task-count-mismatch", "tasks", "Bean Wiki pilot requires exactly three task traces"))
    seen_tasks: set[str] = set()
    for index, item in enumerate(tasks):
        task = _mapping(item)
        prefix = f"tasks[{index}]"
        task_id = str(task.get("task_id") or "")
        if not task_id or task_id in seen_tasks:
            findings.append(_finding("invalid-task-trace", f"{prefix}.task_id", "task id must be present and unique"))
        seen_tasks.add(task_id)
        claim = _mapping(task.get("claim_trace"))
        if not CLAIM_RE.fullmatch(str(claim.get("claim_id") or "")):
            findings.append(_finding("missing-claim-trace", f"{prefix}.claim_trace", "task must carry a canonical claim id"))
        if claim.get("task_id") != task_id or claim.get("unit_id") != task.get("unit_id"):
            findings.append(_finding("claim-identity-mismatch", f"{prefix}.claim_trace", "claim/task/unit identities must agree"))
        if claim.get("status") not in {"blocked", "released"}:
            findings.append(_finding("invalid-claim-status", f"{prefix}.claim_trace.status", "terminal pilot claim must be blocked or released"))
        outputs = _list(task.get("output_refs"))
        if not outputs or any(not _safe_relative(path) for path in outputs):
            findings.append(_finding("missing-task-output", f"{prefix}.output_refs", "task must have safe bounded output refs"))

        routing = _mapping(task.get("routing"))
        missing_routing = [field for field in ROUTING_FIELDS if field not in routing]
        if missing_routing:
            findings.append(_finding("missing-routing-field", f"{prefix}.routing", ", ".join(missing_routing)))
        observed = routing.get("observed_model")
        verified_usage = routing.get("provider_usage_verified") is True
        if observed not in {None, ""} and (
            routing.get("actual_model_status") != "verified"
            or not str(routing.get("observation_source") or "").strip()
        ):
            findings.append(_finding("false-model-observation", f"{prefix}.routing.observed_model", "observed model requires verified status and an observation source"))
        usage_values = tuple(routing.get(key) for key in ("input_tokens", "output_tokens", "cost"))
        if any(value is not None for value in usage_values) and not verified_usage:
            findings.append(_finding("unverified-provider-usage", f"{prefix}.routing", "tokens or cost require verified provider usage"))
        if routing.get("savings_claim") != "unavailable" and not verified_usage:
            findings.append(_finding("unsupported-savings-claim", f"{prefix}.routing.savings_claim", "savings require verified provider usage"))

    compound = _mapping(payload.get("compound"))
    if compound.get("negative_fixture_matched") is not True:
        findings.append(_finding("compound-negative-missing", "compound.negative_fixture_matched", "intentional negative must reproduce"))
    if not isinstance(compound.get("retrieval_match_count"), int) or compound.get("retrieval_match_count", 0) < 1:
        findings.append(_finding("compound-retrieval-missing", "compound.retrieval_match_count", "later lookup must retrieve the record"))

    restart = _mapping(payload.get("restart"))
    if restart.get("same_task") is not True or restart.get("same_claim") is not True:
        findings.append(_finding("restart-identity-mismatch", "restart", "second process must resume the same task and claim"))
    writer_pid, reader_pid = restart.get("writer_pid"), restart.get("reader_pid")
    if not isinstance(writer_pid, int) or not isinstance(reader_pid, int) or writer_pid == reader_pid:
        findings.append(_finding("restart-process-not-distinct", "restart", "writer and reader processes must be distinct"))

    scribe = _mapping(payload.get("scribe"))
    if scribe.get("projection_status") != "fresh" or scribe.get("readiness") != "ready":
        findings.append(_finding("scribe-projection-not-fresh", "scribe", "projection must be fresh and ready"))
    if scribe.get("backlog_before") != scribe.get("backlog_after") or not _valid_sha(scribe.get("backlog_before")):
        findings.append(_finding("scribe-source-mutation", "scribe", "BACKLOG.md digest must remain unchanged"))

    effects = _mapping(payload.get("external_effects"))
    for key in EXPECTED_EXTERNAL_EFFECTS:
        if effects.get(key) != 0:
            findings.append(_finding("external-effect-nonzero", f"external_effects.{key}", "offline pilot requires zero"))

    priorities = {str(_mapping(item).get("priority") or "") for item in _list(payload.get("findings"))}
    if "P0" in priorities and payload.get("result") != "blocked":
        findings.append(_finding("p0-not-blocking", "result", "a P0 finding must block the pilot"))
    return findings


def load_evidence(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("evidence root must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate sanitized consumer-pilot evidence")
    parser.add_argument("--host", default="bean-wiki", help="Fixture host slug")
    parser.add_argument("--fixture", type=Path, default=None, help="Explicit evidence JSON")
    parser.add_argument("--check", action="store_true", help="Fail when findings exist")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent.parent
    path = args.fixture or root / "tests" / "fixtures" / "pilots" / args.host / "evidence.json"
    try:
        payload = load_evidence(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings = [_finding("fixture-unavailable", path.as_posix(), str(exc))]
    else:
        findings = validate_evidence(payload)
    result = {
        "schema": "agent-runtime-pilot-acceptance-result/v1",
        "host": args.host,
        "fixture": path.as_posix(),
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
        "findings": findings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pilot-acceptance: {result['status']}")
        print(f"host={args.host}")
        print(f"fixture={path}")
        print(f"findings={len(findings)}")
        for finding in findings:
            print(f"- {finding['code']} {finding['path']}: {finding['detail']}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
