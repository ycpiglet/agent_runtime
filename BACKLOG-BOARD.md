---
type: backlog_board
id: BACKLOG-BOARD-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [backlog, decision-board, owner-brief, action-board]
generated_at: 2026-06-10
task_count: 46
open_count: 34
---

# Backlog Decision Board

## Bottom Line
- Summary: `46` total tasks; `34` open or active.
- Recommended next: `TASK-AR-205` - 오프라인에서 정답 보유 영역은 구조화된 데이터셋으로 재현 가능한 평가를 수행하고, 90% 미만이면 릴리스를 막는다.

## Signal
- Status: Action `27` / Ask `2` / Review `0` / Later `5` / Done `12`.
- Key Point: Restored prior `ACT / REVIEW / ASK / DEFER` backlog as clearer `Action / Review / Ask / Later` lanes.
- Key Point: Every task includes difficulty, cost, value, importance, team, and agent.

## Insight
- Cause: Format drift recurs when report style is prose-only and not generated or gated.
- Fix: Backlog board is now generated from task metadata and checked by an executable format gate.
- UX: Owner view stays concise, sortable, and machine-readable.

## Decision
- Decision: Use this board as the Owner-facing backlog view.
- Action owner: Agents execute `Action`; Owner resolves `Ask`; reviewers inspect `Review`.
- Format rule: Preserve `Bottom Line / Signal / Insight / Decision` before tables.

## Action Board

### Action

