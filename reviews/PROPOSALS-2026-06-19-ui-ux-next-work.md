---
type: ui-ux-next-work-proposals
id: PROPOSALS-2026-06-19-ui-ux-next-work
status: planned
signal: watch
score: 80
priority: Medium
tags: [ui, ux, design-system, proposal]
---

# UI/UX Next Work Proposals 2026-06-19

## Bottom Line

- Summary: proposal-only UI/UX next-work options are preserved for later task
  registration.
- Result: no UI source mutation is authorized by this record.
- Boundary: follow-up implementation still requires W0-W6 registration and
  claim-first execution.

## Signal

| Proposal | Status | Lead | Evidence |
| --- | --- | --- | --- |
| design_direction_rfc | accepted_rfc | lead-designer | `reviews/RFC-2026-06-19-ui-ux-design-direction.md` |
| implementation_refactor | registration_input_ready | interface-designer | `agents/project/work-items/REGISTRATION-2026-06-19-operator-attention-graph-implementation.json` |
| ux_evaluation_pass | beta_plan_ready | ux-evaluator | `reviews/BETA-PLAN-2026-06-19-operator-attention-graph.md` |
| taskset_board_ia_rfc | seminar_accepted | lead-designer | `reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md` |

## Action

- Register a concrete follow-up task before touching UI source files.
- Keep this record as proposal evidence only.
- Use design-system and UX review roles before implementation begins.

## Risk

- Risk: treating this proposal as an active task would bypass W0-W6.
- Risk: implementation without design direction review may repeat the current
  visual direction.
- Guardrail: source files remain out of scope until a claim exists.

## Decision

- Decision: preserve the proposals as next-work options, not as active work.
- Decision: design exploration, implementation refactor, and UX evaluation stay
  separate work items.

## Next

- Use `reviews/SEMINAR-2026-06-19-ui-ux-design-direction.md` as the selected
  seminar input for the design-direction RFC.
- Use `reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md` as the
  selected seminar input for the next Taskset Board IA RFC.
- Choose the selected proposal and register the RFC task before UI/UX
  implementation work resumes.
- Run focused UI tests and the design-system gate for any future implementation.

## Proposals

### design_direction_rfc

- Status: `accepted_rfc`
- Lead role: `lead-designer`
- Supporting roles: design-system-steward, ux-evaluator
- Review roles: interface-designer
- Future target files: DESIGN.md, docs/design/agent-runtime/DESIGN-SYSTEM.md
- Proposal artifacts: reviews/RFC-2026-06-19-ui-ux-design-direction.md, reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md

Create a Design Exploration RFC when the current visual direction is too repetitive, including references, token delta, component/pattern needs, and responsive/a11y acceptance criteria.

Outcome: `reviews/RFC-2026-06-19-ui-ux-design-direction.md` accepts
`operator_attention_graph`. UI source mutation remains blocked until the next
claimed implementation task.

Acceptance criteria:
- States the user problem, target screen, workflow, and why the existing direction is insufficient.
- Provides 2-3 references or screenshots and records accepted/rejected/promoted outcome.
- Lists minimum token, UI component, and pattern component deltas before implementation.

### implementation_refactor

- Status: `registration_input_ready`
- Lead role: `interface-designer`
- Supporting roles: design-system-steward
- Review roles: ux-evaluator
- Future target files: src/agent_runtime/ui_console_assets.py, src/agent_runtime/ui_design_assets.py, tests/test_ui_console.py, tests/test_ui_design_assets.py
- Proposal artifacts: reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md

Register and claim the next implementation unit only after this proposal is reviewed; page files stay focused on layout/data wiring and repeated UI moves into pattern assets.

Outcome: `TASK-AR-602` produced
`agents/project/work-items/REGISTRATION-2026-06-19-operator-attention-graph-implementation.json`
and `reviews/PLAN-2026-06-19-operator-attention-graph-implementation.md`.

Acceptance criteria:
- Classifies touched UI as design_token, ui_component, pattern_component, or one_off_for_now.
- Uses existing tokens/components first and records any token/component promotion explicitly.
- Runs focused UI tests plus the design-system gate before W4a closeout.

### ux_evaluation_pass

- Status: `beta_plan_ready`
- Lead role: `ux-evaluator`
- Supporting roles: beta-tester, interface-designer
- Review roles: design-system-steward
- Future target files: reviews/SEMINAR-2026-06-19-next-ui-task-ui-ux.md, reviews/MEETING-2026-06-19-next-ui-task-ui-ux.md, reviews/BETA-TEST-2026-06-19-next-ui-task-ui-ux.md
- Proposal artifacts: reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md, reviews/SEMINAR-2026-06-19-next-ui-task-ui-ux.md, reviews/MEETING-2026-06-19-next-ui-task-ui-ux.md, reviews/BETA-TEST-2026-06-19-next-ui-task-ui-ux.md

Plan the post-implementation beta-tester/evaluator pass with clicked/typed actions, edge and recovery attempts, environment notes, and BTC-style visible-defect IDs.

Outcome: `TASK-AR-602` produced
`reviews/BETA-PLAN-2026-06-19-operator-attention-graph.md` for the post-
implementation beta/UX evaluation task.

Acceptance criteria:
- Records user-like actions instead of screenshot-only evidence.
- Covers recovery, empty, interrupted, and responsive states where relevant.
- Links every user-visible defect to a BTC-style failure ID and reproduction path.

### taskset_board_ia_rfc

- Status: `seminar_accepted`
- Lead role: `lead-designer`
- Supporting roles: design-system-steward, interface-designer, ux-evaluator
- Review roles: beta-tester
- Future target files: reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md, docs/design/agent-runtime/DESIGN.md, docs/design/agent-runtime/DESIGN-SYSTEM.md
- Proposal artifacts: reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md, reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md

Publish a Design Exploration RFC for `taskset_attention_workspace`: an
attention-lane Taskset Board IA with a supporting taskset switcher and relation
detail panel. The user problem is the post-OAG board scale watch: `49` tasksets
make target discovery and whole-board focus traversal long.

Outcome: `TASK-AR-609` accepted `taskset_attention_workspace` as the RFC
candidate. UI source mutation remains blocked until the RFC is accepted and a
follow-up implementation taskset is registered and claimed.

Acceptance criteria:
- Defines the attention-lane workspace, switcher, relation detail, schema
  inputs, and beta/UX evidence paths.
- Classifies candidate deltas as design_token, ui_component,
  pattern_component, or one_off_for_now before implementation.
- Rejects pure visual refresh, pure drill-down, and pure command-palette
  alternatives as insufficient for board-scale scanning.
