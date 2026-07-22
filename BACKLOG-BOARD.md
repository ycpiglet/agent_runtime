---
type: backlog_board
id: BACKLOG-BOARD-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [backlog, decision-board, owner-brief, action-board]
generated_at: 2026-07-22T23:01:19+09:00
task_count: 281
open_count: 23
completed_count: 258
task_set_count: 4
completed_task_set_count: 48
---

# Backlog Decision Board

## Bottom Line
- Summary: `23` open or active tasks; `258` completed tasks are archived from this live board.
- Routing rule: choose a task set first, then sort priority, cost, and difficulty inside that task set.

## Signal
- Status: Action `20` / Ask `2` / Review `0` / Later `1` / Done `258`.
- Task Sets: `4` active workflows; `48` completed workflows are hidden from the live action board.
- Key Point: Restored prior `ACT / REVIEW / ASK / DEFER` backlog as clearer `Action / Review / Ask / Later` lanes.
- Key Point: Every task includes difficulty, cost, value, importance, team, and agent.

## Insight
- Cause: Format drift recurs when report style is prose-only and not generated or gated.
- Fix: Backlog board is now generated from task metadata and checked by an executable format gate.
- UX: Owner view stays concise, sortable, and machine-readable.

## Decision
- Decision: Use this board as the Owner-facing backlog view.
- Action owner: Agents execute `Action`; Owner resolves `Ask`; reviewers inspect `Review`.
- Task-set rule: Group by related workflow first; sort priority, cost, and difficulty only inside each task set.
- Format rule: Preserve `Bottom Line / Signal / Insight / Decision` before tables.

## Action Board

- Board rule: task sets are the primary panes of work. Completed tasks and fully completed task sets are archived automatically.

### Merge Truth Keeper (`TASKSET-AR-AUTO-MERGE-INTEGRITY`)

- Flow: Close downstream BUG-014 with deterministic remote read-back.
- Progress: `0/1` done; `1` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-600` | INIT-AR-AUTO-MERGE-INTEGRITY | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-600/UNIT-TASK-AR-600-001.md | planned | Action | P1 | High | Medium | 1h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | Make auto_merge execute fail closed when GitHub rejects a merge and preserve success… |

### Console Overhaul P0 — Trust & Hygiene (`TASKSET-AR-CONSOLE-OVERHAUL-P0`)

- Flow: 결정 비종속 quick-win 묶음. 신선도 배지·캐시 사각지대 해소, 홈 요약 위계 정리, 프론트 위생(죽은 코드·아이콘·i18n·다크베이스·칸반), 데이터 위생(타임스탬프 게이트·actuals/rework 자동화), 세션 delta·throughput 전달 씨앗, REPORTING-FORMAT/OPS 계약 봉합, requirements-lint·NEEDS CLARIFICATION 마커 씨앗. 1–2주.
- Progress: `0/7` done; `7` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-603` | INIT-AR-CONSOLE-OVERHAUL-P0 | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-603/UNIT-TASK-AR-603-001.md | planned | Action | P1 | High | Low | 3h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | 홈 최상단의 시각적 소음과 위계 붕괴를 마크업/CSS 이동 수준에서 즉시 완화한다. |
| `TASK-AR-602` | INIT-AR-CONSOLE-OVERHAUL-P0 | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-602/UNIT-TASK-AR-602-001.md | planned | Action | P1 | High | Medium | 4h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | 콘솔·보드가 표시하는 데이터가 얼마나 오래되었는지 항상 보이게 하고, 감시 사각지대로 인한 최대 300초 stale을 없앤다. |
| `TASK-AR-605` | INIT-AR-CONSOLE-OVERHAUL-P0 | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-605/UNIT-TASK-AR-605-001.md | planned | Action | P1 | High | Medium | 5h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | 흐름 지표의 원료를 신뢰 가능하게 만든다: 타임스탬프 모순 차단, 수동 기입 폐지. |
| `TASK-AR-608` | INIT-AR-CONSOLE-OVERHAUL-P0 | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-608/UNIT-TASK-AR-608-001.md | planned | Action | P1 | High | Medium | 6h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | 요구 명확화·측정 검증 게이트의 기계적 토대를 심어 P1 승격 전 캘리브레이션 데이터를 모은다. |
| `TASK-AR-606` | INIT-AR-CONSOLE-OVERHAUL-P0 | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-606/UNIT-TASK-AR-606-001.md | planned | Ask | P2 | Medium | Low | 3h/1000tok | Low | 6 | agent-runtime-core | lead-engineer | Owner/agent decision | 이미 있는 데이터를 Owner에게 전달하는 최소 경로를 심는다. |
| `TASK-AR-607` | INIT-AR-CONSOLE-OVERHAUL-P0 | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-607/UNIT-TASK-AR-607-001.md | planned | Action | P2 | Medium | Low | 3h/1000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 신설 스킬(/clarify·/quiz)이 등재될 canonical surface를 먼저 정상화한다. |
| `TASK-AR-604` | INIT-AR-CONSOLE-OVERHAUL-P0 | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-604/UNIT-TASK-AR-604-001.md | planned | Action | P2 | Medium | Medium | 5h/1000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | P1 화면 작업 전에 저위험 단건 결함들을 정리해 소음을 제거한다. |

