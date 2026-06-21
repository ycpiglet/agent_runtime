"""Validate Agent Runtime state-machine SSoT files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REQUIRED_MACHINES = {
    "health_signal",
    "cycle",
    "task",
    "task_claim",
    "agent_job",
    "gate",
    "review",
    "release",
    "owner_decision",
    "hook_enforcement",
    "ci",
    "document",
}


def check_path(path: Path) -> list[str]:
    if not path.exists():
        return ["file:missing"]
    text = path.read_text(encoding="utf-8")
    findings: list[str] = []
    if path.suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            findings.append(f"json:invalid:{exc.msg}")
        return findings

    ids = set(re.findall(r"^\s*-\s*id:\s*([A-Za-z0-9_-]+)\s*$", text, flags=re.MULTILINE))
    for machine_id in sorted(REQUIRED_MACHINES - ids):
        findings.append(f"machine:missing:{machine_id}")
    for label in ("pass", "watch", "block"):
        if not re.search(rf"\b{label}\b", text):
            findings.append(f"signal:missing:{label}")
    if re.search(r"\b(Green|Yellow|Red)\b", text):
        findings.append("signal:color-label-found")
    if "transitions:" not in text:
        findings.append("transitions:missing")
    if "score:" not in text:
        findings.append("score:missing")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="State machine SSoT gate")
    parser.add_argument(
        "--path",
        action="append",
        type=Path,
        default=[],
        help="State-machine or schema path to validate",
    )
    parser.add_argument(
        "--optional-path",
        action="append",
        type=Path,
        default=[],
        help=(
            "Path to validate only if it exists; a missing optional path is skipped, "
            "not a finding. Lets one chain reference paths that exist in the Agent "
            "Runtime source repo but not in generated consumer projects."
        ),
    )
    args = parser.parse_args()
    required = args.path or [Path("agents/project/STATE-MACHINES.yml")]
    optional = [path for path in args.optional_path if path.exists()]
    paths = [*required, *optional]
    total = 0
    for path in paths:
        findings = check_path(path)
        if findings:
            total += len(findings)
            print(f"{path}: fail: {', '.join(findings)}")
        else:
            print(f"{path}: pass")
    print(f"findings={total}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
