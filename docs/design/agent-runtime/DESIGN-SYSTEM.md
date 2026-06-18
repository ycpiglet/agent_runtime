---
title: Agent Runtime Design System Operating Contract
status: accepted
date: 2026-06-18
task_set_id: TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE
---

# Agent Runtime Design System Operating Contract

`DESIGN.md` is the accepted visual direction. This file is the operating
contract that tells agents when to reuse, extract, propose, and verify UI
assets.

## Assetization classes

Every non-trivial UI change must classify new or touched UI surface area before
implementation:

| Class | Use when | Examples |
| --- | --- | --- |
| `design_token` | A value should be shared across components or themes. | color, status color, type scale, spacing, radius, shadow, z-index, motion duration |
| `ui_component` | A generic reusable control has stable behavior and state. | Button, IconButton, Input, Select, Tabs, Modal, Card, Table, Badge, EmptyState |
| `pattern_component` | A reusable domain layout combines UI components with Agent Runtime semantics. | TaskLane, ClaimCard, EvidencePanel, CommandBar, StateMachinePanel, WorkItemRow |
| `one_off_for_now` | A surface appears once and has no proven reuse yet. | temporary migration notice, task-specific review widget |

If the same one-off appears a second time, the worker must propose promotion to
`ui_component` or `pattern_component` before adding a third copy.

## Implementation rules

- Use existing design tokens and reusable components first.
- Add raw color, spacing, radius, shadow, or type values only in the token
  definition layer.
- Keep page files focused on layout composition, data wiring, and route/view
  orchestration.
- Move repeated domain structures into pattern components.
- Keep status meaning stable: green pass, amber pending/warning, red
  blocked/failed, blue info, purple primary or active context.
- Status color must never be the only signal; visible text labels are required.
- Do not create live `agents/<role>` directories in this checkout for design
  roles. Use `ORG-MODEL.yml` metadata and generated-host templates.

## Executable asset layer

The current console is a Python stdlib server that emits static HTML, CSS, and
vanilla JavaScript. Until the frontend architecture changes, executable design
assets live in:

| Layer | Module | Contents |
| --- | --- | --- |
| `design_token` | `src/agent_runtime/ui_design_assets.py` | `UI_TOKEN_SCALE_CSS` for shared type, spacing, radius, and tokenized px aliases used by the legacy console CSS. |
| `ui_component` | `src/agent_runtime/ui_design_assets.py` | JS helpers such as `componentButton`, `componentCard`, `componentTable`, `componentModalShell`, `componentProgressBar`, `componentEmptyState`, `componentMetaGrid`, and `componentStateChip`. |
| `pattern_component` | `src/agent_runtime/ui_design_assets.py` | Domain helpers such as `patternTaskLane`, `patternClaimCard`, `patternEvidencePanel`, `patternCommandBar`, `patternStateMachinePanelLegend`, `patternAuditMeta`, and `patternSurfaceMeta`, served into `/app.js` and reused by console renderers. |
| `served_asset` | `src/agent_runtime/ui_console_assets.py` | The served HTML, CSS, and JavaScript asset strings, including composition with `ui_design_assets`. |
| `page assembly` | `src/agent_runtime/ui_console.py` | HTTP routing, API responses, data wiring, and serving the asset module constants. |

New reusable helpers should start in `ui_design_assets.py` unless they are
specific to one view. If a helper starts as a one-off in `ui_console.py` and is
used by a second view, promote it into the asset module before adding a third
copy.

Promoted pattern usage as of `TASK-AR-580`:

| Pattern API | Current console usage |
| --- | --- |
| `patternTaskLane` | Board lane shell in `renderKanban`. |
| `patternClaimCard` | Board task card renderer. |
| `patternEvidencePanel` / `patternAuditCard` | Events, errors, evidence links, and replay panels. |
| `patternCommandBar` | Write command log cards. |
| `patternStateMachinePanelLegend` | State-machine viewer legend shell. |

Token-literal status as of `TASK-AR-581`: the full `--all-ui` raw-literal audit
passes for the current console baseline. Typography, spacing, radius, and the
remaining raw stroke color are now represented through tokens rather than
page-level CSS literals.

Residual one-off boundary: data-heavy SVG layout functions, calendar grids,
office map placement, import/export previews, specialized ops dashboard charts,
and JavaScript geometry constants may remain in `ui_console.py` until a later
unit extracts them behind stable pattern APIs. These are physical decomposition
and layout-geometry debts, not typography/spacing/radius token debts.

