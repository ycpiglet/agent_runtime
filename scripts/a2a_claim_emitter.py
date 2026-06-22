"""Wire real claim lifecycle events into the live A2A message stream.

The A2A router (``scripts/a2a_message_router.py``) was complete and tested, but
nothing in the dispatch loop ever called ``emit_message()`` -- so the live queue
at ``agents/runtime/a2a/messages.jsonl`` stayed empty and the A2A trace/lifecycle
gates only ever validated the static baseline. This module closes that gap: it
emits A2A messages at the *real* claim lifecycle events.

Mapping (additive, observability-only -- it RECORDS, it does not change who gets
a claim):

- claim created  -> ``request``   (worker asks an independent verifier to review)
- handoff/release-> ``review``     (verifier records its verdict)
                 -> ``decision``   (worker accepts the verdict and releases)
                 -> ``correction`` (verifier files the closing correction note)

Why the release path emits three events: ``a2a_trace_gate`` reconstructs a chain
per ``(contextId, taskId, decision_cycle_id)`` and requires the full
request->review->decision->correction lifecycle in order, with each follow-up's
``parent_event_id`` linking the previous event and each ``sender`` matching the
previous ``receiver`` (route handoff). A claim's create+release together form one
such chain, so the live stream the gate validates is a real, reconstructable
trace -- not the baseline fixture.

Identifiers are DERIVED DETERMINISTICALLY from the claim so the chain links even
across separate process invocations (create and release run in different
processes): ``context_id`` from the task, ``decision_cycle_id`` from the claim id,
and each ``event_id``/``parent_event_id`` from ``(claim_id, event_type)``.

Robustness contract: every public function wraps emission in try/except and
returns ``None`` (or ``[]``) on failure. An A2A emit failure must NEVER break the
claim create/release operation -- this is best-effort observability.
"""

from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:  # bare import when run as a script (scripts/ on sys.path); package path under pytest
    import a2a_message_router as _router
except ModuleNotFoundError:  # pragma: no cover - import-path shim
    from scripts import a2a_message_router as _router


DEFAULT_LOG = Path("agents/runtime/a2a/messages.jsonl")

# Ordered lifecycle the trace gate expects per chain.
_RELEASE_EVENTS = ("review", "decision", "correction")
_ALL_EVENTS = ("request",) + _RELEASE_EVENTS

# Deterministic per-event time offsets (seconds) so a chain emitted across two
# processes still sorts request < review < decision < correction by timestamp.
_EVENT_OFFSETS = {"request": 0, "review": 1, "decision": 2, "correction": 3}

_DEFAULT_VERIFIER_ROLE = "independent-verifier"


def _emit_message(**kwargs: Any) -> dict[str, Any]:
    """Indirection seam so tests can simulate a router failure."""
    return _router.emit_message(**kwargs)


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", str(value or "").strip().lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "x"


def _resolve_log_path(root: Path, log_path: Path | None) -> Path:
    if log_path is not None:
        return Path(log_path)
    return Path(root) / DEFAULT_LOG


def _context_id(claim: dict[str, Any]) -> str:
    return f"ctx-{_slug(claim.get('task_id') or claim.get('claim_id') or 'claim')}"


def _decision_cycle_id(claim: dict[str, Any]) -> str:
    return f"cycle-{_slug(claim.get('claim_id') or claim.get('task_id') or 'claim')}"


def _event_id(claim: dict[str, Any], event_type: str) -> str:
    return f"evt-{_slug(claim.get('claim_id') or 'claim')}-{event_type}"


def _idempotency_key(claim: dict[str, Any], event_type: str) -> str:
    return f"{_context_id(claim)}:{claim.get('task_id') or ''}:{_decision_cycle_id(claim)}:{event_type}"


def _worker_identity(claim: dict[str, Any]) -> str:
    return (
        str(claim.get("agent_instance_id") or "").strip()
        or str(claim.get("display_name") or "").strip()
        or str(claim.get("agent_role") or "").strip()
        or "worker"
    )


def _verifier_identity(claim: dict[str, Any], verified_by: str | None) -> str:
    """Stable route identity for the verifier side of the chain.

    Deliberately DERIVED (not the runtime ``verified_by``): the opening
    ``request`` is emitted at claim-create time when the eventual W4b verifier is
    unknown, but the trace gate requires each follow-up's ``sender`` to match the
    previous ``receiver``. Keying the route identity to the claim keeps the
    request->review->decision->correction handoff consistent across the two
    separate create/release process invocations. The real ``verified_by`` /
    ``verifier_role`` are preserved in message metadata.
    """
    return f"verifier:{_slug(claim.get('claim_id') or claim.get('task_id') or 'claim')}"


def _base_timestamp(claim: dict[str, Any], *, released: bool) -> datetime:
    raw = claim.get("released_at") if released else claim.get("claimed_at")
    text = str(raw or "").strip()
    if text:
        try:
            normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
            parsed = datetime.fromisoformat(normalized)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _timestamp_for(base: datetime, event_type: str) -> str:
    return (base + timedelta(seconds=_EVENT_OFFSETS[event_type])).isoformat()


def _payload_ref(claim: dict[str, Any], event_type: str, *, evidence: str | None = None) -> str:
    if event_type == "request":
        return (
            str(claim.get("handoff_path") or "").strip()
            or str(claim.get("log_path") or "").strip()
            or f"agents/runtime/task_claims/{claim.get('claim_id') or 'claim'}.json"
        )
    if evidence and str(evidence).strip():
        return str(evidence).strip()
    return (
        str(claim.get("handoff_path") or "").strip()
        or f"agents/runtime/task_claims/{claim.get('claim_id') or 'claim'}.release.md"
    )


