#!/usr/bin/env python3
"""
Agent orchestrator command router (TASK-082).

User-facing commands:
  /go-to-work               start a work session (lists candidate roles & tasks)
  /leave-for-work           end the work session (snapshots and stops heartbeats)
  /spawn <role> [--task X]  register a new agent in the session registry
  /kill <agent_id>          mark a session stopped, completed, or failed
  /call <role> <message>    write a request message to agents/messages/inbox/
  /qa "..."                 alias for `/call qa ...`
  /lead-engineer "..."      alias for `/call lead-engineer ...`
  /status                   show active sessions, open messages, warnings
  /inbox [--role X]         list open/claimed messages, optionally filtered

Design rules (ORCHESTRATOR-PLAN.md):
  - dry-run by default; real terminal spawning is TASK-085 territory
  - all writes are markdown / JSON files only — no external API calls
  - destructive operations are refused at this layer
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

# TASK-086 safety gate — import local module
sys.path.insert(0, str(Path(__file__).resolve().parent))
import orchestrator_safety_gate as safety_gate  # noqa: E402
import cycle_gate  # noqa: E402
import subagent_dispatch  # noqa: E402

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
MESSAGES_INBOX = REPO_ROOT / "agents" / "messages" / "inbox"
MESSAGES_ARCHIVE = REPO_ROOT / "agents" / "messages" / "archive"
SESSIONS_DIR = REPO_ROOT / "agents" / "runtime" / "sessions"
TASKS_DIR = REPO_ROOT / "agents" / "lead_engineer" / "tasks"
DEFAULT_WORKER_PROVIDER = "codex-agent"


def emit_allimbot_event(event_type: str, data: dict[str, object]) -> None:
    """Lazy profile helper; clean core does not ship or import allimbot.py."""

    if not (REPO_ROOT / "scripts" / "allimbot.py").is_file():
        return
    try:
        import allimbot

        allimbot.emit_event(event_type, data, root=REPO_ROOT)
    except Exception:
        pass

# TASK-118 — /dispatch-next priority order (Critical first, Low last).
PRIORITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
# Owner field aliases used in TASK frontmatter -> orchestrator role slug.
OWNER_TO_ROLE = {
    "Lead Engineer": "lead-engineer",
    "Backend Engineer": "backend",
    "Backend": "backend",
    "CI/CD Engineer": "ci-cd",
    "CI/CD": "ci-cd",
    "UI/UX Designer": "uiux",
    "UI/UX": "uiux",
    "QA": "qa",
    "Beta Tester": "beta-tester",
    "CEO": "ceo",
    "Managing Partner": "managing-partner",
    "Independent Auditor": "independent-auditor",
    "Doc Steward": "doc-steward",
    "Scribe": "scribe",
    "Research Agent": "research",
    "Timeline Agent": "timeline",
    "Requirements Interviewer": "requirements-interviewer",
}

ROLE_ALIASES = {
    "qa": "qa",
    "lead-engineer": "lead-engineer",
    "lead": "lead-engineer",
    "backend": "backend",
    "ci-cd": "ci-cd",
    "uiux": "uiux",
    "beta": "beta-tester",
    "ceo": "ceo",
    "managing-partner": "managing-partner",
    "independent-auditor": "independent-auditor",
    "doc": "doc-steward",
    "doc-steward": "doc-steward",
    "steward": "doc-steward",
    "scribe": "scribe",
    "archivist": "scribe",
    "research": "research",
    "research-agent": "research",
    "researcher": "research",
    "timeline": "timeline",
    "timeline-agent": "timeline",
    "chronology": "timeline",
    "requirements-interviewer": "requirements-interviewer",
    "interviewer": "requirements-interviewer",
    "grill": "requirements-interviewer",
    "deep-interview": "requirements-interviewer",
    "secretary": "secretary",
    "sec": "secretary",
}
KNOWN_ROLES = sorted(set(ROLE_ALIASES.values()))

TASK_RE = re.compile(r"^TASK-\d{3}$|^none$")
AGENT_ID_RE = re.compile(r"^agent_[0-9a-f]{12}$")


@dataclass
class Outcome:
    code: int
    summary: str
    payload: dict


def ts_now_iso() -> str:
    t = time.localtime()
    offset_minutes = -time.altzone // 60 if t.tm_isdst else -time.timezone // 60
    sign = "+" if offset_minutes >= 0 else "-"
    offset = f"{sign}{abs(offset_minutes)//60:02d}:{abs(offset_minutes)%60:02d}"
    return time.strftime("%Y-%m-%dT%H:%M:%S", t) + offset


def ts_now_compact() -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime())


def normalize_role(raw: str) -> str:
    key = raw.strip().lstrip("/").lower().replace("_", "-")
    if key not in ROLE_ALIASES:
        raise SystemExit(f"unknown role '{raw}'. known: {', '.join(KNOWN_ROLES)}")
    return ROLE_ALIASES[key]


def ensure_dirs() -> None:
    MESSAGES_INBOX.mkdir(parents=True, exist_ok=True)
    MESSAGES_ARCHIVE.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def session_path(agent_id: str) -> Path:
    return SESSIONS_DIR / f"{agent_id}.json"


def write_session_json(path: Path, payload: dict) -> None:
    """Crash-safe session write: temp-then-``os.replace`` (issue #274).

    A direct ``write_text`` interrupted by power loss leaves a half-written,
    unparseable JSON that crashes the next session's orchestrator/claim-reaper.
    ``os.replace`` is atomic on the same filesystem, so readers only ever see
    the old or the new record (pattern proven in message_queue and on the
    autofolio host, forced-shutdown scenario included).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{uuid.uuid4().hex[:8]}")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def read_sessions() -> list[dict]:
    if not SESSIONS_DIR.is_dir():
        return []
    out: list[dict] = []
    for p in sorted(SESSIONS_DIR.iterdir()):
        if p.suffix != ".json" or p.name.startswith("."):
            continue
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def read_inbox() -> list[dict]:
    if not MESSAGES_INBOX.is_dir():
        return []
    out: list[dict] = []
    for p in sorted(MESSAGES_INBOX.iterdir()):
        if p.suffix != ".md" or p.name.startswith("."):
            continue
        meta = parse_frontmatter(p)
        if meta:
            meta["__path"] = _display_path(p)
            out.append(meta)
    return out


def parse_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    meta: dict[str, object] = {}
    current_list_key: str | None = None
    for raw in parts[1].splitlines():
        line = raw.rstrip()
        if not line:
            current_list_key = None
            continue
        if line.startswith("  - ") and current_list_key:
            existing = meta.setdefault(current_list_key, [])
            if isinstance(existing, list):
                existing.append(line[4:].strip())
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            meta[key] = []
            current_list_key = key
        else:
            meta[key] = value
            current_list_key = None
    return meta


# ---------- TASK-118 dispatch-next ----------


def read_task_files() -> list[dict]:
    """Read every agents/lead_engineer/tasks/TASK-*.md frontmatter."""
    if not TASKS_DIR.is_dir():
        return []
    out: list[dict] = []
    for p in sorted(TASKS_DIR.iterdir()):
        if p.suffix != ".md" or not p.name.startswith("TASK-"):
            continue
        meta = parse_frontmatter(p)
        if not meta:
            continue
        try:
            meta["__path"] = str(p.relative_to(REPO_ROOT))
        except ValueError:
            meta["__path"] = str(p)
        out.append(meta)
    return out


def task_meta(task_id: str) -> dict | None:
    for meta in read_task_files():
        if meta.get("id") == task_id:
            return meta
    return None


def task_completion_is_authoritative(task_id: str) -> bool:
    """Return true only after the task record is both closed and verified."""
    meta = task_meta(task_id)
    if not meta:
        return False
    status = str(meta.get("status") or "").strip().lower()
    verification_status = str(meta.get("verification_status") or "").strip().lower()
    return status in {"completed", "done", "closed", "완료"} and verification_status == "passed"


def routing_grade_for_task(task_id: str, fallback: str = "Medium") -> str:
    if task_id == "none":
        return fallback
    meta = task_meta(task_id)
    priority = meta.get("priority") if meta else None
    return str(priority or fallback)


def _est_hours(meta: dict) -> float:
    raw = meta.get("est_hours")
    if raw in (None, "", []):
        return 99.0  # unknowns go last within a priority bucket
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 99.0


def candidate_tasks(tasks: list[dict], role: str | None = None) -> list[dict]:
    """Filter to 대기 status, optionally by Owner role, then sort by priority+est."""
    waiting = [t for t in tasks if t.get("status") == "대기"]
    if role:
        target = normalize_role(role)
        waiting = [t for t in waiting if _owner_role(t) == target]
    waiting.sort(key=lambda t: (
        PRIORITY_ORDER.get(t.get("priority", ""), 99),
        _est_hours(t),
        t.get("id", ""),
    ))
    return waiting


def _owner_role(meta: dict) -> str | None:
    raw = meta.get("owner")
    if not isinstance(raw, str) or not raw:
        return None
    # Try direct lookup, then alias map, then normalize_role for slug-style values.
    if raw in OWNER_TO_ROLE:
        return OWNER_TO_ROLE[raw]
    key = raw.strip().lower().replace("_", "-")
    if key in ROLE_ALIASES:
        return ROLE_ALIASES[key]
    return None


def _task_title_hint(path_str: str) -> str:
    """Strip "TASK-NNN-" prefix and ".md" suffix from filename for an intent hint."""
    name = Path(path_str).stem
    parts = name.split("-", 2)
    return parts[2].replace("-", " ") if len(parts) >= 3 else name


def _dispatch_one(top: dict, dry_run: bool, inbox: list[dict]) -> dict:
    """Build a single dispatch result for a candidate task.

    Returns a result dict with `status` set to one of:
      - "dispatched" (message would be / was written)
      - "owner-unmapped" (owner string did not resolve to a role)
      - "blocked"       (safety_gate denied)

    `inbox` is reused so the caller can grow it between calls to honour
    cumulative caps (per-role open-message cap, rate limit window) across
    a multi-dispatch run.
    """
    task_id = top.get("id", "")
    owner_role = _owner_role(top)
    if not owner_role:
        return {
            "status": "owner-unmapped",
            "candidate": {"id": task_id, "owner": top.get("owner")},
            "reason": "owner could not be mapped to a role slug",
        }
    intent = (
        f"auto-dispatch: pick up {task_id} ({_task_title_hint(top['__path'])}) — "
        f"priority {top.get('priority', 'unknown')}, est {top.get('est_hours', '?')} ph"
    )
    decision = safety_gate.evaluate_call(owner_role, intent, task_id, inbox)
    if not decision.allowed:
        ev = safety_gate.write_evidence(
            decision, "dispatch-next",
            {"role": owner_role, "task": task_id, "intent": intent,
             "dry_run": bool(dry_run)},
        )
        try:
            ev_rel = str(ev.relative_to(REPO_ROOT))
        except ValueError:
            ev_rel = str(ev)
        return {
            "status": "blocked",
            "candidate": {"id": task_id, "owner": top.get("owner"), "role": owner_role},
            "decision": decision.to_dict(),
            "evidence": ev_rel,
        }

    msg_id = f"MSG-{ts_now_compact()}-{uuid.uuid4().hex[:6]}"
    msg_path = MESSAGES_INBOX / f"{msg_id}.md"
    body = (
        f"---\n"
        f"id: {msg_id}\n"
        f"from: orchestrator\n"
        f"to: {owner_role}\n"
        f"task_id: {task_id}\n"
        f"intent: {intent}\n"
        f"type: request\n"
        f"status: open\n"
        f"ts: {ts_now_iso()}\n"
        f"in_reply_to:\n"
        f"evidence:\n"
        f"  - {top['__path']}\n"
        f"next:\n"
        f"  - Read the TASK file linked in evidence and confirm scope.\n"
        f"  - Start worker with provider `{DEFAULT_WORKER_PROVIDER}` "
        f"(example: agent_terminal launch --worker --provider {DEFAULT_WORKER_PROVIDER} "
        f"--model auto --routing-grade {top.get('priority', 'Medium')}).\n"
        f"  - Update status -> 진행 중 and start work.\n"
        f"routing_model: auto\n"
        f"routing_grade: {top.get('priority', 'Medium')}\n"
        f"---\n\n"
        f"`/dispatch-next` 자동 분배 (TASK-118 + TASK-120): {task_id} 가 INDEX "
        f"우선순위 후보로 감지됐다. 본 메시지는 orchestrator 가 생성한 추천 — "
        f"실 작업 착수는 Owner 가 결정 (`/spawn` 또는 직접 진행).\n"
    )
    msg_rel = _display_path(msg_path)
    if not dry_run:
        ensure_dirs()
        msg_path.write_text(body, encoding="utf-8")
    # Keep cumulative caps honest within a multi-dispatch run by mirroring
    # the newly-emitted message in the in-memory inbox view.
    inbox.append({
        "id": msg_id, "to": owner_role, "task_id": task_id,
        "intent": intent, "type": "request", "status": "open",
        "ts": ts_now_iso(),
        "routing_model": "auto",
        "routing_grade": top.get("priority", "Medium"),
    })
    return {
        "status": "dispatched",
        "candidate": {
            "id": task_id, "owner": top.get("owner"), "role": owner_role,
            "priority": top.get("priority"), "est_hours": top.get("est_hours"),
            "path": top["__path"],
        },
        "recommended_provider": DEFAULT_WORKER_PROVIDER,
        "message_id": msg_id,
        "path": msg_rel,
    }


def cmd_dispatch_next(args: argparse.Namespace) -> Outcome:
    tasks = read_task_files()
    candidates = candidate_tasks(tasks, role=args.role)
    if not candidates:
        payload = {
            "dry_run": args.dry_run,
            "candidate": None,
            "reason": f"no 대기 TASK found (role={args.role or 'any'})",
        }
        return Outcome(0, "dispatch-next: no candidate", payload)

    count = max(1, int(getattr(args, "count", 1) or 1))
    if count == 1:
        # Backwards-compatible single-dispatch payload (callers + tests).
        result = _dispatch_one(candidates[0], args.dry_run, read_inbox())
        if result["status"] == "owner-unmapped":
            payload = {
                "dry_run": args.dry_run,
                "candidate": result["candidate"],
                "reason": result["reason"],
            }
            return Outcome(1, f"dispatch-next blocked: unknown owner for "
                           f"{result['candidate'].get('id')}", payload)
        if result["status"] == "blocked":
            print(f"BLOCKED: {result['decision']['code']} — "
                  f"{result['decision']['reason']}", file=sys.stderr)
            print(f"evidence: {result['evidence']}", file=sys.stderr)
            return Outcome(1, f"dispatch-next blocked: {result['decision']['code']}", {
                "dry_run": args.dry_run,
                "candidate": result["candidate"],
                "blocked": True,
                "decision": result["decision"],
                "evidence": result["evidence"],
            })
        top = candidates[0]
        payload = {
            "dry_run": args.dry_run,
            "candidate": result["candidate"],
            "message_id": result["message_id"],
            "path": result["path"],
            "remaining_candidates": len(candidates) - 1,
        }
        summary = (
            f"dispatch-next pick={top.get('id')} role={result['candidate']['role']} "
            f"priority={top.get('priority')} dry_run={args.dry_run}"
        )
        return Outcome(0, summary, payload)

    # TASK-120 multi-dispatch — fan out up to N candidates honoring the
    # safety_gate cumulatively (per-role cap, rate limit etc. tighten with
    # each emitted message).
    inbox = read_inbox()
    results: list[dict] = []
    dispatched = 0
    blocked = 0
    for cand in candidates[:count]:
        r = _dispatch_one(cand, args.dry_run, inbox)
        results.append(r)
        if r["status"] == "dispatched":
            dispatched += 1
        else:
            blocked += 1
    payload = {
        "dry_run": args.dry_run,
        "count": count,
        "dispatched": dispatched,
        "blocked": blocked,
        "results": results,
        "remaining_candidates": max(0, len(candidates) - count),
    }
    summary = (
        f"dispatch-next multi count={count} dispatched={dispatched} "
        f"blocked={blocked} dry_run={args.dry_run}"
    )
    code = 0 if dispatched > 0 else 1
    return Outcome(code, summary, payload)


# ---------- commands ----------

def cmd_status(args: argparse.Namespace) -> Outcome:
    sessions = read_sessions()
    inbox = read_inbox()
    active = [s for s in sessions if s.get("status") in {"spawning", "active"}]
    stopping = [s for s in sessions if s.get("status") == "stopping"]
    open_msgs = [m for m in inbox if m.get("status") == "open"]
    claimed = [m for m in inbox if m.get("status") == "claimed"]
    payload = {
        "active_sessions": active,
        "stopping_sessions": stopping,
        "open_messages": open_msgs,
        "claimed_messages": claimed,
        "session_count_total": len(sessions),
        "inbox_count_total": len(inbox),
    }
    summary = (
        f"active={len(active)} stopping={len(stopping)} "
        f"open={len(open_msgs)} claimed={len(claimed)} "
        f"(total sessions={len(sessions)}, inbox={len(inbox)})"
    )
    return Outcome(0, summary, payload)


def cmd_inbox(args: argparse.Namespace) -> Outcome:
    role = normalize_role(args.role) if args.role else None
    inbox = read_inbox()
    if role:
        inbox = [m for m in inbox if m.get("to") == role]
    inbox = [m for m in inbox if m.get("status") in {"open", "claimed"}]
    payload = {"role": role, "messages": inbox}
    summary = f"role={role or 'all'} open|claimed={len(inbox)}"
    return Outcome(0, summary, payload)


def cmd_spawn(args: argparse.Namespace) -> Outcome:
    role = normalize_role(args.role)
    task = args.task or "none"
    if not TASK_RE.match(task):
        raise SystemExit(f"task must match TASK-NNN or 'none', got '{task}'")

    # TASK-086 safety gate + TASK-120 parallel-task-independence
    decision = safety_gate.evaluate_spawn(read_sessions(), task_id=task)
    if not decision.allowed:
        ev = safety_gate.write_evidence(
            decision, "spawn",
            {"role": role, "task": task, "dry_run": bool(args.dry_run)},
        )
        print(f"BLOCKED: {decision.code} — {decision.reason}", file=sys.stderr)
        print(f"evidence: {ev.relative_to(REPO_ROOT)}", file=sys.stderr)
        return Outcome(1, f"spawn blocked: {decision.code}", {
            "blocked": True, "decision": decision.to_dict(),
            "evidence": str(ev.relative_to(REPO_ROOT)),
        })

    agent_id = f"agent_{uuid.uuid4().hex[:12]}"
    record = {
        "agent_id": agent_id,
        "role": role,
        "task_id": task,
        "status": "spawning",
        "started_at": ts_now_iso(),
        "stopped_at": None,
        "context_packet": {
            "role": role,
            "task": task,
            "dry_run": bool(args.dry_run),
        },
    }
    payload = {"dry_run": args.dry_run, "session": record}
    summary = f"spawn role={role} task={task} agent_id={agent_id} dry_run={args.dry_run}"
    if not args.dry_run:
        ensure_dirs()
        write_session_json(session_path(agent_id), record)
    return Outcome(0, summary, payload)


def cmd_kill(args: argparse.Namespace) -> Outcome:
    agent_id = args.agent_id
    # TASK-086 safety gate — id format check (kill itself is always allowed)
    decision = safety_gate.evaluate_kill(agent_id)
    if not decision.allowed:
        ev = safety_gate.write_evidence(decision, "kill", {"agent_id": agent_id})
        print(f"BLOCKED: {decision.code} — {decision.reason}", file=sys.stderr)
        print(f"evidence: {ev.relative_to(REPO_ROOT)}", file=sys.stderr)
        return Outcome(1, f"kill blocked: {decision.code}", {
            "blocked": True, "decision": decision.to_dict(),
            "evidence": str(ev.relative_to(REPO_ROOT)),
        })
    if not AGENT_ID_RE.match(agent_id):
        raise SystemExit(f"agent_id must match agent_{{12 hex}}, got '{agent_id}'")
    p = session_path(agent_id)
    if not p.exists():
        return Outcome(2, f"no session file for {agent_id}", {"agent_id": agent_id})
    try:
        record = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"session file unreadable: {exc}")
    outcome = str(getattr(args, "outcome", "stopped") or "stopped")
    record["status"] = "closed" if outcome in {"completed", "failed"} else "stopping"
    record["outcome"] = outcome
    record["stopped_at"] = ts_now_iso()
    payload = {"dry_run": args.dry_run, "session": record}
    summary = f"kill agent_id={agent_id} dry_run={args.dry_run}"
    if not args.dry_run:
        write_session_json(p, record)
        task_id = str(record.get("task_id") or "none")
        owner_role = str(record.get("role") or "runtime")
        if (
            task_id != "none"
            and outcome == "completed"
            and task_completion_is_authoritative(task_id)
        ):
            emit_allimbot_event(
                "task.state.changed",
                {
                    "task_id": task_id,
                    "from_state": "review",
                    "to_state": "completed",
                    "owner_role": owner_role,
                },
            )
        elif task_id != "none" and outcome == "failed":
            emit_allimbot_event(
                "task.state.changed",
                {
                    "task_id": task_id,
                    "from_state": "working",
                    "to_state": "failed",
                    "owner_role": owner_role,
                },
            )
    return Outcome(0, summary, payload)


