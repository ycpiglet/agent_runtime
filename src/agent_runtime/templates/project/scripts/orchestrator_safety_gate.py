#!/usr/bin/env python3
"""Orchestrator safety gate.

Policy module enforced by `scripts/agent_orchestrator.py` before any spawn/kill/call.
Violations terminate the orchestrator command and write a JSON evidence file under
`agents/runtime/safety_violations/` for later Independent Auditor review.

Nine policies (see agents/independent_auditor/SAFETY-GATE.md for full spec):
  1. MAX_ACTIVE_AGENTS                 = 5      (spawn)
  2. MAX_OPEN_MESSAGES                 = 20     (call)
  3. MAX_OPEN_MESSAGES_PER_ROLE        = 5      (call)
  4. EMERGENCY_STOP_FILE               = ".orchestrator-stop"  (spawn, call)
  5. FORBIDDEN_INTENT_PATTERNS         = 7 regex  (call)
  6. REPEATED_FAILURE_THRESHOLD        = 3 open+claimed for same (role,task)  (call, warn)
  7. AUDIT_REQUIRED_FOR_CRITICAL_TASKS — call body must contain `audit_acknowledged: true`
  8. PARALLEL_TASK_INDEPENDENCE        (spawn)  — same task_id 동시 spawn 차단
  9. RATE_LIMIT_CALLS_PER_MINUTE       = 30     (call, warn)  — 분당 호출 cap

The module is pure (no I/O for evaluate_*); evidence writing is a separate call.
"""

from __future__ import annotations

import json
import re
import sys
import time
import uuid
import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent
EMERGENCY_STOP_FILE = REPO_ROOT / ".orchestrator-stop"
EVIDENCE_DIR = REPO_ROOT / "agents" / "runtime" / "safety_violations"
TASKS_DIR = REPO_ROOT / "agents" / "lead_engineer" / "tasks"

# Policy constants
MAX_ACTIVE_AGENTS = 5
MAX_OPEN_MESSAGES = 20
MAX_OPEN_MESSAGES_PER_ROLE = 5
REPEATED_FAILURE_THRESHOLD = 3
ACTIVE_SESSION_STATES = {"spawning", "active"}
OPEN_MESSAGE_STATES = {"open", "claimed"}
RATE_LIMIT_CALLS_PER_MINUTE = 30
RATE_LIMIT_WINDOW_SECONDS = 60

# Static fallback for critical TASK IDs that are especially sensitive or may be
# referenced before task frontmatter can be read.
STATIC_CRITICAL_TASK_IDS = set()
AUDIT_ACK_TOKEN_RE = re.compile(r"\baudit_acknowledged\s*:\s*true\b", re.IGNORECASE)

# Forbidden intent patterns — regex matched against full call intent text
FORBIDDEN_INTENT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("rm-rf-root", re.compile(r"\brm\s+-rf\s+/(?!\w)", re.IGNORECASE)),
    ("force-push", re.compile(r"\bgit\s+push\s+.*--force\b", re.IGNORECASE)),
    ("drop-table", re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)),
    ("chmod-777", re.compile(r"\bchmod\s+(?:0?)777\b")),
    ("fork-bomb", re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("no-verify", re.compile(r"--no-verify\b")),
]


@dataclass
class SafetyDecision:
    allowed: bool
    code: str  # short policy code, e.g. "max-agents", "ok"
    reason: str  # human-readable single sentence
    severity: str = "error"  # "ok", "warn", "error"
    matched: list[str] = field(default_factory=list)

    @classmethod
    def ok(cls, code: str = "ok", reason: str = "") -> "SafetyDecision":
        return cls(True, code, reason or "passed", severity="ok")

    @classmethod
    def warn(cls, code: str, reason: str, matched: list[str] | None = None) -> "SafetyDecision":
        return cls(True, code, reason, severity="warn", matched=matched or [])

    @classmethod
    def deny(cls, code: str, reason: str, matched: list[str] | None = None) -> "SafetyDecision":
        return cls(False, code, reason, severity="error", matched=matched or [])

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "code": self.code,
            "reason": self.reason,
            "severity": self.severity,
            "matched": self.matched,
        }


# ---------- evaluators ----------

def check_emergency_stop() -> SafetyDecision:
    if EMERGENCY_STOP_FILE.exists():
        return SafetyDecision.deny(
            "emergency-stop",
            f".orchestrator-stop file present — all spawn/call blocked. "
            f"Remove {EMERGENCY_STOP_FILE.name} to resume."
        )
    return SafetyDecision.ok()


