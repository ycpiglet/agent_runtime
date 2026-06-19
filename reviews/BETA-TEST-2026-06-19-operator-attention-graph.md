---
type: beta-tester-review
id: BETA-TEST-2026-06-19-operator-attention-graph
audience: owner
status: accepted_with_findings
signal: watch
score: 78
priority: High
date: 2026-06-19
generated_at: 2026-06-19T10:06:00+09:00
task_set_id: TASKSET-AR-OPERATOR-ATTENTION-GRAPH
task_id: TASK-AR-604
claim_id: CLAIM-20260619-120404-task-ar-604-task-ar-604-beta-resume
original_claim_id: CLAIM-20260619-095200-task-ar-604-operator-attention-graph-beta
source_task_id: TASK-AR-603
participants:
  - beta-tester
  - ux-evaluator
tags: [ui, ux, beta-tester, evidence, operator-attention-graph]
---

# Operator Attention Graph Beta Test

## Bottom Line

- Result: beta pass is accepted with two user-visible findings.
- Scope: tested the first `operator_attention_graph` relation panel on the live Taskset Board and transient recovery fixtures.
- Boundary: no UI source files were changed; findings are routed as BTC-style follow-up candidates.

## Environment Notes

- OS: Windows local checkout.
- Browser automation: Python Playwright, Chromium headless.
- Server: `http://127.0.0.1:8766`, launched from `.worktrees/TASK-AR-604-oag-beta` with local `src` on `PYTHONPATH`.
- Supplemental server after claim resume: `http://127.0.0.1:8767`, launched from the same worktree after root claim metadata was fast-forwarded.
- Data state: live repo state during original run under `CLAIM-20260619-095200-task-ar-604-operator-attention-graph-beta`; evidence was later preserved under resumed claim `CLAIM-20260619-120404-task-ar-604-task-ar-604-beta-resume` after the predecessor expired and was reaped.
- Desktop viewport: `1440x900`.
- Mobile viewport: requested `390x844`; browser reported `641px` layout viewport and the panel did not overflow that viewport.
- Reduced motion: Playwright `reduced_motion=reduce`.

## User-Like Actions

| ID | Viewport | Action path | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- | --- |
| OAG-BETA-001 | Desktop | Open `/#work/board`, dismiss first-run tour with `Skip`, inspect `TASKSET-AR-OPERATOR-ATTENTION-GRAPH` relation panel. | Relation panel is visible and uses text labels for taskset, claim path, evidence freshness, and command readiness. | Panel found. Text included `TASKSET active`, `CLAIM PATH ready to claim`, `EVIDENCE FRESHNESS stale`, and `COMMAND READINESS task.create ready`. | watch |
| OAG-BETA-002 | Desktop | Focus the relation panel, press `Tab`. | Panel is keyboard reachable and focus can leave it predictably. | `document.activeElement` was the relation panel after focus; after `Tab`, focus moved to the `tsboard-add-title` input. | pass |
| OAG-BETA-003 | Desktop | Click `Expand` on Operator Attention Graph, then click child row `TASK-AR-604`. | Child rows expose implementation and evaluation tasks; selecting the evaluation task opens task detail. | Expanded child IDs were `TASK-AR-603`, `TASK-AR-604`; detail panel contained `TASK-AR-604` title, status, owner, priority, and action controls. | pass |
| OAG-BETA-004 | Mobile | Open `/#work/board`, dismiss first-run tour, inspect relation panel. | Graph context stacks without hiding evidence or command state. | Relation body computed as a single column; panel text preserved taskset, claim path, evidence, command, and child graph rows. | pass |
| OAG-BETA-005 | Reduced motion | Open `/#work/board` under reduced-motion media setting. | Runtime honors reduced-motion preference. | `matchMedia('(prefers-reduced-motion: reduce)')` was true, root `data-motion` was `off`, and panel transition duration was near-zero. | pass |

## Recovery Attempts

| State | Attempt | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- |
| First-run interruption | First click attempt hit onboarding overlay; clicked `Skip`. | User can recover and continue without losing route. | Overlay text was visible; after `Skip`, board actions were available. | pass |
| Empty graph | Rendered a transient in-browser `patternAttentionRelationPanel` fixture with `graphItems: []`. | Empty graph has visible fallback text, not a blank panel. | Fixture included `GRAPH CONTEXT` and `No graph context`. | pass |
| Stale evidence | Fixture included stale evidence row. | Stale state is visible through text, not color only. | Fixture included `STALE`, `Stale evidence`, and `No heartbeat after release window`. | pass |
| Missing evidence | Fixture included missing evidence row. | Missing state is visible and scannable. | Fixture included `MISSING`, `Missing graph evidence`, and `No wiki context linked`. | pass |
| Blocked command | Fixture included blocked command readiness row. | Blocked command state explains why action is blocked. | Fixture included `COMMAND READINESS blocked by claim guard` and `BLOCKED Blocked command`. | pass |
| Interrupted claim | Called `tasksetChildRelationState({status: "interrupted", phase: "interrupted"})`. | Interrupted or incomplete claim should not collapse into stale/ready language. | Adapter returned `stale`; live claim panel also showed `ready to claim` while TASK-AR-604 was actively claimed. | fail |

## Failure IDs

| BTC ID | Severity | Reproduction path | Expected | Observed | Follow-up owner | Assetization class |
| --- | --- | --- | --- | --- | --- | --- |
| BTC-OAG-BLOCKED-001 | High | With active or recently reaped TASK-AR-604 claim context, open `http://127.0.0.1:8766/#work/board`, dismiss tour, inspect Operator Attention Graph relation chips. | Claim path and command readiness should reflect the active claim, expired predecessor, or guarded evaluation state. | Relation panel says `CLAIM PATH ready to claim` and `COMMAND READINESS task.create ready`. | interface-designer | pattern_component / one_off_for_now adapter |
| BTC-OAG-INTERRUPT-001 | Medium | In browser context, call `tasksetChildRelationState({status: "interrupted", phase: "interrupted"})` or inspect an incomplete claim state. | Interrupted/incomplete state should have a distinct label or map to a blocked/recovery state. | Adapter returns `stale`, which hides interruption severity. | interface-designer | one_off_for_now adapter |

## Evidence Summary

- Live panel count on Taskset Board: `47`.
- Operator Attention Graph panel found: `true`.
- Resume retest: on `http://127.0.0.1:8767/#work/board`, `/api/state` contained both the resumed claim and the expired predecessor claim, but the Operator Attention Graph panel still showed `CLAIM PATH ready to claim` and `COMMAND READINESS task.create ready`.
- Relation chip text included visible labels for `TASKSET`, `CLAIM PATH`, `EVIDENCE FRESHNESS`, and `COMMAND READINESS`.
- Evidence row text: `STALE / Evidence freshness / 1/2 tasks complete; no recent activity`.
- Graph context rows: `TASK-AR-603 done`, `TASK-AR-604 plan`.
- Mobile panel overflow: `false` for the reported layout viewport.

## Decision

The beta pass is strong enough to close the evaluation unit, but it should feed a follow-up implementation refinement. The next UI/UX cycle should prioritize claim-aware relation mapping before pursuing a new visual direction.
