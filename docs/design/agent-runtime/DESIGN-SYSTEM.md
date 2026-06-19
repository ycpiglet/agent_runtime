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
| `design_token` | `src/agent_runtime/ui_design_assets.py` | `UI_TOKEN_SCALE_CSS` for shared type, semantic spacing, radius, and specialized layout offsets used by the legacy console CSS. |
| `ui_component` | `src/agent_runtime/ui_design_assets.py` | JS helpers such as `componentButton`, `componentCard`, `componentTable`, `componentModalShell`, `componentProgressBar`, `componentEmptyState`, `componentMetaGrid`, and `componentStateChip`. |
| `pattern_component` | `src/agent_runtime/ui_design_assets.py` | Domain helpers such as `patternTaskLane`, `patternClaimCard`, `patternEvidencePanel`, `patternCommandBar`, `patternStateMachinePanelLegend`, `patternSvgLayeredRadialLayout`, `patternSvgGraph`, `patternCalendarGrid`, `patternAuditMeta`, and `patternSurfaceMeta`, served into `/app.js` and reused by console renderers. |
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
| `patternSvgLayeredRadialLayout` / `patternSvgGraph` | Live-map and dependency-graph SVG node/edge layout and paint path. |
| `patternCalendarGrid` | Calendar month/week grid cell renderer in `renderCalendar`. |

Token-literal status as of `TASK-AR-581`: the full `--all-ui` raw-literal audit
passes for the current console baseline. Typography, spacing, radius, and the
remaining raw stroke color are now represented through tokens rather than
page-level CSS literals.

Semantic scale status as of `TASK-AR-583`: transitional `--space-px-*` and
`--radius-px-*` aliases have been removed from the token layer and console CSS
consumers. Shared spacing now uses named scale tokens such as `--space-sm`,
`--space-6xl`, `--space-viewport-gap`, and `--space-floating-offset`; radius
uses `--radius-hairline`, `--radius-xs`, `--radius-md`, `--radius-lg`, and
related scale names.

Residual one-off boundary: office map placement, import/export previews,
specialized ops dashboard charts, and remaining JavaScript geometry constants
may remain in `ui_console.py` until a later unit extracts them behind stable
pattern APIs. These are physical decomposition and layout-geometry debts, not
typography/spacing/radius token debts. As of `TASK-AR-584`, the live/dependency
SVG node/edge layout path and calendar grid cell renderer are promoted into
experimental pattern APIs.

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

Tokens follow the same model. The current spacing and radius scale is `stable`
for new console work: workers must use semantic scale tokens rather than
pixel-named aliases or raw literals. New spacing/radius values start as
`experimental` only when a design exploration proves the existing scale cannot
serve the workflow, and they must not silently re-introduce raw literals.

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

### Accepted RFC: operator attention graph

`reviews/RFC-2026-06-19-ui-ux-design-direction.md` accepts
`operator_attention_graph` as the next design direction. It authorizes a later
implementation task to propose relation-aware assets, but only within these
boundaries:

| Candidate asset | Class | Initial tier | Contract |
| --- | --- | --- | --- |
| Relation trace tokens | `design_token` | `experimental` | Use existing status and line tokens first; add new semantic relation tokens only inside the token definition layer. |
| Relation spacing, motion, and effect tokens | `design_token` | `experimental` | Preserve semantic spacing names, reduced-motion behavior, and shallow evidence-first emphasis. |
| `componentRelationChip` | `ui_component` | `experimental` | Label taskset, claim, evidence, wiki, graph, and command relationships with visible state text and keyboard focus. |
| `componentEvidencePreviewRow` | `ui_component` | `experimental` | Show evidence kind, freshness, status label, and target link for pass, watch, block, missing, and stale states. |
| `patternAttentionRelationPanel` | `pattern_component` | `experimental` | Combine current item, related artifacts, evidence preview, and command readiness without hiding the active taskset. |
| `patternGraphContextStack` | `pattern_component` | `experimental` | Provide the narrow-viewport list equivalent for graph context, including empty, interrupted, stale, and blocked states. |

