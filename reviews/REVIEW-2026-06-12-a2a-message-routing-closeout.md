# REVIEW: TASK-AR-311 A2A Message Routing Closeout

## Scope

- Task: `TASK-AR-311`
- Task set: `TASKSET-AR-VISION-GAP-CLOSURE`
- Goal: replace inferred agent handoffs with explicit local A2A message routing and make `a2a_trace_gate.py` validate message-based chains.

## Changes

- Added `scripts/a2a_message_router.py`.
  - Emits append-only JSONL messages under `agents/runtime/a2a/messages.jsonl`.
  - Preserves `contextId`, `taskId`, and `decision_cycle_id` across the lifecycle.
  - Writes `parent_event_id`, route, retry policy, idempotency key, payload reference, and task context.
  - Rejects duplicate `event_id` and `idempotency_key`.
- Added `agents/runtime/a2a/README.md`.
  - Defines the runtime queue contract and gate command.
- Extended `scripts/a2a_trace_gate.py`.
  - Accepts existing `agent-runtime-a2a-envelope/v1` trace rows.
  - Adds validation for `agent-runtime-a2a-message/v1` rows.
  - Blocks broken message parent links and sender/receiver handoff discontinuity.
- Added `tests/test_a2a_message_router.py`.
  - Proves a lead-engineer <-> qa request -> review -> decision -> correction chain.
  - Proves duplicate idempotency rejection.
  - Proves gate pass for message logs and gate block for broken parent links.

## Verification

- `python -m py_compile scripts/a2a_message_router.py scripts/a2a_trace_gate.py` -> pass.
- `pytest tests/test_a2a_message_router.py -q` -> 4 passed.
- `pytest tests/test_a2a_message_router.py tests/test_planning_evidence_link.py -q` -> 7 passed.
- `python scripts/a2a_trace_gate.py --input agents/project/a2a/a2a-trace-baseline-2026-06-09.jsonl --out .tmp/a2a-trace-gate-task-ar-311-baseline.json` -> status=pass, events=4, chains=1.

## Boundary

This closes the local file-backed A2A message routing layer and deterministic
gate proof. It does not claim networked A2A transport, external agent discovery,
or live multi-process RBAC proof; those remain separate Vision Integrator tasks.
