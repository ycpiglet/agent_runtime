# Runtime A2A Message Queue

`scripts/a2a_message_router.py` writes explicit agent-to-agent lifecycle
messages to `agents/runtime/a2a/messages.jsonl`.

The queue is append-only JSONL. Each row must keep the same `contextId`,
`taskId`, and `decision_cycle_id` across a request -> review -> decision ->
correction chain. Message rows use `agent-runtime-a2a-message/v1` and include:

- `event_id` and `message_id`
- `parent_event_id` linking each follow-up message to the previous event
- `sender`, `receiver`, and `route`
- `task_context` mirroring `contextId`, `taskId`, and `decision_cycle_id`
- `idempotency_key` and `retry_policy`
- `payload_ref` pointing to the task, review, decision, or correction artifact

`scripts/a2a_trace_gate.py --input agents/runtime/a2a/messages.jsonl` validates
that the chain is reconstructable and blocks missing lifecycle events or broken
handoff links.

## Live emission from the claim lifecycle

`scripts/a2a_claim_emitter.py` wires the router into the real claim lifecycle in
`scripts/task_claim_dispatcher.py`, so actual agent work produces live A2A
traffic instead of leaving the stream empty:

- claim **create** -> `request` (opens the chain; worker -> verifier)
- claim **release** -> `review` -> `decision` -> `correction` (closes the chain)

Identifiers are derived deterministically from the claim (`contextId` from the
task, `decision_cycle_id` from the claim id, each `event_id`/`parent_event_id`
from `(claim_id, event_type)`) so the request emitted at create time and the
review/decision/correction emitted at release time link into one reconstructable
chain even though they run in separate processes. Emission is additive
observability only: it records messages, never changes who gets a claim, is
idempotent per claim, and a failure never breaks the claim operation.