def cmd_call(args: argparse.Namespace) -> Outcome:
    role = normalize_role(args.role)
    task = args.task or "none"
    if not TASK_RE.match(task):
        raise SystemExit(f"task must match TASK-NNN or 'none', got '{task}'")

    # TASK-086 safety gate
    decision = safety_gate.evaluate_call(role, args.intent, task, read_inbox())
    safety_warning_evidence: str | None = None
    if not decision.allowed:
        ev = safety_gate.write_evidence(
            decision, "call",
            {"role": role, "task": task, "intent": args.intent,
             "dry_run": bool(args.dry_run)},
        )
        print(f"BLOCKED: {decision.code} — {decision.reason}", file=sys.stderr)
        print(f"evidence: {ev.relative_to(REPO_ROOT)}", file=sys.stderr)
        return Outcome(1, f"call blocked: {decision.code}", {
            "blocked": True, "decision": decision.to_dict(),
            "evidence": str(ev.relative_to(REPO_ROOT)),
        })
    if decision.severity == "warn":
        ev = safety_gate.write_evidence(
            decision, "call",
            {"role": role, "task": task, "intent": args.intent,
             "dry_run": bool(args.dry_run)},
        )
        safety_warning_evidence = str(ev.relative_to(REPO_ROOT))
        print(f"WARN: {decision.code} — {decision.reason}", file=sys.stderr)
        print(f"evidence: {safety_warning_evidence}", file=sys.stderr)

    ts_compact = ts_now_compact()
    msg_id = f"MSG-{ts_compact.replace('-', '-')}-{uuid.uuid4().hex[:6]}"
    msg_path = MESSAGES_INBOX / f"{msg_id}.md"
    routing_grade = getattr(args, "routing_grade", None) or routing_grade_for_task(task)
    body = (
        f"---\n"
        f"id: {msg_id}\n"
        f"from: orchestrator\n"
        f"to: {role}\n"
        f"task_id: {task}\n"
        f"intent: {args.intent}\n"
        f"type: request\n"
        f"status: open\n"
        f"ts: {ts_now_iso()}\n"
        f"in_reply_to:\n"
        f"evidence: []\n"
        f"next: []\n"
        f"routing_model: auto\n"
        f"routing_grade: {routing_grade}\n"
        f"---\n\n"
        f"{args.intent}\n"
    )
    payload = {"dry_run": args.dry_run, "message_id": msg_id,
               "path": _display_path(msg_path),
               "routing_model": "auto",
               "routing_grade": routing_grade}
    if safety_warning_evidence:
        payload["safety_warning_evidence"] = safety_warning_evidence
    summary = f"call role={role} task={task} message_id={msg_id} dry_run={args.dry_run}"
    if not args.dry_run:
        ensure_dirs()
        msg_path.write_text(body, encoding="utf-8")
    return Outcome(0, summary, payload)


