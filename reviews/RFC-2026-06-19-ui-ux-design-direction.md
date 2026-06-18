---
type: ui-ux-design-direction-rfc
id: RFC-2026-06-19-ui-ux-design-direction
status: accepted
signal: pass
score: 88
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-UI-UX-DESIGN-DIRECTION-RFC
task_id: TASK-AR-601
decision: operator_attention_graph
tags: [ui, ux, design-system, rfc, design-direction]
---

# UI/UX Design Direction RFC 2026-06-19

## Bottom Line

- Summary: accept `operator_attention_graph` as the next UI design direction
  for Agent Runtime.
- Result: future UI implementation may introduce relationship-aware attention
  patterns, but only through labelled experimental tokens and pattern assets.
- Boundary: this RFC does not authorize UI source mutation by itself. Source
  changes require a later claimed implementation unit.

## Signal

| Dimension | Verdict | Evidence |
| --- | --- | --- |
| User problem | pass | operators need to see what needs attention, why it matters, and what evidence supports the next safe action |
| Target workflow | pass | backlog or taskset status -> claim and evidence -> wiki or graph context -> command readiness |
| Existing direction gap | pass | the current operator-console direction is consistent, but repeated cards and lists do not expose cross-artifact relationships quickly enough |
| System fit | pass | the direction extends the accepted evidence-first console model instead of replacing it with a generic dashboard |
| Implementation readiness | watch | source mutation must wait for a focused implementation claim and beta-tester evidence |

## Action

| Role | Required action | Boundary |
| --- | --- | --- |
| lead-designer | promote `operator_attention_graph` into the accepted design direction | complete in this RFC and `DESIGN.md` amendment |
| design-system-steward | treat relation tokens, chips, evidence previews, and relation panels as experimental assets until promoted | enforce through `DESIGN-SYSTEM.md` and the design-system gate |
| interface-designer | implement only after a fresh source-mutating claim exists | no UI source mutation in `TASK-AR-601` |
| ux-evaluator | require beta-tester evidence for desktop, mobile, recovery, empty, stale, blocked, and interrupted states | no screenshot-only acceptance |

## Decision

Accepted visual direction: `operator_attention_graph`.

The console should keep the accepted light-first, dense, evidence-first
operator model, while adding a relationship layer that makes tasksets, claims,
evidence records, wiki pages, graph nodes, and safe commands feel connected.
The product should read as an operating surface for decisions, not as a set of
independent data panes.

The first implementation round should target one end-to-end workflow:

1. An operator starts from a taskset or attention item.
2. The UI shows the owning claim, status, and freshest evidence.
3. The UI previews related wiki or graph context without hiding the current
   task.
4. The UI makes the safe command state explicit, including blocked and
   interrupted states.

## References

| Reference | What to borrow | What not to borrow |
| --- | --- | --- |
| Linear-style operator density | compact hierarchy, predictable keyboard-friendly surfaces, restrained visual weight | decorative gradients or marketing composition |
| Sentry-style evidence drilldown | issue-to-event-to-trace clarity, obvious severity and ownership cues | burying evidence behind too many nested detail pages |
| Miro/FigJam-style relationship canvases | visible relationships and spatial grouping when graph context matters | freeform canvas sprawl that weakens command readiness |

These are reference systems, not copy targets. The Agent Runtime result must
remain taskset-first, evidence-first, and governed by the existing design
system contract.

## Assetization Classification

| Surface or behavior | Class | Maturity | Allowed delta |
| --- | --- | --- | --- |
| Relationship trace color, active trace emphasis, and stale trace treatment | `design_token` | experimental | add semantic relation tokens only if existing status/line tokens cannot distinguish current, related, stale, and blocked links |
| Compact graph-adjacent type roles for node labels, evidence previews, and command readiness text | `design_token` | experimental | add named type tokens only after proving existing type scale cannot preserve scan density |
| Relationship chip | `ui_component` | experimental | a compact labelled control for taskset, claim, evidence, wiki, graph, and command relations |
| Evidence preview row | `ui_component` | experimental | a small row that shows evidence kind, freshness, status label, and target link |
| Attention relation panel | `pattern_component` | experimental | a domain panel that combines current item, related artifacts, evidence preview rows, and command state |
| Graph context stack for narrow viewports | `pattern_component` | experimental | a stacked list representation of the same relation graph, not a separate mobile-only concept |
| Task-specific explanatory copy inside the first RFC implementation | `one_off_for_now` | temporary | allowed only inside the originating implementation record and must be removed or promoted if reused |