The implementation may choose names that better fit `ui_design_assets.py`, but
the responsibilities and states above must remain testable. Any one-off
relationship copy or layout used only by the first implementation must be
labelled `one_off_for_now` in closeout evidence and promoted before a third
copy appears.

The next source-mutating UI task must include beta-tester and UX-evaluator
evidence for:

- a user-like path from taskset attention to claim evidence, graph/wiki context,
  and command readiness;
- desktop and mobile viewport behavior;
- keyboard traversal, visible focus, reduced motion, and non-color-only state;
- recovery paths for empty graph, stale evidence, blocked command, and
  interrupted claim.

### Accepted RFC: taskset attention workspace

`reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md` accepts
`taskset_attention_workspace` as the Taskset Board IA direction. It extends the
accepted `operator_attention_graph` direction by changing the board entry point
from a long generated list into attention lanes with a supporting taskset
switcher and relation detail panel.

The first implementation must start every candidate as `experimental` unless it
reuses an existing stable token or helper unchanged:

| Candidate asset | Class | Initial tier | Contract |
| --- | --- | --- | --- |
| Attention state labels | `design_token` | `experimental` | Reuse pass/warn/block/info/active tokens first; add only named attention aliases inside the token layer when current semantics cannot distinguish active, stale, blocked, recently changed, and ready states. |
| Lane density roles | `design_token` | `experimental` | Use the current type, spacing, and radius scale first; add compact lane roles only when beta evidence proves readability, truncation, or target-size gaps. |
| Taskset quick switcher | `ui_component` | `experimental` | Keyboard-first typeahead with selected state, empty state, result count, and jump target. |
| Attention lane filter | `ui_component` | `experimental` | Compact segmented or tab-like control with count, label, focus state, and non-color cue. |
| Taskset attention lane | `pattern_component` | `experimental` | Domain lane combining taskset identity, claim state, evidence freshness, command readiness, and membership reason. |
| Taskset relation detail panel | `pattern_component` | `experimental` | Reuse OAG relation summary and evidence preview responsibilities without duplicating relation chip/card markup. |
| First migration helper copy | `one_off_for_now` | temporary | Allowed only for the first beta cycle; remove or promote before a third use. |

The implementation registration must name its schema or adapter inputs before
editing UI assets: taskset identity/status, active claim, claim phase, progress,
evidence freshness, recent change timestamp, command readiness, and child task
counts. If the current Taskset Board API cannot supply those values, a
read-only adapter must be introduced before lane membership is rendered.

Beta-tester and UX-evaluator evidence must cover unknown-target discovery,
known-target switcher search, keyboard traversal, desktop and `390x844` mobile
fit, reduced motion, empty lane, stale evidence, blocked command, interrupted
claim, expired claim, and no active claim states. User-visible failures use
BTC-style IDs with reproduction paths.

### Accepted RFC: taskset evidence review queue and split loading

`reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md` accepts
`evidence_review_queue_with_progressive_disclosure_and_split_loading` as the
Taskset Board evidence/performance IA direction. It extends
`taskset_attention_workspace` by changing the stale-evidence lane from a flat
list into grouped review queues with visible lane caps, hidden counts,
summary-first loading, and retryable detail states.

The first implementation must start every candidate as `experimental` unless it
reuses an existing stable token or helper unchanged:

