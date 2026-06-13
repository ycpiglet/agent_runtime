"""Meeting Room planner: validate a meeting config and record a MEETING skeleton.

The UI "Meeting Room" (TASK-AR-361) lets an owner drag agent cards into a room,
pick a topic/task, choose a meeting type, and set the number of rounds. The
"start" affordance does NOT mutate ``reviews/`` directly from the console; it
emits a proposal-only command that runs this script's ``plan`` subcommand.

``plan`` is deterministic and proposal-only:

- It validates the config (>=2 participants, rounds>0, known meeting type).
- It writes a ``reviews/MEETING-<date>-<topic-slug>.md`` skeleton with YAML
  frontmatter (``type: meeting`` + participants + agenda) and round headings.
- It NEVER fabricates live multi-agent dialogue; the body is an empty agenda
  shell for the meeting to fill in. Live agent dialogue is a follow-up.

Output is ASCII-safe on the human path and ``ensure_ascii`` on the JSON path so
it stays cp949/Windows-console safe.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "agent-runtime-meeting-plan/v1"
MEETING_TYPES = ("meeting", "seminar", "review")
DEFAULT_ROUNDS = 3
MAX_ROUNDS = 20
REVIEWS_DIRNAME = "reviews"


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _today(now: str | None = None) -> str:
    if now:
        match = re.match(r"(\d{4}-\d{2}-\d{2})", now)
        if match:
            return match.group(1)
    return datetime.now().strftime("%Y-%m-%d")


def _ascii(value: Any) -> str:
    return str(value if value is not None else "").encode("ascii", "replace").decode("ascii")


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return slug or "topic"


def _clean_participant(value: Any) -> str:
    return str(value if value is not None else "").strip()


def normalize_participants(participants: Any) -> list[str]:
    """Dedupe (case-insensitive, first wins) and drop blanks, preserving order."""
    if isinstance(participants, str):
        candidates = [part for part in re.split(r"[,\n]", participants)]
    elif isinstance(participants, (list, tuple)):
        candidates = list(participants)
    else:
        candidates = []
    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        name = _clean_participant(candidate)
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(name)
    return result


def validate_config(
    *,
    topic: str,
    participants: list[str],
    meeting_type: str,
    rounds: int,
) -> list[str]:
    errors: list[str] = []
    if not str(topic or "").strip():
        errors.append("topic is required")
    if meeting_type not in MEETING_TYPES:
        errors.append(f"invalid meeting type: {meeting_type!r} (expected one of {', '.join(MEETING_TYPES)})")
    if len(participants) < 2:
        errors.append("at least 2 participants are required")
    try:
        rounds_int = int(rounds)
    except (TypeError, ValueError):
        errors.append("rounds must be an integer")
        rounds_int = 0
    if rounds_int <= 0:
        errors.append("rounds must be > 0")
    elif rounds_int > MAX_ROUNDS:
        errors.append(f"rounds must be <= {MAX_ROUNDS}")
    return errors


def _frontmatter_list(key: str, values: list[str]) -> list[str]:
    lines = [f"{key}:"]
    for value in values:
        lines.append(f"  - {value}")
    return lines


def render_skeleton(
    *,
    meeting_id: str,
    topic: str,
    participants: list[str],
    meeting_type: str,
    rounds: int,
    task_id: str | None,
    generated_at: str,
) -> str:
    """Render the MEETING markdown skeleton (frontmatter + agenda shell)."""
    tags = ["meeting-room", meeting_type, "agenda-skeleton"]
    if task_id:
        tags.append(slugify(task_id))
    frontmatter: list[str] = ["---", "type: meeting", f"id: {meeting_id}", "audience: owner", "status: planned", "signal: planned"]
    if task_id:
        frontmatter.append(f"task_id: {task_id}")
    frontmatter.append(f"meeting_type: {meeting_type}")
    frontmatter.append(f"rounds: {rounds}")
    frontmatter.append(f"generated_at: {generated_at}")
    frontmatter.extend(_frontmatter_list("participants", participants))
    frontmatter.append("tags: [" + ", ".join(tags) + "]")
    frontmatter.append("---")

    body: list[str] = [
        "",
        f"# {topic}",
        "",
        "## Bottom Line",
        "",
        "- Summary: meeting plan recorded; conclusion pending execution.",
        f"- Type: {meeting_type} | Rounds: {rounds}" + (f" | Task: {task_id}" if task_id else ""),
        "- Boundary: this is a proposal-only skeleton. Live multi-agent dialogue"
        " is recorded by the meeting executor (follow-up), not by the console.",
        "",
        "## Participants",
        "",
    ]
    for participant in participants:
        body.append(f"- {participant}")
    body.extend(["", "## Agenda", ""])
    for index in range(1, int(rounds) + 1):
        body.append(f"### Round {index}")
        body.append("")
        body.append("- _pending_")
        body.append("")
    body.extend(["## Decision", "", "- _pending_", ""])
    return "\n".join(frontmatter + body)


def meeting_id_for(topic: str, today: str) -> str:
    return f"MEETING-{today}-{slugify(topic)}"


def plan(
    root: Path,
    *,
    topic: str,
    participants: Any,
    meeting_type: str = "meeting",
    rounds: int = DEFAULT_ROUNDS,
    task_id: str | None = None,
    now: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Validate config and write a MEETING skeleton under ``reviews/``."""
    generated_at = now or _now_iso()
    today = _today(generated_at)
    normalized = normalize_participants(participants)
    errors = validate_config(
        topic=topic,
        participants=normalized,
        meeting_type=meeting_type,
        rounds=rounds,
    )
    if errors:
        return {
            "schema": SCHEMA,
            "status": "failed",
            "generated_at": generated_at,
            "errors": errors,
        }

    rounds_int = int(rounds)
    meeting_id = meeting_id_for(topic, today)
    reviews_dir = Path(root) / REVIEWS_DIRNAME
    reviews_dir.mkdir(parents=True, exist_ok=True)
    target = reviews_dir / f"{meeting_id}.md"
    if target.exists() and not overwrite:
        return {
            "schema": SCHEMA,
            "status": "failed",
            "generated_at": generated_at,
            "errors": [f"meeting record already exists: {target.name} (pass overwrite to replace)"],
        }

    content = render_skeleton(
        meeting_id=meeting_id,
        topic=str(topic).strip(),
        participants=normalized,
        meeting_type=meeting_type,
        rounds=rounds_int,
        task_id=task_id,
        generated_at=generated_at,
    )
    target.write_text(content, encoding="utf-8")
    try:
        rel = target.resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        rel = target.as_posix()
    return {
        "schema": SCHEMA,
        "status": "recorded",
        "generated_at": generated_at,
        "meeting_id": meeting_id,
        "meeting_type": meeting_type,
        "topic": str(topic).strip(),
        "task_id": task_id,
        "rounds": rounds_int,
        "participants": normalized,
        "path": rel,
        "errors": [],
    }


