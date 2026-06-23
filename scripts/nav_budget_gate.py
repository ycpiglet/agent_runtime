"""Nav-budget gate for the decision-first console IA (RFC-2026-06-23, P2).

The console's core navigation is *frozen to a budget*: at most 7 top-level items
(core links + the single grouped ``More`` disclosure). This is a discipline, not
a snapshot -- adding an 8th core link must require demoting another to ``More``.
This gate parses the rendered console shell and fails the build if the core nav
ever regrows past the budget. Read-only, stdlib-only.

Spec: reviews/RFC-2026-06-23-decision-first-console-IA.md (Tier 1 -- core nav).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# RFC Tier 1: "Home, Work, Agents, Decisions, Records, Search (current 6) + at
# most one more." Counting the grouped More disclosure, the top-level budget is 7.
NAV_BUDGET = 7

_CORE_RE = re.compile(r'<div class="sidebar-core"[^>]*>(.*?)</div>\s*<details', re.S)
_CORE_LINK_RE = re.compile(r'<button class="sidebar-link[^"]*"[^>]*data-view="[^"]+"')


def _console_html() -> str:
    from agent_runtime import ui_console_assets

    return ui_console_assets.HTML


def count_core_nav(html: str) -> int:
    """Top-level nav item count = core links + the single ``More`` disclosure."""
    core = _CORE_RE.search(html)
    if not core:
        raise ValueError("core navigation wrapper (.sidebar-core) not found in console HTML")
    core_links = _CORE_LINK_RE.findall(core.group(1))
    has_more = 'class="sidebar-more-summary"' in html
    return len(core_links) + (1 if has_more else 0)


def evaluate(*, top_level: int) -> dict:
    """Pure budget verdict for a given top-level count (testable without HTML)."""
    status = "pass" if top_level <= NAV_BUDGET else "fail"
    findings = []
    if status == "fail":
        findings.append(
            f"core nav budget exceeded: {top_level} top-level items > {NAV_BUDGET}; "
            "demote a core link to More before adding another"
        )
    return {"status": status, "top_level": top_level, "budget": NAV_BUDGET, "findings": findings}


def check() -> dict:
    return evaluate(top_level=count_core_nav(_console_html()))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Console core-nav budget gate (<=7 top-level).")
    ap.add_argument("--json", action="store_true", help="emit the verdict as JSON")
    args = ap.parse_args(argv)
    result = check()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"nav-budget-gate: {result['status']} top_level={result['top_level']} budget={result['budget']}")
        for finding in result["findings"]:
            print(f"  - {finding}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
