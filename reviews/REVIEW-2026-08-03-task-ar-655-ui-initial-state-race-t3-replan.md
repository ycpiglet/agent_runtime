---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-08-03-task-ar-655-ui-initial-state-race-t3-replan
title: TASK-AR-655 UI Initial-State Race T3 Amendment
date: 2026-08-03
created_at: 2026-08-03T05:33:16+09:00
task_id: TASK-AR-655
unit_id: UNIT-TASK-AR-655-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
initiative_id: INIT-AR-V080-OPERABILITY-HARDENING
project_id: PROJECT-AGENT-RUNTIME
review_kind: t3-replan
reviewer: codex-root-task-ar-655-orchestrator
reviewer_role: orchestrator
status: accepted
signal: pass
verdict: ACCEPT_UI_INITIAL_STATE_RACE_REPAIR
priority: P1
finding_counts: {P0: 0, P1: 1, P2: 0}
candidate_commit: 3adaff660f99c3bdb4a85adb731bc20a5883d508
candidate_tree: 2e85ee1c61e78b73be8c72e7f639a398e7fd8bf0
defect_signature: defect:ui-console-cockpit-render-dereferences-runtime-s:cfd7f51f9ac8179b
compound_lookup_status: clear_no_legacy
release_authorized: false
tags: [task-ar-655, t3-replan, ui, browser, initial-state, race, freshness, fail-closed]
---

# TASK-AR-655 UI initial-state race T3 amendment

## Decision

Accept one release-blocking full-suite finding discovered after the
current-agent authority GREEN. Exact canonical Compound search for
`defect:ui-console-cockpit-render-dereferences-runtime-s:cfd7f51f9ac8179b`
returned no record with legacy fallback disabled.

The complete suite produced `1 failed, 4513 passed, 11 skipped, 4 warnings`.
The failing desktop Playwright case reproduced in isolation while the mobile
parameter passed. The cockpit test intentionally fetches and renders inbox
data before the page's independent initial state request must have completed.
`renderCockpit()` calls `freshnessClock()`, whose `stateFreshness()` directly
reads `runtimeState.built_at` while `runtimeState` is still `null`. The failure
is therefore a deterministic ordering race, not a claim-validator regression.

The bounded repair remains inside the already registered
`src/agent_runtime/ui_console_assets.py` surface and adds only the existing
browser E2E file to the explicit target list. It does not redesign the UI,
change server state, mutate a consumer, or broaden release authority.

## Failure-first order

1. Commit this accepted amendment, signature, target-file addition, and failed
   lifecycle state after the separately committed claim-authority GREEN.
2. Add and commit a focused test-only assertion that the served
   `stateFreshness()` implementation guards the pre-load `runtimeState=null`
   boundary; preserve the existing browser E2E reproduction as system-level
   RED evidence.
3. Make `stateFreshness()` read from a local empty-object fallback until the
   initial state snapshot arrives. Do not synthesize timestamps or suppress
   fetch failures.
4. Rerun the focused asset test, both browser parameters, UI console suites,
   registered TASK-AR-655 suites, mirror/lock checks, and the complete suite.
5. Include this signature in fresh Verify and an append-only Compound before
   replacement W4a, new W4b, and skeptic review.

## Acceptance contract

- Cockpit rendering before the first state response never dereferences null.
- Missing initial state renders the existing neutral `--:--:--` freshness
  text; it does not claim a fabricated current timestamp or healthy state.
- Once state arrives, `built_at` and then `generated_at` retain their existing
  precedence and stale-age semantics.
- Both desktop and mobile two-screen browser cases pass without retries.
- No server API, persistence, claim authority, or consumer behavior changes.

## Preserved boundary

Unit verification remains failed until the full suite is green. The active
claim stays held, the Scribe blocker remains unresolved, and skeptic/release
actions remain stopped. No merge, consumer pilot, CI dispatch, push, tag,
version, package, publication, deployment, or external release is authorized.
