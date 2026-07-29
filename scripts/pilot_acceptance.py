#!/usr/bin/env python3
"""Validate sanitized, replayable consumer-pilot evidence."""

from __future__ import annotations

import argparse
import hashlib
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
HOST_CONTRACTS: dict[str, dict[str, Any]] = {
    "bean-wiki": {
        "semantic_sha256": "e8a6119f3c6cef815c352600188f57c48e669e9d650b3e4e1b67f751a1d8582e",
        "pilot_id": "bean-wiki-v080-red-pilot",
        "result": "blocked",
        "baselines": {
            "host_commit": "357eee4fd8c29c33a949adbe3a0ffa80c874bf42",
            "runtime_commit": "4ab35b89023f23c032fc574a12a8679f1ea57d33",
        },
        "selected_template_files": 243,
        "content_file_count": 125,
        "post_registration_conflicts": ["owner-docs.yml"],
        "tasks": {
            "TASK-AR-001": {
                "unit_id": "UNIT-TASK-AR-001-001",
                "claim_id": "CLAIM-20260729-154746-task-ar-001-bean001",
                "task_status": "blocked",
                "claim_status": "blocked",
            },
            "TASK-AR-002": {
                "unit_id": "UNIT-TASK-AR-002-001",
                "claim_id": "CLAIM-20260729-155712-task-ar-002-bean002",
                "task_status": "completed",
                "claim_status": "released",
            },
            "TASK-AR-003": {
                "unit_id": "UNIT-TASK-AR-003-001",
                "claim_id": "CLAIM-20260729-160224-task-ar-003-bean003",
                "task_status": "completed",
                "claim_status": "released",
            },
        },
        "findings": {
            "registered-taskset-undispatchable": "P0",
            "linked-worktree-self-claim-refused": "P0",
            "template-example-classified-as-orphan": "P0",
            "host-state-runtime-taskset-collision": "P0",
            "managed-file-mutated-by-runtime-producer": "P0",
            "web-content-profile-empty": "P1",
            "role-overlay-not-executed": "P1",
        },
    }
}
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


