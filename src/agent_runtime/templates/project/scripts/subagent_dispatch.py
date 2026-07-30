#!/usr/bin/env python3
"""Subagent dispatch helper (TASK-116).

Standardizes session-layer Agent tool invocation for 7 subagent roles.
TASK-109/113 used ad-hoc subagent calls; this module formalizes the
pattern: pick a role, render a deterministic prompt, optionally emit a
`subagent_call` message and an event log line. The actual provider/native
subagent invocation stays in the parent session — this helper produces the
standardized prompt + audit trail so different execution surfaces produce
the same observable dispatch contract.

7 subagent roles (orthogonal to worker roles like backend/qa/ci-cd):
  - scribe       — low-cost bounded archival and state projection
  - explorer     — read-only repository inspection and bounded evidence lookup
  - implementer  — write the code/files for the task spec
  - reviewer     — check implementation vs spec, surface issues
  - auditor      — independent audit (AGENTS.md §6.4): pass / 보류 / 재검토 필요
  - strategist   — alternatives, tradeoffs, risks before implementation
  - skeptic      — adversarial: what could break, what's missing, what's wrong

Read STAGE-7-CLAUDE-SUBAGENT.md §5 (axes 1 + 2) for the spec.

Usage:
  python scripts/subagent_dispatch.py --list-roles
  python scripts/subagent_dispatch.py --for-worker qa
  python scripts/subagent_dispatch.py --role reviewer --task-id TASK-116 \\
      --intent "review subagent_dispatch.py" --context-packet path.md
  python scripts/subagent_dispatch.py --role reviewer --task-id TASK-116 \\
      --intent "..." --emit-call

Outputs (when not dry-run + --emit-call):
  - agents/messages/inbox/MSG-YYYYMMDD-HHMMSS-{hex}.md (kind=subagent_call)
  - agents/runtime/events/subagent-YYYY-MM-DD.jsonl (dispatch event)
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
ROLES_YML = ROOT / "agents" / "roles.yml"
MESSAGES_INBOX = ROOT / "agents" / "messages" / "inbox"
EVENTS_DIR = ROOT / "agents" / "runtime" / "events"
SUBAGENT_COUNTER_DIR = ROOT / "agents" / "runtime" / "subagent-counter"

import model_routing  # noqa: E402


def resolve_model_decision(
    model: str | None,
    *,
    grade: str | None,
    intent: str,
    changed_files: list[str] | None = None,
    diff_lines: int = 0,
) -> dict | None:
    return model_routing.resolve_model(
        model or "auto",
        grade=grade,
        prompt=intent,
        changed_files=changed_files,
        diff_lines=diff_lines,
    )


def routing_event_fields(
    decision: dict | None,
    *,
    dispatch_id: str | None = None,
    provider: str | None = None,
    route: dict | None = None,
    preflight: dict | None = None,
) -> dict:
    """Return the common observational envelope for a generic dispatch."""
    route = dict(route or {})
    preflight = dict(preflight or {})
    fields = {
        "dispatch_id": dispatch_id,
        "provider": route.get("provider") or provider or "unverified",
        "execution_surface": route.get("execution_surface") or "parent_session_tool",
        "requested_tier": route.get("requested_tier"),
        "selected_tier": route.get("selected_tier"),
        "provider_tier": route.get("provider_tier"),
        "resolved_model": route.get("resolved_model"),
        "model_source": route.get("model_source") or "unverified",
        "reasoning_effort": route.get("reasoning_effort"),
        "reasoning_source": route.get("reasoning_source") or "unverified",
        "route_status": route.get("route_status") or "unverified",
        "equivalence_status": route.get("equivalence_status") or "unverified",
        "application_status": route.get("application_status") or "unverified",
        "model_changed": route.get("model_changed"),
        "route_changed": route.get("route_changed"),
        "role_policy_id": route.get("role_policy_id"),
        "role_policy_status": route.get("role_policy_status"),
        "role_policy_reason": route.get("role_policy_reason"),
        "high_tier_authorized": route.get("high_tier_authorized"),
        "registered_escalation_reason": route.get(
            "registered_escalation_reason"
        ),
        "model_observation_status": "unverified",
        "token_usage_status": "unavailable",
        "tokens_in": None,
        "tokens_out": None,
        "latency_status": "unavailable",
        "latency_ms": None,
        "billed_cost_status": "unavailable",
        "billed_cost": None,
        "currency": None,
        "deterministic_preflight": preflight.get("status", "not_recorded"),
        "deterministic_evidence": list(preflight.get("evidence") or []),
    }
    if decision:
        fields.update(
            {
                "routing_grade": decision["grade"],
                "policy_model": decision["policy_tier"],
                "selected_model": decision["selected_tier"],
                "routing_signals": list(decision.get("signals") or []),
                "routing_reason": decision.get("reason", ""),
            }
        )
    return fields


# ---------- subagent call cap (TASK-143, RETRO §5 / STAGE-7 §7) ----------


def _counter_path(task_id: str) -> Path:
    """Return counter file path for a given TASK id (sanitized)."""
    safe = "".join(ch for ch in task_id if ch.isalnum() or ch in "-_") or "unknown"
    return SUBAGENT_COUNTER_DIR / f"{safe}.json"


def load_subagent_counter(task_id: str) -> int:
    """Return current subagent dispatch count for a TASK (0 if absent)."""
    path = _counter_path(task_id)
    if not path.exists():
        return 0
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get("count", 0))
    except (json.JSONDecodeError, ValueError, OSError):
        return 0


def increment_subagent_counter(task_id: str) -> int:
    """Increment dispatch counter for a TASK and return new value."""
    SUBAGENT_COUNTER_DIR.mkdir(parents=True, exist_ok=True)
    current = load_subagent_counter(task_id)
    new_value = current + 1
    _counter_path(task_id).write_text(
        json.dumps({"task_id": task_id, "count": new_value}, ensure_ascii=False),
        encoding="utf-8",
    )
    return new_value


def reset_subagent_counter(task_id: str) -> None:
    """Reset (delete) counter for a TASK."""
    path = _counter_path(task_id)
    if path.exists():
        path.unlink()


@dataclass(frozen=True)
class SubagentRole:
    role_id: str
    description: str
    system_prompt: str
    output_contract: str


SUBAGENT_ROLES: dict[str, SubagentRole] = {
    "scribe": SubagentRole(
        role_id="scribe",
        description="Low-cost bounded archival and runtime-state projection.",
        system_prompt=(
            "You are the SCRIBE subagent. Preserve bounded, already-established "
            "facts in the project record. Read only the evidence named by the "
            "parent, update only the requested archival or status artifacts when "
            "edits are authorized, and never invent decisions, completion, or "
            "verification. Do not expand into implementation or architecture."
        ),
        output_contract=(
            "Produce: facts archived, exact evidence references, files changed "
            "(if any), and unresolved items explicitly left open."
        ),
    ),
    "explorer": SubagentRole(
        role_id="explorer",
        description="Read-only repository inspection and bounded evidence lookup.",
        system_prompt=(
            "You are the EXPLORER subagent. Inspect the repository read-only. "
            "Use bounded searches and targeted file reads, cite paths and line "
            "numbers, and return evidence. Do not edit files, run destructive "
            "commands, or broaden the requested scope."
        ),
        output_contract=(
            "Produce: concise findings, exact evidence paths/lines, searches "
            "attempted, and any remaining uncertainty. State explicitly that "
            "no files were changed."
        ),
    ),
    "implementer": SubagentRole(
        role_id="implementer",
        description="Writes the code, tests, or docs that satisfy the task spec.",
        system_prompt=(
            "You are the IMPLEMENTER subagent. Your job is to make the change "
            "described in the task spec. Read the spec, edit the necessary "
            "files, and run the verification commands listed. Do not expand "
            "scope. Match existing style. Surface assumptions instead of "
            "guessing silently."
        ),
        output_contract=(
            "Produce: list of changed files, verification command outputs, "
            "and a short summary of decisions made. If you could not finish, "
            "say what is blocked and why."
        ),
    ),
    "reviewer": SubagentRole(
        role_id="reviewer",
        description="Reviews an implementation vs the task spec and quality bar.",
        system_prompt=(
            "You are the REVIEWER subagent. The implementer's changes are in "
            "the repo (read git status / diff). Your job is to verify: (1) "
            "does it meet the spec, (2) does it introduce regressions, (3) "
            "does it follow project conventions (AGENTS.md, CLAUDE.md). "
            "Do NOT re-implement — only review. Be specific about file paths "
            "and line numbers."
        ),
        output_contract=(
            "End with a single line: 'VERDICT: APPROVED' or "
            "'VERDICT: NEEDS_CHANGES — <one-line summary>'. Above that, list "
            "concrete issues found (file:line + reason) or 'no issues'."
        ),
    ),
    "auditor": SubagentRole(
        role_id="auditor",
        description="Independent audit per AGENTS.md §6.4 (pass / 보류 / 재검토 필요).",
        system_prompt=(
            "You are the AUDITOR subagent. Apply AGENTS.md §6.4 Independent "
            "Audit Gate: did the work meet completion criteria with "
            "verifiable evidence? You operate as a separate inference from "
            "the implementer. Do NOT trust narrative — check actual files, "
            "git diff, command outputs. Forbidden inputs: implementer's "
            "rationale, future plans (audit current evidence only)."
        ),
        output_contract=(
            "Produce a `## Independent Audit` section: 판정 (통과 / 보류 / "
            "재검토 필요), 근거 5종 이상, 보류·재검토 시 해소 조건. End with "
            "the verdict line."
        ),
    ),
    "strategist": SubagentRole(
        role_id="strategist",
        description="Strategic analysis before implementation: alternatives, tradeoffs, risks.",
        system_prompt=(
            "You are the STRATEGIST subagent. Before implementation begins, "
            "evaluate the approach: list 2-4 viable alternatives, compare "
            "them on cost / risk / scope creep, and recommend one with "
            "concrete rationale. Do not implement. Surface non-obvious "
            "tradeoffs the implementer would otherwise miss."
        ),
        output_contract=(
            "Produce: alternatives table (≥2 rows, columns cost/risk/scope), "
            "recommendation with 'why this, not the others', and the top 2 "
            "risks that would invalidate the recommendation."
        ),
    ),
    "skeptic": SubagentRole(
        role_id="skeptic",
        description="Adversarial: what could break, what's missing, what's wrong.",
        system_prompt=(
            "You are the SKEPTIC subagent. Your job is to argue AGAINST the "
            "current plan or implementation. Find edge cases that would "
            "break it, hidden assumptions, missing test coverage, and "
            "regressions the team has not considered. Be specific — vague "
            "skepticism is not useful. If you find nothing wrong, say so "
            "explicitly."
        ),
        output_contract=(
            "Produce: numbered list of concrete risks (each with reproduction "
            "scenario or file reference), plus 'severity' tag "
            "(blocking / non-blocking) per item. If list is empty, write "
            "'no objections — checked: <what you checked>'."
        ),
    ),
}


def list_roles() -> list[str]:
    return list(SUBAGENT_ROLES.keys())


def get_role(role_id: str) -> SubagentRole:
    if role_id not in SUBAGENT_ROLES:
        raise KeyError(
            f"unknown subagent role '{role_id}'. "
            f"Known: {', '.join(list_roles())}"
        )
    return SUBAGENT_ROLES[role_id]


# ---------- roles.yml integration (subagent dimension) ----------


def _strip_yaml_comment(line: str) -> str:
    """Strip trailing # comment unless inside quotes (naive)."""
    in_s = False
    in_d = False
    out: list[str] = []
    for ch in line:
        if ch == "'" and not in_d:
            in_s = not in_s
        elif ch == '"' and not in_s:
            in_d = not in_d
        if ch == "#" and not in_s and not in_d:
            break
        out.append(ch)
    return "".join(out).rstrip()