def _emit(result: dict[str, Any], *, json_output: bool) -> int:
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get("status") == "recorded":
        print(_ascii(f"recorded {result['meeting_id']} -> {result['path']}"))
        print(_ascii(f"  type={result['meeting_type']} rounds={result['rounds']} participants={len(result['participants'])}"))
    else:
        print(_ascii(f"meeting plan failed ({result.get('status')})"))
        for error in result.get("errors", []):
            print(_ascii(f"  - {error}"))
    return 0 if result.get("status") == "recorded" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Meeting Room planner")
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan", help="validate a meeting config and write a MEETING skeleton")
    plan_parser.add_argument("--root", default=".", help="repository root (default: cwd)")
    plan_parser.add_argument("--topic", required=True, help="meeting topic / title")
    plan_parser.add_argument(
        "--participant",
        action="append",
        default=[],
        dest="participants",
        help="participant agent role/name (repeatable; >=2 required)",
    )
    plan_parser.add_argument("--participants", dest="participants_csv", help="comma-separated participants")
    plan_parser.add_argument("--type", dest="meeting_type", default="meeting", choices=MEETING_TYPES)
    plan_parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    plan_parser.add_argument("--task-id", dest="task_id", default=None)
    plan_parser.add_argument("--overwrite", action="store_true")
    plan_parser.add_argument("--json", action="store_true", help="emit JSON result")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "plan":
        participants: list[str] = list(args.participants or [])
        if args.participants_csv:
            participants.extend(part for part in args.participants_csv.split(","))
        result = plan(
            Path(args.root),
            topic=args.topic,
            participants=participants,
            meeting_type=args.meeting_type,
            rounds=args.rounds,
            task_id=args.task_id,
            overwrite=args.overwrite,
        )
        return _emit(result, json_output=args.json)
    return 1


if __name__ == "__main__":
    sys.exit(main())
