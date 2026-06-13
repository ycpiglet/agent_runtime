# REVIEW-2026-06-13 taskset boundary execution guard (TASK-AR-328)

## Bottom Line

When a specific taskset is dispatched, the runtime now records that taskset as
the claim's active scope, emits a `taskset.completed` event when it finishes,
and BLOCKS starting new out-of-scope work after completion via a new owner
governance gate. The Owner observed real drift after completion (unregistered
follow-on work); this promotes "stop and report at the taskset boundary" from a
prose reminder into an executable policy + UI signal.

## Problem

After a dispatched taskset completed, work sometimes drifted into adjacent /
unregistered follow-on tasks instead of stopping and reporting. There was no
runtime record of "the scope we were told to execute" and no gate that judged
"starting NEW work outside that scope after completion" as a violation.

## Design

Lazy, OFF-by-default guard so existing flows and the clean-repo stop-hook
approve path are never affected:

- `taskset_dispatcher.py` passes `--active-scope <task_set_id>`; the claim
  records `active_scope` (defaults to `task_set_id`) plus
  `scope_transition_approved` (`task_claim_dispatcher.py`).
- On release with `phase == taskset-completed`, the dispatcher emits a
  `taskset.completed` pane event (scope CLOSED from that point).
- New gate `scripts/taskset_boundary_gate.py`:
  - No-op (pass) unless some released claim recorded an `active_scope` and
    reached `phase == taskset-completed`. This keeps it inert in a clean repo
    and for all pre-existing tasksets, so it cannot regress
    `tests/test_stop_hook_owner_governance.py` (which expects `approve`).
  - BLOCK only when an ACTIVE claim's `task_set_id` differs from a completed
    scope AND the claim was created AFTER that completion AND it carries no
    owner `scope_transition_approved` marker. That is precisely the
    post-completion out-of-scope drift state.
  - Same-scope follow-on (a remaining task in the set) and pre-completion
    parallel claims are NOT blocked.
- Chained into `scripts/owner_governance_gate.py` (after `taskset_work_gate`,
  before `evidence_index_generator`) and mirrored into the template gate
  (parity guard `tests/test_owner_governance_chain_parity.py`).

## Escape / transition path

Consistent with other repo gates (block vs watch, loud transitional escapes):

- `--allow-scope-transition` downgrades blocks to one-line `watch` findings and
  prints a loud stderr warning.
- A new claim created with `--scope-transition-approved` (owner-approved scope
  change) records `scope_transition_approved: true` and is not blocked.

## UI

`ui_state.build_taskset_completion` derives a completion banner from the latest
`taskset.completed` pane event plus the computed task-set summary; the
next-taskset suggestion is explicitly `awaiting_approval` (no auto-start).
`ui_console.py` renders the banner on the Tasksets view
(`#taskset-completion-banner` + `renderTasksetCompletion`) and serves
`/api/taskset_completion`. All banner CSS reuses existing theme tokens
(`--success`, `--success-soft`, `--success-line`, `--muted`, `--subtle`,
`--tile`, `--raise`, `--line-strong`), so the raw-hex token gate still passes.

## Evidence added

- Gate (root + template): `scripts/taskset_boundary_gate.py`,
  `src/agent_runtime/templates/project/scripts/taskset_boundary_gate.py`
- Chain wiring: `scripts/owner_governance_gate.py`,
  `src/agent_runtime/templates/project/scripts/owner_governance_gate.py`
- Scope recording + completion event: `scripts/task_claim_dispatcher.py`,
  `scripts/taskset_dispatcher.py` (+ template mirrors)
- UI: `src/agent_runtime/ui_state.py`, `src/agent_runtime/ui_console.py`
- Tests: `tests/test_taskset_boundary_gate.py`,
  `tests/test_task_claim_dispatcher.py`, `tests/test_ui_state.py`,
  `tests/test_ui_console.py`

## Acceptance

- Out-of-scope new work after taskset completion is BLOCKED by the gate
  (test_gate_blocks_out_of_scope_work_after_completion).
- In-scope follow-on, pre-existing parallel work, approved transitions, and the
  no-active-scope / not-yet-completed cases are NOT blocked (no regression).
- `taskset.completed` is emitted on completion and absent otherwise.
- Stop-hook approve path verified unchanged.
