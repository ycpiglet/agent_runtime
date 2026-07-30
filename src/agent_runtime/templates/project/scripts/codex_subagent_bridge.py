#!/usr/bin/env python3
"""Codex session subagent bridge (TASK-135).

This module does not pretend that repository Python can call Codex platform
developer tools. Instead, it creates an auditable packet for the *parent Codex
session* to execute through its native subagent-spawn capability, then records
the result back into the existing message bus.

Workflow:
  1. dispatch       -> render prompt + optional subagent_call + packet JSON
  2. parent Codex   -> spawn/wait Codex subagent with packet["prompt"]
  3. record-reply   -> write subagent_reply + mark the call answered

Council helpers mirror the same pattern for 2-3 member Codex subagent councils.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import math
import sys
import uuid
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
import subagent_council as sc  # noqa: E402
import subagent_dispatch as sd  # noqa: E402
import model_routing  # noqa: E402
import eval_harness  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_DIR = ROOT / "agents" / "runtime" / "codex_subagents"
SCHEMA_VERSION = 2


def _now() -> _dt.datetime:
    return _dt.datetime.now().astimezone()


def _now_iso() -> str:
    return _now().isoformat(timespec="seconds")


def _new_id(prefix: str) -> str:
    now = _now()
    return f"{prefix}-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"


def _display(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _packet_path(bridge_id: str) -> Path:
    return BRIDGE_DIR / f"{bridge_id}.json"


def _receipt_path(
    explicit: Path | str | None,
    packet: dict | None = None,
) -> Path:
    if explicit is not None:
        return Path(explicit)
    stored = str((packet or {}).get("receipt_log_path") or "").strip()
    if stored:
        path = Path(stored)
        return path if path.is_absolute() else ROOT / path
    return Path(eval_harness.EVAL_LOG)


def _write_packet(packet: dict, dry_run: bool) -> Path:
    path = _packet_path(packet["id"])
    packet["packet_path"] = _display(path)
    if not dry_run:
        BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(packet, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return path


def _load_packet(bridge_id: str) -> dict:
    path = _packet_path(bridge_id)
    if not path.is_file():
        raise FileNotFoundError(f"missing Codex subagent packet: {_display(path)}")
    return json.loads(path.read_text(encoding="utf-8"))


def _update_packet(bridge_id: str, updates: dict, dry_run: bool) -> dict:
    try:
        packet = _load_packet(bridge_id)
    except FileNotFoundError:
        packet = {"id": bridge_id, "schema_version": SCHEMA_VERSION}
    packet.update(updates)
    if not dry_run:
        _write_packet(packet, dry_run=False)
    return packet


def _suggested_agent_type(role_id: str) -> str:
    return "worker" if role_id == "implementer" else "explorer"


def _task_name(role_id: str, task_id: str) -> str:
    raw = f"{role_id}_{task_id}".lower()
    name = "".join(ch if ch.isalnum() else "_" for ch in raw)
    return "_".join(part for part in name.split("_") if part)[:64] or "subagent"


def _execution_instructions(
    role_id: str,
    task_id: str,
    prompt: str,
    route: dict,
    bridge_id: str,
    *,
    council_member: bool = False,
) -> dict:
    role_arg = f" --role {role_id}" if council_member else ""
    return {
        "capability": "native_subagent_spawn",
        "tool_hint": "collaboration.spawn_agent",
        "suggested_agent_type": _suggested_agent_type(role_id),
        "parent_session_only": True,
        "pre_spawn_guard": {
            "required": True,
            "command": (
                "python scripts/codex_subagent_bridge.py authorize "
                f"--bridge-id {bridge_id}{role_arg}"
            ),
            "invariant": (
                "Run immediately before spawn; do not spawn unless the result "
                "says authorized=true."
            ),
        },
        "spawn_args": {
            "task_name": _task_name(role_id, task_id),
            "message": prompt,
            "model": route.get("resolved_model"),
            "reasoning_effort": route.get("reasoning_effort"),
        },
        "after_completion": (
            "On success, cancellation, or spawn error, run "
            "`python scripts/codex_subagent_bridge.py record-reply "
            "--bridge-id <id> --verdict <APPROVED|NEEDS_CHANGES|...> "
            "--summary-file <file> [--status completed|error|skipped]` from "
            "the parent Codex session so the reservation becomes terminal."
        ),
    }


def _optional_nonnegative_int(value: int | str | None, field: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a non-negative integer") from exc
    if parsed < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return parsed


def _optional_nonnegative_float(
    value: float | str | None,
    field: str,
) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a non-negative number") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{field} must be a non-negative number")
    return parsed


def _completion_observation(
    *,
    provider: str | None = None,
    model: str | None = None,
    reasoning_effort: str | None = None,
    tokens_in: int | str | None = None,
    tokens_out: int | str | None = None,
    latency_ms: float | str | None = None,
    billed_cost: float | str | None = None,
    currency: str | None = None,
) -> dict:
    observed_in = _optional_nonnegative_int(tokens_in, "tokens_in")
    observed_out = _optional_nonnegative_int(tokens_out, "tokens_out")
    observed_latency = _optional_nonnegative_float(latency_ms, "latency_ms")
    observed_cost = _optional_nonnegative_float(billed_cost, "billed_cost")
    observed_currency = str(currency or "").strip().upper() or None
    if observed_cost is not None and observed_currency is None:
        raise ValueError("currency is required when billed_cost is supplied")
    token_status = (
        "observed"
        if observed_in is not None and observed_out is not None
        else "partial"
        if observed_in is not None or observed_out is not None
        else "unavailable"
    )
    return {
        "observed_provider": str(provider or "").strip() or None,
        "observed_model": str(model or "").strip() or None,
        "observed_reasoning_effort": str(reasoning_effort or "").strip() or None,
        "model_observation_status": "observed" if model else "unverified",
        "token_usage_status": token_status,
        "tokens_in": observed_in,
        "tokens_out": observed_out,
        "latency_status": "observed" if observed_latency is not None else "unavailable",
        "latency_ms": observed_latency,
        "billed_cost_status": "observed" if observed_cost is not None else "unavailable",
        "billed_cost": observed_cost,
        "currency": observed_currency,
    }


def _route_receipt_fields(route: dict) -> dict:
    return {
        "requested_tier": route.get("requested_tier"),
        "selected_tier": route.get("selected_tier"),
        "resolved_model": route.get("resolved_model"),
        "resolved_reasoning_effort": route.get("reasoning_effort"),
        "resolved_model_source": route.get("model_source"),
        "resolved_reasoning_source": route.get("reasoning_source"),
        "route_status": route.get("route_status"),
        "application_status": route.get("application_status"),
        "model_changed": route.get("model_changed"),
        "route_changed": route.get("route_changed"),
    }


def _no_spawn_receipt_values(
    *,
    dispatch_id: str,
    task_id: str,
    claim_id: str | None,
    role_id: str,
    route: dict,
    source: str,
    reason: str,
    workload_id: str | None = None,
    baseline_receipt_id: str | None = None,
    budget_preflight: dict | None = None,
) -> dict:
    return {
        "dispatch_id": dispatch_id,
        "task_id": task_id,
        "claim_id": claim_id,
        "role": role_id,
        "workload_id": workload_id,
        "provider": "native-codex",
        "execution_surface": "native_subagent_spawn",
        "source": source,
        "status": "skipped",
        "finish_reason": "skipped",
        "error": reason,
        "baseline_receipt_id": baseline_receipt_id,
        "budget_preflight_result": budget_preflight,
        **_route_receipt_fields(route),
    }


def _record_no_spawn_receipt(
    *,
    receipt_path: Path,
    **kwargs,
) -> dict:
    return eval_harness.record_execution_receipt(
        **_no_spawn_receipt_values(**kwargs),
        path=receipt_path,
    )


def _mark_message_answered(parent_id: str, dry_run: bool) -> bool:
    """Best-effort status transition for the matching subagent_call message."""
    path = sd.MESSAGES_INBOX / f"{parent_id}.md"
    if dry_run or not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if "status: open" in text:
        path.write_text(text.replace("status: open", "status: answered", 1),
                        encoding="utf-8")
        return True
    if "status: claimed" in text:
        path.write_text(text.replace("status: claimed", "status: answered", 1),
                        encoding="utf-8")
        return True
    return False


def _read_summary(summary: str | None, summary_file: str | None) -> str:
    if summary_file:
        return Path(summary_file).read_text(encoding="utf-8").strip()
    return (summary or "").strip()


def _parse_members(raw: str) -> list[str]:
    members = [m.strip() for m in raw.split(",") if m.strip()]
    if len(members) < 2:
        raise ValueError("a council needs at least two members")
    return members


def _parse_verdicts(items: list[str]) -> list[sc.Verdict]:
    verdicts: list[sc.Verdict] = []
    for raw in items or []:
        if "=" not in raw:
            raise ValueError(f"--verdict must be role=vote[:summary], got {raw!r}")
        role, _, rest = raw.partition("=")
        vote, _, summary = rest.partition(":")
        verdicts.append(sc.Verdict(role=role.strip(), vote=vote.strip(),
                                   summary=summary.strip()))
    return verdicts


def _parse_observations(items: list[str]) -> dict[str, dict]:
    observations: dict[str, dict] = {}
    for raw in items or []:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"--observation must be a JSON object: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("--observation must be a JSON object")
        role = str(payload.pop("role", "")).strip()
        if not role:
            raise ValueError("--observation JSON requires a role field")
        observations[role] = payload
    return observations


def _parse_role_values(items: list[str], option: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in items or []:
        role, separator, value = str(raw).partition("=")
        role = role.strip()
        value = value.strip()
        if not separator or not role or not value:
            raise ValueError(f"{option} must be role=value, got {raw!r}")
        if role in values:
            raise ValueError(f"{option} repeated role: {role}")
        values[role] = value
    return values


def authorize_dispatch(
    *,
    bridge_id: str,
    role_id: str | None = None,
) -> dict:
    """Revalidate a packet's pending reservation immediately before spawn."""
    packet = _load_packet(bridge_id)
    receipt_path = _receipt_path(None, packet)
    if packet.get("kind") == "codex_session_subagent_council":
        roles = [role_id] if role_id else list(packet.get("members") or [])
        unknown = sorted(set(roles) - set(packet.get("members") or []))
        if unknown:
            raise ValueError(
                "role is not a council member: " + ", ".join(unknown)
            )
        checks = {
            role: eval_harness.validate_dispatch_reservation(
                dispatch_id=f"{bridge_id}:{role}",
                path=receipt_path,
                root=ROOT,
            )
            for role in roles
        }
        authorized = all(check["authorized"] for check in checks.values())
        if authorized:
            for role, check in checks.items():
                marker = eval_harness.record_provider_call_start(
                    dispatch_id=f"{bridge_id}:{role}",
                    task_id=str(check["task_id"]),
                    source="native_codex_authorize",
                    provider="native-codex",
                    execution_surface="native_subagent_spawn",
                    path=receipt_path,
                    root=ROOT,
                )
                check["provider_call_start"] = marker
        return {
            "authorized": authorized,
            "bridge_id": bridge_id,
            "checks": checks,
        }
    if role_id and role_id != packet.get("role"):
        raise ValueError(f"role does not match dispatch packet: {role_id}")
    check = eval_harness.validate_dispatch_reservation(
        dispatch_id=str(packet.get("dispatch_id") or bridge_id),
        path=receipt_path,
        root=ROOT,
    )
    if check["authorized"]:
        check["provider_call_start"] = (
            eval_harness.record_provider_call_start(
                dispatch_id=str(packet.get("dispatch_id") or bridge_id),
                task_id=str(check["task_id"]),
                source="native_codex_authorize",
                provider="native-codex",
                execution_surface="native_subagent_spawn",
                path=receipt_path,
                root=ROOT,
            )
        )
    return {
        **check,
        "bridge_id": bridge_id,
    }


