---
title: Agent Runtime v0.8 Adoption and Enforcement Scope
date: 2026-07-28
signal: watch
score: 96
priority: P0
tags: [v0.8, adoption, enforcement, bean-wiki, allimbot, autofolio]
---

# Agent Runtime v0.8 Adoption and Enforcement Scope

## Bottom Line

Do not publish the current v0.8 candidate. The next release is an Adoption and
Enforcement release whose proof comes from brownfield use in Bean Wiki and
Allimbot, followed by an Autofolio v0.6 migration rehearsal.

The reusable architecture is one runtime package with composable profiles and
host-owned overlays. It is not a bespoke harness per project and not a copy of
the full current template into every repository.

## Signal

signal: watch

| Area | Observed state | Required v0.8 outcome |
| --- | --- | --- |
| Lifecycle truth | Implemented console tasks remain planned/worker-ready with no claim | task, claim, verification, and projections reconcile or block |
| Brownfield adoption | inventory includes generated trees; doctor reports installation absence as failure | `adopt --plan` produces an ownership/conflict plan before mutation |
| Sync | exact unmanaged paths and all-or-nothing conflict handling | profile selection plus managed/seed-once/host-owned/generated ownership |
| Consumer completeness | shipped skills reference scripts absent from the host template | dependency closure is a release gate |
| Hooks | Codex hooks contain Windows-only `.cmd` commands | Linux/Windows parity plus start/compact/restart continuity |
| Knowledge | compound and scribe are monolithic, date/path coupled, and weakly task-linked | per-entry task-linked records and configurable host state adapters |
| Model economy | Codex tiers resolve to one default model | effective-tier detection, dispatch reason, and actual-cost telemetry |
| Allimbot | runtime uses legacy `8787 /trigger` plus direct ntfy fallback | native `ProjectEmitter`/`v1/events` policy adapter |
| UI | tests are green but projections can disagree with work records | UI renders reconciled truth and freshness before broader polish |

## Evidence

- TASK-AR-631 implementation commit exists while its task is `planned`, its
  unit is `worker_ready`, and active claims are zero.
- The task's recorded `nav_budget_gate.py --check` command was unsupported.
- `work.py new` writes task verification commands only in body text while
  `work.py verify` reads frontmatter commands, producing
  `verification:no-commands`.
- Agent Runtime full tests pass (`2237 passed, 3 skipped`) but clean-host skill
  dependency closure is not tested.
- Autofolio v0.6 uses the correct framework/overlay/seam model but carries 21
  unmanaged paths.
- Bean Wiki already owns a mature editorial-agent overlay.
- Allimbot already owns a durable allowlisted project-event integration model.

## Decision

1. Recover TASK-AR-631 honestly; do not fabricate a historical claim.
2. Register one v0.8 initiative and taskset before further implementation.
3. Execute the control-plane and adoption tasks before additional console work.
4. Run pilots in the order Bean Wiki, Allimbot, Autofolio migration.
5. Publish `v0.8.0-rc.1` only after all pilot and clean-host gates pass.
6. Keep tag creation and final release Owner-gated.

## Release Boundaries

Included:

- lifecycle reconciliation and product-diff trace
- profile/ownership config and brownfield adoption plan
- consumer dependency closure
- cross-platform continuity hooks
- task-linked compound/scribe
- effective model-cost routing
- native Allimbot adapter
- Bean Wiki and Allimbot pilots
- Autofolio migration rehearsal
- release truth, version cascade, and mandatory browser smoke

Deferred:

- full `renderAll()` decomposition unless a measured release blocker appears
- full `/clarify` interview system
- W4c quiz
- FLOW-DIGEST automation
- broad i18n, color, and cosmetic passes

## Exit Criteria

- No pre-existing host file is overwritten unexpectedly.
- Clean-host doctor has zero blockers and every shipped skill dependency exists.
- Product/content diffs have an active or explicitly recovered work record.
- Pointer, board, task, claim, verification, and UI projections agree.
- Hook smoke passes on Linux and Windows command paths.
- Bean Wiki and Allimbot each complete at least three real pilot tasks,
  including one restart/compaction scenario.
- Autofolio migration produces a reviewed seam-reduction report.
- RC installs from the exact tag and the mandatory browser smoke passes.
