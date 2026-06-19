---
type: ui-ux-design-seminar
id: SEMINAR-2026-06-19-taskset-board-evidence-performance-ia
status: accepted
signal: pass
score: 89
priority: High
date: 2026-06-19
generated_at: 2026-06-20T00:10:00+09:00
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
task_id: TASK-AR-616
unit_id: UNIT-TASK-AR-616-001
claim_id: CLAIM-20260619-235857-task-ar-616-task-ar-616-evidence-perf-ia-seminar
participants:
  - lead-designer
  - design-system-steward
  - interface-designer
  - ux-evaluator
  - beta-tester
tags: [ui, ux, seminar, lead-designer, taskset-board, evidence, performance, ia]
---

# Taskset Board Evidence And Performance IA Seminar

## Bottom Line

- Decision: choose `evidence_review_queue_with_progressive_disclosure_and_split_loading` as the next RFC candidate.
- User problem: the Taskset Board attention workspace is functionally reliable, but `evidence_gaps=49` dominates the operator's first read and `/api/tasksets_board` has multi-second latency in beta evidence.
- Boundary: this seminar authorizes only `TASK-AR-617` RFC work. It does not authorize UI source mutation.

## Signal

| Signal | Status | Evidence |
| --- | --- | --- |
| Active-claim and empty-lane refinement | pass | `reviews/BETA-TEST-2026-06-19-tsaw-claim-empty-refinement.md` closed `BTC-TSAW-CLAIM-001` and `BTC-TSAW-EMPTY-001`. |
| Evidence-gap overload | watch | The beta run reported `evidence_gaps=49`, making stale evidence the dominant lane. |
| API latency | watch | `/api/tasksets_board` ranged from about `6.9s` to longer cold-path attempts, with one W4B request timing out before a later success. |
| Inactive layout measurement | watch | Active `#view-tsboard` mobile scan passed, but full-page scans can still see wide inactive inbox elements. |
| Design-system readiness | pass | `ui_ux_cycle assess` reports role coverage and `design_system_gate.status=pass`; reusable asset classification is required before implementation. |

## Source Evidence

| Evidence | Signal |
| --- | --- |
| `reviews/BETA-TEST-2026-06-19-tsaw-claim-empty-refinement.md` | Live beta evidence for active claims, zero-count empty lane, desktop, mobile, keyboard, reduced motion, and current lane counts. |
| `reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md` | Accepts the tactical refinement and recommends evidence-gap overload plus performance-aware IA as the next design topic. |
| `reviews/W4B-2026-06-19-TASK-AR-615.md` | Independently verifies the evaluation and records the live API timeout/resolution residual risk. |
| `reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md` | Establishes the maturity gap: colors/theme are assetized, but type, spacing, component APIs, patterns, and gates need stronger contracts. |
| `docs/design/agent-runtime/DESIGN.md` | Accepted product direction remains a dense, evidence-first operator console, not a marketing or decorative dashboard. |
| `docs/design/agent-runtime/DESIGN-SYSTEM.md` | New UI deltas must be classified as `design_token`, `ui_component`, `pattern_component`, or `one_off_for_now`. |

## Seminar Positions

| Role | Position | Constraint |
| --- | --- | --- |
| `lead-designer` | The next design should make stale evidence review feel like a queue with ownership, freshness, severity, and explainable counts. A faster version of the current overloaded lane is not enough. | The first viewport must answer "which evidence gap matters now" and "what can be deferred". |
| `design-system-steward` | The design may introduce new density, count, loading, and evidence-freshness assets, but they must start as named tokens/components/patterns rather than page-local CSS. | Use existing tokens and `components/ui` equivalents first; promote only the reusable deltas. |
| `interface-designer` | Implementation should split first-screen board data from slow secondary evidence detail. The page should wire data and layout; reusable evidence queue, lane cap, loading, and drill-in surfaces belong in assets. | Source mutation waits for RFC plus implementation registration. |
| `ux-evaluator` | The evidence path must test whether operators can triage 49 stale items without reading every card. | Desktop, mobile, keyboard, reduced motion, empty, stale, blocked, and latency paths must be captured. |
| `beta-tester` | The next beta must click and type through real recovery flows, not only inspect DOM presence. | BTC IDs are required for visible failures such as hidden evidence, misleading counts, timeout dead ends, or mobile overflow. |

