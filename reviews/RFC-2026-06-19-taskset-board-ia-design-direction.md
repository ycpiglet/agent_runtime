---
type: ui-ux-design-rfc
id: RFC-2026-06-19-taskset-board-ia-design-direction
status: accepted
signal: pass
score: 90
priority: High
date: 2026-06-19
task_set_id: TASKSET-AR-TASKSET-BOARD-IA-DESIGN-DIRECTION
task_id: TASK-AR-610
claim_id: CLAIM-20260619-175000-task-ar-610-task-ar-610-rfc-resume
participants:
  - lead-designer
  - design-system-steward
  - interface-designer
  - ux-evaluator
tags: [ui, ux, rfc, taskset-board, attention-workspace, design-system]
---

# Taskset Board IA Design Direction RFC

## Summary

- Decision: accept `taskset_attention_workspace` as the next Taskset Board IA
  and visual direction.
- User problem: the Operator Attention Graph cycle closed relation semantics and
  mobile overflow, but the Taskset Board still contains `49` tasksets. Unknown
  target discovery and keyboard traversal across the whole board remain too
  long.
- Direction: make the first Taskset Board viewport an attention workspace with
  explainable lanes, a supporting taskset switcher, and a relation detail panel.
- Boundary: this RFC authorizes design-system documentation and a follow-up
  implementation registration only. It does not authorize UI source mutation.

## Signal

| Signal | Status | Evidence |
| --- | --- | --- |
| Seminar decision | pass | `reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md` selected `taskset_attention_workspace`. |
| Board scale | watch | The current board state includes `49` tasksets; whole-board scanning is too long. |
| OAG dependency | pass | Existing `operator_attention_graph` relation semantics remain the context layer for the new workspace. |
| Source mutation | blocked | No UI source file may change until `TASK-AR-611` derives and registers the implementation/beta units. |

## Source Evidence

| Evidence | Use in this RFC |
| --- | --- |
| `reviews/SEMINAR-2026-06-19-taskset-board-ia-design-direction.md` | Primary design seminar and accepted direction. |
| `reviews/W4B-2026-06-19-TASK-AR-608.md` | Confirms mobile overflow is closed and routes the new board-scale IA problem. |
| `reviews/BETA-TEST-2026-06-19-oag-mobile-responsive-refinement.md` | Provides desktop/mobile Taskset Board behavior and board data size. |
| `reviews/UX-EVAL-2026-06-19-oag-mobile-responsive-refinement.md` | Recommends board navigation/design-direction work rather than another width fix. |
| `reviews/RFC-2026-06-19-ui-ux-design-direction.md` | Accepted `operator_attention_graph` relationship layer that this RFC preserves. |
| `docs/design/agent-runtime/DESIGN-SYSTEM.md` | Governs assetization classes, maturity tiers, and UI/UX cycle evidence. |

## Decision

Accept `taskset_attention_workspace`.

The Taskset Board should stop opening as one long board-first list. The default
operator path becomes:

```text
Taskset Board -> attention lane -> taskset summary -> relation detail -> evidence and command readiness
```

The full taskset list remains available, but the first viewport prioritizes:

1. active claimed work;
2. blocked, interrupted, stale, or decision-needed work;
3. recently changed work;
4. ready next-action candidates;
5. all tasksets as a searchable fallback.

The workspace must explain why each taskset appears in a lane. Lane membership
cannot be decorative or color-only. Each card needs a visible reason such as
`active claim`, `stale evidence`, `blocked command`, `recently changed`, or
`ready next action`.

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| `visual_refresh_only` | rejected | It would change appearance without reducing board-scale discovery or focus traversal. |
| `progressive_drilldown_primary` | rejected as primary | Drill-down reduces first-screen volume, but hides relation/evidence context and slows cross-taskset comparison. |
| `command_palette_primary` | rejected as primary | Typeahead is excellent for known-target retrieval but does not help users discover what matters when they do not know the target id. |
| `dashboard_kpi_layer` | rejected | Aggregate cards risk generic KPI decoration and hide the evidence-first workflow behind summary numbers. |

## Target Workflow

| Flow | Required behavior |
| --- | --- |
| Unknown target discovery | User opens Taskset Board and can identify an active, risky, or ready taskset from the first viewport without scanning all tasksets. |
| Known target retrieval | User types a taskset id or title fragment into the switcher and jumps to the target. |
| Relation inspection | User opens relation detail and sees taskset state, claim path, evidence freshness, graph/wiki context, and command readiness. |
| Keyboard traversal | User reaches lane controls, switcher, target card, relation detail, and next action without tabbing through every card. |
| Mobile operation | At `390x844`, the same workflow stacks lanes and detail without document-level horizontal overflow. |
| Recovery | Empty lane, stale evidence, blocked command, interrupted claim, expired claim, and no active claim states are visibly labelled. |

## Assetization Plan

| Surface | Class | Initial tier | Contract |
| --- | --- | --- | --- |
| Attention state labels | `design_token` | `experimental` | Reuse existing semantic status tokens first; add only named attention aliases if current tokens cannot distinguish active, stale, blocked, recently changed, and ready states. |
| Lane density roles | `design_token` | `experimental` | Use current type and spacing scale first; add compact lane roles only if beta evidence proves truncation or target-size gaps. |
| Taskset quick switcher | `ui_component` | `experimental` | Keyboard-first typeahead with selected state, empty state, result count, and jump target. |
| Attention lane filter | `ui_component` | `experimental` | Segmented or tab-like control with count, focus state, label, and non-color cue. |
| Taskset attention lane | `pattern_component` | `experimental` | Domain lane combining taskset identity, claim state, evidence freshness, command readiness, and membership reason. |
| Taskset relation detail panel | `pattern_component` | `experimental` | Reuses OAG relation summary and evidence preview responsibilities without duplicating relation chip/card markup. |
| First migration helper copy | `one_off_for_now` | temporary | Allowed only for the first beta cycle to orient users; remove or promote before a third use. |