def _existing_cycle_gate_message(inbox: list[dict], *, task: str, to: str,
                                 intent_prefix: str) -> dict | None:
    for msg in inbox:
        if msg.get("task_id") != task:
            continue
        if msg.get("to") != to:
            continue
        if str(msg.get("intent") or "").startswith(intent_prefix):
            return msg
    return None


def dispatch_cycle_gate_workers(
    gate_result: dict,
    *,
    task: str,
    dry_run: bool,
    intent_prefix: str = "cycle_gate triage",
) -> dict:
    """Fan out cycle_gate worker-role requirements into message inbox calls."""
    if not TASK_RE.match(task):
        raise SystemExit(f"task must match TASK-NNN or 'none', got '{task}'")

    grade = str(gate_result.get("grade") or "unknown")
    mode = str(gate_result.get("mode") or "unknown")
    subagents = [str(s) for s in gate_result.get("required_subagents") or []]
    subagent_text = ",".join(subagents) if subagents else "-"
    routing = gate_result.get("routing") or {}
    routing_tier = routing.get("selected_tier") or routing.get("policy_tier") or "auto"
    routing_payload = {
        "grade": routing.get("grade") or grade,
        "policy_tier": routing.get("policy_tier") or routing_tier,
        "selected_tier": routing.get("selected_tier") or routing_tier,
        "signals": list(routing.get("signals") or []),
        "reason": routing.get("reason") or "cycle_gate triage",
    }
    items: list[dict] = []
    subagent_items: list[dict] = []
    dispatched = 0
    subagents_dispatched = 0
    blocked = 0
    skipped_existing = 0
    inbox = read_inbox()

    for raw_subagent in gate_result.get("required_subagents") or []:
        role = str(raw_subagent)
        target = f"subagent-{role}"
        intent = (
            f"{intent_prefix}: cycle_gate grade={grade} mode={mode} "
            f"subagent={role} workers="
            f"{','.join(str(r) for r in gate_result.get('required_worker_roles') or []) or '-'} "
            f"routing={routing_tier}. Provide perspective-local review evidence."
        )
        existing = _existing_cycle_gate_message(
            inbox, task=task, to=target, intent_prefix=intent_prefix,
        )
        if existing is not None:
            skipped_existing += 1
            subagent_items.append({
                "role": role,
                "status": "skipped_existing",
                "path": existing.get("__path"),
                "message_id": existing.get("id"),
            })
            continue
        subagent_dispatch.MESSAGES_INBOX = MESSAGES_INBOX
        msg_path = subagent_dispatch.emit_call_message(
            role_id=role,
            task_id=task,
            intent=intent,
            sender="orchestrator",
            routing=routing_payload,
            dry_run=dry_run,
        )
        evt_path = subagent_dispatch.emit_event(
            role_id=role,
            task_id=task,
            kind="dispatch",
            extra={
                "message_id": msg_path.stem,
                "intent": intent,
                **subagent_dispatch.routing_event_fields(routing_payload),
            },
            dry_run=dry_run,
        )
        item = {
            "role": role,
            "status": "dispatched",
            "message_id": msg_path.stem,
            "path": _display_path(msg_path),
            "event_path": _display_path(evt_path),
        }
        subagent_items.append(item)
        subagents_dispatched += 1
        inbox.append({
            "id": msg_path.stem,
            "to": target,
            "task_id": task,
            "intent": intent,
            "type": "subagent_call",
            "status": "open",
            "__path": _display_path(msg_path),
        })

    for raw_role in gate_result.get("required_worker_roles") or []:
        role = normalize_role(str(raw_role))
        intent = (
            f"{intent_prefix}: cycle_gate grade={grade} mode={mode} "
            f"worker={role} subagents={subagent_text} routing={routing_tier}. "
            "Provide role-local review evidence, risks, and required follow-up."
        )
        existing = _existing_cycle_gate_message(
            inbox, task=task, to=role, intent_prefix=intent_prefix,
        )
        if existing is not None:
            skipped_existing += 1
            items.append({
                "role": role,
                "status": "skipped_existing",
                "path": existing.get("__path"),
                "message_id": existing.get("id"),
            })
            continue
        outcome = cmd_call(argparse.Namespace(
            role=role,
            intent=intent,
            task=task,
            dry_run=dry_run,
            routing_grade=grade,
        ))
        item = {
            "role": role,
            "code": outcome.code,
            "summary": outcome.summary,
            **outcome.payload,
        }
        items.append(item)
        if outcome.code == 0:
            dispatched += 1
            inbox.append({
                "id": outcome.payload.get("message_id"),
                "to": role,
                "task_id": task,
                "intent": intent,
                "type": "request",
                "status": "open",
                "__path": outcome.payload.get("path"),
            })
        else:
            blocked += 1

    return {
        "dry_run": dry_run,
        "task": task,
        "grade": grade,
        "mode": mode,
        "required_subagents": subagents,
        "dispatched": dispatched,
        "subagents_dispatched": subagents_dispatched,
        "blocked": blocked,
        "skipped_existing": skipped_existing,
        "items": items,
        "subagent_items": subagent_items,
    }