## Direction Options

| Option | Description | Strength | Weakness | Decision |
| --- | --- | --- | --- | --- |
| `stale_evidence_grouping` | Group evidence gaps by freshness, severity, owner/team, recent change, and command readiness. | Gives meaning to `evidence_gaps=49` and supports review batching. | Does not by itself solve first-screen latency or overloaded lane rendering. | Partial. Keep as the semantic core. |
| `lane_cap_disclosure_progressive_drill_in` | Cap lane cards, disclose hidden counts, and open a drill-in queue for each evidence class. | Reduces first-screen density and makes counts explainable. | Can hide important work if the cap lacks severity/freshness ordering. | Partial. Keep as the interaction model. |
| `performance_split_board_loading` | Load first-screen lane summary first, then lazy-load evidence rows and secondary panels. | Addresses multi-second API and cold-path timeout watch items. | Faster loading would still leave an overloaded evidence lane if semantics stay flat. | Partial. Keep as the loading strategy. |
| `visual_refresh_only` | Change visual style without changing evidence semantics or data loading. | Low implementation effort. | Repeats the diagnostic failure mode: page-local restyling without asset or workflow improvement. | Rejected. |

## Selected RFC Candidate

Candidate: `evidence_review_queue_with_progressive_disclosure_and_split_loading`.

The RFC should combine the three partial options:

```text
Taskset Board -> lane summary -> evidence gap group -> capped queue -> taskset/evidence detail -> action or defer
```

This is intentionally not a brand-new visual theme. The new design value is in
how evidence overload is shaped into an actionable queue, how counts disclose
what is hidden, and how slow data is split so the first useful screen appears
before secondary detail finishes.

## Assetization Classification

| Surface or behavior | Class | Initial tier | Expected contract |
| --- | --- | --- | --- |
| Evidence freshness aliases | `design_token` | experimental | Named semantic aliases for stale, aging, fresh, missing, and unverified evidence; must include non-color labels. |
| Lane density and cap rhythm | `design_token` | experimental | Compact spacing and count disclosure rhythm for capped lanes, queue rows, and evidence group headers. |
| Loading and latency states | `design_token` | experimental | Tokenized loading emphasis for summary-ready, detail-loading, timeout-watch, and retryable states. |
| Evidence group filter | `ui_component` | experimental | Filter control for freshness, severity, owner/team, and command readiness with visible count and focus state. |
| Lane cap disclosure button | `ui_component` | experimental | Shows visible count, hidden count, and drill-in affordance without depending on color. |
| Latency budget badge | `ui_component` | experimental | Displays first-screen summary age or loading budget state in text. |
| Evidence review queue | `pattern_component` | experimental | Domain pattern combining grouped evidence gaps, capped rows, selected detail, and defer/action states. |
| Split board loading skeleton | `pattern_component` | experimental | Summary-first loading pattern that keeps the board usable while evidence detail loads or times out. |
| Inactive view containment shell | `pattern_component` | experimental | Ensures inactive views cannot create user-visible horizontal overflow or noisy beta measurements. |
| First-run migration copy | `one_off_for_now` | temporary | Allowed only to explain the new evidence queue during beta; must be removed or promoted if repeated. |

## Quality Requirements For RFC