## Token Boundaries

Implementation may propose the following token families, but must use existing
tokens first:

| Token family | Purpose | Guardrail |
| --- | --- | --- |
| Relation trace tokens | distinguish selected, related, stale, and blocked relationships | no raw color values outside token definitions; state labels remain visible |
| Relation spacing tokens | keep graph-adjacent panels compact on desktop and stacked on mobile | do not reintroduce pixel-named spacing aliases |
| Relation motion tokens | clarify focus movement and selection traversal | no decorative motion; respect reduced-motion preferences |
| Relation effect tokens | shallow emphasis for active context and evidence freshness | no heavy depth, glow, or blur as primary information |

If existing semantic tokens cover the need, the implementation must reuse them
instead of adding new tokens.

## Component And Pattern Boundaries

Minimum reusable assets expected from the implementation round:

| Asset | Type | Required states |
| --- | --- | --- |
| `componentRelationChip` | `ui_component` | default, active, stale, blocked, keyboard focus |
| `componentEvidencePreviewRow` | `ui_component` | pass, watch, block, missing, stale |
| `patternAttentionRelationPanel` | `pattern_component` | current item, related artifact list, evidence preview, command readiness |
| `patternGraphContextStack` | `pattern_component` | empty graph, narrow viewport stack, interrupted claim, blocked command |

The implementation may choose different final API names if the local asset
module naming pattern makes a better fit, but it must preserve the same
responsibilities and states.

## Page Assembly Boundary

Page or view files must remain composition and data wiring layers:

- Select the current taskset, claim, evidence, wiki, graph, and command data.
- Pass normalized data into reusable components or pattern helpers.
- Avoid view-local duplicate card, chip, evidence row, or relation list markup
  when a promoted helper exists.
- Keep one-off markup labelled in closeout evidence if it is not promoted.

## Accessibility And Responsive Criteria

The implementation round must prove:

- relation state is visible through text labels, not color alone;
- keyboard traversal can move from current item to related evidence and back;
- focus rings remain visible in light and dark themes;
- reduced-motion users do not receive relationship traversal animation;
- narrow viewports convert graph context into stacked relationship lists
  without losing evidence or command state;
- empty, stale, blocked, and interrupted states have explicit labels and
  recovery paths.

## Beta-Tester And UX-Evaluator Evidence

The next implementation round must create user-like evidence, not screenshot-only
evidence.

| Role | Required evidence |
| --- | --- |
| beta-tester | click or keyboard path from taskset attention item to claim evidence, graph/wiki context, and command readiness |
| beta-tester | recovery path for empty graph, stale evidence, blocked command, and interrupted claim |
| beta-tester | desktop and mobile viewport notes with environment and exact actions |
| ux-evaluator | accessibility review for labels, focus order, reduced motion, and non-color-only state |
| ux-evaluator | BTC-style defect IDs for every visible defect with reproduction path |

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| `visual_refresh_only` | rejected | would polish the same repeated card language without improving decision flow |
| `dashboard_kpi_layer` | rejected | risks generic SaaS summary metrics and pushes evidence/context behind secondary views |

## Risks

- Risk: relation visuals could become decorative lines. Guardrail: every
  relation must explain decision context or command readiness.
- Risk: new tokens could bypass the stable semantic scale. Guardrail: new
  tokens start experimental, use existing tokens first, and must pass the
  design-system gate.
- Risk: graph context could dominate the UI. Guardrail: the taskset and active
  claim remain the primary operator anchor.

## Decision Record

- Promote `operator_attention_graph` into `DESIGN.md` as the accepted next
  direction.
- Add experimental relation token/component/pattern boundaries to
  `DESIGN-SYSTEM.md`.
- Keep implementation blocked until a future claimed task mutates UI source
  files.

## Next

- Use this RFC as input for `TASK-AR-602`.
- Register or derive a focused implementation unit for the first relation-aware
  UI source change.
- Require beta-tester and UX-evaluator evidence after implementation before
  the next UI/UX cycle proposes another change.
