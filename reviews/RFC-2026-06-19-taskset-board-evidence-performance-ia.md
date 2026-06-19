---
type: ui-ux-design-rfc
id: RFC-2026-06-19-taskset-board-evidence-performance-ia
status: accepted
signal: pass
score: 91
priority: High
date: 2026-06-19
generated_at: 2026-06-20T00:42:00+09:00
task_set_id: TASKSET-AR-TASKSET-BOARD-EVIDENCE-PERF-IA
task_id: TASK-AR-617
claim_id: CLAIM-20260620-003424-task-ar-617-task-ar-617-evidence-perf-rfc
decision: evidence_review_queue_with_progressive_disclosure_and_split_loading
participants:
  - lead-designer
  - design-system-steward
  - interface-designer
  - ux-evaluator
  - beta-tester
tags: [ui, ux, rfc, taskset-board, evidence, performance, design-system]
---

# Taskset Board Evidence And Performance IA RFC

## Summary

- Decision: accept `evidence_review_queue_with_progressive_disclosure_and_split_loading`.
- User problem: the Taskset Board attention workspace now has reliable active-claim and empty-lane behavior, but `evidence_gaps=49` dominates the first read and `/api/tasksets_board` has multi-second latency watch items.
- Direction: turn evidence overload into a grouped review queue with lane cap disclosure, visible hidden counts, and summary-first loading before secondary evidence detail.
- Boundary: this RFC authorizes design-system documentation and `TASK-AR-618` implementation-unit derivation only. It does not authorize UI source mutation.

## Signal

| Signal | Status | Evidence |
| --- | --- | --- |
| Seminar decision | pass | `reviews/SEMINAR-2026-06-19-taskset-board-evidence-performance-ia.md` selected the combined evidence queue, progressive disclosure, and split-loading direction. |
| Prior refinement | pass | `reviews/BETA-TEST-2026-06-19-tsaw-claim-empty-refinement.md` closed `BTC-TSAW-CLAIM-001` and `BTC-TSAW-EMPTY-001`. |
| Evidence overload | watch | Current lane state included `evidence_gaps=49`; stale/missing evidence is too flat to triage quickly. |
| Latency | watch | `/api/tasksets_board` varied from about `6.9s` to longer cold-path attempts; W4B recorded one timeout before a later success. |
| Inactive layout scan noise | watch | Active `#view-tsboard` mobile width passed, but full-page inactive view scans can still report wide inactive elements. |
| Source mutation | blocked | No UI source file may change until `TASK-AR-618` derives and registers the implementation/beta units. |

## Source Evidence

| Evidence | Use in this RFC |
| --- | --- |
| `reviews/SEMINAR-2026-06-19-taskset-board-evidence-performance-ia.md` | Primary seminar and accepted direction. |
| `reviews/BETA-TEST-2026-06-19-tsaw-claim-empty-refinement.md` | Live beta state, lane counts, desktop/mobile/keyboard/reduced-motion evidence. |
| `reviews/UX-EVAL-2026-06-19-tsaw-claim-empty-refinement.md` | Recommends evidence-gap overload and performance-aware IA as the next design topic. |
| `reviews/W4B-2026-06-19-TASK-AR-615.md` | Independently verifies the prior evaluation and records API latency residual risk. |
| `reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md` | Establishes the need for token/component/pattern/gate assetization instead of page-local decisions. |
| `reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md` | Provides permitted visual-resource shortlist for future graph/avatar/icon/color/font work; this RFC uses it only as reference context, not as implementation approval. |
| `docs/design/agent-runtime/DESIGN.md` | Keeps the operator console dense, evidence-first, light-by-default, and non-decorative. |
| `docs/design/agent-runtime/DESIGN-SYSTEM.md` | Governs assetization classes, experimental maturity, and role routing. |

## Decision

Accept `evidence_review_queue_with_progressive_disclosure_and_split_loading`.

The Taskset Board should keep the accepted attention workspace entry point, but
the stale/missing evidence lane should no longer behave as one flat pile. The
default operator path becomes:

```text
Taskset Board
-> lane summary
-> evidence gap group
-> capped review queue
-> taskset/evidence detail
-> action, defer, retry, or route as BTC
```

The first useful screen should render a compact summary of groups and counts
before expensive detail panels finish loading. The queue must disclose how many
items are visible, how many are hidden by a cap, why the current group is first,
and whether detail data is still loading, stale, or retryable.