| Candidate asset | Class | Initial tier | Contract |
| --- | --- | --- | --- |
| Evidence freshness aliases | `design_token` | `experimental` | Named aliases for fresh, aging, stale, missing, unknown, unverified, and retryable evidence; visible labels are required. |
| Evidence severity/order aliases | `design_token` | `experimental` | Semantic ordering roles such as urgent, blocked, stale, deferrable, and recently changed, mapped to existing status tokens first. |
| Lane cap and queue density roles | `design_token` | `experimental` | Compact spacing/type roles for group headers, queue rows, hidden-count disclosure, and detail-loading states. |
| Loading and latency state tokens | `design_token` | `experimental` | Summary-ready, detail-loading, timeout-watch, retryable, and stale-summary states. |
| Evidence group filter | `ui_component` | `experimental` | Filter control for freshness, severity, owner/team, and command readiness with visible count and focus state. |
| Lane cap disclosure control | `ui_component` | `experimental` | Shows visible count, hidden count, ordering reason, and drill-in affordance. |
| Latency budget badge | `ui_component` | `experimental` | Displays summary age, detail-loading, timeout-watch, and retryable states in text. |
| Evidence queue row | `ui_component` | `experimental` | Compact row with taskset id, evidence freshness, owner/team, command readiness, and selected/focus states. |
| Evidence review queue | `pattern_component` | `experimental` | Domain pattern combining grouped evidence gaps, capped rows, selected detail, defer/action/retry states, and keyboard traversal. |
| Split board loading skeleton | `pattern_component` | `experimental` | Summary-first loading pattern that keeps lanes usable while detail loads or fails recoverably. |
| Inactive view containment shell | `pattern_component` | `experimental` | Ensures inactive views cannot create user-visible horizontal overflow or ambiguous beta evidence. |
| First-run migration copy | `one_off_for_now` | temporary | Allowed only to orient users during the first beta cycle; remove or promote before a third use. |

The implementation registration must name its schema or adapter inputs before
editing UI assets: taskset id/title/status, evidence freshness, evidence age,
evidence severity, owner/team/role, active claim, claim phase, command
readiness, visible count, hidden count, summary age, and detail loading state.
If the current Taskset Board API cannot supply those values cheaply, a
summary-first read-only adapter must be introduced before UI rendering changes.

Beta-tester and UX-evaluator evidence must cover unknown evidence triage,
known-target search, capped group drill-in, slow detail loading, timeout/retry,
keyboard traversal, desktop and `390x844` mobile fit, reduced motion, inactive
view containment, stale evidence, blocked command, interrupted claim, expired
claim, and no active claim states. User-visible failures use BTC-style IDs with
reproduction paths.

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
3. Run `python scripts/ui_ux_cycle.py --root . propose --dry-run --json`
   to generate proposal-only next-work intake. The proposals must distinguish
   Design Exploration RFCs, implementation refactors, and UX evaluation passes,
   and each proposal must carry role routing plus target file boundaries.
4. Route the selected recommendation through W0-W6 registration and claim.
5. Run `python scripts/ui_ux_cycle.py --root . plan-review --task-id <TASK> --dry-run --json`
   to plan the seminar, implementation meeting, and beta-tester evidence
   skeletons for the selected UI task.
6. Implement only the claimed unit.
7. Verify with the design-system gate, focused tests, and beta-tester evidence.
8. Feed the result back into the next `ui_ux_cycle` report.

The cycle checklist must always cover typography, size/spacing, color, motion,
effects, schema/API boundaries, assets, accessibility, responsiveness, and
interaction recovery paths.

`plan-review` is proposal/evidence plumbing. Dry-run mode must not write files.
Write mode may create only review skeletons and refresh `reviews/INDEX.md`; it
must not fabricate live seminar dialogue, beta-tester results, UI source edits,
claims, or registered follow-up tasks. Beta-tester skeletons must require
user-like actions, recovery attempts, environment notes, and BTC-style failure
IDs before an evaluator can claim the evidence is complete.

`propose` is next-work intake plumbing. Dry-run mode must not write files. Write
mode may create only `reviews/PROPOSALS-<date>-ui-ux-next-work.md` and refresh
`reviews/INDEX.md`; it must not edit UI source files, runtime claims, or work
item records. Proposal records are not approval to implement. A planner or owner
must register/claim the selected follow-up through W0-W6 before any UI file
mutation.

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
