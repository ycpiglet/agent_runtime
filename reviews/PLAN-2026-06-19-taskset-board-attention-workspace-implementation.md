---
type: ui-implementation-plan
id: PLAN-2026-06-19-taskset-board-attention-workspace-implementation
status: accepted
signal: pass
score: 88
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
task_id: TASK-AR-611
claim_id: CLAIM-20260619-182000-task-ar-611-task-ar-611-implementation-beta
source_rfc: RFC-2026-06-19-taskset-board-ia-design-direction
tags: [ui, ux, design-system, taskset-board, implementation-plan]
---

# Taskset Board Attention Workspace Implementation Plan

## Bottom Line

- Summary: turn the accepted `taskset_attention_workspace` RFC into one focused
  source-mutating implementation task plus one beta/UX evaluation task.
- Result: the follow-up registration input is
  `agents/project/work-items/REGISTRATION-2026-06-19-taskset-board-attention-workspace-implementation.json`.
- Boundary: this plan does not mutate UI source files. Source mutation starts
  only after the follow-up implementation task is registered and claimed.

## Signal

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| RFC input | pass | `reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md` accepts `taskset_attention_workspace`. |
| Board scale problem | pass | The RFC records 49 tasksets and whole-board scanning as the problem to solve. |
| Source target clarity | pass | Target files are `ui_state.py`, `ui_console_assets.py`, `ui_design_assets.py`, and focused UI tests. |
| Assetization clarity | pass | Token, UI component, pattern component, and one-off boundaries are defined before implementation. |
| UX evidence path | pass | Beta and UX evaluation are split into a separate evidence task. |
| W0-W6 boundary | pass | Registration input exists; no UI source mutation occurs in `TASK-AR-611`. |

## Action

| Role | Next action | Output |
| --- | --- | --- |
| interface-designer | register and claim the source-mutating implementation task | attention lane schema and workspace UI |
| design-system-steward | review token/component/pattern promotions | design-system gate and assetization evidence |
| beta-tester | execute user-like desktop/mobile paths | beta evidence with actions and recovery attempts |
| ux-evaluator | review accessibility, responsiveness, reduced motion, and defect routing | UX evaluation with BTC-TSAW defect IDs |

## Decision

The next implementation should make Taskset Board open as:

```text
Taskset Board -> attention lanes -> selected taskset summary -> relation detail -> all tasksets fallback
```

The full board remains available and searchable. The first viewport should
prioritize lanes for active claims, guarded or interrupted work, stale/missing
evidence, recently changed tasksets, and ready next-action candidates. Every
lane card must explain why it is present.

The first implementation task should target:

- `src/agent_runtime/ui_state.py`
- `src/agent_runtime/ui_console_assets.py`
- `src/agent_runtime/ui_design_assets.py`
- `tests/test_ui_state.py`
- `tests/test_ui_console.py`
- `tests/test_ui_design_assets.py`

`src/agent_runtime/ui_console.py` should remain untouched unless the worker
proves a route or server data-wiring change is required. If touched, the worker
must record why the page/server assembly boundary could not stay unchanged.

## Assetization

| Surface | Class | Initial tier | Implementation requirement |
| --- | --- | --- | --- |
| attention state aliases | `design_token` | experimental | reuse existing pass/warn/block/info/active tokens first; add aliases only in token definitions if lane states cannot be distinguished |
| taskset quick switcher | `ui_component` | experimental | keyboard-first typeahead with result count, selected state, empty state, and jump target |
| attention lane filter | `ui_component` | experimental | segmented or tab-like control with count, focus state, label, and non-color cue |
| taskset attention lane | `pattern_component` | experimental | combine taskset identity, claim state, evidence freshness, command readiness, and membership reason |
| relation detail panel | `pattern_component` | experimental | extend `patternAttentionRelationPanel` and evidence preview responsibilities without duplicating relation markup |
| migration helper copy | `one_off_for_now` | temporary | allowed only for the first beta cycle; promote or remove before a third use |

## Schema And API

The implementation should use the existing `tasksets_board` resource first.
Required fields already present or derivable from the current board contract:

- `id`, `title`, `status`, `status_bucket`;
- `progress.done`, `progress.total`, `progress_pct`;
- `claim_summary.state`, `claim_summary.label`,
  `claim_summary.command_state`, `claim_summary.command_label`;
- `recent_activity`;
- `children[].phase`, `children[].claim_summary`,
  `children[].relation_state`;
- `assigned_agents`.

If lane membership needs fields beyond this list, the implementation task must
add a small read-only adapter in `ui_state.py` before rendering. It must not
write task, claim, board, or registry records.

## Implementation Gate

The implementation task must run:

```bash
python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py tests/test_ui_state.py -q
python scripts/design_system_gate.py --check --all-ui
python scripts/ui_ux_cycle.py --root . assess --json
python scripts/evidence_index_generator.py --check
git diff --check
```

The worker must also create W4a verification evidence under `reviews/` and
leave the source-mutating claim ready for independent W4b verification.

## Risk

| Risk | Impact | Guardrail |
| --- | --- | --- |
| Attention lanes hide quiet work. | Operators may miss tasksets outside the first viewport. | Keep All Tasksets searchable and keyboard reachable. |
| Lane rules become UI guesses. | Data semantics drift from task and claim truth. | Name every lane input field before rendering. |
| Switcher becomes the whole solution. | Unknown-target discovery remains weak. | Treat switcher as supporting retrieval, not primary IA. |
| New tokens become palette drift. | Design-system maturity regresses. | Reuse semantic tokens first; new tokens start experimental. |
| Detail panel duplicates OAG assets. | Component debt returns. | Extend current relation chip, evidence row, graph stack, and panel helpers. |

## Next

- Use the registration input to register the follow-up implementation taskset.
- Claim the implementation task before touching UI source files.
- Run the beta/UX evaluation after implementation lands.
