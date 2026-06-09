# REVIEW: TASK-AR-221 Operating Chain Integration

## Bottom Line

`TASK-AR-221` now has an operating-chain mapping from the `TASK-AR-223` closeout bundle to the 1-16 requirements, hold routes, and `TASK-AR-210` release-state decision inputs.

## Source Bundle

- entrypoint: `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation.md`
- current recommendation: `ready_for_governance_review`
- release boundary: not `release`
- next decision owner: `TASK-AR-210`

## Requirement Mapping

| Req | Requirement | Evidence | Status | Remaining Route |
|---:|---|---|---|---|
| 1 | Knowledge skill router | `agents/project/CONTEXT-SOURCES.yml`, `agents/project/SKILL-GOVERNANCE.md` | partial | `hold_for_query_contract` if router fields are missing in live use |
| 2 | Runbook skill contract | `agents/project/SKILL-GOVERNANCE.md`, `TASK-AR-202` | partial | keep in governance review |
| 3 | Warehouse document standard | `agents/project/README.md`, `DATASET-CATALOG.yml`, `EVAL-POLICY.yml` | partial | keep in governance review |
| 4 | Skill/data/model co-location enforcement | `agents/project/SKILL-DATA-MAP.yml`, `TASK-AR-204` | partial | block if co-location gate is not executable |
| 5 | Offline eval 90% gate | `OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217.json` | pass-baseline | provider-specific scoring optional boundary |
| 6 | Live reviewer footer | `LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json` | pass-baseline | live provider behavior optional boundary |
| 7 | Auto correction collector | `CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json` | pass-baseline | proposals require owner sign-off |
| 8 | Human definition responsibility | correction proposal files, `SKILL-GOVERNANCE.md` | pass-baseline | final definitions owner-approved only |
| 9 | Enforced rules over warnings | live/offline/A2A gates return block on missing evidence | pass-baseline | CI/preflight hardline still belongs to `TASK-AR-204/210` |
| 10 | Query refinement | goldset `query_contract`, `CONTEXT-SOURCES.yml` | pass-baseline | live missing query fields route `hold_for_query_contract` |
| 11 | SSoT ranking | `CONTEXT-SOURCES.yml`, `DATASET-CATALOG.yml` | partial | source freshness review before public release |
| 12 | Accuracy/speed/cost tradeoff | `EVAL-POLICY.yml`, prediction/reviewer reports | partial | explicit tradeoff score still future hardening |
| 13 | Metadata schema | goldsets, prediction reports, reviewer reports | pass-baseline | live provider output must keep same metadata |
| 14 | Team/roadmap/org overlay | `PROJECT-CONTEXT.yml`, `ROADMAP.md`, `ORG.md`, `LINKS.md`, `TEAMS.md` | partial | `hold_for_overlay` if cross-project simulation is missing |
| 15 | Project overlay portability | `TASK-AR-211/215` references, closeout bundle | partial | requires explicit cross-project simulation |
| 16 | A2A trace/message bus | `A2A-TRACE-GATE-2026-06-09-task-ar-208.json` | pass-baseline | live network transport optional boundary |

## Hold Route Mapping

| Route | Trigger | Current Evidence | Current State |
|---|---|---|---|
| `hold_for_query_contract` | missing business scope, time window, tolerance, ambiguity, source tier | goldset query contracts and prediction scoring | no current baseline blocker |
| `hold_for_overlay` | missing/stale project overlay or cross-project simulation gap | overlay files linked, simulation not finalized | possible governance hold |
| `hold_for_data` | migration/data/provenance evidence gap | migration hold routing exists, approvals still boundary | possible governance hold |
| `block` | missing required evidence or warn-only route | gates now block missing evidence | no current baseline blocker |
| `ready` | all hold routes closed with evidence | validation lanes pass baseline, partial governance boundaries remain | not yet proven |
| `release` | owner-approved ready state and release execution | not attempted | not allowed now |

## TASK-AR-210 Translation Input

- recommended_input_state: `ready_for_governance_review`
- allowed_state_candidate: `hold_for_data` or `hold_for_overlay` unless migration approvals and overlay simulation are closed before decision.
- ready_candidate_condition:
  - migration approval closure complete.
  - overlay cross-project simulation complete.
  - `TASK-AR-204` co-location block rule executable.
  - `TASK-AR-210` accepts baseline-only provider/live transport boundary or adds provider-specific evidence.

## Decision

Proceed to `TASK-AR-210` release-state translation. Do not mark `ready` or `release` until migration, overlay, and co-location governance boundaries are either closed or explicitly owner-approved.

## Verification

- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-operating-chain --check`
- Result: `findings=0`
