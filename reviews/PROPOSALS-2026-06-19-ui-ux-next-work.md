---
type: ui-ux-next-work-proposals
id: PROPOSALS-2026-06-19-ui-ux-next-work
status: planned
tags: [ui, ux, design-system, proposal]
---

# UI/UX Next Work Proposals 2026-06-19

## Boundary

- Mutation policy: `proposal-only`.
- Claim policy: must register and claim follow-up work through W0-W6 before any UI source mutation.
- This artifact proposes work only; it does not register tasks, create claims, or mutate UI source files.

## Proposals

### design_direction_rfc

- Status: `ready_to_register`
- Lead role: `lead-designer`
- Supporting roles: design-system-steward, ux-evaluator
- Review roles: interface-designer
- Future target files: DESIGN.md, docs/design/agent-runtime/DESIGN-SYSTEM.md
- Proposal artifacts: reviews/RFC-2026-06-19-ui-ux-design-direction.md, reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md

Create a Design Exploration RFC when the current visual direction is too repetitive, including references, token delta, component/pattern needs, and responsive/a11y acceptance criteria.

Acceptance criteria:
- States the user problem, target screen, workflow, and why the existing direction is insufficient.
- Provides 2-3 references or screenshots and records accepted/rejected/promoted outcome.
- Lists minimum token, UI component, and pattern component deltas before implementation.

### implementation_refactor

- Status: `needs_task_registration`
- Lead role: `interface-designer`
- Supporting roles: design-system-steward
- Review roles: ux-evaluator
- Future target files: src/agent_runtime/ui_console_assets.py, src/agent_runtime/ui_design_assets.py, tests/test_ui_console.py, tests/test_ui_design_assets.py
- Proposal artifacts: reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md

Register and claim the next implementation unit only after this proposal is reviewed; page files stay focused on layout/data wiring and repeated UI moves into pattern assets.

Acceptance criteria:
- Classifies touched UI as design_token, ui_component, pattern_component, or one_off_for_now.
- Uses existing tokens/components first and records any token/component promotion explicitly.
- Runs focused UI tests plus the design-system gate before W4a closeout.

### ux_evaluation_pass

- Status: `needs_implementation_target`
- Lead role: `ux-evaluator`
- Supporting roles: beta-tester, interface-designer
- Review roles: design-system-steward
- Future target files: reviews/SEMINAR-2026-06-19-next-ui-task-ui-ux.md, reviews/MEETING-2026-06-19-next-ui-task-ui-ux.md, reviews/BETA-TEST-2026-06-19-next-ui-task-ui-ux.md
- Proposal artifacts: reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md, reviews/SEMINAR-2026-06-19-next-ui-task-ui-ux.md, reviews/MEETING-2026-06-19-next-ui-task-ui-ux.md, reviews/BETA-TEST-2026-06-19-next-ui-task-ui-ux.md

Plan the post-implementation beta-tester/evaluator pass with clicked/typed actions, edge and recovery attempts, environment notes, and BTC-style visible-defect IDs.

Acceptance criteria:
- Records user-like actions instead of screenshot-only evidence.
- Covers recovery, empty, interrupted, and responsive states where relevant.
- Links every user-visible defect to a BTC-style failure ID and reproduction path.
