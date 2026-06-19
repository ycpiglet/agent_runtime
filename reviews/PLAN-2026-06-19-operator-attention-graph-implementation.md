---
type: ui-implementation-plan
id: PLAN-2026-06-19-operator-attention-graph-implementation
status: accepted
signal: pass
score: 86
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
task_id: TASK-AR-602
source_rfc: RFC-2026-06-19-ui-ux-design-direction
tags: [ui, ux, design-system, implementation-plan]
---

# Operator Attention Graph Implementation Plan

## Bottom Line

- Summary: turn the accepted `operator_attention_graph` RFC into one focused
  source-mutating implementation task plus one beta/UX evaluation task.
- Result: the follow-up registration input is
  `agents/project/work-items/REGISTRATION-2026-06-19-operator-attention-graph-implementation.json`.
- Boundary: this plan does not mutate UI source files; it defines the next
  W0-W6 work only.

## Signal

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| RFC input | pass | `reviews/RFC-2026-06-19-ui-ux-design-direction.md` accepts `operator_attention_graph` |
| Source target clarity | pass | next implementation target files are `ui_design_assets.py`, `ui_console_assets.py`, and focused UI tests |
| Assetization clarity | pass | token, UI component, pattern component, and one-off boundaries are defined before implementation |
| UX evidence path | pass | beta and UX evaluation are split into a separate evidence task |
| W0-W6 boundary | pass | registration input exists; no source mutation occurs in this derivation task |

## Action

| Role | Next action | Output |
| --- | --- | --- |
| interface-designer | register and claim the source-mutating implementation task | relation assets plus first workflow slice |
| design-system-steward | review token/component/pattern promotions | design-system gate and assetization evidence |
| beta-tester | execute user-like desktop/mobile paths | beta evidence with actions and recovery attempts |
| ux-evaluator | review accessibility, responsive behavior, and defect routing | UX evaluation with BTC-style defect IDs |

## Decision

The next implementation should be one narrow workflow slice:

```text
taskset attention -> claim/evidence preview -> wiki/graph context -> command readiness
```

It should create or reuse relation-aware assets without turning the console
into a broad visual refresh. The first implementation task should target:

- `src/agent_runtime/ui_design_assets.py`
- `src/agent_runtime/ui_console_assets.py`
- `tests/test_ui_design_assets.py`
- `tests/test_ui_console.py`

`src/agent_runtime/ui_console.py` should remain untouched unless the worker
proves a data-wiring change is required. If touched, the worker must record why
page/server assembly could not stay unchanged.

## Assetization

| Surface | Class | Initial tier | Implementation requirement |
| --- | --- | --- | --- |
| relation trace and emphasis values | `design_token` | experimental | use existing semantic tokens first; add new token definitions only if relation states cannot be represented otherwise |
| relation chip | `ui_component` | experimental | render visible state text for default, active, stale, blocked, and focus states |
| evidence preview row | `ui_component` | experimental | show evidence kind, freshness, status label, and target link |
| attention relation panel | `pattern_component` | experimental | combine current item, related artifacts, evidence preview, and command readiness |
| graph context stack | `pattern_component` | experimental | provide narrow-viewport list fallback for graph context |
| implementation-specific helper copy | `one_off_for_now` | temporary | label in closeout and promote before third reuse |

## Implementation Gate

The implementation task must run:

```bash
python -m pytest tests/test_ui_design_assets.py tests/test_ui_console.py -q
python scripts/design_system_gate.py --check --all-ui
python scripts/ui_ux_cycle.py --root . assess --json
python scripts/evidence_index_generator.py --check
```

The worker must also run `git diff --check` and include a W4a verification
record under `reviews/`.

## Data And Schema

The first workflow may use existing console data if it can derive:

- current taskset or attention item;
- owning claim and claim state;
- evidence kind, freshness, status, and target;
- wiki or graph context label and target;
- command readiness state and blocked/interrupted explanation.

If those fields are not available in the current API payload, the worker must
record the schema gap as a follow-up. It should not expand server APIs unless
that target file is explicitly claimed.

## Risk

- Risk: the first slice becomes a broad redesign. Guardrail: only one
  taskset-to-evidence/context/command workflow is in scope.
- Risk: relation assets duplicate existing card/list markup. Guardrail:
  reusable chip, evidence row, and panel helpers are required unless explicitly
  deferred with rationale.
- Risk: graph context becomes decorative. Guardrail: every relation must
  answer ownership, evidence, context, or command-readiness questions.

## Next

- Use the registration input to register the follow-up implementation taskset.
- Claim the implementation task before touching UI source files.
- Run the beta/UX evaluation task after implementation lands.
