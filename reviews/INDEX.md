---
type: evidence_index
id: EVIDENCE-INDEX-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [evidence, traceability, generated-index]
generated_at: 2026-07-30T17:24:13+09:00
record_count: 1154
---

# Evidence Index

## Bottom Line
- Summary: indexed `1154` review and evidence records under `reviews/`.
- Result: task closeout evidence is searchable by path, id, status, signal, and title.

## Signal
| Metric | State | Evidence |
| --- | --- | --- |
| Reviews covered | pass | `1154` files |
| Source | pass | `reviews/` |

## Insight
- Manual review browsing does not scale; this generated file gives agents a stable entrypoint.
- The generator excludes itself from coverage to avoid self-referential churn.

## Decision
- Decision: regenerate this index after adding closeout reviews or evidence reports.
- Decision: use `scripts/evidence_index_generator.py --check` as the stale index gate.

## Action Board
| Path | ID | Kind | Status | Signal | Title |
| --- | --- | --- | --- | --- | --- |
| `reviews/A2A-TRACE-GATE-2026-06-09-task-ar-208.json` | `A2A-TRACE-GATE-2026-06-09-task-ar-208` | json | record | n/a | A2A-TRACE-GATE-2026-06-09-task-ar-208 |
| `reviews/A2A-TRACE-GATE-2026-06-10-task-ar-208-current.json` | `A2A-TRACE-GATE-2026-06-10-task-ar-208-current` | json | record | n/a | A2A-TRACE-GATE-2026-06-10-task-ar-208-current |
| `reviews/A2A-TRACE-GATE-2026-06-10-taskset-quality-loop-final.json` | `A2A-TRACE-GATE-2026-06-10-taskset-quality-loop-final` | json | record | n/a | A2A-TRACE-GATE-2026-06-10-taskset-quality-loop-final |
| `reviews/AUTONOMY-POLICY-GATE-2026-06-09-v0.1.8.json` | `AUTONOMY-POLICY-GATE-2026-06-09-v0.1.8` | json | record | n/a | AUTONOMY-POLICY-GATE-2026-06-09-v0.1.8 |
| `reviews/BETA-EXPLORATION-2026-06-24.md` | `BETA-EXPLORATION-2026-06-24` | beta-exploration-bug-catalog | complete | pass | UI Console Beta Exploration — Bug Catalog (2026-06-24) |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-204-co-location-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-204-co-location-handoff-call` | md | record | n/a | CALL: TASK-AR-204 Co-Location Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-205-offline-eval-followup-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-205-offline-eval-followup-call` | md | record | n/a | CALL: TASK-AR-205 Offline Eval Follow-up |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-206-live-reviewer-followup-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-206-live-reviewer-followup-call` | md | record | n/a | CALL: TASK-AR-206 Live Reviewer Follow-up |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-207-correction-followup-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-207-correction-followup-call` | md | record | n/a | CALL: TASK-AR-207 Correction Collector Follow-up |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-208-a2a-followup-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-208-a2a-followup-call` | md | record | n/a | CALL: TASK-AR-208 A2A Follow-up |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-210-release-state-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-210-release-state-handoff-call` | md | record | n/a | CALL: TASK-AR-210 Release-State Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-214-owner-sync.md` | `CALL-2026-06-09-agent-runtime-task-ar-214-owner-sync` | md | record | n/a | CALL-2026-06-09-agent-runtime-task-ar-214-owner-sync |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-215-context-packet-sync-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-215-context-packet-sync-call` | md | record | n/a | CALL-2026-06-09-agent-runtime-task-ar-215-context-packet-sync-call |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-handoff-call` | md | record | n/a | CALL: TASK-AR-215 Overlay Simulation Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-218-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-218-handoff-call` | md | record | n/a | CALL-2026-06-09-agent-runtime-task-ar-218-handoff-call |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-220-migration-approval-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-220-migration-approval-handoff-call` | md | record | n/a | CALL: TASK-AR-220 Migration Approval Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-221-operating-chain-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-221-operating-chain-handoff-call` | md | record | n/a | CALL: TASK-AR-221 Operating Chain Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-222-v018-closeout-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-222-v018-closeout-handoff-call` | md | record | n/a | CALL: TASK-AR-222 v0.1.8 Closeout Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-223-217-sync-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-223-217-sync-call` | md | record | n/a | CALL: TASK-AR-223/217 Sync Call |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-handoff-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-handoff-call` | md | record | n/a | CALL: TASK-AR-223 Closeout Bundle Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-task-ar-224-sync-call.md` | `CALL-2026-06-09-agent-runtime-task-ar-224-sync-call` | md | record | n/a | CALL (2026-06-09) - TASK-AR-224 sync call |
| `reviews/CALL-2026-06-09-agent-runtime-v018-local-smoke-plan-handoff-call.md` | `CALL-2026-06-09-agent-runtime-v018-local-smoke-plan-handoff-call` | md | record | n/a | CALL: v0.1.8 Local Smoke Plan Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-v018-owner-approval-gate-handoff-call.md` | `CALL-2026-06-09-agent-runtime-v018-owner-approval-gate-handoff-call` | md | record | n/a | CALL: v0.1.8 Owner Approval Gate Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-v018-owner-approval-handoff-call.md` | `CALL-2026-06-09-agent-runtime-v018-owner-approval-handoff-call` | md | record | n/a | CALL: v0.1.8 Owner Approval Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-v018-pending-release-guard-handoff-call.md` | `CALL-2026-06-09-agent-runtime-v018-pending-release-guard-handoff-call` | md | record | n/a | CALL: v0.1.8 Pending Release Guard Handoff |
| `reviews/CALL-2026-06-09-agent-runtime-v018-release-handoff-call.md` | `CALL-2026-06-09-v018-release-handoff` | call | G | n/a | CALL-2026-06-09-agent-runtime-v018-release-handoff-call |
| `reviews/CALL-2026-06-09-agent-runtime-v018-release-readiness-summary-handoff-call.md` | `CALL-2026-06-09-agent-runtime-v018-release-readiness-summary-handoff-call` | md | record | n/a | CALL: v0.1.8 Release Readiness Summary Handoff |
| `reviews/CALL-2026-06-10-agent-runtime-task-ar-221-cycle-sync-call.md` | `CALL-2026-06-10-agent-runtime-task-ar-221-cycle-sync-call` | md | record | n/a | CALL (2026-06-10): TASK-AR-221/219/220 사이클 진행 동기화 콜 |
| `reviews/CALL-2026-06-10-agent-runtime-task-ar-221-handoff-call.md` | `CALL-2026-06-10-agent-runtime-task-ar-221-handoff-call` | md | record | n/a | CALL-2026-06-10-agent-runtime-task-ar-221-handoff-call |
| `reviews/CALL-2026-06-12-agent-runtime-task-ar-210-owner-sync.md` | `CALL-2026-06-12-agent-runtime-task-ar-210-owner-sync` | md | record | n/a | CALL-2026-06-12-agent-runtime-task-ar-210-owner-sync |
| `reviews/CALL-2026-06-13-agent-runtime-task-ar-211-overlay-sync-call.md` | `CALL-2026-06-13-agent-runtime-task-ar-211-overlay-sync-call` | md | record | n/a | CALL-2026-06-13-agent-runtime-task-ar-211-overlay-sync-call |
| `reviews/CALL-2026-06-14-agent-runtime-task-ar-222-sync-call.md` | `CALL-2026-06-14-agent-runtime-task-ar-222-sync-call` | md | record | n/a | CALL: TASK-AR-222 closeout 번들 동기화 콜 |
| `reviews/CALL-2026-06-15-agent-runtime-task-ar-223-sync-call.md` | `CALL-2026-06-15-agent-runtime-task-ar-223-sync-call` | md | record | n/a | CALL (2026-06-15) - TASK-AR-223 closeout sync call |
| `reviews/CO-LOCATION-GATE-2026-06-09-task-ar-204.json` | `CO-LOCATION-GATE-2026-06-09-task-ar-204` | json | record | n/a | CO-LOCATION-GATE-2026-06-09-task-ar-204 |
| `reviews/CO-LOCATION-GATE-2026-06-10-task-ar-223-root-current.json` | `CO-LOCATION-GATE-2026-06-10-task-ar-223-root-current` | json | record | n/a | CO-LOCATION-GATE-2026-06-10-task-ar-223-root-current |
| `reviews/CO-LOCATION-GATE-2026-06-11-task-ar-310.json` | `CO-LOCATION-GATE-2026-06-11-task-ar-310` | json | record | n/a | CO-LOCATION-GATE-2026-06-11-task-ar-310 |
| `reviews/COMPOUND-2026-06-21-business-operating-system.md` | `COMPOUND-2026-06-21-business-operating-system` | compound | recorded | pass | Business Operating System Compound Note |
| `reviews/COMPOUND-2026-06-22-release-ops-and-concurrency.md` | `COMPOUND-2026-06-22-release-ops-and-concurrency` | compound | recorded | pass | Release-ops + shared-checkout concurrency compound |
| `reviews/COMPOUND-2026-07-04-silent-wiring-and-stale-state.md` | `COMPOUND-2026-07-04-silent-wiring-and-stale-state` | compound | recorded | pass | Silent cross-step wiring failures + stale open-state compound |
| `reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md` | `COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction` | compound | recorded | watch | v0.8 lifecycle, closeout, and CI friction |
| `reviews/CONTEXT-KNOWLEDGE-GATE-2026-06-11-final.json` | `CONTEXT-KNOWLEDGE-GATE-2026-06-11-final` | json | record | n/a | CONTEXT-KNOWLEDGE-GATE-2026-06-11-final |
| `reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json` | `CORRECTION-COLLECTOR-2026-06-09-task-ar-207` | json | record | n/a | CORRECTION-COLLECTOR-2026-06-09-task-ar-207 |
| `reviews/CORRECTION-COLLECTOR-2026-06-10-task-ar-207-current.json` | `CORRECTION-COLLECTOR-2026-06-10-task-ar-207-current` | json | record | n/a | CORRECTION-COLLECTOR-2026-06-10-task-ar-207-current |
| `reviews/CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final.json` | `CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final` | json | record | n/a | CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final |
| `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md` | `COUNCIL-2026-06-14-host-feedback-first-deliberation` | council | watch | watch | Council — Host Feedback First Deliberation (TASK-AR-527) |
| `reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md` | `DIAGNOSTIC-2026-06-18-ui-design-system-maturity` | md | accepted | n/a | UI Design System Maturity Diagnostic |
| `reviews/DOC-STEWARD-2026-06-21-business-operating-system.md` | `DOC-STEWARD-2026-06-21-business-operating-system` | doc-steward-review | recorded | pass | Business Operating System Doc Steward Review |
| `reviews/GOVERNANCE-OPS-REPORT-2026-06-10.md` | `GOVERNANCE-OPS-REPORT-2026-06-10` | governance_ops_report | watch | watch | Governance Operations Report |
| `reviews/HANDOFF-2026-06-15-ui-redesign-and-product-structure.md` | `HANDOFF-2026-06-15-ui-redesign-and-product-structure` | md | record | n/a | HANDOFF — UI Redesign & Product-Structure Change (for next session) |
| `reviews/INDEPENDENT-AUDIT-2026-07-30-task-ar-650-closeout.md` | `INDEPENDENT-AUDIT-2026-07-30-task-ar-650-closeout` | md | passed | pass | Independent Auditor Closeout - TASK-AR-650 |
| `reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-206.json` | `LIVE-REVIEWER-GATE-2026-06-09-task-ar-206` | json | record | n/a | LIVE-REVIEWER-GATE-2026-06-09-task-ar-206 |
| `reviews/LIVE-REVIEWER-GATE-2026-06-09-task-ar-207-failure-sample.json` | `LIVE-REVIEWER-GATE-2026-06-09-task-ar-207-failure-sample` | json | record | n/a | LIVE-REVIEWER-GATE-2026-06-09-task-ar-207-failure-sample |
| `reviews/LIVE-REVIEWER-GATE-2026-06-10-task-ar-206-current.json` | `LIVE-REVIEWER-GATE-2026-06-10-task-ar-206-current` | json | record | n/a | LIVE-REVIEWER-GATE-2026-06-10-task-ar-206-current |
| `reviews/LIVE-REVIEWER-GATE-2026-06-10-task-ar-207-failure-sample-current.json` | `LIVE-REVIEWER-GATE-2026-06-10-task-ar-207-failure-sample-current` | json | record | n/a | LIVE-REVIEWER-GATE-2026-06-10-task-ar-207-failure-sample-current |
| `reviews/LIVE-REVIEWER-GATE-2026-06-10-taskset-quality-loop-final.json` | `LIVE-REVIEWER-GATE-2026-06-10-taskset-quality-loop-final` | json | record | n/a | LIVE-REVIEWER-GATE-2026-06-10-taskset-quality-loop-final |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-204-co-location-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-204-co-location-sync` | md | record | n/a | MEETING: TASK-AR-204 Co-Location Gate Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-goldset-readiness-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-205-goldset-readiness-sync` | md | record | n/a | MEETING: TASK-AR-205 Goldset Readiness Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-offline-eval-block-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-205-offline-eval-block-sync` | md | record | n/a | MEETING: TASK-AR-205 Offline Eval Block Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-205-prediction-scoring-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-205-prediction-scoring-sync` | md | record | n/a | MEETING: TASK-AR-205 Prediction Scoring Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-206-live-reviewer-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-206-live-reviewer-sync` | md | record | n/a | MEETING: TASK-AR-206 Live Reviewer Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-207-correction-collector-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-207-correction-collector-sync` | md | record | n/a | MEETING: TASK-AR-207 Correction Collector Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-208-a2a-trace-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-208-a2a-trace-sync` | md | record | n/a | MEETING: TASK-AR-208 A2A Trace Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-210-release-state-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-210-release-state-sync` | md | record | n/a | MEETING: TASK-AR-210 Release-State Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-214-query-contract.md` | `MEETING-2026-06-09-agent-runtime-task-ar-214-query-contract` | md | record | n/a | MEETING-2026-06-09-agent-runtime-task-ar-214-query-contract |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-packet.md` | `MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-packet` | md | record | n/a | MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-packet |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-sync` | md | record | n/a | MEETING: TASK-AR-215 Overlay Simulation Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-216-release-transition.md` | `MEETING-2026-06-09-agent-runtime-task-ar-216-release-transition` | md | record | n/a | MEETING-2026-06-09-agent-runtime-task-ar-216-release-transition |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-218-migration-hardening.md` | `MEETING-2026-06-09-agent-runtime-task-ar-218-migration-hardening` | md | record | n/a | MEETING-2026-06-09-agent-runtime-task-ar-218-migration-hardening |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan.md` | `MEETING-2026-06-09-agent-runtime-task-ar-219-220-unified-release-plan` | md | record | n/a | Bottom Line |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-220-migration-approval-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-220-migration-approval-sync` | md | record | n/a | MEETING: TASK-AR-220 Migration Approval Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-governance-update.md` | `MEETING-2026-06-09-agent-runtime-task-ar-221-governance-update` | md | record | n/a | MEETING (2026-06-09): TASK-AR-221 운영 정합 통합 및 릴리스 업데이트 정렬 |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-operating-chain-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-221-operating-chain-sync` | md | record | n/a | MEETING: TASK-AR-221 Operating Chain Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-221-version-update-and-official-guidance-refresh.md` | `MEETING-2026-06-09-agent-runtime-task-ar-221-version-update-and-official-guidance-refresh` | md | record | n/a | MEETING (2026-06-09): TASK-AR-221 공식 가이드 동기화 및 버전 업데이트 일정 정합 회의 |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-222-v018-closeout-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-222-v018-closeout-sync` | md | record | n/a | MEETING: TASK-AR-222 v0.1.8 Closeout Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-sync` | md | record | n/a | MEETING: TASK-AR-223/217 Closeout Rehearsal Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-sync` | md | record | n/a | MEETING: TASK-AR-223 Closeout Bundle Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-gate-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-224-gate-sync` | md | record | n/a | MEETING (2026-06-09) - TASK-AR-224 gate sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-224-overlay-gate-sync.md` | `MEETING-2026-06-09-agent-runtime-task-ar-224-overlay-gate-sync` | md | record | n/a | MEETING (2026-06-09) - TASK-AR-224 overlay gate sync |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene.md` | `MEETING-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene` | md | record | n/a | MEETING (2026-06-09) - TASK-AR-225 source publication hygiene |
| `reviews/MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap.md` | `MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap` | md | record | n/a | MEETING-2026-06-09-agent-runtime-task-ar-version-roadmap |
| `reviews/MEETING-2026-06-09-agent-runtime-v018-local-smoke-plan-sync.md` | `MEETING-2026-06-09-agent-runtime-v018-local-smoke-plan-sync` | md | record | n/a | MEETING: v0.1.8 Local Smoke Plan Readiness Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-v018-owner-approval-gate-sync.md` | `MEETING-2026-06-09-agent-runtime-v018-owner-approval-gate-sync` | md | record | n/a | MEETING: v0.1.8 Owner Approval Gate Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-v018-pending-release-guard-sync.md` | `MEETING-2026-06-09-agent-runtime-v018-pending-release-guard-sync` | md | record | n/a | MEETING: v0.1.8 Pending Release Guard Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-v018-release-council-sync.md` | `MEETING-2026-06-09-v018-release-council` | meeting | G | n/a | MEETING-2026-06-09-agent-runtime-v018-release-council-sync |
| `reviews/MEETING-2026-06-09-agent-runtime-v018-release-execution-boundary-sync.md` | `MEETING-2026-06-09-agent-runtime-v018-release-execution-boundary-sync` | md | record | n/a | MEETING: v0.1.8 Release Execution Boundary Sync |
| `reviews/MEETING-2026-06-09-agent-runtime-v018-release-readiness-summary-sync.md` | `MEETING-2026-06-09-agent-runtime-v018-release-readiness-summary-sync` | md | record | n/a | MEETING: v0.1.8 Release Readiness Summary Sync |
| `reviews/MEETING-2026-06-10-agent-runtime-rsi-planning-loop.md` | `MEETING-2026-06-10-agent-runtime-rsi-planning-loop` | md | record | n/a | Meeting: RSI Planning Loop And Agent Departments |
| `reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-start.md` | `MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-start` | md | record | n/a | MEETING (2026-06-10): TASK-AR-221 선행 사이클 오프닝 |
| `reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-sync.md` | `MEETING-2026-06-10-agent-runtime-task-ar-221-cycle-sync` | md | record | n/a | MEETING (2026-06-10): 멀티에이전트 순차 실행 동기화 |
| `reviews/MEETING-2026-06-10-agent-runtime-task-ar-221-governance-cycle.md` | `MEETING-2026-06-10-agent-runtime-task-ar-221-governance-cycle` | md | record | n/a | MEETING-2026-06-10-agent-runtime-task-ar-221-governance-cycle |
| `reviews/MEETING-2026-06-10-agent-runtime-task-ar-222-version-update-closeout-plan.md` | `MEETING-2026-06-10-agent-runtime-task-ar-222-version-update-closeout-plan` | md | record | n/a | MEETING: TASK-AR-222 v0.1.8 판정 closeout 기획 |
| `reviews/MEETING-2026-06-10-task-ar-201-definition-policy.md` | `MEETING-2026-06-10-task-ar-201-definition-policy` | md | record | n/a | MEETING-2026-06-10-task-ar-201-definition-policy.md |
| `reviews/MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration.md` | `MEETING-2026-06-11-agent-runtime-rsi-operating-system-registration` | meeting | recorded | pass | RSI Operating System Registration Meeting |
| `reviews/MEETING-2026-06-11-agent-runtime-task-ar-summary-and-version-closeout.md` | `MEETING-2026-06-11-agent-runtime-task-ar-summary-and-version-closeout` | md | record | n/a | MEETING-2026-06-11-agent-runtime-task-ar-summary-and-version-closeout |
| `reviews/MEETING-2026-06-12-agent-runtime-task-ar-210-gate-coordination.md` | `MEETING-2026-06-12-agent-runtime-task-ar-210-gate-coordination` | md | record | n/a | MEETING-2026-06-12-agent-runtime-task-ar-210-gate-coordination |
| `reviews/MEETING-2026-06-12-independent-verification-rule.md` | `MEETING-2026-06-12-independent-verification-rule` | meeting | pass | pass | Independent Verification Rule Meeting |
| `reviews/MEETING-2026-06-12-parallel-work-lifecycle-rules.md` | `MEETING-2026-06-12-parallel-work-lifecycle-rules` | meeting | pass | pass | Parallel Work Lifecycle Rules Meeting |
| `reviews/MEETING-2026-06-12-plan-assumption-deferred-revalidation.md` | `MEETING-2026-06-12-plan-assumption-deferred-revalidation` | meeting | pass | pass | Plan Assumption Deferred Revalidation Meeting |
| `reviews/MEETING-2026-06-12-work-hierarchy-numbering-and-recording.md` | `MEETING-2026-06-12-work-hierarchy-numbering-and-recording` | meeting | pass | pass | Work Hierarchy Numbering And Recording Meeting |
| `reviews/MEETING-2026-06-12-work-item-generator-metadata-agent-identity.md` | `MEETING-2026-06-12-work-item-generator-metadata-agent-identity` | meeting | pass | pass | Work Item Generator, Metadata, And Agent Identity Intake |
| `reviews/MEETING-2026-06-12-work-metadata-a2a-registration-audit.md` | `MEETING-2026-06-12-work-metadata-a2a-registration-audit` | meeting | pass | pass | Work Metadata And A2A Registration Audit |
| `reviews/MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update.md` | `MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update` | md | record | n/a | MEETING-2026-06-13-agent-runtime-cross-project-governance-and-release-update |
| `reviews/MEETING-2026-06-13-agent-runtime-task-ar-211-overlay-implementation-checkpoint.md` | `MEETING-2026-06-13-agent-runtime-task-ar-211-overlay-implementation-checkpoint` | md | record | n/a | MEETING-2026-06-13-agent-runtime-task-ar-211-overlay-implementation-checkpoint |
| `reviews/MEETING-2026-06-13-parallel-wave-replan-post-codex-merge.md` | `MEETING-2026-06-13-parallel-wave-replan-post-codex-merge` | meeting | pass | pass | Parallel Wave Replan After Codex Merge (T3) |
| `reviews/MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync.md` | `MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync` | md | record | n/a | MEETING: TASK-AR-220/222 closeout 동기화 정합 미팅 |
| `reviews/MEETING-2026-06-14-agent-runtime-task-ar-223-closeout-planning.md` | `MEETING-2026-06-14-agent-runtime-task-ar-223-closeout-planning` | md | record | n/a | MEETING (2026-06-14) - TASK-AR-223 closeout planning |
| `reviews/MEETING-2026-06-14-host-feedback-intake-registration.md` | `MEETING-2026-06-14-host-feedback-intake-registration` | meeting | watch | watch | Host Feedback Intake — Deliberation Topic + Taskset Registration |
| `reviews/MEETING-2026-06-14-product-maturity-uplift-taskset-registration.md` | `MEETING-2026-06-14-product-maturity-uplift-taskset-registration` | meeting | watch | watch | Product Maturity Uplift — Taskset Registration |
| `reviews/MEETING-2026-06-14-wave-plan-host-store-console.md` | `MEETING-2026-06-14-wave-plan-host-store-console` | meeting | watch | watch | Wave Execution Plan — Host Feedback + Work Store + Decision Console |
| `reviews/MEETING-2026-06-15-agent-runtime-task-ar-223-cycle-sync.md` | `MEETING-2026-06-15-agent-runtime-task-ar-223-cycle-sync` | md | record | n/a | MEETING (2026-06-15) - TASK-AR-223 closeout cycle sync |
| `reviews/MEETING-2026-06-17-self-improvement-cycle-sync.md` | `MEETING-2026-06-17-self-improvement-cycle-sync` | meeting | planned | planned | Self Improvement Cycle Sync |
| `reviews/MEETING-2026-06-20-ui-refactor-cycle-2-seminar-beta.md` | `MEETING-2026-06-20-ui-refactor-cycle-2-seminar-beta` | md | record | pass | UI Refactor Cycle 2 Seminar and Beta Review |
| `reviews/MEETING-2026-06-20-ui-refactor-cycle-3-seminar-beta.md` | `MEETING-2026-06-20-ui-refactor-cycle-3-seminar-beta` | md | record | pass | UI Refactor Cycle 3 Seminar and Beta Checkpoint |
| `reviews/MEETING-2026-06-20-ui-refactor-cycle-4-seminar-beta.md` | `MEETING-2026-06-20-ui-refactor-cycle-4-seminar-beta` | md | record | pass | UI Refactor Cycle 4 Seminar and Beta Checkpoint |
| `reviews/MEETING-2026-06-20-ui-refactor-cycle-seminar-beta.md` | `MEETING-2026-06-20-ui-refactor-cycle-seminar-beta` | md | record | pass | UI Refactor Cycle Seminar and Beta Review |
| `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion.json` | `OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion` | json | record | n/a | OFFLINE-EVAL-2026-06-09-task-ar-217-after-goldset-expansion |
| `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217-rerun.json` | `OFFLINE-EVAL-2026-06-09-task-ar-217-rerun` | json | record | n/a | OFFLINE-EVAL-2026-06-09-task-ar-217-rerun |
| `reviews/OFFLINE-EVAL-2026-06-09-task-ar-217.json` | `OFFLINE-EVAL-2026-06-09-task-ar-217` | json | record | n/a | OFFLINE-EVAL-2026-06-09-task-ar-217 |
| `reviews/OFFLINE-EVAL-2026-06-10-task-ar-205-current-log.md` | `REVIEW-2026-06-10-task-ar-205-current` | md | record | n/a | REVIEW: TASK-AR-205 Continuation (2026-06-10) |
| `reviews/OFFLINE-EVAL-2026-06-10-task-ar-205-current.json` | `OFFLINE-EVAL-2026-06-10-task-ar-205-current` | json | record | n/a | OFFLINE-EVAL-2026-06-10-task-ar-205-current |
| `reviews/OFFLINE-EVAL-2026-06-10-task-ar-247-pane-progress.json` | `OFFLINE-EVAL-2026-06-10-task-ar-247-pane-progress` | json | record | n/a | OFFLINE-EVAL-2026-06-10-task-ar-247-pane-progress |
| `reviews/OFFLINE-EVAL-2026-06-10-taskset-quality-loop-final.json` | `OFFLINE-EVAL-2026-06-10-taskset-quality-loop-final` | json | record | n/a | OFFLINE-EVAL-2026-06-10-taskset-quality-loop-final |
| `reviews/OFFLINE-EVAL-2026-06-11-context-knowledge-final.json` | `OFFLINE-EVAL-2026-06-11-context-knowledge-final` | json | record | n/a | OFFLINE-EVAL-2026-06-11-context-knowledge-final |
| `reviews/OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217.json` | `OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217` | json | record | n/a | OFFLINE-PREDICTION-SCORE-2026-06-09-task-ar-217 |
| `reviews/OFFLINE-PREDICTION-SCORE-2026-06-10-task-ar-205-current.json` | `OFFLINE-PREDICTION-SCORE-2026-06-10-task-ar-205-current` | json | record | n/a | OFFLINE-PREDICTION-SCORE-2026-06-10-task-ar-205-current |
| `reviews/OFFLINE-PREDICTION-SCORE-2026-06-10-taskset-quality-loop-final.json` | `OFFLINE-PREDICTION-SCORE-2026-06-10-taskset-quality-loop-final` | json | record | n/a | OFFLINE-PREDICTION-SCORE-2026-06-10-taskset-quality-loop-final |
| `reviews/OFFLINE-PREDICTION-SCORE-2026-06-11-context-knowledge-final.json` | `OFFLINE-PREDICTION-SCORE-2026-06-11-context-knowledge-final` | json | record | n/a | OFFLINE-PREDICTION-SCORE-2026-06-11-context-knowledge-final |
| `reviews/OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215.json` | `OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215` | json | record | n/a | OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215 |
| `reviews/OVERLAY-SIMULATION-GATE-2026-06-10-task-ar-223-root-current.json` | `OVERLAY-SIMULATION-GATE-2026-06-10-task-ar-223-root-current` | json | record | n/a | OVERLAY-SIMULATION-GATE-2026-06-10-task-ar-223-root-current |
| `reviews/OVERLAY-SIMULATION-GATE-2026-06-11-context-knowledge-final.json` | `OVERLAY-SIMULATION-GATE-2026-06-11-context-knowledge-final` | json | record | n/a | OVERLAY-SIMULATION-GATE-2026-06-11-context-knowledge-final |
| `reviews/OWNER-APPROVAL-GATE-2026-06-09-v0.1.8.json` | `OWNER-APPROVAL-GATE-2026-06-09-v0.1.8` | json | record | n/a | OWNER-APPROVAL-GATE-2026-06-09-v0.1.8 |
| `reviews/PENDING-RELEASE-GUARD-2026-06-09-v0.1.8.json` | `PENDING-RELEASE-GUARD-2026-06-09-v0.1.8` | json | record | n/a | PENDING-RELEASE-GUARD-2026-06-09-v0.1.8 |
| `reviews/PILOT-ALLIMBOT-v080-GREEN-ATTEMPT-1.md` | `PILOT-ALLIMBOT-v080-GREEN-ATTEMPT-1` | md | record | pass | Allimbot Agent Runtime v0.8 Green Pilot — Attempt 1 |
| `reviews/PILOT-AUTOFOLIO-MIGRATION-v080-GREEN-ATTEMPT-3.md` | `PILOT-AUTOFOLIO-MIGRATION-v080-GREEN-ATTEMPT-3` | md | passed | pass | Autofolio v0.8 Migration Pilot - Green Attempt 3 |
| `reviews/PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-1.md` | `PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-1` | md | failed | red | Autofolio v0.8 Migration Pilot - Red Attempt 1 |
| `reviews/PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-2.md` | `PILOT-AUTOFOLIO-MIGRATION-v080-RED-ATTEMPT-2` | md | failed | red | Autofolio v0.8 Migration Pilot - Red Attempt 2 |
| `reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-1.md` | `PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-1` | md | blocked | fail | Bean Wiki v0.8 Green Replay Attempt 1 |
| `reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-4.md` | `PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-4` | md | blocked | block | Bean Wiki v0.8 Green Pilot Attempt 4 |
| `reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-5.md` | `PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-5` | md | blocked | block | Bean Wiki v0.8 Green Pilot Attempt 5 |
| `reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-6.md` | `PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-6` | md | passed | pass | Bean Wiki v0.8 Green Pilot Attempt 6 |
| `reviews/PILOT-BEAN-WIKI-v080-GREEN.md` | `PILOT-BEAN-WIKI-v080-GREEN` | md | blocked | block | Bean Wiki v0.8 Green Pilot Attempt 3 |
| `reviews/PILOT-BEAN-WIKI-v080.md` | `PILOT-BEAN-WIKI-v080` | md | blocked | fail | Bean Wiki v0.8 Agent Runtime Red Pilot |
| `reviews/PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final.json` | `PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final` | json | record | n/a | PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final |
| `reviews/RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8.json` | `RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8` | json | record | n/a | RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8 |
| `reviews/RELEASE-COUNCIL-GATE-2026-06-13-v0.2.0.json` | `RELEASE-COUNCIL-GATE-2026-06-13-v0.2.0` | json | record | n/a | RELEASE-COUNCIL-GATE-2026-06-13-v0.2.0 |
| `reviews/RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8.json` | `RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8` | json | record | n/a | RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8 |
| `reviews/RELEASE-EXECUTION-GATE-2026-06-13-v0.2.0.json` | `RELEASE-EXECUTION-GATE-2026-06-13-v0.2.0` | json | record | n/a | RELEASE-EXECUTION-GATE-2026-06-13-v0.2.0 |
| `reviews/RELEASE-NOTES-2026-07-23-v0.7.0.md` | `RELEASE-NOTES-2026-07-23-v0.7.0` | md | record | n/a | Agent Runtime v0.7.0 |
| `reviews/RELEASE-READINESS-2026-07-23-v0.7.0-CANDIDATE.md` | `RELEASE-READINESS-2026-07-23-v0.7.0-CANDIDATE` | md | candidate_ready | pass | v0.7.0 Candidate Release Readiness |
| `reviews/RELEASE-READINESS-2026-07-23-v0.7.0-CLOSEOUT.md` | `RELEASE-READINESS-2026-07-23-v0.7.0-CLOSEOUT` | md | pass | n/a | v0.7.0 release closeout readiness |
| `reviews/RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8.json` | `RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8` | json | record | n/a | RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8 |
| `reviews/RELEASE-READINESS-SUMMARY-2026-06-10-task-ar-223-root-current.json` | `RELEASE-READINESS-SUMMARY-2026-06-10-task-ar-223-root-current` | json | record | n/a | RELEASE-READINESS-SUMMARY-2026-06-10-task-ar-223-root-current |
| `reviews/RELEASE-READINESS-SUMMARY-2026-06-13-v0.2.0.json` | `RELEASE-READINESS-SUMMARY-2026-06-13-v0.2.0` | json | record | n/a | RELEASE-READINESS-SUMMARY-2026-06-13-v0.2.0 |
| `reviews/RELEASE-VERSION-CONSISTENCY-STEWARD.json` | `RELEASE-VERSION-CONSISTENCY-STEWARD` | json | record | n/a | RELEASE-VERSION-CONSISTENCY-STEWARD |
| `reviews/REPLAN-2026-06-20-taskset-ar-visual-asset-adoption-task-ar-587-t3.md` | `REPLAN-2026-06-20-taskset-ar-visual-asset-adoption-task-ar-587-t3` | md | record | pass | Visual Asset Adoption T3 Replan for TASK-AR-587 |
| `reviews/REPLAN-2026-06-20-taskset-ar-visual-system-integration-task-ar-591-t3.md` | `REPLAN-2026-06-20-taskset-ar-visual-system-integration-task-ar-591-t3` | md | record | pass | Visual System Integration T3 Replan for TASK-AR-591 |
| `reviews/REPORT-2026-06-17-self-improvement-maturity.md` | `REPORT-2026-06-17-self-improvement-maturity` | md | record | watch | Self Improvement Maturity Report 2026-06-17 |
| `reviews/REPORT-2026-06-17-self-improvement-remediation-delta.md` | `REPORT-2026-06-17-self-improvement-remediation-delta` | md | record | watch | Self Improvement Remediation Delta 2026-06-17 |
| `reviews/REPORT-2026-07-06-self-eval-v0.6.0-baseline-refresh.md` | `REPORT-2026-07-06-self-eval-v0.6.0-baseline-refresh` | md | record | pass | Self-Eval v0.6.0 Baseline Refresh + Host Pipeline Wiring (GH #128) |
| `reviews/RESEARCH-2026-06-09-agent-runtime-official-recommendation-update.md` | `RESEARCH-2026-06-09-agent-runtime-official-recommendation-update` | md | record | n/a | RESEARCH-2026-06-09-agent-runtime-official-recommendation-update.md |
| `reviews/RESEARCH-2026-06-09-agent-runtime-official-runtime-ops-update.md` | `RESEARCH-2026-06-09-agent-runtime-official-runtime-ops-update` | md | record | n/a | RESEARCH-2026-06-09-agent-runtime-official-runtime-ops-update |
| `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-214-official-query-contract.md` | `RESEARCH-2026-06-09-agent-runtime-task-ar-214-official-query-contract` | md | record | n/a | RESEARCH-2026-06-09-agent-runtime-task-ar-214-official-query-contract |
| `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-215-cross-project-overlay.md` | `RESEARCH-2026-06-09-agent-runtime-task-ar-215-cross-project-overlay` | md | record | n/a | RESEARCH-2026-06-09-agent-runtime-task-ar-215-cross-project-overlay |
| `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-218-official-hardening-reference.md` | `RESEARCH-2026-06-09-agent-runtime-task-ar-218-official-hardening-reference` | md | record | n/a | RESEARCH-2026-06-09-agent-runtime-task-ar-218-official-hardening-reference |
| `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-223-217-rehearsal-integration-research.md` | `RESEARCH-2026-06-09-agent-runtime-task-ar-223-217-rehearsal-integration-research` | md | record | n/a | RESEARCH: TASK-AR-223/217 Closeout and Rehearsal Integration |
| `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync.md` | `RESEARCH-2026-06-09-agent-runtime-task-ar-224-official-and-migration-sync` | md | record | n/a | RESEARCH: TASK-AR-224 official + migration sync (2026-06-09) |
| `reviews/RESEARCH-2026-06-09-agent-runtime-task-ar-official-guidance.md` | `RESEARCH-2026-06-09-agent-runtime-task-ar-official-guidance` | md | record | n/a | RESEARCH-2026-06-09-agent-runtime-task-ar-official-guidance |
| `reviews/RESEARCH-2026-06-10-agent-runtime-official-release-governance-research.md` | `RESEARCH-2026-06-10-agent-runtime-official-release-governance-research` | md | record | n/a | RESEARCH (2026-06-10): 공식 가이드 반영 리허설 정합 검토 메모 |
| `reviews/RESEARCH-2026-06-10-agent-runtime-parallel-agents-and-worktrees.md` | `RESEARCH-2026-06-10-agent-runtime-parallel-agents-and-worktrees` | md | record | n/a | Parallel Agents And Worktrees Research |
| `reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md` | `RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research` | md | record | n/a | RSI And Planning Loop Research |
| `reviews/RESEARCH-2026-06-10-continuity-loop-engineering.md` | `RESEARCH-2026-06-10-continuity-loop-engineering` | md | record | n/a | RESEARCH-2026-06-10: Continuity And Loop Engineering |
| `reviews/RESEARCH-2026-06-10-realtime-collab-conflict-patterns.md` | `RESEARCH-2026-06-10-realtime-collab-conflict-patterns` | review | pass | pass | Realtime Collaboration Conflict Pattern Research |
| `reviews/RESEARCH-2026-06-11-agent-runtime-console-platform-feature-research.md` | `RESEARCH-2026-06-11-agent-runtime-console-platform-feature-research` | md | record | n/a | RESEARCH-2026-06-11 — Console Platform Feature Research (시중 플랫폼 전수 분석) |
| `reviews/RESEARCH-2026-06-11-agent-runtime-interactive-gamification-research.md` | `RESEARCH-2026-06-11-agent-runtime-interactive-gamification-research` | md | record | n/a | RESEARCH-2026-06-11 — Interactive/Gamification Console Deep Research |
| `reviews/RESEARCH-2026-06-11-agent-runtime-official-guidance-and-migration-evidence.md` | `RESEARCH-2026-06-11-agent-runtime-official-guidance-and-migration-evidence` | md | record | n/a | RESEARCH-2026-06-11-agent-runtime-official-guidance-and-migration-evidence |
| `reviews/RESEARCH-2026-06-11-agent-runtime-project-management-methods.md` | `RESEARCH-2026-06-11-agent-runtime-project-management-methods` | research | pass | pass | Project Management Methods Research |
| `reviews/RESEARCH-2026-06-11-agent-runtime-ui-design-research.md` | `RESEARCH-2026-06-11-agent-runtime-ui-design-research` | md | accepted | n/a | Agent Runtime UI Research Synthesis |
| `reviews/RESEARCH-2026-06-11-ui-design-implementation-gap.md` | `RESEARCH-2026-06-11-ui-design-implementation-gap` | research | accepted | watch | UI Design Implementation Gap Review |
| `reviews/RESEARCH-2026-06-12-agent-runtime-paperclip-and-doc-to-plan.md` | `RESEARCH-2026-06-12-agent-runtime-paperclip-and-doc-to-plan` | md | record | n/a | RESEARCH-2026-06-12 — Paperclip 분석 및 문서→플랜 파이프라인 기획 |
| `reviews/RESEARCH-2026-06-12-work-hierarchy-taxonomy.md` | `RESEARCH-2026-06-12-work-hierarchy-taxonomy` | research | pass | pass | Work Hierarchy Taxonomy Research |
| `reviews/RESEARCH-2026-06-13-agent-runtime-task-ar-211-official-multi-project-overlay.md` | `RESEARCH-2026-06-13-agent-runtime-task-ar-211-official-multi-project-overlay` | md | record | n/a | RESEARCH-2026-06-13-agent-runtime-task-ar-211-official-multi-project-overlay |
| `reviews/RESEARCH-2026-06-14-agent-org-design-references.md` | `RESEARCH-2026-06-14-agent-org-design-references` | md | record | n/a | RESEARCH — Agent Org Design References (Karpathy · multi-agent architectures · persona diversity) |
| `reviews/RESEARCH-2026-06-14-agent-runtime-task-ar-222-cross-project-overlay-and-governance-research.md` | `RESEARCH-2026-06-14-agent-runtime-task-ar-222-cross-project-overlay-and-governance-research` | md | record | n/a | RESEARCH: TASK-AR-222 closeout을 위한 운영 연구 반영 |
| `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md` | `RESEARCH-2026-06-14-product-maturity-ui-assessment` | research | watch | watch | Product Maturity & UI Assessment — 2026-06-14 |
| `reviews/RESEARCH-2026-06-14-unified-decision-console.md` | `RESEARCH-2026-06-14-unified-decision-console` | research | complete | n/a | Unified Decision/Operations Console — Research Synthesis |
| `reviews/RESEARCH-2026-06-14-work-store-architecture-and-numbering.md` | `RESEARCH-2026-06-14-work-store-architecture-and-numbering` | research | complete | n/a | Work Store Architecture, Archival, Numbering & Performance — Research Synthesis |
| `reviews/RESEARCH-2026-06-15-agent-runtime-task-ar-223-hold-routing-and-overlay-edge-research.md` | `RESEARCH-2026-06-15-agent-runtime-task-ar-223-hold-routing-and-overlay-edge-research` | md | record | n/a | RESEARCH: TASK-AR-223 hold-routing + overlay-edge risk 반영 (2026-06-15) |
| `reviews/RESEARCH-2026-06-18-design-system-governance-role-topology.md` | `RESEARCH-2026-06-18-design-system-governance-role-topology` | md | synthesized (partial verification) | n/a | RESEARCH — Design-System Governance & Design-Org Role Topology |
| `reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md` | `RESEARCH-2026-06-20-ui-ux-visual-resources` | md | synthesized (Strands 1-2 verified; 3-5 from fetched sources + established knowledge) | n/a | RESEARCH — UI/UX Visual Resources (graph · character · fonts · icons · color) |
| `reviews/RESEARCH-2026-06-24-oss-sprite-generators.md` | `RESEARCH-2026-06-24-oss-sprite-generators` | md | synthesized (license + animation facts fetched from primary sources this run; integration sketch is design, not yet spiked) | n/a | RESEARCH — OSS Sprite Generators for Cute, Role-Distinct, Animated Office-Map Characters |
| `reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md` | `RESEARCH-2026-07-28-v080-adoption-enforcement-scope` | md | record | watch | Agent Runtime v0.8 Adoption and Enforcement Scope |
| `reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md` | `RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit` | md | complete | n/a | Agent Runtime 다음 릴리스 하네스 갭 정밀 감사 |
| `reviews/RETRO-2026-06-10-agent-runtime-governance-ops.md` | `RETRO-2026-06-10-agent-runtime-governance-ops` | retro | watch | watch | RETRO-2026-06-10 agent runtime governance ops |
| `reviews/RETRO-2026-06-14-agent-runtime-process-integrity.md` | `RETRO-2026-06-14-agent-runtime-process-integrity` | retro | watch | watch | RETRO 2026-06-14 — Process Integrity (verification / merge / compound-review-retro) |
| `reviews/RETRO-2026-06-14-knowledge-stack.md` | `RETRO-2026-06-14-knowledge-stack` | retro | watch | watch | RETRO 2026-06-14 — Agent knowledge stack (#1–#4) |
| `reviews/RETRO-2026-06-17-self-improvement-cycle.md` | `RETRO-2026-06-17-self-improvement-cycle` | retro | record | n/a | RETRO 2026-06-17 - Self Improvement Cycle |
| `reviews/RETRO-2026-06-21-business-operating-system.md` | `RETRO-2026-06-21-business-operating-system` | retro | recorded | pass | Business Operating System Retro |
| `reviews/RETRO-2026-07-23-july-upstream-intake-closeout.md` | `RETRO-2026-07-23-july-upstream-intake-closeout` | md | complete | n/a | July upstream intake closeout and v0.7.0 release retro |
| `reviews/RETRO-2026-07-23-taskset-ar-work-cli-integrity.md` | `RETRO-2026-07-23-taskset-ar-work-cli-integrity` | md | complete | n/a | TASKSET-AR-WORK-CLI-INTEGRITY Retrospective |
| `reviews/RETRO-2026-07-23-taskset-ar-work-verify-windows-shell-integrity.md` | `RETRO-2026-07-23-taskset-ar-work-verify-windows-shell-integrity` | md | complete | n/a | TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY Retrospective |
| `reviews/RETRO-2026-07-24-work-frontmatter-scalar-integrity.md` | `RETRO-2026-07-24-work-frontmatter-scalar-integrity` | md | completed | pass | Work Frontmatter Scalar Integrity Retrospective |
| `reviews/RETRO-2026-07-29-task-ar-645-compound-scribe.md` | `RETRO-2026-07-29-task-ar-645-compound-scribe` | md | completed | pass | TASK-AR-645 Compound and Scribe Retrospective |
| `reviews/RETRO-2026-07-29-task-ar-646-model-routing.md` | `RETRO-2026-07-29-task-ar-646-model-routing` | md | completed | pass-with-followup | TASK-AR-646 Model-Routing Retrospective |
| `reviews/RETRO-2026-07-29-task-ar-647-native-events-security-boundary.md` | `RETRO-2026-07-29-task-ar-647-native-events-security-boundary` | md | completed | pass-with-compound | TASK-AR-647 Native-Events and Security-Boundary Retrospective |
| `reviews/REVIEW-2026-06-08-agent-runtime-after-pass-1.md` | `REVIEW-2026-06-08-agent-runtime-after-pass-1` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-after-pass-1 |
| `reviews/REVIEW-2026-06-08-agent-runtime-baseline.md` | `REVIEW-2026-06-08-agent-runtime-baseline` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-baseline |
| `reviews/REVIEW-2026-06-08-agent-runtime-claim-backup-validity-comparison-pass-25.md` | `REVIEW-2026-06-08-agent-runtime-claim-backup-validity-comparison-pass-25` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-claim-backup-validity-comparison-pass-25 |
| `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-comparison-record.md` | `REVIEW-2026-06-08-agent-runtime-critic-feedback-comparison-record` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-critic-feedback-comparison-record |
| `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-final-comparison-pass-26.md` | `REVIEW-2026-06-08-agent-runtime-critic-feedback-final-comparison-pass-26` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-critic-feedback-final-comparison-pass-26 |
| `reviews/REVIEW-2026-06-08-agent-runtime-critic-feedback-post-pass-27-recompare.md` | `REVIEW-2026-06-08-agent-runtime-critic-feedback-post-pass-27-recompare` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-critic-feedback-post-pass-27-recompare |
| `reviews/REVIEW-2026-06-08-agent-runtime-post-pass-2.md` | `REVIEW-2026-06-08-agent-runtime-post-pass-2` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-post-pass-2 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-10.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-10` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-10 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-11.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-11` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-11 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-12.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-12` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-12 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-13.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-13` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-13 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-14.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-14` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-14 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-15.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-15` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-15 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-16.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-16` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-16 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-17.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-17` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-17 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-18.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-18` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-18 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-19-critic-feedback-archive.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-19-critic-feedback-archive` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-19-critic-feedback-archive |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2.5.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2.5` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2.5 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-2 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-20-critic-feedback-retrospective.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-20-critic-feedback-retrospective` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-20-critic-feedback-retrospective |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-21-critic-feedback-comparison.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-21-critic-feedback-comparison` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-21-critic-feedback-comparison |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-22-critic-feedback-continuation.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-22-critic-feedback-continuation` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-22-critic-feedback-continuation |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-23-command-sandbox-review.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-23-command-sandbox-review` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-23-command-sandbox-review |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-24-critic-feedback-full-comparison.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-24-critic-feedback-full-comparison` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-24-critic-feedback-full-comparison |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-27-review-cycle.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-27-review-cycle` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-27-review-cycle |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-3.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-3` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-3 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-4.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-4` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-4 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-5.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-5` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-5 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-6.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-6` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-6 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-7.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-7` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-7 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-8.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-8` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-8 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9 |
| `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9b-critique-alignment.md` | `REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9b-critique-alignment` | md | record | n/a | REVIEW-2026-06-08-agent-runtime-recompare-after-pass-9b-critique-alignment |
| `reviews/REVIEW-2026-06-09-agent-runtime-agentic-cycle-001.md` | `REVIEW-2026-06-09-agent-runtime-agentic-cycle-001` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-agentic-cycle-001 |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-100.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-100` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-100.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-101.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-101` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-101.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-102.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-102` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-102.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-103.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-103` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-103.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-104.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-104` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-104.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-105.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-105` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-105.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-106.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-106` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-106.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-107.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-107` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-107.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-108.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-108` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-108.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-109.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-109` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-109.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-110.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-110` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-110.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-111.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-111` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-111.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-112.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-112` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-112.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-113.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-113` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-113.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-114.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-114` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-114.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-28.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-28` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-28 |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-29.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-29` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-29 |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-30.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-30` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-30 |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-31.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-31` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-31.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-32.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-32` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-32 |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-33.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-33` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-33.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-34.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-34` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-34.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-35.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-35` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-35.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-36.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-36` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-36.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-37.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-37` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-37.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-38.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-38` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-38.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-39.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-39` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-39.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-40.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-40` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-40.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-41.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-41` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-41.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-42.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-42` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-42.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-43.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-43` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-43.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-44.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-44` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-44.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-45.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-45` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-45.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-46.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-46` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-46.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-47.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-47` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-47.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-48.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-48` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-48.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-49.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-49` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-49.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-50.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-50` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-50.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-51.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-51` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-51.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-52.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-52` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-52.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-53.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-53` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-53.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-54.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-54` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-54.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-55.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-55` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-55.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-56.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-56` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-56.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-57.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-57` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-57.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-58.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-58` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-58.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-59.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-59` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-59.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-60.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-60` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-60.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-61.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-61` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-61.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-62.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-62` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-62.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-63.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-63` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-63.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-64.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-64` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-64.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-65.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-65` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-65.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-66.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-66` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-66.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-67.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-67` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-67.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-68.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-68` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-68.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-69.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-69` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-69.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-70.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-70` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-70.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-71.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-71` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-71.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-72.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-72` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-72.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-73.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-73` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-73.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-74.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-74` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-74.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-75.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-75` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-75.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-76.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-76` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-76.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-77.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-77` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-77.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-78.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-78` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-78.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-79.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-79` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-79.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-80.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-80` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-80.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-81.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-81` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-81.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-82.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-82` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-82.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-83.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-83` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-83.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-84.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-84` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-84.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-85.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-85` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-85.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-86.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-86` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-86.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-87.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-87` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-87.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-88.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-88` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-88.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-89.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-89` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-89.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-90.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-90` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-90.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-91.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-91` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-91.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-92.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-92` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-92.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-93.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-93` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-93.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-94.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-94` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-94.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-95.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-95` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-95.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-96.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-96` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-96.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-97.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-97` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-97.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-98.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-98` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-98.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-99.md` | `REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-99` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-critic-feedback-recompare-pass-99.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-project-context-overlay.md` | `REVIEW-2026-06-09-agent-runtime-project-context-overlay` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-project-context-overlay.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-recompare-post-pass-114-release-preflight-final.md` | `REVIEW-2026-06-09-agent-runtime-recompare-post-pass-114-release-preflight-final` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-recompare-post-pass-114-release-preflight-final.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox.md` | `REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-recompare-post-pass-28-advanced-command-sandbox |
| `reviews/REVIEW-2026-06-09-agent-runtime-release-preflight-source-dot-recheck.md` | `REVIEW-2026-06-09-agent-runtime-release-preflight-source-dot-recheck` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-release-preflight-source-dot-recheck.md |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-204-co-location-gate-closure.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-204-co-location-gate-closure` | md | record | n/a | REVIEW: TASK-AR-204 Co-Location Gate Closure |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-goldset-expansion-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-205-goldset-expansion-log` | md | record | n/a | REVIEW: TASK-AR-205 Goldset Expansion Log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-offline-eval-gate-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-205-offline-eval-gate-log` | md | record | n/a | REVIEW: TASK-AR-205 Offline Eval Gate Log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-205-prediction-scoring-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-205-prediction-scoring-log` | md | record | n/a | REVIEW: TASK-AR-205 Prediction Scoring Log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-206-live-reviewer-gate-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-206-live-reviewer-gate-log` | md | record | n/a | REVIEW: TASK-AR-206 Live Reviewer Gate Log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-207-correction-collector-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-207-correction-collector-log` | md | record | n/a | REVIEW: TASK-AR-207 Correction Collector Log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-208-a2a-trace-gate-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-208-a2a-trace-gate-log` | md | record | n/a | REVIEW: TASK-AR-208 A2A Trace Gate Log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-210-ready-redecision.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-210-ready-redecision` | md | record | n/a | REVIEW: TASK-AR-210 Ready Re-Decision |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-210-release-state-translation.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-210-release-state-translation` | md | record | n/a | REVIEW: TASK-AR-210 Release-State Translation |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-closure.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-215-overlay-simulation-closure` | md | record | n/a | REVIEW: TASK-AR-215 Cross-Project Overlay Simulation Closure |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-rehearsal-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-217-rehearsal-log` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-task-ar-217-rehearsal-log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-plan |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-runbook.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-runbook` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-task-ar-217-release-rehearsal-runbook |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-log` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-plan.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-218-migration-hardening-plan` | md | record | n/a | REVIEW-2026-06-09-agent-runtime-task-AR-218-migration-hardening-plan |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-220-migration-approval-closure.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-220-migration-approval-closure` | md | record | n/a | REVIEW: TASK-AR-220 Migration Approval Closure |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-221-operating-chain-integration` | md | record | n/a | REVIEW: TASK-AR-221 Operating Chain Integration |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-222-v018-closeout-bundle.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-222-v018-closeout-bundle` | md | record | n/a | REVIEW: TASK-AR-222 v0.1.8 Closeout Bundle |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-223-217-closeout-rehearsal-log` | md | record | n/a | REVIEW: TASK-AR-223/217 Closeout Rehearsal Log |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-223-closeout-bundle-consolidation` | md | record | n/a | REVIEW: TASK-AR-223 Closeout Bundle Consolidation |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-224-executable-proof` | md | record | n/a | REVIEW (2026-06-09) - TASK-AR-224 executable overlay packet + preflight proof |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-224-overlay-and-gate-check` | md | record | n/a | REVIEW (2026-06-09) - TASK-AR-224 overlay-only + gate template check |
| `reviews/REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log.md` | `REVIEW-2026-06-09-agent-runtime-task-ar-225-source-publication-hygiene-log` | md | record | n/a | REVIEW: TASK-AR-225 Source Publication Hygiene |
| `reviews/REVIEW-2026-06-09-agent-runtime-v016-agentic-knowledge-plan.md` | `REVIEW-2026-06-09-agent-runtime-v016-agentic-knowledge-plan` | md | record | n/a | REVIEW-2026-06-09 agent_runtime v0.1.6 agentic knowledge plan |
| `reviews/REVIEW-2026-06-09-agent-runtime-v018-automation-policy-release.md` | `RELEASE-2026-06-09-v0.1.8` | release | G | n/a | REVIEW-2026-06-09-agent-runtime-v018-automation-policy-release |
| `reviews/REVIEW-2026-06-09-agent-runtime-v018-local-smoke-plan-readiness.md` | `REVIEW-2026-06-09-agent-runtime-v018-local-smoke-plan-readiness` | md | record | n/a | REVIEW: v0.1.8 Local Smoke Plan Readiness |
| `reviews/REVIEW-2026-06-09-agent-runtime-v018-owner-approval-gate.md` | `REVIEW-2026-06-09-agent-runtime-v018-owner-approval-gate` | md | record | n/a | REVIEW: v0.1.8 Owner Approval Gate |
| `reviews/REVIEW-2026-06-09-agent-runtime-v018-pending-release-guard.md` | `REVIEW-2026-06-09-agent-runtime-v018-pending-release-guard` | md | record | n/a | REVIEW: v0.1.8 Pending Release Guard |
| `reviews/REVIEW-2026-06-09-agent-runtime-v018-release-execution-boundary.md` | `REVIEW-2026-06-09-agent-runtime-v018-release-execution-boundary` | md | record | n/a | REVIEW: v0.1.8 Release Execution Boundary |
| `reviews/REVIEW-2026-06-09-agent-runtime-v018-release-readiness-summary.md` | `REVIEW-2026-06-09-agent-runtime-v018-release-readiness-summary` | md | record | n/a | REVIEW: v0.1.8 Release Readiness Summary |
| `reviews/REVIEW-2026-06-09-backlog-board-restoration-owner-format-gate.md` | `REVIEW-2026-06-09-backlog-board-restoration-owner-format-gate` | review | completed | pass | Backlog Board Restoration and Owner Format Gate |
| `reviews/REVIEW-2026-06-09-backlog-brief-format-drift-compound.md` | `REVIEW-2026-06-09-backlog-brief-format-drift-compound` | review | Y | n/a | REVIEW: Backlog BRIEF Format Drift Recurrence |
| `reviews/REVIEW-2026-06-10-agent-runtime-collaboration-governance-redesign.md` | `REVIEW-2026-06-10-agent-runtime-collaboration-governance-redesign` | md | record | n/a | REVIEW-2026-06-10 agent runtime collaboration governance redesign |
| `reviews/REVIEW-2026-06-10-agent-runtime-pane-progress-taskset.md` | `REVIEW-2026-06-10-agent-runtime-pane-progress-taskset` | md | pass | pass | Pane Progress Task Set Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-parallel-collaboration-audit.md` | `REVIEW-2026-06-10-agent-runtime-parallel-collaboration-audit` | review | watch | n/a | Parallel Collaboration Audit - 2026-06-10 |
| `reviews/REVIEW-2026-06-10-agent-runtime-parallel-session-protocol.md` | `REVIEW-2026-06-10-agent-runtime-parallel-session-protocol` | review | pass | pass | Parallel Session Protocol Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-release-steward-claim-normalization.md` | `REVIEW-2026-06-10-agent-runtime-release-steward-claim-normalization` | review | pass | pass | REVIEW: Release Steward Claim Normalization |
| `reviews/REVIEW-2026-06-10-agent-runtime-release-steward-taskset-closeout.md` | `REVIEW-2026-06-10-agent-runtime-release-steward-taskset-closeout` | review | pass | pass | REVIEW: Release Steward Taskset Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation.md` | `REVIEW-2026-06-10-agent-runtime-rsi-planning-loop-implementation` | md | draft | n/a | RSI Planning Loop Implementation Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-rsi-planning-registration.md` | `REVIEW-2026-06-10-agent-runtime-rsi-planning-registration` | review | pass | pass | RSI Planning Registration Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-206-claim-closeout.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-206-claim-closeout` | md | record | n/a | REVIEW: TASK-AR-206 Claim Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-207-claim-closeout.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-207-claim-closeout` | md | record | n/a | REVIEW: TASK-AR-207 Claim Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-208-claim-closeout.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-208-claim-closeout` | md | record | n/a | REVIEW: TASK-AR-208 Claim Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-210-completion-audit.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-210-completion-audit` | review | watch | watch | REVIEW: TASK-AR-210 Completion Audit |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-210-release-steward-snapshot.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-210-release-steward-snapshot` | review | pass | pass | REVIEW: TASK-AR-210 Release Steward Snapshot |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-210-remote-publish-boundary.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-210-remote-publish-boundary` | review | pass | pass | REVIEW: TASK-AR-210 Remote Publish Boundary |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-210-remote-publish-deferral.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-210-remote-publish-deferral` | review | pass | pass | REVIEW: TASK-AR-210 Remote Publish Deferral |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-216-already-complete-claim-release.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-216-already-complete-claim-release` | review | pass | pass | REVIEW: TASK-AR-216 Already-Complete Claim Release |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-216-duplicate-claim-release.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-216-duplicate-claim-release` | review | pass | pass | REVIEW: TASK-AR-216 Duplicate Claim Release |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-219-claim-closeout.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-219-claim-closeout` | review | pass | pass | REVIEW: TASK-AR-219 Claim Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-219-current-state-marker-hardening.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-219-current-state-marker-hardening` | review | pass | pass | REVIEW: TASK-AR-219 Current-State Marker Hardening |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-219-gate-pass-handoff.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-219-gate-pass-handoff` | review | pass | pass | REVIEW: TASK-AR-219 Gate Pass Handoff |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-219-handoff-readiness.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-219-handoff-readiness` | review | watch | watch | REVIEW: TASK-AR-219 Handoff Readiness |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-219-schedule-consistency-report.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-219-schedule-consistency-report` | review | watch | watch | REVIEW: TASK-AR-219 Schedule Consistency Report |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-221-quality-loop-closeout.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-221-quality-loop-closeout` | md | record | n/a | REVIEW: TASK-AR-221 Quality Loop Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-222-bundle-index.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-222-bundle-index` | review | watch | watch | REVIEW: TASK-AR-222 Bundle Index |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-222-claim-closeout.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-222-claim-closeout` | review | pass | pass | REVIEW: TASK-AR-222 Claim Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-222-closeout-evidence-map.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-222-closeout-evidence-map` | review | watch | watch | REVIEW: TASK-AR-222 Closeout Evidence Map |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-222-source-output-coverage.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-222-source-output-coverage` | review | pass | pass | REVIEW: TASK-AR-222 Source Output Coverage |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-222-start-checkpoint.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-222-start-checkpoint` | review | watch | watch | REVIEW: TASK-AR-222 Start Checkpoint |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-222-watch-lane-disposition.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-222-watch-lane-disposition` | review | watch | watch | REVIEW: TASK-AR-222 Watch Lane Disposition |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-223-final-handoff.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-223-final-handoff` | review | pass | pass | REVIEW: TASK-AR-223 Final Handoff |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-223-release-state-bridge.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-223-release-state-bridge` | review | pass | pass | REVIEW: TASK-AR-223 Release-State Bridge |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-223-release-steward-integration-checkpoint.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-223-release-steward-integration-checkpoint` | md | record | n/a | REVIEW: TASK-AR-223 Release Steward Integration Checkpoint |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-223-root-integration-closeout.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-223-root-integration-closeout` | md | record | n/a | REVIEW: TASK-AR-223 Root Integration Closeout |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-223-source-output-coverage.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-223-source-output-coverage` | review | pass | pass | REVIEW: TASK-AR-223 Source Output Coverage |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-226-data-map.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-226-data-map` | review | pass | pass | TASK-AR-226 UI Runtime Data Map Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-227-ui-state-api.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-227-ui-state-api` | review | record | pass | TASK-AR-227 UI State API Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-228-ui-console-mvp.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-228-ui-console-mvp` | review | record | pass | TASK-AR-228 UI Console MVP Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-229-write-commands.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-229-write-commands` | review | record | pass | TASK-AR-229 UI Write Commands Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-230-runtime-commands.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-230-runtime-commands` | review | pass | pass | TASK-AR-230 Runtime Command Controls Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-231-live-observability.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-231-live-observability` | review | pass | pass | TASK-AR-231 Live Observability Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-232-map-views.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-232-map-views` | review | pass | pass | TASK-AR-232 Map Views Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-task-ar-243-planning-evidence-link.md` | `REVIEW-2026-06-10-agent-runtime-task-ar-243-planning-evidence-link` | md | record | n/a | REVIEW: TASK-AR-243 Planning Evidence Link |
| `reviews/REVIEW-2026-06-10-agent-runtime-taskset-dispatcher.md` | `REVIEW-2026-06-10-agent-runtime-taskset-dispatcher` | review | pass | pass | Task Set Dispatcher Review |
| `reviews/REVIEW-2026-06-10-agent-runtime-worktree-cleanup-cycle-map.md` | `REVIEW-2026-06-10-agent-runtime-worktree-cleanup-cycle-map` | review | pass | pass | Worktree Cleanup and Backlog Cycle Map |
| `reviews/REVIEW-2026-06-10-task-ar-201-context-router.md` | `REVIEW-2026-06-10-task-ar-201-context-router` | md | record | n/a | REVIEW-2026-06-10-task-ar-201-context-router.md |
| `reviews/REVIEW-2026-06-11-agent-runtime-branch-cleanup-sha-manifest.md` | `REVIEW-2026-06-11-agent-runtime-branch-cleanup-sha-manifest` | md | record | n/a | REVIEW-2026-06-11 — Branch Cleanup SHA Manifest |
| `reviews/REVIEW-2026-06-11-agent-runtime-context-knowledge-taskset-closeout.md` | `REVIEW-2026-06-11-agent-runtime-context-knowledge-taskset-closeout` | taskset_closeout_review | pass | pass | Context Knowledge Taskset Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-ops-feedback-analysis-session.md` | `REVIEW-2026-06-11-agent-runtime-ops-feedback-analysis-session` | md | record | n/a | REVIEW-2026-06-11 — Ops Feedback / Plan / Analysis Session Record |
| `reviews/REVIEW-2026-06-11-agent-runtime-pm-operating-system-registration.md` | `REVIEW-2026-06-11-agent-runtime-pm-operating-system-registration` | review | pass | pass | PM Operating System Registration Review |
| `reviews/REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration.md` | `REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration` | review | pass | pass | RSI Operating System Registration Review |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-278-console-shell.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-278-console-shell` | review | pass | pass | TASK-AR-278 Console Shell Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-279-backlog-hierarchy.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-279-backlog-hierarchy` | review | pass | pass | TASK-AR-279 Backlog Hierarchy Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-280-agent-command-panes.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-280-agent-command-panes` | review | pass | pass | TASK-AR-280 Agent And Command Pane Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-281-evidence-event-panes.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-281-evidence-event-panes` | review | pass | pass | TASK-AR-281 Evidence And Event Pane Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-282-map-planner-source-write-panes.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-282-map-planner-source-write-panes` | review | pass | pass | TASK-AR-282 Map Planner Source Write Pane Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-283-responsive-accessibility-polish.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-283-responsive-accessibility-polish` | review | pass | pass | TASK-AR-283 Responsive Accessibility Polish Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-297-evidence-inbox-contract.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-297-evidence-inbox-contract` | review | pass | pass | TASK-AR-297 Evidence Inbox Contract Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-ar-298-eval-verification-registry.md` | `REVIEW-2026-06-11-agent-runtime-task-ar-298-eval-verification-registry` | review | pass | pass | TASK-AR-298 Evaluation Verification Registry Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-task-identity-taskset-closeout.md` | `REVIEW-2026-06-11-agent-runtime-task-identity-taskset-closeout` | taskset_closeout_review | pass | pass | Task Identity Taskset Closeout |
| `reviews/REVIEW-2026-06-11-agent-runtime-ui-design-implementation-final-handoff.md` | `REVIEW-2026-06-11-agent-runtime-ui-design-implementation-final-handoff` | review | pass | pass | UI Design Implementation Final Handoff |
| `reviews/REVIEW-2026-06-11-agent-runtime-ui-design-taskset-closeout.md` | `REVIEW-2026-06-11-agent-runtime-ui-design-taskset-closeout` | taskset_closeout_review | pass | pass | Agent Runtime UI Design Taskset Closeout |
| `reviews/REVIEW-2026-06-11-current-session-final-closeout.md` | `REVIEW-2026-06-11-current-session-final-closeout` | review | pass | pass | Current Session Final Closeout |
| `reviews/REVIEW-2026-06-11-multipane-runtime-assurance-closeout.md` | `REVIEW-2026-06-11-multipane-runtime-assurance-closeout` | taskset_closeout_review | pass | pass | Multi-Pane Runtime Assurance Closeout |
| `reviews/REVIEW-2026-06-11-multipane-runtime-assurance-registration.md` | `REVIEW-2026-06-11-multipane-runtime-assurance-registration` | review | watch | watch | Multi-Pane Runtime Assurance Registration |
| `reviews/REVIEW-2026-06-11-session-closeout-automation-closeout.md` | `REVIEW-2026-06-11-session-closeout-automation-closeout` | taskset_closeout_review | pass | pass | Session Closeout Automation Closeout |
| `reviews/REVIEW-2026-06-11-session-closeout-automation-registration.md` | `REVIEW-2026-06-11-session-closeout-automation-registration` | review | pass | pass | Session Closeout Automation Registration |
| `reviews/REVIEW-2026-06-11-tag-manual-independence-closeout.md` | `REVIEW-2026-06-11-tag-manual-independence-closeout` | brief | record | pass | REVIEW-2026-06-11-tag-manual-independence-closeout |
| `reviews/REVIEW-2026-06-11-toolrunner-policy-closeout.md` | `REVIEW-2026-06-11-toolrunner-policy-closeout` | brief | record | pass | REVIEW-2026-06-11-toolrunner-policy-closeout |
| `reviews/REVIEW-2026-06-12-a2a-message-routing-closeout.md` | `REVIEW-2026-06-12-a2a-message-routing-closeout` | md | record | n/a | REVIEW: TASK-AR-311 A2A Message Routing Closeout |
| `reviews/REVIEW-2026-06-12-agent-runtime-live-structure-two-layer-decision.md` | `REVIEW-2026-06-12-agent-runtime-live-structure-two-layer-decision` | review | pass | pass | Live Structure Two-Layer Decision Review |
| `reviews/REVIEW-2026-06-12-agent-runtime-ops-feedback-analysis-closeout.md` | `REVIEW-2026-06-12-agent-runtime-ops-feedback-analysis-closeout` | review | pass | pass | Ops Feedback Analysis Closeout Review |
| `reviews/REVIEW-2026-06-12-agent-runtime-parallel-wave-scheduling-design.md` | `REVIEW-2026-06-12-agent-runtime-parallel-wave-scheduling-design` | review | pass | pass | Parallel Wave Scheduling Design Review |
| `reviews/REVIEW-2026-06-12-agent-runtime-pm-operating-system-closeout.md` | `REVIEW-2026-06-12-agent-runtime-pm-operating-system-closeout` | review | pass | pass | PM Operating System Closeout Review |
| `reviews/REVIEW-2026-06-12-agent-runtime-release-plan-v019-v020.md` | `REVIEW-2026-06-12-agent-runtime-release-plan-v019-v020` | review | pass | pass | Release Plan v0.1.9 / v0.2.0 Review |
| `reviews/REVIEW-2026-06-12-agent-runtime-rsi-operating-system-closeout.md` | `REVIEW-2026-06-12-agent-runtime-rsi-operating-system-closeout` | review | pass | pass | RSI Operating System Closeout Review |
| `reviews/REVIEW-2026-06-12-agent-runtime-task-ar-210-release-gate.md` | `REVIEW-2026-06-12-agent-runtime-task-ar-210-release-gate` | md | record | n/a | REVIEW-2026-06-12-agent-runtime-task-ar-210-release-gate |
| `reviews/REVIEW-2026-06-12-agent-runtime-vision-gap-closure-closeout.md` | `REVIEW-2026-06-12-agent-runtime-vision-gap-closure-closeout` | review | pass | pass | Vision Gap Closure Closeout Review |
| `reviews/REVIEW-2026-06-12-claim-lease-closeout.md` | `REVIEW-2026-06-12-claim-lease-closeout` | brief | record | pass | REVIEW-2026-06-12-claim-lease-closeout |
| `reviews/REVIEW-2026-06-12-rbac-write-gate-closeout.md` | `REVIEW-2026-06-12-rbac-write-gate-closeout` | md | record | n/a | REVIEW: TASK-AR-312 RBAC Write Gate Closeout |
| `reviews/REVIEW-2026-06-12-taskset-ar-agent-identity-contract-registration.md` | `REVIEW-2026-06-12-taskset-ar-agent-identity-contract-registration` | md | record | pass | Agent Identity Contract Registration |
| `reviews/REVIEW-2026-06-12-work-assign-command.md` | `REVIEW-2026-06-12-work-assign-command` | md | record | pass | Work Assign Command |
| `reviews/REVIEW-2026-06-12-work-close-command.md` | `REVIEW-2026-06-12-work-close-command` | md | record | pass | Work Close Command |
| `reviews/REVIEW-2026-06-12-work-criteria-command.md` | `REVIEW-2026-06-12-work-criteria-command` | md | record | pass | Work Criteria Command |
| `reviews/REVIEW-2026-06-12-work-hierarchy-conflict-closure-registration.md` | `REVIEW-2026-06-12-work-hierarchy-conflict-closure-registration` | review | pass | pass | Work Hierarchy Conflict Closure Registration Review |
| `reviews/REVIEW-2026-06-12-work-now-timestamp-source.md` | `REVIEW-2026-06-12-work-now-timestamp-source` | md | record | pass | Work Now Timestamp Source Closeout |
| `reviews/REVIEW-2026-06-12-work-registration-cli.md` | `REVIEW-2026-06-12-work-registration-cli` | md | record | pass | Work Registration CLI Closeout |
| `reviews/REVIEW-2026-06-12-work-registration-unit-scaffold.md` | `REVIEW-2026-06-12-work-registration-unit-scaffold` | md | record | pass | Work Registration Unit Scaffold Closeout |
| `reviews/REVIEW-2026-06-12-work-schema-ssot-gate.md` | `REVIEW-2026-06-12-work-schema-ssot-gate` | md | record | pass | Work Schema SSoT Gate Closeout |
| `reviews/REVIEW-2026-06-12-work-split-command.md` | `REVIEW-2026-06-12-work-split-command` | md | record | pass | Work Split Command |
| `reviews/REVIEW-2026-06-12-work-stats-command.md` | `REVIEW-2026-06-12-work-stats-command` | md | record | pass | Work Stats Command |
| `reviews/REVIEW-2026-06-12-work-verify-command.md` | `REVIEW-2026-06-12-work-verify-command` | md | record | pass | Work Verify Command Closeout |
| `reviews/REVIEW-2026-06-13-agent-runtime-task-ar-211-overlay-bundle-review.md` | `REVIEW-2026-06-13-agent-runtime-task-ar-211-overlay-bundle-review` | md | record | n/a | REVIEW-2026-06-13-agent-runtime-task-ar-211-overlay-bundle-review |
| `reviews/REVIEW-2026-06-13-agent-runtime-task-ar-331-properties-labels-automation-triage.md` | `REVIEW-2026-06-13-agent-runtime-task-ar-331-properties-labels-automation-triage` | review | record | pass | TASK-AR-331 Custom Properties / Labels / Automation Rules / Triage Review |
| `reviews/REVIEW-2026-06-13-dependency-model-timeline-graph.md` | `REVIEW-2026-06-13-dependency-model-timeline-graph` | md | record | n/a | REVIEW-2026-06-13 subtask + dependency model, timeline, dependency graph (TASK-AR-330) |
| `reviews/REVIEW-2026-06-13-parallel-wave-1-2-closeout.md` | `REVIEW-2026-06-13-parallel-wave-1-2-closeout` | review | pass | pass | Parallel Wave 1-2 Closeout (AR-500/503/505/509/510/513/515) |
| `reviews/REVIEW-2026-06-13-parallel-wave-500-series-capability-analysis.md` | `REVIEW-2026-06-13-parallel-wave-500-series-capability-analysis` | review | pass | pass | 500-Series Capability Analysis — Implemented, Applied, Verified |
| `reviews/REVIEW-2026-06-13-parallel-wave-500-series-final-closeout.md` | `REVIEW-2026-06-13-parallel-wave-500-series-final-closeout` | review | pass | pass | 500-Series Parallel Execution — Final Closeout |
| `reviews/REVIEW-2026-06-13-taskset-boundary-execution-guard.md` | `REVIEW-2026-06-13-taskset-boundary-execution-guard` | md | record | n/a | REVIEW-2026-06-13 taskset boundary execution guard (TASK-AR-328) |
| `reviews/REVIEW-2026-06-13-v0.2.0-release-readiness.md` | `REVIEW-2026-06-13-v0.2.0-release-readiness` | review | pass | pass | v0.2.0 Release Readiness |
| `reviews/REVIEW-2026-06-14-agent-runtime-task-ar-222-closeout-log.md` | `REVIEW-2026-06-14-agent-runtime-task-ar-222-closeout-log` | md | record | n/a | REVIEW: TASK-AR-222 closeout 실행 로그 |
| `reviews/REVIEW-2026-06-14-deadlock-eval-automation-closeout.md` | `REVIEW-2026-06-14-deadlock-eval-automation-closeout` | review | watch | watch | REVIEW 2026-06-14 — Deadlock guardrails · eval · auto-merge closeout |
| `reviews/REVIEW-2026-06-14-knowledge-stack-closeout.md` | `REVIEW-2026-06-14-knowledge-stack-closeout` | review | watch | watch | REVIEW 2026-06-14 — Agent knowledge stack closeout (#1–#4) |
| `reviews/REVIEW-2026-06-14-knowledge-stack-followups-closeout.md` | `REVIEW-2026-06-14-knowledge-stack-followups-closeout` | review | watch | watch | REVIEW 2026-06-14 — Knowledge-stack follow-ups closeout (A/B/C) |
| `reviews/REVIEW-2026-06-15-doc-to-plan-closeout.md` | `REVIEW-2026-06-15-doc-to-plan-closeout` | md | record | n/a | REVIEW — Doc-to-Plan: Closeout (TASKSET-AR-DOC-TO-PLAN) |
| `reviews/REVIEW-2026-06-15-paperclip-gap-adoption-decision.md` | `REVIEW-2026-06-15-paperclip-gap-adoption-decision` | md | record | n/a | REVIEW — Paperclip Gap Analysis & Adoption Decision (TASK-AR-367) |
| `reviews/REVIEW-2026-06-15-product-maturity-uplift-closeout.md` | `REVIEW-2026-06-15-product-maturity-uplift-closeout` | md | record | n/a | REVIEW — Product Maturity Uplift: Closeout (TASKSET-AR-PRODUCT-MATURITY-UPLIFT) |
| `reviews/REVIEW-2026-06-15-work-hierarchy-conflict-closure-closeout.md` | `REVIEW-2026-06-15-work-hierarchy-conflict-closure-closeout` | md | record | n/a | REVIEW — Work Hierarchy Conflict Closure: Closeout (TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE) |
| `reviews/REVIEW-2026-06-16-task-ar-565-nav-prune-core7.md` | `REVIEW-2026-06-16-task-ar-565-nav-prune-core7` | review | pass | pass | REVIEW - TASK-AR-565 Nav Prune Core 7 |
| `reviews/REVIEW-2026-06-16-task-ar-566-progressive-disclosure.md` | `REVIEW-2026-06-16-task-ar-566-progressive-disclosure` | review | pass | pass | REVIEW - TASK-AR-566 Progressive Disclosure Detail Panel |
| `reviews/REVIEW-2026-06-16-task-ar-567-work-state-board.md` | `REVIEW-2026-06-16-task-ar-567-work-state-board` | md | record | n/a | TASK-AR-567 W4a Review - Work State Board |
| `reviews/REVIEW-2026-06-16-task-ar-568-i18n-toggle.md` | `REVIEW-2026-06-16-task-ar-568-i18n-toggle` | md | record | n/a | TASK-AR-568 W4a Review - i18n KO/EN UI Toggle |
| `reviews/REVIEW-2026-06-16-task-ar-569-e2e-dom-budget.md` | `REVIEW-2026-06-16-task-ar-569-e2e-dom-budget` | md | record | n/a | TASK-AR-569 W4a Review - E2E + DOM Budget Regression |
| `reviews/REVIEW-2026-06-17-decision-first-console-ia-closeout.md` | `REVIEW-2026-06-17-decision-first-console-ia-closeout` | md | record | n/a | REVIEW: Decision-First Console IA Closeout |
| `reviews/REVIEW-2026-06-17-self-improvement-cycle.md` | `REVIEW-2026-06-17-self-improvement-cycle` | md | record | watch | Self Improvement Cycle 2026-06-17 |
| `reviews/REVIEW-2026-06-17-task-ar-573-scribe-evidence.md` | `REVIEW-2026-06-17-task-ar-573-scribe-evidence` | md | record | watch | TASK-AR-573 Scribe Evidence |
| `reviews/REVIEW-2026-06-17-task-ar-574-monitored-role-evidence.md` | `REVIEW-2026-06-17-task-ar-574-monitored-role-evidence` | md | record | watch | TASK-AR-574 Monitored Role Evidence |
| `reviews/REVIEW-2026-06-17-task-ar-575-runtime-asset-lifecycle.md` | `REVIEW-2026-06-17-task-ar-575-runtime-asset-lifecycle` | review | approved | pass | TASK-AR-575 Runtime Asset Lifecycle Review |
| `reviews/REVIEW-2026-06-17-task-ar-577-business-operations-teams.md` | `REVIEW-2026-06-17-task-ar-577-business-operations-teams` | md | record | n/a | TASK-AR-577 W4a Review - Business Operations Teams |
| `reviews/REVIEW-2026-06-17-taskset-ar-business-operations-teams-registration.md` | `REVIEW-2026-06-17-taskset-ar-business-operations-teams-registration` | md | record | pass | Business Operations Teams Registration |
| `reviews/REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-registration.md` | `REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-registration` | md | record | pass | Self Improvement Cadence Registration |
| `reviews/REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-t3-replan-after-cycle.md` | `REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-t3-replan-after-cycle` | md | record | pass | Self Improvement Cadence T3 Replan After Cycle |
| `reviews/REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-t3-replan-after-report.md` | `REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-t3-replan-after-report` | md | record | pass | Self Improvement Cadence T3 Replan After Report |
| `reviews/REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-t3-replan.md` | `REVIEW-2026-06-17-taskset-ar-self-improvement-cadence-t3-replan` | md | record | pass | Self Improvement Cadence T3 Replan |
| `reviews/REVIEW-2026-06-17-taskset-ar-self-improvement-remediation-cycle-registration.md` | `REVIEW-2026-06-17-taskset-ar-self-improvement-remediation-cycle-registration` | md | record | pass | Self Improvement Remediation Registration |
| `reviews/REVIEW-2026-06-18-beta-tester-role-strengthening.md` | `REVIEW-2026-06-18-beta-tester-role-strengthening` | review | pass | pass | Beta Tester Role Strengthening |
| `reviews/REVIEW-2026-06-18-knowledge-graph-corpus-expansion.md` | `REVIEW-2026-06-18-knowledge-graph-corpus-expansion` | md | record | pass | Knowledge Graph Corpus Expansion |
| `reviews/REVIEW-2026-06-18-llm-wiki-preservation-branch-deferred.md` | `REVIEW-2026-06-18-llm-wiki-preservation-branch-deferred` | md | accepted | n/a | LLM-Wiki Preservation Branch Deferred |
| `reviews/REVIEW-2026-06-18-llm-wiki-worktree-preservation-closeout.md` | `REVIEW-2026-06-18-llm-wiki-worktree-preservation-closeout` | review | pass | n/a | LLM-Wiki Worktree Preservation Closeout |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-assetization-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-assetization-registration` | md | record | pass | Design System Assetization Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-component-patterns-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-component-patterns-registration` | md | record | pass | Design System Component Patterns Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-debt-consolidation-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-debt-consolidation-registration` | md | record | pass | Design System Debt Consolidation Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-governance-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-governance-registration` | md | record | pass | Design System Governance Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-served-asset-split-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-served-asset-split-registration` | md | record | pass | Design System Served Asset Split Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-token-debt-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-token-debt-registration` | md | record | pass | Design System Token Debt Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-release-auto-noncritical-registration.md` | `REVIEW-2026-06-18-taskset-ar-release-auto-noncritical-registration` | md | record | pass | Noncritical Release Auto-Execution Registration |
| `reviews/REVIEW-2026-06-20-taskset-ar-visual-asset-adoption-registration.md` | `REVIEW-2026-06-20-taskset-ar-visual-asset-adoption-registration` | md | record | pass | Visual Asset Adoption Registration |
| `reviews/REVIEW-2026-06-20-taskset-ar-visual-system-integration-registration.md` | `REVIEW-2026-06-20-taskset-ar-visual-system-integration-registration` | md | record | pass | Visual System Integration & Verification Registration |
| `reviews/REVIEW-2026-06-21-taskset-ar-business-operating-system-registration.md` | `REVIEW-2026-06-21-taskset-ar-business-operating-system-registration` | md | record | pass | Business Operating System Registration |
| `reviews/REVIEW-2026-06-22-agent-skill-track-consolidation.md` | `REVIEW-2026-06-22-agent-skill-track-consolidation` | review | assessed | pass | Agent/skill track consolidation — what to take to main |
| `reviews/REVIEW-2026-06-22-autofolio-upstream-candidates.md` | `REVIEW-2026-06-22-autofolio-upstream-candidates` | review | assessed | pass | autofolio → agent_runtime upstream-candidate assessment |
| `reviews/REVIEW-2026-06-22-subsystem-verification-audit.md` | `REVIEW-2026-06-22-subsystem-verification-audit` | review | assessed | watch | Subsystem verification audit (2026-06-22) |
| `reviews/REVIEW-2026-06-22-system-health-rsi-diagnosis.md` | `REVIEW-2026-06-22-system-health-rsi-diagnosis` | review | assessed | watch | System-health / RSI diagnosis (2026-06-22) |
| `reviews/REVIEW-2026-07-19-auto-merge-execution-readback.md` | `REVIEW-2026-07-19-AUTO-MERGE-READBACK` | review | approved | n/a | Auto-merge execution read-back design |
| `reviews/REVIEW-2026-07-19-taskset-ar-auto-merge-integrity-registration.md` | `REVIEW-2026-07-19-taskset-ar-auto-merge-integrity-registration` | md | record | pass | Merge Truth Keeper Registration |
| `reviews/REVIEW-2026-07-19-taskset-ar-july-upstream-intake-closeout-registration.md` | `REVIEW-2026-07-19-taskset-ar-july-upstream-intake-closeout-registration` | md | record | pass | Upstream Intake Closer Registration |
| `reviews/REVIEW-2026-07-19-taskset-ar-role-routing-closeout-reliability-registration.md` | `REVIEW-2026-07-19-taskset-ar-role-routing-closeout-reliability-registration` | md | record | pass | Role Routing Closeout Reliability Registration |
| `reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md` | `REVIEW-2026-07-22-decision-console-overhaul-masterplan` | md | record | pass | Decision Console Overhaul Masterplan |
| `reviews/REVIEW-2026-07-22-post-merge-plan-revalidation.md` | `REVIEW-2026-07-22-post-merge-plan-revalidation` | plan-revalidation | approved | pass | Post-merge plan revalidation |
| `reviews/REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery.md` | `REVIEW-2026-07-22-pr-303-ci-baseline-schema-recovery` | md | record | pass | PR 303 CI baseline schema recovery |
| `reviews/REVIEW-2026-07-22-release-impact-issues-291-300-audit.md` | `REVIEW-2026-07-22-release-impact-issues-291-300-audit` | planning | record | action | Release-impact issue audit for #291 through #300 |
| `reviews/REVIEW-2026-07-22-release-impact-verification-command-correction.md` | `REVIEW-2026-07-22-release-impact-verification-command-correction` | planning | record | pass | Release-impact verification command correction |
| `reviews/REVIEW-2026-07-22-remote-main-integration-id-collision.md` | `REVIEW-2026-07-22-remote-main-integration-id-collision` | integration-decision | approved | pass | Remote main integration and TASK-AR-600 collision |
| `reviews/REVIEW-2026-07-22-task-ar-599-packaging-scope-amendment.md` | `REVIEW-2026-07-22-task-ar-599-packaging-scope-amendment` | md | record | pass | TASK-AR-599 packaging scope amendment |
| `reviews/REVIEW-2026-07-22-task-ar-600-host-lock-scope-amendment.md` | `REVIEW-2026-07-22-task-ar-600-host-lock-scope-amendment` | planning | record | pass | TASK-AR-600 host lock scope amendment |
| `reviews/REVIEW-2026-07-22-task-ar-600-scope-transition-approval.md` | `REVIEW-2026-07-22-task-ar-600-scope-transition-approval` | planning | record | pass | TASK-AR-600 taskset scope transition approval |
| `reviews/REVIEW-2026-07-22-task-ar-600-verification-frontmatter-amendment.md` | `REVIEW-2026-07-22-task-ar-600-verification-frontmatter-amendment` | planning | record | pass | TASK-AR-600 verification frontmatter amendment |
| `reviews/REVIEW-2026-07-22-task-ar-603-unicode-boundary-t3-replan.md` | `REVIEW-2026-07-22-task-ar-603-unicode-boundary-t3-replan` | md | record | pass | TASK-AR-603 Unicode Token Boundary T3 Replan |
| `reviews/REVIEW-2026-07-22-task-ar-604-integration-t3-replan.md` | `REVIEW-2026-07-22-task-ar-604-integration-t3-replan` | md | record | pass | TASK-AR-604 Integration T3 Replan |
| `reviews/REVIEW-2026-07-22-task-ar-605-dispatch-t3-replan.md` | `REVIEW-2026-07-22-task-ar-605-dispatch-t3-replan` | md | record | pass | TASK-AR-605 Dispatch T3 Replan |
| `reviews/REVIEW-2026-07-22-task-ar-605-integration-t3-replan.md` | `REVIEW-2026-07-22-task-ar-605-integration-t3-replan` | md | record | pass | TASK-AR-605 Integration T3 Replan |
| `reviews/REVIEW-2026-07-22-task-ar-606-dispatch-t3-replan.md` | `REVIEW-2026-07-22-task-ar-606-dispatch-t3-replan` | md | record | pass | TASK-AR-606 Dispatch T3 Replan |
| `reviews/REVIEW-2026-07-22-task-ar-606-integration-t3-replan.md` | `REVIEW-2026-07-22-task-ar-606-integration-t3-replan` | md | record | pass | TASK-AR-606 Integration T3 Replan |
| `reviews/REVIEW-2026-07-22-task-ar-610-scope-amendment.md` | `REVIEW-2026-07-22-task-ar-610-scope-amendment` | md | record | pass | TASK-AR-610 scope amendment |
| `reviews/REVIEW-2026-07-22-taskset-ar-backlog-taskset-test-recovery-registration.md` | `REVIEW-2026-07-22-taskset-ar-backlog-taskset-test-recovery-registration` | md | record | pass | Backlog Taskset Test Recovery Registration |
| `reviews/REVIEW-2026-07-22-taskset-ar-july-release-impact-remediation-registration.md` | `REVIEW-2026-07-22-taskset-ar-july-release-impact-remediation-registration` | md | record | pass | Release Impact Remediator Registration |
| `reviews/REVIEW-2026-07-22-taskset-ar-pr303-ci-schema-recovery-registration.md` | `REVIEW-2026-07-22-taskset-ar-pr303-ci-schema-recovery-registration` | md | record | pass | CI Schema Recovery Registration |
| `reviews/REVIEW-2026-07-22-taskset-ar-terminal-status-start-guard-registration.md` | `REVIEW-2026-07-22-taskset-ar-terminal-status-start-guard-registration` | md | record | pass | Terminal Status Start Guard Registration |
| `reviews/REVIEW-2026-07-23-cadence-isolation-backlog-expectation-recovery-plan.md` | `REVIEW-2026-07-23-cadence-isolation-backlog-expectation-recovery-plan` | md | record | needs-fix | Cadence Isolation Backlog Expectation Recovery Plan |
| `reviews/REVIEW-2026-07-23-release-auto-fixture-head-recovery-plan.md` | `REVIEW-2026-07-23-release-auto-fixture-head-recovery-plan` | md | record | needs-fix | Release-Auto Fixture HEAD Recovery Plan |
| `reviews/REVIEW-2026-07-23-release-auto-fixture-recovery-window-plan.md` | `REVIEW-2026-07-23-release-auto-fixture-recovery-window-plan` | md | record | needs-fix | Release-Auto Fixture Recovery Window Hardening Plan |
| `reviews/REVIEW-2026-07-23-release-cadence-injection-test-isolation-plan.md` | `REVIEW-2026-07-23-release-cadence-injection-test-isolation-plan` | md | record | needs-fix | Release Cadence Injection Test Isolation Plan |
| `reviews/REVIEW-2026-07-23-release-cadence-query-recovery-plan.md` | `REVIEW-2026-07-23-release-cadence-query-recovery-plan` | md | record | needs-fix | Release Cadence Query Recovery Plan |
| `reviews/REVIEW-2026-07-23-self-eval-query-integrity-plan.md` | `REVIEW-2026-07-23-self-eval-query-integrity-plan` | md | record | needs-fix | Self-Eval Query Integrity Recovery Plan |
| `reviews/REVIEW-2026-07-23-task-ar-602-t3-release-replan.md` | `REVIEW-2026-07-23-task-ar-602-t3-release-replan` | md | approved | watch | TASK-AR-602 T3 Release Replan |
| `reviews/REVIEW-2026-07-23-task-ar-602-w4a-command-replan.md` | `REVIEW-2026-07-23-task-ar-602-w4a-command-replan` | md | approved | n/a | TASK-AR-602 W4a command portability replan |
| `reviews/REVIEW-2026-07-23-task-ar-607-dispatch-t3-replan.md` | `REVIEW-2026-07-23-task-ar-607-dispatch-t3-replan` | md | record | pass | TASK-AR-607 Dispatch T3 Replan |
| `reviews/REVIEW-2026-07-23-task-ar-608-dispatch-t3-replan.md` | `REVIEW-2026-07-23-task-ar-608-dispatch-t3-replan` | md | record | pass | TASK-AR-608 Dispatch T3 Replan |
| `reviews/REVIEW-2026-07-23-task-ar-609-dispatch-t3-replan.md` | `REVIEW-2026-07-23-task-ar-609-dispatch-t3-replan` | md | record | pass | TASK-AR-609 Dispatch T3 Replan |
| `reviews/REVIEW-2026-07-23-task-ar-617-t3-cross-consumer-replan.md` | `REVIEW-2026-07-23-task-ar-617-t3-cross-consumer-replan` | md | record | pass | TASK-AR-617 Cross-Consumer T3 Replan |
| `reviews/REVIEW-2026-07-23-task-ar-617-t3-parser-compatibility-replan.md` | `REVIEW-2026-07-23-task-ar-617-t3-parser-compatibility-replan` | md | record | pass | TASK-AR-617 Parser Compatibility T3 Replan |
| `reviews/REVIEW-2026-07-23-task-ar-618-selector-precedence.md` | `REVIEW-2026-07-23-task-ar-618-selector-precedence` | md | implemented | n/a | TASK-AR-618 Exact Selector Precedence |
| `reviews/REVIEW-2026-07-23-task-ar-618-t3-selector-replan.md` | `REVIEW-2026-07-23-task-ar-618-t3-selector-replan` | md | record | pass | TASK-AR-618 Exact Selector T3 Replan |
| `reviews/REVIEW-2026-07-23-task-ar-621-closeout.md` | `REVIEW-2026-07-23-task-ar-621-closeout` | md | complete | n/a | TASK-AR-621 Closeout |
| `reviews/REVIEW-2026-07-23-task-ar-621-t3-windows-shell-replan.md` | `REVIEW-2026-07-23-task-ar-621-t3-windows-shell-replan` | md | approved | n/a | TASK-AR-621 T3 Windows verification shell replan and re-anchor |
| `reviews/REVIEW-2026-07-23-task-ar-621-verification-command-contract.md` | `REVIEW-2026-07-23-task-ar-621-verification-command-contract` | md | approved | n/a | TASK-AR-621 portable verification command execution contract |
| `reviews/REVIEW-2026-07-23-task-ar-622-t3-legacy-scalar-replan.md` | `REVIEW-2026-07-23-task-ar-622-t3-legacy-scalar-replan` | md | approved | n/a | TASK-AR-622 T3 legacy scalar replan and re-anchor |
| `reviews/REVIEW-2026-07-23-taskset-ar-cadence-isolation-backlog-expectation-recovery-registration.md` | `REVIEW-2026-07-23-taskset-ar-cadence-isolation-backlog-expectation-recovery-registration` | md | record | pass | Cadence Isolation Backlog Expectation Recovery Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-release-auto-fixture-head-recovery-registration.md` | `REVIEW-2026-07-23-taskset-ar-release-auto-fixture-head-recovery-registration` | md | record | pass | Release-Auto Fixture HEAD Recovery Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-release-auto-fixture-recovery-window-registration.md` | `REVIEW-2026-07-23-taskset-ar-release-auto-fixture-recovery-window-registration` | md | record | pass | Release-Auto Fixture Recovery Window Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-release-cadence-injection-test-isolation-registration.md` | `REVIEW-2026-07-23-taskset-ar-release-cadence-injection-test-isolation-registration` | md | record | pass | Release Cadence Injection Test Isolation Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-release-cadence-query-recovery-registration.md` | `REVIEW-2026-07-23-taskset-ar-release-cadence-query-recovery-registration` | md | record | pass | Release Cadence Query Recovery Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-self-eval-query-integrity-registration.md` | `REVIEW-2026-07-23-taskset-ar-self-eval-query-integrity-registration` | md | record | pass | Self-Eval Query Integrity Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-work-cli-integrity-registration.md` | `REVIEW-2026-07-23-taskset-ar-work-cli-integrity-registration` | md | record | pass | Work CLI Integrity Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-work-frontmatter-scalar-integrity-registration.md` | `REVIEW-2026-07-23-taskset-ar-work-frontmatter-scalar-integrity-registration` | md | record | pass | Work Frontmatter Scalar Integrity Registration |
| `reviews/REVIEW-2026-07-23-taskset-ar-work-verify-windows-shell-integrity-registration.md` | `REVIEW-2026-07-23-taskset-ar-work-verify-windows-shell-integrity-registration` | md | record | pass | Work Verify Windows Shell Integrity Registration |
| `reviews/REVIEW-2026-07-23-v0.7.0-release-notes-prepublication.md` | `REVIEW-2026-07-23-v0.7.0-release-notes-prepublication` | md | approved | pass | v0.7.0 Release Notes Prepublication Review |
| `reviews/REVIEW-2026-07-23-work-cli-integrity-design.md` | `REVIEW-2026-07-23-work-cli-integrity-design` | md | record | pass | Work CLI Metadata Integrity Design |
| `reviews/REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration.md` | `REVIEW-2026-07-23-work-frontmatter-scalar-integrity-registration` | md | registered | n/a | Work frontmatter scalar integrity defect |
| `reviews/REVIEW-2026-07-23-work-verify-windows-shell-registration.md` | `REVIEW-2026-07-23-work-verify-windows-shell-registration` | md | registered | n/a | Windows work-verify shell argument preservation defect |
| `reviews/REVIEW-2026-07-24-task-ar-622-closeout.md` | `REVIEW-2026-07-24-task-ar-622-closeout` | md | passed | pass | TASK-AR-622 Lifecycle Closeout |
| `reviews/REVIEW-2026-07-24-task-ar-622-frontmatter-scalar-contract.md` | `REVIEW-2026-07-24-task-ar-622-frontmatter-scalar-contract` | md | approved | n/a | TASK-AR-622 Frontmatter Scalar Integrity Contract |
| `reviews/REVIEW-2026-07-24-task-ar-622-t3-current-head-revalidation.md` | `REVIEW-2026-07-24-task-ar-622-t3-current-head-revalidation` | md | approved | n/a | TASK-AR-622 Current-Head T3 Revalidation |
| `reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md` | `REVIEW-2026-07-26-console-overhaul-owner-decisions` | md | record | pass | Console Overhaul Owner Decisions (15) Resolved |
| `reviews/REVIEW-2026-07-26-taskset-ar-console-overhaul-p0-registration.md` | `REVIEW-2026-07-26-taskset-ar-console-overhaul-p0-registration` | md | record | pass | Console Overhaul P0 — Trust & Hygiene Registration |
| `reviews/REVIEW-2026-07-26-taskset-ar-console-overhaul-p1-registration.md` | `REVIEW-2026-07-26-taskset-ar-console-overhaul-p1-registration` | md | record | pass | Console Overhaul P1 — Core Structure Registration |
| `reviews/REVIEW-2026-07-28-task-ar-639-unit-002-t3-replan.md` | `REVIEW-2026-07-28-task-ar-639-unit-002-t3-replan` | md | record | pass | TASK-AR-639 UNIT-002 T3 Replan |
| `reviews/REVIEW-2026-07-28-task-ar-640-w0-t3-replan.md` | `REVIEW-2026-07-28-task-ar-640-w0-t3-replan` | md | record | pass | TASK-AR-640 W0 T3 Replan |
| `reviews/REVIEW-2026-07-28-task-ar-641-w0-t3-replan.md` | `REVIEW-2026-07-28-task-ar-641-w0-t3-replan` | md | record | pass | TASK-AR-641 W0 T3 Replan |
| `reviews/REVIEW-2026-07-28-task-ar-642-w0-t3-replan.md` | `REVIEW-2026-07-28-task-ar-642-w0-t3-replan` | md | record | pass | TASK-AR-642 W0 T3 Replan |
| `reviews/REVIEW-2026-07-28-task-ar-643-w0-t3-replan.md` | `REVIEW-2026-07-28-task-ar-643-w0-t3-replan` | md | record | pass | TASK-AR-643 W0 T3 Replan |
| `reviews/REVIEW-2026-07-28-taskset-ar-v080-adoption-enforcement-registration.md` | `REVIEW-2026-07-28-taskset-ar-v080-adoption-enforcement-registration` | md | record | pass | v0.8 Adoption and Enforcement Registration |
| `reviews/REVIEW-2026-07-29-task-ar-644-w0-t3-replan.md` | `REVIEW-2026-07-29-task-ar-644-w0-t3-replan` | md | record | pass | TASK-AR-644 W0 T3 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-645-unit-002-t3-replan.md` | `REVIEW-2026-07-29-task-ar-645-unit-002-t3-replan` | md | record | pass | TASK-AR-645 UNIT-002 W0 T3 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-645-w0-t3-replan.md` | `REVIEW-2026-07-29-task-ar-645-w0-t3-replan` | md | record | pass | TASK-AR-645 W0 T3 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-646-w0-t3-replan.md` | `REVIEW-2026-07-29-task-ar-646-w0-t3-replan` | md | record | pass | TASK-AR-646 W0 T3 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-647-w0-t3-replan.md` | `REVIEW-2026-07-29-task-ar-647-w0-t3-replan` | md | record | pass | TASK-AR-647 W0 T3 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-bean-attempt-2-registration.md` | `REVIEW-2026-07-29-task-ar-648-bean-attempt-2-registration` | md | active | pass | TASK-AR-648 Bean Wiki Attempt-2 Registration |
| `reviews/REVIEW-2026-07-29-task-ar-648-bean-attempt-2-t3-replan.md` | `REVIEW-2026-07-29-task-ar-648-bean-attempt-2-t3-replan` | md | active | pass | TASK-AR-648 Bean Attempt-2 T3 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-blocked-unit-redispatch-p0-replan.md` | `REVIEW-2026-07-29-task-ar-648-blocked-unit-redispatch-p0-replan` | md | active | stop | TASK-AR-648 Blocked Unit Redispatch P0 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-claim-tree-toctou-p0-replan.md` | `REVIEW-2026-07-29-task-ar-648-claim-tree-toctou-p0-replan` | planning | record | pass | TASK-AR-648 Claim Tree TOCTOU P0 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-green-evidence-scope-amendment.md` | `REVIEW-2026-07-29-task-ar-648-green-evidence-scope-amendment` | planning | record | pass | TASK-AR-648 Bean green evidence scope amendment |
| `reviews/REVIEW-2026-07-29-task-ar-648-head-lock-handoff-p0-replan.md` | `REVIEW-2026-07-29-task-ar-648-head-lock-handoff-p0-replan` | md | active | block | TASK-AR-648 Symbolic HEAD Lock Handoff P0 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-head-reflog-p1-replan.md` | `REVIEW-2026-07-29-task-ar-648-head-reflog-p1-replan` | planning | record | fail | TASK-AR-648 Actual Worktree HEAD Reflog P1 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-host-lock-scope-amendment.md` | `REVIEW-2026-07-29-task-ar-648-host-lock-scope-amendment` | planning | record | pass | TASK-AR-648 host lock scope amendment |
| `reviews/REVIEW-2026-07-29-task-ar-648-overlay-claim-p0-replan.md` | `REVIEW-2026-07-29-task-ar-648-overlay-claim-p0-replan` | planning | record | pass | TASK-AR-648 Auto-review Overlay Claim P0 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-p0-remediation-replan.md` | `REVIEW-2026-07-29-task-ar-648-p0-remediation-replan` | md | record | pass | TASK-AR-648 Bean Pilot P0 Remediation Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-p0-replan.md` | `REVIEW-2026-07-29-task-ar-648-portable-continuity-p0-replan` | md | active | stop | TASK-AR-648 Portable Continuity P0 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-portable-continuity-remediation-registration.md` | `REVIEW-2026-07-29-task-ar-648-portable-continuity-remediation-registration` | md | active | pass | TASK-AR-648 Portable Continuity Remediation Registration |
| `reviews/REVIEW-2026-07-29-task-ar-648-post-commit-head-race-p0-replan.md` | `REVIEW-2026-07-29-task-ar-648-post-commit-head-race-p0-replan` | planning | record | fail | TASK-AR-648 Post-Commit HEAD Race P0 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-second-p0-remediation-replan.md` | `REVIEW-2026-07-29-task-ar-648-second-p0-remediation-replan` | planning | record | pass | TASK-AR-648 Second Bean P0 Remediation Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-symbolic-head-race-p0-replan.md` | `REVIEW-2026-07-29-task-ar-648-symbolic-head-race-p0-replan` | planning | record | fail | TASK-AR-648 Symbolic HEAD Race P0 Replan |
| `reviews/REVIEW-2026-07-29-task-ar-648-w0-t3-replan.md` | `REVIEW-2026-07-29-task-ar-648-w0-t3-replan` | md | record | pass | TASK-AR-648 W0 T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-3-registration.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-3-registration` | md | active | pass | TASK-AR-648 Bean Wiki Attempt-3 Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-3-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-3-t3-replan` | md | approved | pass | TASK-AR-648 Bean Attempt-3 T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-4-registration.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-4-registration` | md | active | pass | TASK-AR-648 Bean Wiki Attempt-4 Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-4-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-4-t3-replan` | md | approved | pass | TASK-AR-648 Bean Attempt-4 T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-5-registration.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-5-registration` | md | active | pass | TASK-AR-648 Bean Wiki Attempt 5 Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-5-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-5-t3-replan` | md | approved | pass | TASK-AR-648 Bean Wiki Attempt 5 T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-6-registration.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-6-registration` | md | active | pass | TASK-AR-648 Bean Wiki Attempt 6 Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-bean-attempt-6-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-bean-attempt-6-t3-replan` | md | approved | pass | TASK-AR-648 Bean Wiki Attempt 6 T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-consumer-continuity-ownership-registration.md` | `REVIEW-2026-07-30-task-ar-648-consumer-continuity-ownership-registration` | md | active | pass | Consumer Continuity Ownership Repair Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-consumer-continuity-ownership-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-consumer-continuity-ownership-t3-replan` | md | approved | pass | Consumer Continuity Ownership T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-mirror-expected-inventory-registration.md` | `REVIEW-2026-07-30-task-ar-648-mirror-expected-inventory-registration` | md | active | pass | TASK-AR-648 Expected Common Mirror Inventory Repair Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-mirror-expected-inventory-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-mirror-expected-inventory-t3-replan` | md | approved | pass | TASK-AR-648 Expected Common Mirror Inventory T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-pilot-evidence-contract-registration.md` | `REVIEW-2026-07-30-task-ar-648-pilot-evidence-contract-registration` | md | active | pass | TASK-AR-648 Pilot Evidence Contract Repair Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-pilot-evidence-contract-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-pilot-evidence-contract-t3-replan` | md | approved | pass | TASK-AR-648 Pilot Evidence Contract T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-portable-continuity-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-portable-continuity-t3-replan` | md | approved | pass | TASK-AR-648 Portable Continuity T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-648-template-mirror-isolation-registration.md` | `REVIEW-2026-07-30-task-ar-648-template-mirror-isolation-registration` | md | active | pass | TASK-AR-648 Template Mirror and Pilot Isolation Repair Registration |
| `reviews/REVIEW-2026-07-30-task-ar-648-template-mirror-isolation-t3-replan.md` | `REVIEW-2026-07-30-task-ar-648-template-mirror-isolation-t3-replan` | md | approved | pass | TASK-AR-648 Template Mirror and Pilot Isolation T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-649-allimbot-t3-replan.md` | `REVIEW-2026-07-30-task-ar-649-allimbot-t3-replan` | md | approved | pass | TASK-AR-649 Allimbot Pilot T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-650-autofolio-t3-replan.md` | `REVIEW-2026-07-30-task-ar-650-autofolio-t3-replan` | md | approved | pass | TASK-AR-650 Autofolio Migration T3 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-650-autofolio-t4-replan.md` | `REVIEW-2026-07-30-task-ar-650-autofolio-t4-replan` | md | approved | pass | TASK-AR-650 Autofolio Migration T4 Replan |
| `reviews/REVIEW-2026-07-30-task-ar-650-w4-contract-deadlock-replan.md` | `REVIEW-2026-07-30-task-ar-650-w4-contract-deadlock-replan` | md | accepted | n/a | TASK-AR-650 W4 계약 순환 차단 재계획 |
| `reviews/REVIEW-2026-07-30-task-ar-652-readiness-target-path-t3-replan.md` | `REVIEW-2026-07-30-task-ar-652-readiness-target-path-t3-replan` | md | accepted | n/a | TASK-AR-652 준비성 경로·실행 경계 T3 재계획 |
| `reviews/REVIEW-2026-07-30-task-ar-652-scope-transition-approval.md` | `REVIEW-2026-07-30-task-ar-652-scope-transition-approval` | planning | record | pass | TASK-AR-652 operability taskset scope transition approval |
| `reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-approval-replan.md` | `REVIEW-2026-07-30-task-ar-652-w4b-final-approval-replan` | md | accepted | n/a | TASK-AR-652 final-approval W4b repair replan |
| `reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-candidate-replan.md` | `REVIEW-2026-07-30-task-ar-652-w4b-final-candidate-replan` | md | accepted | n/a | TASK-AR-652 final-candidate provider-identity replan |
| `reviews/REVIEW-2026-07-30-task-ar-652-w4b-final-scope-amendment.md` | `REVIEW-2026-07-30-task-ar-652-w4b-final-scope-amendment` | md | accepted | n/a | TASK-AR-652 final W4b governance scope amendment |
| `reviews/REVIEW-2026-07-30-taskset-ar-v080-operability-dependency-t0-replan.md` | `REVIEW-2026-07-30-taskset-ar-v080-operability-dependency-t0-replan` | md | approved | pass | v0.8 Operability Dependency Preservation T0 Replan |
| `reviews/REVIEW-2026-07-30-taskset-ar-v080-operability-hardening-registration.md` | `REVIEW-2026-07-30-taskset-ar-v080-operability-hardening-registration` | md | record | pass | v0.8 Operability Hardening Registration |
| `reviews/REVIEW-2026-07-30-taskset-ar-v080-operability-hardening-t0-replan.md` | `REVIEW-2026-07-30-taskset-ar-v080-operability-hardening-t0-replan` | md | approved | pass | v0.8 Operability Hardening T0 Replan |
| `reviews/RFC-2026-06-23-character-design-exploration.md` | `RFC-2026-06-23-character-design-exploration` | rfc | proposal | decide | RFC — Character Design Exploration (P1 decision gate) |
| `reviews/RFC-2026-06-23-decision-first-console-IA.md` | `RFC-2026-06-23-decision-first-console-IA` | rfc | proposal | decide | RFC — Decision-First Console IA |
| `reviews/RFC-2026-06-23-i18n-en-schema-ko-ui.md` | `RFC-2026-06-23-i18n-en-schema-ko-ui` | rfc | proposal | decide | RFC — i18n: EN Canonical Schema + KO UI Localization |
| `reviews/RFC-2026-06-23-visual-identity-and-agent-characters.md` | `RFC-2026-06-23-visual-identity-and-agent-characters` | rfc | proposal | decide | RFC — Visual Identity & Agent Characters |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-594-INDEPENDENT-AUDITOR.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-594-INDEPENDENT-AUDITOR` | role-review | record | n/a | TASK-AR-594 Independent Auditor Role Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-594-SKEPTIC.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-594-SKEPTIC` | role-review | record | n/a | TASK-AR-594 Skeptic Role Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-595-INDEPENDENT-AUDITOR.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-595-INDEPENDENT-AUDITOR` | role-review | record | n/a | TASK-AR-595 Independent Auditor Role Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-596-INDEPENDENT-AUDITOR.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-596-INDEPENDENT-AUDITOR` | role-review | record | n/a | TASK-AR-596 Independent Auditor Role Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-597-INDEPENDENT-AUDITOR.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-597-INDEPENDENT-AUDITOR` | role-review | record | n/a | TASK-AR-597 Independent Auditor Role Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-598-INDEPENDENT-AUDITOR.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-598-INDEPENDENT-AUDITOR` | role-review | record | n/a | TASK-AR-598 Independent Auditor Role Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-598-SKEPTIC.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-598-SKEPTIC` | role-review | record | n/a | TASK-AR-598 Skeptic Closeout Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-601-INDEPENDENT-AUDITOR.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-601-INDEPENDENT-AUDITOR` | role-review | record | n/a | TASK-AR-601 Independent Auditor Role Review |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-601-SKEPTIC-RECHECK.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-601-SKEPTIC-RECHECK` | role-review | record | n/a | TASK-AR-601 Skeptic Hardening Recheck |
| `reviews/ROLE-REVIEW-2026-07-19-TASK-AR-601-SKEPTIC.md` | `ROLE-REVIEW-2026-07-19-TASK-AR-601-SKEPTIC` | role-review | record | n/a | TASK-AR-601 Skeptic Role Review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-599-SKEPTIC-REWORK.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-599-SKEPTIC-REWORK` | md | record | pass | TASK-AR-599 skeptical rework review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-599-SKEPTIC.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-599-SKEPTIC` | md | record | block | TASK-AR-599 skeptical security and external-effect review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC-REWORK.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC-REWORK` | md | record | block | TASK-AR-600 skeptical high-risk rework review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC-REWORK2.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC-REWORK2` | md | record | block | TASK-AR-600 skeptical high-risk rework 2 review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC-REWORK3.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC-REWORK3` | md | record | pass | TASK-AR-600 skeptical high-risk rework 3 review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-600-SKEPTIC` | md | record | block | TASK-AR-600 skeptical high-risk and external-effect review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-603-SKEPTIC-BLOCK.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-603-SKEPTIC-BLOCK` | md | record | fail | TASK-AR-603 Skeptic Adversarial Review - BLOCK |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-603-SKEPTIC-REWORK.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-603-SKEPTIC-REWORK` | md | record | pass | TASK-AR-603 Skeptic Unicode Boundary Rework Review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-604-SKEPTIC` | md | record | pass | TASK-AR-604 Skeptic High-Risk Review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-605-SKEPTIC-REWORK.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-605-SKEPTIC-REWORK` | md | record | pass | TASK-AR-605 High-Risk Skeptic Rework Review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-605-SKEPTIC.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-605-SKEPTIC` | md | record | fail | TASK-AR-605 High-Risk Skeptic Review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC-REWORK.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC-REWORK` | md | record | fail | TASK-AR-606 Security and Cross-Platform Skeptic Rework Review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC-REWORK2.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC-REWORK2` | md | record | pass | TASK-AR-606 Security and Cross-Platform Skeptic Rework 2 Review |
| `reviews/ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC.md` | `ROLE-REVIEW-2026-07-22-TASK-AR-606-SKEPTIC` | md | record | fail | TASK-AR-606 Security and Cross-Platform Skeptic Review |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-CANDIDATE-SKEPTIC-APPROVAL.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-602-CANDIDATE-SKEPTIC-APPROVAL` | md | conditional_approval | conditional_pass | TASK-AR-602 v0.7.0 Candidate Skeptic Approval |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC-RECHECK-2.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC-RECHECK-2` | md | approved | pass | TASK-AR-602 Final Skeptic Recheck Addendum 2 |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC-RECHECK.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC-RECHECK` | md | hold | fail | TASK-AR-602 Final Skeptic Recheck Addendum |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-602-FINAL-SKEPTIC` | md | hold | fail | TASK-AR-602 Final Skeptic W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-607-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-607-SKEPTIC` | md | record | pass | TASK-AR-607 Skeptic and Adversarial Review |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-608-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-608-SKEPTIC` | md | record | pass | TASK-AR-608 Skeptic and Adversarial W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-609-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-609-SKEPTIC` | md | record | pass | TASK-AR-609 Skeptic and Adversarial W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-612-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-612-SKEPTIC` | md | record | pass | TASK-AR-612 Skeptic and Adversarial W4b Review |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-613-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-613-SKEPTIC` | md | record | fail | TASK-AR-613 Skeptic and Adversarial W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-614-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-614-SKEPTIC` | md | record | pass | TASK-AR-614 Skeptic and Adversarial W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-615-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-615-SKEPTIC` | md | record | pass | TASK-AR-615 Skeptic and Adversarial W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-616-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-616-SKEPTIC` | md | record | pass | TASK-AR-616 Skeptic and Adversarial W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-617-SKEPTIC-APPROVAL.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-617-SKEPTIC-APPROVAL` | md | record | pass | TASK-AR-617 Skeptic Approval W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-617-SKEPTIC-FINAL.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-617-SKEPTIC-FINAL` | md | record | fail | TASK-AR-617 Final Skeptic Adversarial W4b |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-617-SKEPTIC-RECHECK.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-617-SKEPTIC-RECHECK` | md | record | fail | TASK-AR-617 Skeptic Adversarial W4b Recheck |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-618-SKEPTIC-APPROVAL.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-618-SKEPTIC-APPROVAL` | md | record | pass | TASK-AR-618 회의적 W4b 검토 |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-619-SKEPTIC-APPROVAL.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-619-SKEPTIC-APPROVAL` | md | record | pass | TASK-AR-619 회의적 W4b 검토 |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-620-SKEPTIC-APPROVAL.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-620-SKEPTIC-APPROVAL` | md | record | pass | TASK-AR-620 회의적 W4b 검토 |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-621-SKEPTIC-RECHECK.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-621-SKEPTIC-RECHECK` | md | approved | pass | TASK-AR-621 Skeptic Recheck |
| `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-621-SKEPTIC.md` | `ROLE-REVIEW-2026-07-23-TASK-AR-621-SKEPTIC` | md | hold | fail | TASK-AR-621 Skeptic and Adversarial Review |
| `reviews/ROLE-REVIEW-2026-07-24-TASK-AR-622-SKEPTIC-FINAL.md` | `ROLE-REVIEW-2026-07-24-TASK-AR-622-SKEPTIC-FINAL` | md | approved | pass | TASK-AR-622 Final Skeptical W4b Review |
| `reviews/ROLE-REVIEW-2026-07-24-TASK-AR-622-SKEPTIC-RECHECK.md` | `ROLE-REVIEW-2026-07-24-TASK-AR-622-SKEPTIC-RECHECK` | md | approved | pass | TASK-AR-622 Skeptic Recheck |
| `reviews/ROLE-REVIEW-2026-07-24-TASK-AR-622-SKEPTIC.md` | `ROLE-REVIEW-2026-07-24-TASK-AR-622-SKEPTIC` | md | hold | fail | TASK-AR-622 Skeptic and Adversarial Review |
| `reviews/ROLE-REVIEW-2026-07-28-TASK-AR-631-W4B.md` | `ROLE-REVIEW-2026-07-28-TASK-AR-631-W4B` | md | record | watch | TASK-AR-631 Independent W4b and Lifecycle Recovery Review |
| `reviews/RSI-PLANNING-TASKSET-VERIFY.json` | `RSI-PLANNING-TASKSET-VERIFY` | json | record | n/a | RSI-PLANNING-TASKSET-VERIFY |
| `reviews/SCOUT-2026-07-28-taskset-ar-v080-adoption-enforcement-w1.md` | `SCOUT-2026-07-28-taskset-ar-v080-adoption-enforcement-w1` | progress-scout-sweep | record | n/a | v0.8 Adoption and Enforcement — Wave 1 Progress Sweep |
| `reviews/SCRIBE-2026-06-21-business-operating-system.md` | `SCRIBE-2026-06-21-business-operating-system` | scribe | recorded | pass | Business Operating System Scribe Log |
| `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-214-query-contract.md` | `SEMINAR-2026-06-09-agent-runtime-task-ar-214-query-contract` | md | record | n/a | SEMINAR-2026-06-09-agent-runtime-task-ar-214-query-contract |
| `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-215-overlay-scenario.md` | `SEMINAR-2026-06-09-agent-runtime-task-ar-215-overlay-scenario` | md | record | n/a | SEMINAR-2026-06-09-agent-runtime-task-ar-215-overlay-scenario |
| `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-218-overlay-hardening-seminar.md` | `SEMINAR-2026-06-09-agent-runtime-task-ar-218-overlay-hardening-seminar` | md | record | n/a | SEMINAR-2026-06-09-agent-runtime-task-ar-218-overlay-hardening-seminar |
| `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-223-217-release-seminar.md` | `SEMINAR-2026-06-09-agent-runtime-task-ar-223-217-release-seminar` | md | record | n/a | SEMINAR: Release Evidence Model for Multi-Project agent_runtime |
| `reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-224-governance-seminar.md` | `SEMINAR-2026-06-09-agent-runtime-task-ar-224-governance-seminar` | md | record | n/a | SEMINAR (2026-06-09) - TASK-AR-224 governance seminar |
| `reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-multi-agent-sync-seminar.md` | `SEMINAR-2026-06-10-agent-runtime-task-ar-221-multi-agent-sync-seminar` | md | record | n/a | SEMINAR-2026-06-10-agent-runtime-task-ar-221-multi-agent-sync-seminar |
| `reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-release-governance-seminar.md` | `SEMINAR-2026-06-10-agent-runtime-task-ar-221-release-governance-seminar` | md | record | n/a | SEMINAR (2026-06-10): Release Governance for TASK-AR-221 Track |
| `reviews/SEMINAR-2026-06-12-agent-runtime-task-ar-gate-seminar-notes.md` | `SEMINAR-2026-06-12-agent-runtime-task-ar-gate-seminar-notes` | md | record | n/a | SEMINAR-2026-06-12-agent-runtime-task-ar-gate-seminar-notes |
| `reviews/SEMINAR-2026-06-13-agent-runtime-task-ar-211-overlay-seminar-notes.md` | `SEMINAR-2026-06-13-agent-runtime-task-ar-211-overlay-seminar-notes` | md | record | n/a | SEMINAR-2026-06-13-agent-runtime-task-ar-211-overlay-seminar-notes |
| `reviews/SEMINAR-2026-06-14-agent-runtime-task-ar-222-closeout-sync.md` | `SEMINAR-2026-06-14-agent-runtime-task-ar-222-closeout-sync` | md | record | n/a | SEMINAR: TASK-AR-222 closeout 번들 운영 동기화 세미나 |
| `reviews/SEMINAR-2026-06-15-agent-runtime-task-ar-223-governance-sync.md` | `SEMINAR-2026-06-15-agent-runtime-task-ar-223-governance-sync` | md | record | n/a | SEMINAR (2026-06-15) - TASK-AR-223 governance sync |
| `reviews/SEMINAR-2026-06-17-self-improvement-cadence.md` | `SEMINAR-2026-06-17-self-improvement-cadence` | meeting | planned | planned | Self Improvement Cadence Seminar |
| `reviews/SEMINAR-2026-06-21-business-operating-system.md` | `SEMINAR-2026-06-21-business-operating-system` | seminar | recorded | pass | Business Operating System Seminar |
| `reviews/SKEPTIC-2026-07-29-task-ar-648-overlay-claim-contract.md` | `SKEPTIC-2026-07-29-task-ar-648-overlay-claim-contract` | md | request_changes | block | TASK-AR-648 Skeptic Audit — Closeout Overlay Claim Contract |
| `reviews/SKEPTIC-2026-07-30-task-ar-649-closeout.md` | `SKEPTIC-2026-07-30-task-ar-649-closeout` | md | passed | pass | TASK-AR-649 Closeout Skeptic Review |
| `reviews/SKEPTIC-2026-07-30-task-ar-650-closeout.md` | `SKEPTIC-2026-07-30-task-ar-650-closeout` | md | passed | pass | TASK-AR-650 Skeptic Closeout |
| `reviews/VERIFY-2026-06-12-task-ar-375-20260612150820.json` | `VERIFY-2026-06-12-task-ar-375-20260612150820` | json | record | n/a | VERIFY-2026-06-12-task-ar-375-20260612150820 |
| `reviews/VERIFY-2026-06-12-task-ar-375-20260612151830.json` | `VERIFY-2026-06-12-task-ar-375-20260612151830` | json | record | n/a | VERIFY-2026-06-12-task-ar-375-20260612151830 |
| `reviews/VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151030.json` | `VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151030` | json | record | n/a | VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151030 |
| `reviews/VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151220.json` | `VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151220` | json | record | n/a | VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612151220 |
| `reviews/VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612153000.json` | `VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612153000` | json | record | n/a | VERIFY-2026-06-12-taskset-ar-agent-identity-contract-20260612153000 |
| `reviews/VERIFY-2026-06-12-unit-task-ar-372-005-20260612131309.json` | `VERIFY-2026-06-12-unit-task-ar-372-005-20260612131309` | json | record | n/a | VERIFY-2026-06-12-unit-task-ar-372-005-20260612131309 |
| `reviews/VERIFY-2026-06-12-unit-task-ar-372-006-20260612133100.json` | `VERIFY-2026-06-12-unit-task-ar-372-006-20260612133100` | json | record | n/a | VERIFY-2026-06-12-unit-task-ar-372-006-20260612133100 |
| `reviews/VERIFY-2026-06-12-unit-task-ar-372-007-20260612135400.json` | `VERIFY-2026-06-12-unit-task-ar-372-007-20260612135400` | json | record | n/a | VERIFY-2026-06-12-unit-task-ar-372-007-20260612135400 |
| `reviews/VERIFY-2026-06-12-unit-task-ar-372-008-20260612141409.json` | `VERIFY-2026-06-12-unit-task-ar-372-008-20260612141409` | json | record | n/a | VERIFY-2026-06-12-unit-task-ar-372-008-20260612141409 |
| `reviews/VERIFY-2026-06-12-unit-task-ar-372-009-20260612143100.json` | `VERIFY-2026-06-12-unit-task-ar-372-009-20260612143100` | json | record | n/a | VERIFY-2026-06-12-unit-task-ar-372-009-20260612143100 |
| `reviews/VERIFY-2026-06-12-unit-task-ar-375-001-20260612150512.json` | `VERIFY-2026-06-12-unit-task-ar-375-001-20260612150512` | json | record | n/a | VERIFY-2026-06-12-unit-task-ar-375-001-20260612150512 |
| `reviews/VERIFY-2026-06-12-unit-task-ar-375-001-20260612151810.json` | `VERIFY-2026-06-12-unit-task-ar-375-001-20260612151810` | json | record | n/a | VERIFY-2026-06-12-unit-task-ar-375-001-20260612151810 |
| `reviews/VERIFY-2026-06-15-unit-task-ar-372-005-20260615112119.json` | `VERIFY-2026-06-15-unit-task-ar-372-005-20260615112119` | json | record | n/a | VERIFY-2026-06-15-unit-task-ar-372-005-20260615112119 |
| `reviews/VERIFY-2026-06-17-task-ar-570-20260617085000.json` | `VERIFY-2026-06-17-task-ar-570-20260617085000` | json | record | n/a | VERIFY-2026-06-17-task-ar-570-20260617085000 |
| `reviews/VERIFY-2026-06-17-task-ar-571-20260617162554.json` | `VERIFY-2026-06-17-task-ar-571-20260617162554` | json | record | n/a | VERIFY-2026-06-17-task-ar-571-20260617162554 |
| `reviews/VERIFY-2026-06-17-task-ar-572-20260617170100.json` | `VERIFY-2026-06-17-task-ar-572-20260617170100` | json | record | n/a | VERIFY-2026-06-17-task-ar-572-20260617170100 |
| `reviews/VERIFY-2026-06-17-task-ar-572-20260617170800.json` | `VERIFY-2026-06-17-task-ar-572-20260617170800` | json | record | n/a | VERIFY-2026-06-17-task-ar-572-20260617170800 |
| `reviews/VERIFY-2026-06-17-task-ar-573-20260617173707.json` | `VERIFY-2026-06-17-task-ar-573-20260617173707` | json | record | n/a | VERIFY-2026-06-17-task-ar-573-20260617173707 |
| `reviews/VERIFY-2026-06-17-task-ar-574-20260617175559.json` | `VERIFY-2026-06-17-task-ar-574-20260617175559` | json | record | n/a | VERIFY-2026-06-17-task-ar-574-20260617175559 |
| `reviews/VERIFY-2026-06-17-task-ar-575-20260617182232.json` | `VERIFY-2026-06-17-task-ar-575-20260617182232` | json | record | n/a | VERIFY-2026-06-17-task-ar-575-20260617182232 |
| `reviews/VERIFY-2026-06-17-task-ar-576-20260617184640.json` | `VERIFY-2026-06-17-task-ar-576-20260617184640` | json | record | n/a | VERIFY-2026-06-17-task-ar-576-20260617184640 |
| `reviews/VERIFY-2026-06-17-task-ar-577-20260617223600.json` | `VERIFY-2026-06-17-task-ar-577-20260617223600` | json | record | n/a | VERIFY-2026-06-17-task-ar-577-20260617223600 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-570-001-20260617084842.json` | `VERIFY-2026-06-17-unit-task-ar-570-001-20260617084842` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-570-001-20260617084842 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-571-001-20260617162341.json` | `VERIFY-2026-06-17-unit-task-ar-571-001-20260617162341` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-571-001-20260617162341 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-572-001-20260617165800.json` | `VERIFY-2026-06-17-unit-task-ar-572-001-20260617165800` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-572-001-20260617165800 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-573-001-20260617172602.json` | `VERIFY-2026-06-17-unit-task-ar-573-001-20260617172602` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-573-001-20260617172602 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-574-001-20260617174554.json` | `VERIFY-2026-06-17-unit-task-ar-574-001-20260617174554` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-574-001-20260617174554 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-575-001-20260617180903.json` | `VERIFY-2026-06-17-unit-task-ar-575-001-20260617180903` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-575-001-20260617180903 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-576-001-20260617183459.json` | `VERIFY-2026-06-17-unit-task-ar-576-001-20260617183459` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-576-001-20260617183459 |
| `reviews/VERIFY-2026-06-17-unit-task-ar-577-001-20260617223200.json` | `VERIFY-2026-06-17-unit-task-ar-577-001-20260617223200` | json | record | n/a | VERIFY-2026-06-17-unit-task-ar-577-001-20260617223200 |
| `reviews/VERIFY-2026-06-18-design-system-diagnostic-closure.md` | `VERIFY-2026-06-18-design-system-diagnostic-closure` | md | accepted | n/a | Design System Diagnostic Closure Audit |
| `reviews/VERIFY-2026-06-18-task-ar-578-20260618130030.json` | `VERIFY-2026-06-18-task-ar-578-20260618130030` | json | record | n/a | VERIFY-2026-06-18-task-ar-578-20260618130030 |
| `reviews/VERIFY-2026-06-18-task-ar-579-20260618143800.json` | `VERIFY-2026-06-18-task-ar-579-20260618143800` | json | record | n/a | VERIFY-2026-06-18-task-ar-579-20260618143800 |
| `reviews/VERIFY-2026-06-18-task-ar-580-20260618150500.json` | `VERIFY-2026-06-18-task-ar-580-20260618150500` | json | record | n/a | VERIFY-2026-06-18-task-ar-580-20260618150500 |
| `reviews/VERIFY-2026-06-18-task-ar-581-20260618154000.json` | `VERIFY-2026-06-18-task-ar-581-20260618154000` | json | record | n/a | VERIFY-2026-06-18-task-ar-581-20260618154000 |
| `reviews/VERIFY-2026-06-18-task-ar-582-20260618161500.json` | `VERIFY-2026-06-18-task-ar-582-20260618161500` | json | record | n/a | VERIFY-2026-06-18-task-ar-582-20260618161500 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735.json` | `VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300.json` | `VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000.json` | `VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500.json` | `VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000.json` | `VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000 |
| `reviews/VERIFY-2026-06-20-task-ar-583-semantic-scale.json` | `VERIFY-2026-06-20-task-ar-583-semantic-scale` | json | record | n/a | VERIFY-2026-06-20-task-ar-583-semantic-scale |
| `reviews/VERIFY-2026-06-20-task-ar-584-pattern-renderers.json` | `VERIFY-2026-06-20-task-ar-584-pattern-renderers` | json | record | n/a | VERIFY-2026-06-20-task-ar-584-pattern-renderers |
| `reviews/VERIFY-2026-06-20-task-ar-587-avatar-identity.json` | `VERIFY-2026-06-20-task-ar-587-avatar-identity` | json | record | n/a | VERIFY-2026-06-20-task-ar-587-avatar-identity |
| `reviews/VERIFY-2026-06-20-task-ar-588-20260620114515.json` | `VERIFY-2026-06-20-task-ar-588-20260620114515` | json | record | n/a | VERIFY-2026-06-20-task-ar-588-20260620114515 |
| `reviews/VERIFY-2026-06-20-task-ar-591-live-wiring.json` | `VERIFY-2026-06-20-task-ar-591-live-wiring` | json | record | n/a | VERIFY-2026-06-20-task-ar-591-live-wiring |
| `reviews/VERIFY-2026-06-20-task-ar-592-a11y-responsive.json` | `VERIFY-2026-06-20-task-ar-592-a11y-responsive` | json | record | n/a | VERIFY-2026-06-20-task-ar-592-a11y-responsive |
| `reviews/VERIFY-2026-06-20-unit-task-ar-588-001-20260620114055.json` | `VERIFY-2026-06-20-unit-task-ar-588-001-20260620114055` | json | record | n/a | VERIFY-2026-06-20-unit-task-ar-588-001-20260620114055 |
| `reviews/VERIFY-2026-06-20-unit-task-ar-588-002-20260620114421.json` | `VERIFY-2026-06-20-unit-task-ar-588-002-20260620114421` | json | record | n/a | VERIFY-2026-06-20-unit-task-ar-588-002-20260620114421 |
| `reviews/VERIFY-2026-06-21-task-ar-593-20260621171220.json` | `VERIFY-2026-06-21-task-ar-593-20260621171220` | json | record | n/a | VERIFY-2026-06-21-task-ar-593-20260621171220 |
| `reviews/VERIFY-2026-06-21-unit-task-ar-593-001-20260621171000.json` | `VERIFY-2026-06-21-unit-task-ar-593-001-20260621171000` | json | record | n/a | VERIFY-2026-06-21-unit-task-ar-593-001-20260621171000 |
| `reviews/VERIFY-2026-07-19-task-ar-594-20260719105444.json` | `VERIFY-2026-07-19-task-ar-594-20260719105444` | json | record | n/a | VERIFY-2026-07-19-task-ar-594-20260719105444 |
| `reviews/VERIFY-2026-07-19-task-ar-594-20260719110720.json` | `VERIFY-2026-07-19-task-ar-594-20260719110720` | json | record | n/a | VERIFY-2026-07-19-task-ar-594-20260719110720 |
| `reviews/VERIFY-2026-07-19-task-ar-594-20260719110741.json` | `VERIFY-2026-07-19-task-ar-594-20260719110741` | json | record | n/a | VERIFY-2026-07-19-task-ar-594-20260719110741 |
| `reviews/VERIFY-2026-07-19-task-ar-595-20260719115127.json` | `VERIFY-2026-07-19-task-ar-595-20260719115127` | json | record | n/a | VERIFY-2026-07-19-task-ar-595-20260719115127 |
| `reviews/VERIFY-2026-07-19-task-ar-596-20260719120359.json` | `VERIFY-2026-07-19-task-ar-596-20260719120359` | json | record | n/a | VERIFY-2026-07-19-task-ar-596-20260719120359 |
| `reviews/VERIFY-2026-07-19-task-ar-597-20260719122124.json` | `VERIFY-2026-07-19-task-ar-597-20260719122124` | json | record | n/a | VERIFY-2026-07-19-task-ar-597-20260719122124 |
| `reviews/VERIFY-2026-07-19-task-ar-601-20260719112303.json` | `VERIFY-2026-07-19-task-ar-601-20260719112303` | json | record | n/a | VERIFY-2026-07-19-task-ar-601-20260719112303 |
| `reviews/VERIFY-2026-07-19-task-ar-601-20260719114310.json` | `VERIFY-2026-07-19-task-ar-601-20260719114310` | json | record | n/a | VERIFY-2026-07-19-task-ar-601-20260719114310 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-594-001-20260719103702.json` | `VERIFY-2026-07-19-unit-task-ar-594-001-20260719103702` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-594-001-20260719103702 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-594-001-20260719110031.json` | `VERIFY-2026-07-19-unit-task-ar-594-001-20260719110031` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-594-001-20260719110031 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-595-001-20260719114606.json` | `VERIFY-2026-07-19-unit-task-ar-595-001-20260719114606` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-595-001-20260719114606 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-596-001-20260719115906.json` | `VERIFY-2026-07-19-unit-task-ar-596-001-20260719115906` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-596-001-20260719115906 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-597-001-20260719121242.json` | `VERIFY-2026-07-19-unit-task-ar-597-001-20260719121242` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-597-001-20260719121242 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-598-001-20260719122843.json` | `VERIFY-2026-07-19-unit-task-ar-598-001-20260719122843` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-598-001-20260719122843 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-598-001-20260719123919.json` | `VERIFY-2026-07-19-unit-task-ar-598-001-20260719123919` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-598-001-20260719123919 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-598-001-20260719124202.json` | `VERIFY-2026-07-19-unit-task-ar-598-001-20260719124202` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-598-001-20260719124202 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-601-001-20260719111136.json` | `VERIFY-2026-07-19-unit-task-ar-601-001-20260719111136` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-601-001-20260719111136 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-601-001-20260719111759.json` | `VERIFY-2026-07-19-unit-task-ar-601-001-20260719111759` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-601-001-20260719111759 |
| `reviews/VERIFY-2026-07-19-unit-task-ar-601-001-20260719113247.json` | `VERIFY-2026-07-19-unit-task-ar-601-001-20260719113247` | json | record | n/a | VERIFY-2026-07-19-unit-task-ar-601-001-20260719113247 |
| `reviews/VERIFY-2026-07-22-task-ar-598-20260722163903.json` | `VERIFY-2026-07-22-task-ar-598-20260722163903` | json | record | n/a | VERIFY-2026-07-22-task-ar-598-20260722163903 |
| `reviews/VERIFY-2026-07-22-task-ar-599-20260722171444.json` | `VERIFY-2026-07-22-task-ar-599-20260722171444` | json | record | n/a | VERIFY-2026-07-22-task-ar-599-20260722171444 |
| `reviews/VERIFY-2026-07-22-task-ar-599-20260722172533.json` | `VERIFY-2026-07-22-task-ar-599-20260722172533` | json | record | n/a | VERIFY-2026-07-22-task-ar-599-20260722172533 |
| `reviews/VERIFY-2026-07-22-task-ar-600-20260722175324.json` | `VERIFY-2026-07-22-task-ar-600-20260722175324` | json | record | n/a | VERIFY-2026-07-22-task-ar-600-20260722175324 |
| `reviews/VERIFY-2026-07-22-task-ar-600-20260722175452.json` | `VERIFY-2026-07-22-task-ar-600-20260722175452` | json | record | n/a | VERIFY-2026-07-22-task-ar-600-20260722175452 |
| `reviews/VERIFY-2026-07-22-task-ar-600-20260722175618.json` | `VERIFY-2026-07-22-task-ar-600-20260722175618` | json | record | n/a | VERIFY-2026-07-22-task-ar-600-20260722175618 |
| `reviews/VERIFY-2026-07-22-task-ar-600-20260722180529.json` | `VERIFY-2026-07-22-task-ar-600-20260722180529` | json | record | n/a | VERIFY-2026-07-22-task-ar-600-20260722180529 |
| `reviews/VERIFY-2026-07-22-task-ar-600-20260722181037.json` | `VERIFY-2026-07-22-task-ar-600-20260722181037` | json | record | n/a | VERIFY-2026-07-22-task-ar-600-20260722181037 |
| `reviews/VERIFY-2026-07-22-task-ar-600-20260722181559.json` | `VERIFY-2026-07-22-task-ar-600-20260722181559` | json | record | n/a | VERIFY-2026-07-22-task-ar-600-20260722181559 |
| `reviews/VERIFY-2026-07-22-task-ar-603-20260722202126.json` | `VERIFY-2026-07-22-task-ar-603-20260722202126` | json | record | n/a | VERIFY-2026-07-22-task-ar-603-20260722202126 |
| `reviews/VERIFY-2026-07-22-task-ar-603-20260722203041.json` | `VERIFY-2026-07-22-task-ar-603-20260722203041` | json | record | n/a | VERIFY-2026-07-22-task-ar-603-20260722203041 |
| `reviews/VERIFY-2026-07-22-task-ar-603-20260722205045.json` | `VERIFY-2026-07-22-task-ar-603-20260722205045` | json | record | n/a | VERIFY-2026-07-22-task-ar-603-20260722205045 |
| `reviews/VERIFY-2026-07-22-task-ar-604-20260722212421.json` | `VERIFY-2026-07-22-task-ar-604-20260722212421` | json | record | n/a | VERIFY-2026-07-22-task-ar-604-20260722212421 |
| `reviews/VERIFY-2026-07-22-task-ar-605-20260722224220.json` | `VERIFY-2026-07-22-task-ar-605-20260722224220` | json | record | n/a | VERIFY-2026-07-22-task-ar-605-20260722224220 |
| `reviews/VERIFY-2026-07-22-task-ar-606-20260722232457.json` | `VERIFY-2026-07-22-task-ar-606-20260722232457` | json | record | n/a | VERIFY-2026-07-22-task-ar-606-20260722232457 |
| `reviews/VERIFY-2026-07-22-task-ar-606-20260722233631.json` | `VERIFY-2026-07-22-task-ar-606-20260722233631` | json | record | n/a | VERIFY-2026-07-22-task-ar-606-20260722233631 |
| `reviews/VERIFY-2026-07-22-task-ar-606-20260722234957.json` | `VERIFY-2026-07-22-task-ar-606-20260722234957` | json | record | n/a | VERIFY-2026-07-22-task-ar-606-20260722234957 |
| `reviews/VERIFY-2026-07-22-task-ar-610-20260722183640.json` | `VERIFY-2026-07-22-task-ar-610-20260722183640` | json | record | n/a | VERIFY-2026-07-22-task-ar-610-20260722183640 |
| `reviews/VERIFY-2026-07-22-task-ar-611-20260722193355.json` | `VERIFY-2026-07-22-task-ar-611-20260722193355` | json | record | n/a | VERIFY-2026-07-22-task-ar-611-20260722193355 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-599-001-20260722171357.json` | `VERIFY-2026-07-22-unit-task-ar-599-001-20260722171357` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-599-001-20260722171357 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-599-001-20260722172509.json` | `VERIFY-2026-07-22-unit-task-ar-599-001-20260722172509` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-599-001-20260722172509 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-600-001-20260722175209.json` | `VERIFY-2026-07-22-unit-task-ar-600-001-20260722175209` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-600-001-20260722175209 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-600-001-20260722180521.json` | `VERIFY-2026-07-22-unit-task-ar-600-001-20260722180521` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-600-001-20260722180521 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-600-001-20260722181034.json` | `VERIFY-2026-07-22-unit-task-ar-600-001-20260722181034` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-600-001-20260722181034 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-600-001-20260722181556.json` | `VERIFY-2026-07-22-unit-task-ar-600-001-20260722181556` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-600-001-20260722181556 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-603-001-20260722202039.json` | `VERIFY-2026-07-22-unit-task-ar-603-001-20260722202039` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-603-001-20260722202039 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-603-001-20260722202956.json` | `VERIFY-2026-07-22-unit-task-ar-603-001-20260722202956` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-603-001-20260722202956 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-603-001-20260722205011.json` | `VERIFY-2026-07-22-unit-task-ar-603-001-20260722205011` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-603-001-20260722205011 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-604-001-20260722212349.json` | `VERIFY-2026-07-22-unit-task-ar-604-001-20260722212349` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-604-001-20260722212349 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722222914.json` | `VERIFY-2026-07-22-unit-task-ar-605-001-20260722222914` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-605-001-20260722222914 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-605-001-20260722224206.json` | `VERIFY-2026-07-22-unit-task-ar-605-001-20260722224206` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-605-001-20260722224206 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-606-001-20260722232426.json` | `VERIFY-2026-07-22-unit-task-ar-606-001-20260722232426` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-606-001-20260722232426 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-606-001-20260722233621.json` | `VERIFY-2026-07-22-unit-task-ar-606-001-20260722233621` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-606-001-20260722233621 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-606-001-20260722234951.json` | `VERIFY-2026-07-22-unit-task-ar-606-001-20260722234951` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-606-001-20260722234951 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-610-001-20260722183557.json` | `VERIFY-2026-07-22-unit-task-ar-610-001-20260722183557` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-610-001-20260722183557 |
| `reviews/VERIFY-2026-07-22-unit-task-ar-611-001-20260722192021.json` | `VERIFY-2026-07-22-unit-task-ar-611-001-20260722192021` | json | record | n/a | VERIFY-2026-07-22-unit-task-ar-611-001-20260722192021 |
| `reviews/VERIFY-2026-07-23-task-ar-602-20260723143848.json` | `VERIFY-2026-07-23-task-ar-602-20260723143848` | json | record | n/a | VERIFY-2026-07-23-task-ar-602-20260723143848 |
| `reviews/VERIFY-2026-07-23-task-ar-607-20260723003910.json` | `VERIFY-2026-07-23-task-ar-607-20260723003910` | json | record | n/a | VERIFY-2026-07-23-task-ar-607-20260723003910 |
| `reviews/VERIFY-2026-07-23-task-ar-608-20260723063647.json` | `VERIFY-2026-07-23-task-ar-608-20260723063647` | json | record | n/a | VERIFY-2026-07-23-task-ar-608-20260723063647 |
| `reviews/VERIFY-2026-07-23-task-ar-608-20260723064403.json` | `VERIFY-2026-07-23-task-ar-608-20260723064403` | json | record | n/a | VERIFY-2026-07-23-task-ar-608-20260723064403 |
| `reviews/VERIFY-2026-07-23-task-ar-608-20260723064958.json` | `VERIFY-2026-07-23-task-ar-608-20260723064958` | json | record | n/a | VERIFY-2026-07-23-task-ar-608-20260723064958 |
| `reviews/VERIFY-2026-07-23-task-ar-609-20260723072306.json` | `VERIFY-2026-07-23-task-ar-609-20260723072306` | json | record | n/a | VERIFY-2026-07-23-task-ar-609-20260723072306 |
| `reviews/VERIFY-2026-07-23-task-ar-609-20260723073137.json` | `VERIFY-2026-07-23-task-ar-609-20260723073137` | json | record | n/a | VERIFY-2026-07-23-task-ar-609-20260723073137 |
| `reviews/VERIFY-2026-07-23-task-ar-612-20260723080853.json` | `VERIFY-2026-07-23-task-ar-612-20260723080853` | json | record | n/a | VERIFY-2026-07-23-task-ar-612-20260723080853 |
| `reviews/VERIFY-2026-07-23-task-ar-613-20260723014533.json` | `VERIFY-2026-07-23-task-ar-613-20260723014533` | json | record | n/a | VERIFY-2026-07-23-task-ar-613-20260723014533 |
| `reviews/VERIFY-2026-07-23-task-ar-613-20260723022608.json` | `VERIFY-2026-07-23-task-ar-613-20260723022608` | json | record | n/a | VERIFY-2026-07-23-task-ar-613-20260723022608 |
| `reviews/VERIFY-2026-07-23-task-ar-614-20260723043608.json` | `VERIFY-2026-07-23-task-ar-614-20260723043608` | json | record | n/a | VERIFY-2026-07-23-task-ar-614-20260723043608 |
| `reviews/VERIFY-2026-07-23-task-ar-615-20260723033758.json` | `VERIFY-2026-07-23-task-ar-615-20260723033758` | json | record | n/a | VERIFY-2026-07-23-task-ar-615-20260723033758 |
| `reviews/VERIFY-2026-07-23-task-ar-616-20260723052952.json` | `VERIFY-2026-07-23-task-ar-616-20260723052952` | json | record | n/a | VERIFY-2026-07-23-task-ar-616-20260723052952 |
| `reviews/VERIFY-2026-07-23-task-ar-617-20260723091055.json` | `VERIFY-2026-07-23-task-ar-617-20260723091055` | json | record | n/a | VERIFY-2026-07-23-task-ar-617-20260723091055 |
| `reviews/VERIFY-2026-07-23-task-ar-617-20260723091656.json` | `VERIFY-2026-07-23-task-ar-617-20260723091656` | json | record | n/a | VERIFY-2026-07-23-task-ar-617-20260723091656 |
| `reviews/VERIFY-2026-07-23-task-ar-617-20260723093020.json` | `VERIFY-2026-07-23-task-ar-617-20260723093020` | json | record | n/a | VERIFY-2026-07-23-task-ar-617-20260723093020 |
| `reviews/VERIFY-2026-07-23-task-ar-617-20260723094020.json` | `VERIFY-2026-07-23-task-ar-617-20260723094020` | json | record | n/a | VERIFY-2026-07-23-task-ar-617-20260723094020 |
| `reviews/VERIFY-2026-07-23-task-ar-618-20260723123800.json` | `VERIFY-2026-07-23-task-ar-618-20260723123800` | json | record | n/a | VERIFY-2026-07-23-task-ar-618-20260723123800 |
| `reviews/VERIFY-2026-07-23-task-ar-619-20260723103734.json` | `VERIFY-2026-07-23-task-ar-619-20260723103734` | json | record | n/a | VERIFY-2026-07-23-task-ar-619-20260723103734 |
| `reviews/VERIFY-2026-07-23-task-ar-619-20260723110846.json` | `VERIFY-2026-07-23-task-ar-619-20260723110846` | json | record | n/a | VERIFY-2026-07-23-task-ar-619-20260723110846 |
| `reviews/VERIFY-2026-07-23-task-ar-620-20260723112305.json` | `VERIFY-2026-07-23-task-ar-620-20260723112305` | json | record | n/a | VERIFY-2026-07-23-task-ar-620-20260723112305 |
| `reviews/VERIFY-2026-07-23-task-ar-621-20260723161123.json` | `VERIFY-2026-07-23-task-ar-621-20260723161123` | json | record | n/a | VERIFY-2026-07-23-task-ar-621-20260723161123 |
| `reviews/VERIFY-2026-07-23-task-ar-621-20260723161245.json` | `VERIFY-2026-07-23-task-ar-621-20260723161245` | json | record | n/a | VERIFY-2026-07-23-task-ar-621-20260723161245 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723135202.json` | `VERIFY-2026-07-23-unit-task-ar-602-001-20260723135202` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-602-001-20260723135202 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723141048.json` | `VERIFY-2026-07-23-unit-task-ar-602-001-20260723141048` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-602-001-20260723141048 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-602-001-20260723142627.json` | `VERIFY-2026-07-23-unit-task-ar-602-001-20260723142627` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-602-001-20260723142627 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-607-001-20260723003750.json` | `VERIFY-2026-07-23-unit-task-ar-607-001-20260723003750` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-607-001-20260723003750 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-608-001-20260723063712.json` | `VERIFY-2026-07-23-unit-task-ar-608-001-20260723063712` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-608-001-20260723063712 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-608-001-20260723064414.json` | `VERIFY-2026-07-23-unit-task-ar-608-001-20260723064414` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-608-001-20260723064414 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-608-001-20260723065008.json` | `VERIFY-2026-07-23-unit-task-ar-608-001-20260723065008` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-608-001-20260723065008 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723072326.json` | `VERIFY-2026-07-23-unit-task-ar-609-001-20260723072326` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-609-001-20260723072326 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723073123.json` | `VERIFY-2026-07-23-unit-task-ar-609-001-20260723073123` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-609-001-20260723073123 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-609-001-20260723073144.json` | `VERIFY-2026-07-23-unit-task-ar-609-001-20260723073144` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-609-001-20260723073144 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-612-001-20260723080740.json` | `VERIFY-2026-07-23-unit-task-ar-612-001-20260723080740` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-612-001-20260723080740 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-613-001-20260723015000.json` | `VERIFY-2026-07-23-unit-task-ar-613-001-20260723015000` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-613-001-20260723015000 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-613-001-20260723023209.json` | `VERIFY-2026-07-23-unit-task-ar-613-001-20260723023209` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-613-001-20260723023209 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-614-001-20260723043928.json` | `VERIFY-2026-07-23-unit-task-ar-614-001-20260723043928` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-614-001-20260723043928 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-615-001-20260723034405.json` | `VERIFY-2026-07-23-unit-task-ar-615-001-20260723034405` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-615-001-20260723034405 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-616-001-20260723053647.json` | `VERIFY-2026-07-23-unit-task-ar-616-001-20260723053647` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-616-001-20260723053647 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723091106.json` | `VERIFY-2026-07-23-unit-task-ar-617-001-20260723091106` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-617-001-20260723091106 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723091709.json` | `VERIFY-2026-07-23-unit-task-ar-617-001-20260723091709` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-617-001-20260723091709 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723093043.json` | `VERIFY-2026-07-23-unit-task-ar-617-001-20260723093043` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-617-001-20260723093043 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723094101.json` | `VERIFY-2026-07-23-unit-task-ar-617-001-20260723094101` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-617-001-20260723094101 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-618-001-20260723122800.json` | `VERIFY-2026-07-23-unit-task-ar-618-001-20260723122800` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-618-001-20260723122800 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-619-001-20260723103124.json` | `VERIFY-2026-07-23-unit-task-ar-619-001-20260723103124` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-619-001-20260723103124 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-619-001-20260723110342.json` | `VERIFY-2026-07-23-unit-task-ar-619-001-20260723110342` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-619-001-20260723110342 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-620-001-20260723112251.json` | `VERIFY-2026-07-23-unit-task-ar-620-001-20260723112251` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-620-001-20260723112251 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723155106.json` | `VERIFY-2026-07-23-unit-task-ar-621-001-20260723155106` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-621-001-20260723155106 |
| `reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723160351.json` | `VERIFY-2026-07-23-unit-task-ar-621-001-20260723160351` | json | record | n/a | VERIFY-2026-07-23-unit-task-ar-621-001-20260723160351 |
| `reviews/VERIFY-2026-07-24-task-ar-622-20260724161222.json` | `VERIFY-2026-07-24-task-ar-622-20260724161222` | json | record | n/a | VERIFY-2026-07-24-task-ar-622-20260724161222 |
| `reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724154051.json` | `VERIFY-2026-07-24-unit-task-ar-622-001-20260724154051` | json | record | n/a | VERIFY-2026-07-24-unit-task-ar-622-001-20260724154051 |
| `reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724155415.json` | `VERIFY-2026-07-24-unit-task-ar-622-001-20260724155415` | json | record | n/a | VERIFY-2026-07-24-unit-task-ar-622-001-20260724155415 |
| `reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724160143.json` | `VERIFY-2026-07-24-unit-task-ar-622-001-20260724160143` | json | record | n/a | VERIFY-2026-07-24-unit-task-ar-622-001-20260724160143 |
| `reviews/VERIFY-2026-07-26-unit-task-ar-623-001-20260726131911.json` | `VERIFY-2026-07-26-unit-task-ar-623-001-20260726131911` | json | record | n/a | VERIFY-2026-07-26-unit-task-ar-623-001-20260726131911 |
| `reviews/VERIFY-2026-07-26-unit-task-ar-624-001-20260726131913.json` | `VERIFY-2026-07-26-unit-task-ar-624-001-20260726131913` | json | record | n/a | VERIFY-2026-07-26-unit-task-ar-624-001-20260726131913 |
| `reviews/VERIFY-2026-07-26-unit-task-ar-625-001-20260726131916.json` | `VERIFY-2026-07-26-unit-task-ar-625-001-20260726131916` | json | record | n/a | VERIFY-2026-07-26-unit-task-ar-625-001-20260726131916 |
| `reviews/VERIFY-2026-07-26-unit-task-ar-626-001-20260726131919.json` | `VERIFY-2026-07-26-unit-task-ar-626-001-20260726131919` | json | record | n/a | VERIFY-2026-07-26-unit-task-ar-626-001-20260726131919 |
| `reviews/VERIFY-2026-07-26-unit-task-ar-627-001-20260726131920.json` | `VERIFY-2026-07-26-unit-task-ar-627-001-20260726131920` | json | record | n/a | VERIFY-2026-07-26-unit-task-ar-627-001-20260726131920 |
| `reviews/VERIFY-2026-07-26-unit-task-ar-628-001-20260726131923.json` | `VERIFY-2026-07-26-unit-task-ar-628-001-20260726131923` | json | record | n/a | VERIFY-2026-07-26-unit-task-ar-628-001-20260726131923 |
| `reviews/VERIFY-2026-07-26-unit-task-ar-629-001-20260726131926.json` | `VERIFY-2026-07-26-unit-task-ar-629-001-20260726131926` | json | record | n/a | VERIFY-2026-07-26-unit-task-ar-629-001-20260726131926 |
| `reviews/VERIFY-2026-07-27-unit-task-ar-630-001-20260727103021.json` | `VERIFY-2026-07-27-unit-task-ar-630-001-20260727103021` | json | record | n/a | VERIFY-2026-07-27-unit-task-ar-630-001-20260727103021 |
| `reviews/VERIFY-2026-07-27-unit-task-ar-630-001-20260727104728.json` | `VERIFY-2026-07-27-unit-task-ar-630-001-20260727104728` | json | record | n/a | VERIFY-2026-07-27-unit-task-ar-630-001-20260727104728 |
| `reviews/VERIFY-2026-07-27-unit-task-ar-631-001-20260727111227.json` | `VERIFY-2026-07-27-unit-task-ar-631-001-20260727111227` | json | record | n/a | VERIFY-2026-07-27-unit-task-ar-631-001-20260727111227 |
| `reviews/VERIFY-2026-07-28-task-ar-631-20260728163046.json` | `VERIFY-2026-07-28-task-ar-631-20260728163046` | json | record | n/a | VERIFY-2026-07-28-task-ar-631-20260728163046 |
| `reviews/VERIFY-2026-07-28-task-ar-639-20260728191831.json` | `VERIFY-2026-07-28-task-ar-639-20260728191831` | json | record | n/a | VERIFY-2026-07-28-task-ar-639-20260728191831 |
| `reviews/VERIFY-2026-07-28-task-ar-640-20260728204500.json` | `VERIFY-2026-07-28-task-ar-640-20260728204500` | json | record | n/a | VERIFY-2026-07-28-task-ar-640-20260728204500 |
| `reviews/VERIFY-2026-07-28-task-ar-641-20260728215509.json` | `VERIFY-2026-07-28-task-ar-641-20260728215509` | json | record | n/a | VERIFY-2026-07-28-task-ar-641-20260728215509 |
| `reviews/VERIFY-2026-07-28-task-ar-642-20260728231433.json` | `VERIFY-2026-07-28-task-ar-642-20260728231433` | json | record | n/a | VERIFY-2026-07-28-task-ar-642-20260728231433 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-639-001-20260728170913.json` | `VERIFY-2026-07-28-unit-task-ar-639-001-20260728170913` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-639-001-20260728170913 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728181538.json` | `VERIFY-2026-07-28-unit-task-ar-639-002-20260728181538` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-639-002-20260728181538 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728183121.json` | `VERIFY-2026-07-28-unit-task-ar-639-002-20260728183121` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-639-002-20260728183121 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728183401.json` | `VERIFY-2026-07-28-unit-task-ar-639-002-20260728183401` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-639-002-20260728183401 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-639-002-20260728184625.json` | `VERIFY-2026-07-28-unit-task-ar-639-002-20260728184625` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-639-002-20260728184625 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-640-001-20260728200124.json` | `VERIFY-2026-07-28-unit-task-ar-640-001-20260728200124` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-640-001-20260728200124 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-640-001-20260728201555.json` | `VERIFY-2026-07-28-unit-task-ar-640-001-20260728201555` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-640-001-20260728201555 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-640-001-20260728202110.json` | `VERIFY-2026-07-28-unit-task-ar-640-001-20260728202110` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-640-001-20260728202110 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-640-001-20260728202444.json` | `VERIFY-2026-07-28-unit-task-ar-640-001-20260728202444` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-640-001-20260728202444 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-640-001-20260728203048.json` | `VERIFY-2026-07-28-unit-task-ar-640-001-20260728203048` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-640-001-20260728203048 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-641-001-20260728210208.json` | `VERIFY-2026-07-28-unit-task-ar-641-001-20260728210208` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-641-001-20260728210208 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-641-001-20260728211515.json` | `VERIFY-2026-07-28-unit-task-ar-641-001-20260728211515` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-641-001-20260728211515 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-641-001-20260728212212.json` | `VERIFY-2026-07-28-unit-task-ar-641-001-20260728212212` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-641-001-20260728212212 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-641-001-20260728213523.json` | `VERIFY-2026-07-28-unit-task-ar-641-001-20260728213523` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-641-001-20260728213523 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-641-001-20260728215537.json` | `VERIFY-2026-07-28-unit-task-ar-641-001-20260728215537` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-641-001-20260728215537 |
| `reviews/VERIFY-2026-07-28-unit-task-ar-642-001-20260728231513.json` | `VERIFY-2026-07-28-unit-task-ar-642-001-20260728231513` | json | record | n/a | VERIFY-2026-07-28-unit-task-ar-642-001-20260728231513 |
| `reviews/VERIFY-2026-07-29-task-ar-643-20260729003452.json` | `VERIFY-2026-07-29-task-ar-643-20260729003452` | json | record | n/a | VERIFY-2026-07-29-task-ar-643-20260729003452 |
| `reviews/VERIFY-2026-07-29-task-ar-643-20260729005318.json` | `VERIFY-2026-07-29-task-ar-643-20260729005318` | json | record | n/a | VERIFY-2026-07-29-task-ar-643-20260729005318 |
| `reviews/VERIFY-2026-07-29-task-ar-644-20260729023558.json` | `VERIFY-2026-07-29-task-ar-644-20260729023558` | json | record | n/a | VERIFY-2026-07-29-task-ar-644-20260729023558 |
| `reviews/VERIFY-2026-07-29-task-ar-644-20260729025243.json` | `VERIFY-2026-07-29-task-ar-644-20260729025243` | json | record | n/a | VERIFY-2026-07-29-task-ar-644-20260729025243 |
| `reviews/VERIFY-2026-07-29-task-ar-644-20260729031017.json` | `VERIFY-2026-07-29-task-ar-644-20260729031017` | json | record | n/a | VERIFY-2026-07-29-task-ar-644-20260729031017 |
| `reviews/VERIFY-2026-07-29-task-ar-645-20260729054620.json` | `VERIFY-2026-07-29-task-ar-645-20260729054620` | json | record | n/a | VERIFY-2026-07-29-task-ar-645-20260729054620 |
| `reviews/VERIFY-2026-07-29-task-ar-646-20260729073326.json` | `VERIFY-2026-07-29-task-ar-646-20260729073326` | json | record | n/a | VERIFY-2026-07-29-task-ar-646-20260729073326 |
| `reviews/VERIFY-2026-07-29-task-ar-646-20260729073520.json` | `VERIFY-2026-07-29-task-ar-646-20260729073520` | json | record | n/a | VERIFY-2026-07-29-task-ar-646-20260729073520 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729094525.json` | `VERIFY-2026-07-29-task-ar-647-20260729094525` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729094525 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729102601.json` | `VERIFY-2026-07-29-task-ar-647-20260729102601` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729102601 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729112131.json` | `VERIFY-2026-07-29-task-ar-647-20260729112131` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729112131 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729120704.json` | `VERIFY-2026-07-29-task-ar-647-20260729120704` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729120704 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729125149.json` | `VERIFY-2026-07-29-task-ar-647-20260729125149` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729125149 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729132647.json` | `VERIFY-2026-07-29-task-ar-647-20260729132647` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729132647 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729133558.json` | `VERIFY-2026-07-29-task-ar-647-20260729133558` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729133558 |
| `reviews/VERIFY-2026-07-29-task-ar-647-20260729140829.json` | `VERIFY-2026-07-29-task-ar-647-20260729140829` | json | record | n/a | VERIFY-2026-07-29-task-ar-647-20260729140829 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-643-001-20260729003236.json` | `VERIFY-2026-07-29-unit-task-ar-643-001-20260729003236` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-643-001-20260729003236 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-643-001-20260729005339.json` | `VERIFY-2026-07-29-unit-task-ar-643-001-20260729005339` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-643-001-20260729005339 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729022142.json` | `VERIFY-2026-07-29-unit-task-ar-644-001-20260729022142` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-644-001-20260729022142 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729023334.json` | `VERIFY-2026-07-29-unit-task-ar-644-001-20260729023334` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-644-001-20260729023334 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729025018.json` | `VERIFY-2026-07-29-unit-task-ar-644-001-20260729025018` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-644-001-20260729025018 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-644-001-20260729030636.json` | `VERIFY-2026-07-29-unit-task-ar-644-001-20260729030636` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-644-001-20260729030636 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729041748.json` | `VERIFY-2026-07-29-unit-task-ar-645-001-20260729041748` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-645-001-20260729041748 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729042042.json` | `VERIFY-2026-07-29-unit-task-ar-645-001-20260729042042` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-645-001-20260729042042 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-645-001-20260729043455.json` | `VERIFY-2026-07-29-unit-task-ar-645-001-20260729043455` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-645-001-20260729043455 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-645-002-20260729054357.json` | `VERIFY-2026-07-29-unit-task-ar-645-002-20260729054357` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-645-002-20260729054357 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-645-002-20260729054503.json` | `VERIFY-2026-07-29-unit-task-ar-645-002-20260729054503` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-645-002-20260729054503 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-646-001-20260729072848.json` | `VERIFY-2026-07-29-unit-task-ar-646-001-20260729072848` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-646-001-20260729072848 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729093804.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729093804` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729093804 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729102332.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729102332` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729102332 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729111858.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729111858` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729111858 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729120428.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729120428` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729120428 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729124908.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729124908` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729124908 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729132409.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729132409` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729132409 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729133326.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729133326` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729133326 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-647-001-20260729140550.json` | `VERIFY-2026-07-29-unit-task-ar-647-001-20260729140550` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-647-001-20260729140550 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-001-20260729162858.json` | `VERIFY-2026-07-29-unit-task-ar-648-001-20260729162858` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-001-20260729162858 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-003-20260729190144.json` | `VERIFY-2026-07-29-unit-task-ar-648-003-20260729190144` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-003-20260729190144 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-003-20260729192303.json` | `VERIFY-2026-07-29-unit-task-ar-648-003-20260729192303` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-003-20260729192303 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-004-20260729200919.json` | `VERIFY-2026-07-29-unit-task-ar-648-004-20260729200919` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-004-20260729200919 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-005-20260729210330.json` | `VERIFY-2026-07-29-unit-task-ar-648-005-20260729210330` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-005-20260729210330 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-005-20260729213242.json` | `VERIFY-2026-07-29-unit-task-ar-648-005-20260729213242` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-005-20260729213242 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-005-20260729214144.json` | `VERIFY-2026-07-29-unit-task-ar-648-005-20260729214144` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-005-20260729214144 |
| `reviews/VERIFY-2026-07-29-unit-task-ar-648-005-20260729224310.json` | `VERIFY-2026-07-29-unit-task-ar-648-005-20260729224310` | json | record | n/a | VERIFY-2026-07-29-unit-task-ar-648-005-20260729224310 |
| `reviews/VERIFY-2026-07-30-task-ar-648-20260730072800.json` | `VERIFY-2026-07-30-task-ar-648-20260730072800` | json | record | n/a | VERIFY-2026-07-30-task-ar-648-20260730072800 |
| `reviews/VERIFY-2026-07-30-task-ar-649-20260730083005.json` | `VERIFY-2026-07-30-task-ar-649-20260730083005` | json | record | n/a | VERIFY-2026-07-30-task-ar-649-20260730083005 |
| `reviews/VERIFY-2026-07-30-task-ar-649-20260730083100.json` | `VERIFY-2026-07-30-task-ar-649-20260730083100` | json | record | n/a | VERIFY-2026-07-30-task-ar-649-20260730083100 |
| `reviews/VERIFY-2026-07-30-task-ar-650-20260730121429.json` | `VERIFY-2026-07-30-task-ar-650-20260730121429` | json | record | n/a | VERIFY-2026-07-30-task-ar-650-20260730121429 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-648-007-20260730000654.json` | `VERIFY-2026-07-30-unit-task-ar-648-007-20260730000654` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-648-007-20260730000654 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-648-007-20260730001127.json` | `VERIFY-2026-07-30-unit-task-ar-648-007-20260730001127` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-648-007-20260730001127 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-648-008-20260730011630.json` | `VERIFY-2026-07-30-unit-task-ar-648-008-20260730011630` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-648-008-20260730011630 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-648-010-20260730022400.json` | `VERIFY-2026-07-30-unit-task-ar-648-010-20260730022400` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-648-010-20260730022400 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-648-016-20260730072000.json` | `VERIFY-2026-07-30-unit-task-ar-648-016-20260730072000` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-648-016-20260730072000 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-649-001-20260730083000.json` | `VERIFY-2026-07-30-unit-task-ar-649-001-20260730083000` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-649-001-20260730083000 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-650-001-20260730121113.json` | `VERIFY-2026-07-30-unit-task-ar-650-001-20260730121113` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-650-001-20260730121113 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730130910.json` | `VERIFY-2026-07-30-unit-task-ar-652-001-20260730130910` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-652-001-20260730130910 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730141633.json` | `VERIFY-2026-07-30-unit-task-ar-652-001-20260730141633` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-652-001-20260730141633 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730150652.json` | `VERIFY-2026-07-30-unit-task-ar-652-001-20260730150652` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-652-001-20260730150652 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730155247.json` | `VERIFY-2026-07-30-unit-task-ar-652-001-20260730155247` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-652-001-20260730155247 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730163357.json` | `VERIFY-2026-07-30-unit-task-ar-652-001-20260730163357` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-652-001-20260730163357 |
| `reviews/VERIFY-2026-07-30-unit-task-ar-652-001-20260730170435.json` | `VERIFY-2026-07-30-unit-task-ar-652-001-20260730170435` | json | record | n/a | VERIFY-2026-07-30-unit-task-ar-652-001-20260730170435 |
| `reviews/W4A-2026-07-29-unit-task-ar-644-001-ci-followup.md` | `W4A-2026-07-29-unit-task-ar-644-001-ci-followup` | md | passed | pass | TASK-AR-644 UNIT-001 CI Sanitization Follow-up W4a |
| `reviews/W4A-2026-07-29-unit-task-ar-644-001.md` | `W4A-2026-07-29-unit-task-ar-644-001` | md | passed | pass | TASK-AR-644 UNIT-001 W4a Self-Review |
| `reviews/W4A-2026-07-29-unit-task-ar-645-001.md` | `W4A-2026-07-29-unit-task-ar-645-001` | md | passed | pass | TASK-AR-645 UNIT-001 W4a Self-Review |
| `reviews/W4A-2026-07-29-unit-task-ar-645-002.md` | `W4A-2026-07-29-unit-task-ar-645-002` | md | passed | pass | TASK-AR-645 UNIT-002 W4a Self-Review |
| `reviews/W4A-2026-07-29-unit-task-ar-646-001.md` | `W4A-2026-07-29-unit-task-ar-646-001` | md | passed | pass | TASK-AR-646 UNIT-001 W4a Self-Review |
| `reviews/W4A-2026-07-29-unit-task-ar-647-001-r2.md` | `W4A-2026-07-29-unit-task-ar-647-001-r2` | md | passed | pass | TASK-AR-647 UNIT-001 W4a Remediation Self-Review |
| `reviews/W4A-2026-07-29-unit-task-ar-647-001-r3.md` | `W4A-2026-07-29-unit-task-ar-647-001-r3` | md | passed | pass | TASK-AR-647 UNIT-001 W4a Structural-Boundary Remediation Review |
| `reviews/W4A-2026-07-29-unit-task-ar-647-001-r4.md` | `W4A-2026-07-29-unit-task-ar-647-001-r4` | md | passed | pass | TASK-AR-647 UNIT-001 W4a Registry and Gate Integrity Remediation Review |
| `reviews/W4A-2026-07-29-unit-task-ar-647-001-r6.md` | `W4A-2026-07-29-unit-task-ar-647-001-r6` | md | passed | pass | TASK-AR-647 UNIT-001 Missing-Gate and Scalar Integrity Remediation W4a |
| `reviews/W4A-2026-07-29-unit-task-ar-647-001-r7.md` | `W4A-2026-07-29-unit-task-ar-647-001-r7` | md | passed | pass | TASK-AR-647 UNIT-001 Security Metadata Snapshot Remediation W4a |
| `reviews/W4A-2026-07-29-unit-task-ar-647-001-r8.md` | `W4A-2026-07-29-unit-task-ar-647-001-r8` | md | passed | pass | TASK-AR-647 UNIT-001 HTML Block Section Integrity Remediation W4a |
| `reviews/W4A-2026-07-29-unit-task-ar-647-001.md` | `W4A-2026-07-29-unit-task-ar-647-001` | md | passed | pass | TASK-AR-647 UNIT-001 W4a Self-Review |
| `reviews/W4A-2026-07-29-unit-task-ar-648-003-r2.md` | `W4A-2026-07-29-unit-task-ar-648-003-r2` | md | passed | pass | TASK-AR-648 UNIT-003 HEAD-persisted Claim Gate W4a R2 |
| `reviews/W4A-2026-07-29-unit-task-ar-648-003.md` | `W4A-2026-07-29-unit-task-ar-648-003` | md | passed | pass | TASK-AR-648 UNIT-003 Claim SCM and Portable State Runtime W4a |
| `reviews/W4A-2026-07-29-unit-task-ar-648-004.md` | `W4A-2026-07-29-unit-task-ar-648-004` | md | passed | pass | TASK-AR-648 UNIT-004 Overlay and Claim Transaction W4a |
| `reviews/W4A-2026-07-29-unit-task-ar-648-005-r3.md` | `W4A-2026-07-29-unit-task-ar-648-005-r3` | md | passed | pass | TASK-AR-648 UNIT-005 Atomic Claim Publication W4a R3 |
| `reviews/W4A-2026-07-29-unit-task-ar-648-005-r4.md` | `W4A-2026-07-29-unit-task-ar-648-005-r4` | md | passed | pass | TASK-AR-648 UNIT-005 Atomic Claim Publication W4a R4 |
| `reviews/W4A-2026-07-29-unit-task-ar-648-005.md` | `W4A-2026-07-29-unit-task-ar-648-005` | md | passed | pass | TASK-AR-648 UNIT-005 Immutable Claim Tree W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-648-007.md` | `W4A-2026-07-30-unit-task-ar-648-007` | md | passed | pass | TASK-AR-648 UNIT-007 Blocked Unit Redispatch Guard W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-648-008.md` | `W4A-2026-07-30-unit-task-ar-648-008` | md | passed | pass | TASK-AR-648 UNIT-008 Portable Continuity Contract W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-648-009.md` | `W4A-2026-07-30-unit-task-ar-648-009` | md | blocked | block | W4a — UNIT-TASK-AR-648-009 |
| `reviews/W4A-2026-07-30-unit-task-ar-648-010.md` | `W4A-2026-07-30-unit-task-ar-648-010` | md | passed | pass | TASK-AR-648 UNIT-010 Consumer Continuity Ownership W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-648-011.md` | `W4A-2026-07-30-unit-task-ar-648-011` | md | blocked | block | W4a — UNIT-TASK-AR-648-011 |
| `reviews/W4A-2026-07-30-unit-task-ar-648-012.md` | `W4A-2026-07-30-unit-task-ar-648-012` | md | approved | approve | W4a — UNIT-TASK-AR-648-012 |
| `reviews/W4A-2026-07-30-unit-task-ar-648-013.md` | `W4A-2026-07-30-unit-task-ar-648-013` | md | approved | approve | W4a — UNIT-TASK-AR-648-013 |
| `reviews/W4A-2026-07-30-unit-task-ar-648-014.md` | `W4A-2026-07-30-unit-task-ar-648-014` | md | blocked | block | W4a — UNIT-TASK-AR-648-014 |
| `reviews/W4A-2026-07-30-unit-task-ar-648-015.md` | `W4A-2026-07-30-unit-task-ar-648-015` | md | approved | pass | W4a — UNIT-TASK-AR-648-015 |
| `reviews/W4A-2026-07-30-unit-task-ar-648-016.md` | `W4A-2026-07-30-unit-task-ar-648-016` | md | passed | pass | W4a — UNIT-TASK-AR-648-016 |
| `reviews/W4A-2026-07-30-unit-task-ar-649-001.md` | `W4A-2026-07-30-unit-task-ar-649-001` | md | passed | n/a | W4a — UNIT-TASK-AR-649-001 |
| `reviews/W4A-2026-07-30-unit-task-ar-650-001.md` | `W4A-2026-07-30-unit-task-ar-650-001` | md | pass | n/a | W4a - UNIT-TASK-AR-650-001 |
| `reviews/W4A-2026-07-30-unit-task-ar-652-001-final-approval-repair.md` | `W4A-2026-07-30-unit-task-ar-652-001-final-approval-repair` | md | passed | pass | TASK-AR-652 UNIT-001 Final Approval Repair W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-652-001-final-followup.md` | `W4A-2026-07-30-unit-task-ar-652-001-final-followup` | md | passed | pass | TASK-AR-652 UNIT-001 Final Recheck Repair W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-652-001-followup.md` | `W4A-2026-07-30-unit-task-ar-652-001-followup` | md | passed | pass | TASK-AR-652 UNIT-001 Economic Routing Repair Follow-up W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-652-001-provider-identity-repair.md` | `W4A-2026-07-30-unit-task-ar-652-001-provider-identity-repair` | md | passed | pass | TASK-AR-652 UNIT-001 Provider Identity Repair W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-652-001-recheck-followup.md` | `W4A-2026-07-30-unit-task-ar-652-001-recheck-followup` | md | passed | pass | TASK-AR-652 UNIT-001 Second Recheck Repair W4a |
| `reviews/W4A-2026-07-30-unit-task-ar-652-001.md` | `W4A-2026-07-30-unit-task-ar-652-001` | md | passed | pass | W4a - UNIT-TASK-AR-652-001 |
| `reviews/W4B-2026-06-13-TASK-AR-320.md` | `W4B-2026-06-13-TASK-AR-320` | verification | record | n/a | W4b Independent Verification — TASK-AR-320 (Theme System) |
| `reviews/W4B-2026-06-13-TASK-AR-321.md` | `W4B-2026-06-13-TASK-AR-321` | verification | record | n/a | W4b Independent Verification — TASK-AR-321 (Sidebar IA + Hash Routing) |
| `reviews/W4B-2026-06-13-TASK-AR-322.md` | `W4B-2026-06-13-TASK-AR-322` | verification | record | n/a | W4b Independent Verification — TASK-AR-322 (Common List Pattern) |
| `reviews/W4B-2026-06-13-TASK-AR-324.md` | `W4B-2026-06-13-TASK-AR-324` | verification | record | n/a | W4b Independent Verification — TASK-AR-324 (Team/Agent RPG Cards) |
| `reviews/W4B-2026-06-13-TASK-AR-325.md` | `W4B-2026-06-13-TASK-AR-325` | verification | record | n/a | W4b Independent Verification — TASK-AR-325 (Roadmap Timeline) |
| `reviews/W4B-2026-06-13-TASK-AR-326.md` | `W4B-2026-06-13-TASK-AR-326` | verification | record | n/a | W4b Independent Verification — TASK-AR-326 (Realtime Presence + Live Map) |
| `reviews/W4B-2026-06-13-TASK-AR-327.md` | `W4B-2026-06-13-TASK-AR-327` | verification | record | n/a | W4b Independent Verification — TASK-AR-327 (Channels View + Meeting/Seminar) |
| `reviews/W4B-2026-06-13-TASK-AR-328.md` | `W4B-2026-06-13-TASK-AR-328` | verification | record | n/a | W4b Independent Verification — TASK-AR-328 (Taskset Boundary Execution Guard) |
| `reviews/W4B-2026-06-13-TASK-AR-329.md` | `W4B-2026-06-13-TASK-AR-329` | verification | record | n/a | W4b Independent Verification — TASK-AR-329 (Taskset Lifecycle UI) |
| `reviews/W4B-2026-06-13-TASK-AR-330.md` | `W4B-2026-06-13-TASK-AR-330` | verification | record | n/a | W4b Independent Verification — TASK-AR-330 (Subtask/Dependency + Timeline + Graph) |
| `reviews/W4B-2026-06-13-TASK-AR-331.md` | `W4B-2026-06-13-TASK-AR-331` | verification | record | n/a | W4b Independent Verification — TASK-AR-331 (Custom Properties + Labels + Automation + Triage) |
| `reviews/W4B-2026-06-13-TASK-AR-332.md` | `W4B-2026-06-13-TASK-AR-332` | verification | record | n/a | W4b Independent Verification — TASK-AR-332 (File Attachments) |
| `reviews/W4B-2026-06-13-TASK-AR-333.md` | `W4B-2026-06-13-TASK-AR-333` | verification | record | n/a | W4b Independent Verification — TASK-AR-333 (Import/Export) |
| `reviews/W4B-2026-06-13-TASK-AR-334.md` | `W4B-2026-06-13-TASK-AR-334` | verification | record | n/a | W4b Independent Verification — TASK-AR-334 (Global Search + Quick Open) |
| `reviews/W4B-2026-06-13-TASK-AR-335.md` | `W4B-2026-06-13-TASK-AR-335` | verification | record | n/a | W4b Independent Verification — TASK-AR-335 (Calendar + Scheduled Dispatch) |
| `reviews/W4B-2026-06-13-TASK-AR-336.md` | `W4B-2026-06-13-TASK-AR-336` | verification | record | n/a | W4b Independent Verification — TASK-AR-336 (State-Machine Viewer) |
| `reviews/W4B-2026-06-13-TASK-AR-337.md` | `W4B-2026-06-13-TASK-AR-337` | verification | record | n/a | W4b Independent Verification — TASK-AR-337 (Team/Role Assignment + Workload Heatmap) |
| `reviews/W4B-2026-06-13-TASK-AR-362.md` | `W4B-2026-06-13-TASK-AR-362` | verification | record | n/a | W4b Independent Verification — TASK-AR-362 (Board Peek + DnD + Quick Actions) |
| `reviews/W4B-2026-06-14-TASK-AR-338.md` | `W4B-2026-06-14-TASK-AR-338` | verification | record | n/a | W4b Independent Verification — TASK-AR-338 (Notification center + mentions/pins/reactions + daily brief) |
| `reviews/W4B-2026-06-14-TASK-AR-339.md` | `W4B-2026-06-14-TASK-AR-339` | verification | record | n/a | W4b Independent Verification — TASK-AR-339 (Ops dashboard — token/cost, eval, gates, burndown) |
| `reviews/W4B-2026-06-14-TASK-AR-340.md` | `W4B-2026-06-14-TASK-AR-340` | verification | record | n/a | W4b Independent Verification — TASK-AR-340 (Microinteractions + gamification policy layer) |
| `reviews/W4B-2026-06-14-TASK-AR-341.md` | `W4B-2026-06-14-TASK-AR-341` | verification | record | n/a | W4b Independent Verification — TASK-AR-341 (Workspace switcher + widget extension points + i18n) |
| `reviews/W4B-2026-06-14-TASK-AR-363.md` | `W4B-2026-06-14-TASK-AR-363` | verification | record | n/a | W4b Independent Verification — TASK-AR-363 (Growth system — project Lv / business stage / XP with guardrails) |
| `reviews/W4B-2026-06-14-TASK-AR-364.md` | `W4B-2026-06-14-TASK-AR-364` | verification | record | n/a | W4b Independent Verification — TASK-AR-364 (2D office map — agent sprites + emoji action glyphs) |
| `reviews/W4B-2026-06-14-TASK-AR-365.md` | `W4B-2026-06-14-TASK-AR-365` | verification | record | n/a | W4b Independent Verification — TASK-AR-365 (External notification routing — webhook-first) |
| `reviews/W4B-2026-06-14-TASK-AR-526.md` | `W4B-2026-06-14-TASK-AR-526` | verification | record | n/a | W4b Independent Verification — TASK-AR-526 (Host feedback intake + triage classifier) |
| `reviews/W4B-2026-06-14-TASK-AR-527.md` | `W4B-2026-06-14-TASK-AR-527` | verification | record | n/a | W4b Independent Verification — TASK-AR-527 (Blind-Delphi deliberation harness + first run) |
| `reviews/W4B-2026-06-14-TASK-AR-528.md` | `W4B-2026-06-14-TASK-AR-528` | verification | record | n/a | W4b Independent Verification — TASK-AR-528 (Host-feedback reply-back mechanism) |
| `reviews/W4B-2026-06-14-TASK-AR-529.md` | `W4B-2026-06-14-TASK-AR-529` | verification | record | n/a | W4b Independent Verification — TASK-AR-529 (post-hoc actual-vs-declared footprint check) |
| `reviews/W4B-2026-06-14-TASK-AR-530.md` | `W4B-2026-06-14-TASK-AR-530` | verification | record | n/a | W4b Independent Verification — TASK-AR-530 (cross-version self-eval harness, advisory gate) |
| `reviews/W4B-2026-06-14-TASK-AR-531.md` | `W4B-2026-06-14-TASK-AR-531` | verification | record | n/a | W4b Independent Verification — TASK-AR-531 (wheel-dotfile packaging, P1 sub-gap) |
| `reviews/W4B-2026-06-14-TASK-AR-532.md` | `W4B-2026-06-14-TASK-AR-532` | verification | record | n/a | W4b Independent Verification — TASK-AR-532 (open BUG verify-first regression guards) |
| `reviews/W4B-2026-06-14-TASK-AR-533.md` | `W4B-2026-06-14-TASK-AR-533` | verification | record | n/a | W4b Independent Verification — TASK-AR-533 (Board attention-lanes + archive manifest extraction) |
| `reviews/W4B-2026-06-14-TASK-AR-534.md` | `W4B-2026-06-14-TASK-AR-534` | verification | record | n/a | W4b Independent Verification — TASK-AR-534 (Reviews date-shard capability + planner) |
| `reviews/W4B-2026-06-14-TASK-AR-535.md` | `W4B-2026-06-14-TASK-AR-535` | verification | record | n/a | W4b Independent Verification — TASK-AR-535 (Classifier ordinal as canonical human ID + numbering policy) |
| `reviews/W4B-2026-06-14-TASK-AR-536.md` | `W4B-2026-06-14-TASK-AR-536` | verification | record | n/a | W4b Independent Verification — TASK-AR-536 (UUIDv7 stable key + reservation demotion) |
| `reviews/W4B-2026-06-14-TASK-AR-537.md` | `W4B-2026-06-14-TASK-AR-537` | verification | record | n/a | W4b Independent Verification — TASK-AR-537 (Manifest-first read surface + perf config) |
| `reviews/W4B-2026-06-14-TASK-AR-538.md` | `W4B-2026-06-14-TASK-AR-538` | verification | record | n/a | W4b Independent Verification — TASK-AR-538 (Triage intake status + needs-attention lane) |
| `reviews/W4B-2026-06-14-TASK-AR-539.md` | `W4B-2026-06-14-TASK-AR-539` | verification | record | n/a | W4b Independent Verification — TASK-AR-539 (Unified artifact entity catalog) |
| `reviews/W4B-2026-06-14-TASK-AR-540.md` | `W4B-2026-06-14-TASK-AR-540` | verification | record | n/a | W4b Independent Verification — TASK-AR-540 (command palette + cross-entity search) |
| `reviews/W4B-2026-06-14-TASK-AR-541-545.md` | `W4B-2026-06-14-TASK-AR-541-545` | verification | record | n/a | W4b Independent Verification — Decision Console Surfaces (TASK-AR-541/542/543/544/545) |
| `reviews/W4B-2026-06-15-TASK-AR-366-368.md` | `W4B-2026-06-15-TASK-AR-366-368` | md | record | n/a | W4B Independent Verification — TASK-AR-366 & TASK-AR-368 |
| `reviews/W4B-2026-06-15-TASK-AR-371-374.md` | `W4B-2026-06-15-TASK-AR-371-374` | md | record | n/a | W4B-2026-06-15-TASK-AR-371-374 |
| `reviews/W4B-2026-06-15-TASK-AR-546-556.md` | `W4B-2026-06-15-TASK-AR-546-556` | md | record | n/a | W4B Independent Verification — TASKSET-AR-546-556 (product-maturity-uplift) |
| `reviews/W4B-2026-06-15-TASK-AR-557.md` | `W4B-2026-06-15-TASK-AR-557` | md | record | n/a | W4B Independent Verification — TASK-AR-557 (Unit 1: Role/Team/Tier Registry) |
| `reviews/W4B-2026-06-15-TASK-AR-558-562.md` | `W4B-2026-06-15-TASK-AR-558-562` | md | record | n/a | W4B Independent Verification — TASK-AR-558..562 (Agent Org Delegation) |
| `reviews/W4B-2026-06-15-TASK-AR-563-564.md` | `W4B-2026-06-15-TASK-AR-563-564` | md | record | n/a | W4B Independent Verification — TASK-AR-563/564 (decision-first cockpit) |
| `reviews/W4B-2026-06-16-TASK-AR-565.md` | `W4B-2026-06-16-TASK-AR-565` | verification | record | n/a | W4b Independent Verification - TASK-AR-565 |
| `reviews/W4B-2026-06-16-TASK-AR-566.md` | `W4B-2026-06-16-TASK-AR-566` | md | record | n/a | W4b Independent Verification - TASK-AR-566 |
| `reviews/W4B-2026-06-16-TASK-AR-567.md` | `W4B-2026-06-16-TASK-AR-567` | md | record | n/a | W4B Verification - TASK-AR-567 |
| `reviews/W4B-2026-06-16-TASK-AR-568.md` | `W4B-2026-06-16-TASK-AR-568` | md | record | n/a | W4B Verification - TASK-AR-568 |
| `reviews/W4B-2026-06-17-TASK-AR-569.md` | `W4B-2026-06-17-TASK-AR-569` | md | record | n/a | TASK-AR-569 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-570.md` | `W4B-2026-06-17-TASK-AR-570` | md | record | n/a | TASK-AR-570 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-571.md` | `W4B-2026-06-17-TASK-AR-571` | md | record | n/a | TASK-AR-571 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-572.md` | `W4B-2026-06-17-TASK-AR-572` | md | record | n/a | TASK-AR-572 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-573.md` | `W4B-2026-06-17-TASK-AR-573` | md | record | n/a | TASK-AR-573 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-574.md` | `W4B-2026-06-17-TASK-AR-574` | md | approved | pass | TASK-AR-574 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-575.md` | `W4B-2026-06-17-TASK-AR-575` | md | approved | pass | TASK-AR-575 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-576.md` | `W4B-2026-06-17-TASK-AR-576` | md | approved | pass | TASK-AR-576 W4b Independent Verification |
| `reviews/W4B-2026-06-17-TASK-AR-577.md` | `W4B-2026-06-17-TASK-AR-577` | w4b-independent-verification | approved | pass | W4b Independent Verification: TASK-AR-577 |
| `reviews/W4B-2026-06-18-TASK-AR-578.md` | `W4B-2026-06-18-TASK-AR-578` | md | passed | pass | W4b Verification - TASK-AR-578 |
| `reviews/W4B-2026-06-18-TASK-AR-579.md` | `W4B-2026-06-18-TASK-AR-579` | md | accepted | n/a | W4B Independent Verification - TASK-AR-579 |
| `reviews/W4B-2026-06-18-TASK-AR-580.md` | `W4B-2026-06-18-TASK-AR-580` | md | accepted | n/a | W4B Independent Verification - TASK-AR-580 |
| `reviews/W4B-2026-06-18-TASK-AR-581.md` | `W4B-2026-06-18-TASK-AR-581` | md | accepted | n/a | W4B Independent Verification - TASK-AR-581 |
| `reviews/W4B-2026-06-18-TASK-AR-582.md` | `W4B-2026-06-18-TASK-AR-582` | md | accepted | n/a | W4B Independent Verification - TASK-AR-582 |
| `reviews/W4B-2026-06-20-TASK-AR-583.md` | `W4B-2026-06-20-TASK-AR-583` | md | accepted | n/a | W4B Independent Verification - TASK-AR-583 |
| `reviews/W4B-2026-06-20-TASK-AR-584.md` | `W4B-2026-06-20-TASK-AR-584` | md | accepted | n/a | W4B Independent Verification - TASK-AR-584 |
| `reviews/W4B-2026-06-20-TASK-AR-587.md` | `W4B-2026-06-20-TASK-AR-587` | md | accepted | n/a | W4B Independent Verification - TASK-AR-587 |
| `reviews/W4B-2026-06-20-TASK-AR-588.md` | `W4B-2026-06-20-TASK-AR-588` | md | accepted | pass | W4B Independent Verification - TASK-AR-588 |
| `reviews/W4B-2026-06-20-TASK-AR-591.md` | `W4B-2026-06-20-TASK-AR-591` | md | accepted | n/a | W4B Independent Verification - TASK-AR-591 |
| `reviews/W4B-2026-06-20-TASK-AR-592.md` | `W4B-2026-06-20-TASK-AR-592` | md | accepted | n/a | W4B Independent Verification - TASK-AR-592 |
| `reviews/W4B-2026-06-21-TASK-AR-593.md` | `W4B-2026-06-21-TASK-AR-593` | w4b-independent-verification | approved | pass | W4b Independent Verification: TASK-AR-593 |
| `reviews/W4B-2026-07-19-TASK-AR-594-RECHECK.md` | `W4B-2026-07-19-TASK-AR-594-RECHECK` | w4b-independent-verification | approved | pass | W4b Independent Verification Recheck: TASK-AR-594 |
| `reviews/W4B-2026-07-19-TASK-AR-594-REWORK.md` | `W4B-2026-07-19-TASK-AR-594-REWORK` | w4b-independent-verification | approved | pass | TASK-AR-594 Rework W4b Independent Verification |
| `reviews/W4B-2026-07-19-TASK-AR-594.md` | `W4B-2026-07-19-TASK-AR-594` | w4b-independent-verification | conditional_reject | fail | W4b Independent Verification: TASK-AR-594 |
| `reviews/W4B-2026-07-19-TASK-AR-595.md` | `W4B-2026-07-19-TASK-AR-595` | w4b-independent-verification | approved | pass | TASK-AR-595 W4b Independent Verification |
| `reviews/W4B-2026-07-19-TASK-AR-596.md` | `W4B-2026-07-19-TASK-AR-596` | w4b-independent-verification | approved | pass | TASK-AR-596 W4b Independent Verification |
| `reviews/W4B-2026-07-19-TASK-AR-597.md` | `W4B-2026-07-19-TASK-AR-597` | w4b-independent-verification | approved | pass | TASK-AR-597 W4b Independent Verification |
| `reviews/W4B-2026-07-19-TASK-AR-598-REWORK.md` | `W4B-2026-07-19-TASK-AR-598-REWORK` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-598 Rework |
| `reviews/W4B-2026-07-19-TASK-AR-598.md` | `W4B-2026-07-19-TASK-AR-598` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-598 |
| `reviews/W4B-2026-07-19-TASK-AR-601-HARDENING.md` | `W4B-2026-07-19-TASK-AR-601-HARDENING` | w4b-independent-verification | approved | pass | TASK-AR-601 Hardening W4b Independent Verification |
| `reviews/W4B-2026-07-19-TASK-AR-601-RECHECK.md` | `W4B-2026-07-19-TASK-AR-601-RECHECK` | w4b-independent-verification | approved | pass | TASK-AR-601 W4b Independent Verification Recheck |
| `reviews/W4B-2026-07-19-TASK-AR-601.md` | `W4B-2026-07-19-TASK-AR-601` | w4b-independent-verification | rejected | fail | TASK-AR-601 W4b Independent Verification |
| `reviews/W4B-2026-07-22-TASK-AR-599-REWORK.md` | `W4B-2026-07-22-TASK-AR-599-REWORK` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-599 Rework |
| `reviews/W4B-2026-07-22-TASK-AR-599.md` | `W4B-2026-07-22-TASK-AR-599` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-599 |
| `reviews/W4B-2026-07-22-TASK-AR-600-REWORK.md` | `W4B-2026-07-22-TASK-AR-600-REWORK` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-600 Rework |
| `reviews/W4B-2026-07-22-TASK-AR-600-REWORK2.md` | `W4B-2026-07-22-TASK-AR-600-REWORK2` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-600 Second Rework |
| `reviews/W4B-2026-07-22-TASK-AR-600-REWORK3.md` | `W4B-2026-07-22-TASK-AR-600-REWORK3` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-600 Third Remediation |
| `reviews/W4B-2026-07-22-TASK-AR-600.md` | `W4B-2026-07-22-TASK-AR-600` | w4b-independent-verification | approved | pass | W4b Independent Verification — TASK-AR-600 |
| `reviews/W4B-2026-07-22-TASK-AR-603-UNICODE-REWORK.md` | `W4B-2026-07-22-TASK-AR-603-UNICODE-REWORK` | md | record | pass | TASK-AR-603 Unicode Rework Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-603.md` | `W4B-2026-07-22-TASK-AR-603` | md | record | pass | TASK-AR-603 Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-604.md` | `W4B-2026-07-22-TASK-AR-604` | md | record | pass | TASK-AR-604 Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-605-REWORK.md` | `W4B-2026-07-22-TASK-AR-605-REWORK` | md | record | pass | TASK-AR-605 Rework Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-605.md` | `W4B-2026-07-22-TASK-AR-605` | md | record | pass | TASK-AR-605 Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-606-REWORK.md` | `W4B-2026-07-22-TASK-AR-606-REWORK` | md | record | fail | TASK-AR-606 Rework Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-606-REWORK2.md` | `W4B-2026-07-22-TASK-AR-606-REWORK2` | md | record | pass | TASK-AR-606 Rework2 Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-606.md` | `W4B-2026-07-22-TASK-AR-606` | md | record | pass | TASK-AR-606 Independent W4b Verification |
| `reviews/W4B-2026-07-22-TASK-AR-610.md` | `W4B-2026-07-22-TASK-AR-610` | md | record | pass | TASK-AR-610 Independent W4b |
| `reviews/W4B-2026-07-22-TASK-AR-611.md` | `W4B-2026-07-22-TASK-AR-611` | md | record | pass | TASK-AR-611 Independent W4b |
| `reviews/W4B-2026-07-23-TASK-AR-602-CANDIDATE-APPROVAL.md` | `W4B-2026-07-23-TASK-AR-602-CANDIDATE-APPROVAL` | md | candidate_approved | pass | TASK-AR-602 v0.7.0 Candidate Independent W4b Approval |
| `reviews/W4B-2026-07-23-TASK-AR-602-FINAL.md` | `W4B-2026-07-23-TASK-AR-602-FINAL` | md | final_approved | pass | TASK-AR-602 v0.7.0 Final Independent W4b Technical Approval |
| `reviews/W4B-2026-07-23-TASK-AR-607.md` | `W4B-2026-07-23-TASK-AR-607` | md | record | pass | TASK-AR-607 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-608.md` | `W4B-2026-07-23-TASK-AR-608` | md | record | pass | TASK-AR-608 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-609.md` | `W4B-2026-07-23-TASK-AR-609` | md | record | pass | TASK-AR-609 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-612.md` | `W4B-2026-07-23-TASK-AR-612` | md | record | pass | TASK-AR-612 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-613.md` | `W4B-2026-07-23-TASK-AR-613` | md | record | fail | TASK-AR-613 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-614.md` | `W4B-2026-07-23-TASK-AR-614` | md | record | pass | TASK-AR-614 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-615.md` | `W4B-2026-07-23-TASK-AR-615` | md | record | pass | TASK-AR-615 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-616.md` | `W4B-2026-07-23-TASK-AR-616` | md | record | pass | TASK-AR-616 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-617-APPROVAL.md` | `W4B-2026-07-23-TASK-AR-617-APPROVAL` | md | record | pass | TASK-AR-617 Final W4b Approval Reverification |
| `reviews/W4B-2026-07-23-TASK-AR-617-FINAL.md` | `W4B-2026-07-23-TASK-AR-617-FINAL` | md | record | fail | TASK-AR-617 Final Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-617-RECHECK.md` | `W4B-2026-07-23-TASK-AR-617-RECHECK` | md | record | fail | TASK-AR-617 Independent W4b Recheck |
| `reviews/W4B-2026-07-23-TASK-AR-617.md` | `W4B-2026-07-23-TASK-AR-617` | md | record | fail | TASK-AR-617 Independent W4b Verification |
| `reviews/W4B-2026-07-23-TASK-AR-618-APPROVAL.md` | `W4B-2026-07-23-TASK-AR-618-APPROVAL` | md | record | pass | TASK-AR-618 Final Independent W4b Approval |
| `reviews/W4B-2026-07-23-TASK-AR-619-APPROVAL.md` | `W4B-2026-07-23-TASK-AR-619-APPROVAL` | md | record | pass | TASK-AR-619 Final CI-Aware Independent W4b Approval |
| `reviews/W4B-2026-07-23-TASK-AR-620-APPROVAL.md` | `W4B-2026-07-23-TASK-AR-620-APPROVAL` | md | record | pass | TASK-AR-620 Final CI-Aware Independent W4b Approval |
| `reviews/W4B-2026-07-23-TASK-AR-621-APPROVAL.md` | `W4B-2026-07-23-TASK-AR-621-APPROVAL` | md | approved | pass | TASK-AR-621 Independent W4b Technical Approval |
| `reviews/W4B-2026-07-23-TASK-AR-621-RECHECK.md` | `W4B-2026-07-23-TASK-AR-621-RECHECK` | md | approved | pass | TASK-AR-621 Independent W4b Recheck |
| `reviews/W4B-2026-07-23-TASK-AR-621-RELEASE.md` | `W4B-2026-07-23-TASK-AR-621-RELEASE` | md | approved | pass | TASK-AR-621 Independent W4b Release Evidence |
| `reviews/W4B-2026-07-24-TASK-AR-622-FINAL.md` | `W4B-2026-07-24-TASK-AR-622-FINAL` | md | approved | pass | TASK-AR-622 Final Independent W4b Verification |
| `reviews/W4B-2026-07-24-TASK-AR-622-INDEPENDENT.md` | `W4B-2026-07-24-TASK-AR-622-INDEPENDENT` | md | blocked | block | TASK-AR-622 Independent W4b Technical Verification |
| `reviews/W4B-2026-07-24-TASK-AR-622-RECHECK.md` | `W4B-2026-07-24-TASK-AR-622-RECHECK` | md | blocked | block | TASK-AR-622 Independent W4b Recheck |
| `reviews/W4B-2026-07-28-unit-task-ar-639-001.md` | `W4B-2026-07-28-unit-task-ar-639-001` | verification | record | n/a | W4b Independent Verification — UNIT-TASK-AR-639-001 |
| `reviews/W4B-2026-07-28-unit-task-ar-639-002-recheck-2.md` | `W4B-2026-07-28-unit-task-ar-639-002-recheck-2` | verification | passed | pass | UNIT-TASK-AR-639-002 Independent W4b Approval Recheck |
| `reviews/W4B-2026-07-28-unit-task-ar-639-002-recheck.md` | `W4B-2026-07-28-unit-task-ar-639-002-recheck` | verification | blocked | fail | UNIT-TASK-AR-639-002 Independent W4b Recheck |
| `reviews/W4B-2026-07-28-unit-task-ar-639-002.md` | `W4B-2026-07-28-unit-task-ar-639-002` | verification | blocked | fail | UNIT-TASK-AR-639-002 Independent W4b Blocking Review |
| `reviews/W4B-2026-07-28-unit-task-ar-640-001-recheck.md` | `W4B-2026-07-28-unit-task-ar-640-001-recheck` | md | approved | pass | TASK-AR-640 UNIT-001 Independent W4b Recheck |
| `reviews/W4B-2026-07-28-unit-task-ar-640-001.md` | `W4B-2026-07-28-unit-task-ar-640-001` | md | changes_required | fail | TASK-AR-640 UNIT-001 Independent W4b Verification |
| `reviews/W4B-2026-07-28-unit-task-ar-641-001-approved.md` | `W4B-2026-07-28-unit-task-ar-641-001-approved` | md | approved | pass | TASK-AR-641 UNIT-001 Final Independent W4b Approval |
| `reviews/W4B-2026-07-28-unit-task-ar-641-001-final.md` | `W4B-2026-07-28-unit-task-ar-641-001-final` | md | changes_required | fail | TASK-AR-641 UNIT-001 Final Independent W4b |
| `reviews/W4B-2026-07-28-unit-task-ar-641-001.md` | `W4B-2026-07-28-unit-task-ar-641-001` | md | changes_required | fail | TASK-AR-641 UNIT-001 Independent W4b Verification |
| `reviews/W4B-2026-07-28-unit-task-ar-642-001-approved.md` | `W4B-2026-07-28-unit-task-ar-642-001-approved` | md | approved | pass | TASK-AR-642 UNIT-001 Independent W4b Approval |
| `reviews/W4B-2026-07-29-unit-task-ar-643-001-approved.md` | `W4B-2026-07-29-unit-task-ar-643-001-approved` | md | approved | pass | TASK-AR-643 UNIT-001 Independent W4b Approval |
| `reviews/W4B-2026-07-29-unit-task-ar-644-001-ci-followup.md` | `W4B-2026-07-29-unit-task-ar-644-001-ci-followup` | md | approved | pass | TASK-AR-644 UNIT-001 CI Sanitization Follow-up W4b |
| `reviews/W4B-2026-07-29-unit-task-ar-644-001.md` | `W4B-2026-07-29-unit-task-ar-644-001` | md | approved | pass | TASK-AR-644 UNIT-001 Independent W4b Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-645-001.md` | `W4B-2026-07-29-unit-task-ar-645-001` | md | approved | pass | TASK-AR-645 UNIT-001 Independent W4b Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-645-002.md` | `W4B-2026-07-29-unit-task-ar-645-002` | md | approved | pass | TASK-AR-645 UNIT-002 Independent W4b Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-646-001.md` | `W4B-2026-07-29-unit-task-ar-646-001` | md | approved | pass | TASK-AR-646 UNIT-001 Independent W4b Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-647-001-r2.md` | `W4B-2026-07-29-unit-task-ar-647-001-r2` | md | changes_required | fail | TASK-AR-647 UNIT-001 Independent W4b Remediation Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-647-001-r3.md` | `W4B-2026-07-29-unit-task-ar-647-001-r3` | md | changes_required | fail | TASK-AR-647 UNIT-001 Independent W4b Structural Remediation Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-647-001-r5.md` | `W4B-2026-07-29-unit-task-ar-647-001-r5` | md | changes_required | fail | TASK-AR-647 UNIT-001 Independent W4b Integrity Remediation Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-647-001-r6.md` | `W4B-2026-07-29-unit-task-ar-647-001-r6` | md | changes_required | fail | TASK-AR-647 UNIT-001 Independent W4b Missing-Gate and Scalar Remediation Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-647-001-r7.md` | `W4B-2026-07-29-unit-task-ar-647-001-r7` | md | changes_required | block | TASK-AR-647 UNIT-001 Independent W4b Security Metadata Remediation Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-647-001-r8.md` | `W4B-2026-07-29-unit-task-ar-647-001-r8` | md | approved | pass | TASK-AR-647 UNIT-001 Independent W4b HTML Block Remediation Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-647-001.md` | `W4B-2026-07-29-unit-task-ar-647-001` | md | changes_required | fail | TASK-AR-647 UNIT-001 Independent W4b Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-648-001.md` | `W4B-2026-07-29-unit-task-ar-648-001` | md | approved | pass | TASK-AR-648 UNIT-001 Independent W4b Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-648-002.md` | `W4B-2026-07-29-unit-task-ar-648-002` | md | blocked | fail | TASK-AR-648 UNIT-002 Independent W4b Verification |
| `reviews/W4B-2026-07-29-unit-task-ar-648-003-r2.md` | `W4B-2026-07-29-unit-task-ar-648-003-r2` | md | passed | pass | TASK-AR-648 UNIT-003 Independent W4b R2 |
| `reviews/W4B-2026-07-29-unit-task-ar-648-003.md` | `W4B-2026-07-29-unit-task-ar-648-003` | md | blocked | fail | TASK-AR-648 UNIT-003 독립 W4b 재검증 |
| `reviews/W4B-2026-07-29-unit-task-ar-648-004.md` | `W4B-2026-07-29-unit-task-ar-648-004` | md | failed | block | TASK-AR-648 UNIT-004 Independent W4b |
| `reviews/W4B-2026-07-29-unit-task-ar-648-005-r4.md` | `W4B-2026-07-29-unit-task-ar-648-005-r4` | md | passed | pass | TASK-AR-648 UNIT-005 Independent W4b R4 |
| `reviews/W4B-2026-07-29-unit-task-ar-648-005.md` | `W4B-2026-07-29-unit-task-ar-648-005` | md | failed | block | TASK-AR-648 UNIT-005 Independent W4b |
| `reviews/W4B-2026-07-29-unit-task-ar-648-006-continuity-block.md` | `W4B-2026-07-29-unit-task-ar-648-006-continuity-block` | md | failed | block | Bean Wiki Attempt-2 Portable Continuity Independent Review |
| `reviews/W4B-2026-07-30-unit-task-ar-648-007.md` | `W4B-2026-07-30-unit-task-ar-648-007` | md | passed | pass | TASK-AR-648 UNIT-007 Blocked Unit Redispatch Guard W4b |
| `reviews/W4B-2026-07-30-unit-task-ar-648-008.md` | `W4B-2026-07-30-unit-task-ar-648-008` | md | passed | pass | TASK-AR-648 UNIT-008 Portable Continuity Contract W4b |
| `reviews/W4B-2026-07-30-unit-task-ar-648-009.md` | `W4B-2026-07-30-unit-task-ar-648-009` | md | blocked | block | W4b — UNIT-TASK-AR-648-009 Bean attempt 3 |
| `reviews/W4B-2026-07-30-unit-task-ar-648-010.md` | `W4B-2026-07-30-unit-task-ar-648-010` | md | passed | pass | TASK-AR-648 UNIT-010 Consumer Continuity Ownership W4b |
| `reviews/W4B-2026-07-30-unit-task-ar-648-011.md` | `W4B-2026-07-30-unit-task-ar-648-011` | md | blocked | block | W4b — UNIT-TASK-AR-648-011 |
| `reviews/W4B-2026-07-30-unit-task-ar-648-012.md` | `W4B-2026-07-30-unit-task-ar-648-012` | md | blocked | block | W4b — UNIT-TASK-AR-648-012 |
| `reviews/W4B-2026-07-30-unit-task-ar-648-013.md` | `W4B-2026-07-30-unit-task-ar-648-013` | md | approved | approve | W4b — UNIT-TASK-AR-648-013 |
| `reviews/W4B-2026-07-30-unit-task-ar-648-014.md` | `W4B-2026-07-30-unit-task-ar-648-014` | md | blocked | block | W4b — UNIT-TASK-AR-648-014 |
| `reviews/W4B-2026-07-30-unit-task-ar-648-015.md` | `W4B-2026-07-30-unit-task-ar-648-015` | md | approved | pass | W4b — UNIT-TASK-AR-648-015 |
| `reviews/W4B-2026-07-30-unit-task-ar-648-016.md` | `W4B-2026-07-30-unit-task-ar-648-016` | md | passed | pass | W4b — UNIT-TASK-AR-648-016 |
| `reviews/W4B-2026-07-30-unit-task-ar-649-001.md` | `W4B-2026-07-30-unit-task-ar-649-001` | md | passed | pass | W4b — UNIT-TASK-AR-649-001 |
| `reviews/W4B-2026-07-30-unit-task-ar-650-001.md` | `W4B-2026-07-30-unit-task-ar-650-001` | md | passed | pass | W4b - UNIT-TASK-AR-650-001 |
| `reviews/W4B-2026-07-30-unit-task-ar-652-001-final-approval.md` | `W4B-2026-07-30-unit-task-ar-652-001-final-approval` | md | blocked | block | W4b Final Approval - UNIT-TASK-AR-652-001 |
| `reviews/W4B-2026-07-30-unit-task-ar-652-001-final-candidate.md` | `W4B-2026-07-30-unit-task-ar-652-001-final-candidate` | md | blocked | block | W4b Final Candidate - UNIT-TASK-AR-652-001 |
| `reviews/W4B-2026-07-30-unit-task-ar-652-001-final-recheck.md` | `W4B-2026-07-30-unit-task-ar-652-001-final-recheck` | md | blocked | block | W4b Final Recheck - UNIT-TASK-AR-652-001 |
| `reviews/W4B-2026-07-30-unit-task-ar-652-001-provider-identity.md` | `W4B-2026-07-30-unit-task-ar-652-001-provider-identity` | md | blocked | block | W4b Provider Identity - UNIT-TASK-AR-652-001 |
| `reviews/W4B-2026-07-30-unit-task-ar-652-001-recheck.md` | `W4B-2026-07-30-unit-task-ar-652-001-recheck` | md | blocked | block | W4b Recheck - UNIT-TASK-AR-652-001 |
| `reviews/W4B-2026-07-30-unit-task-ar-652-001.md` | `W4B-2026-07-30-unit-task-ar-652-001` | md | blocked | block | W4b - UNIT-TASK-AR-652-001 |
| `reviews/WORK-REGISTRATION-2026-07-19-role-routing-closeout-reliability.json` | `WORK-REGISTRATION-2026-07-19-role-routing-closeout-reliability` | json | record | n/a | WORK-REGISTRATION-2026-07-19-role-routing-closeout-reliability |
| `reviews/WORK-REGISTRATION-2026-07-19-upstream-intake.json` | `WORK-REGISTRATION-2026-07-19-upstream-intake` | json | record | n/a | WORK-REGISTRATION-2026-07-19-upstream-intake |
| `reviews/WORK-REGISTRATION-2026-07-23-work-cli-integrity.json` | `WORK-REGISTRATION-2026-07-23-work-cli-integrity` | json | record | n/a | WORK-REGISTRATION-2026-07-23-work-cli-integrity |

## Risks / Blockers
- Risk: this index proves coverage, not semantic correctness of each evidence file.

## Next Steps
- Run `python scripts/evidence_index_generator.py --write` after adding new reviews.
- Run `python scripts/evidence_index_generator.py --check` before closeout.