def create_dispatch_packet(
    *,
    role_id: str,
    task_id: str,
    intent: str,
    context_packet_path: str | None = None,
    sender: str = "lead-engineer",
    evidence: list[str] | None = None,
    requested_tier: str | None = None,
    escalation_triggers: list[str] | None = None,
    claim_id: str | None = None,
    dispatch_ceiling: int | str | None = None,
    task_token_budget: int | str | None = None,
    claim_token_budget: int | str | None = None,
    workload_id: str | None = None,
    baseline_receipt_id: str | None = None,
    receipt_log_path: Path | str | None = None,
    preflight_status: str | None = None,
    preflight_evidence: list[str] | None = None,
    emit_call: bool = False,
    dry_run: bool = False,
) -> dict:
    """Create a single Codex subagent dispatch packet."""
    sd.get_role(role_id)
    bridge_id = _new_id("CODEX-SUBAGENT")
    receipt_path = _receipt_path(receipt_log_path)
    tier_route = model_routing.resolve_subagent_tier(
        role_id,
        requested_tier=requested_tier,
        escalation_triggers=escalation_triggers,
    )
    provider_route = model_routing.resolve_provider_route(
        "native-codex",
        tier_route["selected_tier"],
        requested_tier=tier_route["requested_tier"],
    )
    route = {**tier_route, **provider_route}
    preflight = model_routing.deterministic_preflight(
        intent,
        status=preflight_status,
        evidence=preflight_evidence,
    )
    if preflight["status"] == "completed_sufficient":
        receipt = None
        if not dry_run:
            receipt = _record_no_spawn_receipt(
                dispatch_id=bridge_id,
                task_id=task_id,
                claim_id=str(claim_id or "").strip() or None,
                role_id=role_id,
                route=route,
                source="deterministic_preflight_complete",
                reason=str(preflight["reason"]),
                receipt_path=receipt_path,
                workload_id=workload_id,
                baseline_receipt_id=baseline_receipt_id,
            )
        return {
            "id": bridge_id,
            "schema_version": SCHEMA_VERSION,
            "kind": "codex_session_subagent_dispatch",
            "runtime": "codex-session",
            "status": "deterministic_complete_no_spawn",
            "task_id": task_id,
            "role": role_id,
            "intent": intent,
            "dispatch_id": bridge_id,
            "routing": route,
            "deterministic_preflight": preflight,
            "execution_receipt": (
                {
                    "receipt_id": receipt["receipt_id"],
                    "path": _display(receipt_path),
                }
                if receipt
                else None
            ),
            "execution": None,
        }
    if not preflight["allow_dispatch"]:
        if not dry_run:
            _record_no_spawn_receipt(
                dispatch_id=bridge_id,
                task_id=task_id,
                claim_id=str(claim_id or "").strip() or None,
                role_id=role_id,
                route=route,
                source="deterministic_preflight_blocked",
                reason=str(preflight["reason"]),
                receipt_path=receipt_path,
                workload_id=workload_id,
                baseline_receipt_id=baseline_receipt_id,
            )
        raise ValueError(
            f"deterministic preflight blocked model dispatch: {preflight['reason']}"
        )
    try:
        budget_check = (
            eval_harness.budget_preflight
            if dry_run
            else eval_harness.reserve_dispatch_budget
        )
        budget_preflight = budget_check(
            path=receipt_path,
            root=ROOT,
            task_id=task_id,
            claim_id=str(claim_id or "").strip() or None,
            dispatch_id=bridge_id,
            dispatch_ceiling=_optional_nonnegative_int(
                dispatch_ceiling,
                "dispatch_ceiling",
            ),
            task_token_budget=task_token_budget,
            claim_token_budget=claim_token_budget,
            **({"source": "codex_subagent_bridge"} if not dry_run else {}),
        )
    except eval_harness.ReceiptIntegrityError as exc:
        budget_preflight = {
            "allowed": False,
            "reason": "receipt_ledger_untrusted",
            "dispatch_id": bridge_id,
            "error": str(exc),
        }
    if not budget_preflight["allowed"]:
        receipt = None
        if not dry_run and budget_preflight["reason"] != "duplicate_dispatch_id":
            receipt = _record_no_spawn_receipt(
                dispatch_id=bridge_id,
                task_id=task_id,
                claim_id=str(claim_id or "").strip() or None,
                role_id=role_id,
                route=route,
                source="budget_preflight",
                reason=str(budget_preflight["reason"]),
                receipt_path=receipt_path,
                workload_id=workload_id,
                baseline_receipt_id=baseline_receipt_id,
                budget_preflight=budget_preflight,
            )
        return {
            "id": bridge_id,
            "schema_version": SCHEMA_VERSION,
            "kind": "codex_session_subagent_dispatch",
            "runtime": "codex-session",
            "status": "budget_blocked_no_spawn",
            "task_id": task_id,
            "role": role_id,
            "intent": intent,
            "dispatch_id": bridge_id,
            "routing": route,
            "deterministic_preflight": preflight,
            "budget_preflight": budget_preflight,
            "execution_receipt": (
                {
                    "receipt_id": receipt["receipt_id"],
                    "path": _display(receipt_path),
                }
                if receipt
                else None
            ),
            "execution": None,
        }
    prompt = sd.render_prompt(
        role_id=role_id,
        task_id=task_id,
        intent=intent,
        context_packet_path=context_packet_path,
        extra_context=(
            "Codex runtime note: this is a session-layer subagent dispatch. "
            "The parent Codex session will use its native subagent capability; "
            "repository Python only records the packet and evidence."
        ),
        tier_route=tier_route,
        provider_route=provider_route,
        requested_tier=requested_tier,
        escalation_triggers=escalation_triggers,
        provider="native-codex",
    )
    packet_path = _packet_path(bridge_id)
    ev = list(evidence or [])
    ev.append(_display(packet_path) or str(packet_path))

    call_path = None
    event_path = None
    if emit_call:
        call_path = sd.emit_call_message(
            role_id=role_id,
            task_id=task_id,
            intent=intent,
            sender=sender,
            evidence=ev,
            tier_route=tier_route,
            provider_route=provider_route,
            requested_tier=requested_tier,
            escalation_triggers=escalation_triggers,
            provider="native-codex",
            dispatch_id=bridge_id,
            claim_id=(
                (budget_preflight.get("budget_authority") or {}).get(
                    "claim_id"
                )
                or claim_id
            ),
            task_token_budget=budget_preflight.get("task_token_budget"),
            claim_token_budget=budget_preflight.get("claim_token_budget"),
            workload_id=workload_id,
            baseline_receipt_id=baseline_receipt_id,
            dry_run=dry_run,
        )
        event_path = sd.emit_event(
            role_id=role_id,
            task_id=task_id,
            kind="dispatch",
            extra={
                "runtime": "codex-session",
                "bridge_id": bridge_id,
                "message_id": call_path.stem,
                "intent": intent,
                **sd.routing_event_fields(
                    None,
                    dispatch_id=bridge_id,
                    provider="native-codex",
                    route={**tier_route, **provider_route},
                    preflight=preflight,
                ),
            },
            dry_run=dry_run,
        )

    packet = {
        "id": bridge_id,
        "schema_version": SCHEMA_VERSION,
        "kind": "codex_session_subagent_dispatch",
        "runtime": "codex-session",
        "status": "pending_parent_spawn",
        "created_at": _now_iso(),
        "sender": sender,
        "task_id": task_id,
        "role": role_id,
        "intent": intent,
        "dispatch_id": bridge_id,
        "claim_id": str(claim_id or "").strip() or None,
        "workload_id": str(workload_id or "").strip() or None,
        "baseline_receipt_id": str(baseline_receipt_id or "").strip() or None,
        "receipt_log_path": _display(receipt_path),
        "budget_preflight": budget_preflight,
        "context_packet": context_packet_path,
        "evidence": ev,
        "prompt": prompt,
        "routing": {
            **tier_route,
            **provider_route,
        },
        "deterministic_preflight": preflight,
        "call_message": _display(call_path),
        "dispatch_event": _display(event_path),
        "execution": _execution_instructions(
            role_id,
            task_id,
            prompt,
            provider_route,
            bridge_id,
        ),
    }
    _write_packet(packet, dry_run=dry_run)
    return packet


