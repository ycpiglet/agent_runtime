"""Validate causal isolation evidence for disposable consumer pilots."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


RAW_SCHEMA = "agent-runtime-pilot-isolation/v1"
PORTABLE_SCHEMA = "agent-runtime-pilot-isolation/v2"
RAW_PROOF_SCHEMA = "agent-runtime-pilot-isolation-raw-proof/v1"
SCHEMA = RAW_SCHEMA
ROLES = {"disposable_target", "frozen_control", "live_observation"}
ATTRIBUTIONS = {"authorized_target", "none", "external_or_unattributed", "pilot_caused"}
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")


def _finding(severity: str, code: str, path: str, detail: str) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "path": path,
        "detail": detail,
    }


def _canonical_absolute(value: object) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    raw = Path(value)
    if not raw.is_absolute() or ".." in raw.parts:
        return None
    resolved = raw.resolve(strict=False)
    if str(raw) != str(resolved):
        return None
    return resolved


def _valid_snapshot(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return (
        isinstance(value.get("head"), str)
        and HEX_40.fullmatch(value["head"]) is not None
        and isinstance(value.get("status_sha256"), str)
        and HEX_64.fullmatch(value["status_sha256"]) is not None
        and isinstance(value.get("tracked_diff_sha256"), str)
        and HEX_64.fullmatch(value["tracked_diff_sha256"]) is not None
    )


def _changed(before: dict[str, str], after: dict[str, str]) -> bool:
    return any(
        before[field] != after[field]
        for field in ("head", "status_sha256", "tracked_diff_sha256")
    )


def _overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


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


def _portable_checkout_findings(
    raw_checkouts: object,
) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    findings: list[dict[str, str]] = []
    if not isinstance(raw_checkouts, list):
        return (
            [
                _finding(
                    "block",
                    "isolation:invalid-checkouts",
                    "checkouts",
                    "checkouts must be a list",
                )
            ],
            [],
        )

    checkouts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    role_counts = {role: 0 for role in ROLES}
    allowed_keys = {
        "id",
        "role",
        "before",
        "after",
        "change_attribution",
    }
    for index, raw_checkout in enumerate(raw_checkouts):
        path = f"checkouts[{index}]"
        if not isinstance(raw_checkout, dict):
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-checkout",
                    path,
                    "checkout entry must be an object",
                )
            )
            continue
        unknown = sorted(set(raw_checkout) - allowed_keys)
        if unknown:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-portable-checkout-field",
                    path,
                    f"unexpected fields: {', '.join(unknown)}",
                )
            )
        checkout_id = raw_checkout.get("id")
        if not isinstance(checkout_id, str) or not checkout_id.strip():
            findings.append(
                _finding(
                    "block",
                    "isolation:missing-checkout-id",
                    path,
                    "checkout id is required",
                )
            )
            continue
        if checkout_id in seen_ids:
            findings.append(
                _finding(
                    "block",
                    "isolation:duplicate-checkout-id",
                    checkout_id,
                    "checkout ids must be unique",
                )
            )
            continue
        seen_ids.add(checkout_id)

        role = raw_checkout.get("role")
        if role not in ROLES:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-checkout-role",
                    checkout_id,
                    f"role must be one of {sorted(ROLES)}",
                )
            )
            continue
        role_counts[role] += 1
        before = raw_checkout.get("before")
        after = raw_checkout.get("after")
        snapshots_valid = True
        if not _valid_snapshot(before):
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-before-snapshot",
                    checkout_id,
                    "before snapshot must contain a 40-hex head and two 64-hex digests",
                )
            )
            snapshots_valid = False
        if not _valid_snapshot(after):
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-after-snapshot",
                    checkout_id,
                    "after snapshot must contain a 40-hex head and two 64-hex digests",
                )
            )
            snapshots_valid = False
        attribution = raw_checkout.get("change_attribution")
        if attribution not in ATTRIBUTIONS:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-change-attribution",
                    checkout_id,
                    f"change_attribution must be one of {sorted(ATTRIBUTIONS)}",
                )
            )
        checkouts.append(
            {
                "id": checkout_id,
                "role": role,
                "before": before,
                "after": after,
                "snapshots_valid": snapshots_valid,
                "attribution": attribution,
            }
        )

    if role_counts["disposable_target"] == 0:
        findings.append(
            _finding(
                "block",
                "isolation:missing-disposable-target",
                "checkouts",
                "at least one disposable_target checkout is required",
            )
        )
    if role_counts["frozen_control"] == 0:
        findings.append(
            _finding(
                "block",
                "isolation:missing-frozen-control",
                "checkouts",
                "at least one frozen_control checkout is required",
            )
        )
    return findings, checkouts


def _analyze_portable(
    payload: dict[str, Any],
    evidence_path: Path,
) -> dict[str, object]:
    findings: list[dict[str, str]] = []
    allowed_root = {
        "schema",
        "evidence_mode",
        "pilot_id",
        "raw_proof",
        "observed_write_checkout_ids",
        "checkouts",
    }
    unknown_root = sorted(set(payload) - allowed_root)
    if unknown_root:
        findings.append(
            _finding(
                "block",
                "isolation:invalid-portable-field",
                "$",
                f"unexpected fields: {', '.join(unknown_root)}",
            )
        )
    if payload.get("evidence_mode") != "sanitized_projection":
        findings.append(
            _finding(
                "block",
                "isolation:invalid-evidence-mode",
                "evidence_mode",
                "v2 evidence must use sanitized_projection",
            )
        )
    if not isinstance(payload.get("pilot_id"), str) or not payload["pilot_id"].strip():
        findings.append(
            _finding(
                "block",
                "isolation:missing-pilot-id",
                str(evidence_path),
                "pilot_id is required",
            )
        )
    absolute_paths = _absolute_string_paths(payload)
    if absolute_paths:
        findings.append(
            _finding(
                "block",
                "isolation:absolute-path-leak",
                absolute_paths[0],
                "sanitized projection must not contain absolute paths",
            )
        )

    raw_proof = payload.get("raw_proof")
    if not isinstance(raw_proof, dict):
        raw_proof = {}
        findings.append(
            _finding(
                "block",
                "isolation:missing-raw-proof",
                "raw_proof",
                "sanitized projection requires a raw proof binding",
            )
        )
    allowed_proof = {
        "schema",
        "evidence_sha256",
        "status",
        "block_count",
        "watch_count",
        "finding_codes",
    }
    unknown_proof = sorted(set(raw_proof) - allowed_proof)
    if unknown_proof:
        findings.append(
            _finding(
                "block",
                "isolation:invalid-raw-proof-field",
                "raw_proof",
                f"unexpected fields: {', '.join(unknown_proof)}",
            )
        )
    if raw_proof.get("schema") != RAW_PROOF_SCHEMA:
        findings.append(
            _finding(
                "block",
                "isolation:invalid-raw-proof-schema",
                "raw_proof.schema",
                f"expected {RAW_PROOF_SCHEMA}",
            )
        )
    if not isinstance(raw_proof.get("evidence_sha256"), str) or not HEX_64.fullmatch(
        raw_proof["evidence_sha256"]
    ):
        findings.append(
            _finding(
                "block",
                "isolation:invalid-raw-evidence-digest",
                "raw_proof.evidence_sha256",
                "raw evidence binding must be a 64-hex SHA-256",
            )
        )
    block_count = raw_proof.get("block_count")
    watch_count = raw_proof.get("watch_count")
    finding_codes = raw_proof.get("finding_codes")
    if (
        not isinstance(block_count, int)
        or isinstance(block_count, bool)
        or block_count != 0
        or raw_proof.get("status") not in {"pass", "pass_with_watch"}
    ):
        findings.append(
            _finding(
                "block",
                "isolation:raw-proof-blocked",
                "raw_proof",
                "projection requires a recorded raw decision with zero blockers",
            )
        )
    if (
        not isinstance(watch_count, int)
        or isinstance(watch_count, bool)
        or watch_count < 0
        or not isinstance(finding_codes, list)
        or len(finding_codes) != watch_count
        or any(not isinstance(code, str) or not code for code in finding_codes)
        or (
            isinstance(finding_codes, list)
            and all(isinstance(code, str) for code in finding_codes)
            and len(set(finding_codes)) != len(finding_codes)
        )
        or (watch_count == 0 and raw_proof.get("status") != "pass")
        or (watch_count > 0 and raw_proof.get("status") != "pass_with_watch")
    ):
        findings.append(
            _finding(
                "block",
                "isolation:invalid-raw-proof-decision",
                "raw_proof",
                "status, watch count, and finding codes must agree",
            )
        )

    checkout_findings, checkouts = _portable_checkout_findings(payload.get("checkouts"))
    findings.extend(checkout_findings)
    checkouts_by_id = {checkout["id"]: checkout for checkout in checkouts}
    write_ids = payload.get("observed_write_checkout_ids")
    if not isinstance(write_ids, list):
        write_ids = []
        findings.append(
            _finding(
                "block",
                "isolation:invalid-observed-write-checkout-ids",
                "observed_write_checkout_ids",
                "observed_write_checkout_ids must be a list",
            )
        )
    seen_write_ids: set[str] = set()
    for index, checkout_id in enumerate(write_ids):
        path = f"observed_write_checkout_ids[{index}]"
        if not isinstance(checkout_id, str) or not checkout_id:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-observed-write-checkout",
                    path,
                    "observed write checkout id must be a non-empty string",
                )
            )
            continue
        if checkout_id in seen_write_ids:
            findings.append(
                _finding(
                    "block",
                    "isolation:duplicate-observed-write-checkout",
                    path,
                    "observed write checkout ids must be unique",
                )
            )
            continue
        seen_write_ids.add(checkout_id)
        checkout = checkouts_by_id.get(checkout_id)
        if checkout is None:
            findings.append(
                _finding(
                    "block",
                    "isolation:unknown-observed-write-checkout",
                    path,
                    "observed write id must map to a declared checkout",
                )
            )
        elif checkout["role"] != "disposable_target":
            findings.append(
                _finding(
                    "block",
                    "isolation:write-outside-disposable-target",
                    checkout_id,
                    "observed writes must map only to disposable_target checkouts",
                )
            )

    for checkout in checkouts:
        if not checkout["snapshots_valid"] or checkout["attribution"] not in ATTRIBUTIONS:
            continue
        checkout_id = checkout["id"]
        changed = _changed(checkout["before"], checkout["after"])
        attribution = checkout["attribution"]
        role = checkout["role"]
        if role == "disposable_target" and changed and attribution != "authorized_target":
            findings.append(
                _finding(
                    "block",
                    f"isolation:target-change-unattributed:{checkout_id}",
                    checkout_id,
                    "a changed disposable target must use authorized_target attribution",
                )
            )
        if (
            role == "disposable_target"
            and changed
            and checkout_id not in seen_write_ids
        ):
            findings.append(
                _finding(
                    "block",
                    f"isolation:changed-target-write-unrecorded:{checkout_id}",
                    checkout_id,
                    "a changed disposable target must be present in observed writes",
                )
            )
        elif role == "frozen_control":
            if changed:
                findings.append(
                    _finding(
                        "block",
                        f"isolation:frozen-control-changed:{checkout_id}",
                        checkout_id,
                        "a frozen control changed during the pilot window",
                    )
                )
            if attribution != "none":
                findings.append(
                    _finding(
                        "block",
                        f"isolation:frozen-control-attribution:{checkout_id}",
                        checkout_id,
                        "a frozen control must use none attribution",
                    )
                )
        elif role == "live_observation" and changed:
            if attribution == "pilot_caused":
                findings.append(
                    _finding(
                        "block",
                        f"isolation:unsupported-live-causality:{checkout_id}",
                        checkout_id,
                        "pilot causality cannot be claimed outside the disposable write surface",
                    )
                )
            elif attribution != "external_or_unattributed":
                findings.append(
                    _finding(
                        "block",
                        f"isolation:live-drift-attribution:{checkout_id}",
                        checkout_id,
                        "changed live observations must use external_or_unattributed",
                    )
                )

    if isinstance(finding_codes, list) and isinstance(watch_count, int):
        for code in finding_codes[: max(watch_count, 0)]:
            if isinstance(code, str) and code:
                findings.append(
                    _finding(
                        "watch",
                        code,
                        "raw_proof.finding_codes",
                        "watch preserved from validated raw isolation evidence",
                    )
                )
    return _result(findings)


def project_sanitized_evidence(
    payload: object,
    *,
    evidence_path: Path,
    raw_evidence_sha256: str,
) -> dict[str, object]:
    if not isinstance(raw_evidence_sha256, str) or not HEX_64.fullmatch(
        raw_evidence_sha256
    ):
        raise ValueError("isolation:invalid-raw-evidence-digest")
    if not isinstance(payload, dict) or payload.get("schema") != RAW_SCHEMA:
        raise ValueError("isolation:projection-requires-raw-v1")
    raw_result = analyze(payload, evidence_path)
    if raw_result["block_count"]:
        raise ValueError("isolation:raw-proof-blocked")

    raw_checkouts = payload.get("checkouts")
    if not isinstance(raw_checkouts, list):
        raise ValueError("isolation:invalid-checkouts")
    checkouts_by_root: list[tuple[str, str, Path]] = []
    portable_checkouts: list[dict[str, object]] = []
    for raw_checkout in raw_checkouts:
        if not isinstance(raw_checkout, dict):
            raise ValueError("isolation:invalid-checkout")
        checkout_id = str(raw_checkout.get("id") or "")
        role = str(raw_checkout.get("role") or "")
        root = _canonical_absolute(raw_checkout.get("root"))
        if not checkout_id or role not in ROLES or root is None:
            raise ValueError("isolation:invalid-checkout")
        checkouts_by_root.append((checkout_id, role, root))
        portable_checkouts.append(
            {
                "id": checkout_id,
                "role": role,
                "before": raw_checkout.get("before"),
                "after": raw_checkout.get("after"),
                "change_attribution": raw_checkout.get("change_attribution"),
            }
        )

    observed_ids: list[str] = []
    raw_write_roots = payload.get("observed_write_roots")
    if not isinstance(raw_write_roots, list):
        raise ValueError("isolation:invalid-observed-write-roots")
    for raw_write_root in raw_write_roots:
        write_root = _canonical_absolute(raw_write_root)
        if write_root is None:
            raise ValueError("isolation:invalid-observed-write-root")
        matches = [
            checkout_id
            for checkout_id, role, root in checkouts_by_root
            if role == "disposable_target"
            and (write_root == root or root in write_root.parents)
        ]
        if len(matches) != 1:
            raise ValueError("isolation:write-root-mapping-ambiguous")
        if matches[0] not in observed_ids:
            observed_ids.append(matches[0])

    projection = {
        "schema": PORTABLE_SCHEMA,
        "evidence_mode": "sanitized_projection",
        "pilot_id": payload["pilot_id"],
        "raw_proof": {
            "schema": RAW_PROOF_SCHEMA,
            "evidence_sha256": raw_evidence_sha256,
            "status": raw_result["status"],
            "block_count": raw_result["block_count"],
            "watch_count": raw_result["watch_count"],
            "finding_codes": [
                finding["code"]
                for finding in raw_result["findings"]
                if finding["severity"] == "watch"
            ],
        },
        "observed_write_checkout_ids": observed_ids,
        "checkouts": portable_checkouts,
    }
    portable_result = _analyze_portable(projection, evidence_path)
    if portable_result["block_count"]:
        raise ValueError("isolation:invalid-sanitized-projection")
    return projection


def analyze(payload: object, evidence_path: Path) -> dict[str, object]:
    if isinstance(payload, dict) and payload.get("schema") == PORTABLE_SCHEMA:
        return _analyze_portable(payload, evidence_path)
    findings: list[dict[str, str]] = []
    if not isinstance(payload, dict):
        findings.append(
            _finding(
                "block",
                "isolation:invalid-evidence-root",
                str(evidence_path),
                "evidence must be a JSON object",
            )
        )
        return _result(findings)

    if payload.get("schema") != SCHEMA:
        findings.append(
            _finding(
                "block",
                "isolation:invalid-schema",
                str(evidence_path),
                f"schema must be {SCHEMA}",
            )
        )
    if not isinstance(payload.get("pilot_id"), str) or not payload["pilot_id"].strip():
        findings.append(
            _finding("block", "isolation:missing-pilot-id", str(evidence_path), "pilot_id is required")
        )

    raw_checkouts = payload.get("checkouts")
    if not isinstance(raw_checkouts, list):
        raw_checkouts = []
        findings.append(
            _finding(
                "block",
                "isolation:invalid-checkouts",
                str(evidence_path),
                "checkouts must be a list",
            )
        )

    seen_ids: set[str] = set()
    checkouts: list[dict[str, Any]] = []
    roots: list[tuple[str, Path]] = []
    role_counts = {role: 0 for role in ROLES}
    for index, raw_checkout in enumerate(raw_checkouts):
        fallback_path = f"checkouts[{index}]"
        if not isinstance(raw_checkout, dict):
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-checkout",
                    fallback_path,
                    "checkout entry must be an object",
                )
            )
            continue
        checkout_id = raw_checkout.get("id")
        checkout_path = str(checkout_id) if isinstance(checkout_id, str) and checkout_id else fallback_path
        if not isinstance(checkout_id, str) or not checkout_id.strip():
            findings.append(
                _finding("block", "isolation:missing-checkout-id", fallback_path, "checkout id is required")
            )
            continue
        if checkout_id in seen_ids:
            findings.append(
                _finding(
                    "block",
                    "isolation:duplicate-checkout-id",
                    checkout_id,
                    "checkout ids must be unique",
                )
            )
            continue
        seen_ids.add(checkout_id)

        role = raw_checkout.get("role")
        if role not in ROLES:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-checkout-role",
                    checkout_path,
                    f"role must be one of {sorted(ROLES)}",
                )
            )
            continue
        role_counts[role] += 1

        root = _canonical_absolute(raw_checkout.get("root"))
        if root is None:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-checkout-root",
                    checkout_path,
                    "checkout root must be an absolute canonical path",
                )
            )
            continue
        roots.append((checkout_id, root))

        before = raw_checkout.get("before")
        after = raw_checkout.get("after")
        snapshots_valid = True
        if not _valid_snapshot(before):
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-before-snapshot",
                    checkout_path,
                    "before snapshot must contain a 40-hex head and two 64-hex digests",
                )
            )
            snapshots_valid = False
        if not _valid_snapshot(after):
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-after-snapshot",
                    checkout_path,
                    "after snapshot must contain a 40-hex head and two 64-hex digests",
                )
            )
            snapshots_valid = False

        attribution = raw_checkout.get("change_attribution")
        if attribution not in ATTRIBUTIONS:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-change-attribution",
                    checkout_path,
                    f"change_attribution must be one of {sorted(ATTRIBUTIONS)}",
                )
            )
        checkouts.append(
            {
                "id": checkout_id,
                "role": role,
                "root": root,
                "before": before,
                "after": after,
                "snapshots_valid": snapshots_valid,
                "attribution": attribution,
            }
        )

    if role_counts["disposable_target"] == 0:
        findings.append(
            _finding(
                "block",
                "isolation:missing-disposable-target",
                "checkouts",
                "at least one disposable_target checkout is required",
            )
        )
    if role_counts["frozen_control"] == 0:
        findings.append(
            _finding(
                "block",
                "isolation:missing-frozen-control",
                "checkouts",
                "at least one frozen_control checkout is required",
            )
        )

    for index, (left_id, left_root) in enumerate(roots):
        for right_id, right_root in roots[index + 1 :]:
            if _overlap(left_root, right_root):
                findings.append(
                    _finding(
                        "block",
                        "isolation:overlapping-checkout-roots",
                        f"{left_id},{right_id}",
                        f"checkout roots overlap: {left_root} and {right_root}",
                    )
                )

    target_roots = [
        checkout["root"]
        for checkout in checkouts
        if checkout["role"] == "disposable_target"
    ]
    raw_write_roots = payload.get("observed_write_roots")
    if not isinstance(raw_write_roots, list):
        raw_write_roots = []
        findings.append(
            _finding(
                "block",
                "isolation:invalid-observed-write-roots",
                "observed_write_roots",
                "observed_write_roots must be a list",
            )
        )
    for index, raw_write_root in enumerate(raw_write_roots):
        write_root = _canonical_absolute(raw_write_root)
        if write_root is None:
            findings.append(
                _finding(
                    "block",
                    "isolation:invalid-observed-write-root",
                    f"observed_write_roots[{index}]",
                    "observed write root must be an absolute canonical path",
                )
            )
            continue
        if not any(write_root == target or target in write_root.parents for target in target_roots):
            findings.append(
                _finding(
                    "block",
                    "isolation:write-outside-disposable-target",
                    str(write_root),
                    "observed writes must be contained by a disposable_target root",
                )
            )

    for checkout in checkouts:
        if not checkout["snapshots_valid"] or checkout["attribution"] not in ATTRIBUTIONS:
            continue
        checkout_id = checkout["id"]
        changed = _changed(checkout["before"], checkout["after"])
        attribution = checkout["attribution"]
        role = checkout["role"]
        if role == "disposable_target":
            if changed and attribution != "authorized_target":
                findings.append(
                    _finding(
                        "block",
                        f"isolation:target-change-unattributed:{checkout_id}",
                        checkout_id,
                        "a changed disposable target must use authorized_target attribution",
                    )
                )
        elif role == "frozen_control":
            if changed:
                findings.append(
                    _finding(
                        "block",
                        f"isolation:frozen-control-changed:{checkout_id}",
                        checkout_id,
                        "a frozen control changed during the pilot window",
                    )
                )
            if attribution != "none":
                findings.append(
                    _finding(
                        "block",
                        f"isolation:frozen-control-attribution:{checkout_id}",
                        checkout_id,
                        "a frozen control must use none attribution",
                    )
                )
        elif role == "live_observation" and changed:
            if attribution == "external_or_unattributed":
                findings.append(
                    _finding(
                        "watch",
                        f"isolation:live-drift-unattributed:{checkout_id}",
                        checkout_id,
                        "live checkout drift was observed but is not attributed to the pilot",
                    )
                )
            elif attribution == "pilot_caused":
                findings.append(
                    _finding(
                        "block",
                        f"isolation:unsupported-live-causality:{checkout_id}",
                        checkout_id,
                        "pilot causality cannot be claimed outside the disposable write surface",
                    )
                )
            else:
                findings.append(
                    _finding(
                        "block",
                        f"isolation:live-drift-attribution:{checkout_id}",
                        checkout_id,
                        "changed live observations must use external_or_unattributed",
                    )
                )

    return _result(findings)


def _result(findings: list[dict[str, str]]) -> dict[str, object]:
    block_count = sum(item["severity"] == "block" for item in findings)
    watch_count = sum(item["severity"] == "watch" for item in findings)
    status = "fail" if block_count else ("pass_with_watch" if watch_count else "pass")
    return {
        "schema": SCHEMA,
        "status": status,
        "block_count": block_count,
        "watch_count": watch_count,
        "findings": findings,
    }


def _load(
    path: Path,
) -> tuple[object, bytes | None, dict[str, object] | None]:
    try:
        encoded = path.read_bytes()
        payload = json.loads(encoded.decode("utf-8"))
        return payload, encoded, None
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        finding = _finding(
            "block",
            "isolation:invalid-evidence-json",
            str(path),
            str(exc),
        )
        return {}, None, _result([finding])


def render(payload: dict[str, object], *, as_json: bool) -> str:
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)
    lines = [
        (
            f"pilot-isolation: status={payload['status']} "
            f"blocks={payload['block_count']} watches={payload['watch_count']}"
        )
    ]
    for finding in payload["findings"]:
        lines.append(
            f"- {finding['severity']} {finding['code']} {finding['path']}: {finding['detail']}"
        )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate disposable pilot isolation evidence")
    parser.add_argument("--evidence", type=Path, required=True, help="Pilot isolation evidence JSON")
    parser.add_argument(
        "--sanitize-out",
        type=Path,
        default=None,
        help="Write a deterministic v2 projection after raw v1 validation",
    )
    parser.add_argument("--check", action="store_true", help="Fail on block findings")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw, raw_bytes, load_error = _load(args.evidence)
    if args.sanitize_out is not None and load_error is None:
        try:
            if raw_bytes is None:
                raise ValueError("isolation:raw-evidence-bytes-missing")
            digest = hashlib.sha256(raw_bytes).hexdigest()
            projection = project_sanitized_evidence(
                raw,
                evidence_path=args.evidence,
                raw_evidence_sha256=digest,
            )
            _write_json_atomic(args.sanitize_out, projection)
            raw = projection
        except (OSError, ValueError) as exc:
            load_error = _result(
                [
                    _finding(
                        "block",
                        "isolation:projection-failed",
                        str(args.sanitize_out),
                        str(exc),
                    )
                ]
            )
    payload = load_error or analyze(raw, args.evidence)
    print(render(payload, as_json=args.json))
    if args.check and payload["block_count"]:
        return 1
    return 0


def _write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