def cmd_triage_cycle(args: argparse.Namespace) -> Outcome:
    task = args.task
    if not TASK_RE.match(task):
        raise SystemExit(f"task must match TASK-NNN or 'none', got '{task}'")
    if args.diff:
        changed = cycle_gate._git_changed(args.diff)
        diff_lines = cycle_gate._git_diff_line_count(args.diff) if args.diff_lines is None else args.diff_lines
    elif args.changed is not None:
        changed = args.changed
        diff_lines = 0 if args.diff_lines is None else args.diff_lines
    else:
        changed = cycle_gate._git_changed("origin/main")
        diff_lines = cycle_gate._git_diff_line_count("origin/main") if args.diff_lines is None else args.diff_lines

    gate_result = cycle_gate.evaluate(
        changed,
        prompt=args.prompt or "",
        diff_lines=diff_lines,
    )
    payload = dispatch_cycle_gate_workers(
        gate_result,
        task=task,
        dry_run=args.dry_run,
        intent_prefix=args.intent_prefix,
    )
    payload["changed"] = changed
    payload["diff_lines"] = diff_lines
    summary = (
        f"triage-cycle task={task} grade={payload['grade']} "
        f"workers={len(gate_result.get('required_worker_roles') or [])} "
        f"dispatched={payload['dispatched']} blocked={payload['blocked']} "
        f"dry_run={args.dry_run}"
    )
    return Outcome(0 if payload["blocked"] == 0 else 1, summary, payload)