def record_reply(
    *,
    bridge_id: str,
    verdict: str,
    role_id: str | None = None,
    task_id: str | None = None,
    parent_id: str | None = None,
    sender: str = "lead-engineer",
    summary: str | None = None,
    summary_file: str | None = None,
    evidence: list[str] | None = None,
    observed_provider: str | None = None,
    observed_model: str | None = None,
    observed_reasoning_effort: str | None = None,
    tokens_in: int | str | None = None,
    tokens_out: int | str | None = None,
    latency_ms: float | str | None = None,
    billed_cost: float | str | None = None,
    currency: str | None = None,
    status: str = "completed",
    finish_reason: str | None = None,
    error: str | None = None,
    workload_id: str | None = None,
    baseline_receipt_id: str | None = None,
    receipt_log_path: Path | str | None = None,
    dry_run: bool = False,
) -> dict:
    """Record a completed Codex subagent result as subagent_reply evidence."""
    packet = _load_packet(bridge_id)
    role = role_id or packet.get("role")
    task = task_id or packet.get("task_id")
    if not role or not task:
        raise ValueError("role/task_id required when packet does not provide them")
    sd.get_role(role)
    terminal_status = str(status or "completed").strip().lower()
    if terminal_status not in {"completed", "error", "skipped"}:
        raise ValueError("status must be completed, error, or skipped")
    terminal_error = str(error or "").strip() or None
    if terminal_status == "error" and terminal_error is None:
        raise ValueError("error detail is required when status=error")
    terminal_finish = (
        None
        if finish_reason is None and terminal_status == "completed"
        else terminal_status
        if finish_reason is None
        else str(finish_reason)
    )

    call_message = packet.get("call_message")
    parent = parent_id
    if not parent and call_message:
        parent = Path(str(call_message)).stem

    ev = list(evidence or [])
    packet_path = packet.get("packet_path")
    if packet_path:
        ev.append(packet_path)
    text = _read_summary(summary, summary_file)
    observation = _completion_observation(
        provider=observed_provider,
        model=observed_model,
        reasoning_effort=observed_reasoning_effort,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        billed_cost=billed_cost,
        currency=currency,
    )
    requested_route = dict(packet.get("routing") or {})
    completed_route = {
        **requested_route,
        **model_routing.resolve_provider_route(
            "native-codex",
            str(requested_route.get("selected_tier") or "worker_standard"),
            requested_tier=str(
                requested_route.get("requested_tier")
                or requested_route.get("selected_tier")
                or "worker_standard"
            ),
            observed_model=observation["observed_model"],
            observed_reasoning_effort=observation["observed_reasoning_effort"],
        ),
    }
    dispatch_id = str(packet.get("dispatch_id") or bridge_id)
    receipt_path = _receipt_path(receipt_log_path, packet)
    receipt = None
    if not dry_run:
        receipt = eval_harness.record_execution_receipt(
            dispatch_id=dispatch_id,
            task_id=str(task),
            claim_id=str(packet.get("claim_id") or "").strip() or None,
            role=str(role),
            workload_id=(
                str(workload_id or packet.get("workload_id") or "").strip()
                or None
            ),
            provider="native-codex",
            execution_surface="native_subagent_spawn",
            requested_tier=completed_route.get("requested_tier"),
            selected_tier=completed_route.get("selected_tier"),
            resolved_model=completed_route.get("resolved_model"),
            resolved_reasoning_effort=completed_route.get("reasoning_effort"),
            resolved_model_source=completed_route.get("model_source"),
            resolved_reasoning_source=completed_route.get("reasoning_source"),
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
            source="native_codex_reply",
            status=terminal_status,
            finish_reason=terminal_finish,
            error=terminal_error,
            route_status=completed_route.get("route_status"),
            application_status=completed_route.get("application_status"),
            model_changed=completed_route.get("model_changed"),
            route_changed=completed_route.get("route_changed"),
            baseline_receipt_id=(
                str(
                    baseline_receipt_id
                    or packet.get("baseline_receipt_id")
                    or ""
                ).strip()
                or None
            ),
            budget_preflight_result=dict(packet.get("budget_preflight") or {}),
            path=receipt_path,
        )
    reply_path = None
    event_path = None
    marked = False
    if parent:
        reply_path = sd.emit_reply_message(
            parent_id=parent,
            role_id=role,
            task_id=task,
            verdict=verdict,
            sender=sender,
            summary=text,
            evidence=ev,
            dry_run=dry_run,
        )
        event_path = sd.emit_event(
            role_id=role,
            task_id=task,
            kind="reply",
            extra={
                "runtime": "codex-session",
                "bridge_id": bridge_id,
                "message_id": reply_path.stem,
                "in_reply_to": parent,
                "verdict": verdict,
                **sd.routing_event_fields(
                    None,
                    dispatch_id=dispatch_id,
                    provider="native-codex",
                    route=completed_route,
                    preflight=dict(packet.get("deterministic_preflight") or {}),
                ),
                **observation,
            },
            dry_run=dry_run,
        )
        marked = _mark_message_answered(parent, dry_run=dry_run)
    updates = {
        "status": terminal_status,
        "completed_at": _now_iso(),
        "finish_reason": terminal_finish,
        "error": terminal_error,
        "verdict": verdict,
        "reply_message": _display(reply_path),
        "reply_event": _display(event_path),
        "parent_marked_answered": marked,
        "completion_observation": observation,
        "routing_completion": completed_route,
        "execution_receipt": (
            {
                "receipt_id": receipt["receipt_id"],
                "path": _display(receipt_path),
            }
            if receipt
            else None
        ),
    }
    _update_packet(bridge_id, updates, dry_run=dry_run)
    return {**updates, "role": role, "task_id": task, "summary": text}


