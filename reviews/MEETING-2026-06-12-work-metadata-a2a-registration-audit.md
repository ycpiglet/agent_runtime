---
type: meeting
id: MEETING-2026-06-12-work-metadata-a2a-registration-audit
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [planning-record, backlog-audit, work-items, metadata, a2a, agent-identity]
---

# Work Metadata And A2A Registration Audit

## Bottom Line

- Summary: audited whether the Owner/Claude/Codex discussion about A2A,
  Work Items, metadata, generators, statistics, and agent identity exists as
  durable task records.
- Result: A2A core work is registered and mostly completed in archived task
  sets; Work hierarchy and generator work is visible on the live board; the
  broader metadata/analytics/agent-attribution follow-up is now explicitly
  registered as `TASKSET-AR-WORK-METADATA-ANALYTICS`.
- Boundary: this record is an audit and routing decision. It does not claim the
  missing follow-up tasks are implemented.

## Signal

| Topic | Registration State | Board Visibility | Evidence |
| --- | --- | --- | --- |
| A2A message routing | registered/completed | archived, not live Action Board | `TASK-AR-311`, `reviews/REVIEW-2026-06-12-a2a-message-routing-closeout.md` |
| A2A lifecycle proof | registered/completed | archived, not live Action Board | `TASK-AR-302`, `reviews/REVIEW-2026-06-12-agent-runtime-rsi-operating-system-closeout.md` |
| Trace/eval/A2A proposal evidence | registered/completed | archived, not live Action Board | `TASK-AR-243`, `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md` |
| Work hierarchy naming and numbering | registered/partly completed | live under `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE` plus archived `TASK-AR-369` | `TASK-AR-369` through `TASK-AR-374` |
| Work registration generator | registered/planned | live Action Board | `TASK-AR-372` |
| Work Item envelope schema/gate | registered for follow-through | live Action Board | `TASK-AR-515` |
| `work stats` metadata consumer | registered for follow-through | live Action Board | `TASK-AR-517` |
| Work Explorer tree and roll-up | registered for follow-through | live Action Board | `TASK-AR-516` |
| Agent instance attribution across evidence/A2A/commits | registered for follow-through | live Action Board | `TASK-AR-518` |
| Metadata field catalog, query/export, analytics dimensions | registered for follow-through | live Action Board | `TASK-AR-515`, `TASK-AR-517` |
| Verification freshness/stale evidence | registered for follow-through | live Action Board | `TASK-AR-519` |
| Conversation-to-work traceability | registered for follow-through | live Action Board | `TASK-AR-514` |

## Insight

- The board is not empty: `BACKLOG-BOARD.md` currently shows live work for
  `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE` and
  `TASKSET-AR-PARALLEL-WAVE-EXECUTION`, and archived rows for completed A2A
  tasks.
- The Owner's confusion is valid because completed A2A items are hidden from
  the live Action Board by design, while newer metadata and attribution ideas
  were implemented or discussed across several surfaces without a single
  Owner-facing taskset that says "this is the remaining metadata/A2A analytics
  follow-up."
- Existing generic UI/platform tasks are too broad to serve as acceptance
  criteria for the recent discussion. The new metadata taskset makes Work Item
  envelope fields, instance attribution, evidence references, stale
  verification, and dimension/metric analytics explicit.
- Root checkout is currently ahead/behind `origin/main`, so board trust also
  depends on syncing or deliberately choosing the current canonical worktree
  before updating tasks.

## Decision

- Decision: treat A2A core as registered/completed unless the desired scope is
  external/network A2A transport or deeper attribution analytics.
- Decision: treat Work hierarchy/generator work as registered but incomplete:
  continue through `TASK-AR-370` through `TASK-AR-374`.
- Decision: use `TASKSET-AR-WORK-METADATA-ANALYTICS` as the dedicated follow-up
  registration for the remaining metadata/analytics/agent-attribution ideas.
- Decision: do not rely on broad platform tasks as the only tracking surface
  when Owner discussion produced measurable metadata and verification
  requirements.

## Action Board

| Status | Action | Owner | Evidence |
| --- | --- | --- | --- |
| Done | Confirm A2A routing and lifecycle are already recorded | lead-engineer | `TASK-AR-311`, `TASK-AR-302` |
| Done | Confirm Work hierarchy/generator work is live on board | lead-engineer | `TASK-AR-370` through `TASK-AR-374` |
| Done | Register missing metadata/analytics follow-up as a dedicated taskset | planning-office | `TASK-AR-514` through `TASK-AR-519` |
| Watch | Decide whether recent `work stats` and schema PRs need backfilled task records | lead-engineer | root/origin reconciliation |
| Watch | Update next-session pointer after root/worktree cleanup | lead-engineer | `agents/project/NEXT-SESSION-POINTER.yml` |

## Proposed Follow-Up Registration

| Proposed Task | Scope | Verification |
| --- | --- | --- |
| `TASK-AR-515` | `WORK-SCHEMA.yml` fields for provenance, resolution, relationships, verification, routing, display/search, and schema version | schema gate fixtures plus unknown-field watch |
| `TASK-AR-516` | Initiative -> Taskset -> Task -> Unit tree with level filters, facet filters, and computed progress only | UI/API tests plus board snapshot |
| `TASK-AR-517` | group-by, filters, CSV/JSON export, saved views, computed-only metrics | `work stats` tests plus export fixtures |
| `TASK-AR-518` | require `instance_uid` actor in claims, A2A messages, evidence, closeout, and optional commit trailers | attribution gate with role-only watch/block fixtures |
| `TASK-AR-519` | mark evidence stale when source files or commits move after verification | stale fixture plus closeout gate |

## Risks / Blockers

- Risk: the Owner sees nothing in the live board for completed A2A because the
  board intentionally archives completed tasks. The board needs a clearer
  "recently completed / relevant archived evidence" affordance.
- Risk: without a dedicated metadata taskset, future agents may claim the
  conversation was handled by generic search/dashboard/platform tasks even
  though measurable acceptance criteria are missing.
- Blocker: root checkout is ahead/behind `origin/main`; avoid broad task edits
  until canonical base is selected.

## Next Steps

- Start `TASKSET-AR-WORK-METADATA-ANALYTICS` from the live board after root and
  worktree cleanup.
- Keep each task's acceptance criteria and verification commands explicit before
  implementation.
- Regenerate `BACKLOG-BOARD.md`, `reviews/INDEX.md`, and
  `WORK-ITEM-CLASSIFICATION.md` after task registration.
- Update `NEXT-SESSION-POINTER.yml` so the next session starts from the
  registered follow-up, not from stale broad UI tasksets.
