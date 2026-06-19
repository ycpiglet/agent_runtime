---
type: beta-tester-review
id: BETA-TEST-2026-06-19-oag-mobile-responsive-refinement
audience: owner
status: accepted
signal: pass
score: 94
priority: High
date: 2026-06-19
generated_at: 2026-06-19T15:10:00+09:00
task_set_id: TASKSET-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT
task_id: TASK-AR-608
unit_id: UNIT-TASK-AR-608-001
claim_id: CLAIM-20260619-145600-task-ar-608-mobile-responsive-beta
source_task_id: TASK-AR-607
participants:
  - beta-tester
  - ux-evaluator
tags: [ui, ux, beta-tester, evidence, mobile-responsive, taskset-board]
---

# OAG Mobile Responsive Refinement Beta Test

## Bottom Line

- Result: accepted. The repeat beta path confirms `BTC-OAG-CLAIM-MOBILE-001` is closed at the document level.
- Scope: tested the Taskset Board after the `TASK-AR-607` responsive refinement, using the active `TASK-AR-608` claim state.
- Boundary: no UI source files were changed by this evaluation unit.

## Environment Notes

- OS: Windows local checkout.
- Browser automation: Python Playwright, Chromium headless.
- Server: `http://127.0.0.1:8772`, launched from `.worktrees/TASK-AR-608-oag-mobile-beta`.
- Source HEAD: `d6f9cb3` (`Claim TASK-AR-608 mobile responsive beta evaluation`), including the merged `TASK-AR-607` responsive implementation.
- Data state: `/api/tasksets_board` had `49` tasksets, `267` tasks, `266` completed tasks.
- Target state: `TASKSET-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT` was active at `50%`, with `TASK-AR-607` complete and `TASK-AR-608` claimed.
- Active claim label: `claimed by codex-ux-evaluator-ar-608`.
- Command readiness label: `claim guard active`.
- Desktop viewport: `1440x900`.
- Mobile viewport: `390x844`.
- Reduced motion: Playwright `reduced_motion=reduce`; `matchMedia('(prefers-reduced-motion: reduce)')` returned `true`.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Desktop navigation | pass | `/` -> `Skip` if visible -> `loadState()` -> `More` -> `Taskset Board`; active view became `view-tsboard`. |
| Mobile navigation | pass | `/` -> `Skip` if visible -> hamburger `.sidebar-toggle` -> `More` -> `Taskset Board`; active view became `view-tsboard`. |
| Desktop width | pass | `innerWidth=1440`, `documentElement.scrollWidth=1440`, `body.scrollWidth=1440`, overflow `false`. |
| Mobile width | pass | `innerWidth=390`, `documentElement.scrollWidth=390`, `body.scrollWidth=390`, overflow `false`. |
| Target relation labels | pass | Target card showed `Taskset active`, `Claim path claimed by codex-ux-evaluator-ar-608`, `Evidence freshness stale`, `Command readiness claim guard active`, `TASK-AR-607 done`, and `TASK-AR-608 plan`. |
| Reduced motion | pass | Mobile reduced-motion path preserved `docScrollWidth=390`, `bodyScrollWidth=390`, and the same visible relation labels. |
| Wide child scan | pass | No target-card descendants had `scrollWidth > clientWidth + 1` after the mobile target card was visible. |

## User-Like Actions

| ID | Viewport | Action path | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- | --- |
| OAG-MOBILE-BETA-001 | Desktop `1440x900` | Open `/`, click first-run `Skip` if visible, run `loadState()`, open `More`, click `Taskset Board`. | Taskset Board opens and remains within the desktop viewport. | `activeView=view-tsboard`; `docScrollWidth=1440`; `bodyScrollWidth=1440`; no horizontal overflow. | pass |
| OAG-MOBILE-BETA-002 | Desktop `1440x900` | Inspect `OAG Mobile Responsive Refinement` card and relation panel. | Active TASK-AR-608 claim remains guarded, not ready-to-claim. | Chips read `Claim path claimed by codex-ux-evaluator-ar-608` and `Command readiness claim guard active`. | pass |
| OAG-MOBILE-BETA-003 | Desktop `1440x900` | Focus the target relation panel, press `Tab`. | Target panel is keyboard reachable and focus can leave the panel. | Panel exposed `aria-label="Attention graph for TASKSET-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT"`; focus moved to `.tsboard-add-title` and then `.tsboard-add-task`. | pass |
| OAG-MOBILE-BETA-004 | Mobile `390x844` | Open `/`, click first-run `Skip` if visible, click hamburger, open `More`, click `Taskset Board`. | Mobile navigation reaches the Taskset Board without overflow. | `activeView=view-tsboard`; `docScrollWidth=390`; `bodyScrollWidth=390`; no horizontal overflow. | pass |
| OAG-MOBILE-BETA-005 | Mobile `390x844` | Scroll the target taskset card into view and inspect relation labels. | Target relation state is visible and readable inside the viewport. | Target panel rect was `width=300`, `y=179`; card rect was `width=332`; relation chips were visible with the active claim labels. | pass |
| OAG-MOBILE-BETA-006 | Mobile `390x844`, reduced motion | Repeat mobile path with `prefers-reduced-motion: reduce`. | Reduced-motion preference does not hide state labels or create overflow. | `prefersReducedMotion=true`; `docScrollWidth=390`; `bodyScrollWidth=390`; no overflow. | pass |

