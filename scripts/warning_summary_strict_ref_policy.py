#!/usr/bin/env python3
"""Utilities for strict-ref policy decision artifact write/validation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def _normalize_lines(value: str) -> str:
    return "\n".join(
        line.strip()
        for line in (value or "").replace("\r", "").splitlines()
        if line.strip()
    )


def _resolve_env(value: str | None, env_var: str) -> str:
    if value is not None:
        return value
    return os.environ.get(env_var, "")


def _write_artifact(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _load_artifact(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"policy artifact missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"policy artifact payload must be JSON object, got {type(data)}")
    return data


def _validate(payload: dict, expected: dict) -> list[str]:
    mismatches = []
    if payload.get("github_event_name") != expected["github_event_name"]:
        mismatches.append(
            f"github_event_name mismatch: {payload.get('github_event_name')!r} != {expected['github_event_name']!r}"
        )
    if payload.get("github_ref") != expected["github_ref"]:
        mismatches.append(
            f"github_ref mismatch: {payload.get('github_ref')!r} != {expected['github_ref']!r}"
        )
    if str(payload.get("run_id", "")) != expected["run_id"]:
        mismatches.append(
            f"run_id mismatch: {payload.get('run_id')!r} != {expected['run_id']!r}"
        )
    if str(payload.get("job_attempt", "")) != expected["job_attempt"]:
        mismatches.append(
            f"job_attempt mismatch: {payload.get('job_attempt')!r} != {expected['job_attempt']!r}"
        )
    if str(payload.get("matrix_python_version", "")) != expected["matrix_python_version"]:
        mismatches.append(
            f"matrix_python_version mismatch: {payload.get('matrix_python_version')!r} != {expected['matrix_python_version']!r}"
        )
    if payload.get("strict_refs_source") != expected["strict_refs_source"]:
        mismatches.append(
            f"strict_refs_source mismatch: {payload.get('strict_refs_source')!r} != {expected['strict_refs_source']!r}"
        )
    if _normalize_lines(payload.get("strict_refs", "")) != _normalize_lines(expected["strict_refs"]):
        mismatches.append("strict_refs mismatch after normalization")
    if str(payload.get("require_send_targets", "")) != expected["require_send_targets"]:
        mismatches.append(
            f"require_send_targets mismatch: {payload.get('require_send_targets')!r} != {expected['require_send_targets']!r}"
        )
    return mismatches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write/validate warning-summary strict-ref policy artifact."
    )
    parser.add_argument("--artifact", required=True, help="Path to policy artifact json.")
    parser.add_argument("--mode", choices=["write", "validate"], default="validate")
    parser.add_argument("--github-event-name", default=None, help="Expected/recorded github event name.")
    parser.add_argument("--github-ref", default=None, help="Expected/recorded github ref.")
    parser.add_argument("--run-id", default=None, help="Expected/recorded run id.")
    parser.add_argument("--job-attempt", default=None, help="Expected/recorded job attempt.")
    parser.add_argument("--matrix-python-version", default=None, help="Expected/recorded matrix python version.")
    parser.add_argument("--strict-refs-source", default=None, help="Expected/recorded strict refs source.")
    parser.add_argument("--strict-refs", default=None, help="Expected/recorded strict refs list as multiline string.")
    parser.add_argument("--require-send-targets", default=None, help="Expected/recorded require-send-targets value.")

    args = parser.parse_args(argv)
    expected = {
        "github_event_name": _resolve_env(args.github_event_name, "GITHUB_EVENT_NAME"),
        "github_ref": _resolve_env(args.github_ref, "GITHUB_REF"),
        "run_id": _resolve_env(args.run_id, "GITHUB_RUN_ID"),
        "job_attempt": _resolve_env(args.job_attempt, "GITHUB_RUN_ATTEMPT"),
        "matrix_python_version": _resolve_env(
            args.matrix_python_version,
            "MATRIX_PYTHON_VERSION",
        ),
        "strict_refs_source": _resolve_env(args.strict_refs_source, "STRICT_REFS_SOURCE"),
        "strict_refs": _resolve_env(args.strict_refs, "STRICT_REFS"),
        "require_send_targets": _resolve_env(args.require_send_targets, "REQUIRE_SEND_TARGETS"),
    }

    artifact_path = Path(args.artifact)
    if args.mode == "write":
        payload = {
            "github_event_name": expected["github_event_name"],
            "github_ref": expected["github_ref"],
            "run_id": str(expected["run_id"]),
            "job_attempt": str(expected["job_attempt"]),
            "matrix_python_version": expected["matrix_python_version"],
            "strict_refs_source": expected["strict_refs_source"],
            "strict_refs": expected["strict_refs"],
            "require_send_targets": expected["require_send_targets"],
        }
        _write_artifact(artifact_path, payload)
        print(f"wrote strict-ref policy artifact: {artifact_path}")
        return 0

    payload = _load_artifact(artifact_path)
    mismatches = _validate(payload, expected)
    if mismatches:
        print("policy artifact consistency check failed:")
        for issue in mismatches:
            print("-", issue)
        return 1

    strict_refs_lines = _normalize_lines(payload.get("strict_refs", ""))
    line_count = len(strict_refs_lines.splitlines()) if strict_refs_lines else 0
    print(
        f"policy artifact consistent: source={payload.get('strict_refs_source')}, "
        f"require_send_targets={payload.get('require_send_targets')}, "
        f"strict_refs_lines={line_count}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
