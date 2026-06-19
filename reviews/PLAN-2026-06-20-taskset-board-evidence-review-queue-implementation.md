---
type: ui-implementation-plan
id: PLAN-2026-06-20-taskset-board-evidence-review-queue-implementation
status: accepted
signal: pass
score: 90
priority: High
date: 2026-06-20
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
task_id: TASK-AR-618
claim_id: CLAIM-20260620-010012-task-ar-618-task-ar-618-evidence-perf-implementation-plan
source_rfc: RFC-2026-06-19-taskset-board-evidence-performance-ia
tags: [ui, ux, design-system, taskset-board, evidence-review-queue, implementation-plan]
---

# Taskset Board Evidence Review Queue Implementation Plan

## Bottom Line

- Summary: turn the accepted `evidence_review_queue_with_progressive_disclosure_and_split_loading` RFC into one source-mutating implementation task and one beta/UX evaluation task.
- Result: the follow-up registration input is `agents/project/work-items/REGISTRATION-2026-06-20-taskset-board-evidence-review-queue-implementation.json`.
- Boundary: this plan does not mutate UI source files. Source mutation starts only after the follow-up implementation taskset is registered and claimed.

## Signal

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| RFC input | pass | `reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md` accepts the combined evidence queue, progressive disclosure, and split loading direction. |
| Prior beta input | pass | `reviews/BETA-TEST-2026-06-19-tsaw-claim-empty-refinement.md` and `reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md` identify evidence overload and latency as next design risks. |
| Source target clarity | pass | Source mutation is limited to `ui_state.py`, `ui_design_assets.py`, `ui_console_assets.py`, and focused UI tests. |
| Schema clarity | pass | The registration input names `attention_workspace.evidence_review_queue` and required summary/detail fields. |
| Assetization clarity | pass | Token, UI component, pattern component, and one-off boundaries are named before implementation. |
| UX evidence path | pass | Beta and UX evidence are split into a separate task with clicked/typed, keyboard, mobile, reduced-motion, and latency paths. |

## Decision

Register the next taskset as `TASKSET-AR-TASKSET-BOARD-EVIDENCE-REVIEW-QUEUE`.

The next implementation should keep the existing Taskset Board attention workspace, then add an evidence review queue inside it:

```text
Taskset Board
-> attention workspace
-> evidence review queue summary
-> group filter
-> capped queue rows
-> selected evidence detail
-> retry, defer, or route as BTC
```

The first implementation should target:

- `src/agent_runtime/ui_state.py`
- `src/agent_runtime/ui_design_assets.py`
- `src/agent_runtime/ui_console_assets.py`
- `tests/test_ui_state.py`
- `tests/test_ui_console.py`
- `tests/test_ui_design_assets.py`

`src/agent_runtime/ui_console.py` should remain untouched unless the worker proves a route or server assembly change is required. If touched, the worker must record why the existing `/api/tasksets_board` and shell assembly boundaries were insufficient.

## Schema And API

The implementation should add a read-only derived payload at:

```text
tasksets_board.items.attention_workspace.evidence_review_queue
```

Required fields:

| Field | Purpose |
| --- | --- |
| `version` | Must be `taskset_evidence_review_queue/v1`. |
| `summary_loaded_at` | Textual latency and freshness context. |
| `detail_loading_state` | Summary-ready, detail-loading, stale-summary, timeout-watch, or retryable. |
| `selected_group_id` | Default group for first viewport triage. |
| `selected_taskset_id` | Selected row/detail anchor. |
| `groups[].id`, `label`, `count` | Group identity and total size. |
| `groups[].visible_count`, `hidden_count` | Progressive disclosure and cap transparency. |
| `groups[].ordering_reason` | Why this group/row ordering is meaningful. |
| `groups[].freshness`, `severity` | Textual non-color state. |
| `groups[].items[]` | Queue rows with taskset id, title, owner/team, progress, evidence freshness, evidence age, severity, active claim, claim phase, command readiness, reason, and detail loading state. |

The implementation may initially derive this synchronously from the existing Taskset Board cards. It still must expose summary/detail state labels now so a later true async split can reuse the same schema.

## Assetization

| Surface | Class | Initial tier | Implementation requirement |
| --- | --- | --- | --- |
| evidence freshness aliases | `design_token` | experimental | map stale, aging, fresh, missing, unverified, retryable to existing semantic status tokens first. |
| evidence severity/order aliases | `design_token` | experimental | encode urgent, blocked, stale, deferrable, recently changed as semantic ordering roles, not new palette choices. |
| queue density roles | `design_token` | experimental | compact spacing/type roles for filters, queue rows, cap disclosure, and detail state. |
| loading and latency aliases | `design_token` | experimental | summary-ready, detail-loading, timeout-watch, retryable, stale-summary labels. |
| evidence group filter | `ui_component` | experimental | visible count, selected state, keyboard focus, and non-color cue. |
| lane cap disclosure | `ui_component` | experimental | visible count, hidden count, ordering reason, and drill-in affordance. |
| latency budget badge | `ui_component` | experimental | summary age, detail loading, stale summary, timeout, and retryable labels. |
| evidence queue row | `ui_component` | experimental | taskset id/title, freshness, severity, owner/team, command readiness, selected/focus state. |
| evidence review queue | `pattern_component` | experimental | group filter, capped rows, selected detail, retry/defer state, keyboard traversal. |
| split board loading shell | `pattern_component` | experimental | summary-first loading and recoverable detail states. |
| inactive view containment shell | `pattern_component` | experimental | distinguishes active viewport fit from inactive DOM scan noise. |
| first-cycle orientation copy | `one_off_for_now` | temporary | allowed for one beta cycle; promote or remove before a third use. |

## Implementation Gate

The implementation task must run:

```bash
python -m pytest tests/test_ui_state.py tests/test_ui_console.py tests/test_ui_design_assets.py -q
python scripts/design_system_gate.py --check --all-ui
python scripts/ui_ux_cycle.py --root . assess --json
python scripts/evidence_index_generator.py --check
git diff --check
```

The worker must create W4a verification evidence under `reviews/` and leave the source-mutating claim ready for independent W4b verification.

## Beta Gate

The beta task must prove:

- unknown evidence triage from first viewport to selected detail;
- known target retrieval by taskset id/title;
- capped group drill-in with visible count, hidden count, and ordering reason;
- slow detail, stale summary, timeout/retry, defer/action, empty group, blocked command, interrupted claim, expired claim, and no active claim states;
- keyboard traversal through filters, cap disclosure, rows, detail, retry/defer controls, and fallback list;
- desktop and 390x844 mobile viewport fit;
- reduced-motion behavior and non-color-only state.

## Risks

| Risk | Impact | Guardrail |
| --- | --- | --- |
| Queue hides urgent items behind a cap. | Operators miss high-risk evidence gaps. | Sorting must expose severity/freshness reasons and hidden counts. |
| Split loading creates false freshness. | Users trust stale detail. | Always show summary age and detail loading state text. |
| UI assets duplicate page markup. | Design-system debt returns. | Repeated filter, cap, row, badge, and pattern surfaces live in asset helpers. |
| Schema is too expensive to compute. | The board remains slow. | Start with a read-only summary/detail contract and preserve a path for async split. |
| Beta evidence becomes screenshot-only. | User workflows are not proved. | Require clicked/typed paths, keyboard steps, viewport/data state, and BTC routing. |

## Next

- Use the registration input to register the follow-up implementation taskset.
- Claim the implementation task before touching UI source files.
- Run the paired beta/UX evaluation after the implementation is merged or available in a verification worktree.