def critical_task_ids() -> set[str]:
    """Return critical TASK IDs from frontmatter plus static fallbacks."""
    ids = set(STATIC_CRITICAL_TASK_IDS)
    if not TASKS_DIR.is_dir():
        return ids
    for path in TASKS_DIR.glob("TASK-*.md"):
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if not text.startswith("---"):
            continue
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        meta = parts[1]
        task_id = None
        priority = None
        for raw in meta.splitlines():
            line = raw.strip()
            if line.startswith("id:"):
                task_id = line.partition(":")[2].strip()
            elif line.startswith("priority:"):
                priority = line.partition(":")[2].strip()
        if task_id and priority == "Critical":
            ids.add(task_id)
    return ids


def evaluate_spawn(active_sessions: list[dict],
                   task_id: str | None = None) -> SafetyDecision:
    """Return SafetyDecision for a /spawn attempt given current sessions.

    When `task_id` is supplied (and not 'none'), the
    PARALLEL_TASK_INDEPENDENCE policy blocks a second spawn on the same
    task. Two workers may run in parallel, but not on the same TASK.
    """
    stop = check_emergency_stop()
    if not stop.allowed:
        return stop
    active = [s for s in active_sessions if s.get("status") in ACTIVE_SESSION_STATES]
    if len(active) >= MAX_ACTIVE_AGENTS:
        return SafetyDecision.deny(
            "max-agents",
            f"max active agents {MAX_ACTIVE_AGENTS} reached "
            f"(currently {len(active)} in {sorted(ACTIVE_SESSION_STATES)})"
        )
    if task_id and task_id != "none":
        collisions = [s for s in active if s.get("task_id") == task_id]
        if collisions:
            return SafetyDecision.deny(
                "parallel-task-collision",
                f"task {task_id} already has {len(collisions)} active session(s); "
                f"PARALLEL_TASK_INDEPENDENCE policy blocks duplicate spawn",
                matched=[task_id],
            )
    return SafetyDecision.ok("spawn-ok", "spawn allowed")


def evaluate_kill(agent_id: str) -> SafetyDecision:
    """kill is always allowed (it's a safety release) — but check format."""
    if not re.match(r"^agent_[0-9a-f]{12}$", agent_id):
        return SafetyDecision.deny(
            "bad-agent-id",
            f"agent_id '{agent_id}' must match agent_{{12 hex}}"
        )
    return SafetyDecision.ok("kill-ok", "kill allowed")


def _recent_calls_within_window(inbox: list[dict],
                               now: _dt.datetime | None = None,
                               window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
                               ) -> list[dict]:
    """Return inbox messages whose `ts` falls within the recent window."""
    if not inbox:
        return []
    ref = now or _dt.datetime.now().astimezone()
    out: list[dict] = []
    for m in inbox:
        ts = m.get("ts", "")
        if not isinstance(ts, str) or not ts:
            continue
        try:
            t = _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            continue
        if t.tzinfo is None:
            t = t.replace(tzinfo=ref.tzinfo)
        if 0 <= (ref - t).total_seconds() <= window_seconds:
            out.append(m)
    return out


def evaluate_call(role: str, intent: str, task: str, inbox: list[dict],
                 now: _dt.datetime | None = None) -> SafetyDecision:
    """Return SafetyDecision for a /call attempt.

    inbox is the list of frontmatter dicts from agents/messages/inbox/.
    Worst (most severe) decision wins; warn does not block but is surfaced.

    `now` is an optional injection point for the rate-limit
    policy so tests can pin a reference time.
    """
    stop = check_emergency_stop()
    if not stop.allowed:
        return stop

    # Policy 5: forbidden intent patterns
    matched = [name for name, pat in FORBIDDEN_INTENT_PATTERNS if pat.search(intent)]
    if matched:
        return SafetyDecision.deny(
            "forbidden-intent",
            f"intent matches forbidden pattern(s): {', '.join(matched)}",
            matched=matched,
        )

    # Policy 2: total open msgs cap
    open_msgs = [m for m in inbox if m.get("status") in OPEN_MESSAGE_STATES]
    if len(open_msgs) >= MAX_OPEN_MESSAGES:
        return SafetyDecision.deny(
            "max-open-messages",
            f"max open|claimed messages {MAX_OPEN_MESSAGES} reached "
            f"(currently {len(open_msgs)})"
        )

    # Policy 3: per-role cap
    per_role = [m for m in open_msgs if m.get("to") == role]
    if len(per_role) >= MAX_OPEN_MESSAGES_PER_ROLE:
        return SafetyDecision.deny(
            "max-per-role",
            f"max open|claimed messages per role {MAX_OPEN_MESSAGES_PER_ROLE} reached "
            f"for role '{role}' (currently {len(per_role)})"
        )

    # Policy 7: audit-required for critical task
    critical_ids = critical_task_ids()
    if task in critical_ids and not AUDIT_ACK_TOKEN_RE.search(intent):
        return SafetyDecision.deny(
            "audit-required",
            f"call targeting critical {task} must include "
            f"'audit_acknowledged: true' token in intent",
            matched=[task],
        )

    # Policy 6: repeated failure threshold (warn, does not block)
    same_pair = [m for m in open_msgs if m.get("to") == role and m.get("task_id") == task]
    if len(same_pair) >= REPEATED_FAILURE_THRESHOLD:
        return SafetyDecision.warn(
            "repeated-failure",
            f"role={role} task={task} already has {len(same_pair)} open|claimed "
            f"message(s) — consider escalation rather than another /call",
            matched=[m.get("id", "?") for m in same_pair],
        )

    # Policy 9: rate limit — recent calls within the window
    if RATE_LIMIT_CALLS_PER_MINUTE > 0:
        recent = _recent_calls_within_window(inbox, now=now)
        if len(recent) >= RATE_LIMIT_CALLS_PER_MINUTE:
            return SafetyDecision.warn(
                "rate-limit",
                f"rate limit: {len(recent)} call(s) in last "
                f"{RATE_LIMIT_WINDOW_SECONDS}s (cap {RATE_LIMIT_CALLS_PER_MINUTE}) — "
                f"backoff recommended before next call",
                matched=[m.get("id", "?") for m in recent[:5]],
            )

    return SafetyDecision.ok("call-ok", "call allowed")


