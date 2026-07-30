#!/usr/bin/env python3
"""Bounded synchronous auto-dispatch runner (TASK-208, CYCLE-076).

Stage-7 auto-dispatch that is runaway-proof *by construction* — the Owner's
hard requirement (past incident: an unbounded background loop wasted tokens).

Why this design has no runaway/orphan/race surface:
  - SINGLE process, SYNCHRONOUS: each provider.run() is awaited and its result
    collected before the next dispatch — no fire-and-forget, so no orphaned
    agent can keep billing after the runner moves on.
  - PERSISTENT task/claim budget: immutable execution receipts are re-read
    before each call, so cumulative usage survives a process restart. The
    append-only ledger uses an exclusive lock and rejects duplicate dispatch
    ids.
  - Layered on the CYCLE-075 guardrails: each provider.run() is itself bounded
    by DISPATCH_PER_CALL_CAP, and get_provider() refuses billable providers
    unless DISPATCH_ENABLE_LIVE=1. So even one dispatch cannot run away, and
    accidental live spend is blocked.

Halt is checked BEFORE every dispatch, on the FIRST of:
  - session token budget exhausted,
  - max_dispatches reached,
  - a stop file present (agents/runtime/STOP_LOOP or .orchestrator-stop),
  - work list exhausted.

The session-budget check is *cumulative and pre-call*: before every provider
call, the runner compares remaining session budget with the provider's
worst-case per-dispatch ceiling. If the next call cannot fit, it is skipped
without spend. Routed agent providers expose `per_dispatch_cap`; providers that
do not expose a ceiling are allowed only when no task/claim budget is
configured; configured durable budgets fail closed when the ceiling is
unknown.

Default provider is 'dummy' (zero cost). Usage:
  python scripts/auto_dispatch.py --demo                 # dummy, safe
  python scripts/auto_dispatch.py --demo --max-dispatches 3 --session-budget 500
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:  # Windows 콘솔 cp949 에서도 한글 stdout 안전
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from providers import get_provider  # noqa: E402
import model_routing  # noqa: E402
import eval_harness  # noqa: E402
from message_queue import (  # noqa: E402
    claim_message as lease_claim_message,
    mark_answered as lease_mark_answered,
    has_active_claim,
    current_claim_token,
    _has_reply,
    parse_frontmatter,
)
from agent_worker import (  # noqa: E402
    append_event,
    write_reply,
    _completion_observation,
    _provider_routing_event_fields,
    _route_with_observation,
)

RUNTIME_DIR = REPO_ROOT / "agents" / "runtime"
EVENTS_DIR = RUNTIME_DIR / "events"
STOP_LOOP_FILE = RUNTIME_DIR / "STOP_LOOP"
ORCHESTRATOR_STOP_FILE = REPO_ROOT / ".orchestrator-stop"
DEFAULT_STOP_FILES = (STOP_LOOP_FILE, ORCHESTRATOR_STOP_FILE)

# Conservative defaults — anti-runaway first. Override via CLI.
DEFAULT_SESSION_BUDGET = 200_000
DEFAULT_MAX_DISPATCHES = 10


def _routing_decision_for_item(item: dict, instruction: str) -> dict | None:
    context = dict(item.get("context", {}) or {})
    model = item.get("routing_model") or context.get("routing_model") or context.get("model")
    triggers = (
        item.get("escalation_triggers")
        or context.get("escalation_triggers")
        or item.get("routing_escalation_triggers")
        or context.get("routing_escalation_triggers")
        or []
    )
    role = str(item.get("role") or context.get("role") or "worker").strip()
    if role.lower().startswith("subagent-"):
        role = role[len("subagent-"):]
    return model_routing.resolve_subagent_tier(
        role,
        requested_tier=str(model or "auto"),
        escalation_triggers=triggers,
    )


def _apply_routing_to_provider(
    provider,
    provider_name: str,
    decision: dict | None,
    *,
    baseline_model: str | None = None,
    baseline_reasoning_effort: str | None = None,
) -> dict | None:
    if not decision:
        return None
    route = model_routing.resolve_provider_route(
        provider_name,
        decision["selected_tier"],
        requested_tier=(
            decision.get("requested_tier") or decision.get("policy_tier")
        ),
        baseline_model=baseline_model,
        baseline_reasoning_effort=baseline_reasoning_effort,
    )
    for name, value in dict(route.get("provider_env") or {}).items():
        import os
        os.environ[name] = value
        if name in ("CLAUDE_AGENT_MODEL", "CODEX_PROVIDER_MODEL") and hasattr(provider, "model"):
            setattr(provider, "model", value)
    return route


def _routing_result_fields(
    decision: dict | None,
    route: dict | None,
    observation: dict,
    *,
    dispatch_id: str,
) -> dict:
    return _provider_routing_event_fields(
        decision,
        route,
        observation,
        dispatch_id=dispatch_id,
    )


def _positive_int(value) -> int | None:
    try:
        parsed = int(value or 0)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _eval_baseline_tokens(item: dict) -> int | None:
    context = dict(item.get("context", {}) or {})
    return (
        _positive_int(item.get("eval_baseline_tokens"))
        or _positive_int(item.get("baseline_tokens"))
        or _positive_int(context.get("eval_baseline_tokens"))
        or _positive_int(context.get("baseline_tokens"))
    )


def _eval_baseline_model(item: dict) -> str | None:
    context = dict(item.get("context", {}) or {})
    for value in (
        item.get("eval_baseline_model"),
        item.get("baseline_model"),
        context.get("eval_baseline_model"),
        context.get("baseline_model"),
    ):
        model = str(value or "").strip()
        if model:
            return model
    return None


def _item_context_value(item: dict, *keys: str):
    context = dict(item.get("context", {}) or {})
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
        value = context.get(key)
        if value not in (None, ""):
            return value
    return None


def _eval_baseline_reasoning(item: dict) -> str | None:
    value = _item_context_value(
        item,
        "eval_baseline_reasoning_effort",
        "baseline_reasoning_effort",
    )
    return str(value or "").strip() or None


def _eval_baseline_observation_status(item: dict) -> str:
    value = _item_context_value(
        item,
        "eval_baseline_observation_status",
        "baseline_observation_status",
    )
    if value not in (None, ""):
        return str(value).strip()
    return "configured" if _eval_baseline_model(item) else "unavailable"


def _budget_value(item: dict, key: str) -> int | str | None:
    return _item_context_value(item, key)


def _claim_id(item: dict) -> str | None:
    value = _item_context_value(item, "claim_id")
    return str(value or "").strip() or None


def _baseline_receipt_id(item: dict) -> str | None:
    value = _item_context_value(
        item,
        "eval_baseline_receipt_id",
        "baseline_receipt_id",
    )
    return str(value or "").strip() or None


def _workload_id(item: dict) -> str | None:
    value = _item_context_value(item, "eval_workload_id", "workload_id")
    return str(value or "").strip() or None


def _item_task_id(item: dict, dispatch_id: str) -> str:
    value = _item_context_value(item, "task_id")
    task_id = str(value or "").strip()
    if task_id and task_id.lower() not in {"none", "unknown", "null"}:
        return task_id
    return str(dispatch_id)


def _optional_nonnegative_float(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) and parsed >= 0 else None


def _not_dispatched_observation() -> dict:
    return {
        "observed_provider": None,
        "observed_model": None,
        "observed_reasoning_effort": None,
        "model_observation_status": "unverified",
        "token_usage_status": "not_dispatched",
        "tokens_in": None,
        "tokens_out": None,
        "latency_status": "unavailable",
        "latency_ms": None,
        "billed_cost_status": "unavailable",
        "billed_cost": None,
        "currency": None,
    }


def _eval_baseline_cost(item: dict) -> tuple[float | None, str | None]:
    context = dict(item.get("context", {}) or {})
    cost = None
    for value in (
        item.get("eval_baseline_billed_cost"),
        item.get("baseline_billed_cost"),
        context.get("eval_baseline_billed_cost"),
        context.get("baseline_billed_cost"),
    ):
        cost = _optional_nonnegative_float(value)
        if cost is not None:
            break
    currency = None
    for value in (
        item.get("eval_baseline_currency"),
        item.get("baseline_currency"),
        context.get("eval_baseline_currency"),
        context.get("baseline_currency"),
    ):
        currency = str(value or "").strip().upper() or None
        if currency:
            break
    if cost is None or currency is None:
        return None, None
    return cost, currency


def _metadata_task_id(meta: dict, fallback: str | None = None) -> str:
    task_id = str(meta.get("task_id") or "").strip()
    if task_id and task_id.lower() not in {"none", "unknown", "null"}:
        return task_id
    return str(fallback or meta.get("id") or "none")


def _routing_eval_skip_reason(
    routing_decision: dict | None,
    route: dict | None,
    observation: dict,
    *,
    baseline_tokens: int | None,
    baseline_model: str | None,
    baseline_observation_status: str,
) -> str | None:
    if not routing_decision or not route:
        return "routing_not_resolved"
    if not observation.get("observed_model"):
        return "model_observation_unavailable"
    if route.get("application_status") != "applied":
        return "routing_not_applied"
    if route.get("route_changed") is not True:
        return "route_not_effective"
    if not baseline_model:
        return "baseline_model_unavailable"
    if baseline_observation_status != "observed":
        return "baseline_observation_unavailable"
    if observation.get("token_usage_status") != "observed":
        return "token_usage_unavailable"
    if baseline_tokens is None:
        return "baseline_usage_unavailable"
    return None


def _record_execution_receipt(
    item: dict,
    provider_name: str,
    routing_decision: dict | None,
    route: dict | None,
    observation: dict,
    finish_reason: str,
    error,
    eval_log_path: Path | None,
    *,
    dispatch_id: str,
    role: str,
    status: str,
    source: str,
    budget_preflight_result: dict | None = None,
) -> tuple[bool, str | None]:
    baseline = _eval_baseline_tokens(item)
    baseline_model = _eval_baseline_model(item)
    baseline_reasoning = _eval_baseline_reasoning(item)
    baseline_observation = _eval_baseline_observation_status(item)
    context = dict(item.get("context", {}) or {})
    baseline_cost, baseline_currency = _eval_baseline_cost(item)
    task_id = _item_task_id(item, dispatch_id)
    try:
        receipt = eval_harness.record_execution_receipt(
            dispatch_id=dispatch_id,
            task_id=task_id,
            claim_id=_claim_id(item),
            role=role,
            workload_id=_workload_id(item),
            provider=provider_name,
            execution_surface=(
                route.get("execution_surface") if route else "provider_worker"
            ),
            requested_tier=route.get("requested_tier") if route else None,
            selected_tier=route.get("selected_tier") if route else None,
            resolved_model=route.get("resolved_model") if route else None,
            resolved_reasoning_effort=(
                route.get("reasoning_effort") if route else None
            ),
            resolved_model_source=(
                route.get("model_source") if route else "unavailable"
            ),
            resolved_reasoning_source=(
                route.get("reasoning_source") if route else "unavailable"
            ),
            observed_provider=observation.get("observed_provider"),
            observed_model=observation.get("observed_model"),
            observed_reasoning_effort=observation.get(
                "observed_reasoning_effort"
            ),
            token_usage_status=observation.get("token_usage_status"),
            tokens_in=observation.get("tokens_in"),
            tokens_out=observation.get("tokens_out"),
            billed_cost_status=observation.get("billed_cost_status"),
            billed_cost=observation.get("billed_cost"),
            currency=observation.get("currency"),
            source=source,
            status=status,
            error=str(error or "").strip() or None,
            route_status=route.get("route_status") if route else None,
            application_status=(
                route.get("application_status") if route else None
            ),
            model_changed=route.get("model_changed") if route else None,
            route_changed=route.get("route_changed") if route else None,
            baseline_receipt_id=_baseline_receipt_id(item),
            baseline_model=baseline_model,
            baseline_reasoning_effort=baseline_reasoning,
            baseline_observation_status=baseline_observation,
            baseline_tokens=baseline,
            baseline_billed_cost=baseline_cost,
            baseline_currency=baseline_currency,
            grade=(
                routing_decision.get("grade") if routing_decision else "?"
            ),
            policy_model=(
                routing_decision.get("policy_tier")
                if routing_decision
                else None
            ),
            selected_model=(
                routing_decision.get("selected_tier")
                if routing_decision
                else None
            ),
            routing_signals=(
                list(routing_decision.get("signals") or [])
                if routing_decision
                else []
            ),
            budget_preflight_result=budget_preflight_result,
            path=eval_log_path or eval_harness.EVAL_LOG,
            finish_reason=str(finish_reason or "stop"),
        )
    except eval_harness.ReceiptConflictError:
        return False, "duplicate_dispatch_id"
    except eval_harness.ReceiptIntegrityError:
        return False, "receipt_ledger_untrusted"
    skip_reason = _routing_eval_skip_reason(
        routing_decision,
        route,
        observation,
        baseline_tokens=receipt.get("baseline_tokens"),
        baseline_model=receipt.get("baseline_model"),
        baseline_observation_status=(
            "observed"
            if receipt.get("baseline_reference_status") == "verified"
            else str(receipt.get("baseline_reference_reason") or "unavailable")
        ),
    )
    return True, skip_reason


@dataclass
class SessionBudget:
    """In-memory cumulative token budget for one runner process.

    This fast local counter supplements, but never replaces, the durable
    task/claim budget enforced through execution receipts. `remaining()` never
    goes negative; `exhausted()` is the halt signal.
    """

    total: int
    spent: int = 0

    def remaining(self) -> int:
        return max(0, self.total - self.spent)

    def exhausted(self) -> bool:
        return self.spent >= self.total

    def record(self, tokens: int) -> None:
        # Spend is monotonic; clamp negatives defensively.
        self.spent += max(0, int(tokens))


def _provider_dispatch_ceiling(provider) -> int | None:
    """Return provider worst-case tokens for one run(), when known."""
    for attr in ("per_dispatch_cap", "tokens_per_call"):
        value = getattr(provider, attr, None)
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            continue
        if parsed > 0:
            return parsed
    return None


def _budget_skip_result(index: int, role: str, budget: SessionBudget,
                        ceiling: int | None) -> dict:
    result = {
        "index": index,
        "role": role,
        "tokens": 0,
        "finish_reason": "skipped",
        "error": "budget_insufficient",
        "remaining_budget": budget.remaining(),
    }
    if ceiling is not None:
        result["provider_dispatch_ceiling"] = ceiling
    return result


def _stop_file_present(stop_files) -> Path | None:
    for p in stop_files:
        try:
            if Path(p).exists():
                return Path(p)
        except Exception:
            continue
    return None


def _claim_source(path: Path, role: str | None = None):
    """Re-read a source message fresh and atomically claim open->claimed, using
    the same primitive agent_worker uses. Returns (meta, body) on success, or
    None if it is no longer claimable (already taken / not open / unreadable).

    Re-reading fresh (not trusting the stale snapshot) is what stops an old work
    list from overwriting a message a worker changed since the scan. The residual
    check-then-write window is identical to agent_worker.claim_message's — this
    serializes with a concurrent worker, it does not add a stronger guarantee.
    """
    try:
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not meta or meta.get("status") != "open":
        return None
    if not lease_claim_message(path, meta, body, role=role):
        return None
    return meta, body


def _write_back_reply(role: str, src_meta: dict, reply_text: str, source_path: Path):
    """Write the dispatch reply into the source inbox and mark the original
    answered, reusing agent_worker's primitives so the lifecycle is identical to
    a real worker's (open->claimed->answered + a reply message).

    Returns the reply Path, or None if the reply write itself failed. The two
    steps are independent: if the reply is written but the status flip raises
    (an IO error), the reply is still returned (accounting stays correct) and the
    message is left at 'claimed' — the same best-effort the real worker gives
    (agent_worker only logs a WARN on a failed mark_answered). So the orphan-free
    guarantee covers provider errors, not a write-side IO failure on the flip."""
    claim_identity = {"role": role}
    token = current_claim_token(source_path)
    if token is not None:
        claim_identity["token"] = token

    if not has_active_claim(source_path, role=role, worker_identity=claim_identity):
        return None
    if _has_reply(src_meta["id"], source_path.parent):
        try:
            lease_mark_answered(source_path, role=role, worker_identity=claim_identity)
        except Exception:
            pass
        return None

    try:
        reply_path = write_reply(role, src_meta, reply_text, inbox=source_path.parent)
    except Exception:
        return None
    if not has_active_claim(source_path, role=role, worker_identity=claim_identity):
        return None
    try:
        lease_mark_answered(source_path, role=role, worker_identity=claim_identity)
    except Exception:
        pass  # reply already written; failed flip leaves 'claimed' (worker-equivalent)
    return reply_path


def run_bounded_dispatch(
    work_items: list[dict],
    provider_name: str = "dummy",
    *,
    session_budget: int = DEFAULT_SESSION_BUDGET,
    max_dispatches: int = DEFAULT_MAX_DISPATCHES,
    stop_files=DEFAULT_STOP_FILES,
    write_back: bool = False,
    eval_log_path: Path | None = None,
    events_dir: Path | None = None,
    out=None,
) -> dict:
    """Dispatch each work item synchronously under hard bounds.

    work_items: list of {"role", "instruction", "context"?} dicts.
    Returns a summary dict: dispatched count, halt_reason, spent, per-item results.
    Never raises on a provider error — it is captured per item so one bad
    dispatch cannot abort accounting (and cannot orphan).

    write_back (TASK-212, default off → read-only as in CYCLE-078): for items that
    carry a "_source_path" (inbox snapshots), claim the source BEFORE the billable
    call, then write the provider's reply back and mark the original answered. The
    claim-before-dispatch order keeps the anti-waste invariant — a lost claim means
    no provider call and so no spend. A provider error still writes an error reply
    so a claimed message is never left orphaned.
    """
    out = out if out is not None else sys.stdout
    events_dir = EVENTS_DIR if events_dir is None else Path(events_dir)
    provider = get_provider(provider_name)  # live-gate enforced here (CYCLE-075)
    budget = SessionBudget(total=session_budget)
    results: list[dict] = []
    halt_reason = "work_exhausted"

    for i, item in enumerate(work_items):
        # --- halt checks BEFORE any billable call ---
        if i >= max_dispatches:
            halt_reason = f"max_dispatches ({max_dispatches})"
            break
        stop = _stop_file_present(stop_files)
        if stop is not None:
            halt_reason = f"stop_file ({stop.name})"
            break

        role = str(item.get("role", "worker"))
        instruction = str(item.get("instruction", ""))
        context = dict(item.get("context", {}) or {})
        dispatch_id = str(
            item.get("dispatch_id")
            or context.get("dispatch_id")
            or f"dispatch-{uuid.uuid4().hex[:12]}"
        )
        source = item.get("_source_path") if write_back else None
        if budget.exhausted():
            halt_reason = f"session_budget ({budget.total})"
            break
        baseline_model = _eval_baseline_model(item)
        baseline_reasoning = _eval_baseline_reasoning(item)
        dispatch_ceiling = _provider_dispatch_ceiling(provider)
        receipt_path = Path(eval_log_path or eval_harness.EVAL_LOG)
        task_id = _item_task_id(item, dispatch_id)
        try:
            routing_decision = _routing_decision_for_item(item, instruction)
            planned_route = _apply_routing_to_provider(
                provider,
                provider_name,
                routing_decision,
                baseline_model=baseline_model,
                baseline_reasoning_effort=baseline_reasoning,
            )
        except (KeyError, ValueError) as exc:
            observation = _not_dispatched_observation()
            error = f"routing_policy_rejected: {exc}"
            receipt_recorded, receipt_skip_reason = _record_execution_receipt(
                item,
                provider_name,
                None,
                None,
                observation,
                "skipped",
                error,
                receipt_path,
                dispatch_id=dispatch_id,
                role=role,
                status="skipped",
                source="routing_policy",
            )
            skipped = {
                "index": i,
                "role": role,
                "tokens": 0,
                "finish_reason": "skipped",
                "error": error,
                "budget_preflight": None,
                "eval_recorded": receipt_recorded,
                "receipt_recorded": receipt_recorded,
                "eval_skip_reason": receipt_skip_reason,
                **_routing_result_fields(
                    None,
                    None,
                    observation,
                    dispatch_id=dispatch_id,
                ),
            }
            results.append(skipped)
            append_event(
                events_dir,
                role,
                "auto_dispatch_skipped",
                provider=provider_name,
                dispatch_status="skipped",
                **{key: value for key, value in skipped.items() if key != "role"},
            )
            continue
        try:
            persistent_preflight = eval_harness.reserve_dispatch_budget(
                path=receipt_path,
                root=REPO_ROOT,
                task_id=task_id,
                claim_id=_claim_id(item),
                dispatch_id=dispatch_id,
                dispatch_ceiling=dispatch_ceiling,
                task_token_budget=_budget_value(item, "task_token_budget"),
                claim_token_budget=_budget_value(item, "claim_token_budget"),
                source="auto_dispatch",
            )
        except eval_harness.ReceiptIntegrityError as exc:
            persistent_preflight = {
                "allowed": False,
                "reason": "receipt_ledger_untrusted",
                "dispatch_id": dispatch_id,
                "error": str(exc),
            }
        if not persistent_preflight["allowed"]:
            halt_reason = f"durable_budget ({persistent_preflight['reason']})"
            observation = _not_dispatched_observation()
            receipt_recorded = False
            receipt_skip_reason = persistent_preflight["reason"]
            if persistent_preflight["reason"] != "duplicate_dispatch_id":
                receipt_recorded, receipt_skip_reason = _record_execution_receipt(
                    item,
                    provider_name,
                    routing_decision,
                    planned_route,
                    observation,
                    "skipped",
                    persistent_preflight["reason"],
                    receipt_path,
                    dispatch_id=dispatch_id,
                    role=role,
                    status="skipped",
                    source="budget_preflight",
                    budget_preflight_result=persistent_preflight,
                )
            skipped = {
                "index": i,
                "role": role,
                "tokens": 0,
                "finish_reason": "skipped",
                "error": persistent_preflight["reason"],
                "budget_preflight": persistent_preflight,
                "eval_recorded": receipt_recorded,
                "receipt_recorded": receipt_recorded,
                "eval_skip_reason": receipt_skip_reason,
                **_routing_result_fields(
                    routing_decision,
                    planned_route,
                    observation,
                    dispatch_id=dispatch_id,
                ),
            }
            results.append(skipped)
            append_event(
                events_dir,
                role,
                "auto_dispatch_skipped",
                provider=provider_name,
                dispatch_status="skipped",
                **{key: value for key, value in skipped.items() if key != "role"},
            )
            break
        if dispatch_ceiling is not None and dispatch_ceiling > budget.remaining():
            halt_reason = f"session_budget ({budget.total})"
            observation = _not_dispatched_observation()
            receipt_recorded, eval_skip_reason = _record_execution_receipt(
                item,
                provider_name,
                routing_decision,
                planned_route,
                observation,
                "skipped",
                "budget_insufficient",
                receipt_path,
                dispatch_id=dispatch_id,
                role=role,
                status="skipped",
                source="session_budget_preflight",
                budget_preflight_result=persistent_preflight,
            )
            skipped = {
                **_budget_skip_result(i, role, budget, dispatch_ceiling),
                "budget_preflight": persistent_preflight,
                "eval_recorded": receipt_recorded,
                "receipt_recorded": receipt_recorded,
                "eval_skip_reason": eval_skip_reason,
                **_routing_result_fields(
                    routing_decision,
                    planned_route,
                    observation,
                    dispatch_id=dispatch_id,
                ),
            }
            results.append(skipped)
            append_event(
                events_dir,
                role,
                "auto_dispatch_skipped",
                provider=provider_name,
                dispatch_status="skipped",
                **{key: value for key, value in skipped.items() if key != "role"},
            )
            break
        if dispatch_ceiling is not None and hasattr(provider, "per_dispatch_cap"):
            try:
                provider.per_dispatch_cap = min(int(provider.per_dispatch_cap), budget.remaining())
            except (TypeError, ValueError):
                pass
        context["session_budget_remaining"] = budget.remaining()
        context["dispatch_id"] = dispatch_id
        if routing_decision:
            context["routing"] = routing_decision
            context["provider_model"] = (
                planned_route.get("resolved_model") if planned_route else None
            )
            context["provider_route"] = planned_route

        if source is not None:
            # --- write-back path: claim BEFORE any billable call ---
            claimed = _claim_source(Path(source), role=role)
            if claimed is None:
                # Lost the claim (a worker took it, or it is no longer open).
                # No dispatch => no spend: the anti-waste invariant holds.
                observation = _not_dispatched_observation()
                receipt_recorded, eval_skip_reason = _record_execution_receipt(
                    item,
                    provider_name,
                    routing_decision,
                    planned_route,
                    observation,
                    "skipped",
                    "claim_lost",
                    receipt_path,
                    dispatch_id=dispatch_id,
                    role=role,
                    status="skipped",
                    source="claim_preflight",
                    budget_preflight_result=persistent_preflight,
                )
                skipped = {
                    "index": i, "role": role, "tokens": 0,
                    "finish_reason": "skipped", "error": "claim_lost", "reply": None,
                    "budget_preflight": persistent_preflight,
                    "eval_recorded": receipt_recorded,
                    "receipt_recorded": receipt_recorded,
                    "eval_skip_reason": eval_skip_reason,
                    **_routing_result_fields(
                        routing_decision,
                        planned_route,
                        observation,
                        dispatch_id=dispatch_id,
                    ),
                }
                results.append(skipped)
                append_event(
                    events_dir,
                    role,
                    "auto_dispatch_skipped",
                    provider=provider_name,
                    dispatch_status="skipped",
                    **{key: value for key, value in skipped.items() if key != "role"},
                )
                continue
            src_meta, _ = claimed
            call_started = time.monotonic()
            try:
                res = provider.run(role, instruction, context)
                reply_text = (getattr(res, "text", "") or getattr(res, "error", "") or "").strip()
                tokens = int(getattr(res, "tokens_in", 0) or 0) + int(getattr(res, "tokens_out", 0) or 0)
                finish = getattr(res, "finish_reason", "stop")
                err = getattr(res, "error", None)
                observation = _completion_observation(
                    res, (time.monotonic() - call_started) * 1000
                )
            except Exception as exc:  # reply with the error so the claim is never orphaned
                reply_text = f"[{role}] dispatch error: {exc.__class__.__name__}: {exc}"
                tokens, finish, err = 0, "error", f"{exc.__class__.__name__}: {exc}"
                observation = _completion_observation(
                    None, (time.monotonic() - call_started) * 1000
                )
            completion_route = _route_with_observation(
                provider_name,
                routing_decision,
                baseline_model=baseline_model,
                baseline_reasoning_effort=baseline_reasoning,
                observation=observation,
            )
            budget.record(tokens)  # synchronous: recorded before next dispatch
            eval_recorded, eval_skip_reason = _record_execution_receipt(
                item,
                provider_name,
                routing_decision,
                completion_route,
                observation,
                finish,
                err,
                receipt_path,
                dispatch_id=dispatch_id,
                role=role,
                status="completed" if not err else "error",
                source="provider_completion",
                budget_preflight_result=persistent_preflight,
            )
            reply_path = _write_back_reply(role, src_meta, reply_text, Path(source))
            result = {
                "index": i, "role": role, "tokens": tokens,
                "finish_reason": finish, "error": err,
                "reply": reply_path.name if reply_path else None,
                "eval_recorded": eval_recorded,
                "receipt_recorded": eval_recorded,
                "budget_preflight": persistent_preflight,
                **_routing_result_fields(
                    routing_decision,
                    completion_route,
                    observation,
                    dispatch_id=dispatch_id,
                ),
            }
            if eval_skip_reason:
                result["eval_skip_reason"] = eval_skip_reason
            results.append(result)
            append_event(
                events_dir,
                role,
                "auto_dispatch_completed",
                provider=provider_name,
                dispatch_status="completed" if not err else "error",
                **{key: value for key, value in result.items() if key != "role"},
            )
            continue

        call_started = time.monotonic()
        try:
            res = provider.run(role, instruction, context)
            tokens = int(getattr(res, "tokens_in", 0) or 0) + int(getattr(res, "tokens_out", 0) or 0)
            observation = _completion_observation(
                res, (time.monotonic() - call_started) * 1000
            )
            completion_route = _route_with_observation(
                provider_name,
                routing_decision,
                baseline_model=baseline_model,
                baseline_reasoning_effort=baseline_reasoning,
                observation=observation,
            )
            budget.record(tokens)  # synchronous: recorded before next dispatch
            finish = getattr(res, "finish_reason", "stop")
            err = getattr(res, "error", None)
            eval_recorded, eval_skip_reason = _record_execution_receipt(
                item,
                provider_name,
                routing_decision,
                completion_route,
                observation,
                finish,
                err,
                receipt_path,
                dispatch_id=dispatch_id,
                role=role,
                status="completed" if not err else "error",
                source="provider_completion",
                budget_preflight_result=persistent_preflight,
            )
            result = {
                "index": i, "role": role, "tokens": tokens,
                "finish_reason": finish,
                "error": err,
                "eval_recorded": eval_recorded,
                "receipt_recorded": eval_recorded,
                "budget_preflight": persistent_preflight,
                **_routing_result_fields(
                    routing_decision,
                    completion_route,
                    observation,
                    dispatch_id=dispatch_id,
                ),
            }
            if eval_skip_reason:
                result["eval_skip_reason"] = eval_skip_reason
            results.append(result)
            append_event(
                events_dir,
                role,
                "auto_dispatch_completed",
                provider=provider_name,
                dispatch_status="completed" if not err else "error",
                **{key: value for key, value in result.items() if key != "role"},
            )
        except Exception as exc:  # capture — never orphan, never abort accounting
            err = f"{exc.__class__.__name__}: {exc}"
            observation = _completion_observation(
                None, (time.monotonic() - call_started) * 1000
            )
            completion_route = _route_with_observation(
                provider_name,
                routing_decision,
                baseline_model=baseline_model,
                baseline_reasoning_effort=baseline_reasoning,
                observation=observation,
            )
            eval_recorded, eval_skip_reason = _record_execution_receipt(
                item,
                provider_name,
                routing_decision,
                completion_route,
                observation,
                "error",
                err,
                receipt_path,
                dispatch_id=dispatch_id,
                role=role,
                status="error",
                source="provider_error",
                budget_preflight_result=persistent_preflight,
            )
            result = {
                "index": i, "role": role, "tokens": 0,
                "finish_reason": "error", "error": err,
                "eval_recorded": eval_recorded,
                "receipt_recorded": eval_recorded,
                "budget_preflight": persistent_preflight,
                **_routing_result_fields(
                    routing_decision,
                    completion_route,
                    observation,
                    dispatch_id=dispatch_id,
                ),
            }
            if eval_skip_reason:
                result["eval_skip_reason"] = eval_skip_reason
            results.append(result)
            append_event(
                events_dir,
                role,
                "auto_dispatch_completed",
                provider=provider_name,
                dispatch_status="error",
                **{key: value for key, value in result.items() if key != "role"},
            )

    replied = sum(1 for r in results if r.get("reply"))
    summary = {
        "provider": provider_name,
        "dispatched": len(results),
        "halt_reason": halt_reason,
        "spent": budget.spent,
        "session_budget": budget.total,
        "remaining": budget.remaining(),
        "max_dispatches": max_dispatches,
        "write_back": write_back,
        "replied": replied,
        "results": results,
    }
    out.write(
        f"[auto_dispatch] provider={provider_name} dispatched={len(results)} "
        f"halt={halt_reason} spent={budget.spent}/{budget.total} "
        f"remaining={budget.remaining()}"
        + (f" replied={replied}" if write_back else "")
        + "\n"
    )
    return summary


def _demo_items(n: int = 20) -> list[dict]:
    return [
        {"role": "worker", "instruction": f"demo task {k}", "context": {"task_id": "DEMO"}}
        for k in range(n)
    ]


def inbox_work_items(role=None, *, limit=DEFAULT_MAX_DISPATCHES, inbox_dir=None) -> list[dict]:
    """Snapshot pending inbox messages as a bounded work_items list — READ-ONLY.

    This is the work-source adapter that connects the runner to real pending
    work (TASK-210). It deliberately does NOT claim or mutate any message:
    `agent_worker` owns the open->claimed->answered lifecycle, so a read-only
    snapshot cannot race a running worker or orphan a claim. The runner that
    consumes these items also never writes back — the whole inbox path stays
    read-only, which keeps the anti-runaway/orphan invariants intact.

    Returns at most `limit` items (oldest first by filename = timestamp), so the
    dispatch work list is bounded regardless of inbox size. Note the *disk scan*
    is still O(inbox size): we read every file to learn whether it qualifies and
    stop appending at `limit`, but do not short-circuit the directory walk. That
    is fine because the inbox is operationally bounded; we do not silently cap the
    scan (which could drop qualifying messages past an arbitrary cutoff).
    `role=None` snapshots every role; a role string filters to messages to it.
    """
    # Lazy import: reuse agent_worker's frontmatter parser + inbox path rather
    # than re-implementing the schema (its only import side effect is providers,
    # which we already import). Keeps auto_dispatch's core dependency-light.
    from agent_worker import MESSAGES_INBOX, parse_frontmatter

    inbox = Path(inbox_dir) if inbox_dir is not None else MESSAGES_INBOX
    items: list[dict] = []
    if not inbox.is_dir():
        return items
    for p in sorted(inbox.iterdir()):
        if len(items) >= limit:
            break
        if p.suffix != ".md" or p.name.startswith("."):
            continue
        try:
            meta, body = parse_frontmatter(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        # Same selection as agent_worker.list_inbox_for: open, non-reply only.
        if not meta or meta.get("status") != "open" or meta.get("type") == "reply":
            continue
        to = meta.get("to")
        normalized_to = str(to or "worker").strip()
        if normalized_to.lower().startswith("subagent-"):
            normalized_to = normalized_to[len("subagent-"):]
        if role is not None:
            normalized_filter = str(role).strip()
            if normalized_filter.lower().startswith("subagent-"):
                normalized_filter = normalized_filter[len("subagent-"):]
            if normalized_to != normalized_filter:
                continue
        msg_id = meta.get("id")
        task_id = _metadata_task_id(meta, msg_id)
        dispatch_id = str(meta.get("dispatch_id") or msg_id or p.stem).strip()
        role_id = normalized_to

        def _metadata_list(value) -> list[str]:
            if value in (None, "", "[]"):
                return []
            if isinstance(value, list):
                return [
                    str(item).strip()
                    for item in value
                    if str(item).strip()
                ]
            text = str(value).strip()
            if text.startswith("[") and text.endswith("]"):
                text = text[1:-1]
            return [
                part.strip()
                for part in text.split(",")
                if part.strip()
            ]

        eval_baseline_tokens = (
            meta.get("eval_baseline_tokens")
            if meta.get("eval_baseline_tokens") not in (None, "")
            else meta.get("baseline_tokens")
        )
        context = {
            "msg_id": msg_id,
            "type": meta.get("type"),
            "task_id": task_id,
            "dispatch_id": dispatch_id,
            "recipient": to,
        }
        item = {
            "role": role_id,
            "instruction": (body or "").strip() or str(meta.get("subject", "")),
            "context": context,
            "dispatch_id": dispatch_id,
            "routing_model": (
                meta.get("routing_model")
                or meta.get("requested_model_tier")
                or meta.get("selected_model_tier")
            ),
            "routing_grade": meta.get("routing_grade"),
            "routing_changed_files": _metadata_list(
                meta.get("routing_changed_files")
            ),
            "routing_diff_lines": meta.get("routing_diff_lines") or 0,
            "task_id": task_id,
            "eval_baseline_tokens": eval_baseline_tokens,
            # Source path for the optional write-back path (TASK-212). The
            # snapshot meta/body are deliberately NOT carried: write-back
            # re-reads fresh at claim time so a stale snapshot can never
            # overwrite a message a worker changed since the scan.
            "_source_path": p,
        }
        triggers = _metadata_list(
            meta.get("escalation_triggers")
            or meta.get("routing_escalation_triggers")
        )
        if triggers:
            item["escalation_triggers"] = triggers
            context["escalation_triggers"] = triggers
        for key in (
            "claim_id",
            "task_token_budget",
            "claim_token_budget",
            "eval_workload_id",
            "workload_id",
            "eval_baseline_receipt_id",
            "baseline_receipt_id",
            "eval_baseline_model",
            "baseline_model",
            "eval_baseline_reasoning_effort",
            "baseline_reasoning_effort",
            "eval_baseline_observation_status",
            "baseline_observation_status",
            "eval_baseline_billed_cost",
            "baseline_billed_cost",
            "eval_baseline_currency",
            "baseline_currency",
        ):
            value = meta.get(key)
            if value not in (None, ""):
                item[key] = value
                context[key] = value
        if eval_baseline_tokens is not None:
            context["eval_baseline_tokens"] = eval_baseline_tokens
        items.append(item)
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Bounded synchronous auto-dispatch runner")
    ap.add_argument("--provider", default="dummy",
                    help="provider name (dummy=safe default; live needs DISPATCH_ENABLE_LIVE=1)")
    ap.add_argument("--session-budget", type=int, default=DEFAULT_SESSION_BUDGET,
                    help="hard cumulative token budget for this run")
    ap.add_argument("--max-dispatches", type=int, default=DEFAULT_MAX_DISPATCHES,
                    help="hard cap on number of dispatches")
    ap.add_argument("--demo", action="store_true",
                    help="run against generated demo work items (dummy-safe)")
    ap.add_argument("--from-inbox", action="store_true",
                    help="snapshot pending open inbox messages as work (read-only; "
                         "does not claim/mutate — agent_worker owns the lifecycle)")
    ap.add_argument("--role", default=None,
                    help="with --from-inbox, only messages addressed to this role")
    ap.add_argument("--write-back", action="store_true",
                    help="with --from-inbox, claim each message before dispatch and "
                         "write the reply back + mark answered (default off = read-only). "
                         "Claim-before-dispatch means a lost claim costs no tokens.")
    ap.add_argument("--format", choices=["human", "json"], default="human")
    args = ap.parse_args(argv)

    if args.write_back and not args.from_inbox:
        # write-back only acts on items carrying a _source_path (inbox snapshots);
        # with --demo it would silently no-op. Say so rather than mislead.
        print("[auto_dispatch] --write-back has no effect without --from-inbox "
              "(only inbox messages have a source to reply to); ignoring.")
    if args.from_inbox:
        items = inbox_work_items(args.role, limit=args.max_dispatches)
    elif args.demo:
        items = _demo_items()
    else:
        items = []
    if not items:
        print("[auto_dispatch] no work items "
              "(use --demo for a safe dry exercise, or --from-inbox for pending messages)")
        return 0
    # For json output, discard the human progress line into an in-memory sink
    # (no file handle to leak) and print only the structured summary.
    import io
    summary = run_bounded_dispatch(
        items, args.provider,
        session_budget=args.session_budget,
        max_dispatches=args.max_dispatches,
        write_back=args.write_back,
        out=(sys.stdout if args.format == "human" else io.StringIO()),
    )
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
