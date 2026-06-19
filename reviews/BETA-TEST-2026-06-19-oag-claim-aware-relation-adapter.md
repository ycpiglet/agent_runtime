---
type: beta-tester-review
id: BETA-TEST-2026-06-19-oag-claim-aware-relation-adapter
audience: owner
status: accepted_with_findings
signal: watch
score: 86
priority: High
date: 2026-06-19
generated_at: 2026-06-19T13:40:00+09:00
task_set_id: TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER
task_id: TASK-AR-606
unit_id: UNIT-TASK-AR-606-001
claim_id: CLAIM-20260619-132600-task-ar-606-claim-aware-relation-beta
source_task_id: TASK-AR-605
participants:
  - beta-tester
  - ux-evaluator
tags: [ui, ux, beta-tester, evidence, claim-aware-relation-adapter]
---

# Claim-Aware Relation Adapter Beta Test

## Bottom Line

- Result: accepted with one responsive defect.
- Scope: tested the claim-aware relation adapter after `TASK-AR-605` on the live Taskset Board, including active claim, no-claim, guarded/expired, interrupted, keyboard, reduced-motion, and mobile paths.
- Boundary: no UI source files were changed. One temporary interrupted-claim fixture was created in the evaluation worktree, verified through the browser/API, then deleted before evidence closeout.

## Environment Notes

- OS: Windows local checkout.
- Browser automation: Python Playwright, Chromium headless.
- Server: `http://127.0.0.1:8769`, launched from `.worktrees/TASK-AR-606-claim-aware-relation-beta`.
- Data state: root/worktree had active claim `CLAIM-20260619-132600-task-ar-606-claim-aware-relation-beta`; `TASK-AR-605` was released and completed.
- Desktop viewport: `1440x900`.
- Mobile viewport: `390x844`.
- Reduced motion: Playwright `reduced_motion=reduce`; `matchMedia('(prefers-reduced-motion: reduce)')` returned `true`.

## User-Like Actions

| ID | Viewport | Action path | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- | --- |
| OAG-CLAIM-BETA-001 | Desktop | Open `/`, click first-run `Skip`, open `More`, click `Taskset Board`. | Taskset Board opens and target relation panel is visible. | `activeView=view-tsboard`; panel visible with `Attention graph for TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER`. | pass |
| OAG-CLAIM-BETA-002 | Desktop | Inspect `Claim-Aware Relation Adapter` panel. | Active TASK-AR-606 claim is not shown as ready-to-claim or task.create-ready. | Chips read `CLAIM PATH claimed by codex-ux-evaluator-ar-606` and `COMMAND READINESS claim guard active`. | pass |
| OAG-CLAIM-BETA-003 | Desktop | Inspect guarded predecessor state on `Operator Attention Graph`. | Expired/reaped claim context appears guarded, not ready. | Chips read `CLAIM PATH 1 guarded` and `COMMAND READINESS claim guard review`. | pass |
| OAG-CLAIM-BETA-004 | Desktop | Inspect no-active-claim taskset `Console Operator`. | No-claim taskset uses normal ready labels. | Chips read `CLAIM PATH ready to claim` and `COMMAND READINESS task.create ready`. | pass |
| OAG-CLAIM-BETA-005 | Desktop | Focus target relation panel, press `Tab`. | Panel is keyboard reachable and focus exits predictably. | Panel focus succeeded; next focus moved to `.tsboard-add-title`. | pass |
| OAG-CLAIM-BETA-006 | Mobile | Open `/`, click `Skip`, click hamburger, open `More`, click `Taskset Board`. | Mobile navigation reaches Taskset Board. | `hamburger`, `more`, and `tsboard` clicks passed; target panel visible. | pass |
| OAG-CLAIM-BETA-007 | Mobile | Inspect Taskset Board layout after target panel is visible. | Page fits the 390px viewport without horizontal scroll. | `documentElement.scrollWidth=641`, `window.innerWidth=390`, `overflowX=true`. | fail |

## Recovery Attempts

| State | Attempt | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- |
| First-run interruption | Initial page showed onboarding tour; clicked `Skip`. | User can recover without losing context. | Tour dismissed and desktop Taskset Board navigation became clickable. | pass |
| Active claim | Used current TASK-AR-606 claim. | Claim and command readiness are guarded by active claim. | `claimed by codex-ux-evaluator-ar-606`; `claim guard active`. | pass |
| Expired/guarded claim | Inspected `TASKSET-AR-OPERATOR-ATTENTION-GRAPH`, which carries a guarded prior claim. | Guarded path is visible and not color-only. | `1 guarded`; `claim guard review`; `.relation-guarded`. | pass |
| Interrupted claim | Added temporary worktree-only claim `CLAIM-TEMP-20260619-task-ar-606-interrupted-fixture` with `phase=interrupted`, refreshed UI/API, then deleted it. | Interrupted claim maps to recovery wording. | API state became `interrupted`; DOM showed `CLAIM PATH 1 interrupted`, `COMMAND READINESS interruption recovery`, and `.relation-interrupted`. | pass |
| No claim | Inspected `TASKSET-AR-UI-CONSOLE` / `Console Operator`. | Normal taskset remains ready to claim/create. | `ready to claim`; `task.create ready`. | pass |
| Reduced motion | Loaded desktop under reduced motion. | Reduced-motion preference is honored while relation states remain legible. | `matchMedia(...reduce)=true`; state text remained visible. | pass |

## Failure IDs

| BTC ID | Severity | Reproduction path | Expected | Observed | Follow-up owner | Assetization class |
| --- | --- | --- | --- | --- | --- | --- |
| BTC-OAG-CLAIM-MOBILE-001 | Medium | `390x844` viewport -> `/` -> `Skip` -> hamburger -> `More` -> `Taskset Board`. | Target Taskset Board and relation panel fit without horizontal overflow. | Document width was `641px` against a `390px` viewport after the panel became visible. | interface-designer | pattern_component / responsive layout token use |

## Evidence Summary

- Live Taskset Board panel count: `48`.
- Target panel visible on desktop and mobile after the correct navigation path.
- Target active state: `CLAIM PATH claimed by codex-ux-evaluator-ar-606`; `COMMAND READINESS claim guard active`.
- Guarded state sample: `Operator Attention Graph` showed `1 guarded` and `claim guard review`.
- Interrupted fixture sample: `claim_summary.state=interrupted`; `command_label=interruption recovery`; DOM used `.relation-interrupted`.
- No-claim sample: `Console Operator` showed `ready to claim` and `task.create ready`.
- Accessibility sample: target panel aria label was `Attention graph for TASKSET-AR-OAG-CLAIM-AWARE-RELATION-ADAPTER`; `tabindex=0`; `Tab` moved to `.tsboard-add-title`.

## Decision

The claim-aware adapter fix is semantically accepted. The next UI/UX cycle should be another implementation refinement, not a new visual direction yet: fix the mobile Taskset Board overflow while preserving the claim-aware state semantics.