def load_roles_yml() -> dict:
    """Return parsed roles.yml as {"roles": [...]}.

    Reuses the minimal yaml shape established by agent_context_packet.py;
    we only read the fields we need (id, aliases, default_subagents).
    """
    if not ROLES_YML.exists():
        raise FileNotFoundError(f"missing role registry: {ROLES_YML}")
    raw = ROLES_YML.read_text(encoding="utf-8").splitlines()

    roles: list[dict] = []
    current: dict | None = None
    current_key: str | None = None

    for raw_line in raw:
        line = _strip_yaml_comment(raw_line)
        stripped = line.lstrip()
        if not stripped:
            current_key = None
            continue
        if stripped.startswith("- id:"):
            if current is not None:
                roles.append(current)
            current = {"id": stripped[len("- id:"):].strip()}
            current_key = None
            continue
        if current is None:
            continue
        # block-list continuation
        if stripped.startswith("- ") and current_key:
            current.setdefault(current_key, []).append(stripped[2:].strip())
            continue
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "" or value == "|":
            current_key = key
            current.setdefault(key, [])
            continue
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            current[key] = (
                [item.strip() for item in inner.split(",") if item.strip()]
                if inner
                else []
            )
            current_key = None
            continue
        current[key] = value
        current_key = None

    if current is not None:
        roles.append(current)
    return {"roles": roles}


