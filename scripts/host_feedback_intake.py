"""Host feedback intake + triage queue (TASK-AR-526).

Treat host (autofolio) dogfooding feedback as first-class, non-ignorable input:
classify each item into one of four categories and hold it in a triage queue
until the council/seminar deliberation (TASK-AR-527) accepts/defers/rejects it
and the decision is replied back to the issue (TASK-AR-528).

This module is the canonical, re-runnable surface:
  --check   validate the queue (schema, unique ids, valid category/status,
            source + title present); exit non-zero on any finding.
  --write   render the Owner-facing HOST-FEEDBACK-QUEUE.md view.

The queue is data (HOST-FEEDBACK-QUEUE.json); re-running is idempotent and never
duplicates an entry (ids are the dedup key).
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUEUE_JSON = ROOT / "agents" / "project" / "work-items" / "HOST-FEEDBACK-QUEUE.json"
QUEUE_MD = ROOT / "agents" / "project" / "work-items" / "HOST-FEEDBACK-QUEUE.md"
SCHEMA = "agent-runtime-host-feedback-queue/v1"


def load_queue(path: Path = QUEUE_JSON) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_queue(queue: dict) -> list[str]:
    """Return a list of findings; empty means valid."""
    findings: list[str] = []
    if str(queue.get("schema") or "") != SCHEMA:
        findings.append(f"schema:expected-{SCHEMA}")
    categories = set(queue.get("categories") or [])
    statuses = set(queue.get("statuses") or [])
    if not categories:
        findings.append("categories:empty")
    if not statuses:
        findings.append("statuses:empty")
    seen_ids: set[str] = set()
    for index, entry in enumerate(queue.get("entries") or []):
        eid = str(entry.get("id") or "").strip()
        if not eid:
            findings.append(f"entry:{index}:missing-id")
            continue
        if eid in seen_ids:
            findings.append(f"entry:{eid}:duplicate-id")
        seen_ids.add(eid)
        if not str(entry.get("source") or "").strip():
            findings.append(f"entry:{eid}:missing-source")
        if not str(entry.get("title") or "").strip():
            findings.append(f"entry:{eid}:missing-title")
        if str(entry.get("category") or "") not in categories:
            findings.append(f"entry:{eid}:invalid-category:{entry.get('category')}")
        if str(entry.get("status") or "") not in statuses:
            findings.append(f"entry:{eid}:invalid-status:{entry.get('status')}")
    return findings


def render_md(queue: dict) -> str:
    today = date.today().isoformat()
    entries = list(queue.get("entries") or [])
    by_status: dict[str, int] = {}
    for entry in entries:
        by_status[str(entry.get("status"))] = by_status.get(str(entry.get("status")), 0) + 1
    summary = ", ".join(f"{status} `{count}`" for status, count in sorted(by_status.items())) or "none"
    lines = [
        "---",
        "type: host_feedback_queue",
        "id: HOST-FEEDBACK-QUEUE-agent-runtime",
        "audience: owner",
        "status: pass",
        "signal: pass",
        "score: 90",
        "priority: High",
        "tags: [host-feedback, intake, triage, dogfooding, generated-index]",
        f"generated_at: {today}",
        f"entry_count: {len(entries)}",
        "---",
        "",
        "# Host Feedback Intake Queue",
        "",
        "## Bottom Line",
        f"- Summary: `{len(entries)}` host (autofolio) feedback items in the intake queue ({summary}).",
        "- Rule: host feedback is first-class input. Items sit in `triage` until the TASK-AR-527 deliberation accepts/defers/rejects them and TASK-AR-528 replies back to the issue.",
        "",
        "## Signal",
        "| Item | Category | Status | Source | Tasks | Title |",
        "|---|---|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{entry.get('id')}`",
                    str(entry.get("category")),
                    str(entry.get("status")),
                    str(entry.get("source")),
                    ", ".join(entry.get("tasks") or []) or "-",
                    str(entry.get("title")).replace("|", "/"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "- Decision: route every host feedback item through this queue; never let it rot as an unconsumed issue.",
            "- Guardrails: deliberation informs but does not override the Owner on product direction; safety/order boundary is always a human (R3); votes are a priority signal, not a direction decider.",
            "",
            "## Next",
            "- Run the TASK-AR-527 council/seminar deliberation on `triage` items; record verdicts and reply back (TASK-AR-528).",
            "- Re-run `python scripts/host_feedback_intake.py --write` after queue changes.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Host feedback intake + triage queue")
    parser.add_argument("--check", action="store_true", help="validate the queue and exit non-zero on findings")
    parser.add_argument("--write", action="store_true", help="render HOST-FEEDBACK-QUEUE.md")
    args = parser.parse_args()

    queue = load_queue()
    findings = check_queue(queue)
    if args.check:
        if findings:
            for finding in findings:
                print(f"host-feedback-intake: fail: {finding}")
            print(f"findings={len(findings)}")
            return 1
        print("host-feedback-intake: pass")
        print("findings=0")
        return 0
    if args.write:
        if findings:
            for finding in findings:
                print(f"host-feedback-intake: fail: {finding}")
            return 1
        QUEUE_MD.write_text(render_md(queue), encoding="utf-8")
        print(f"wrote={QUEUE_MD}")
        print(f"entries={len(queue.get('entries') or [])}")
        return 0
    print(render_md(queue))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
