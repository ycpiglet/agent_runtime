---
id: REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation
status: draft
owner: lead-engineer
task_set_id: TASKSET-AR-RSI-PLANNING
tasks:
  - TASK-AR-234
  - TASK-AR-235
  - TASK-AR-236
  - TASK-AR-237
  - TASK-AR-238
  - TASK-AR-239
  - TASK-AR-240
  - TASK-AR-241
  - TASK-AR-242
  - TASK-AR-243
  - TASK-AR-244
  - TASK-AR-245
created: 2026-06-10
---

# RSI Planning Loop Implementation Review

## Bottom Line

The RSI planning loop now has a proposal-only B-mode implementation path:
contract, proposal schema, read-only scan, proposal outbox, draft task writer,
planning gate, UI Planner panel, approved apply skeleton, release steward,
retro synthesizer, trace/eval ingestion, guardrail policy, diversity council
protocol, and C-mode promotion gate.

## Signal

- Contract: `agents/project/PLANNING-LOOP-CONTRACT.md`.
- Proposal schema: `schemas/planning-proposal.schema.json`.
- Guardrails: `agents/project/PLANNING-GUARDRAILS.yml`.
- C-mode checklist: `agents/project/C-MODE-PROMOTION-CHECKLIST.md`.
- Council protocol: `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md`.
- Runtime implementation: `scripts/planning_loop.py`.
- Release/version steward: `scripts/release_version_consistency_steward.py`.
- UI command and panel: `src/agent_runtime/ui_commands.py`, `src/agent_runtime/ui_state.py`, `src/agent_runtime/ui_console.py`.
- Tests added: `tests/test_planning_loop.py`, `tests/test_release_version_consistency_steward.py`, `tests/test_planning_ui.py`.

## Insight

B-mode is the safe default because scan/proposal/draft outputs remain
inspectable and reversible. C-mode remains blocked until repeated proposal-only
cycles, release steward status, guardrail status, rollback proof, owner policy,
and diversity council review all pass.

## Decision

- Treat proposal generation as safe local work.
- Treat canonical apply, release/version movement, publication, dependency
  install, secret/prod-data changes, destructive changes, and gate weakening as
  owner-boundary work.
- Keep UI scan requests queued and gated; the UI cannot apply proposals.

## Action Board

- `TASK-AR-234`: planning loop contract and proposal schema implemented.
- `TASK-AR-235`: deterministic read-only scan implemented.
- `TASK-AR-236`: proposal outbox and draft task writer implemented.
- `TASK-AR-237`: planning gate and UI-trigger-safe scan request implemented.
- `TASK-AR-238`: Planner panel state resource and read-only console tab implemented.
- `TASK-AR-239`: approved apply skeleton implemented for supported low-risk `new_task` proposals.
- `TASK-AR-240`: release/version steward script restored for proposal-only report generation.
- `TASK-AR-241`: compound/retro synthesizer path implemented.
- `TASK-AR-242`: department/council protocol documented and linked.
- `TASK-AR-243`: trace/eval/correction/A2A evidence ingestion implemented.
- `TASK-AR-244`: guardrail policy and gate checks implemented.
- `TASK-AR-245`: C-mode promotion gate implemented and default-blocking.

## Next

Run targeted tests and gates, then close task statuses and claim artifacts only
after verification evidence exists.


## Hook and Schedule Integration Addendum

- Owner governance hook path now includes `scripts/planning_loop.py gate --trigger hook --action scan` through `scripts/owner_governance_gate.py`.
- Schedule/manual proposal-only trigger entrypoint: `scripts/planning_trigger.py`.
- Boundary: both paths run gate/scan/propose only and keep `canonical_mutation_allowed=false`.
- Verification status: pending; `scripts/verify_rsi_planning_taskset.py` includes the schedule trigger check but has not been run in this slice.

## Verification and Closeout Procedure

- Verification command: `python scripts/verify_rsi_planning_taskset.py --out reviews/RSI-PLANNING-TASKSET-VERIFY.json`.
- Closeout dry run: `python scripts/close_rsi_planning_taskset.py --verification-report reviews/RSI-PLANNING-TASKSET-VERIFY.json --json`.
- Closeout apply after verification pass: `python scripts/close_rsi_planning_taskset.py --verification-report reviews/RSI-PLANNING-TASKSET-VERIFY.json --apply --json`.
- Final completion proof: closeout apply must report `status=pass`, including backlog board regeneration, named task-set require-complete gate, and owner governance gate.
- Boundary: no completion claim before this procedure passes.

## Proposal Outbox Dedupe Maintenance (2026-06-10T23:15:00+09:00)

- Added and applied `scripts/planning_loop.py dedupe-outbox --apply`.
- Result: status `pass`; six older duplicate proposal records were marked `superseded`, with the latest proposal retained per dedupe key.
- Changed proposal records:
  - `agents/planning/outbox/PROP-A067489BF476.json`
  - `agents/planning/outbox/PROP-D82A7F8031DD.json`
  - `agents/planning/outbox/PROP-F3AE867AB70B.json`
  - `agents/planning/outbox/PROP-348B9A5A03B5.json`
  - `agents/planning/outbox/PROP-4E287D09FAEA.json`
  - `agents/planning/outbox/PROP-52110EF7CBF8.json`
- Boundary: no canonical backlog/task/status closeout was performed.