Served asset ownership as of `TASK-AR-582`: `ui_console.py` no longer owns the
large HTML/CSS/JS strings. `ui_console_assets.py` owns the static served assets,
while `ui_console.py` owns routing and API behavior. Remaining extraction work is
inside the JavaScript renderer asset itself, where view-specific renderers still
need promotion into pattern modules.

## Maturity tiers

Every token, UI component, and pattern component carries a maturity tier so new
design can enter the system without destabilizing it. This is the
consistency-vs-novelty mechanism: novelty is allowed but *labelled* and not
load-bearing until it earns promotion (model adapted from the USWDS, GitHub
Primer, and VA.gov component lifecycles — see
`reviews/RESEARCH-2026-06-18-design-system-governance-role-topology.md`).

| Tier | Meaning | Allowed use |
| --- | --- | --- |
| `experimental` | New or in-flight; API and visuals may still change. Enters via a Design Exploration RFC or a first extraction. | Behind the originating view only; never a load-bearing shared dependency. |
| `stable` | Proven, documented, reused; breaking changes require a migration note. | Default for new screens. Workers build from stable assets only. |
| `deprecated` | Superseded; kept only for migration. | Do not add new usages; replace on touch. |

Promotion `experimental -> stable` is decided by the `design-system-steward`
against objective, checkable criteria:

1. **Adoption** — used by at least two views (the rule-of-three trigger in *Assetization classes*).
2. **Stability** — the asset API did not change across its last use, and there is no open visual-regression issue.
3. **Evidence** — listed in the *Executable asset layer* table and backed by `visual_verification` for desktop and mobile.

Demotion or deprecation is allowed from any tier. Tier transitions are recorded
in the asset module docstring and in the touching task's closeout evidence.

Tokens follow the same model. The current `--space-px-*` and `--radius-px-*`
aliases are `stable` but transitional: they tokenize the legacy literal values
rather than a designed scale. Consolidating them into a semantic scale (for
example `--space-1..n`) is a future `experimental` token delta that promotes
only after the asset layer migrates to it, and it must not silently re-introduce
raw literals.

## New design proposal path

New visual direction is allowed, but it must enter through a Design Exploration
RFC before implementation:

1. State the user problem, target screen, and workflow.
2. Provide 2-3 reference systems or screenshots.
3. Explain why the existing visual direction is insufficient.
4. List the minimum token delta.
5. List new UI components or pattern components needed.
6. State accessibility, density, and responsive acceptance criteria.
7. Record whether the change is exploratory, accepted, rejected, or promoted.

Accepted RFCs update `DESIGN.md` for visual direction and this file for system
rules. Workers then implement from the updated contract.

## Role routing

| Role | Responsibility |
| --- | --- |
| `lead-designer` | Owns new design direction, references, product fit, and RFC decisions. |
| `design-system-steward` | Owns tokens, component/pattern promotion, and design-system gates. |
| `interface-designer` | Implements screens using accepted tokens, UI components, and pattern components. |
| `ux-evaluator` | Verifies usability, accessibility, responsive behavior, and visual regressions. |

Legacy `uiux` aliases resolve to `interface-designer` for backward
compatibility, but new planning records should choose the focused role.

## Required closeout evidence

UI tasks must include:

- `assetization_classification`: a short table of touched UI surfaces and their
  class.
- `design_system_gate`: command and result.
- `visual_verification`: desktop and mobile evidence when UI rendering changed.
- `role_route`: the focused UI/UX role responsible for design, implementation,
  or evaluation.

## UI/UX cycle conductor

Long-running UI improvement uses a repeatable cycle rather than a one-off
styling pass:

1. Run `python scripts/ui_ux_cycle.py --root . assess --json`.
2. Confirm the next refactor candidate and any active-claim footprint conflict.
3. Run or plan the relevant seminar/meeting/beta-tester review surfaces before
   the next implementation round.
4. Implement only the claimed unit.
5. Verify with the design-system gate, focused tests, and beta-tester evidence.
6. Feed the result back into the next `ui_ux_cycle` report.

The cycle checklist must always cover typography, size/spacing, color, motion,
effects, schema/API boundaries, assets, accessibility, responsiveness, and
interaction recovery paths.

## Gate

Run:

```bash
python scripts/design_system_gate.py --check
```

The default `--check` mode scans added UI diff lines plus untracked UI files and
blocks new raw style literals outside token definitions. `--path` and `--all-ui`
perform full-file audits. As of `TASK-AR-581`, `--all-ui` is expected to pass for
the current console baseline; failures represent new drift or newly registered
UI files that need tokenization or an explicit design-system promotion path.