def create_council_packet(
    *,
    task_id: str,
    members: list[str],
    intent: str,
    method: str = "any_veto",
    context_packet_path: str | None = None,
    sender: str = "lead-engineer",
    evidence: list[str] | None = None,
    claim_id: str | None = None,
    dispatch_ceiling: int | str | None = None,
    task_token_budget: int | str | None = None,
    claim_token_budget: int | str | None = None,
    workload_id: str | None = None,
    baseline_receipt_ids: dict[str, str] | None = None,
    receipt_log_path: Path | str | None = None,
    preflight_status: str | None = None,
    preflight_evidence: list[str] | None = None,
    emit_calls: bool = False,
    dry_run: bool = False,
) -> dict:
    """Create a Codex subagent council packet with one prompt per member."""
    if method not in sc.CONSENSUS_METHODS:
        raise ValueError(f"method must be one of {sorted(sc.CONSENSUS_METHODS)}")
    if len(members) < 2:
        raise ValueError("a council needs at least two members")
    if len(set(members)) != len(members):
        raise ValueError("council members must be unique")
    for member in members:
        sd.get_role(member)
    bridge_id = _new_id("CODEX-COUNCIL")
    receipt_path = _receipt_path(receipt_log_path)
    member_execution: dict[str, dict] = {}
    for member in members:
        tier_route = model_routing.resolve_subagent_tier(member)
        provider_route = model_routing.resolve_provider_route(
            "native-codex",
            tier_route["selected_tier"],
            requested_tier=tier_route["requested_tier"],
        )
        member_execution[member] = {
            "routing": {**tier_route, **provider_route},
        }
    preflight = model_routing.deterministic_preflight(
        intent,
        status=preflight_status,
        evidence=preflight_evidence,
    )
    if not preflight["allow_dispatch"]:
        source = (
            "deterministic_preflight_complete"
            if preflight["status"] == "completed_sufficient"
            else "deterministic_preflight_blocked"
        )
        receipts: list[dict] = []
        if not dry_run:
            receipts = eval_harness.record_execution_receipts(
                [
                    _no_spawn_receipt_values(
                        dispatch_id=f"{bridge_id}:{member}",
                        task_id=task_id,
                        claim_id=str(claim_id or "").strip() or None,
                        role_id=member,
                        route=member_execution[member]["routing"],
                        source=source,
                        reason=str(preflight["reason"]),
                        workload_id=workload_id,
                        baseline_receipt_id=(
                            (baseline_receipt_ids or {}).get(member)
                        ),
                    )
                    for member in members
                ],
                path=receipt_path,
            )
        if preflight["status"] == "completed_sufficient":
            return {
                "id": bridge_id,
                "schema_version": SCHEMA_VERSION,
                "kind": "codex_session_subagent_council",
                "runtime": "codex-session",
                "status": "deterministic_complete_no_spawn",
                "task_id": task_id,
                "members": members,
                "intent": intent,
                "deterministic_preflight": preflight,
                "execution_receipts": {
                    member: {
                        "receipt_id": receipt["receipt_id"],
                        "path": _display(receipt_path),
                    }
                    for member, receipt in zip(members, receipts)
                },
                "execution": None,
            }
        raise ValueError(
            f"deterministic preflight blocked model dispatch: {preflight['reason']}"
        )

    parsed_ceiling = _optional_nonnegative_int(
        dispatch_ceiling,
        "dispatch_ceiling",
    )
    budget_requests = [
        {
            "root": ROOT,
            "task_id": task_id,
            "claim_id": str(claim_id or "").strip() or None,
            "dispatch_id": f"{bridge_id}:{member}",
            "dispatch_ceiling": parsed_ceiling,
            "task_token_budget": task_token_budget,
            "claim_token_budget": claim_token_budget,
        }
        for member in members
    ]
    try:
        budget_batch = (
            eval_harness.plan_dispatch_budgets(
                budget_requests,
                path=receipt_path,
                root=ROOT,
                source="codex_subagent_council_dry_run",
            )
            if dry_run
            else eval_harness.reserve_dispatch_budgets(
                budget_requests,
                path=receipt_path,
                root=ROOT,
                source="codex_subagent_council",
            )
        )
    except eval_harness.ReceiptIntegrityError as exc:
        budget_batch = {
            "allowed": False,
            "results": [
                {
                    "allowed": False,
                    "reason": "receipt_ledger_untrusted",
                    "dispatch_id": f"{bridge_id}:{member}",
                    "error": str(exc),
                }
                for member in members
            ],
            "reservations": [],
        }
    member_budget_preflights = {
        member: result
        for member, result in zip(members, budget_batch["results"])
    }
    if not budget_batch["allowed"]:
        receipts: list[dict] = []
        if not dry_run:
            receipts = eval_harness.record_execution_receipts(
                [
                    _no_spawn_receipt_values(
                        dispatch_id=f"{bridge_id}:{member}",
                        task_id=task_id,
                        claim_id=str(claim_id or "").strip() or None,
                        role_id=member,
                        route=member_execution[member]["routing"],
                        source="budget_preflight",
                        reason=str(
                            member_budget_preflights[member].get(
                                "batch_reason"
                            )
                            or member_budget_preflights[member].get("reason")
                            or "council_batch_budget_denied"
                        ),
                        workload_id=workload_id,
                        baseline_receipt_id=(
                            (baseline_receipt_ids or {}).get(member)
                        ),
                        budget_preflight=member_budget_preflights[member],
                    )
                    for member in members
                ],
                path=receipt_path,
            )
        return {
            "id": bridge_id,
            "schema_version": SCHEMA_VERSION,
            "kind": "codex_session_subagent_council",
            "runtime": "codex-session",
            "status": "budget_blocked_no_spawn",
            "task_id": task_id,
            "members": members,
            "intent": intent,
            "claim_id": str(claim_id or "").strip() or None,
            "deterministic_preflight": preflight,
            "member_budget_preflights": member_budget_preflights,
            "execution_receipts": {
                member: {
                    "receipt_id": receipt["receipt_id"],
                    "path": _display(receipt_path),
                }
                for member, receipt in zip(members, receipts)
            },
            "execution": None,
        }

    prompts = sc.render_council_prompts(
        task_id=task_id,
        members=members,
        intent=intent,
        context_packet_path=context_packet_path,
    )
    packet_path = _packet_path(bridge_id)
    ev = list(evidence or [])
    ev.append(_display(packet_path) or str(packet_path))

    calls: list[dict] = []
    for member in members:
        member_route = member_execution[member]["routing"]
        prompts[member] = sd.render_prompt(
            role_id=member,
            task_id=task_id,
            intent=intent,
            context_packet_path=context_packet_path,
            extra_context=(
                f"Codex council member: {member}. The parent session executes "
                "the exact native spawn arguments recorded in this packet."
            ),
            tier_route=member_route,
            provider_route=member_route,
            provider="native-codex",
        )
        instructions = _execution_instructions(
            member,
            task_id,
            prompts[member],
            member_route,
            bridge_id,
            council_member=True,
        )
        member_execution[member]["spawn_args"] = instructions["spawn_args"]
        member_execution[member]["pre_spawn_guard"] = instructions[
            "pre_spawn_guard"
        ]
    if emit_calls:
        for member in members:
            member_route = member_execution[member]["routing"]
            call_path = sd.emit_call_message(
                role_id=member,
                task_id=task_id,
                intent=f"{intent} (council member: {member})",
                sender=sender,
                evidence=ev,
                tier_route=member_route,
                provider_route=member_route,
                provider="native-codex",
                dispatch_id=f"{bridge_id}:{member}",
                claim_id=(
                    (
                        member_budget_preflights[member].get(
                            "budget_authority"
                        )
                        or {}
                    ).get("claim_id")
                    or claim_id
                ),
                task_token_budget=member_budget_preflights[member].get(
                    "task_token_budget"
                ),
                claim_token_budget=member_budget_preflights[member].get(
                    "claim_token_budget"
                ),
                workload_id=workload_id,
                baseline_receipt_id=(
                    (baseline_receipt_ids or {}).get(member)
                ),
                dry_run=dry_run,
            )
            event_path = sd.emit_event(
                role_id=member,
                task_id=task_id,
                kind="dispatch",
                extra={
                    "runtime": "codex-session",
                    "bridge_id": bridge_id,
                    "council_member": member,
                    "message_id": call_path.stem,
                    "intent": intent,
                    **sd.routing_event_fields(
                        None,
                        dispatch_id=f"{bridge_id}:{member}",
                        provider="native-codex",
                        route=member_route,
                        preflight=preflight,
                    ),
                },
                dry_run=dry_run,
            )
            calls.append({
                "role": member,
                "call_message": _display(call_path),
                "dispatch_event": _display(event_path),
                "routing": member_route,
            })

    packet = {
        "id": bridge_id,
        "schema_version": SCHEMA_VERSION,
        "kind": "codex_session_subagent_council",
        "runtime": "codex-session",
        "status": "pending_parent_spawn",
        "created_at": _now_iso(),
        "sender": sender,
        "task_id": task_id,
        "claim_id": str(claim_id or "").strip() or None,
        "workload_id": str(workload_id or "").strip() or None,
        "baseline_receipt_ids": dict(baseline_receipt_ids or {}),
        "members": members,
        "method": method,
        "intent": intent,
        "context_packet": context_packet_path,
        "receipt_log_path": _display(receipt_path),
        "member_budget_preflights": member_budget_preflights,
        "evidence": ev,
        "prompts": prompts,
        "deterministic_preflight": preflight,
        "member_execution": member_execution,
        "call_messages": calls,
        "execution": {
            "capability": "native_subagent_spawn",
            "tool_hint": "collaboration.spawn_agent",
            "parent_session_only": True,
            "suggested_parallelism": "spawn one Codex subagent per member",
            "spawn_args_by_member": {
                role: data["spawn_args"]
                for role, data in member_execution.items()
            },
            "pre_spawn_guard_by_member": {
                role: data["pre_spawn_guard"]
                for role, data in member_execution.items()
            },
            "after_completion": (
                "Run `python scripts/codex_subagent_bridge.py council-record "
                "--bridge-id <id> --task-id <task> --method <method> "
                "--verdict role=vote[:summary] ...`. For every cancellation, "
                "skipped member, or spawn error, also pass one "
                "`--observation '{\"role\":\"<role>\",\"status\":"
                "\"error|skipped\",\"error\":\"<reason>\"}'` so every "
                "reservation becomes terminal even when no verdict exists."
            ),
        },
    }
    _write_packet(packet, dry_run=dry_run)
    return packet