def cmd_go_to_work(args: argparse.Namespace) -> Outcome:
    sessions = read_sessions()
    inbox = read_inbox()
    candidates = [m for m in inbox if m.get("status") == "open"]
    plan = {
        "now": ts_now_iso(),
        "active_sessions_carried_over": [s for s in sessions if s.get("status") in {"spawning", "active"}],
        "open_messages_needing_attention": candidates,
        "next_actions": [
            "review open messages and decide which roles to /spawn",
            "use /call <role> for explicit asks",
            "use /status to confirm before any real spawn",
        ],
    }
    payload = {"dry_run": args.dry_run, "plan": plan}
    summary = f"go-to-work carried={len(plan['active_sessions_carried_over'])} open={len(candidates)}"
    return Outcome(0, summary, payload)


def cmd_leave_for_work(args: argparse.Namespace) -> Outcome:
    sessions = read_sessions()
    actions: list[str] = []
    for s in sessions:
        if s.get("status") in {"spawning", "active"}:
            actions.append(f"would transition {s.get('agent_id')} -> stopping")
    payload = {"dry_run": args.dry_run, "actions": actions, "session_count": len(sessions)}
    summary = f"leave-for-work would_stop={len(actions)} (dry_run={args.dry_run})"
    if not args.dry_run:
        ensure_dirs()
        ts = ts_now_iso()
        for s in sessions:
            if s.get("status") in {"spawning", "active"}:
                p = session_path(s["agent_id"])
                s["status"] = "stopping"
                s["stopped_at"] = ts
                write_session_json(p, s)
    return Outcome(0, summary, payload)