## Rejected Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| `stale_evidence_grouping_only` | rejected as sufficient | Grouping gives meaning to `49` gaps but does not address lane density or slow first-screen data. |
| `lane_cap_disclosure_only` | rejected as sufficient | Caps reduce visible volume but can hide urgent stale evidence unless ordered by freshness/severity. |
| `performance_split_loading_only` | rejected as sufficient | Faster loading preserves the same overloaded semantics if evidence remains flat. |
| `visual_refresh_only` | rejected | Decorative polish repeats the design-system maturity failure mode and does not improve task selection. |
| `generic_dashboard_kpi_layer` | rejected | Aggregate cards would make evidence look summarized while hiding the actual work and recovery path. |

## Target Workflow

| Flow | Required behavior |
| --- | --- |
| Unknown evidence triage | User opens Taskset Board and identifies the highest-priority evidence group without reading all `49` stale items. |
| Known target retrieval | User types a taskset id/title and jumps to the matching evidence detail. |
| Capped group drill-in | User sees visible count, hidden count, ordering reason, and opens the full group queue. |
| Detail loading | Summary and queue controls remain usable while secondary evidence detail loads. |
| Timeout/retry | Slow detail shows a textual retryable state instead of a dead or blank panel. |
| Defer/action | User can distinguish actionable evidence gaps from deferrable stale records. |
| Keyboard traversal | User reaches group filters, cap disclosure, queue rows, selected detail, and retry/defer controls without traversing every card. |
| Mobile operation | At `390x844`, summary, group list, queue, and detail stack without document-level horizontal overflow. |
| Recovery | Empty group, stale evidence, blocked command, interrupted claim, no active claim, expired claim, and inactive-view containment states are visibly labelled. |

## Visual And IA Requirements

| Area | Requirement |
| --- | --- |
| Information hierarchy | First viewport shows group identity, count, hidden count, freshness/severity reason, summary age, and selected taskset/evidence state. |
| Typography | Evidence group headings and counts use compact, readable roles; long taskset ids and status text wrap or truncate predictably at desktop and `390x844`. |
| Density | Lane summaries and queue rows favor dense scanning, but touch targets and keyboard focus targets remain stable. |
| Color and non-color cue | Freshness, severity, command readiness, and loading status reuse semantic tokens first and always include text or structural labels. |
| Motion | Expansion, drill-in, and lazy detail loading cannot rely on animation for meaning; reduced motion keeps the same labels and focus states. |
| Effects | Focus, hover, selected row, loading, timeout, and retry states clarify interaction; shadows/glow/blur cannot carry operational meaning. |
| Latency | The first useful board summary should be separable from slow evidence detail. If the API cannot split this yet, the implementation must introduce a read-only adapter contract first. |
| Inactive containment | Active Taskset Board viewport fit is the acceptance target; inactive DOM scan noise must be distinguished from user-visible overflow. |

## Assetization Plan

| Surface | Class | Initial tier | Contract |
| --- | --- | --- | --- |
| Evidence freshness aliases | `design_token` | `experimental` | Named aliases for stale, aging, fresh, missing, unverified, and retryable evidence; labels remain visible. |
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

## Schema Contract

The implementation may use the existing Taskset Board API only if these fields
are available directly or through a named read-only adapter:

| Field | Purpose | Required state examples |
| --- | --- | --- |
| `taskset_id`, `title`, `status` | Queue identity and fallback search. | active, planned, completed, archived |
| `evidence_freshness` | Grouping and stale/missing labels. | fresh, aging, stale, missing, unknown, unverified |
| `evidence_age` or `evidence_updated_at` | Ordering and summary age. | today, this session, older, unknown |
| `evidence_severity` | Queue priority within caps. | blocked, urgent, watch, deferrable |
| `owner`, `team`, `role` | Group filter and accountability. | lead-designer, interface-designer, ux-evaluator |
| `active_claim` | Active/risky relation context. | claimed, released, expired, missing |
| `claim_phase`, `progress_pct`, `status_text` | Recovery and queue reason text. | implementing, verified, interrupted, blocked |
| `command_readiness` | Safe next action and blocked command cue. | ready, guarded, blocked, unavailable |
| `visible_count`, `hidden_count` | Cap disclosure and drill-in. | 0, 1, n |
| `summary_loaded_at`, `detail_loading_state` | Latency and retry evidence. | ready, loading, stale-summary, timeout, retryable |

If these values require expensive reads, the implementation task must define a
summary-first path and lazy secondary detail path before UI assets are edited.

## Loading Budget

| State | Required UI behavior | Implementation note |
| --- | --- | --- |
| Summary ready | Lane summary, group counts, and hidden counts render first. | May use cached/read-only summary adapter. |
| Detail loading | Selected detail area shows textual loading state and keeps summary controls enabled. | No blank detail panel. |
| Timeout watch | Timeout state names what failed and offers retry/defer context. | Must not imply fresh evidence. |
| Stale summary | UI shows summary age when detail freshness is unknown. | Visible label required. |
| Retryable | Retry control is keyboard reachable and labelled. | Beta path must click or keyboard through it. |

