"""Lint acceptance criteria for measurable-requirement hygiene (TASK-AR-629).

Axis-3 seed: measurable verification presupposes that the acceptance criteria are
themselves written in measurable language. This gate flags vague vocabulary and
open-ended escape clauses in the `acceptance` frontmatter of worker-ready units so
they can be tightened (ideally via the /clarify interview) before dispatch.

It is ADVISORY by default (`--check` reports findings but exits 0) so it never
retro-breaks the existing backlog; `--strict` returns non-zero on findings for
future enforcement once the backlog is clean. Non-mutating.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import backlog_board

UNITS_DIR = Path("agents/lead_engineer/tasks/units")
# Statuses whose acceptance is still actionable (completed/done are frozen).
ACTIVE_STATUSES = {"worker_ready", "ready", "planned", "pending", "in_progress"}

# Vague vocabulary: adjectives/adverbs with no measurable threshold. Word-boundary
# matched (English) or substring (Korean particles attach, so substring is right).
_VAGUE_EN = (
    "as needed", "as appropriate", "as necessary", "if needed", "if appropriate",
    "appropriately", "properly", "quickly", "fast enough", "reasonable", "reasonably",
    "and so on", "etc.", "various", "some sort of", "tbd", "to be determined",
)
_VAGUE_KO = ("빠르게", "적절히", "적절하게", "알아서", "대충", "필요시", "필요에 따라", "가능하면", "등등", "잘 ")
_VAGUE_EN_RE = re.compile("|".join(re.escape(w) for w in _VAGUE_EN), re.IGNORECASE)


def check_text(text: str) -> list[str]:
    """Return vague-vocabulary findings for a single acceptance criterion."""
    findings: list[str] = []
    value = str(text or "")
    for match in _VAGUE_EN_RE.findall(value):
        findings.append(f"vague-term:{match.strip().lower()}")
    for term in _VAGUE_KO:
        if term in value:
            findings.append(f"vague-term:{term.strip()}")
    return findings


def _iter_unit_acceptance(root: Path):
    base = root / UNITS_DIR
    if not base.exists():
        return
    for path in sorted(base.glob("TASK-*/UNIT-*.md")):
        try:
            meta, _ = backlog_board.parse_frontmatter(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        status = str(meta.get("status") or "").strip().lower()
        if status and status not in ACTIVE_STATUSES:
            continue
        acceptance = meta.get("acceptance")
        items = acceptance if isinstance(acceptance, list) else [acceptance]
        for item in items:
            if item:
                yield path, str(item)


def check_root(root: Path) -> list[str]:
    findings: list[str] = []
    for path, criterion in _iter_unit_acceptance(root):
        rel = path.resolve().relative_to(root.resolve()).as_posix()
        for finding in check_text(criterion):
            findings.append(f"{rel}: requirements-lint:{finding}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Acceptance-criteria requirements lint (advisory)")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    parser.add_argument("--check", action="store_true", help="Scan and report (advisory: exit 0 unless --strict)")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when findings exist (future enforcement)")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = check_root(root)
    status = "watch" if findings else "pass"
    print(f"requirements-lint-gate: {status}")
    print(f"root={root}")
    print(f"findings={len(findings)}")
    for finding in findings:
        print(f"- {finding}")
    return 1 if (args.strict and findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
