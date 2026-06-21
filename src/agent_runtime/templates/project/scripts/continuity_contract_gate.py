"""Validate live-work continuity and self-improvement documentation contracts."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT_DOCS = (
    "README.md",
)

# Each entry lists candidate locations for one logical protocol doc, in priority
# order: the consumer-project root first, then the Agent Runtime source-repo
# template path. A doc counts as present if it exists in ANY candidate location,
# so the gate passes both in the source repo (template paths exist) and in a
# generated consumer project (root docs exist, the template tree is absent).
PROTOCOL_DOCS = (
    ("AGENTS.md", "src/agent_runtime/templates/project/AGENTS.md"),
    ("CLAUDE.md", "src/agent_runtime/templates/project/CLAUDE.md"),
)

POINTER_PATHS = (
    "agents/project/NEXT-SESSION-POINTER.yml",
    "src/agent_runtime/templates/project/agents/project/NEXT-SESSION-POINTER.yml",
)

REQUIRED_POINTER_FIELDS = (
    "schema:",
    "updated_at:",
    "current_state:",
    "active_work:",
    "resume:",
    "roles:",
    "pointers:",
    "rules:",
    "verification:",
    "task_set_id:",
    "step_index:",
    "step_total:",
    "status_text:",
)


@dataclass(frozen=True)
class ContinuityFinding:
    path: str
    kind: str
    detail: str


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def _has(pattern: str, text: str) -> bool:
    return re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None


def _check_readme(root: Path, findings: list[ContinuityFinding]) -> None:
    readme = _read(root / "README.md")
    if not readme:
        findings.append(ContinuityFinding("README.md", "continuity:readme-missing", "README.md is required"))
        return

    if not _has(r"^##\s+(한국어|Korean)\b", readme):
        findings.append(
            ContinuityFinding(
                "README.md",
                "continuity:readme-korean-section-missing",
                "README must expose a Korean entry section",
            )
        )
    if not _has(r"^##\s+English\b", readme):
        findings.append(
            ContinuityFinding(
                "README.md",
                "continuity:readme-english-section-missing",
                "README must expose an English entry section",
            )
        )

    required_tokens = (
        "AGENTS.md",
        "CLAUDE.md",
        "NEXT-SESSION-POINTER.yml",
        "agents/project/",
    )
    for token in required_tokens:
        if token not in readme:
            findings.append(
                ContinuityFinding(
                    "README.md",
                    f"continuity:readme-pointer-token-missing:{token}",
                    f"README must point developers and agents to {token}",
                )
            )


def _check_pointer(root: Path, findings: list[ContinuityFinding]) -> None:
    existing = [rel for rel in POINTER_PATHS if (root / rel).exists()]
    if not existing:
        findings.append(
            ContinuityFinding(
                "agents/project/NEXT-SESSION-POINTER.yml",
                "continuity:pointer-missing",
                "at least one live-work pointer must exist",
            )
        )
        return

    for rel in existing:
        text = _read(root / rel)
        for field in REQUIRED_POINTER_FIELDS:
            if field not in text:
                findings.append(
                    ContinuityFinding(
                        rel,
                        f"continuity:pointer-field-missing:{field.rstrip(':')}",
                        f"pointer file must include {field}",
                    )
                )
        if "agent-runtime-next-session-pointer/v1" not in text:
            findings.append(
                ContinuityFinding(
                    rel,
                    "continuity:pointer-schema-missing",
                    "pointer file must declare schema agent-runtime-next-session-pointer/v1",
                )
            )


def _check_protocol_docs(root: Path, findings: list[ContinuityFinding]) -> None:
    docs: list[tuple[str, str]] = []
    for candidates in PROTOCOL_DOCS:
        present = [(rel, _read(root / rel)) for rel in candidates if (root / rel).exists()]
        if not any(text for _, text in present):
            findings.append(
                ContinuityFinding(
                    candidates[0],
                    "continuity:protocol-doc-missing",
                    f"protocol doc is required in one of: {', '.join(candidates)}",
                )
            )
            continue
        docs.extend((rel, text) for rel, text in present if text)

    combined = "\n".join(text for _, text in docs)
    if not combined:
        return

    rule_checks = (
        (
            "continuity:pointer-rule-missing",
            r"NEXT-SESSION-POINTER\.yml",
            "protocol docs must require live work pointer maintenance",
        ),
        (
            "continuity:live-work-rule-missing",
            r"(active_work|live\s+work|실시간.*작업|pane_id|progress_pct)",
            "protocol docs must track active agent/team/pane state and progress",
        ),
        (
            "continuity:measured-improvement-rule-missing",
            r"(Evaluate\s*->\s*Propose\s*->\s*Verify\s*->\s*Merge|평가\s*->\s*제안\s*->\s*검증\s*->\s*병합)",
            "protocol docs must define the measured improvement loop",
        ),
        (
            "continuity:repeated-request-api-rule-missing",
            r"(Repeated Request API|반복\s*요청.*API|function/API|함수/API)",
            "protocol docs must promote repeated requests into functions, APIs, scripts, or gates",
        ),
        (
            "continuity:compound-auto-capture-rule-missing",
            r"(Compound.*(automatic|auto|mandatory|forced|자동|강제|필수)|반복.*Compound)",
            "protocol docs must force repeated criticism or mistakes into Compound capture",
        ),
        (
            "continuity:golden-set-rule-missing",
            r"(golden\s*set|goldset|오답|실패\s*사례|edge\s*case)",
            "protocol docs must preserve fixed eval cases, failures, and edge cases",
        ),
        (
            "continuity:owner-merge-rule-missing",
            r"Owner",
            "protocol docs must reserve final criteria and merge authority for Owner",
        ),
    )

    for kind, pattern, detail in rule_checks:
        if not _has(pattern, combined):
            findings.append(ContinuityFinding("AGENTS.md/CLAUDE.md", kind, detail))


def analyze(root: Path) -> list[ContinuityFinding]:
    findings: list[ContinuityFinding] = []
    root = root.resolve()
    _check_readme(root, findings)
    _check_pointer(root, findings)
    _check_protocol_docs(root, findings)
    return findings


def render(root: Path, findings: list[ContinuityFinding]) -> str:
    status = "pass" if not findings else "fail"
    lines = [
        f"continuity-contract-gate: {status}",
        f"root={root.resolve()}",
        f"findings={len(findings)}",
    ]
    for finding in findings:
        lines.append(f"- {finding.kind} {finding.path}: {finding.detail}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate session continuity and self-improvement contracts")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Fail when findings exist")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    findings = analyze(args.root)
    print(render(args.root, findings))
    if args.check and findings:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
