---
type: ui-ux-design-seminar
id: SEMINAR-2026-06-19-taskset-board-ia-design-direction
status: accepted
signal: pass
score: 88
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
task_id: TASK-AR-609
unit_id: UNIT-TASK-AR-609-001
claim_id: CLAIM-20260619-153911-task-ar-609-task-ar-609-taskset-board-ia-seminar
participants:
  - lead-designer
  - design-system-steward
  - interface-designer
  - ux-evaluator
tags: [ui, ux, seminar, lead-designer, taskset-board, ia, design-system]
---

# Taskset Board IA Design Seminar

## Bottom Line

- Decision: choose `taskset_attention_workspace` as the RFC candidate for the
  next Taskset Board design direction.
- User problem: `TASK-AR-608` closed mobile overflow, but W4B and beta/UX
  evidence show the board now contains `49` tasksets, so target discovery and
  whole-board focus traversal are too long.
- Boundary: this seminar authorizes an RFC only. It does not authorize UI
  source mutation.

## Signal

| Signal | Status | Evidence |
| --- | --- | --- |
| Mobile overflow closure | pass | `TASK-AR-608` W4B confirms `390px` document/body width at a `390px` viewport. |
| Board scale pressure | watch | The board data state is `49` tasksets, making target discovery and whole-board focus traversal long. |
| Current design fit | partial | `operator_attention_graph` exposes relation context, but the entry surface still behaves like one long generated board. |
| Next-cycle readiness | pass | `ui_ux_cycle assess` now finds `TASK-AR-610` as the next RFC candidate after this seminar. |

## Source Evidence

| Evidence | Signal |
| --- | --- |
| `reviews/W4B-2026-06-19-TASK-AR-608.md` | Passes mobile responsive W4B and routes the next problem: `49` tasksets make discovery and focus traversal long. |
| `reviews/BETA-TEST-2026-06-19-oag-mobile-responsive-refinement.md` | Desktop and `390x844` paths pass; target board data state is `49` tasksets, `267` tasks, `266` completed tasks. |
| `reviews/UX-EVAL-2026-06-19-oag-mobile-responsive-refinement.md` | Confirms overflow is closed and recommends board navigation/design-direction work instead of another width fix. |
| `reviews/RFC-2026-06-19-ui-ux-design-direction.md` | Existing accepted direction is `operator_attention_graph`: taskset -> claim/evidence -> graph/wiki context -> command readiness. |
| `docs/design/agent-runtime/DESIGN-SYSTEM.md` | New UI deltas must be classified as token, UI component, pattern component, or one-off before implementation. |

## Seminar Positions

| Role | Position | Constraint |
| --- | --- | --- |
| `lead-designer` | The board needs a stronger attention model, not a visual refresh. Users should see active, blocked, stale, recently changed, and next-action-ready tasksets before scanning the full archive-like list. | The first viewport must answer "what needs attention now" and "where can I safely act next". |
| `design-system-steward` | New design is allowed only through labelled assets. The direction may introduce attention-lane and taskset-switcher patterns, but tokens/components start experimental until reused and verified. | No new raw style literals; status meaning remains labelled and non-color-only. |
| `interface-designer` | Implementation should preserve current Taskset Board data contracts, relation labels, and OAG panel semantics while changing page assembly around them. | Page files should wire data and layout; repeated lane, switcher, and relation surfaces must move into assets. |
| `ux-evaluator` | The beta path must prove fewer steps to reach a known target and keyboard movement that does not require traversing every card. | Evidence must include clicked/typed paths, focus order, mobile fit, reduced motion, and recovery cases. |

## Direction Options

| Option | Description | Strength | Weakness | Decision |
| --- | --- | --- | --- | --- |
| `progressive_drilldown` | Group tasksets by initiative/status, then open nested taskset details. | Reduces first-screen volume and can fit mobile well. | Risks hiding claim/evidence context behind extra clicks and making cross-taskset comparison slower. | Rejected as the primary direction; useful as a responsive fallback. |
| `command_palette_taskset_switcher` | Add a keyboard-first typeahead switcher that jumps directly to a taskset or evidence target. | Best for known-target retrieval and power-user flow. | Does not teach users what matters when they do not already know the taskset id. | Rejected as the primary direction; include as a supporting UI component. |
| `attention_lane_workspace` | Reframe Taskset Board into prioritized lanes: Active Claims, Needs Decision, Stale Evidence, Recently Changed, and All Tasksets, with relation detail preserved. | Solves scanning, keeps evidence-first semantics visible, and gives mobile a stackable lane model. | Needs careful schema/lane derivation and beta proof that lanes do not hide work. | Selected RFC candidate. |

## Selected RFC Candidate

Candidate: `taskset_attention_workspace`.

The next RFC should define a Taskset Board workspace that defaults to attention
lanes rather than a single long board. The full list still exists, but the
first operator path becomes:

```text
Taskset Board -> attention lane -> taskset relation detail -> evidence/command readiness
```

The workspace should preserve the accepted `operator_attention_graph`
direction, but make the starting point more opinionated. The first viewport
should show current claims and risky work before lower-value completed or quiet
tasksets. The taskset switcher is a supporting control, not the whole design
direction.

## Assetization Classification