# ---------- evidence writer ----------

def _evidence_id() -> str:
    return f"SAFETY-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _ts_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def write_evidence(decision: SafetyDecision, action: str, context: dict) -> Path:
    """Persist a violation/warning to disk for later audit. Returns evidence path."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    eid = _evidence_id()
    record = {
        "evidence_id": eid,
        "ts": _ts_iso(),
        "action": action,
        "decision": decision.to_dict(),
        "context": context,
    }
    path = EVIDENCE_DIR / f"{eid}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ---------- CLI for ad-hoc inspection ----------

def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Inspect safety gate policy or simulate a decision.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("policy", help="print policy catalog (JSON)")
    p_eval_spawn = sub.add_parser("eval-spawn", help="simulate spawn decision (no real sessions)")
    p_eval_spawn.add_argument("--active", type=int, default=0,
                              help="number of active sessions to assume")
    p_eval_spawn.add_argument("--task", default=None,
                              help="task_id for parallel-independence check")
    p_eval_spawn.add_argument("--collide-task", default=None,
                              help="if set, fake active sessions also hold this task_id "
                                   "(use to simulate a parallel-task collision)")
    p_eval_call = sub.add_parser("eval-call", help="simulate call decision")
    p_eval_call.add_argument("--role", required=True)
    p_eval_call.add_argument("--task", default="none")
    p_eval_call.add_argument("--intent", required=True)
    p_eval_call.add_argument("--open-per-role", type=int, default=0,
                             help="assume N existing open messages to this role")
    args = parser.parse_args(argv)

    if args.cmd == "policy":
        print(json.dumps({
            "MAX_ACTIVE_AGENTS": MAX_ACTIVE_AGENTS,
            "MAX_OPEN_MESSAGES": MAX_OPEN_MESSAGES,
            "MAX_OPEN_MESSAGES_PER_ROLE": MAX_OPEN_MESSAGES_PER_ROLE,
            "REPEATED_FAILURE_THRESHOLD": REPEATED_FAILURE_THRESHOLD,
            "RATE_LIMIT_CALLS_PER_MINUTE": RATE_LIMIT_CALLS_PER_MINUTE,
            "RATE_LIMIT_WINDOW_SECONDS": RATE_LIMIT_WINDOW_SECONDS,
            "EMERGENCY_STOP_FILE": str(EMERGENCY_STOP_FILE.relative_to(REPO_ROOT)),
            "CRITICAL_TASK_IDS": sorted(critical_task_ids()),
            "FORBIDDEN_INTENT_PATTERNS": [name for name, _ in FORBIDDEN_INTENT_PATTERNS],
        }, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "eval-spawn":
        fake_sessions = [{"status": "active", "task_id": args.collide_task or "none"}
                         for _ in range(args.active)]
        decision = evaluate_spawn(fake_sessions, task_id=args.task)
        print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))
        return 0 if decision.allowed else 1

    if args.cmd == "eval-call":
        fake_inbox = [{"to": args.role, "task_id": args.task, "status": "open"}
                      for _ in range(args.open_per_role)]
        decision = evaluate_call(args.role, args.intent, args.task, fake_inbox)
        print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))
        return 0 if decision.allowed else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
