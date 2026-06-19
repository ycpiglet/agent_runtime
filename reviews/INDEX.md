---
type: evidence_index
id: EVIDENCE-INDEX-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [evidence, traceability, generated-index]
generated_at: 2026-06-19T09:26:11+09:00
record_count: 631
---

# Evidence Index

## Bottom Line
- Summary: indexed `631` review and evidence records under `reviews/`.
- Result: task closeout evidence is searchable by path, id, status, signal, and title.

## Signal
| Metric | State | Evidence |
| --- | --- | --- |
| Reviews covered | pass | `631` files |
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
| `reviews/BETA-PLAN-2026-06-19-operator-attention-graph.md` | `BETA-PLAN-2026-06-19-operator-attention-graph` | ui-beta-test-plan | accepted | pass | Operator Attention Graph Beta Plan |
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
| `reviews/CONTEXT-KNOWLEDGE-GATE-2026-06-11-final.json` | `CONTEXT-KNOWLEDGE-GATE-2026-06-11-final` | json | record | n/a | CONTEXT-KNOWLEDGE-GATE-2026-06-11-final |
| `reviews/CORRECTION-COLLECTOR-2026-06-09-task-ar-207.json` | `CORRECTION-COLLECTOR-2026-06-09-task-ar-207` | json | record | n/a | CORRECTION-COLLECTOR-2026-06-09-task-ar-207 |
| `reviews/CORRECTION-COLLECTOR-2026-06-10-task-ar-207-current.json` | `CORRECTION-COLLECTOR-2026-06-10-task-ar-207-current` | json | record | n/a | CORRECTION-COLLECTOR-2026-06-10-task-ar-207-current |
| `reviews/CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final.json` | `CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final` | json | record | n/a | CORRECTION-COLLECTOR-2026-06-10-taskset-quality-loop-final |
| `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md` | `COUNCIL-2026-06-14-host-feedback-first-deliberation` | council | watch | watch | Council — Host Feedback First Deliberation (TASK-AR-527) |
| `reviews/DIAGNOSTIC-2026-06-18-ui-design-system-maturity.md` | `DIAGNOSTIC-2026-06-18-ui-design-system-maturity` | md | accepted | n/a | UI Design System Maturity Diagnostic |
| `reviews/GOVERNANCE-OPS-REPORT-2026-06-10.md` | `GOVERNANCE-OPS-REPORT-2026-06-10` | governance_ops_report | watch | watch | Governance Operations Report |
| `reviews/HANDOFF-2026-06-15-ui-redesign-and-product-structure.md` | `HANDOFF-2026-06-15-ui-redesign-and-product-structure` | md | record | n/a | HANDOFF — UI Redesign & Product-Structure Change (for next session) |
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
| `reviews/MEETING-2026-06-18-self-improvement-cycle-sync.md` | `MEETING-2026-06-18-self-improvement-cycle-sync` | meeting | planned | planned | Self Improvement Cycle Sync |
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
| `reviews/PLAN-2026-06-19-operator-attention-graph-implementation.md` | `PLAN-2026-06-19-operator-attention-graph-implementation` | ui-implementation-plan | accepted | pass | Operator Attention Graph Implementation Plan |
| `reviews/PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final.json` | `PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final` | json | record | n/a | PLANNING-EVIDENCE-LINK-2026-06-10-task-ar-243-final |
| `reviews/PROPOSALS-2026-06-19-ui-ux-next-work.md` | `PROPOSALS-2026-06-19-ui-ux-next-work` | ui-ux-next-work-proposals | planned | watch | UI/UX Next Work Proposals 2026-06-19 |
| `reviews/RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8.json` | `RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8` | json | record | n/a | RELEASE-COUNCIL-GATE-2026-06-09-v0.1.8 |
| `reviews/RELEASE-COUNCIL-GATE-2026-06-13-v0.2.0.json` | `RELEASE-COUNCIL-GATE-2026-06-13-v0.2.0` | json | record | n/a | RELEASE-COUNCIL-GATE-2026-06-13-v0.2.0 |
| `reviews/RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8.json` | `RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8` | json | record | n/a | RELEASE-EXECUTION-GATE-2026-06-09-v0.1.8 |
| `reviews/RELEASE-EXECUTION-GATE-2026-06-13-v0.2.0.json` | `RELEASE-EXECUTION-GATE-2026-06-13-v0.2.0` | json | record | n/a | RELEASE-EXECUTION-GATE-2026-06-13-v0.2.0 |
| `reviews/RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8.json` | `RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8` | json | record | n/a | RELEASE-READINESS-SUMMARY-2026-06-09-v0.1.8 |
| `reviews/RELEASE-READINESS-SUMMARY-2026-06-10-task-ar-223-root-current.json` | `RELEASE-READINESS-SUMMARY-2026-06-10-task-ar-223-root-current` | json | record | n/a | RELEASE-READINESS-SUMMARY-2026-06-10-task-ar-223-root-current |
| `reviews/RELEASE-READINESS-SUMMARY-2026-06-13-v0.2.0.json` | `RELEASE-READINESS-SUMMARY-2026-06-13-v0.2.0` | json | record | n/a | RELEASE-READINESS-SUMMARY-2026-06-13-v0.2.0 |
| `reviews/RELEASE-VERSION-CONSISTENCY-STEWARD.json` | `RELEASE-VERSION-CONSISTENCY-STEWARD` | json | record | n/a | RELEASE-VERSION-CONSISTENCY-STEWARD |
| `reviews/REPORT-2026-06-17-self-improvement-maturity.md` | `REPORT-2026-06-17-self-improvement-maturity` | md | record | watch | Self Improvement Maturity Report 2026-06-17 |
| `reviews/REPORT-2026-06-17-self-improvement-remediation-delta.md` | `REPORT-2026-06-17-self-improvement-remediation-delta` | md | record | watch | Self Improvement Remediation Delta 2026-06-17 |
| `reviews/REPORT-2026-06-18-self-improvement-maturity.md` | `REPORT-2026-06-18-self-improvement-maturity` | md | record | pass | Self Improvement Maturity Report 2026-06-18 |
| `reviews/REPORT-2026-06-19-ui-ux-cycle.md` | `REPORT-2026-06-19-ui-ux-cycle` | report | planned | n/a | UI/UX Cycle Report 2026-06-19 |
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
| `reviews/RETRO-2026-06-10-agent-runtime-governance-ops.md` | `RETRO-2026-06-10-agent-runtime-governance-ops` | retro | watch | watch | RETRO-2026-06-10 agent runtime governance ops |
| `reviews/RETRO-2026-06-14-agent-runtime-process-integrity.md` | `RETRO-2026-06-14-agent-runtime-process-integrity` | retro | watch | watch | RETRO 2026-06-14 — Process Integrity (verification / merge / compound-review-retro) |
| `reviews/RETRO-2026-06-14-knowledge-stack.md` | `RETRO-2026-06-14-knowledge-stack` | retro | watch | watch | RETRO 2026-06-14 — Agent knowledge stack (#1–#4) |
| `reviews/RETRO-2026-06-17-self-improvement-cycle.md` | `RETRO-2026-06-17-self-improvement-cycle` | retro | record | n/a | RETRO 2026-06-17 - Self Improvement Cycle |
| `reviews/RETRO-2026-06-18-self-improvement-cycle.md` | `RETRO-2026-06-18-self-improvement-cycle` | retro | record | n/a | RETRO 2026-06-18 - Self Improvement Cycle |
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
| `reviews/REVIEW-2026-06-18-knowledge-graph-corpus-expansion.md` | `REVIEW-2026-06-18-knowledge-graph-corpus-expansion` | md | record | pass | Knowledge Graph Corpus Expansion |
| `reviews/REVIEW-2026-06-18-llm-wiki-preservation-branch-deferred.md` | `REVIEW-2026-06-18-llm-wiki-preservation-branch-deferred` | md | accepted | n/a | LLM-Wiki Preservation Branch Deferred |
| `reviews/REVIEW-2026-06-18-llm-wiki-registration-current-line.md` | `REVIEW-2026-06-18-llm-wiki-registration-current-line` | md | record | pass | LLM-Wiki Registration Current-Line Integration |
| `reviews/REVIEW-2026-06-18-llm-wiki-worktree-preservation-closeout.md` | `REVIEW-2026-06-18-llm-wiki-worktree-preservation-closeout` | review | pass | n/a | LLM-Wiki Worktree Preservation Closeout |
| `reviews/REVIEW-2026-06-18-monitored-role-artifact-evidence.md` | `REVIEW-2026-06-18-monitored-role-artifact-evidence` | md | record | pass | Monitored Role Artifact Evidence |
| `reviews/REVIEW-2026-06-18-self-improvement-cycle.md` | `REVIEW-2026-06-18-self-improvement-cycle` | md | record | pass | Self Improvement Cycle 2026-06-18 |
| `reviews/REVIEW-2026-06-18-self-improvement-owner-state-alignment.md` | `REVIEW-2026-06-18-self-improvement-owner-state-alignment` | md | record | pass | Self Improvement Owner State Alignment |
| `reviews/REVIEW-2026-06-18-stop-hook-session-scope-quoted-payload.md` | `REVIEW-2026-06-18-stop-hook-session-scope-quoted-payload` | md | record | pass | Stop Hook Session Scope Quoted Payload Guard |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-assetization-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-assetization-registration` | md | record | pass | Design System Assetization Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-component-patterns-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-component-patterns-registration` | md | record | pass | Design System Component Patterns Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-debt-consolidation-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-debt-consolidation-registration` | md | record | pass | Design System Debt Consolidation Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-governance-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-governance-registration` | md | record | pass | Design System Governance Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-served-asset-split-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-served-asset-split-registration` | md | record | pass | Design System Served Asset Split Registration |
| `reviews/REVIEW-2026-06-18-taskset-ar-design-system-token-debt-registration.md` | `REVIEW-2026-06-18-taskset-ar-design-system-token-debt-registration` | md | record | pass | Design System Token Debt Registration |
| `reviews/REVIEW-2026-06-18-wiki-page-api-envelope.md` | `REVIEW-2026-06-18-wiki-page-api-envelope` | md | record | pass | Wiki Page API Envelope |
| `reviews/REVIEW-2026-06-18-wiki-page-view.md` | `REVIEW-2026-06-18-wiki-page-view` | md | record | pass | Wiki Page View |
| `reviews/REVIEW-2026-06-18-wiki-search-ask.md` | `REVIEW-2026-06-18-wiki-search-ask` | md | record | pass | Wiki Search And Ask |
| `reviews/REVIEW-2026-06-19-stop-hook-silent-success-regression.md` | `REVIEW-2026-06-19-stop-hook-silent-success-regression` | md | record | pass | Stop Hook Silent Success Regression |
| `reviews/REVIEW-2026-06-19-taskset-ar-operator-attention-graph-registration.md` | `REVIEW-2026-06-19-taskset-ar-operator-attention-graph-registration` | md | record | pass | Operator Attention Graph Registration |
| `reviews/REVIEW-2026-06-19-taskset-ar-ui-ux-cycle-automation-registration.md` | `REVIEW-2026-06-19-taskset-ar-ui-ux-cycle-automation-registration` | md | record | pass | UI UX Cycle Automation Registration |
| `reviews/REVIEW-2026-06-19-taskset-ar-ui-ux-cycle-automation-t3-replan-after-conductor.md` | `REVIEW-2026-06-19-taskset-ar-ui-ux-cycle-automation-t3-replan-after-conductor` | review | accepted | replan | UI/UX Cycle Automation T3 Replan After Conductor |
| `reviews/REVIEW-2026-06-19-taskset-ar-ui-ux-cycle-automation-t3-replan-after-review-planning.md` | `REVIEW-2026-06-19-taskset-ar-ui-ux-cycle-automation-t3-replan-after-review-planning` | review | accepted | replan | UI/UX Cycle Automation T3 Replan After Review Planning |
| `reviews/REVIEW-2026-06-19-taskset-ar-ui-ux-design-direction-rfc-registration.md` | `REVIEW-2026-06-19-taskset-ar-ui-ux-design-direction-rfc-registration` | md | record | pass | UI UX Design Direction RFC Registration |
| `reviews/RFC-2026-06-19-ui-ux-design-direction.md` | `RFC-2026-06-19-ui-ux-design-direction` | ui-ux-design-direction-rfc | accepted | pass | UI/UX Design Direction RFC 2026-06-19 |
| `reviews/RSI-PLANNING-TASKSET-VERIFY.json` | `RSI-PLANNING-TASKSET-VERIFY` | json | record | n/a | RSI-PLANNING-TASKSET-VERIFY |
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
| `reviews/SEMINAR-2026-06-18-self-improvement-cadence.md` | `SEMINAR-2026-06-18-self-improvement-cadence` | meeting | planned | planned | Self Improvement Cadence Seminar |
| `reviews/SEMINAR-2026-06-19-ui-ux-design-direction.md` | `SEMINAR-2026-06-19-ui-ux-design-direction` | ui-ux-design-direction-seminar | accepted | pass | UI/UX Design Direction Seminar 2026-06-19 |
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
| `reviews/VERIFY-2026-06-18-task-ar-593-20260618234500.json` | `VERIFY-2026-06-18-task-ar-593-20260618234500` | json | record | n/a | VERIFY-2026-06-18-task-ar-593-20260618234500 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735.json` | `VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-578-001-20260618125735 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300.json` | `VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-579-001-20260618143300 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000.json` | `VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-580-001-20260618150000 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500.json` | `VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-581-001-20260618153500 |
| `reviews/VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000.json` | `VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000` | json | record | n/a | VERIFY-2026-06-18-unit-task-ar-582-001-20260618161000 |
| `reviews/VERIFY-2026-06-19-operator-attention-graph-implementation.json` | `VERIFY-2026-06-19-operator-attention-graph-implementation` | json | record | n/a | VERIFY-2026-06-19-operator-attention-graph-implementation |
| `reviews/VERIFY-2026-06-19-task-ar-583-20260619003823.json` | `VERIFY-2026-06-19-task-ar-583-20260619003823` | json | record | n/a | VERIFY-2026-06-19-task-ar-583-20260619003823 |
| `reviews/VERIFY-2026-06-19-task-ar-584-20260619011843.json` | `VERIFY-2026-06-19-task-ar-584-20260619011843` | json | record | n/a | VERIFY-2026-06-19-task-ar-584-20260619011843 |
| `reviews/VERIFY-2026-06-19-task-ar-584-root-integration-20260619013817.json` | `VERIFY-2026-06-19-task-ar-584-root-integration-20260619013817` | json | record | n/a | VERIFY-2026-06-19-task-ar-584-root-integration-20260619013817 |
| `reviews/VERIFY-2026-06-19-task-ar-594-20260619031224.json` | `VERIFY-2026-06-19-task-ar-594-20260619031224` | json | record | n/a | VERIFY-2026-06-19-task-ar-594-20260619031224 |
| `reviews/VERIFY-2026-06-19-task-ar-595-20260619073554.json` | `VERIFY-2026-06-19-task-ar-595-20260619073554` | json | record | n/a | VERIFY-2026-06-19-task-ar-595-20260619073554 |
| `reviews/VERIFY-2026-06-19-task-ar-596-20260619080600.json` | `VERIFY-2026-06-19-task-ar-596-20260619080600` | json | record | n/a | VERIFY-2026-06-19-task-ar-596-20260619080600 |
| `reviews/VERIFY-2026-06-19-task-ar-596-closeout-20260619080337.json` | `VERIFY-2026-06-19-task-ar-596-closeout-20260619080337` | json | record | n/a | VERIFY-2026-06-19-task-ar-596-closeout-20260619080337 |
| `reviews/VERIFY-2026-06-19-task-ar-597-root-integration-20260619021833.json` | `VERIFY-2026-06-19-task-ar-597-root-integration-20260619021833` | json | record | n/a | VERIFY-2026-06-19-task-ar-597-root-integration-20260619021833 |
| `reviews/VERIFY-2026-06-19-task-ar-598-20260619015334.json` | `VERIFY-2026-06-19-task-ar-598-20260619015334` | json | record | n/a | VERIFY-2026-06-19-task-ar-598-20260619015334 |
| `reviews/VERIFY-2026-06-19-task-ar-598-root-integration-20260619021304.json` | `VERIFY-2026-06-19-task-ar-598-root-integration-20260619021304` | json | record | n/a | VERIFY-2026-06-19-task-ar-598-root-integration-20260619021304 |
| `reviews/VERIFY-2026-06-19-task-ar-599-20260619023818.json` | `VERIFY-2026-06-19-task-ar-599-20260619023818` | json | record | n/a | VERIFY-2026-06-19-task-ar-599-20260619023818 |
| `reviews/VERIFY-2026-06-19-task-ar-600-20260619082941.json` | `VERIFY-2026-06-19-task-ar-600-20260619082941` | json | record | n/a | VERIFY-2026-06-19-task-ar-600-20260619082941 |
| `reviews/VERIFY-2026-06-19-task-ar-601-20260619084352.json` | `VERIFY-2026-06-19-task-ar-601-20260619084352` | json | record | n/a | VERIFY-2026-06-19-task-ar-601-20260619084352 |
| `reviews/VERIFY-2026-06-19-task-ar-602-20260619090000.json` | `VERIFY-2026-06-19-task-ar-602-20260619090000` | json | record | n/a | VERIFY-2026-06-19-task-ar-602-20260619090000 |
| `reviews/VERIFY-2026-06-19-unit-task-ar-596-001-20260619012500.json` | `VERIFY-2026-06-19-unit-task-ar-596-001-20260619012500` | json | record | n/a | VERIFY-2026-06-19-unit-task-ar-596-001-20260619012500 |
| `reviews/VERIFY-2026-06-19-unit-task-ar-597-001-20260619002525.json` | `VERIFY-2026-06-19-unit-task-ar-597-001-20260619002525` | json | record | n/a | VERIFY-2026-06-19-unit-task-ar-597-001-20260619002525 |
| `reviews/VERIFY-2026-06-19-unit-task-ar-600-001-20260619082323.json` | `VERIFY-2026-06-19-unit-task-ar-600-001-20260619082323` | json | record | n/a | VERIFY-2026-06-19-unit-task-ar-600-001-20260619082323 |
| `reviews/VERIFY-2026-06-19-unit-task-ar-600-001-20260619082349.json` | `VERIFY-2026-06-19-unit-task-ar-600-001-20260619082349` | json | record | n/a | VERIFY-2026-06-19-unit-task-ar-600-001-20260619082349 |
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
| `reviews/W4B-2026-06-19-TASK-AR-583.md` | `W4B-2026-06-19-TASK-AR-583` | md | accepted | n/a | W4B Independent Verification - TASK-AR-583 |
| `reviews/W4B-2026-06-19-TASK-AR-584.md` | `W4B-2026-06-19-TASK-AR-584` | md | record | n/a | W4B Verification - TASK-AR-584 UI Pattern Renderers |
| `reviews/W4B-2026-06-19-TASK-AR-593.md` | `W4B-2026-06-19-TASK-AR-593` | w4b-independent-verification | record | pass | TASK-AR-593 W4b Independent Verification |
| `reviews/W4B-2026-06-19-TASK-AR-594.md` | `W4B-2026-06-19-TASK-AR-594` | md | record | pass | W4B TASK-AR-594 Independent Verification |
| `reviews/W4B-2026-06-19-TASK-AR-595.md` | `W4B-2026-06-19-TASK-AR-595` | md | record | pass | TASK-AR-595 W4b Independent Verification |
| `reviews/W4B-2026-06-19-TASK-AR-596.md` | `W4B-2026-06-19-TASK-AR-596` | w4b-independent-verification | record | pass | TASK-AR-596 W4b Independent Verification |
| `reviews/W4B-2026-06-19-TASK-AR-597.md` | `W4B-2026-06-19-TASK-AR-597` | md | record | pass | TASK-AR-597 W4b Independent Verification |
| `reviews/W4B-2026-06-19-TASK-AR-598.md` | `W4B-2026-06-19-TASK-AR-598` | md | record | pass | TASK-AR-598 W4b Independent Verification |
| `reviews/W4B-2026-06-19-TASK-AR-599.md` | `W4B-2026-06-19-TASK-AR-599` | md | record | pass | TASK-AR-599 W4b Independent Verification |
| `reviews/W4B-2026-06-19-TASK-AR-600.md` | `W4B-2026-06-19-TASK-AR-600` | w4b-independent-verification | accepted | pass | W4B Independent Verification - TASK-AR-600 |
| `reviews/W4B-2026-06-19-TASK-AR-601.md` | `W4B-2026-06-19-TASK-AR-601` | w4b-independent-verification | accepted | pass | W4B Independent Verification - TASK-AR-601 |
| `reviews/W4B-2026-06-19-TASK-AR-602.md` | `W4B-2026-06-19-TASK-AR-602` | w4b-independent-verification | accepted | pass | W4B Independent Verification - TASK-AR-602 |
| `reviews/W4B-2026-06-19-UNIT-TASK-AR-596-001.md` | `W4B-2026-06-19-UNIT-TASK-AR-596-001` | md | accepted | pass | W4B Independent Verification - UNIT-TASK-AR-596-001 |

## Risks / Blockers
- Risk: this index proves coverage, not semantic correctness of each evidence file.

## Next Steps
- Run `python scripts/evidence_index_generator.py --write` after adding new reviews.
- Run `python scripts/evidence_index_generator.py --check` before closeout.