def get_default_subagents(worker_role: str) -> list[str]:
    """Return roles.yml `default_subagents` for a worker role, or []."""
    data = load_roles_yml()
    for role in data.get("roles", []):
        if role.get("id") == worker_role or worker_role in (role.get("aliases") or []):
            ds = role.get("default_subagents") or []
            if isinstance(ds, str):
                ds = [ds]
            return [r for r in ds if r in SUBAGENT_ROLES]
    return []


# ---------- prompt rendering ----------


def render_prompt(
    role_id: str,
    task_id: str,
    intent: str,
    context_packet_path: str | None = None,
    extra_context: str | None = None,
    grade: str | None = None,
    model: str | None = None,
    changed_files: list[str] | None = None,
    diff_lines: int = 0,
    tier_route: dict | None = None,
    provider_route: dict | None = None,
) -> str:
    """Render the full dispatch prompt the parent invokes Agent tool with."""
    role = get_role(role_id)
    # Every executable prompt is role-bound.  The legacy grade/prompt resolver
    # remains available as a compatibility helper, but it may not select the
    # model used by an actual dispatch because it accepts arbitrary raw model
    # names and does not know the role's economic policy.
    tier = dict(
        tier_route
        or model_routing.resolve_subagent_tier(
            role_id,
            requested_tier=model or "auto",
        )
    )
    route = dict(
        provider_route
        or model_routing.resolve_provider_route(
            "native-codex",
            tier["selected_tier"],
            requested_tier=tier["requested_tier"],
        )
    )
    parts: list[str] = [
        f"# Subagent dispatch — role={role.role_id} task={task_id}",
        "",
        f"## System prompt",
        role.system_prompt,
        "",
        f"## Intent",
        intent,
        "",
        f"## Output contract",
        role.output_contract,
        "",
    ]
    triggers = ",".join(tier.get("escalation_triggers") or []) or "-"
    parts.extend([
        "## Model routing",
        (
            f"provider={route.get('provider') or 'unverified'} "
            f"surface={route.get('execution_surface') or 'unverified'}"
        ),
        (
            f"requested_pm_tier={route.get('requested_tier')} "
            f"selected_pm_tier={route.get('selected_tier')} "
            f"provider_tier={route.get('provider_tier')}"
        ),
        (
            f"resolved_request_model={route.get('resolved_model')} "
            f"reasoning_effort={route.get('reasoning_effort')} "
            f"route_status={route.get('route_status')}"
        ),
        (
            f"escalation_triggers={triggers} "
            f"reason={tier.get('reason') or 'provider-aware route'}"
        ),
        (
            "The resolved request model is configuration intent; the "
            "observed model remains unverified until completion."
        ),
        "",
    ])
    if context_packet_path:
        parts.append("## Context packet")
        parts.append(f"Read this file first: `{context_packet_path}`")
        parts.append("")
    if extra_context:
        parts.append("## Additional context")
        parts.append(extra_context)
        parts.append("")
    parts.append("## Operating rules")
    parts.append(
        "- Stay within the role's responsibility (do not switch personas).\n"
        "- Cite file paths and line numbers when referencing code.\n"
        "- End with the role's required final line (see output contract)."
    )
    return "\n".join(parts).rstrip() + "\n"


