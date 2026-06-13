---
type: backlog_board
id: BACKLOG-BOARD-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [backlog, decision-board, owner-brief, action-board]
generated_at: 2026-06-13
task_count: 186
open_count: 35
completed_count: 151
task_set_count: 5
completed_task_set_count: 22
---

# Backlog Decision Board

## Bottom Line
- Summary: `35` open or active tasks; `151` completed tasks are archived from this live board.
- Routing rule: choose a task set first, then sort priority, cost, and difficulty inside that task set.

## Signal
- Status: Action `30` / Ask `4` / Review `0` / Later `1` / Done `151`.
- Task Sets: `5` active workflows; `22` completed workflows are hidden from the live action board.
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

### Console Experience Architect (`TASKSET-AR-UI-UX-V2`)

- Flow: Notion-like light theme, sidebar IA, sort/filter/density patterns, taskset-first views, org chart, roadmap, live presence, comms, and taskset-scope guard.
- Progress: `0/9` done; `9` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-320` | - | - | - | planned | Action | P1 | High | Medium | 6h/5000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 기본 테마를 Notion형 라이트로 전환하고 기존 Linear 다크 토큰을 Dark Mode 옵션으로 보존한다. |
| `TASK-AR-328` | - | - | - | planned | Action | P1 | High | Medium | 6h/5000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 특정 taskset 실행을 지시했을 때 해당 taskset 완료 후 scope 밖 작업으로 이탈하지 않고 정지·보고하도록 런타임 정책으로 강제한다 (Ow… |
| `TASK-AR-321` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 9개 수평 탭을 접이식 좌측 사이드바(Home / WORK / AGENTS / COMMS / RECORDS / OPS 그룹)로 전환해 V2 뷰 확장을 수… |
| `TASK-AR-324` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | TEAMS/ORG/roles 데이터로 조직도 트리를 렌더링하고, 에이전트 카드를 온라인 RPG 길드 멤버처럼 상태가 살아있는 프레즌스로 보여준다. |
| `TASK-AR-322` | - | - | - | planned | Action | P1 | High | High | 10h/8000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 모든 리스트 뷰(task/agent/event/message/evidence)에 Notion/Linear형 정렬·필터·그룹·검색 바와 간략히/자세히 밀도… |
| `TASK-AR-323` | - | - | - | planned | Ask | P1 | High | High | 10h/8000tok | Low | 6 | agent-runtime-core | lead-engineer | Owner/agent decision | task 평면 나열 대신 taskset 단위로 묶인 직관적 작업 뷰를 기본 진입점으로 만들고, Owner가 진행 중 흐름에 task를 안전하게 삽입할 수… |
| `TASK-AR-325` | - | - | - | planned | Action | P2 | Medium | Medium | 6h/5000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Vision → Milestone/Release → Taskset 3계층을 한 뷰에서 보여줘 고수준 방향과 실제 진행률을 연결한다. |
| `TASK-AR-327` | - | - | - | planned | Ask | P2 | Medium | High | 10h/8000tok | Low | 5 | agent-runtime-core | lead-engineer | Owner/agent decision | 에이전트 간 대화를 Slack/Discord처럼 채널/스레드로 관전하고, Owner가 UI에서 meeting/seminar를 소집할 수 있게 한다. |
| `TASK-AR-326` | - | - | - | planned | Action | P2 | Medium | High | 12h/9000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 에이전트/업무/메시지가 온라인 RPG처럼 실시간으로 살아 움직이는 감각을 SSE 이벤트 스트림과 라이브 그래프로 구현한다. |

### Platform Builder (`TASKSET-AR-UI-PLATFORM-EXTENSIONS`)

- Flow: Taskset CRUD, dependencies/timeline, custom properties/automation, attachments, import/export, search, calendar, state-machine viewer, team workload, notifications, ops dashboard, gamification, and workspace extensibility.
- Progress: `0/13` done; `13` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-332` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 사진/문서를 task·메시지에 드래그드롭/붙여넣기로 첨부하고, 미리보기·다운로드할 수 있게 한다 (Notion/Slack/Jira 모델). |
| `TASK-AR-334` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | task/taskset/메시지/이벤트/evidence/reviews 문서를 한 검색창에서 풀텍스트로 찾고 즉시 이동한다 (Notion 검색 + Slack… |
| `TASK-AR-337` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | task/taskset을 개인 에이전트가 아닌 팀/역할 단위로 배정하고, 에이전트·팀별 부하를 히트맵으로 보여준다 (Jira 컴포넌트 + Asana Wo… |
| `TASK-AR-329` | - | - | - | planned | Ask | P1 | High | High | 10h/8000tok | Low | 6 | agent-runtime-core | lead-engineer | Owner/agent decision | Owner가 UI에서 taskset을 직접 만들고, task를 넣고 빼고, 일괄 편집할 수 있게 한다 (Linear Projects / Notion DB… |
| `TASK-AR-330` | - | - | - | planned | Action | P1 | High | High | 10h/8000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | task 계층(서브태스크)과 의존성(blocks/blocked-by)을 데이터 모델로 정식화하고 타임라인(Gantt)·의존 그래프로 시각화한다. |
| `TASK-AR-333` | - | - | - | planned | Action | P2 | Medium | Medium | 6h/5000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | taskset/보드/이벤트를 표준 포맷으로 내보내고, 외부 목록을 task로 일괄 가져올 수 있게 한다 (Notion/Jira 모델). |
| `TASK-AR-336` | - | - | - | planned | Action | P2 | Medium | Medium | 6h/5000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | `agents/project/STATE-MACHINES.yml`의 라이프사이클(task/claim/role)을 인터랙티브 그래프로 보여주고, 선택한 ta… |
| `TASK-AR-338` | - | - | - | planned | Action | P2 | Medium | Medium | 8h/6000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 중요한 변화(blocked, 승인 대기, 마감 임박, 멘션)를 인앱 알림 인박스로 모으고, 채널에 멘션·핀·리액션을 더한다 (Slack + Linear… |
| `TASK-AR-339` | - | - | - | planned | Action | P2 | Medium | Medium | 8h/6000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 운영 지표를 Grafana/Sentry형 대시보드로 상시 노출한다: 토큰/비용 추이, eval 점수, 게이트 pass/watch/block 보드, tas… |
| `TASK-AR-331` | - | - | - | planned | Action | P2 | Medium | High | 10h/8000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Notion형 커스텀 속성과 Monday/ClickUp형 "when X then Y" 자동화 규칙, Linear형 트리아지 큐를 제공한다. |
| `TASK-AR-335` | - | - | - | planned | Action | P2 | Medium | High | 10h/8000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 마일스톤/회의/완료 이력/예약 실행을 캘린더 뷰로 통합하고, taskset 디스패치를 예약·반복 실행할 수 있게 한다 (Notion Calendar/Mo… |
| `TASK-AR-340` | - | - | - | planned | Action | P3 | Low | Medium | 8h/6000tok | Low | 4 | agent-runtime-core | lead-engineer | Execute next | 콘솔에 생동감을 더하는 애니메이션/이펙트와 RPG형 게임화 요소를 토글 가능한 폴리시 레이어로 추가한다 (기본은 차분한 진지 모드). |
| `TASK-AR-341` | - | - | - | planned | Action | P3 | Low | High | 10h/8000tok | Low | 4 | agent-runtime-core | lead-engineer | Execute next | 멀티 호스트 프로젝트(agent_runtime, autofolio 등)를 Notion 워크스페이스처럼 전환하고, 대시보드 위젯 확장 포인트와 KR/EN… |

### World Builder (`TASKSET-AR-UI-LIVING-CONSOLE`)

- Flow: Idea vault with resurfacing loop, drag-in meeting room, direct-manipulation layer, progression system with guardrails, 2D office map, and webhook-first external notifications.
- Progress: `0/6` done; `6` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-360` | - | - | - | planned | Ask | P1 | High | Medium | 6h/5000tok | Low | 6 | agent-runtime-core | lead-engineer | Owner/agent decision | 기각/보류 아이디어를 폐기하지 않고 보존·재발굴하는 체계를 RSI 운영 원칙으로 정착시킨다 (Owner 통찰: 진화 시 과거를 잊지 않고 주기적으로 재평… |
| `TASK-AR-361` | - | - | - | planned | Action | P1 | High | High | 12h/9000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 사이드탭의 회의실 공간에 에이전트를 마우스로 끌어다 넣고, 주제/태스크를 선택하면 참여 에이전트들이 의견을 주고받는 회의를 실행한다. |
| `TASK-AR-362` | - | - | - | planned | Action | P2 | Medium | Medium | 8h/6000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | hover 미리보기와 드래그앤드롭을 콘솔 전역의 1급 상호작용 동사로 표준화한다 (Notion peek + Discord 접근성 DnD 패턴). |
| `TASK-AR-363` | - | - | - | planned | Action | P2 | Medium | Medium | 8h/6000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 프로젝트의 성숙도를 진화하는 캐릭터처럼 측정·표시한다: 프로젝트 Lv.N(누적 경험), 사업 단계 칭호(garage→seed→startup→scaleup… |
| `TASK-AR-365` | - | - | - | planned | Action | P2 | Medium | Medium | 8h/6000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | 작업 이벤트(완료/차단/승인 대기)를 사용자가 쓰는 메신저로 내보낸다 — LangSmith 패턴(범용 웹훅 + 채널 레시피, 집계 윈도우 기반)을 채택. |
| `TASK-AR-364` | - | - | - | planned | Action | P3 | Low | High | 12h/9000tok | Low | 4 | agent-runtime-core | lead-engineer | Execute next | 실제 회사 같은 2D 맵에 에이전트를 배치해 한눈에 조직 활동을 보여준다 (Smallville/Generative Agents 패턴 — arXiv 230… |

### Pitch Alchemist (`TASKSET-AR-DOC-TO-PLAN`)

- Flow: Document-to-plan intake pipeline, Paperclip gap adoption, actuals capture, and multi-factor evaluation/sorting.
- Progress: `0/3` done; `3` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-367` | - | - | - | planned | Action | P1 | High | Medium | 6h/5000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 비전이 동일한 오픈소스 Paperclip(github.com/paperclipai/paperclip, MIT)의 기능 중 agent_runtime에 없는… |
| `TASK-AR-368` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | 예상치(est_*)만 있는 현 체계에 실측치를 더해, task/taskset을 우선순위·난이도·예상/실제 토큰·예상/실제 시간·부서 등 다요소로 정렬·필… |
| `TASK-AR-366` | - | - | - | planned | Later | P1 | High | Critical | 16h/12000tok | Low | 6 | agent-runtime-core | lead-engineer | Wait for dependency | pitch deck/기획서/아이디어 문서(PPT, PDF, Word, HTML, md)를 넣으면 시스템이 스스로 분석해 plan을 짜고 실현 가능한 ta… |

### Work Taxonomist (`TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE`)

- Flow: Initiative vocabulary, collision-free task registration, shared backlog deconfliction, and unit-readiness migration.
- Progress: `2/6` done; `4` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-372` | INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE | PROJECT-AGENT-RUNTIME-PM-OS | - | in_progress | Action | P1 | High | High | 12h/9000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | Provide one structured registration command path so planners stop hand-editing board… |
| `TASK-AR-371` | INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE | PROJECT-AGENT-RUNTIME-PM-OS | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Remove `BACKLOG.md` as a top-of-file shared manual registration hotspot while preserv… |
| `TASK-AR-373` | INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE | PROJECT-AGENT-RUNTIME-PM-OS | - | planned | Action | P3 | Low | Medium | 6h/5000tok | Low | 5 | governance-loop | independent-auditor | Execute next | Make it visible which planned tasks are worker-ready and which still require planner… |
| `TASK-AR-374` | INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE | PROJECT-AGENT-RUNTIME-PM-OS | - | planned | Action | P3 | Low | Low | 8h/4000tok | Low | 4 | agent-runtime-core | lead-engineer | Execute next | Prove that the work hierarchy and registration conflict surfaces are actually closed… |

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
| Project Workbreaker (`TASKSET-AR-PM-OPERATING-SYSTEM`) | Project-to-unit hierarchy, worker-ready specs, model-tier routing, WIP controls, dispatcher scope stops, and PM verification gates. | `9/9` done | `9` completed task files archived |
| Agent Identity Contract (`TASKSET-AR-AGENT-IDENTITY-CONTRACT`) | Add role/instance/display identity records, spawn provenance, and attribution gates for multi-agent work. | `1/1` done | `1` completed task files archived |
| Work Metadata Analyst (`TASKSET-AR-WORK-METADATA-ANALYTICS`) | Conversation-to-work traceability, Work Item metadata, Explorer roll-ups, query/export, agent attribution, and stale verification evidence. | `6/6` done | `6` completed task files archived |
| Wave Conductor (`TASKSET-AR-PARALLEL-WAVE-EXECUTION`) | Claim-time footprint conflict gate, wave dispatcher with cascade/parallel modes, integrator merge queue, and claim-first enforcement. | `10/10` done | `10` completed task files archived |

## Archived Task Files

- Restore rule: completed tasks stay hidden from the live Action Board, but every completed task file remains visible here with identity and lifecycle metadata.
| Task | UID | Task Set | Status | registered_at | started_at | completed_at | updated_at | Summary |
|---|---|---|---|---|---|---|---|---|
| `TASK-AR-201` | `c3c2b9a3-a92…` | `TASKSET-AR-CONTEXT-KNOWLEDGE` | completed | 2026-06-09 | 2026-06-09T09:20:00+09:00 | 2026-06-11T11:50:00+09:00 | 2026-06-11T11:50:00+09:00 | `agent_runtime`가 프로젝트별 요청을 처리할 때 source-tier, owner, 접근권한, freshness를 기준으로 지식 소스를 라우팅… |
| `TASK-AR-202` | `f4057c67-bc4…` | `TASKSET-AR-CONTEXT-KNOWLEDGE` | completed | 2026-06-11 | 2026-06-11T11:45:00+09:00 | 2026-06-11T11:50:00+09:00 | 2026-06-11T11:50:00+09:00 | `runbook`를 재사용 가능한 숙련 프로세스로 표준화해, 질문 명확화-자료 검색-실행-적대적 검토-검증-기록 흐름을 에이전트가 강제하도록 한다. |
| `TASK-AR-204` | `d384f27a-407…` | `TASKSET-AR-CONTEXT-KNOWLEDGE` | completed | 2026-06-09 | 2026-06-09 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | 런타임의 스킬/런북 문서가 코드/데이터/스키마 변경과 동기화되지 않을 경우 릴리스가 차단되도록 한다. |
| `TASK-AR-214` | `ba4b73b4-634…` | `TASKSET-AR-CONTEXT-KNOWLEDGE` | completed | 2026-06-09 | 2026-06-09T10:20:00+09:00 | 2026-06-11T11:50:00+09:00 | 2026-06-11T11:50:00+09:00 | 질의 실행 전후의 `source_tier`, `owner`, `access`, `freshness`, `lineage`, `ambiguity`, `tra… |
| `TASK-AR-203` | `cb363212-ce9…` | `TASKSET-AR-CONTEXT-KNOWLEDGE` | completed | 2026-06-11 | 2026-06-11T11:45:00+09:00 | 2026-06-11T11:50:00+09:00 | 2026-06-11T11:50:00+09:00 | 지식창고 문서를 `빠른 참조, 차원 설명, 핵심 테이블, 주의사항/패턴, 상위 문맥 링크` 형식으로 표준화해 사람이 즉시 구조를 읽고 판단할 수 있게 한… |
| `TASK-AR-211` | `d477effb-70e…` | `TASKSET-AR-CONTEXT-KNOWLEDGE` | completed | 2026-06-11 | 2026-06-11T11:45:00+09:00 | 2026-06-11T11:50:00+09:00 | 2026-06-11T11:50:00+09:00 | 에이전트 런타임을 여러 프로젝트에서 공통 reuse할 때 프로젝트 고유의 vision/roadmap/조직/연결 문맥을 오버레이로 주입한다. |
| `TASK-AR-215` | `08b01bc0-2ee…` | `TASKSET-AR-CONTEXT-KNOWLEDGE` | completed | 2026-06-09 | 2026-06-09T11:00:00+09:00 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | 다른 프로젝트로 에이전트를 투입할 때 공용 런타임은 유지하고 오버레이만 교체해 vision, roadmap, 조직도, 팀, 링크, 협의기록을 즉시 맥락에… |
| `TASK-AR-205` | `fb3af52e-1ae…` | `TASKSET-AR-QUALITY-LOOP` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | 오프라인에서 정답 보유 영역은 구조화된 데이터셋으로 재현 가능한 평가를 수행하고, 90% 미만이면 릴리스를 막는다. |
| `TASK-AR-217` | `06b35d56-8b2…` | `TASKSET-AR-QUALITY-LOOP` | completed | 2026-06-09 | 2026-06-09 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `v0.1.8` 공개 후보(2026-07-02/07-09/07-16)를 가정한 `release-preflight`, 오프라인 90% 게이트, review… |
| `TASK-AR-243` | `97d57c17-96d…` | `TASKSET-AR-QUALITY-LOOP` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:22:00+09:00 | 2026-06-11T00:00:00+09:00 | Connect trace, grader, eval, correction, live-review, and A2A evidence to planning pr… |
| `TASK-AR-206` | `739ed262-4fe…` | `TASKSET-AR-QUALITY-LOOP` | completed | 2026-06-11 | 2026-06-11 | 2026-06-10T22:04:00+09:00 | 2026-06-11T00:00:00+09:00 | 라이브 작업 종료 시 reviewer agent의 적대적 검토를 강제하고, 답변에 근거/태그를 붙인다. |
| `TASK-AR-207` | `44bcf47c-75b…` | `TASKSET-AR-QUALITY-LOOP` | completed | 2026-06-11 | 2026-06-11 | 2026-06-10T22:12:00+09:00 | 2026-06-11T00:00:00+09:00 | 채팅, 리뷰, 메시지에서 탐지된 오답/누락/모호성의 교정 제안을 자동 수집한다. |
| `TASK-AR-208` | `9e6f55b7-ad4…` | `TASKSET-AR-QUALITY-LOOP` | completed | 2026-06-11 | 2026-06-11 | 2026-06-10T22:20:00+09:00 | 2026-06-11T00:00:00+09:00 | 요청/리뷰/결정 이벤트를 추적 가능한 A2A 메시지 스키마로 관리해 멀티 에이전트/멀티 프로젝트 운영 안정성을 확보한다. |
| `TASK-AR-221` | `f1d2c4ec-6d9…` | `TASKSET-AR-QUALITY-LOOP` | completed | 2026-06-09 | 2026-06-09T18:00:00+09:00 | 2026-06-10T23:22:00+09:00 | 2026-06-11T00:00:00+09:00 | 에이전트 런타임을 한 번에 재사용 가능한 MVP/멀티 프로젝트 운영 구조로 정리한다. 공식 가이드(Claude/Codex/OpenAI 권고)에 맞추어 아… |
| `TASK-AR-209` | `914d9b65-a63…` | `TASKSET-AR-MIGRATION-PARITY` | completed | 2026-06-09 | 2026-06-13T10:10:00+09:00 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `레거시 전신 프로젝트`에서 `agent_runtime`로 이식할 때 누락·변형·의도적 제외 항목을 분리해, 다음 릴리스에서 추적 가능하게 증빙한다. |
| `TASK-AR-218` | `aa5a97ba-86b…` | `TASKSET-AR-MIGRATION-PARITY` | completed | 2026-06-09 | 2026-06-09T16:00:00+09:00 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `TASK-AR-216`/`TASK-AR-217` 판정 전제 조건을 위해 `레거시 전신 프로젝트` 이식 누락·변경 근거가 미정으로 남는 상태를 제거하고,… |
| `TASK-AR-224` | `330694dc-a51…` | `TASKSET-AR-MIGRATION-PARITY` | completed | 2026-06-19 | 2026-06-19 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `v0.1.8` 판정에서 공통 정합 규칙(공식 가이드 반영, migration 근거, 레거시 전신 프로젝트 이식 누락 처리)이 줄지 않게 동작하도록 공식… |
| `TASK-AR-213` | `8cf05d05-ae0…` | `TASKSET-AR-MIGRATION-PARITY` | completed | 2026-06-18 | 2026-06-18T09:30:00+09:00 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `레거시 전신 프로젝트` 이식에서 `skill / hook / script` 항목을 `kept/changed/deprecated/dropped/missi… |
| `TASK-AR-220` | `d447eec2-368…` | `TASKSET-AR-MIGRATION-PARITY` | completed | 2026-06-09 | 2026-06-10T09:15:00+09:00 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `레거시 전신 프로젝트`에서 `agent_runtime`으로 이동할 때 skill/hook/script 누락·변형·의도적 제외가 의도된 이유인지, 기술적… |
| `TASK-AR-212` | `cc5a29c5-ad5…` | `TASKSET-AR-MIGRATION-PARITY` | completed | 2026-06-11 | 2026-06-13T10:25:00+09:00 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `TASK-AR-209`의 마이그레이션 감사 결과를 재현 가능한 증거로 완결하고, 향후 release-block 규칙에 연결한다. |
| `TASK-AR-216` | `84debe84-e47…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-09 | 2026-06-09T13:00:00+09:00 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | `v0.1.7` 공개 판정의 미충족 항목을 `v0.1.8` 판정으로 안전하게 이관하고, 릴리스 보드가 읽는 하나의 `release-state` 체인으로… |
| `TASK-AR-210` | `a28ea57b-202…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-11 | 2026-06-12T09:30:00+09:00 | 2026-06-10T20:55:00+09:00 | 2026-06-11T00:00:00+09:00 | `v0.1.6`/`v0.1.7` 공개 판단을 근거 기반으로 고정하고, `v0.1.8` 판정(`07-02/07-09/07-16`)을 기준으로 release… |
| `TASK-AR-240` | `a82d6c89-997…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-10 | 2026-06-10T22:22:00+09:00 | 2026-06-10T22:50:00+09:00 | 2026-06-11T00:00:00+09:00 | Create a version and release consistency steward that checks release state, version s… |
| `TASK-AR-223` | `efce46d4-273…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-14 | 2026-06-14 | 2026-06-10T22:12:00+09:00 | 2026-06-11T00:00:00+09:00 | `agent_runtime`에서 모델/핵심 루틴 재작성 없이 프로젝트 투입 시 오버레이 교체만으로 공식 가이드(Claude/Codex/OpenAI) 정합… |
| `TASK-AR-219` | `bc4aeb9b-e59…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-09 | 2026-06-10T09:00:00+09:00 | 2026-06-10T22:24:00+09:00 | 2026-06-11T00:00:00+09:00 | 현재 로드맵 기준으로 `v0.1.8` 후보 공개 판단을 한 번 더 고정하고, Claude/Codex 계열 공식 권고(컨텍스트 우선순위, trace-gra… |
| `TASK-AR-225` | `046534c6-22d…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-09 | 2026-06-09 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Close the `release-preflight findings=358` blocker discovered by `TASK-AR-224` execut… |
| `TASK-AR-222` | `59a6a708-690…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-09 | 2026-06-09 | 2026-06-10T22:48:00+09:00 | 2026-06-11T00:00:00+09:00 | `v0.1.8` 1차 판정(2026-07-02)을 위해 요구사항 1~16 및 공식 권고를 하나의 판정 번들로 정합한다. 특히 `agent_runtime`… |
| `TASK-AR-509` | `734a1b79-485…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-12T22:42:24+09:00 | 2026-06-13T01:23:31+09:00 | 2026-06-13T02:30:00+09:00 | 2026-06-13T02:30:00+09:00 | 호스트 프로젝트(autofolio 등)가 agent_runtime 새 릴리스를 자동으로 인지하게 한다: 세션 시작 시 업스트림 최신 태그와 호스트 고정… |
| `TASK-AR-510` | `9da9903c-250…` | `TASKSET-AR-RELEASE-STEWARD` | completed | 2026-06-12T22:55:34+09:00 | 2026-06-13T01:33:44+09:00 | 2026-06-13T03:05:00+09:00 | 2026-06-13T03:05:00+09:00 | 릴리스 타이밍을 사람이 기억하는 대신 트리거가 감지하게 한다: 마지막 릴리스 태그 이후 누적 변경이 임계치를 넘거나 taskset closeout wav… |
| `TASK-AR-226` | `8fe1f6c1-1ec…` | `TASKSET-AR-UI-CONSOLE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Map the current `agent_runtime` state sources before building a web UI, so the UI rea… |
| `TASK-AR-227` | `808cdda2-38c…` | `TASKSET-AR-UI-CONSOLE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Expose a safe, read-first backend interface for the UI console, using runtime files a… |
| `TASK-AR-230` | `ea8b33bf-62d…` | `TASKSET-AR-UI-CONSOLE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Allow the user to control runtime work from the UI by sending prompts and lifecycle c… |
| `TASK-AR-229` | `9d3ec2a8-472…` | `TASKSET-AR-UI-CONSOLE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Let the UI manage tasks safely by sending changes through runtime APIs or a command o… |
| `TASK-AR-231` | `4862fdea-931…` | `TASKSET-AR-UI-CONSOLE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Make the UI trustworthy during long `/goal` runs by surfacing freshness, live event c… |
| `TASK-AR-228` | `1b4f4177-8cb…` | `TASKSET-AR-UI-CONSOLE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Build the first read-only web console so the user can see backlog, current work, agen… |
| `TASK-AR-232` | `bd41c885-08d…` | `TASKSET-AR-UI-CONSOLE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Add the post-MVP visualizations that make the runtime understandable as an agent orga… |
| `TASK-AR-234` | `3b6a93f7-451…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Define the planning loop contract and state machine for bounded recursive self-improv… |
| `TASK-AR-235` | `cdc49e24-448…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Implement a read-only planning scan that compares backlog, status, roadmap, task file… |
| `TASK-AR-236` | `c6b42720-2e6…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Add a proposal outbox and draft task writer so planning findings become inspectable p… |
| `TASK-AR-237` | `8ffebe48-326…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Connect the planning loop to safe triggers: cycle completion, task completion, schedu… |
| `TASK-AR-241` | `4ef77297-594…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Build a review/compound/retro synthesizer that reads historical tasks, reviews, compo… |
| `TASK-AR-238` | `e79087b1-0d5…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Add a UI Planner panel that shows planning scans, proposals, evidence, risk tier, rev… |
| `TASK-AR-239` | `575111ea-51a…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Implement approved proposal apply and verification so accepted planning proposals can… |
| `TASK-AR-244` | `8fbd6e5d-d87…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Add stability, budget, drift, and non-divergence guardrails for recursive planning lo… |
| `TASK-AR-242` | `2decefad-5dd…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Define an agent department and diversity council model so similar topics are reviewed… |
| `TASK-AR-245` | `47b6de8b-c38…` | `TASKSET-AR-RSI-PLANNING` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T22:56:04+09:00 | 2026-06-11T00:00:00+09:00 | Define the long-term C-mode promotion gate for bounded auto-planning and low-risk aut… |
| `TASK-AR-297` | `1570ec36-9aa…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-11T13:10:53+09:00 | 2026-06-11T13:12:23+09:00 | 2026-06-11T13:12:23+09:00 | Create the canonical place to capture trace, eval, grader, A2A, correction, review, r… |
| `TASK-AR-298` | `7b4e4dc4-915…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-11T13:14:53+09:00 | 2026-06-11T13:16:20+09:00 | 2026-06-11T13:16:20+09:00 | Make evaluation and verification evidence queryable instead of scattered across revie… |
| `TASK-AR-299` | `4a99d83d-eed…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | Convert scattered failure, compound, retro, and review notes into a single searchable… |
| `TASK-AR-300` | `6fd3e4b4-ee0…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | Define how normalized evidence becomes task, plan, doc, eval, release, or skill propo… |
| `TASK-AR-301` | `8a5e638a-7f0…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | Make the council layer measurable: different viewpoints should improve proposal quali… |
| `TASK-AR-303` | `5cccc334-b5c…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | Keep C-mode as a potential long-term department runtime without promoting it before B… |
| `TASK-AR-305` | `d273c1a0-c43…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | Close the A안 taskset only after the registries, casebook, proposal contract, council… |
| `TASK-AR-302` | `0f90a9b0-18f…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | Close the gap between A2A evidence fields existing in documents and an actual end-to-… |
| `TASK-AR-304` | `023a2874-3b9…` | `TASKSET-AR-RSI-OPERATING-SYSTEM` | completed | 2026-06-11T12:10:00+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | 2026-06-12T02:17:42+09:00 | Add the missing skill layer so future sessions follow the RSI operating process witho… |
| `TASK-AR-247` | `b025becb-046…` | `TASKSET-AR-PANE-PROGRESS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Create the fixed pane/task-set progress golden set before UI or enforcement changes. |
| `TASK-AR-250` | `35989583-b68…` | `TASKSET-AR-PANE-PROGRESS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Make task-set work user-friendly enough that a prompt like `taskset-quality-loop 진행해줘… |
| `TASK-AR-248` | `db637774-594…` | `TASKSET-AR-PANE-PROGRESS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10 | 2026-06-10 | Show pane and task-set progress in the runtime UI using phase, step counter, rough pe… |
| `TASK-AR-246` | `db571ed2-737…` | `TASKSET-AR-PANE-PROGRESS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Implement dispatcher helpers for safe parallel Codex/Claude work: one task per worktr… |
| `TASK-AR-249` | `5437aec8-572…` | `TASKSET-AR-PANE-PROGRESS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10 | 2026-06-10 | Enforce progress updates in task claims and continuity pointers so new panes can resu… |
| `TASK-AR-255` | `f65fb879-d50…` | `TASKSET-AR-COLLAB-CONCURRENCY` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:20:00+09:00 | 2026-06-10T23:20:00+09:00 | Run collaboration concurrency checks with the rest of the owner governance gate. |
| `TASK-AR-251` | `262e447d-0f0…` | `TASKSET-AR-COLLAB-CONCURRENCY` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:20:00+09:00 | 2026-06-10T23:20:00+09:00 | Record the conversation research on Google Docs/Slides, Figma, Notion, Firestore, Act… |
| `TASK-AR-252` | `c702cf3c-d50…` | `TASKSET-AR-COLLAB-CONCURRENCY` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:20:00+09:00 | 2026-06-10T23:20:00+09:00 | Add an append-only event stream for pane lifecycle and task-set coordination events. |
| `TASK-AR-253` | `485edce3-c9c…` | `TASKSET-AR-COLLAB-CONCURRENCY` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:20:00+09:00 | 2026-06-10T23:20:00+09:00 | Block worker pane attempts to write shared SSoT files directly. |
| `TASK-AR-254` | `1515a1ec-6b5…` | `TASKSET-AR-COLLAB-CONCURRENCY` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:20:00+09:00 | 2026-06-10T23:20:00+09:00 | Make task-set start create the missing task worktree before claim creation, preventin… |
| `TASK-AR-256` | `8188dea3-31d…` | `TASKSET-AR-COLLAB-CONCURRENCY` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:20:00+09:00 | 2026-06-10T23:20:00+09:00 | Expose pane collaboration events and task-set summaries through the UI state adapter. |
| `TASK-AR-285` | `49555bdd-520…` | `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE` | completed | 2026-06-11T01:45:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Count and classify live pane, claim, task-set, worktree, and event evidence in one re… |
| `TASK-AR-286` | `e1b6076f-bb1…` | `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE` | completed | 2026-06-11T01:45:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Verify whether plan, review, compound, retro, meeting, seminar, Ralph, scribe, and do… |
| `TASK-AR-287` | `326fe2d8-f5a…` | `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE` | completed | 2026-06-11T01:45:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Make pane lifecycle events mandatory enough that UI replay and audits can prove what… |
| `TASK-AR-288` | `3de2947c-1b6…` | `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE` | completed | 2026-06-11T01:45:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Track excluded, underused, waived, and lifecycle-stale agents across multi-pane colla… |
| `TASK-AR-291` | `b7cb44f9-75c…` | `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE` | completed | 2026-06-11T01:45:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Close the multi-pane assurance task set only after census, process, role, event, drif… |
| `TASK-AR-289` | `382b4490-69e…` | `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE` | completed | 2026-06-11T01:45:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Resolve or explain future heartbeat values, released-claim phase/progress drift, and… |
| `TASK-AR-290` | `2ce7f36f-3bd…` | `TASKSET-AR-MULTIPANE-RUNTIME-ASSURANCE` | completed | 2026-06-11T01:45:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Make multi-pane census, process compliance, role coverage, drift, and event replay vi… |
| `TASK-AR-292` | `76c8c0f6-2f0…` | `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION` | completed | 2026-06-11T02:30:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Define the canonical contract for session closeout, including how to separate baselin… |
| `TASK-AR-293` | `5dd9af8e-fbb…` | `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION` | completed | 2026-06-11T02:30:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Capture a compact baseline at session start so closeout can distinguish pre-existing… |
| `TASK-AR-294` | `21597a69-4e0…` | `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION` | completed | 2026-06-11T02:30:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Classify late dirty work and produce a safe route before any stash drop, branch delet… |
| `TASK-AR-295` | `b75fac0b-3f4…` | `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION` | completed | 2026-06-11T02:30:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Wire the baseline and dirty-intake scripts into session lifecycle hooks without addin… |
| `TASK-AR-296` | `eef9ec3b-5b4…` | `TASKSET-AR-SESSION-CLOSEOUT-AUTOMATION` | completed | 2026-06-11T02:30:00+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | 2026-06-11T11:53:49+09:00 | Package the closeout workflow as a reusable skill and verify the full taskset through… |
| `TASK-AR-257` | `278344d7-334…` | `TASKSET-AR-GOVERNANCE-OPS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:55:00+09:00 | 2026-06-10T23:55:00+09:00 | Register the remaining collaboration-governance, waiver, lifecycle, usage, sync, and… |
| `TASK-AR-258` | `f3096efc-ab5…` | `TASKSET-AR-GOVERNANCE-OPS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:55:00+09:00 | 2026-06-10T23:55:00+09:00 | Reduce explicit collaboration waivers by promoting safe root runtime capabilities and… |
| `TASK-AR-259` | `59a01025-c27…` | `TASKSET-AR-GOVERNANCE-OPS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:55:00+09:00 | 2026-06-10T23:55:00+09:00 | Normalize lifecycle evidence so released claims, heartbeats, active worktrees, and ta… |
| `TASK-AR-260` | `17f86f7a-f7d…` | `TASKSET-AR-GOVERNANCE-OPS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:55:00+09:00 | 2026-06-10T23:55:00+09:00 | Make developed skills, hooks, triggers, gates, and runtime scripts measurable for act… |
| `TASK-AR-261` | `38a4b41b-831…` | `TASKSET-AR-GOVERNANCE-OPS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:55:00+09:00 | 2026-06-10T23:55:00+09:00 | Prevent task progress from drifting away from backlog board, status, and next-session… |
| `TASK-AR-262` | `1da38bf4-98d…` | `TASKSET-AR-GOVERNANCE-OPS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:55:00+09:00 | 2026-06-10T23:55:00+09:00 | Separate root verification from generated-project template verification so broad test… |
| `TASK-AR-263` | `f8e9f655-d3e…` | `TASKSET-AR-GOVERNANCE-OPS` | completed | 2026-06-10 | 2026-06-10 | 2026-06-10T23:55:00+09:00 | 2026-06-10T23:55:00+09:00 | Publish a recurring governance operations report that turns watch/waived/unused/low-r… |
| `TASK-AR-20260611-001100-cf344293` | `cf344293-778…` | `TASKSET-AR-TASK-IDENTITY` | completed | 2026-06-11T00:11:00+09:00 | 2026-06-11T00:11:00+09:00 | 2026-06-11T00:11:00+09:00 | 2026-06-11T00:11:00+09:00 | Backfill registered, started, updated, and completed timestamps across canonical task… |
| `TASK-AR-20260611-001300-56389c0e` | `56389c0e-ba1…` | `TASKSET-AR-TASK-IDENTITY` | completed | 2026-06-11T00:13:00+09:00 | 2026-06-11T00:13:00+09:00 | 2026-06-11T00:13:00+09:00 | 2026-06-11T00:13:00+09:00 | Verify no task, plan, task set, identity, or board synchronization work was omitted. |
| `TASK-AR-20260611-001000-815e18ab` | `815e18ab-168…` | `TASKSET-AR-TASK-IDENTITY` | completed | 2026-06-11T00:10:00+09:00 | 2026-06-11T00:10:00+09:00 | 2026-06-11T00:10:00+09:00 | 2026-06-11T00:10:00+09:00 | Implement collision-proof task_uid allocation and owner governance enforcement. |
| `TASK-AR-20260611-001200-f2b67a5a` | `f2b67a5a-76b…` | `TASKSET-AR-TASK-IDENTITY` | completed | 2026-06-11T00:12:00+09:00 | 2026-06-11T00:12:00+09:00 | 2026-06-11T00:12:00+09:00 | 2026-06-11T00:12:00+09:00 | Expose task identity and lifecycle metadata through UI state and archived backlog boa… |
| `TASK-AR-264` | `9484fb10-d2b…` | `TASKSET-AR-UI-DESIGN-SYSTEM` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Completed the UI research synthesis and implementation plan for the Agent Runtime con… |
| `TASK-AR-265` | `db774f7c-204…` | `TASKSET-AR-UI-DESIGN-SYSTEM` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Published a project-specific UI design guide that maps the research result to concret… |
| `TASK-AR-266` | `c008f8b2-b12…` | `TASKSET-AR-UI-DESIGN-SYSTEM` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Applied the selected dark operator-console token system to the Agent Runtime UI shell… |
| `TASK-AR-267` | `a751c680-e52…` | `TASKSET-AR-UI-DESIGN-SYSTEM` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Restyled backlog lanes, task cards, agent cards, event cards, evidence cards, source… |
| `TASK-AR-268` | `8983774d-497…` | `TASKSET-AR-UI-DESIGN-SYSTEM` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Updated visual tokens and component styling so pass, warning, blocked, failed, active… |
| `TASK-AR-269` | `d927d484-7f3…` | `TASKSET-AR-UI-DESIGN-SYSTEM` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Kept the existing responsive layout, visible labels, status text, focus states, and m… |
| `TASK-AR-270` | `a7032c6f-439…` | `TASKSET-AR-UI-DESIGN-SYSTEM` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Closed the UI design task set with task records, design documentation, implementation… |
| `TASK-AR-278` | `1238e8f8-9a3…` | `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` | completed | 2026-06-11 | 2026-06-11 | 2026-06-11T02:48:39+09:00 | 2026-06-11T02:48:39+09:00 | Apply the accepted Linear-like operator-console design system to the top-level consol… |
| `TASK-AR-279` | `3cf6f3eb-bd8…` | `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` | completed | 2026-06-11 | 2026-06-11T04:51:27+09:00 | 2026-06-11T08:01:53+09:00 | 2026-06-11T08:01:53+09:00 | Make backlog lanes and task cards easier to scan for status, priority, owner, task se… |
| `TASK-AR-280` | `d9f3edb5-70e…` | `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` | completed | 2026-06-11 | 2026-06-11T08:42:47+09:00 | 2026-06-11T09:05:05+09:00 | 2026-06-11T09:05:05+09:00 | Make active agent state, claims, progress, and command safety boundaries visible in t… |
| `TASK-AR-281` | `082e33ce-bc3…` | `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` | completed | 2026-06-11 | 2026-06-11T10:17:46+09:00 | 2026-06-11T10:32:26+09:00 | 2026-06-11T10:32:26+09:00 | Make events, errors, evidence, and replay records look audit-ready and severity-aware. |
| `TASK-AR-283` | `d39df02e-7bf…` | `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` | completed | 2026-06-11 | 2026-06-11T12:16:38+09:00 | 2026-06-11T12:34:25+09:00 | 2026-06-11T12:34:25+09:00 | Keep the dark operator console usable on desktop and mobile without relying on color-… |
| `TASK-AR-284` | `539c16e9-2ff…` | `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` | completed | 2026-06-11 | 2026-06-11T12:45:13+09:00 | 2026-06-11T12:55:13+09:00 | 2026-06-11T12:55:13+09:00 | Close the active UI design implementation task set only after focused checks, Owner g… |
| `TASK-AR-282` | `3d7b5d8e-d81…` | `TASKSET-AR-UI-DESIGN-IMPLEMENTATION` | completed | 2026-06-11 | 2026-06-11T10:47:46+09:00 | 2026-06-11T10:59:38+09:00 | 2026-06-11T10:59:38+09:00 | Bring graph, state-machine, roadmap, planner, source, and write surfaces into the sam… |
| `TASK-AR-233` | `d475a04e-6c5…` | `TASKSET-AR-REPO-HYGIENE` | completed | 2026-06-10 | 2026-06-10 | 2026-06-11T00:00:00+09:00 | 2026-06-11T00:00:00+09:00 | Clean the current working tree through an intentional commit and push, then keep back… |
| `TASK-AR-511` | `bf47ce08-f7a…` | `TASKSET-AR-REPO-HYGIENE` | completed | 2026-06-12T23:15:32+09:00 | 2026-06-13T12:30:36+09:00 | 2026-06-13T13:20:00+09:00 | 2026-06-13T13:20:00+09:00 | 서로 다른 OS/LLM/페인에서 작업한 파일이 줄바꿈·인코딩 차이로 가짜 diff와 경고를 만드는 것을 차단한다. 현재 `.gitattributes`가… |
| `TASK-AR-520` | `bbb306dd-5fc…` | `TASKSET-AR-REPO-HYGIENE` | completed | 2026-06-13T02:54:38+09:00 | 2026-06-13T02:58:38+09:00 | 2026-06-13T08:10:00+09:00 | 2026-06-13T08:10:00+09:00 | taskset_work_gate judges BACKLOG-BOARD.md stale within minutes because the generator… |
| `TASK-AR-512` | `94b7763f-436…` | `TASKSET-AR-REPO-HYGIENE` | completed | 2026-06-12T23:15:32+09:00 | 2026-06-13T02:58:37+09:00 | 2026-06-13T07:50:00+09:00 | 2026-06-13T07:50:00+09:00 | 형상관리 산출물(branch/worktree/stash/PR/issue/claim)의 "지저분함"을 사람이 인지하기 전에 주기 점검 루프가 감지·보고·정… |
| `TASK-AR-521` | `ac308082-386…` | `TASKSET-AR-REPO-HYGIENE` | completed | 2026-06-13T02:54:38+09:00 | 2026-06-13T09:47:58+09:00 | 2026-06-13T13:20:00+09:00 | 2026-06-13T13:20:00+09:00 | Template owner_governance_gate.py is missing evidence_index_generator/context_knowled… |
| `TASK-AR-522` | `d947e814-6af…` | `TASKSET-AR-REPO-HYGIENE` | completed | 2026-06-13T02:54:38+09:00 | 2026-06-13T10:33:54+09:00 | 2026-06-13T13:50:00+09:00 | 2026-06-13T13:50:00+09:00 | Bundle of independently-verified small fixes: (1) work.py emits verification_status p… |
| `TASK-AR-306` | `9fc495d7-bfd…` | `TASKSET-AR-OPS-FEEDBACK-ANALYSIS` | completed | 2026-06-11T17:34:00+09:00 | 2026-06-11T16:30:00+09:00 | 2026-06-11T17:34:00+09:00 | 2026-06-11T17:34:00+09:00 | Owner 7개 지시(브랜치/스태시 정리, UI 적용, 플러그인/훅 정리, 레거시 전신 프로젝트 정리, 구조 분석, 비전 분석, 기록/등록)를 단일 세션… |
| `TASK-AR-309` | `d5458ef2-2dd…` | `TASKSET-AR-OPS-FEEDBACK-ANALYSIS` | completed | 2026-06-11T17:34:00+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-11 "UI 미반영" 사건의 두 원인(비-editable stale 설치, 장수 구버전 서버 프로세스)이 재발하지 않도록 가드 방안을 계획… |
| `TASK-AR-307` | `2457f407-5d4…` | `TASKSET-AR-OPS-FEEDBACK-ANALYSIS` | completed | 2026-06-11T17:34:00+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-11 전사 구조 분석에서 식별된 개선 항목을 Owner가 우선순위 결정할 수 있는 실행 계획으로 확정한다 (분석/계획 전용, 구현 없음). |
| `TASK-AR-308` | `0985351f-c25…` | `TASKSET-AR-OPS-FEEDBACK-ANALYSIS` | completed | 2026-06-11T17:34:00+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-12T02:08:54+09:00 | 2026-06-12T02:08:54+09:00 | Ralph/Loop Engineering, Multi-agent/A2A, 측정 가능한 평가·검증, backlog UI/task management, 추적… |
| `TASK-AR-310` | `9f5e2229-3d3…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-11T22:14:43+09:00 | 2026-06-11T23:01:07+09:00 | 2026-06-11T23:01:07+09:00 | 레거시 전신 프로젝트에 대한 라이브 의존을 모두 해소해 이관을 최종 마감하고, agent_runtime이 레거시 참조 없이 완전히 독립하도록 한다. |
| `TASK-AR-313` | `753d8012-6dd…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-11T23:16:07+09:00 | 2026-06-11T23:26:35+09:00 | 2026-06-11T23:26:35+09:00 | 광범위한 python 허용 목록을 정확한 명령 프로파일(ci/owner/research)로 좁혀 임의 코드 실행 경로를 제거한다. |
| `TASK-AR-311` | `6a155432-3a2…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-11T23:40:19+09:00 | 2026-06-12T00:02:26+09:00 | 2026-06-12T00:02:26+09:00 | 에이전트 간 통신을 태스크 상태/로그 추론 방식에서 명시적 메시지 패싱 API로 전환해 A2A 체인을 구조적으로 보장한다. |
| `TASK-AR-312` | `13d31d8a-bac…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-12T00:08:33+09:00 | 2026-06-12T00:19:40+09:00 | 2026-06-12T00:19:40+09:00 | 문서로만 정의된 역할 체계(TEAMS/ORG/diversity council)를 실제 2~3개 동시 에이전트 인스턴스 실행으로 증명하고, 역할별 쓰기 권… |
| `TASK-AR-314` | `616a4093-bef…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-12T00:37:16+09:00 | 2026-06-12T00:44:07+09:00 | 2026-06-12T00:44:07+09:00 | 리스 기반 클레임 원시 연산으로 다중 프로세스 환경의 중복 응답/소유권 경합을 구조적으로 차단한다. |
| `TASK-AR-316` | `e60e5407-f2b…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-12T00:55:55+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | skills/(session-closeout, taskset-dispatch)를 버전·트리거 조건·메타데이터를 갖춘 재사용 가능한 패키지로 만들어 다른… |
| `TASK-AR-315` | `ee3763c2-877…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | 결정적 계약 베이스라인(현 1.0 대체 통과)이 가리고 있는 실제 모델 출력 정확도(offline 0.6667 vs 목표 0.90) 격차를 provide… |
| `TASK-AR-319` | `6c03c440-54d…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | 368+개 reviews/ 증거를 수동 탐색에서 자동 색인/검증 체계로 전환해 문서 추적성을 규모에 견디게 만든다. |
| `TASK-AR-317` | `4ffc5085-45b…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | UI 콘솔을 읽기 전용 스냅샷 대시보드에서 운영 제어 표면으로 승격한다: 에이전트 루프 진행이 실시간 반영되고, 제안 승인/거절이 UI에서 가능해야 한다. |
| `TASK-AR-318` | `367a501a-c74…` | `TASKSET-AR-VISION-GAP-CLOSURE` | completed | 2026-06-11T17:58:45+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | 2026-06-12T02:02:59+09:00 | 이벤트/수정 기록을 나열에서 인과 체인 재생으로 승격해, 상태 변화를 프레임 단위로 거슬러 볼 수 있게 한다. |
| `TASK-AR-342` | `a9df4c1b-0cd…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Make `project -> taskset -> task -> unit` and short/mid/long horizon metadata a canon… |
| `TASK-AR-343` | `8fa333a3-328…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Create the detailed unit document shape that lower-cost implementation models can exe… |
| `TASK-AR-345` | `ece0f0d8-c21…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Add planner/worker/reviewer tier metadata and escalation triggers to task and unit re… |
| `TASK-AR-350` | `a6ec5d39-e11…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Add a taskset verification wrapper and Owner-facing closeout evidence for the PM oper… |
| `TASK-AR-344` | `53dc0739-dc3…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Block low-tier worker dispatch when task or unit records lack enough detail. |
| `TASK-AR-346` | `72489271-63b…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Extend taskset dispatch so a worker can claim one unit and must stop at the taskset/u… |
| `TASK-AR-347` | `815686ed-3b2…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Add Kanban-style WIP controls and flow signals for tasksets, teams, and worker units. |
| `TASK-AR-349` | `7e8741f0-87d…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Mirror the PM hierarchy, unit templates, schemas, and gates into generated host proje… |
| `TASK-AR-348` | `79254591-b67…` | `TASKSET-AR-PM-OPERATING-SYSTEM` | completed | 2026-06-11T19:50:16+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | 2026-06-12T01:38:36+09:00 | Render project/taskset/task/unit hierarchy without stuffing detailed instructions int… |
| `TASK-AR-369` | `9d171d09-6c3…` | `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE` | completed | 2026-06-12T08:17:54+09:00 | 2026-06-12T08:42:59+09:00 | 2026-06-12T09:04:46+09:00 | 2026-06-12T09:04:46+09:00 | Finish the terminology migration from ambiguous `project -> taskset -> task -> unit`… |
| `TASK-AR-370` | `5655d2cb-a03…` | `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE` | completed | 2026-06-12T08:17:54+09:00 | 2026-06-12T09:43:38+09:00 | 2026-06-12T11:06:57+09:00 | 2026-06-12T11:06:57+09:00 | Prevent concurrent panes from selecting the same human display ID before a task file… |
| `TASK-AR-375` | `fe4cf218-9eb…` | `TASKSET-AR-AGENT-IDENTITY-CONTRACT` | completed | 2026-06-12T14:50:00+09:00 | 2026-06-12T15:05:12+09:00 | 2026-06-12T15:25:40+09:00 | 2026-06-12T15:25:40+09:00 | Create durable instance-level identity records and a deterministic gate that rejects… |
| `TASK-AR-514` | `5b5f167a-3a1…` | `TASKSET-AR-WORK-METADATA-ANALYTICS` | completed | 2026-06-12T23:30:00+09:00 | 2026-06-13T01:33:45+09:00 | 2026-06-13T04:30:00+09:00 | 2026-06-13T04:30:00+09:00 | Owner/Claude/Codex planning discussions must map to review records, task records, boa… |
| `TASK-AR-517` | `da2e7699-1f7…` | `TASKSET-AR-WORK-METADATA-ANALYTICS` | completed | 2026-06-12T23:33:00+09:00 | 2026-06-13T02:45:16+09:00 | 2026-06-13T11:50:00+09:00 | 2026-06-13T11:50:00+09:00 | Turn Work Item metadata into queryable statistics, JSON/CSV export, and reusable save… |
| `TASK-AR-519` | `f9b99655-ff0…` | `TASKSET-AR-WORK-METADATA-ANALYTICS` | completed | 2026-06-12T23:35:00+09:00 | 2026-06-13T02:45:17+09:00 | 2026-06-13T11:20:00+09:00 | 2026-06-13T11:20:00+09:00 | Mark verification evidence stale when source files, commits, claims, or task records… |
| `TASK-AR-515` | `9c205ef4-f27…` | `TASKSET-AR-WORK-METADATA-ANALYTICS` | completed | 2026-06-12T23:31:00+09:00 | 2026-06-13T01:33:46+09:00 | 2026-06-13T02:55:00+09:00 | 2026-06-13T02:55:00+09:00 | Define and gate the Work Item metadata catalog for provenance, resolution, relationsh… |
| `TASK-AR-518` | `93485297-632…` | `TASKSET-AR-WORK-METADATA-ANALYTICS` | completed | 2026-06-12T23:34:00+09:00 | 2026-06-13T02:45:17+09:00 | 2026-06-13T08:40:00+09:00 | 2026-06-13T08:40:00+09:00 | Require instance_uid actor attribution across claims, A2A messages, evidence, closeou… |
| `TASK-AR-516` | `0d48b9fe-4c6…` | `TASKSET-AR-WORK-METADATA-ANALYTICS` | completed | 2026-06-12T23:32:00+09:00 | 2026-06-13T02:58:37+09:00 | 2026-06-13T09:10:00+09:00 | 2026-06-13T09:10:00+09:00 | Make initiative/taskset/task/unit progress and metadata visible through one Work Expl… |
| `TASK-AR-504` | `acd02367-581…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T18:51:54+09:00 | 2026-06-12T18:51:54+09:00 | 2026-06-12T18:55:00+09:00 | 2026-06-12T18:55:00+09:00 | 병렬 세션(codex/claude)이 서로의 미머지 변경을 모른 채 세운 계획이 merge 후 조용히 무효화되는 문제를 지연평가로 해결한다: 계획의 전제… |
| `TASK-AR-508` | `41f58968-7dc…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T21:53:22+09:00 | 2026-06-12T21:55:08+09:00 | 2026-06-12T22:15:00+09:00 | 2026-06-12T22:15:00+09:00 | dirty intake와 session baseline의 residue 보존 규칙이 `codex/*` 브랜치에 하드코딩되어 있어 `claude/*` 브랜… |
| `TASK-AR-503` | `4966fce3-64b…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T18:35:45+09:00 | 2026-06-13T01:33:43+09:00 | 2026-06-13T02:50:00+09:00 | 2026-06-13T02:50:00+09:00 | 워크트리 작업은 반드시 main 체크아웃에 활성 클레임을 먼저 남기고 시작하도록 강제한다. 클레임 없는 워크트리 작업은 보드/ui-console 양쪽에서… |
| `TASK-AR-500` | `15e90de2-ca8…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T18:35:45+09:00 | 2026-06-12T21:27:17+09:00 | 2026-06-13T01:55:00+09:00 | 2026-06-13T02:05:00+09:00 | 충돌 발견 시점을 merge-time(사후)에서 claim-time(사전)으로 옮긴다. 새 클레임 생성 시 활성 클레임들의 선언 footprint(`ta… |
| `TASK-AR-505` | `69f8bed3-e0d…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T21:15:09+09:00 | 2026-06-13T01:23:31+09:00 | 2026-06-13T02:25:00+09:00 | 2026-06-13T02:25:00+09:00 | 작업 수명주기의 W5(통합 후 정리) 단계를 실행 가능하게 만든다: merge 완료 + claim released 상태의 좀비 워크트리/브랜치를 검출하고… |
| `TASK-AR-507` | `2df22d07-cea…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T21:24:50+09:00 | 2026-06-13T08:37:43+09:00 | 2026-06-13T10:30:00+09:00 | 2026-06-13T10:30:00+09:00 | Owner 규칙 "작업자가 스스로 검증 금지, 항상 다른 에이전트가 검증"을 실행 가능하게 강제한다: claim release/closeout 시 ver… |
| `TASK-AR-506` | `25e129f5-2ad…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T21:15:09+09:00 | 2026-06-13T09:53:21+09:00 | 2026-06-13T12:40:00+09:00 | 2026-06-13T12:40:00+09:00 | 이번 taskset에만 수동 적용된 지연평가 규율(T0 스냅샷/T2 착수 체크)과 W0~W6 수명주기를 **모든 작업의 기본값**으로 만든다 — Owne… |
| `TASK-AR-513` | `7dcaf575-583…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T23:22:49+09:00 | 2026-06-13T01:23:31+09:00 | 2026-06-13T02:45:00+09:00 | 2026-06-13T02:45:00+09:00 | main 보드가 미머지 브랜치의 진행 상황을 모르는 인식 오류를 없앤다. Owner 보고(2026-06-12): "main의 백로그만 보면 아직 진행이… |
| `TASK-AR-501` | `cb503e0c-71f…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T18:35:45+09:00 | 2026-06-13T02:45:16+09:00 | 2026-06-13T09:30:00+09:00 | 2026-06-13T09:30:00+09:00 | planner가 unit 의존성 DAG를 topological wave로 분해하고, 디스패처가 같은 wave의 K개 unit에 대해 claim+workt… |
| `TASK-AR-502` | `59fda519-2e9…` | `TASKSET-AR-PARALLEL-WAVE-EXECUTION` | completed | 2026-06-12T18:35:45+09:00 | 2026-06-13T02:58:36+09:00 | 2026-06-13T08:20:00+09:00 | 2026-06-13T08:20:00+09:00 | 워커 브랜치의 main 합류를 단일 통합자(orchestrator)가 직렬 rebase-test-merge 큐로 처리해, 병렬 구현 기간에도 merge… |

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