| Task | Status | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-205` | in_progress | P0 | Critical | Medium | 14h/2200tok | High | 11 | validation-team | qa | Execute next | 오프라인에서 정답 보유 영역은 구조화된 데이터셋으로 재현 가능한 평가를 수행하고, 90% 미만이면 릴리스를 막는다. |
| `TASK-AR-209` | in_progress | P0 | Critical | Medium | 12h/2200tok | High | 11 | governance-loop | independent-auditor | Execute next | `tag_manual`에서 `agent_runtime`로 이식할 때 누락·변형·의도적 제외 항목을 분리해, 다음 릴리스에서 추적 가능하게 증빙한다. |
| `TASK-AR-210` | in_progress | P0 | Critical | Medium | 12h/2000tok | High | 11 | agent-runtime-core | lead-engineer | Execute next | `v0.1.6`/`v0.1.7` 공개 판단을 근거 기반으로 고정하고, `v0.1.8` 판정(`07-02/07-09/07-16`)을 기준으로 release… |
| `TASK-AR-218` | in_progress | P0 | Critical | Medium | 12h/2400tok | High | 11 | governance-loop | independent-auditor | Execute next | `TASK-AR-216`/`TASK-AR-217` 판정 전제 조건을 위해 `tag_manual` 이식 누락·변경 근거가 미정으로 남는 상태를 제거하고,… |
| `TASK-AR-202` | planned | P0 | Critical | Medium | 10h/1700tok | Medium | 10 | agent-runtime-core | lead-engineer | Execute next | `runbook`를 재사용 가능한 숙련 프로세스로 표준화해, 질문 명확화-자료 검색-실행-적대적 검토-검증-기록 흐름을 에이전트가 강제하도록 한다. |
| `TASK-AR-217` | in_progress | P0 | Critical | High | 14h/2800tok | Medium | 10 | validation-team | qa | Execute next | `v0.1.8` 공개 후보(2026-07-02/07-09/07-16)를 가정한 `release-preflight`, 오프라인 90% 게이트, review… |
| `TASK-AR-223` | in_progress | P0 | Critical | Medium | 12h/2600tok | Medium | 10 | validation-team | qa | Execute next | `agent_runtime`에서 모델/핵심 루틴 재작성 없이 프로젝트 투입 시 오버레이 교체만으로 공식 가이드(Claude/Codex/OpenAI) 정합… |
| `TASK-AR-240` | planned | P0 | Critical | Medium | 12h/2200tok | Medium | 10 | agent-runtime-core | lead-engineer | Execute next | Create a version and release consistency steward that checks release state, version s… |
| `TASK-AR-206` | in_progress | P0 | Critical | Medium | 10h/1800tok | Medium | 9 | validation-team | qa | Execute next | 라이브 작업 종료 시 reviewer agent의 적대적 검토를 강제하고, 답변에 근거/태그를 붙인다. |
| `TASK-AR-207` | in_progress | P0 | Critical | Medium | 12h/1800tok | Medium | 9 | validation-team | qa | Execute next | 채팅, 리뷰, 메시지에서 탐지된 오답/누락/모호성의 교정 제안을 자동 수집한다. |
| `TASK-AR-208` | in_progress | P0 | Critical | Medium | 12h/1800tok | Medium | 9 | validation-team | qa | Execute next | 요청/리뷰/결정 이벤트를 추적 가능한 A2A 메시지 스키마로 관리해 멀티 에이전트/멀티 프로젝트 운영 안정성을 확보한다. |
| `TASK-AR-211` | in_progress | P0 | Critical | Medium | 16h/2200tok | Medium | 9 | project-context | doc-steward | Execute next | 에이전트 런타임을 여러 프로젝트에서 공통 reuse할 때 프로젝트 고유의 vision/roadmap/조직/연결 문맥을 오버레이로 주입한다. |
| `TASK-AR-212` | in_progress | P0 | Critical | Medium | 14h/2400tok | Medium | 9 | governance-loop | independent-auditor | Execute next | `TASK-AR-209`의 마이그레이션 감사 결과를 재현 가능한 증거로 완결하고, 향후 release-block 규칙에 연결한다. |
| `TASK-AR-213` | in_progress | P0 | Critical | Medium | 12h/2400tok | Medium | 9 | governance-loop | independent-auditor | Execute next | `tag_manual` 이식에서 `skill / hook / script` 항목을 `kept/changed/deprecated/dropped/missin… |
| `TASK-AR-219` | in_progress | P0 | Critical | Medium | 10h/1800tok | Medium | 9 | agent-runtime-core | lead-engineer | Execute next | 현재 로드맵 기준으로 `v0.1.8` 후보 공개 판단을 한 번 더 고정하고, Claude/Codex 계열 공식 권고(컨텍스트 우선순위, trace-gra… |
| `TASK-AR-220` | in_progress | P0 | Critical | Medium | 12h/2200tok | Medium | 9 | governance-loop | independent-auditor | Execute next | `tag_manual`에서 `agent_runtime`으로 이동할 때 skill/hook/script 누락·변형·의도적 제외가 의도된 이유인지, 기술적… |
| `TASK-AR-224` | in_progress | P0 | Critical | Medium | 8h/1600tok | Medium | 9 | governance-loop | independent-auditor | Execute next | `v0.1.8` 판정에서 공통 정합 규칙(공식 가이드 반영, migration 근거, tag_manual 이식 누락 처리)이 줄지 않게 동작하도록 공식/… |
| `TASK-AR-203` | planned | P0 | Critical | Medium | 8h/1500tok | Medium | 8 | project-context | doc-steward | Execute next | 지식창고 문서를 `빠른 참조, 차원 설명, 핵심 테이블, 주의사항/패턴, 상위 문맥 링크` 형식으로 표준화해 사람이 즉시 구조를 읽고 판단할 수 있게 한… |
| `TASK-AR-221` | in_progress | P0 | Critical | High | 16h/3200tok | Medium | 8 | validation-team | qa | Execute next | 에이전트 런타임을 한 번에 재사용 가능한 MVP/멀티 프로젝트 운영 구조로 정리한다. 공식 가이드(Claude/Codex/OpenAI 권고)에 맞추어 아… |
| `TASK-AR-222` | in_progress | P0 | Critical | High | 14h/2800tok | Medium | 8 | agent-runtime-core | lead-engineer | Execute next | `v0.1.8` 1차 판정(2026-07-02)을 위해 요구사항 1~16 및 공식 권고를 하나의 판정 번들로 정합한다. 특히 `agent_runtime`… |
| `TASK-AR-234` | planned | P0 | Critical | Medium | 10h/1800tok | Medium | 8 | agent-runtime-core | lead-engineer | Execute next | Define the planning loop contract and state machine for bounded recursive self-improv… |
| `TASK-AR-235` | planned | P0 | Critical | Medium | 12h/2200tok | Medium | 8 | agent-runtime-core | lead-engineer | Execute next | Implement a read-only planning scan that compares backlog, status, roadmap, task file… |
| `TASK-AR-236` | planned | P0 | Critical | Medium | 12h/2200tok | Medium | 8 | agent-runtime-core | lead-engineer | Execute next | Add a proposal outbox and draft task writer so planning findings become inspectable p… |
| `TASK-AR-237` | planned | P0 | Critical | Medium | 12h/2200tok | Medium | 8 | agent-runtime-core | lead-engineer | Execute next | Connect the planning loop to safe triggers: cycle completion, task completion, schedu… |
| `TASK-AR-246` | planned | P0 | Critical | Medium | 12h/2200tok | Medium | 8 | agent-runtime-core | lead-engineer | Execute next | Implement dispatcher helpers for safe parallel Codex/Claude work: one task per worktr… |
| `TASK-AR-238` | planned | P1 | High | Medium | 14h/2400tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | Add a UI Planner panel that shows planning scans, proposals, evidence, risk tier, rev… |
| `TASK-AR-241` | planned | P1 | High | Medium | 12h/2200tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | Build a review/compound/retro synthesizer that reads historical tasks, reviews, compo… |

### Ask

| Task | Status | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-201` | in_progress | P0 | Critical | Medium | 8h/1200tok | High | 12 | project-context | doc-steward | Owner/agent decision | `agent_runtime`가 프로젝트별 요청을 처리할 때 source-tier, owner, 접근권한, freshness를 기준으로 지식 소스를 라우팅… |
| `TASK-AR-214` | in_progress | P0 | Critical | Medium | 16h/2600tok | Medium | 10 | validation-team | qa | Owner/agent decision | 질의 실행 전후의 `source_tier`, `owner`, `access`, `freshness`, `lineage`, `ambiguity`, `tra… |

### Review

| Task | Status | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---:|---|---|---|---|---:|---|---|---|---|
| - | - | - | - | - | - | - | - | - | - | - | - |

### Later

| Task | Status | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-243` | planned | P0 | Critical | High | 16h/3000tok | Medium | 9 | validation-team | qa | Wait for dependency | Connect trace, grader, eval, correction, live-review, and A2A evidence to planning pr… |
| `TASK-AR-239` | planned | P0 | Critical | High | 16h/2800tok | Low | 7 | agent-runtime-core | lead-engineer | Wait for dependency | Implement approved proposal apply and verification so accepted planning proposals can… |
| `TASK-AR-244` | planned | P0 | Critical | High | 16h/2800tok | Low | 7 | agent-runtime-core | lead-engineer | Wait for dependency | Add stability, budget, drift, and non-divergence guardrails for recursive planning lo… |
| `TASK-AR-242` | planned | P1 | High | High | 16h/2600tok | Low | 6 | agent-runtime-core | lead-engineer | Wait for dependency | Define an agent department and diversity council model so similar topics are reviewed… |
| `TASK-AR-245` | planned | P1 | High | High | 16h/2800tok | Low | 6 | agent-runtime-core | lead-engineer | Wait for dependency | Define the long-term C-mode promotion gate for bounded auto-planning and low-risk aut… |

### Done

| Task | Status | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-204` | completed | P0 | Critical | Medium | 12h/1800tok | Medium | 8 | agent-runtime-core | lead-engineer | Archive/evidence only | 런타임의 스킬/런북 문서가 코드/데이터/스키마 변경과 동기화되지 않을 경우 릴리스가 차단되도록 한다. |
| `TASK-AR-216` | completed | P0 | Critical | Medium | 10h/2200tok | Medium | 8 | agent-runtime-core | lead-engineer | Archive/evidence only | `v0.1.7` 공개 판정의 미충족 항목을 `v0.1.8` 판정으로 안전하게 이관하고, 릴리스 보드가 읽는 하나의 `release-state` 체인으로… |
| `TASK-AR-215` | completed | P0 | Critical | Medium | 18h/3000tok | Low | 6 | project-context | doc-steward | Archive/evidence only | 다른 프로젝트로 에이전트를 투입할 때 공용 런타임은 유지하고 오버레이만 교체해 vision, roadmap, 조직도, 팀, 링크, 협의기록을 즉시 맥락에… |
| `TASK-AR-225` | completed | P0 | Critical | Medium | 10h/1800tok | Low | 6 | agent-runtime-core | cicd-engineer | Archive/evidence only | Close the `release-preflight findings=358` blocker discovered by `TASK-AR-224` execut… |
| `TASK-AR-226` | completed | P0 | Critical | Medium | 8h/1400tok | Low | 6 | agent-runtime-core | lead-engineer | Archive/evidence only | Map the current `agent_runtime` state sources before building a web UI, so the UI rea… |
| `TASK-AR-227` | completed | P0 | Critical | Medium | 12h/2200tok | Low | 6 | agent-runtime-core | lead-engineer | Archive/evidence only | Expose a safe, read-first backend interface for the UI console, using runtime files a… |
| `TASK-AR-233` | completed | P0 | Critical | Medium | 6h/1400tok | Low | 6 | agent-runtime-core | lead-engineer | Archive/evidence only | Clean the current working tree through an intentional commit and push, then keep back… |
| `TASK-AR-228` | completed | P0 | Critical | High | 14h/2600tok | Low | 5 | agent-runtime-core | lead-engineer | Archive/evidence only | Build the first read-only web console so the user can see backlog, current work, agen… |
| `TASK-AR-229` | completed | P1 | High | Medium | 12h/2200tok | Low | 5 | agent-runtime-core | lead-engineer | Archive/evidence only | Let the UI manage tasks safely by sending changes through runtime APIs or a command o… |
| `TASK-AR-230` | completed | P1 | High | Medium | 10h/2000tok | Low | 5 | agent-runtime-core | lead-engineer | Archive/evidence only | Allow the user to control runtime work from the UI by sending prompts and lifecycle c… |
| `TASK-AR-231` | completed | P1 | High | Medium | 12h/2200tok | Low | 5 | agent-runtime-core | lead-engineer | Archive/evidence only | Make the UI trustworthy during long `/goal` runs by surfacing freshness, live event c… |
| `TASK-AR-232` | completed | P2 | Medium | High | 16h/2600tok | Low | 3 | agent-runtime-core | lead-engineer | Archive/evidence only | Add the post-MVP visualizations that make the runtime understandable as an agent orga… |

## Risks / Blockers
- Format drift risk: backlog output must not collapse into a plain task list.
- Metadata gap risk: missing team/agent/value fields reduce Owner decision quality.
- Gate gap risk: prose rules are insufficient without an executable format check.

## Next Steps
- Run `python scripts/backlog_board.py --write` after task frontmatter changes.
- Run `python scripts/owner_doc_format_gate.py BACKLOG-BOARD.md` before sharing Owner-facing backlog/report docs.
- Promote missing task metadata into frontmatter when repeated inference is needed.

## Tags / References
- tags: backlog, action-board, owner-brief, decision-support
- references: `BACKLOG.md`, `STATUS.md`, `agents/lead_engineer/tasks/*.md`