def record_council(
    *,
    bridge_id: str,
    task_id: str | None,
    method: str | None,
    verdicts: list[sc.Verdict],
    sender: str = "lead-engineer",
    observations: dict[str, dict] | None = None,
    receipt_log_path: Path | str | None = None,
    dry_run: bool = False,
) -> dict:
    packet = _load_packet(bridge_id)
    task = task_id or packet.get("task_id")
    method_name = method or packet.get("method")
    if not task or not method_name:
        raise ValueError("task_id/method required when packet does not provide them")
    members = list(packet.get("members") or [])
    verdict_roles = {verdict.role for verdict in verdicts}
    unknown_verdict_roles = sorted(verdict_roles - set(members))
    if unknown_verdict_roles:
        raise ValueError(
            "verdict role is not a council member: "
            + ", ".join(unknown_verdict_roles)
        )
    result = (
        sc.decide(method_name, verdicts)
        if verdicts
        else sc.CouncilResult(
            method=method_name,
            final="incomplete",
            rationale="no council member verdict was recorded",
            verdicts=[],
        )
    )
    supplied_observations = observations or {}
    member_observations: dict[str, dict] = {}
    member_terminal: dict[str, dict] = {}
    for role in members:
        raw = dict(supplied_observations.get(role) or {})
        default_status = "completed" if role in verdict_roles else "skipped"
        status = str(raw.pop("status", default_status) or default_status).lower()
        if status not in {"completed", "error", "skipped"}:
            raise ValueError(
                f"member {role} status must be completed, error, or skipped"
            )
        error = str(raw.pop("error", "") or "").strip() or None
        if status == "error" and error is None:
            raise ValueError(f"member {role} error detail is required")
        if status == "skipped" and error is None and role not in verdict_roles:
            error = "member_verdict_missing"
        supplied_finish = raw.pop("finish_reason", None)
        finish_reason = (
            None
            if supplied_finish is None and status == "completed"
            else status
            if supplied_finish is None
            else str(supplied_finish)
        )
        workload_id = str(raw.pop("workload_id", "") or "").strip() or None
        baseline_receipt_id = (
            str(raw.pop("baseline_receipt_id", "") or "").strip() or None
        )
        member_observations[role] = _completion_observation(**raw)
        member_terminal[role] = {
            "status": status,
            "finish_reason": finish_reason,
            "error": error,
            "workload_id": workload_id,
            "baseline_receipt_id": baseline_receipt_id,
        }
    incomplete = [
        role
        for role, terminal in member_terminal.items()
        if terminal["status"] != "completed"
    ]
    if incomplete:
        result = sc.CouncilResult(
            method=result.method,
            final="incomplete",
            rationale=(
                "council member execution incomplete: " + ", ".join(incomplete)
            ),
            verdicts=result.verdicts,
        )
    member_routing: dict[str, dict] = {}
    for role in members:
        requested = dict(
            (packet.get("member_execution") or {}).get(role, {}).get("routing")
            or {}
        )
        observation = member_observations[role]
        member_routing[role] = {
            **requested,
            **model_routing.resolve_provider_route(
                "native-codex",
                str(requested.get("selected_tier") or "worker_standard"),
                requested_tier=str(
                    requested.get("requested_tier")
                    or requested.get("selected_tier")
                    or "worker_standard"
                ),
                observed_model=observation.get("observed_model"),
                observed_reasoning_effort=observation.get(
                    "observed_reasoning_effort"
                ),
            ),
        }
    receipt_path = _receipt_path(receipt_log_path, packet)
    receipt_preflights = dict(packet.get("member_budget_preflights") or {})
    execution_receipts: dict[str, dict | None] = {role: None for role in members}
    if not dry_run:
        receipt_values: list[dict] = []
        for role in members:
            route = member_routing[role]
            observation = member_observations[role]
            terminal = member_terminal[role]
            receipt_values.append({
                "dispatch_id": f"{bridge_id}:{role}",
                "task_id": str(task),
                "claim_id": str(packet.get("claim_id") or "").strip() or None,
                "role": role,
                "workload_id": (
                    terminal["workload_id"]
                    or str(packet.get("workload_id") or "").strip()
                    or None
                ),
                "provider": "native-codex",
                "execution_surface": "native_subagent_spawn",
                "requested_tier": route.get("requested_tier"),
                "selected_tier": route.get("selected_tier"),
                "resolved_model": route.get("resolved_model"),
                "resolved_reasoning_effort": route.get("reasoning_effort"),
                "resolved_model_source": route.get("model_source"),
                "resolved_reasoning_source": route.get("reasoning_source"),
                "observed_provider": observation.get("observed_provider"),
                "observed_model": observation.get("observed_model"),
                "observed_reasoning_effort": observation.get(
                    "observed_reasoning_effort"
                ),
                "token_usage_status": observation.get("token_usage_status"),
                "tokens_in": observation.get("tokens_in"),
                "tokens_out": observation.get("tokens_out"),
                "billed_cost_status": observation.get("billed_cost_status"),
                "billed_cost": observation.get("billed_cost"),
                "currency": observation.get("currency"),
                "source": "native_codex_council_reply",
                "status": terminal["status"],
                "finish_reason": terminal["finish_reason"],
                "error": terminal["error"],
                "baseline_receipt_id": (
                    terminal["baseline_receipt_id"]
                    or (packet.get("baseline_receipt_ids") or {}).get(role)
                ),
                "route_status": route.get("route_status"),
                "application_status": route.get("application_status"),
                "model_changed": route.get("model_changed"),
                "route_changed": route.get("route_changed"),
                "budget_preflight_result": dict(
                    receipt_preflights.get(role) or {}
                ),
            })
        receipts = eval_harness.record_execution_receipts(
            receipt_values,
            path=receipt_path,
        )
        for role, receipt in zip(members, receipts):
            execution_receipts[role] = {
                "receipt_id": receipt["receipt_id"],
                "path": _display(receipt_path),
            }
    consensus_path = sc.emit_consensus_message(
        task_id=task,
        result=result,
        sender=sender,
        dry_run=dry_run,
    )
    event_path = sd.emit_event(
        role_id="council",
        task_id=task,
        kind="verdict",
        extra={
            "runtime": "codex-session",
            "bridge_id": bridge_id,
            "method": result.method,
            "final": result.final,
            "message_id": consensus_path.stem,
            "dispatch_id": bridge_id,
            "provider": "native-codex",
            "execution_surface": "native_subagent_spawn",
            "requested_tier": "per_member",
            "selected_tier": "per_member",
            "provider_tier": "per_member",
            "resolved_model": "per_member",
            "model_source": "per_member",
            "reasoning_effort": "per_member",
            "route_status": "per_member",
            "equivalence_status": "per_member",
            "application_status": "per_member",
            "model_observation_status": "per_member",
            "token_usage_status": "per_member",
            "latency_status": "per_member",
            "billed_cost_status": "per_member",
            "deterministic_preflight": str(
                (packet.get("deterministic_preflight") or {}).get(
                    "status", "not_recorded"
                )
            ),
            "deterministic_evidence": list(
                (packet.get("deterministic_preflight") or {}).get("evidence")
                or []
            ),
            "member_routing": member_routing,
            "member_observations": member_observations,
            "member_terminal": member_terminal,
        },
        dry_run=dry_run,
    )
    marked_calls: list[str] = []
    for call in packet.get("call_messages") or []:
        call_path = call.get("call_message")
        if not call_path:
            continue
        parent_id = Path(str(call_path)).stem
        if _mark_message_answered(parent_id, dry_run=dry_run):
            marked_calls.append(parent_id)
    updates = {
        "status": "completed",
        "completed_at": _now_iso(),
        "final": result.final,
        "rationale": result.rationale,
        "consensus_message": _display(consensus_path),
        "verdict_event": _display(event_path),
        "parent_calls_marked_answered": marked_calls,
        "member_routing_completion": member_routing,
        "member_observations": member_observations,
        "member_terminal": member_terminal,
        "execution_receipts": execution_receipts,
    }
    _update_packet(bridge_id, updates, dry_run=dry_run)
    return {**updates, "task_id": task, "method": result.method}