### Console Overhaul P1 — Core Structure (`TASKSET-AR-CONSOLE-OVERHAUL-P1`)

- Flow: attention 단일 정본화, 홈 Decision Screenfit 완성(verdict 배지+어텐션 큐+집계 스트립+흐름 타일), renderAll 해체, /clarify 인터뷰 게이트+EARS, 요구-검증-증거 3자 추적성, W4c 이해도 퀴즈 게이트 승격+held-out, Owner 승인 위험 티어링, FLOW-DIGEST 주간 자동+actor 스탬프+Ownership Concentration. 1–2개월. Phase 0 완료가 전제.
- Progress: `0/8` done; `8` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-609` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Action | P1 | High | Medium | 6h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | 보드 Rollups 휴리스틱과 콘솔 attention_inbox를 하나의 모듈로 통합해 두 표면이 다른 현황을 말하는 구조를 원천 차단하고, watch… |
| `TASK-AR-615` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Ask | P1 | High | Medium | 7h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Owner/agent decision | 저위험 승인을 council 위임으로 돌려 퀴즈/체크포인트로 늘어나는 Owner 접점을 상쇄한다. |
| `TASK-AR-613` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Action | P1 | High | Medium | 8h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | acceptance criterion에 ID를 부여하고 검증 명령과 매핑해 dangling(검증 없는 요구/요구 없는 검증)을 기계 적발한다. |
| `TASK-AR-610` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Action | P1 | High | High | 12h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | 스크롤 없이 5초 내 '개입 필요 여부'에 예/아니오로 답하는 단일 화면을 완성한다. |
| `TASK-AR-612` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Action | P1 | High | High | 12h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | 엔지니어링 요구에 대해 모호성을 탐지하고 불일치 지점만 인터뷰해 합의된 EARS 수용 기준을 강제한다. |
| `TASK-AR-614` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Action | P1 | High | High | 14h/1000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | diff를 이해했는지 pre-PR 단계에서 독립 출제자가 퀴즈로 검증하고, 통과 못 하면 teach-back으로 반복 학습시킨다. |
| `TASK-AR-611` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Action | P2 | Medium | High | 10h/1000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 매 4초 37개 렌더 함수 전량 재실행을 활성 뷰+콕핏 선택 렌더로 바꾸고 4s/8s/15s+SSE 4중 경로를 단일 디스패처로 통합한다. |
| `TASK-AR-616` | INIT-AR-CONSOLE-OVERHAUL-P1 | PROJECT-AGENT-RUNTIME | - | planned | Action | P2 | Medium | High | 10h/1000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 흐름 인사이트를 주간 다이제스트로 자동 전달하고, 주체별 점유를 측정 가능하게 만들어 독박을 지표로 확인한다. |

### Console Overhaul P2 — Structure Complete (`TASKSET-AR-CONSOLE-OVERHAUL-P2`)

- Flow: 프론트 물리 파일 분리(빌드리스), IA 재프루닝 2.0(관제 6허브+drawer)+확장기 산출물 정산+VISION.md 갱신, 상태 전이 이벤트 로그 실체화(JSONL+샤딩+하트비트), 실패 패턴 압축 파이프라인, 축3 패턴군 UI 통합(InterviewPanel·QuizGate 카드), orchestrator 권한 3분할, 에이전트 상호검증 debate 확장. 2개월+. Phase 0/1 안착이 전제.
- Progress: `0/7` done; `7` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-619` | INIT-AR-CONSOLE-OVERHAUL-P2 | PROJECT-AGENT-RUNTIME | - | planned | Action | P2 | Medium | Medium | 8h/1000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 설계됐으나 없는 agents/runtime/events/*.jsonl을 훅 체인이 생산하게 해 단계별 체류시간·병목·stall을 관측한다. |
| `TASK-AR-618` | INIT-AR-CONSOLE-OVERHAUL-P2 | PROJECT-AGENT-RUNTIME | - | planned | Action | P2 | Medium | High | 14h/1000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 35개 뷰를 관제 6허브(Home/Work/Agents/Records/Ops/Search)+drawer로 재편하고, 확장기 산출물 존치/폐기를 정산하며,… |
| `TASK-AR-620` | INIT-AR-CONSOLE-OVERHAUL-P2 | PROJECT-AGENT-RUNTIME | - | planned | Action | P3 | Low | Medium | 7h/1000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 게이트 실패·W4b 반려·VERIFY 실패를 원인/파일 기준 클러스터링해 top recurring failure를 뽑아 regression으로 전환한다. |
| `TASK-AR-621` | INIT-AR-CONSOLE-OVERHAUL-P2 | PROJECT-AGENT-RUNTIME | - | planned | Action | P3 | Low | High | 12h/1000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 1-4~1-6에서 확정된 데이터 계약(INTERVIEW/QUIZ 스키마)을 콘솔에 1급 컴포넌트로 통합한다. |
| `TASK-AR-622` | INIT-AR-CONSOLE-OVERHAUL-P2 | PROJECT-AGENT-RUNTIME | - | planned | Action | P3 | Low | High | 12h/1000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | lead-engineer에 집중된 독박을 분해해 planner(W1)와 integrator(W5)를 우선 실체화하고 산출물 크기를 비례화한다. |
| `TASK-AR-623` | INIT-AR-CONSOLE-OVERHAUL-P2 | PROJECT-AGENT-RUNTIME | - | planned | Action | P3 | Low | High | 12h/1000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 사람 퀴즈 장치를 에이전트 간 상호검증으로 확장해 설명자-심문자-심판 3역 debate 구조를 도입한다. |
| `TASK-AR-617` | INIT-AR-CONSOLE-OVERHAUL-P2 | PROJECT-AGENT-RUNTIME | - | planned | Later | P2 | Medium | High | 16h/1000tok | Low | 5 | agent-runtime-core | lead-engineer | Wait for dependency | 파이썬 문자열 3종에 내장된 16,800줄 프론트를 static/console/ 실파일 + 네이티브 ES modules로 분리해 대규모 작업을 diff/… |

## Archived Task Sets

- Archive rule: completed task sets stay out of the live Action Board but remain visible as workflow-level completion evidence.
| Task Set | Flow | Progress | Evidence |
|---|---|---:|---|
| Context Cartographer (`TASKSET-AR-CONTEXT-KNOWLEDGE`) | Project context, source routing, and reusable knowledge structure. | `7/7` done | `7` completed task files archived |
| Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`) | Offline evals, live review, correction loops, and traceable validation. | `7/7` done | `7` completed task files archived |
| Migration Archivist (`TASKSET-AR-MIGRATION-PARITY`) | Legacy-source parity, migration evidence, and skill/hook/script provenance. | `6/6` done | `6` completed task files archived |
| Release Steward (`TASKSET-AR-RELEASE-STEWARD`) | Version decisions, release closeout, and consistency checks. | `9/9` done | `9` completed task files archived |
| Console Operator (`TASKSET-AR-UI-CONSOLE`) | Runtime UI console surfaces, command paths, and observability views. | `7/7` done | `7` completed task files archived |
| Planning Architect (`TASKSET-AR-RSI-PLANNING`) | Bounded recursive self-improvement, planning scans, and proposal review. | `10/10` done | `10` completed task files archived |
| Evidence-to-Proposal Operator (`TASKSET-AR-RSI-OPERATING-SYSTEM`) | Evidence inboxes, failure casebooks, proposal quality metrics, council review, and bounded apply gates. | `9/9` done | `9` completed task files archived |
| Progress Scout (`TASKSET-AR-PANE-PROGRESS`) | Pane/task-set progress, live continuity, claims, and resumable handoffs. | `5/5` done | `5` completed task files archived |
| Concurrency Steward (`TASKSET-AR-COLLAB-CONCURRENCY`) | Real-time pane collaboration, event replay, SSoT ownership, and conflict gates. | `6/6` done | `6` completed task files archived |
| Multi-Pane Auditor (`TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE`) | Live pane census, process compliance, event enforcement, role coverage, drift normalization, and assurance UI. | `7/7` done | `7` completed task files archived |
| Closeout Automation Steward (`TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION`) | Session baseline capture, dirty-intake routing, archive/issue preservation, and closeout skill/hook enforcement. | `5/5` done | `5` completed task files archived |
| Governance Operator (`TASKSET-AR-GOVERNANCE-OPS`) | Waiver burn-down, lifecycle cleanup, runtime asset usage, sync enforcement, and verification hygiene. | `7/7` done | `7` completed task files archived |
| Identity Steward (`TASKSET-AR-TASK-IDENTITY`) | Collision-proof task identity, UUID metadata, lifecycle timestamps, and recovery visibility. | `4/4` done | `4` completed task files archived |
| Design Operator (`TASKSET-AR-UI-DESIGN-SYSTEM`) | Agent Runtime UI research, design-system guidance, and console visual implementation. | `7/7` done | `7` completed task files archived |
| Interface Stylist (`TASKSET-AR-UI-DESIGN-IMPLEMENTATION`) | Active UI design implementation work that applies the accepted design system across runtime panes. | `7/7` done | `7` completed task files archived |
| Repo Custodian (`TASKSET-AR-REPO-HYGIENE`) | Working-tree cleanup, backlog cycle hygiene, and handoff publication. | `6/6` done | `6` completed task files archived |
| Feedback Analyst (`TASKSET-AR-OPS-FEEDBACK-ANALYSIS`) | Owner feedback intake, enterprise-wide structure/vision analysis, and follow-up planning records. | `4/4` done | `4` completed task files archived |
| Vision Integrator (`TASKSET-AR-VISION-GAP-CLOSURE`) | Legacy independence, A2A messaging, multi-agent RBAC, loop hardening, live eval, skill packaging, realtime UI, and doc traceability. | `10/10` done | `10` completed task files archived |
| Console Experience Architect (`TASKSET-AR-UI-UX-V2`) | Notion-like light theme, sidebar IA, sort/filter/density patterns, taskset-first views, org chart, roadmap, live presence, comms, and taskset-scope guard. | `9/9` done | `9` completed task files archived |
| Platform Builder (`TASKSET-AR-UI-PLATFORM-EXTENSIONS`) | Taskset CRUD, dependencies/timeline, custom properties/automation, attachments, import/export, search, calendar, state-machine viewer, team workload, notifications, ops dashboard, gamification, and workspace extensibility. | `13/13` done | `13` completed task files archived |
| World Builder (`TASKSET-AR-UI-LIVING-CONSOLE`) | Idea vault with resurfacing loop, drag-in meeting room, direct-manipulation layer, progression system with guardrails, 2D office map, and webhook-first external notifications. | `6/6` done | `6` completed task files archived |
| Project Workbreaker (`TASKSET-AR-PM-OPERATING-SYSTEM`) | Project-to-unit hierarchy, worker-ready specs, model-tier routing, WIP controls, dispatcher scope stops, and PM verification gates. | `9/9` done | `9` completed task files archived |
| Pitch Alchemist (`TASKSET-AR-DOC-TO-PLAN`) | Document-to-plan intake pipeline, Paperclip gap adoption, actuals capture, and multi-factor evaluation/sorting. | `3/3` done | `3` completed task files archived |
| Work Taxonomist (`TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE`) | Initiative vocabulary, collision-free task registration, shared backlog deconfliction, and unit-readiness migration. | `6/6` done | `6` completed task files archived |
| Agent Identity Contract (`TASKSET-AR-AGENT-IDENTITY-CONTRACT`) | Add role/instance/display identity records, spawn provenance, and attribution gates for multi-agent work. | `1/1` done | `1` completed task files archived |
| Work Metadata Analyst (`TASKSET-AR-WORK-METADATA-ANALYTICS`) | Conversation-to-work traceability, Work Item metadata, Explorer roll-ups, query/export, agent attribution, and stale verification evidence. | `6/6` done | `6` completed task files archived |
| Wave Conductor (`TASKSET-AR-PARALLEL-WAVE-EXECUTION`) | Claim-time footprint conflict gate, wave dispatcher with cascade/parallel modes, integrator merge queue, and claim-first enforcement. | `10/10` done | `10` completed task files archived |
| Ops Ergonomics (`TASKSET-AR-OPS-ERGONOMICS`) | Make the 500-series infrastructure easy to operate: session-start W0 dashboard hook, trigger-based skills for wave/merge/verify/work-analytics/release, asset registry entries, and an ops command reference. | `3/3` done | `3` completed task files archived |
| Host Liaison (`TASKSET-AR-HOST-FEEDBACK-INTAKE`) | Treat host (autofolio) dogfooding feedback as first-class input: intake/triage, blind-Delphi council/seminar deliberation with diversity + Owner-boundary guardrails, decision reply-back to issues, plus the feedback-derived footprint-gate, self-eval/RSI fitness, host-fit, and open-bug candidates whose adoption the first deliberation decides. | `7/7` done | `7` completed task files archived |
| Store Architect (`TASKSET-AR-WORK-STORE-RESTRUCTURE`) | Stop the board from dumping the archive and reviews from accumulating unbounded: board attention-lanes (Triage/Active/Rollup) + extracted archive manifest, reviews date-shard + compacted index, classifier ordinal as canonical human ID with cosmetic TASK-AR-NNN gaps, UUIDv7/ULID stable keys, a manifest-first derived read-index + repo perf config, and a triage intake status. Single store + status field + views; no lifecycle directories. | `6/6` done | `6` completed task files archived |
| Decision Cartographer (`TASKSET-AR-UNIFIED-DECISION-CONSOLE`) | A decision/operations-optimized console over a typed entity catalog of every artifact (plan/review/issue/pr/git-log/branch/skill/council/seminar/work-items/waves/state/history): catalog model + manifest, universal command palette + cross-entity search, entity detail + backlinks, activity/provenance timeline + audit, faceted saved views + rollups + needs-attention inbox, live SCM surface, and governance-document surface. | `7/7` done | `7` completed task files archived |
| Maturity Steward (`TASKSET-AR-PRODUCT-MATURITY-UPLIFT`) | Close product-maturity gaps from the UI/quality assessment: end-to-end browser tests (Playwright), responsive layout, form validation + error UX, accessibility uplift, SSE real-time updates, i18n hardening, claim_reaper concurrency stress, observability export, multi-host claim safety, and owner-gated release automation. | `11/11` done | `11` completed task files archived |
| Org Conductor (`TASKSET-AR-AGENT-ORG-DELEGATION`) | Operationalize a Director->Lead->Worker+Reviewer agent org by reconciling the template org-suite (roles.yml/orchestrator/subagent/seminar) with the repo claim/wave execution: role/team/tier registry + owner normalization, lead taskset->unit decomposition, seam-aware + risk-based dispatch gate, orchestrator with a swappable WorkerBackend (sub-agents now, headless daemon later), a blind-Delphi persona-diversity deliberation layer, and a minimal org/state read-API. Research-grounded (Karpathy autonomy, gstack, multi-agent architectures, persona diversity); seam-aware parallelism + phased autonomy; token cost binding (~15x). | `6/6` done | `6` completed task files archived |
| Decision Cockpit (`TASKSET-AR-DECISION-FIRST-CONSOLE-IA`) | UI redesign #1: turn the 80-screen data-dump home into a decision-first cockpit whose hero is an Attention Inbox ('what needs me now', 6 signal groups derived from existing gates/records), prune nav 67->core 7 (+More), progressive disclosure (essentials on screen, detail on interaction), preserve the just-landed maturity behaviors (responsive/a11y/SSE/i18n/validation), and a KO/EN UI toggle. Incremental on the monolith; component/token extraction + 2.5D characters + insight graph are sub-project #3. | `7/7` done | `7` completed task files archived |
| Hook Portability Maintainer (`TASKSET-AR-HOOK-PORTABILITY-CLEANUP`) | Repair cross-platform hook commands, activate Git hook wiring, and verify a clean worktree lifecycle. | `1/1` done | `1` completed task files archived |
| Self Improvement Cadence (`TASKSET-AR-SELF-IMPROVEMENT-CADENCE`) | Detect low-frequency roles and runtime assets, run review/retro/meeting/seminar/compound/doc-steward/scribe cycles from evidence, and publish measurable maturity signals. | `3/3` done | `3` completed task files archived |
| Self Improvement Remediation (`TASKSET-AR-SELF-IMPROVEMENT-REMEDIATION-CYCLE`) | Burn down the first-cycle maturity blockers: scribe waiver debt, dormant monitored-role evidence, low-reuse runtime assets, and a follow-up measurable report. | `4/4` done | `4` completed task files archived |
| Business Operations Teams (`TASKSET-AR-BUSINESS-OPERATIONS-TEAMS`) | Extend the live org overlay and host scaffold with business-side teams for monetization, asset management, marketing, and compliant sales automation. | `1/1` done | `1` completed task files archived |
| Design System Governance (`TASKSET-AR-DESIGN-SYSTEM-GOVERNANCE`) | Publish a design-system operating contract, assetization classification workflow, UI/UX role split, and deterministic gate so new UI work can reuse components while still proposing new design directions. | `1/1` done | `1` completed task files archived |
| Design System Assetization (`TASKSET-AR-DESIGN-SYSTEM-ASSETIZATION`) | Move the first reusable UI primitives and domain patterns out of ui_console.py, add token scale assets, and tighten the design-system gate so existing baseline debt is tracked without blocking safe incremental refactors. | `1/1` done | `1` completed task files archived |
| Design System Component Patterns (`TASKSET-AR-DESIGN-SYSTEM-COMPONENT-PATTERNS`) | Add reusable Button/Card/Table/Modal-style component helpers and domain pattern helpers for TaskLane, ClaimCard, EvidencePanel, CommandBar, and StateMachinePanel, then wire representative console renderers to those helpers. | `1/1` done | `1` completed task files archived |
| Business Operating System (`TASKSET-AR-BUSINESS-OPERATING-SYSTEM`) | Extend business operations beyond team registration by adding operations/support and planning/strategy lanes plus a reusable operating packet for cross-agent business cycles. | `1/1` done | `1` completed task files archived |
| Design System Token Debt (`TASKSET-AR-DESIGN-SYSTEM-TOKEN-DEBT`) | Replace console typography, spacing, and radius CSS literals with token references, remove the remaining raw color literal, and make the design-system full audit prove that literal debt is no longer hidden in the console baseline. | `1/1` done | `1` completed task files archived |
| Design System Served Asset Split (`TASKSET-AR-DESIGN-SYSTEM-SERVED-ASSET-SPLIT`) | Physically separate the console's served HTML/CSS/JS string assets from the Python API/server module while preserving /, /app.css, and /app.js behavior. | `1/1` done | `1` completed task files archived |
| Design System Debt Consolidation (`TASKSET-AR-DESIGN-SYSTEM-DEBT-CONSOLIDATION`) | Consolidate transitional spacing/radius px-alias tokens into a designed semantic scale, and promote remaining view-specific JS renderers into stable pattern modules, without re-introducing raw literals. | `2/2` done | `2` completed task files archived |
| Noncritical Release Auto-Execution (`TASKSET-AR-RELEASE-AUTO-NONCRITICAL`) | Fix the stale release execution gate (parameterize the hardcoded v0.1.8) and wire a cadence-bound auto-release path that runs the agent-council vote, gates, tag, and push for noncritical releases on green main CI, while keeping major/breaking/critical releases Owner-gated. Correct the release-conductor skill doc to match the implemented tier rule. | `2/2` done | `2` completed task files archived |
| Visual Asset Adoption (`TASKSET-AR-VISUAL-ASSET-ADOPTION`) | Implement the research-backed visual upgrade: DiceBear CC0 seeded agent avatars with role accents; Dagre+d3-force graph rendering for dependency/state-machine/live-agent views; Geist OFL fonts; Lucide icons; unDraw state illustrations; Radix+Carbon data-viz palette tokens and sparklines. Permissive-only, no-build, self-hosted, token-driven, landed experimental. | `4/4` done | `4` completed task files archived |
| Visual System Integration & Verification (`TASKSET-AR-VISUAL-SYSTEM-INTEGRATION`) | Wire the new visual components into every relevant live view, boot-verify the served console, fix integration gaps, and run a WCAG AA + responsive pass on the new visual system. Permissive, no-build, token-driven. | `2/2` done | `2` completed task files archived |

## Rollups
- Overview-first: this board is an attention surface. Bulk archives are summarized here as counts + pointers, not dumped inline (TASK-AR-533).
- Needs attention: `2` — triage awaiting `0`, owner-decision (Ask) `2` (TASK-AR-538).
- Triage: `0` awaiting accept/defer.
- Active: `23` open across `4` task sets (see Action Board above).
- Throughput (7d): `1` tasks completed in the last 7 days (TASK-AR-606).
- Archived task sets: `48` (see Archived Task Sets above).
- Archived task files: `258` — see `ARCHIVE-INDEX.md`.

## Risks / Blockers
- Format drift risk: backlog output must not collapse into a plain task list.
- Metadata gap risk: missing team/agent/value fields reduce Owner decision quality.
- Gate gap risk: prose rules are insufficient without an executable format check.

## Next Steps
- Run `python scripts/backlog_board.py --write` after task frontmatter changes.
- Run `python scripts/owner_doc_format_gate.py BACKLOG-BOARD.md` before sharing Owner-facing backlog/report docs.
- Keep `task_set_id` in every task frontmatter so panes can claim related workflow bundles without reclassifying from prose.
- Promote missing task metadata into frontmatter when repeated inference is needed.
- Use completed task files as archival evidence; do not render them in the live action board unless an explicit archive view is added.

## Tags / References
- tags: backlog, action-board, owner-brief, decision-support
- references: `BACKLOG.md`, `STATUS.md`, `agents/lead_engineer/tasks/*.md`
