"""Validate causal isolation evidence for disposable consumer pilots."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "agent-runtime-pilot-isolation/v1"
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


def analyze(payload: object, evidence_path: Path) -> dict[str, object]:
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


def _load(path: Path) -> tuple[object, dict[str, object] | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        finding = _finding(
            "block",
            "isolation:invalid-evidence-json",
            str(path),
            str(exc),
        )
        return {}, _result([finding])


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
    parser.add_argument("--check", action="store_true", help="Fail on block findings")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw, load_error = _load(args.evidence)
    payload = load_error or analyze(raw, args.evidence)
    print(render(payload, as_json=args.json))
    if args.check and payload["block_count"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