def _semantic_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _absolute_string_paths(value: object, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            findings.extend(_absolute_string_paths(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_absolute_string_paths(item, f"{path}[{index}]"))
    elif isinstance(value, str):
        text = value.strip().replace("\\", "/")
        if text.startswith("/") or re.match(r"^[A-Za-z]:/", text):
            findings.append(path)
    return findings


def _count(record: dict[str, Any], key: str) -> int | None:
    value = record.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def validate_evidence(
    payload: object,
    *,
    expected_host: str | None = None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        return [_finding("invalid-root", "$", "evidence must be a JSON object")]
    if payload.get("schema") != SCHEMA:
        findings.append(_finding("invalid-schema", "schema", f"expected {SCHEMA}"))

    host = expected_host or str(payload.get("host") or "")
    contract = HOST_CONTRACTS.get(host)
    if not contract:
        findings.append(_finding("unknown-host-contract", "host", "a pinned host contract is required"))
        contract = {}
    if payload.get("host") != host:
        findings.append(_finding("host-contract-mismatch", "host", f"expected {host}"))
    if contract and payload.get("pilot_id") != contract["pilot_id"]:
        findings.append(_finding("pilot-contract-mismatch", "pilot_id", f"expected {contract['pilot_id']}"))
    if contract and payload.get("result") != contract["result"]:
        findings.append(_finding("result-contract-mismatch", "result", f"expected {contract['result']}"))
    if contract and _semantic_sha256(payload) != contract["semantic_sha256"]:
        findings.append(_finding("fixture-semantic-digest-mismatch", "$", "fixture differs from the pinned semantic evidence contract"))
    absolute_paths = _absolute_string_paths(payload)
    if absolute_paths:
        findings.append(_finding("absolute-path-leak", absolute_paths[0], "fixture strings must not contain absolute local paths"))

    baselines = _mapping(payload.get("baselines"))
    for key in ("host_commit", "runtime_commit"):
        value = str(baselines.get(key) or "")
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            findings.append(_finding("invalid-baseline", f"baselines.{key}", "expected a full git SHA"))
        elif contract and value != contract["baselines"][key]:
            findings.append(_finding("baseline-contract-mismatch", f"baselines.{key}", "value differs from pinned pilot contract"))

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
    if contract and selected != contract["selected_template_files"]:
        findings.append(_finding("selection-contract-mismatch", "adoption.selected_template_files", "value differs from pinned pilot contract"))
    post_registration = _mapping(adoption.get("post_work_registration_reconcile"))
    post_conflicts = _list(post_registration.get("conflict_paths"))
    if (
        _count(post_registration, "safe_updates") != 0
        or _count(post_registration, "conflicts") != len(post_conflicts)
        or post_conflicts != contract.get("post_registration_conflicts", [])
    ):
        findings.append(
            _finding(
                "post-registration-reconcile-mismatch",
                "adoption.post_work_registration_reconcile",
                "conflict count and paths must match the pinned red-pilot observation",
            )
        )

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
    if _count(content, "file_count") != contract.get("content_file_count"):
        findings.append(_finding("content-file-count-mismatch", "preservation.content.file_count", "value differs from pinned pilot contract"))
    if not _valid_sha(content.get("before")) or not _valid_sha(content.get("after")):
        findings.append(_finding("invalid-content-digest", "preservation.content", "content manifests must be SHA-256 values"))
    elif content.get("before") != content.get("after"):
        findings.append(_finding("content-mutation", "preservation.content", "src/content manifest changed"))

    bootstrap = _mapping(payload.get("bootstrap"))
    if not CLAIM_RE.fullmatch(str(bootstrap.get("upstream_claim_id") or "")):
        findings.append(_finding("missing-bootstrap-claim", "bootstrap.upstream_claim_id", "bootstrap must map to a persisted upstream claim"))
    for key in ("unmapped_diff_count", "consumer_commit_count", "consumer_push_count"):
        if _count(bootstrap, key) != 0:
            findings.append(_finding("bootstrap-effect-nonzero", f"bootstrap.{key}", "must be the integer zero"))

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
        expected_task = _mapping(_mapping(contract.get("tasks")).get(task_id))
        if not expected_task:
            findings.append(_finding("unexpected-task-trace", prefix, "task is not in the pinned host contract"))
        elif (
            task.get("unit_id") != expected_task.get("unit_id")
            or task.get("status") != expected_task.get("task_status")
            or claim.get("claim_id") != expected_task.get("claim_id")
            or claim.get("status") != expected_task.get("claim_status")
        ):
            findings.append(_finding("task-contract-mismatch", prefix, "task, unit, claim, or terminal status differs from the pinned host contract"))
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
        if verified_usage:
            token_values = tuple(routing.get(key) for key in ("input_tokens", "output_tokens"))
            cost = routing.get("cost")
            if (
                routing.get("actual_model_status") != "verified"
                or not str(observed or "").strip()
                or not str(routing.get("observation_source") or "").strip()
                or any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in token_values)
                or not isinstance(cost, (int, float))
                or isinstance(cost, bool)
                or cost < 0
            ):
                findings.append(_finding("invalid-provider-usage-proof", f"{prefix}.routing", "verified usage requires an observed model, source, nonnegative integer tokens, and nonnegative numeric cost"))
        savings_claim = routing.get("savings_claim")
        if savings_claim != "unavailable" and (
            not verified_usage
            or not str(routing.get("savings_observation_source") or "").strip()
            or not str(routing.get("comparison_baseline") or "").strip()
        ):
            findings.append(_finding("unsupported-savings-claim", f"{prefix}.routing.savings_claim", "savings require verified usage, an observation source, and a comparison baseline"))

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
        if _count(effects, key) != 0:
            findings.append(_finding("external-effect-nonzero", f"external_effects.{key}", "offline pilot requires the integer zero"))

    observed_findings: dict[str, str] = {}
    duplicate_finding_codes: set[str] = set()
    for item in _list(payload.get("findings")):
        record = _mapping(item)
        code = str(record.get("code") or "")
        if code in observed_findings:
            duplicate_finding_codes.add(code)
        observed_findings[code] = str(record.get("priority") or "")
    if duplicate_finding_codes or observed_findings != contract.get("findings", {}):
        findings.append(_finding("finding-contract-mismatch", "findings", "codes and priorities must exactly match the pinned host contract"))
    priorities = set(observed_findings.values())
    if "P0" in priorities and payload.get("result") != "blocked":
        findings.append(_finding("p0-not-blocking", "result", "a P0 finding must block the pilot"))

    verification = _mapping(payload.get("verification"))
    expected_verification = {
        "doctor_post_repair_blockers": 0,
        "doctor_post_repair_warnings": 8,
        "check_content_returncode": 0,
        "check_editorial_returncode": 0,
        "state_sync_blockers": 2,
        "work_item_classifier_findings": 2,
    }
    for key, expected in expected_verification.items():
        if _count(verification, key) != expected:
            findings.append(_finding("verification-contract-mismatch", f"verification.{key}", f"expected integer {expected}"))
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
        fixture_label = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        fixture_label = path.name
    try:
        payload = load_evidence(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        findings = [
            _finding(
                "fixture-unavailable",
                fixture_label,
                f"{type(exc).__name__}: fixture could not be loaded",
            )
        ]
    else:
        findings = validate_evidence(payload, expected_host=args.host)
    result = {
        "schema": "agent-runtime-pilot-acceptance-result/v1",
        "host": args.host,
        "fixture": fixture_label,
        "status": "pass" if not findings else "fail",
        "finding_count": len(findings),
        "findings": findings,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"pilot-acceptance: {result['status']}")
        print(f"host={args.host}")
        print(f"fixture={fixture_label}")
        print(f"findings={len(findings)}")
        for finding in findings:
            print(f"- {finding['code']} {finding['path']}: {finding['detail']}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
