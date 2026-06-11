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