| Dimension | Evidence requirement |
| --- | --- |
| Typography | Define readable type roles for evidence group headings, taskset ids, counts, latency labels, and queue rows at desktop and `390x844`; include truncation and line-wrap rules. |
| Size and spacing | Define capped lane density, touch targets, queue row height, group header rhythm, and stable dimensions so counts and loading states do not shift layout. |
| Color | Reuse semantic status tokens first; every freshness, severity, loading, and command state must also be textual or structural. |
| Motion | Lane expansion, queue drill-in, and lazy loading cannot rely on animation for meaning; reduced motion must preserve focus and state labels. |
| Effects | Specify focus, hover, selected row, loading, and retry states; no decorative effects should carry operational meaning. |
| Schema | Name fields for evidence freshness, evidence group, owner/team, severity, recent change, visible count, hidden count, selected detail, summary age, and loading status. |
| Assets | RFC must list token, UI component, pattern component, and one-off boundaries before any source mutation is registered. |
| Accessibility | Prove keyboard flow, focus order, labels, count announcements, retry states, empty group states, and screen-reader-visible freshness/loading text. |
| Responsiveness | Desktop may show summary, queue, and detail together; mobile must stack summary -> group -> queue -> detail without document horizontal overflow. |
| Interaction | Beta must include unknown-target triage, known-target search, stale evidence grouping, capped lane drill-in, empty group, slow detail loading, timeout/retry, blocked command, and interrupted claim paths. |

## Implementation Boundary

- Do not edit UI source from this seminar.
- `TASK-AR-617` should publish the RFC and only promote reusable design-system rules or asset contracts into design docs/gates.
- `TASK-AR-618` should derive source-mutation implementation units after the RFC is accepted.
- The eventual implementation should keep page files focused on layout and data wiring while repeated evidence queue, lane cap, loading, and containment surfaces move into assets.
- If `/api/tasksets_board` cannot provide summary-first data, the implementation task must name the state/API adapter delta before UI assets are edited.

## Beta And UX Evidence Path

| Flow | Required proof |
| --- | --- |
| Unknown evidence triage | User opens Taskset Board and identifies the highest-priority evidence gap group without reading all `49` stale items. |
| Known target retrieval | User types a taskset id/title and jumps to the matching evidence detail. |
| Capped lane drill-in | User sees visible count, hidden count, and opens the queue for the hidden evidence group. |
| Slow detail loading | Summary remains usable while detail loads; timeout or retry state is textual and recoverable. |
| Keyboard path | User reaches filters, cap disclosure, queue rows, selected detail, and retry/defer controls without traversing every card. |
| Mobile path | At `390x844`, summary, group, queue, and detail remain within document width. |
| Reduced motion | Drill-in and loading states preserve labels and focus without motion-dependent meaning. |
| Recovery | Empty group, stale evidence, blocked command, interrupted claim, inactive view containment, and no active claim states are visible and routable to BTC-style defects if broken. |

## Decision

Accept `evidence_review_queue_with_progressive_disclosure_and_split_loading` for
`TASK-AR-617`. Reject a pure stale-grouping pass, pure lane-cap pass, pure
performance pass, or pure visual refresh as insufficient alone.

## Action

| Action | Owner | State |
| --- | --- | --- |
| Publish evidence/performance IA RFC | lead-designer | next |
| Define token/component/pattern boundaries and gate implications | design-system-steward | next |
| Convert the accepted RFC into implementation registration and beta plan | interface-designer | pending |
| Verify desktop, mobile, keyboard, reduced motion, latency, and recovery evidence | ux-evaluator / beta-tester | pending |

## Risk

| Risk | Impact | Guardrail |
| --- | --- | --- |
| Lane caps hide important evidence. | Operators miss high-risk stale work. | Cap order must be explainable by severity/freshness and disclose hidden counts. |
| Split loading makes stale data feel current. | Operators trust incomplete detail. | Summary age, detail loading, timeout, and retry states must be textual. |
| New tokens become visual drift. | Design-system maturity regresses. | Use existing semantic tokens first and mark new tokens experimental. |
| Inactive DOM noise masks real mobile defects. | Beta evidence becomes ambiguous. | RFC must distinguish active-view containment from full-page inactive view scans. |

## Next

- `TASK-AR-617`: publish `reviews/RFC-2026-06-19-taskset-board-evidence-performance-ia.md`.
- `TASK-AR-618`: derive the source-mutation implementation registration input and paired beta/UX plan after the RFC is accepted.
- Keep `reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md` proposal-only; no UI source mutation is authorized by this seminar.