CLAIM_PROGRESS_SUCCESS_STATUSES = {
    "heartbeated",
    "heartbeat_committed_with_warnings",
}
CLAIM_PROGRESS_PROJECTION_OPERATIONS = {
    "merge",
    "overlay-no-primary-pointer",
}


def _strict_revision(value: object) -> int | None:
    if type(value) is not int or value < 0:
        return None
    return value


def _bounded_claim_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value[:256]


def _claim_progress_identity_value_valid(
    value: object,
    *,
    required: bool,
) -> bool:
    if value is None:
        return not required
    if not isinstance(value, str) or len(value) > 256:
        return False
    if "\n" in value or "\r" in value or value != value.strip():
        return False
    return bool(value) if required else True


def _claim_progress_identity_matches(
    candidate: dict[str, object],
    claim: dict[str, object],
) -> bool:
    for field, required in (
        ("task_id", True),
        ("unit_id", False),
        ("task_set_id", False),
    ):
        value = claim.get(field)
        if not _claim_progress_identity_value_valid(value, required=required):
            return False
        if candidate.get(field) != value:
            return False
    return True


def _claim_progress_projection_valid(
    payload: dict[str, object],
    claim: dict[str, object],
    projection: dict[str, object],
    *,
    claim_id: str,
    committed_revision: int,
) -> bool:
    claim_ref = f"agents/runtime/task_claims/{claim_id}.json"
    if (
        payload.get("path") != claim_ref
        or projection.get("status") != "projection"
        or projection.get("task_claim_ref") != claim_ref
        or not _claim_progress_identity_matches(projection, claim)
    ):
        return False

    operation = projection.get("operation")
    if operation == "overlay-no-primary-pointer":
        return claim.get("overlay") is True and "pointer" not in projection
    if operation != "merge" or claim.get("overlay") is True:
        return False

    pointer = projection.get("pointer")
    if not isinstance(pointer, dict):
        return False
    if (
        pointer.get("active_task") != claim.get("task_id")
        or pointer.get("active_task_set") != claim.get("task_set_id")
        or pointer.get("active_claims") != [claim_ref]
    ):
        return False
    current_agents = pointer.get("current_agents")
    if not isinstance(current_agents, list) or len(current_agents) != 1:
        return False
    current_agent = current_agents[0]
    return (
        isinstance(current_agent, dict)
        and current_agent.get("claim_id") == claim_id
        and _strict_revision(current_agent.get("mutation_revision"))
        == committed_revision
        and _claim_progress_identity_matches(current_agent, claim)
    )