| Surface or behavior | Class | Initial tier | Expected contract |
| --- | --- | --- | --- |
| Attention lane state colors and non-color labels | `design_token` | experimental | Reuse existing status tokens first; add attention tokens only if active, stale, blocked, and recently-changed states cannot be distinguished through current semantic tokens. |
| Dense lane heading, taskset count, and evidence freshness type roles | `design_token` | experimental | Use existing type scale first; add compact label tokens only if readability or truncation evidence proves a gap. |
| Taskset quick switcher | `ui_component` | experimental | Keyboard-first typeahead with visible selected state, empty result state, and target jump. |
| Attention lane tab/filter control | `ui_component` | experimental | Compact filter with count, status label, focus state, and non-color cue. |
| Taskset attention lane | `pattern_component` | experimental | Domain lane combining taskset card summary, claim state, evidence freshness, command readiness, and keyboard target. |
| Taskset relation detail drawer or panel | `pattern_component` | experimental | Reuses OAG relation summary and evidence preview without duplicating chip/card markup. |
| First implementation migration copy | `one_off_for_now` | temporary | Allowed only to explain the new layout during the first beta cycle; must be removed or promoted if repeated. |

## Quality Requirements For RFC

| Dimension | Evidence requirement |
| --- | --- |
| Typography | Prove lane headings, taskset ids, claim labels, and evidence freshness remain readable at desktop and `390x844`; define truncation and line-wrap rules. |
| Size and spacing | Define density for lanes, cards, switcher rows, and relation detail; verify stable dimensions so counts, labels, and hover/focus states do not shift layout. |
| Color | Reuse semantic pass/warn/block/info/active tokens; require visible state labels so lane meaning is not color-only. |
| Motion | Allow only purposeful focus/selection transitions; define reduced-motion behavior where lane changes and switcher jumps happen without animation. |
| Effects | Define focus ring, hover, active lane, and shallow detail-panel emphasis; no decorative shadows or glow as information. |
| Schema | Specify derived lane inputs from existing taskset board API: taskset status, active claim, evidence freshness, recently changed timestamp, command state, and child task state. |
| Assets | Name token, UI component, pattern component, and one-off boundaries before source mutation. |
| Accessibility | Prove landmarks, keyboard flow, focus order, labels, count announcements, empty states, and screen-reader-visible state. |
| Responsiveness | Desktop may use lanes plus a detail panel; mobile should stack lanes and use the switcher without document-level horizontal overflow. |
| Interaction | Beta evidence must include unknown-target scanning, known-target search, keyboard navigation, empty lane recovery, stale evidence, blocked command, and interrupted claim paths. |

## Implementation Boundary

- Do not edit UI source from this seminar.
- The RFC may update `DESIGN.md` and `DESIGN-SYSTEM.md` only for accepted
  reusable direction and asset contracts.
- The eventual implementation should keep API and schema changes explicit. If
  the current `/api/tasksets_board` payload cannot derive an attention lane,
  the implementation task must name the required schema delta before editing
  UI assets.
- Existing OAG relation labels must remain visible: taskset state, claim path,
  evidence freshness, and command readiness.

## Beta And UX Evidence Path

| Flow | Required proof |
| --- | --- |
| Unknown target | User opens Taskset Board and identifies an active or risky taskset from the first viewport without scanning all `49` tasksets. |
| Known target | User types a taskset id or title fragment into the switcher and jumps to the target. |
| Keyboard path | User reaches lane filters, switcher, target card, relation detail, and next actionable control without traversing every board card. |
| Mobile path | User opens mobile sidebar -> Taskset Board -> attention lane -> target detail at `390x844` with no horizontal overflow. |
| Reduced motion | Lane changes and switcher jumps preserve labels and focus without motion-dependent meaning. |
| Recovery | Empty lane, stale evidence, blocked command, interrupted claim, and no active claim states are visible and routable to BTC-style defects if broken. |

## Decision

Accept `taskset_attention_workspace` for the next RFC. The RFC should promote
an attention-lane workspace with a supporting taskset switcher and relation
detail panel. It should reject a pure visual refresh, a pure drill-down tree,
and a pure command palette as insufficient for the current board-scale problem.

## Action

| Action | Owner | State |
| --- | --- | --- |
| Publish Taskset Board IA RFC from this seminar | lead-designer | next |
| Define token/component/pattern boundaries before source mutation | design-system-steward | next |
| Convert accepted RFC into implementation and beta-evaluation tasksets | interface-designer | pending |
| Require beta evidence for unknown-target scanning, known-target jump, keyboard path, mobile path, and recovery states | ux-evaluator | pending |

## Risk

| Risk | Impact | Guardrail |
| --- | --- | --- |
| Attention lanes could hide quiet but important tasksets. | Operators may miss work outside the first viewport. | Keep All Tasksets available and make lane membership explainable. |
| A switcher-only implementation could optimize known-target retrieval while leaving discovery weak. | New users still have to know the target id. | Treat switcher as supporting UI, not the primary design direction. |
| New lane tokens could become decorative drift. | Design-system maturity regresses. | Use existing status tokens first and start new tokens as experimental. |
| Schema derivation may be underspecified. | Implementation may hardcode lane membership in UI code. | RFC must name the API fields or adapter contract before implementation. |

## Next

- `TASK-AR-610`: publish
  `reviews/RFC-2026-06-19-taskset-board-ia-design-direction.md`.
- `TASK-AR-611`: derive the source-mutating implementation taskset and paired
  beta/UX evaluation plan after the RFC is accepted.
- Keep `reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md` proposal-only; no UI
  source mutation is authorized by this seminar.
