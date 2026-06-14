"""Host feedback decision reply-back + traceability (TASK-AR-528).

Closes the intake pipeline loop (GH #131): after the council deliberation
(TASK-AR-527) records a verdict per host-feedback item in HOST-FEEDBACK-QUEUE.json,
this posts the decision + rationale BACK to the originating GitHub issue so the
host (autofolio) can track adoption. Reply is bidirectionally traceable:
issue <-> queue entry <-> deliberation record <-> task.

  --write-drafts   render the per-issue replies to HOST-FEEDBACK-REPLIES.md (local)
  --post           post each reply as a `gh issue comment` (EXTERNAL; owner-gated)
  --check          validate every accepted/deferred/rejected entry has a verdict

The actual posting is an outward action; run --write-drafts first to review.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "agents" / "project" / "work-items" / "HOST-FEEDBACK-QUEUE.json"
DRAFTS = ROOT / "agents" / "project" / "work-items" / "HOST-FEEDBACK-REPLIES.md"
REPO = "ycpiglet/agent_runtime"
DELIBERATION = "reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md"
# Hidden marker so re-running --post is idempotent (skip issues already replied).
REPLY_MARKER = "<!-- ar528-replyback -->"


def _issue_number(source: str) -> str | None:
    if "#" in source:
        return source.rsplit("#", 1)[1].strip()
    return None


def build_replies(queue: dict) -> list[dict]:
    """One reply per source issue (entries are 1:1 with issues here)."""
    by_issue: dict[str, list[dict]] = defaultdict(list)
    for entry in queue.get("entries", []):
        number = _issue_number(str(entry.get("source") or ""))
        if number:
            by_issue[number].append(entry)
    replies: list[dict] = []
    for number, entries in sorted(by_issue.items(), key=lambda kv: int(kv[0])):
        lines = ["**agent_runtime — host-feedback intake decision**", ""]
        lines.append(
            "This feedback was run through the host-feedback intake pipeline "
            f"(GH #131): triaged, deliberated by a blind-Delphi diversity council, "
            f"and a verdict recorded. Deliberation record: `{DELIBERATION}`."
        )
        lines.append("")
        for entry in entries:
            status = str(entry.get("status") or "").upper()
            priority = entry.get("priority") or "-"
            tasks = ", ".join(entry.get("tasks") or []) or "-"
            lines.append(f"- **Decision: {status}** (priority {priority}) — tracked as {tasks}.")
            lines.append(f"  - {entry.get('verdict') or '(no rationale recorded)'}")
        lines.append("")
        lines.append(
            "Guardrails: this is a recommendation + priority signal; product "
            "direction stays with the Owner, safety/order with a human (R3)."
        )
        lines.append("")
        lines.append(REPLY_MARKER)
        replies.append({"issue": number, "body": "\n".join(lines)})
    return replies


def check_queue(queue: dict) -> list[str]:
    findings: list[str] = []
    for entry in queue.get("entries", []):
        eid = entry.get("id")
        if str(entry.get("status")) in {"accepted", "deferred", "rejected"} and not str(entry.get("verdict") or "").strip():
            findings.append(f"{eid}:decided-without-verdict")
        if not _issue_number(str(entry.get("source") or "")):
            findings.append(f"{eid}:no-issue-number")
    return findings


def render_drafts(replies: list[dict]) -> str:
    out = ["---", "type: host_feedback_replies", "id: HOST-FEEDBACK-REPLIES", "audience: owner", "---", "", "# Host Feedback Reply-Back Drafts (TASK-AR-528)", ""]
    for reply in replies:
        out.append(f"## GH #{reply['issue']}")
        out.append("")
        out.append(reply["body"])
        out.append("")
    return "\n".join(out)


def _already_replied(issue: str) -> bool:
    """True if an ar528 reply marker is already present on the issue (idempotency)."""
    result = subprocess.run(
        ["gh", "issue", "view", issue, "--repo", REPO, "--json", "comments"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    try:
        comments = json.loads(result.stdout).get("comments", [])
    except json.JSONDecodeError:
        return False
    return any(REPLY_MARKER in str(comment.get("body") or "") for comment in comments)


def post_reply(issue: str, body: str) -> tuple[bool, str]:
    result = subprocess.run(
        ["gh", "issue", "comment", issue, "--repo", REPO, "--body", body],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, (result.stdout or result.stderr).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Host feedback decision reply-back (TASK-AR-528)")
    parser.add_argument("--write-drafts", action="store_true")
    parser.add_argument("--post", action="store_true", help="EXTERNAL: post replies to GitHub (owner-gated)")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    findings = check_queue(queue)
    if args.check:
        for finding in findings:
            print(f"host-feedback-replyback: fail: {finding}")
        print(f"findings={len(findings)}")
        return 1 if findings else 0

    replies = build_replies(queue)
    if args.write_drafts:
        DRAFTS.write_text(render_drafts(replies), encoding="utf-8")
        print(f"wrote={DRAFTS}")
        print(f"replies={len(replies)}")
        return 0
    if args.post:
        if findings:
            print(f"host-feedback-replyback: refusing to post; {len(findings)} findings")
            return 1
        for reply in replies:
            if _already_replied(reply["issue"]):
                print(f"#{reply['issue']}: skipped (already replied; idempotent)")
                continue
            ok, detail = post_reply(reply["issue"], reply["body"])
            print(f"#{reply['issue']}: {'posted ' + detail if ok else 'FAILED ' + detail}")
        return 0
    print(render_drafts(replies))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
