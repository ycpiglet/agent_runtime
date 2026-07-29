"""Block silent drift between source and packaged project scripts.

The mirror contract pins the exact paths expected on both sides. Those scripts
must be byte-identical unless a deliberate source/consumer variant pins both
byte digests and a bounded reason. Root-only and template-only scripts remain
valid when they are outside the expected-common inventory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCHEMA = "agent-runtime-template-mirror-contract/v2"
SOURCE_REL = Path("scripts")
TEMPLATE_REL = Path("src/agent_runtime/templates/project/scripts")
CONTRACT_REL = Path("agents/project/TEMPLATE-MIRROR-CONTRACT.json")
ELIGIBLE_SUFFIXES = {".py", ".cmd"}
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
MIN_REASON_LENGTH = 20
MAX_REASON_LENGTH = 500


class DuplicateContractKey(ValueError):
    """Raised when JSON object syntax repeats a key."""

    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, value in pairs:
        if key in payload:
            raise DuplicateContractKey(key)
        payload[key] = value
    return payload


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _eligible(directory: Path) -> dict[str, Path]:
    if not directory.is_dir():
        return {}
    return {
        path.relative_to(directory).as_posix(): path
        for path in directory.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix in ELIGIBLE_SUFFIXES
    }


def _safe_script_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    candidate = PurePosixPath(value)
    if (
        candidate.is_absolute()
        or candidate.as_posix() != value
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.suffix not in ELIGIBLE_SUFFIXES
    ):
        return None
    return value


def _load_contract(
    path: Path,
    findings: list[str],
) -> tuple[list[str], dict[str, Any]]:
    if not path.is_file():
        findings.append(f"mirror:missing-contract:{CONTRACT_REL.as_posix()}")
        return [], {}
    try:
        payload = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_object,
        )
    except DuplicateContractKey as exc:
        findings.append(f"mirror:duplicate-contract-key:{exc.key}")
        return [], {}
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(f"mirror:invalid-contract-json:{CONTRACT_REL.as_posix()}:{exc}")
        return [], {}
    if not isinstance(payload, dict):
        findings.append(f"mirror:invalid-contract-root:{CONTRACT_REL.as_posix()}")
        return [], {}
    if payload.get("schema") != SCHEMA:
        findings.append(f"mirror:invalid-contract-schema:{CONTRACT_REL.as_posix()}")

    expected_raw = payload.get("expected_common")
    expected: list[str] = []
    if not isinstance(expected_raw, list):
        findings.append("mirror:invalid-expected-common-list")
    else:
        if all(isinstance(item, str) for item in expected_raw):
            if expected_raw != sorted(expected_raw):
                findings.append("mirror:unsorted-expected-common")
        seen: set[str] = set()
        for raw_path in expected_raw:
            path_value = _safe_script_path(raw_path)
            if path_value is None:
                findings.append(f"mirror:invalid-expected-path:{raw_path}")
                continue
            if path_value in seen:
                findings.append(f"mirror:duplicate-expected-path:{path_value}")
                continue
            seen.add(path_value)
            expected.append(path_value)

    divergences = payload.get("intentional_divergences")
    if not isinstance(divergences, dict):
        findings.append(f"mirror:invalid-divergence-map:{CONTRACT_REL.as_posix()}")
        return expected, {}
    return expected, divergences


def analyze(root: Path) -> dict[str, object]:
    root = root.resolve()
    findings: list[str] = []
    source_dir = root / SOURCE_REL
    template_dir = root / TEMPLATE_REL
    if not source_dir.is_dir():
        findings.append(f"mirror:missing-source-directory:{SOURCE_REL.as_posix()}")
    if not template_dir.is_dir():
        findings.append(f"mirror:missing-template-directory:{TEMPLATE_REL.as_posix()}")

    source = _eligible(source_dir)
    template = _eligible(template_dir)
    common = sorted(source.keys() & template.keys())
    expected, contract = _load_contract(root / CONTRACT_REL, findings)
    expected_set = set(expected)
    common_set = set(common)

    for path in expected:
        if path not in source:
            findings.append(f"mirror:expected-source-missing:{path}")
        if path not in template:
            findings.append(f"mirror:expected-template-missing:{path}")
    for path in sorted(common_set - expected_set):
        findings.append(f"mirror:unexpected-common:{path}")

    valid_contract: dict[str, dict[str, str]] = {}
    for raw_path, raw_entry in sorted(contract.items(), key=lambda item: str(item[0])):
        path = _safe_script_path(raw_path)
        if path is None:
            findings.append(f"mirror:invalid-exception-path:{raw_path}")
            continue
        if path not in expected_set:
            findings.append(f"mirror:exception-not-expected:{path}")
            continue
        if path not in common_set:
            findings.append(f"mirror:exception-not-common:{path}")
            continue
        if not isinstance(raw_entry, dict):
            findings.append(f"mirror:invalid-exception-record:{path}")
            continue

        reason = raw_entry.get("reason")
        source_sha = raw_entry.get("source_sha256")
        template_sha = raw_entry.get("template_sha256")
        valid = True
        if (
            not isinstance(reason, str)
            or len(reason.strip()) < MIN_REASON_LENGTH
            or len(reason.strip()) > MAX_REASON_LENGTH
        ):
            findings.append(f"mirror:invalid-exception-reason:{path}")
            valid = False
        if not isinstance(source_sha, str) or DIGEST_PATTERN.fullmatch(source_sha) is None:
            findings.append(f"mirror:invalid-source-digest:{path}")
            valid = False
        if not isinstance(template_sha, str) or DIGEST_PATTERN.fullmatch(template_sha) is None:
            findings.append(f"mirror:invalid-template-digest:{path}")
            valid = False
        if valid:
            valid_contract[path] = {
                "reason": reason.strip(),
                "source_sha256": source_sha,
                "template_sha256": template_sha,
            }

    identical = 0
    intentional = 0
    for path in sorted(expected_set & common_set):
        source_digest = _digest(source[path])
        template_digest = _digest(template[path])
        entry = valid_contract.get(path)
        if source_digest == template_digest:
            identical += 1
            if path in contract:
                findings.append(f"mirror:stale-identical-exception:{path}")
            continue
        if path not in contract:
            findings.append(f"mirror:unlisted-drift:{path}")
            continue
        if entry is None:
            continue
        entry_valid = True
        if entry["source_sha256"] != source_digest:
            findings.append(f"mirror:exception-source-digest-mismatch:{path}")
            entry_valid = False
        if entry["template_sha256"] != template_digest:
            findings.append(f"mirror:exception-template-digest-mismatch:{path}")
            entry_valid = False
        if entry_valid:
            intentional += 1

    return {
        "schema": SCHEMA,
        "expected_common": len(expected),
        "current_common": len(common),
        "eligible_common": len(common),
        "identical": identical,
        "intentional": intentional,
        "findings": findings,
    }


def render(payload: dict[str, object], *, as_json: bool) -> str:
    if as_json:
        return json.dumps(payload, indent=2, sort_keys=True)
    findings = payload["findings"]
    lines = [
        (
            "template-mirror: "
            f"expected={payload['expected_common']} "
            f"common={payload['current_common']} "
            f"identical={payload['identical']} "
            f"intentional={payload['intentional']} "
            f"findings={len(findings)}"
        )
    ]
    lines.extend(f"- block {finding}" for finding in findings)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify source/template script mirror parity")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Agent Runtime repository root")
    parser.add_argument("--check", action="store_true", help="Fail when mirror findings exist")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = analyze(args.root)
    print(render(payload, as_json=args.json))
    if args.check and payload["findings"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