## Quality Requirements

| Dimension | Requirement | Evidence |
| --- | --- | --- |
| Typography | Lane headings, taskset ids, reason labels, and evidence freshness text must remain readable in dense desktop and `390x844` mobile layouts. | Desktop/mobile beta notes with truncation and wrap observations. |
| Size and spacing | Lane controls, cards, switcher rows, and detail panel must use stable dimensions and semantic spacing tokens. | Design-system gate plus screenshot or DOM measurement for overflow and layout shift. |
| Color | State meaning must use existing semantic pass/warn/block/info/active tokens first and visible text labels always. | Contrast and non-color cue notes in UX evaluation. |
| Motion | Lane changes and switcher jumps may use only short focus/selection transitions; reduced motion must remove movement-dependent meaning. | Reduced-motion beta path. |
| Effects | Focus rings, hover, active lane, and detail emphasis must clarify interaction state; shadows/glow cannot carry workflow meaning. | Keyboard/focus evidence. |
| Schema | Lane derivation must name its inputs: taskset status, active claim, claim phase, evidence freshness, recently changed time, command readiness, and child task state. | Implementation registration names API or adapter fields before source edits. |
| Assets | Every new helper is classified as token, UI component, pattern component, or one-off before implementation. | Closeout assetization table. |
| Accessibility | Landmarks, labels, count announcements, empty states, and screen-reader-visible state must be present. | UX evaluation and focused UI tests. |
| Responsiveness | Desktop may use lanes plus detail panel; mobile stacks lanes, switcher, and detail without horizontal overflow. | `390x844` measurement and desktop regression path. |
| Interaction | Unknown-target, known-target, keyboard, mobile, reduced-motion, stale, blocked, interrupted, empty, and no-claim paths are tested. | Beta-tester artifact with clicked/typed steps and BTC IDs for failures. |

## Schema Contract

The implementation may derive the workspace from the existing Taskset Board API
only if these fields are available or can be produced by a named adapter:

| Field | Purpose | Required state examples |
| --- | --- | --- |
| `taskset_id`, `title`, `status` | Lane card identity and full-list fallback. | active, planned, completed, archived |
| `active_claim` | Active lane and relation detail entry. | claimed, released, expired, missing |
| `claim_phase`, `progress_pct`, `status_text` | Operational state and lane reason. | implementing, verified, interrupted, blocked |
| `evidence_freshness` | Stale or risky evidence lane. | fresh, stale, unknown, missing |
| `updated_at` or `recent_change` | Recently changed lane. | today, this session, older |
| `command_readiness` | Safe next action and blocked command cue. | ready, guarded, blocked, unavailable |
| `child_task_counts` | Summary density and all-tasksets comparison. | open, active, completed, blocked |

If the current API cannot provide these values, the implementation task must
introduce a small read-only adapter before rendering lane membership in UI code.

## Implementation Boundary

- Do not mutate `src/agent_runtime/ui_console_assets.py`,
  `src/agent_runtime/ui_design_assets.py`, tests, or API code in this RFC task.
- `TASK-AR-611` must derive the implementation and beta units from this RFC.
- The first source-mutating task must keep page assembly focused on data wiring
  and layout orchestration.
- Repeated lane, switcher, relation detail, state chip, and evidence preview
  surfaces must move into `ui_design_assets.py` helpers or be explicitly marked
  `one_off_for_now`.

## Action

| Action | Owner | State |
| --- | --- | --- |
| Record this RFC in `DESIGN.md` and `DESIGN-SYSTEM.md` | lead-designer | done in TASK-AR-610 |
| Derive implementation and beta registration input | interface-designer | next in TASK-AR-611 |
| Decide exact helper names and API adapter boundary | design-system-steward | next |
| Run beta-tester and UX-evaluator paths after implementation | ux-evaluator | next |

## Risk

| Risk | Impact | Guardrail |
| --- | --- | --- |
| Attention lanes hide quiet work. | Operators may miss work outside the first viewport. | Keep All Tasksets available, searchable, and keyboard reachable. |
| Lane rules become hardcoded UI guesses. | Data semantics drift from task/claim truth. | Implementation must name schema/adapter inputs before rendering. |
| Switcher becomes the whole solution. | Unknown-target discovery remains weak. | Treat switcher as a supporting component only. |
| New tokens become palette drift. | Design-system maturity regresses. | Reuse semantic tokens first; new tokens start experimental and only in token layer. |
| Detail panel duplicates OAG assets. | Component debt returns. | Reuse relation chip/evidence preview responsibilities or promote shared helpers. |

## Decision Outcome

`taskset_attention_workspace` is accepted and promoted to the design-system
contract as an experimental direction. It extends `operator_attention_graph`
instead of replacing it. Source mutation remains blocked until `TASK-AR-611`
creates the implementation and beta-evaluation registration input.

## Next

- `TASK-AR-611`: derive a source-mutating implementation task and paired
  beta/UX evaluation plan.
- The implementation registration must name target files, schema/adapter
  fields, assetization classes, focused tests, design-system gate, evidence
  index check, and independent W4b verification.
- The beta plan must include clicked/typed actions, keyboard traversal,
  reduced-motion behavior, desktop/mobile viewport evidence, recovery paths,
  and BTC-style failure routing.