def _claim_progress_current(payload: object) -> dict[str, object]:
    claim = payload.get("claim") if isinstance(payload, dict) else None
    receipt = payload.get("receipt") if isinstance(payload, dict) else None
    projection = payload.get("projection") if isinstance(payload, dict) else None
    return {
        "claim_id": (
            _bounded_claim_id(claim.get("claim_id"))
            if isinstance(claim, dict)
            else None
        ),
        "claim_revision": (
            _strict_revision(claim.get("mutation_revision"))
            if isinstance(claim, dict)
            else None
        ),
        "receipt_revision": (
            _strict_revision(receipt.get("claim_revision"))
            if isinstance(receipt, dict)
            else None
        ),
        "projection_claim_id": (
            _bounded_claim_id(projection.get("claim_id"))
            if isinstance(projection, dict)
            else None
        ),
        "projection_revision": (
            _strict_revision(projection.get("claim_revision"))
            if isinstance(projection, dict)
            else None
        ),
    }


def _claim_progress_receipt_valid(
    payload: object,
    *,
    claim_id: str,
    committed_revision: int,
) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("status") not in CLAIM_PROGRESS_SUCCESS_STATUSES:
        return False
    claim = payload.get("claim")
    receipt = payload.get("receipt")
    projection = payload.get("projection")
    if not all(isinstance(item, dict) for item in (claim, receipt, projection)):
        return False
    assert isinstance(claim, dict)
    assert isinstance(receipt, dict)
    assert isinstance(projection, dict)
    identity_and_revision_valid = (
        claim.get("claim_id") == claim_id
        and _strict_revision(claim.get("mutation_revision"))
        == committed_revision
        and receipt.get("committed") is True
        and _strict_revision(receipt.get("claim_revision"))
        == committed_revision
        and projection.get("claim_id") == claim_id
        and _strict_revision(projection.get("claim_revision"))
        == committed_revision
        and projection.get("operation")
        in CLAIM_PROGRESS_PROJECTION_OPERATIONS
    )
    return identity_and_revision_valid and _claim_progress_projection_valid(
        payload,
        claim,
        projection,
        claim_id=claim_id,
        committed_revision=committed_revision,
    )


def _claim_progress_indeterminate(
    args: argparse.Namespace,
    *,
    dispatcher_returncode: int,
    payload: object,
    stderr: object,
) -> Outcome:
    committed_revision = args.expected_revision + 1
    bounded_stderr = " ".join(str(stderr or "").split())[:256]
    result = {
        "status": "claim_progress_receipt_indeterminate",
        "commit_state": "unknown",
        "retry_safe": False,
        "dispatcher_returncode": dispatcher_returncode,
        "expected": {
            "claim_id": args.claim_id,
            "prior_revision": args.expected_revision,
            "committed_revision": committed_revision,
        },
        "current": _claim_progress_current(payload),
    }
    if bounded_stderr:
        result["stderr"] = bounded_stderr
    return Outcome(2, "claim_progress_receipt_indeterminate", result)


def cmd_claim_progress(args: argparse.Namespace) -> Outcome:
    """Delegate one progress mutation to the serial claim authority."""

    dispatcher = Path(__file__).resolve().parent / "task_claim_dispatcher.py"
    command = [
        sys.executable,
        str(dispatcher),
        "--root",
        str(REPO_ROOT),
        "heartbeat",
        "--claim-id",
        args.claim_id,
        "--agent-instance-id",
        args.agent_instance_id,
        "--callsite-id",
        args.callsite_id,
        "--expected-revision",
        str(args.expected_revision),
        "--phase",
        args.phase,
        "--progress-pct",
        str(args.progress_pct),
        "--step-index",
        str(args.step_index),
        "--step-total",
        str(args.step_total),
        "--status-text",
        args.status_text,
    ]
    if args.now:
        command.extend(("--now", args.now))
    command.append("--json")
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return Outcome(
            1,
            "claim_progress_failed",
            {
                "status": "claim_progress_failed",
                "stderr": " ".join(str(exc).split())[:256],
            },
        )
    try:
        parsed_payload = json.loads(result.stdout)
    except (json.JSONDecodeError, TypeError):
        parsed_payload = None
    if result.returncode == 0:
        committed_revision = args.expected_revision + 1
        if not _claim_progress_receipt_valid(
            parsed_payload,
            claim_id=args.claim_id,
            committed_revision=committed_revision,
        ):
            return _claim_progress_indeterminate(
                args,
                dispatcher_returncode=result.returncode,
                payload=parsed_payload,
                stderr=result.stderr,
            )
        assert isinstance(parsed_payload, dict)
        return Outcome(0, str(parsed_payload["status"]), parsed_payload)
    if isinstance(parsed_payload, dict):
        payload = parsed_payload
    else:
        payload = {
            "status": "claim_progress_failed",
            "stderr": " ".join(str(result.stderr or "").split())[:256],
        }
    summary = str(payload.get("status") or "claim_progress")
    return Outcome(result.returncode, summary, payload)