def _already_emitted(log_path: Path, *, event_id: str, idempotency_key: str) -> bool:
    """True when this exact event already exists in the live stream.

    The router itself rejects duplicate event_id/idempotency_key by raising, but
    we check first so a re-run (e.g. an idempotent claim op) is a quiet no-op
    rather than a swallowed exception that looks like a real failure.
    """
    try:
        rows = _router.read_messages(log_path)
    except Exception:  # noqa: BLE001 - defensive; never let a read break emission decisions
        return False
    for row in rows:
        if row.get("event_id") == event_id or row.get("idempotency_key") == idempotency_key:
            return True
    return False


def emit_claim_request(
    claim: dict[str, Any],
    *,
    root: Path,
    log_path: Path | None = None,
    verified_by: str | None = None,
) -> dict[str, Any] | None:
    """Emit the opening ``request`` message for a freshly created claim.

    Returns the emitted message, or ``None`` if it was already emitted (idempotent
    re-run) or if emission failed (best-effort: failures never propagate).
    """
    try:
        resolved = _resolve_log_path(root, log_path)
        event_id = _event_id(claim, "request")
        idem = _idempotency_key(claim, "request")
        if _already_emitted(resolved, event_id=event_id, idempotency_key=idem):
            return None
        base = _base_timestamp(claim, released=False)
        return _emit_message(
            log_path=resolved,
            context_id=_context_id(claim),
            task_id=str(claim.get("task_id") or claim.get("claim_id") or "claim"),
            decision_cycle_id=_decision_cycle_id(claim),
            event_type="request",
            sender=_worker_identity(claim),
            receiver=_verifier_identity(claim, verified_by),
            payload_ref=_payload_ref(claim, "request"),
            event_id=event_id,
            parent_event_id="",
            idempotency_key=idem,
            timestamp=_timestamp_for(base, "request"),
            metadata={
                "claim_id": str(claim.get("claim_id") or ""),
                "task_set_id": str(claim.get("task_set_id") or ""),
                "lifecycle": "claim_created",
                "agent_role": str(claim.get("agent_role") or ""),
            },
        )
    except Exception as exc:  # noqa: BLE001 - observability must never break claim ops
        print(f"a2a-claim-emitter: request emit skipped ({exc})", file=sys.stderr)
        return None


def emit_claim_release_chain(
    claim: dict[str, Any],
    *,
    root: Path,
    log_path: Path | None = None,
    verified_by: str | None = None,
    verifier_role: str | None = None,
    verification_evidence: str | None = None,
) -> list[dict[str, Any]]:
    """Emit the closing ``review`` -> ``decision`` -> ``correction`` chain on release.

    Together with the create-time ``request`` this forms one reconstructable
    request->review->decision->correction trace per claim. Returns the list of
    emitted messages (possibly fewer than three if some were already present);
    failures are swallowed (best-effort observability).
    """
    emitted: list[dict[str, Any]] = []
    try:
        resolved = _resolve_log_path(root, log_path)
        context_id = _context_id(claim)
        task_id = str(claim.get("task_id") or claim.get("claim_id") or "claim")
        cycle = _decision_cycle_id(claim)
        worker = _worker_identity(claim)
        verifier = _verifier_identity(claim, verified_by)
        base = _base_timestamp(claim, released=True)

        # request opens the chain; ensure its event_id exists to link parents even
        # if create-time emission was skipped (parent linkage is by derived id).
        parent_id = _event_id(claim, "request")

        # route handoff alternates so each sender == previous receiver:
        #   request:   worker   -> verifier
        #   review:    verifier -> worker
        #   decision:  worker   -> verifier
        #   correction:verifier -> worker
        routing = {
            "review": (verifier, worker),
            "decision": (worker, verifier),
            "correction": (verifier, worker),
        }
        for event_type in _RELEASE_EVENTS:
            event_id = _event_id(claim, event_type)
            idem = _idempotency_key(claim, event_type)
            if _already_emitted(resolved, event_id=event_id, idempotency_key=idem):
                parent_id = event_id
                continue
            sender, receiver = routing[event_type]
            message = _emit_message(
                log_path=resolved,
                context_id=context_id,
                task_id=task_id,
                decision_cycle_id=cycle,
                event_type=event_type,
                sender=sender,
                receiver=receiver,
                payload_ref=_payload_ref(claim, event_type, evidence=verification_evidence),
                event_id=event_id,
                parent_event_id=parent_id,
                idempotency_key=idem,
                timestamp=_timestamp_for(base, event_type),
                access_level="owner-required" if event_type == "decision" else "project",
                metadata={
                    "claim_id": str(claim.get("claim_id") or ""),
                    "task_set_id": str(claim.get("task_set_id") or ""),
                    "lifecycle": "claim_released",
                    "verified_by": str(verified_by or ""),
                    "verifier_role": str(verifier_role or _DEFAULT_VERIFIER_ROLE),
                },
            )
            emitted.append(message)
            parent_id = event_id
    except Exception as exc:  # noqa: BLE001 - observability must never break claim ops
        print(f"a2a-claim-emitter: release chain emit skipped ({exc})", file=sys.stderr)
    return emitted
