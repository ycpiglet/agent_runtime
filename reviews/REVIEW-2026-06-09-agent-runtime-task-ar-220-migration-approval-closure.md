# REVIEW: TASK-AR-220 Migration Approval Closure

## Bottom Line

Migration approval closure is complete for the `v0.1.8` baseline. The `scripts-source-only` hold is no longer release-blocking because every source-only group now has owner, approval, decision date, expiry, justification, and target state.

## Decision

- migration_release_state: `ready`
- previous_release_state: `hold_for_data`
- closed_by: `TASK-AR-220`
- closed_at: `2026-06-09`
- release_blocking: `false`
- unresolved_source_only: `0`

## Evidence

- `agents/project/MIGRATION-HOLD-ROUTING.yml`
- `agents/project/MIGRATION-COMPAT-MAP.yml`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-222-v018-closeout-bundle.md`
- `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-210-release-state-translation.md`

## Group Closure Table

| Group | Count | Target State | Owner | Approved By | Expiry |
|---|---:|---|---|---|---|
| placeholder | 1 | `drop-or-ignore` | doc-steward | TASK-AR-220 | 2026-12-31 |
| external-deploy-or-platform-scope | 10 | `keep-source-only-or-port-as-optional-plugin` | lead-engineer | TASK-AR-220 | 2026-12-31 |
| project-report-or-docs-scope | 3 | `project-overlay-or-doc-pack` | doc-steward | TASK-AR-220 | 2026-12-31 |
| runtime-gap-review | 6 | `optional-examples-or-eval-pack` | lead-engineer | TASK-AR-220 | 2026-12-31 |
| legacy-scope | 1 | `dropped` | owner | owner | 2026-12-31 |
| test-only | 32 | `port-test-if-capability-ported` | qa | TASK-AR-220 | 2026-12-31 |

## Boundary

This does not mean every source-only capability has been ported. It means the non-ported items are approved into explicit target states and are not blocking the `v0.1.8` core runtime baseline.

## Release Impact

- `hold_for_data` from migration routing can be cleared.
- Remaining release boundaries move to:
  - `TASK-AR-215` cross-project overlay simulation.
  - `TASK-AR-204` co-location enforcement executable gate.
  - `TASK-AR-210` release-state re-evaluation.

## Verification

- `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-migration-closure --check`
- Result: `findings=0`