## Mobile Width Evidence

| State | Viewport width | Document width | Body width | Target panel/card width | Overflow |
| --- | ---: | ---: | ---: | --- | --- |
| Desktop Taskset Board | `1440` | `1440` | `1440` | panel `389`, card `421` | false |
| Mobile Taskset Board | `390` | `390` | `390` | panel `300`, card `332` | false |
| Mobile target scrolled into view | `390` | `390` | `390` | panel `300`, card `332` | false |
| Mobile reduced motion | `390` | `390` | `390` | panel `300`, card `332` | false |

## Recovery Attempts

| State | Attempt | Expected result | Observed result | Status |
| --- | --- | --- | --- | --- |
| First-run interruption | Clicked `Skip` when the onboarding tour appeared. | User can recover and continue to the Taskset Board. | Tour dismissed and the Taskset Board path worked on desktop and mobile. | pass |
| Mobile hidden sidebar | Used hamburger before opening `More`. | Mobile user can reveal hidden navigation and reach Taskset Board. | `.sidebar-toggle` -> `.sidebar-more-summary` -> `button[data-view="tsboard"]` worked. | pass |
| Target card below fold | Scrolled `TASKSET-AR-OAG-MOBILE-RESPONSIVE-REFINEMENT` into view. | Labels remain readable after scroll and no overflow appears. | Target panel became visible at `y=179` with no wide child elements. | pass |
| Active claim | Used current `TASK-AR-608` claim. | Active claim state remains guarded. | UI showed `claimed by codex-ux-evaluator-ar-608` and `claim guard active`. | pass |

## Failure IDs

| BTC ID | Current status | Reproduction path | Evidence |
| --- | --- | --- | --- |
| BTC-OAG-CLAIM-MOBILE-001 | closed | `390x844` -> `/` -> `Skip` -> hamburger -> `More` -> `Taskset Board` -> target card visible. | Document and body widths both measured `390px` against a `390px` viewport. |

No new BTC IDs were assigned. No remaining user-visible defect was reproduced in the desktop, mobile, or reduced-motion paths.

## Insight

- The responsive fix worked where the prior beta failed: the same `390x844` path now has `docScrollWidth=390` instead of the earlier `641`.
- The claim-aware semantics survived the layout fix: active claim state still reads as `claimed by codex-ux-evaluator-ar-608` and command readiness still reads as `claim guard active`.
- The target taskset is far down the generated board because the board currently contains `49` tasksets; that is an information-architecture watch, not a regression in the mobile overflow fix.

## Decision

The mobile responsive refinement is beta-accepted. The next UI/UX cycle should move to a new design-direction seminar or IA proposal, not another implementation refinement for `BTC-OAG-CLAIM-MOBILE-001`.

## Action Board

| Action | Owner | State |
| --- | --- | --- |
| Close `BTC-OAG-CLAIM-MOBILE-001` as fixed in beta evidence | ux-evaluator | done |
| Preserve the exact desktop and mobile paths for W4b verification | qa-reviewer | ready |
| Use the next UI/UX cycle to propose a higher-level Taskset Board design direction | uiux / lead designer role | recommended |

## Risks / Blockers

- Risk: this beta evidence proves document-level overflow and visible labels, not a full visual screenshot review across every taskset card.
- Risk: keyboard traversal across a generated board with `49` tasksets is long. The target panel is focusable, but broader board-level quick navigation should be considered in a future design-direction cycle.

## Next Steps

- Run W4a gates for `TASK-AR-608`.
- Run independent W4b verification against this evidence.
- After release and merge, let the next UI/UX cycle select a new design-direction seminar rather than another mobile-overflow refinement.
