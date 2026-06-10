"""Validate the live response/reporting contract.

This gate checks normative reporting-format documents, not historical archives.
It prevents stale color status contracts from re-entering Owner-facing output
rules and makes the pre-answer language/BRIEF checklist explicit.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


NORMATIVE_COLOR_STATUS_PATHS = (
    "src/agent_runtime/templates/project/AGENTS.md",
    "src/agent_runtime/templates/project/docs/agent_bootstrap/scheduled_prompts.md",
    "agents/lead_engineer/REPORTING-FORMAT.md",
    "src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md",
)

REQUIRED_RESPONSE_CONTRACT_PATHS = (
    "agents/lead_engineer/REPORTING-FORMAT.md",
    "src/agent_runtime/templates/project/agents/lead_engineer/REPORTING-FORMAT.md",
)

COLOR_STATUS_PATTERNS = (
    re.compile(r"status:\s*G\|Y\|R", re.IGNORECASE),
    re.compile(r"\bG/Y/R(?:/B)?\b", re.IGNORECASE),
    re.compile(r"\|\s*`?[GYRB]`?\s*\|\s*(Green|Yellow|Red|Blue)\b", re.IGNORECASE),
    re.compile(r"\bUse\s+`G`,\s*`Y`,\s*and\s*`R`\b", re.IGNORECASE),
)

REQUIRED_PATTERNS = {
    "pre-answer-check": re.compile(r"대화\s*응답\s*전\s*자체\s*점검"),
    "user-language": re.compile(r"사용자\s*언어"),
    "owner-default-korean": re.compile(
        r"(사용자|Owner|CEO).{0,40}(직접\s*)?대화.{0,40}(무조건|기본).{0,20}한국어|"
        r"한국어.{0,40}(기본값|기본|무조건)",
        re.IGNORECASE | re.DOTALL,
    ),
    "brief-order": re.compile(r"Bottom Line\s*[-/>]+\s*Signal\s*[-/>]+\s*Insight\s*[-/>]+\s*Decision", re.IGNORECASE),
    "status-signal": re.compile(r"pass.*watch.*block|pass/watch/block", re.IGNORECASE | re.DOTALL),
    "score": re.compile(r"score\s*:\s*0-100|score`\s*:\s*`?0-100|0-100"),
}


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def check_text(text: str, *, require_response_contract: bool) -> list[str]:
    findings: list[str] = []
    for pattern in COLOR_STATUS_PATTERNS:
        if pattern.search(text):
            findings.append("response-contract:color-status-contract")
            break
    if not require_response_contract:
        return findings
    for name, pattern in REQUIRED_PATTERNS.items():
        if not pattern.search(text):
            findings.append(f"response-contract:{name}-missing")
    return findings


def check_root(root: Path) -> list[str]:
    findings: list[str] = []
    candidates = [root / rel for rel in NORMATIVE_COLOR_STATUS_PATHS]
    existing = [path for path in candidates if path.exists()]
    if not existing:
        findings.append("response-contract:normative-doc-missing")
        return findings
    required_paths = {(root / rel).resolve() for rel in REQUIRED_RESPONSE_CONTRACT_PATHS}
    for path in existing:
        rel = _rel(root, path)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(f"{rel}: response-contract:read-error: {exc}")
            continue
        for finding in check_text(text, require_response_contract=path.resolve() in required_paths):
            findings.append(f"{rel}: {finding}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Response/BRIEF contract gate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository or host root")
    parser.add_argument("--check", action="store_true", help="Return non-zero when findings exist")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = check_root(root)
    status = "fail" if findings else "pass"
    print(f"response-contract-gate: {status}")
    print(f"root={root}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if args.check and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