# ---------- message emission ----------


def _now_iso() -> str:
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def _new_msg_id(when: _dt.datetime | None = None) -> str:
    w = when or _dt.datetime.now()
    return (
        f"MSG-{w.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    )


def emit_call_message(
    role_id: str,
    task_id: str,
    intent: str,
    sender: str = "lead-engineer",
    evidence: list[str] | None = None,
    next_items: list[str] | None = None,
    routing: dict | None = None,
    tier_route: dict | None = None,
    provider_route: dict | None = None,
    dispatch_id: str | None = None,
    claim_id: str | None = None,
    task_token_budget: int | str | None = None,
    claim_token_budget: int | str | None = None,
    workload_id: str | None = None,
    baseline_receipt_id: str | None = None,
    dry_run: bool = False,
) -> Path:
    """Write a subagent_call message to agents/messages/inbox/."""
    get_role(role_id)  # validates role_id early
    effective_tier = dict(
        tier_route
        or model_routing.resolve_subagent_tier(
            role_id,
            requested_tier=(
                (routing or {}).get("selected_tier") or "auto"
            ),
            escalation_triggers=(
                (routing or {}).get("escalation_triggers")
                or (routing or {}).get("signals")
                or []
            ),
        )
    )
    effective_provider = dict(
        provider_route
        or model_routing.resolve_provider_route(
            "native-codex",
            effective_tier["selected_tier"],
            requested_tier=effective_tier["requested_tier"],
        )
    )
    msg_id = _new_msg_id()
    ts = _now_iso()
    front = [
        "---",
        f"id: {msg_id}",
        f"from: {sender}",
        f"to: subagent-{role_id}",
        f"task_id: {task_id}",
        f"intent: {intent}",
        "type: subagent_call",
        "status: open",
        f"ts: {ts}",
        "in_reply_to:",
        f"dispatch_id: {str(dispatch_id or '').strip() or msg_id}",
    ]
    normalized_claim = str(claim_id or "").strip()
    if normalized_claim:
        front.append(f"claim_id: {normalized_claim}")
    for key, value in (
        ("task_token_budget", task_token_budget),
        ("claim_token_budget", claim_token_budget),
    ):
        if value in (None, ""):
            continue
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be a non-negative integer") from exc
        if parsed < 0:
            raise ValueError(f"{key} must be a non-negative integer")
        front.append(f"{key}: {parsed}")
    normalized_workload = str(workload_id or "").strip()
    if normalized_workload:
        front.append(f"eval_workload_id: {normalized_workload}")
    normalized_baseline = str(baseline_receipt_id or "").strip()
    if normalized_baseline:
        front.append(f"eval_baseline_receipt_id: {normalized_baseline}")
    ev = evidence or []
    if ev:
        front.append("evidence:")
        for item in ev:
            front.append(f"  - {item}")
    else:
        front.append("evidence: []")
    nx = next_items or []
    if nx:
        front.append("next:")
        for item in nx:
            front.append(f"  - {item}")
    else:
        front.append("next: []")
    if effective_provider:
        route = effective_provider
        tier = effective_tier
        front.append(f"provider: {route.get('provider') or 'unverified'}")
        front.append(
            f"execution_surface: {route.get('execution_surface') or 'unverified'}"
        )
        front.append(
            f"requested_model_tier: {route.get('requested_tier') or 'unverified'}"
        )
        front.append(
            f"selected_model_tier: {route.get('selected_tier') or 'unverified'}"
        )
        front.append(
            f"resolved_model: {route.get('resolved_model') or 'unverified'}"
        )
        front.append(
            f"routing_status: {route.get('route_status') or 'unverified'}"
        )
        front.append(
            f"reasoning_effort: {route.get('reasoning_effort') or 'unverified'}"
        )
        front.append(
            f"reasoning_source: {route.get('reasoning_source') or 'unverified'}"
        )
        front.append(
            f"role_policy_id: {tier.get('role_policy_id') or 'unverified'}"
        )
        front.append(
            "role_policy_status: "
            f"{tier.get('role_policy_status') or 'unverified'}"
        )
        front.append(
            "high_tier_authorized: "
            f"{str(tier.get('high_tier_authorized')).lower()}"
        )
        front.append(
            "registered_escalation_reason: "
            f"{tier.get('registered_escalation_reason') or 'none'}"
        )
        triggers = [
            str(item).strip()
            for item in (tier.get("escalation_triggers") or [])
            if str(item).strip()
        ]
        if triggers:
            front.append("escalation_triggers:")
            for trigger in triggers:
                front.append(f"  - {trigger}")
        else:
            front.append("escalation_triggers: []")
    front.append("---")
    body = (
        f"\nSubagent role: **{role_id}** — {SUBAGENT_ROLES[role_id].description}\n"
        f"\nDispatched for {task_id}. See render_prompt() output for the full "
        f"prompt; this message records the dispatch as evidence.\n"
    )
    text = "\n".join(front) + body
    target = MESSAGES_INBOX / f"{msg_id}.md"
    if not dry_run:
        MESSAGES_INBOX.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return target


def emit_reply_message(
    parent_id: str,
    role_id: str,
    task_id: str,
    verdict: str,
    sender: str = "lead-engineer",
    summary: str = "",
    evidence: list[str] | None = None,
    dry_run: bool = False,
) -> Path:
    """Write a subagent_reply message in archive lifecycle position.

    Reply lifecycle: type=subagent_reply, status=answered, in_reply_to=parent.
    """
    get_role(role_id)
    msg_id = _new_msg_id()
    ts = _now_iso()
    front = [
        "---",
        f"id: {msg_id}",
        f"from: subagent-{role_id}",
        f"to: {sender}",
        f"task_id: {task_id}",
        f"intent: subagent reply ({role_id})",
        "type: subagent_reply",
        "status: answered",
        f"ts: {ts}",
        f"in_reply_to: {parent_id}",
    ]
    ev = evidence or []
    if ev:
        front.append("evidence:")
        for item in ev:
            front.append(f"  - {item}")
    else:
        front.append("evidence: []")
    front.append("next: []")
    front.append("---")
    body = f"\nVERDICT: {verdict}\n"
    if summary:
        body += f"\n{summary}\n"
    text = "\n".join(front) + body
    target = MESSAGES_INBOX / f"{msg_id}.md"
    if not dry_run:
        MESSAGES_INBOX.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    return target


def emit_event(
    role_id: str,
    task_id: str,
    kind: str,
    extra: dict | None = None,
    dry_run: bool = False,
) -> Path:
    """Append an event JSONL line to agents/runtime/events/subagent-YYYY-MM-DD.jsonl."""
    if kind not in {"dispatch", "reply", "verdict"}:
        raise ValueError(f"unknown event kind '{kind}'")
    now = _dt.datetime.now().astimezone()
    record: dict = {
        "ts": now.isoformat(timespec="seconds"),
        "kind": kind,
        "role": role_id,
        "task_id": task_id,
    }
    if extra:
        record.update(extra)
    target = EVENTS_DIR / f"subagent-{now.strftime('%Y-%m-%d')}.jsonl"
    if not dry_run:
        EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return target


# ---------- CLI ----------


def _display(path: Path) -> str:
    """Repo-relative path when possible, else str(path)."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _cmd_list_roles(args: argparse.Namespace) -> int:
    for r in SUBAGENT_ROLES.values():
        print(f"{r.role_id:<11}  {r.description}")
    return 0


def _cmd_for_worker(args: argparse.Namespace) -> int:
    try:
        defaults = get_default_subagents(args.for_worker)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not defaults:
        print(f"(no default_subagents declared for worker '{args.for_worker}')")
        return 0
    for r in defaults:
        print(r)
    return 0


def _cmd_dispatch(args: argparse.Namespace) -> int:
    preflight = model_routing.deterministic_preflight(
        args.intent,
        status=args.preflight_status,
        evidence=args.preflight_evidence,
    )
    if args.emit_call and not preflight["allow_dispatch"]:
        if preflight["status"] == "completed_sufficient":
            print(
                "[dispatch] deterministic work completed sufficiently; "
                "no model call emitted"
            )
            return 0
        print(
            f"ERROR: model dispatch blocked: {preflight['reason']}",
            file=sys.stderr,
        )
        return 2
    try:
        role_route = model_routing.resolve_subagent_tier(
            args.role,
            requested_tier=args.pm_tier or args.model,
            escalation_triggers=args.escalation_trigger,
        )
        provider_route = model_routing.resolve_provider_route(
            args.provider or "native-codex",
            role_route["selected_tier"],
            requested_tier=role_route["requested_tier"],
        )
        prompt = render_prompt(
            role_id=args.role,
            task_id=args.task_id,
            intent=args.intent,
            context_packet_path=args.context_packet,
            extra_context=None,
            grade=args.grade,
            model=args.model,
            changed_files=args.changed_file,
            diff_lines=args.diff_lines,
            tier_route=role_route,
            provider_route=provider_route,
        )
    except (KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    routing_decision = role_route
    print(prompt)
    if args.emit_call:
        # Cap check (TASK-143, RETRO §5 / STAGE-7 §7) — runs before write.
        if args.max_subagents_per_task and args.max_subagents_per_task > 0:
            current = load_subagent_counter(args.task_id)
            if current >= args.max_subagents_per_task:
                print(
                    f"ERROR: subagent cap reached for {args.task_id}: "
                    f"{current}/{args.max_subagents_per_task}. "
                    f"Reset with --reset-counter or raise --max-subagents-per-task.",
                    file=sys.stderr,
                )
                return 2
            if not args.dry_run:
                new_value = increment_subagent_counter(args.task_id)
                print(
                    f"[cap] {args.task_id} dispatch count: "
                    f"{new_value}/{args.max_subagents_per_task}"
                )
        msg_path = emit_call_message(
            role_id=args.role,
            task_id=args.task_id,
            intent=args.intent,
            sender=args.sender,
            evidence=args.evidence or [],
            routing=routing_decision,
            tier_route=role_route,
            provider_route=provider_route,
            dispatch_id=args.dispatch_id,
            claim_id=args.claim_id,
            task_token_budget=args.task_token_budget,
            claim_token_budget=args.claim_token_budget,
            workload_id=args.workload_id,
            baseline_receipt_id=args.baseline_receipt_id,
            dry_run=args.dry_run,
        )
        effective_dispatch_id = args.dispatch_id or msg_path.stem
        evt_path = emit_event(
            role_id=args.role,
            task_id=args.task_id,
            kind="dispatch",
            extra={
                "message_id": msg_path.stem,
                "intent": args.intent,
                **routing_event_fields(
                    routing_decision,
                    dispatch_id=effective_dispatch_id,
                    provider=args.provider,
                    route={**role_route, **dict(provider_route or {})},
                    preflight=preflight,
                ),
            },
            dry_run=args.dry_run,
        )
        kind_word = "would write" if args.dry_run else "wrote"
        print(f"\n[dispatch] {kind_word} {_display(msg_path)}")
        print(f"[dispatch] {kind_word} event to {_display(evt_path)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="subagent_dispatch.py",
        description="Stage 7-A subagent dispatch helper (TASK-116).",
    )
    p.add_argument(
        "--role",
        choices=list_roles(),
        help="Subagent role to dispatch (7 standard roles).",
    )
    p.add_argument("--task-id", help="Related TASK id, e.g. TASK-116.")
    p.add_argument("--intent", help="One-line dispatch intent.")
    p.add_argument(
        "--context-packet",
        help="Path to a context packet (see scripts/agent_context_packet.py).",
    )
    p.add_argument(
        "--model",
        default="auto",
        choices=sorted(
            {"auto", "haiku", "sonnet", "opus"}
            | set(model_routing.ALLOWED_PM_TIERS)
        ),
        help="Role-bound PM/compatibility tier (default: auto); raw model names are rejected.",
    )
    p.add_argument(
        "--provider",
        default="native-codex",
        help="Execution provider/surface for auditable resolution (for example native-codex)",
    )
    p.add_argument(
        "--pm-tier",
        choices=sorted(model_routing.ALLOWED_PM_TIERS),
        help="Requested provider-neutral PM tier; role default when omitted",
    )
    p.add_argument(
        "--escalation-trigger",
        action="append",
        default=[],
        help="Registered task/unit risk signal used for PM-tier escalation",
    )
    p.add_argument(
        "--preflight-status",
        choices=sorted(model_routing.PREFLIGHT_STATUSES),
        help="Deterministic-first result for lookup-only dispatch",
    )
    p.add_argument(
        "--preflight-evidence",
        action="append",
        default=[],
        help="Bounded deterministic attempt evidence (repeatable)",
    )
    p.add_argument(
        "--grade",
        default="Medium",
        help="Task grade used when --model=auto (default: Medium).",
    )
    p.add_argument(
        "--changed-file",
        action="append",
        help="Changed file path used by model routing (repeatable).",
    )
    p.add_argument(
        "--diff-lines",
        type=int,
        default=0,
        help="Approximate changed line count used by model routing.",
    )
    p.add_argument(
        "--sender",
        default="lead-engineer",
        help="Worker role that owns the dispatch (default: lead-engineer).",
    )
    p.add_argument(
        "--dispatch-id",
        help="Stable dispatch identity; defaults to the emitted message id.",
    )
    p.add_argument(
        "--claim-id",
        help="Canonical task-claim identity carried into the inbox contract.",
    )
    p.add_argument(
        "--task-token-budget",
        type=int,
        help="Optional non-negative task token budget carried into the message.",
    )
    p.add_argument(
        "--claim-token-budget",
        type=int,
        help="Optional non-negative claim token budget carried into the message.",
    )
    p.add_argument(
        "--workload-id",
        help="Comparable evaluation workload identity.",
    )
    p.add_argument(
        "--baseline-receipt-id",
        help="Immutable baseline execution receipt identity.",
    )
    p.add_argument(
        "--evidence",
        action="append",
        help="Path or URL referenced as evidence (repeatable).",
    )
    p.add_argument(
        "--emit-call",
        action="store_true",
        help="Write a subagent_call message + dispatch event (default: render only).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Render and resolve paths but do not write files.",
    )
    p.add_argument(
        "--list-roles",
        action="store_true",
        help="List the 7 standard subagent roles.",
    )
    p.add_argument(
        "--for-worker",
        help="Print roles.yml default_subagents for the given worker role.",
    )
    p.add_argument(
        "--max-subagents-per-task",
        type=int,
        default=0,
        help="Cap on subagent dispatches per TASK (0 = unlimited). "
        "When the counter (agents/runtime/subagent-counter/<task>.json) reaches the cap, "
        "--emit-call fails with exit 2. TASK-143 / STAGE-7 §7.",
    )
    p.add_argument(
        "--reset-counter",
        action="store_true",
        help="Reset subagent counter for the given --task-id and exit 0.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.list_roles:
        return _cmd_list_roles(args)
    if args.for_worker:
        return _cmd_for_worker(args)
    if args.reset_counter:
        if not args.task_id:
            print("ERROR: --reset-counter requires --task-id", file=sys.stderr)
            return 2
        reset_subagent_counter(args.task_id)
        print(f"[cap] reset counter for {args.task_id}")
        return 0
    if not args.role or not args.task_id or not args.intent:
        print(
            "ERROR: --role, --task-id, and --intent are required "
            "(or use --list-roles / --for-worker).",
            file=sys.stderr,
        )
        return 2
    return _cmd_dispatch(args)


if __name__ == "__main__":
    raise SystemExit(main())