# ---------- CLI ----------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true",
                        help="emit machine-readable JSON payload")

    parser = argparse.ArgumentParser(
        prog="agent_orchestrator",
        description="Agent orchestrator command router (TASK-082).",
        parents=[common],
    )

    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>",
                                parser_class=argparse.ArgumentParser)

    def add_dry_run(p):
        p.add_argument("--dry-run", action="store_true",
                       help="show what would change without writing files")

    def sp(name, **kw):
        return sub.add_parser(name, parents=[common], **kw)

    p_status = sp("status", help="show active sessions and pending messages")
    p_status.set_defaults(func=cmd_status)

    p_inbox = sp("inbox", help="list open/claimed messages")
    p_inbox.add_argument("--role", help="filter by recipient role")
    p_inbox.set_defaults(func=cmd_inbox)

    p_spawn = sp("spawn", help="register a new agent session")
    p_spawn.add_argument("role")
    p_spawn.add_argument("--task", help="TASK-NNN this agent is claiming")
    add_dry_run(p_spawn)
    p_spawn.set_defaults(func=cmd_spawn)

    p_kill = sp("kill", help="close an agent session with an explicit outcome")
    p_kill.add_argument("agent_id")
    p_kill.add_argument(
        "--outcome",
        choices=("stopped", "completed", "failed"),
        default="stopped",
        help="send a task notification only for completed or failed",
    )
    add_dry_run(p_kill)
    p_kill.set_defaults(func=cmd_kill)

    p_call = sp("call", help="write a request message to a role")
    p_call.add_argument("role")
    p_call.add_argument("intent", help="one-line message body")
    p_call.add_argument("--task", help="TASK-NNN this request is about")
    add_dry_run(p_call)
    p_call.set_defaults(func=cmd_call)

    p_triage = sp("triage-cycle", help="fan out cycle_gate worker roles into inbox calls")
    p_triage.add_argument("--task", required=True, help="TASK-NNN this triage is about")
    p_triage.add_argument("--changed", nargs="*", default=None, help="changed file paths")
    p_triage.add_argument("--diff", metavar="BASE", help="git diff base (e.g. origin/main)")
    p_triage.add_argument("--prompt", default="", help="optional prompt text for routing signals")
    p_triage.add_argument("--diff-lines", type=int, default=None,
                          help="override changed line count for model routing")
    p_triage.add_argument("--intent-prefix", default="cycle_gate triage",
                          help="prefix for emitted worker call intents")
    add_dry_run(p_triage)
    p_triage.set_defaults(func=cmd_triage_cycle)

    p_gtw = sp("go-to-work", help="start a session and show plan")
    add_dry_run(p_gtw)
    p_gtw.set_defaults(func=cmd_go_to_work)

    p_lfw = sp("leave-for-work", help="end the session and stop heartbeats")
    add_dry_run(p_lfw)
    p_lfw.set_defaults(func=cmd_leave_for_work)

    p_progress = sp(
        "claim-progress",
        help="atomically record progress through task_claim_dispatcher heartbeat",
    )
    p_progress.add_argument("--claim-id", required=True)
    p_progress.add_argument("--agent-instance-id", required=True)
    p_progress.add_argument("--callsite-id", required=True)
    p_progress.add_argument("--expected-revision", type=int, required=True)
    p_progress.add_argument("--phase", required=True)
    p_progress.add_argument("--progress-pct", type=int, required=True)
    p_progress.add_argument("--step-index", type=int, required=True)
    p_progress.add_argument("--step-total", type=int, required=True)
    p_progress.add_argument("--status-text", required=True)
    p_progress.add_argument("--now")
    p_progress.set_defaults(func=cmd_claim_progress)

    p_dn = sp("dispatch-next", help="auto-dispatch the highest-priority 대기 TASK to its Owner")
    p_dn.add_argument("--role", help="optional Owner role filter (qa/backend/...)")
    p_dn.add_argument("--count", type=int, default=1,
                      help="TASK-120: dispatch up to N candidates in priority order (default 1)")
    add_dry_run(p_dn)
    p_dn.set_defaults(func=cmd_dispatch_next)

    return parser


def normalize_argv(argv: list[str]) -> list[str]:
    """Strip leading '/' on the first positional command for friendlier UX.

    `agent_orchestrator.py /status` is rewritten to `agent_orchestrator.py status`.
    Role aliases like `/qa` are also supported as a call shortcut.
    """
    if not argv:
        return argv
    first = argv[0]
    if first.startswith("/"):
        stripped = first[1:]
        # TASK-118: /dispatch-next is its own command, not a /call shortcut.
        if stripped == "dispatch-next":
            return ["dispatch-next"] + argv[1:]
        if stripped in {"qa", "lead-engineer", "backend", "ci-cd", "uiux", "ceo",
                        "doc", "doc-steward", "steward", "scribe", "archivist",
                        "research", "research-agent", "researcher",
                        "timeline", "timeline-agent", "chronology"}:
            # /qa "msg" -> call qa "msg"
            return ["call", stripped] + argv[1:]
        return [stripped] + argv[1:]
    return argv


def render(outcome: Outcome, as_json: bool) -> int:
    if as_json:
        print(json.dumps(outcome.payload, indent=2, ensure_ascii=False))
    else:
        print(outcome.summary)
        if outcome.payload:
            for k, v in outcome.payload.items():
                if isinstance(v, list) and v:
                    print(f"  {k}: {len(v)} item(s)")
                    for item in v[:5]:
                        if isinstance(item, dict):
                            short = " / ".join(f"{kk}={vv}" for kk, vv in list(item.items())[:3])
                            print(f"    - {short}")
                        else:
                            print(f"    - {item}")
                elif isinstance(v, dict) and v:
                    print(f"  {k}:")
                    for kk, vv in list(v.items())[:5]:
                        print(f"    {kk}: {vv}")
                else:
                    print(f"  {k}: {v}")
    return outcome.code


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    argv = normalize_argv(list(argv if argv is not None else sys.argv[1:]))
    args = parser.parse_args(argv)
    outcome = args.func(args)
    return render(outcome, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
