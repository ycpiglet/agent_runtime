"""Opt-in, read-only evidence checks for an independent security review.

This checks declared identities, source binding and local evidence integrity.
It does not authenticate reviewers, execute tests or certify a live service.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from contextlib import ExitStack
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "agent-runtime-security-review/v1"
CHECKS = frozenset({"authorization-bypass", "request-replay", "failure-recovery"})
MAX_REPORT_BYTES = 256 * 1024
MAX_EVIDENCE_BYTES = 1024 * 1024
SAFE_OPEN_SUPPORTED = os.open in os.supports_dir_fd and hasattr(os, "O_NOFOLLOW")


def _read_regular(root: Path, relative: PurePosixPath, maximum: int) -> bytes:
    """Pin the entire absolute directory chain, including root's ancestors."""
    if not SAFE_OPEN_SUPPORTED:
        raise NotImplementedError
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        directory = os.open(root.anchor, directory_flags)
        stack.callback(os.close, directory)
        for part in (*root.parts[1:], *relative.parts[:-1]):
            directory = os.open(part, directory_flags, dir_fd=directory)
            stack.callback(os.close, directory)
        descriptor = os.open(relative.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=directory)
        stack.callback(os.close, descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            return stream.read(maximum + 1)


def check_report(report: object, *, evidence_root: Path, head: str, base: str) -> dict[str, Any]:
    """Validate closure evidence without trusting commands or URLs in a report."""
    errors: list[str] = []
    unknown = False
    try:
        root = evidence_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError
    except (OSError, RuntimeError, ValueError):
        return {"status": "block", "errors": ["evidence-root:unavailable"]}

    def text(value: object) -> bool:
        return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= 512

    def identity(value: object) -> bool:
        return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_/@:.-]{1,256}", value) is not None

    def reference(value: object, label: str) -> None:
        if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
            errors.append(f"{label}:invalid-reference")
            return
        raw, digest = value["path"], value["sha256"]
        if not isinstance(raw, str) or not raw or len(raw) > 512 or "\\" in raw:
            errors.append(f"{label}:unsafe-path")
            return
        rel = PurePosixPath(raw)
        if rel.is_absolute() or any(part in {"", ".", ".."} for part in raw.split("/")):
            errors.append(f"{label}:unsafe-path")
            return
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            errors.append(f"{label}:invalid-digest")
            return
        try:
            # Pin each parent directory and atomically reject links at open.
            # A path check followed by Path.open would be vulnerable to swaps.
            data = _read_regular(root, rel, MAX_EVIDENCE_BYTES)
            if not data or len(data) > MAX_EVIDENCE_BYTES:
                raise ValueError
            if hashlib.sha256(data).hexdigest() != digest:
                errors.append(f"{label}:evidence-changed")
        except (OSError, ValueError, NotImplementedError, AttributeError):
            errors.append(f"{label}:evidence-unavailable")

    def references(value: object, label: str) -> None:
        if not isinstance(value, list) or not 1 <= len(value) <= 32:
            errors.append(f"{label}:missing-evidence")
            return
        for item in value:
            reference(item, label)

    if not isinstance(report, dict):
        return {"status": "block", "errors": ["report:invalid"]}
    if report.get("schema_version") != SCHEMA or not text(report.get("goal_id")):
        errors.append("report:invalid-identity")
    if not all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) for value in (head, base)):
        errors.append("source:invalid-expected-revision")
    source = report.get("source")
    if not isinstance(source, dict) or source.get("head") != head or source.get("base") != base:
        errors.append("source:revision-mismatch")
    reviewer, contributors = report.get("reviewer"), report.get("contributors")
    if not identity(reviewer) or not isinstance(contributors, list) or not 1 <= len(contributors) <= 64 or not all(identity(x) for x in contributors):
        errors.append("reviewer:identity-missing")
    elif reviewer in contributors:
        errors.append("reviewer:self-review")
    environment = report.get("environment")
    if not isinstance(environment, dict) or not isinstance(environment.get("kind"), str) or environment["kind"] not in {"synthetic", "isolated", "staging", "production-read-only"} or not text(environment.get("target")) or not text(environment.get("authorization_ref")):
        errors.append("environment:scope-missing")

    checks = report.get("checks")
    seen: set[str] = set()
    if not isinstance(checks, list) or len(checks) > 3:
        errors.append("checks:invalid")
        checks = []
    for item in checks:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or item["id"] not in CHECKS or item["id"] in seen:
            errors.append("checks:unknown-or-duplicate")
            continue
        seen.add(item["id"])
        status = item.get("status")
        if status == "unknown":
            unknown = True
            if not text(item.get("reason")):
                errors.append("checks:unknown-without-reason")
        elif isinstance(status, str) and status in {"passed", "failed"}:
            references(item.get("evidence_refs"), f"checks:{item['id']}")
            if status == "failed":
                errors.append(f"checks:{item['id']}:failed")
        else:
            errors.append("checks:invalid-status")
    if seen != CHECKS:
        unknown = True

    findings = report.get("findings")
    if not isinstance(findings, list) or len(findings) > 100:
        errors.append("findings:invalid")
        findings = []
    finding_ids: set[str] = set()
    for item in findings:
        if not isinstance(item, dict) or not text(item.get("id")):
            errors.append("findings:invalid-identity")
            continue
        if item["id"] in finding_ids:
            errors.append("findings:duplicate")
        finding_ids.add(item["id"])
        reference(item.get("reproduction"), "finding:reproduction")
        state = item.get("state")
        if not isinstance(state, str) or state not in {"open", "fixed", "verified"}:
            errors.append("finding:invalid-state")
        elif state != "verified":
            errors.append("finding:not-independently-verified")
        else:
            for key in ("fix_refs", "retest_refs", "regression_refs"):
                references(item.get(key), f"finding:{key}")
            if item.get("verified_by") != reviewer or item.get("verified_head") != head:
                errors.append("finding:verification-binding-mismatch")
    return {
        "status": "block" if errors else "unknown" if unknown else "pass",
        "errors": errors,
        "missing_checks": sorted(CHECKS - seen),
        "assurance": "declared-scope-evidence-only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--base", required=True)
    args = parser.parse_args(argv)
    try:
        report_path = args.report.absolute()
        raw = _read_regular(report_path.parent.resolve(strict=True), PurePosixPath(report_path.name), MAX_REPORT_BYTES)
        if len(raw) > MAX_REPORT_BYTES:
            raise ValueError
        result = check_report(json.loads(raw), evidence_root=args.evidence_root, head=args.head, base=args.base)
    except (OSError, ValueError, RuntimeError, NotImplementedError):
        result = {"status": "block", "errors": ["report:unavailable-or-invalid"]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