## Quality Requirements

| Dimension | Requirement | Evidence |
| --- | --- | --- |
| Typography | Group headings, counts, queue rows, taskset ids, freshness labels, and latency labels stay readable at desktop and `390x844`. | Beta/UX notes include wrap/truncation observations. |
| Size and spacing | Queue rows, filters, cap controls, and detail panels use semantic spacing and stable dimensions. | Design-system gate plus desktop/mobile layout evidence. |
| Color | Status, freshness, severity, and loading states reuse semantic tokens first and include text labels. | Non-color cue review. |
| Motion | Drill-in/loading transitions respect reduced motion and preserve focus. | Reduced-motion beta path. |
| Effects | Focus/hover/selected/loading/retry states are visible without decorative effects. | Keyboard focus evidence. |
| Schema | Required fields and summary/detail split are named before source mutation. | `TASK-AR-618` registration input. |
| Assets | Every new helper is classified before implementation. | Closeout assetization table. |
| Accessibility | Labels, count announcements, empty states, retry states, and focus order are explicit. | UX evaluation and focused tests. |
| Responsiveness | Desktop may show summary, queue, and detail together; mobile stacks without horizontal overflow. | `390x844` measurement. |
| Interaction | Unknown triage, known search, capped drill-in, slow loading, timeout/retry, stale/blocked/interrupted/empty states are tested. | Beta-tester clicked/typed evidence and BTC IDs. |

## Implementation Boundary

- Do not edit `src/agent_runtime/*`, tests, or API code in this RFC task.
- `TASK-AR-618` must derive the source-mutating implementation registration and paired beta/UX plan.
- Page assembly in the later implementation must stay focused on layout composition and data wiring.
- Repeated evidence queue, cap disclosure, latency, and containment surfaces must move into `ui_design_assets.py` helpers or be labelled `one_off_for_now`.
- If the current Taskset Board payload cannot support summary-first loading, the implementation must register the adapter/API delta before rendering the new IA.

## Beta-Tester And UX-Evaluator Evidence

| Role | Required evidence |
| --- | --- |
| beta-tester | Click/type path for unknown evidence triage from first viewport to selected queue detail. |
| beta-tester | Known-target search path by taskset id/title. |
| beta-tester | Capped group drill-in showing visible count, hidden count, and ordering reason. |
| beta-tester | Slow detail loading and timeout/retry recovery path. |
| beta-tester | Desktop and `390x844` mobile viewport measurements with environment notes. |
| beta-tester | Keyboard traversal through filters, cap disclosure, queue rows, detail, retry/defer controls. |
| ux-evaluator | Typography, density, non-color cues, focus order, reduced motion, and screen-reader-visible state review. |
| ux-evaluator | BTC-style IDs for every visible defect with reproduction path. |

## Risk

| Risk | Impact | Guardrail |
| --- | --- | --- |
| Lane caps hide urgent work. | Operators may miss high-risk evidence gaps. | Cap ordering must be based on visible freshness/severity reasons and disclose hidden counts. |
| Split loading creates stale trust. | Operators may treat incomplete detail as fresh. | Summary age, detail loading, timeout, and retryable states are textual. |
| Queue becomes a generic inbox. | The Taskset Board loses taskset ownership semantics. | Queue rows must preserve taskset id, owner/team, claim context, and command readiness. |
| New tokens become palette drift. | Design-system maturity regresses. | Reuse existing semantic tokens first; new values are experimental and token-layer only. |
| Inactive scan noise is misread as user overflow. | Beta results route false defects. | Active-view width is measured separately from inactive full-page scan notes. |

## Decision Outcome

`evidence_review_queue_with_progressive_disclosure_and_split_loading` is
accepted and promoted to the design-system contract as an experimental
direction. It extends `taskset_attention_workspace` and `operator_attention_graph`
instead of replacing them. Source mutation remains blocked until `TASK-AR-618`
creates the implementation and beta-evaluation registration input.

## Next

- `TASK-AR-618`: derive a source-mutating implementation task and paired beta/UX evaluation plan.
- The implementation registration must name target files, schema/adapter fields, assetization classes, focused tests, design-system gate, evidence index check, and independent W4b verification.
- The beta plan must include clicked/typed actions, keyboard traversal, reduced-motion behavior, desktop/mobile viewport evidence, latency recovery, inactive-view containment, and BTC-style failure routing.