def _print_packet(packet: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(packet, ensure_ascii=False, indent=2))
        return
    print(f"id: {packet['id']}")
    print(f"kind: {packet['kind']}")
    print(f"packet: {packet.get('packet_path')}")
    if packet.get("call_message"):
        print(f"call_message: {packet['call_message']}")
    if packet.get("call_messages"):
        print("call_messages:")
        for call in packet["call_messages"]:
            print(f"  - {call['role']}: {call['call_message']}")
    print("execution: parent Codex session must use native_subagent_spawn")
    if "prompt" in packet:
        print("\n--- prompt ---")
        print(packet["prompt"])
    elif "prompts" in packet:
        for role, prompt in packet["prompts"].items():
            print(f"\n--- prompt: {role} ---")
            print(prompt)


def _cmd_dispatch(args: argparse.Namespace) -> int:
    try:
        packet = create_dispatch_packet(
            role_id=args.role,
            task_id=args.task_id,
            intent=args.intent,
            context_packet_path=args.context_packet,
            sender=args.sender,
            evidence=args.evidence or [],
            requested_tier=args.pm_tier,
            escalation_triggers=args.escalation_trigger,
            claim_id=args.claim_id,
            dispatch_ceiling=args.dispatch_ceiling,
            task_token_budget=args.task_token_budget,
            claim_token_budget=args.claim_token_budget,
            workload_id=args.workload_id,
            baseline_receipt_id=args.baseline_receipt_id,
            receipt_log_path=args.receipt_log,
            preflight_status=args.preflight_status,
            preflight_evidence=args.preflight_evidence,
            emit_call=args.emit_call,
            dry_run=args.dry_run,
        )
    except (ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    _print_packet(packet, args.json)
    return 0


def _cmd_record_reply(args: argparse.Namespace) -> int:
    try:
        result = record_reply(
            bridge_id=args.bridge_id,
            role_id=args.role,
            task_id=args.task_id,
            parent_id=args.parent_id,
            verdict=args.verdict,
            sender=args.sender,
            summary=args.summary,
            summary_file=args.summary_file,
            evidence=args.evidence or [],
            observed_provider=args.observed_provider,
            observed_model=args.observed_model,
            observed_reasoning_effort=args.observed_reasoning_effort,
            tokens_in=args.tokens_in,
            tokens_out=args.tokens_out,
            latency_ms=args.latency_ms,
            billed_cost=args.billed_cost,
            currency=args.currency,
            status=args.status,
            finish_reason=args.finish_reason,
            error=args.error,
            workload_id=args.workload_id,
            baseline_receipt_id=args.baseline_receipt_id,
            receipt_log_path=args.receipt_log,
            dry_run=args.dry_run,
        )
    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        eval_harness.ReceiptIntegrityError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _cmd_authorize(args: argparse.Namespace) -> int:
    try:
        result = authorize_dispatch(
            bridge_id=args.bridge_id,
            role_id=args.role,
        )
    except (
        FileNotFoundError,
        ValueError,
        eval_harness.ReceiptIntegrityError,
    ) as exc:
        result = {
            "authorized": False,
            "bridge_id": args.bridge_id,
            "reason": "authorization_failed",
            "error": str(exc),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("authorized") else 1


def _cmd_council_plan(args: argparse.Namespace) -> int:
    try:
        members = _parse_members(args.members)
        baseline_receipts = _parse_role_values(
            args.baseline_receipt,
            "--baseline-receipt",
        )
        packet = create_council_packet(
            task_id=args.task_id,
            members=members,
            intent=args.intent,
            method=args.method,
            context_packet_path=args.context_packet,
            sender=args.sender,
            evidence=args.evidence or [],
            claim_id=args.claim_id,
            dispatch_ceiling=args.dispatch_ceiling,
            task_token_budget=args.task_token_budget,
            claim_token_budget=args.claim_token_budget,
            workload_id=args.workload_id,
            baseline_receipt_ids=baseline_receipts,
            receipt_log_path=args.receipt_log,
            preflight_status=args.preflight_status,
            preflight_evidence=args.preflight_evidence,
            emit_calls=args.emit_calls,
            dry_run=args.dry_run,
        )
    except (ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    _print_packet(packet, args.json)
    return 0


def _cmd_council_record(args: argparse.Namespace) -> int:
    try:
        verdicts = _parse_verdicts(args.verdict)
        observations = _parse_observations(args.observation)
        result = record_council(
            bridge_id=args.bridge_id,
            task_id=args.task_id,
            method=args.method,
            verdicts=verdicts,
            sender=args.sender,
            observations=observations,
            receipt_log_path=args.receipt_log,
            dry_run=args.dry_run,
        )
    except (
        FileNotFoundError,
        ValueError,
        KeyError,
        eval_harness.ReceiptIntegrityError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["final"] == "approved" else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="codex_subagent_bridge.py",
        description="Codex session subagent bridge (TASK-135).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    d = sub.add_parser("dispatch", help="create one Codex subagent packet")
    d.add_argument("--role", required=True, choices=sd.list_roles())
    d.add_argument("--task-id", required=True)
    d.add_argument("--intent", required=True)
    d.add_argument("--context-packet")
    d.add_argument("--sender", default="lead-engineer")
    d.add_argument("--evidence", action="append")
    d.add_argument("--pm-tier", choices=sorted(model_routing.ALLOWED_PM_TIERS))
    d.add_argument("--escalation-trigger", action="append", default=[])
    d.add_argument("--claim-id")
    d.add_argument("--dispatch-ceiling", type=int)
    d.add_argument("--task-token-budget")
    d.add_argument("--claim-token-budget")
    d.add_argument("--workload-id")
    d.add_argument("--baseline-receipt-id")
    d.add_argument("--receipt-log")
    d.add_argument(
        "--preflight-status",
        choices=sorted(model_routing.PREFLIGHT_STATUSES),
    )
    d.add_argument("--preflight-evidence", action="append", default=[])
    d.add_argument("--emit-call", action="store_true")
    d.add_argument("--dry-run", action="store_true")
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=_cmd_dispatch)

    rr = sub.add_parser("record-reply", help="record a Codex subagent result")
    rr.add_argument("--bridge-id", required=True)
    rr.add_argument("--role", choices=sd.list_roles())
    rr.add_argument("--task-id")
    rr.add_argument("--parent-id")
    rr.add_argument("--verdict", required=True)
    rr.add_argument("--summary")
    rr.add_argument("--summary-file")
    rr.add_argument("--sender", default="lead-engineer")
    rr.add_argument("--evidence", action="append")
    rr.add_argument("--observed-provider")
    rr.add_argument("--observed-model")
    rr.add_argument("--observed-reasoning-effort")
    rr.add_argument("--tokens-in", type=int)
    rr.add_argument("--tokens-out", type=int)
    rr.add_argument("--latency-ms", type=float)
    rr.add_argument("--billed-cost", type=float)
    rr.add_argument("--currency")
    rr.add_argument(
        "--status",
        default="completed",
        choices=["completed", "error", "skipped"],
    )
    rr.add_argument("--finish-reason")
    rr.add_argument("--error")
    rr.add_argument("--workload-id")
    rr.add_argument("--baseline-receipt-id")
    rr.add_argument("--receipt-log")
    rr.add_argument("--dry-run", action="store_true")
    rr.set_defaults(func=_cmd_record_reply)

    auth = sub.add_parser(
        "authorize",
        help="revalidate a pending reservation immediately before native spawn",
    )
    auth.add_argument("--bridge-id", required=True)
    auth.add_argument("--role", choices=sd.list_roles())
    auth.set_defaults(func=_cmd_authorize)

    cp = sub.add_parser("council-plan", help="create a Codex council packet")
    cp.add_argument("--task-id", required=True)
    cp.add_argument("--members", required=True)
    cp.add_argument("--intent", required=True)
    cp.add_argument("--method", default="any_veto",
                    choices=sorted(sc.CONSENSUS_METHODS))
    cp.add_argument("--context-packet")
    cp.add_argument("--sender", default="lead-engineer")
    cp.add_argument("--evidence", action="append")
    cp.add_argument("--claim-id")
    cp.add_argument("--dispatch-ceiling", type=int)
    cp.add_argument("--task-token-budget")
    cp.add_argument("--claim-token-budget")
    cp.add_argument("--workload-id")
    cp.add_argument(
        "--baseline-receipt",
        action="append",
        default=[],
        help="role=receipt_id, repeatable",
    )
    cp.add_argument("--receipt-log")
    cp.add_argument(
        "--preflight-status",
        choices=sorted(model_routing.PREFLIGHT_STATUSES),
    )
    cp.add_argument("--preflight-evidence", action="append", default=[])
    cp.add_argument("--emit-calls", action="store_true")
    cp.add_argument("--dry-run", action="store_true")
    cp.add_argument("--json", action="store_true")
    cp.set_defaults(func=_cmd_council_plan)

    cr = sub.add_parser("council-record", help="record a Codex council result")
    cr.add_argument("--bridge-id", required=True)
    cr.add_argument("--task-id")
    cr.add_argument("--method", choices=sorted(sc.CONSENSUS_METHODS))
    cr.add_argument("--verdict", action="append", default=[],
                    help="role=vote[:summary], repeatable")
    cr.add_argument("--sender", default="lead-engineer")
    cr.add_argument("--receipt-log")
    cr.add_argument(
        "--observation",
        action="append",
        default=[],
        help='Member observation JSON, e.g. {"role":"reviewer","model":"...","tokens_in":1}',
    )
    cr.add_argument("--dry-run", action="store_true")
    cr.set_defaults(func=_cmd_council_record)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
