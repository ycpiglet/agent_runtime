---
type: backlog_board
id: BACKLOG-BOARD-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [backlog, decision-board, owner-brief, action-board]
generated_at: 2026-06-11
task_count: 63
open_count: 5
completed_count: 58
task_set_count: 1
completed_task_set_count: 9
---

# Backlog Decision Board

## Bottom Line
- Summary: `5` open or active tasks; `58` completed tasks are archived from this live board.
- Routing rule: choose a task set first, then sort priority, cost, and difficulty inside that task set.

## Signal
- Status: Action `3` / Ask `2` / Review `0` / Later `0` / Done `58`.
- Task Sets: `1` active workflows; `9` completed workflows are hidden from the live action board.
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

### Context Cartographer (`TASKSET-AR-CONTEXT-KNOWLEDGE`)

- Flow: Project context, source routing, and reusable knowledge structure.
- Progress: `2/7` done; `5` open or active.
| Task | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-201` | in_progress | Ask | P0 | Critical | Medium | 8h/1200tok | High | 12 | project-context | doc-steward | Owner/agent decision | `agent_runtime`가 프로젝트별 요청을 처리할 때 source-tier, owner, 접근권한, freshness를 기준으로 지식 소스를 라우팅… |
| `TASK-AR-202` | planned | Action | P0 | Critical | Medium | 10h/1700tok | Medium | 10 | agent-runtime-core | lead-engineer | Execute next | `runbook`를 재사용 가능한 숙련 프로세스로 표준화해, 질문 명확화-자료 검색-실행-적대적 검토-검증-기록 흐름을 에이전트가 강제하도록 한다. |
| `TASK-AR-214` | in_progress | Ask | P0 | Critical | Medium | 16h/2600tok | Medium | 10 | validation-team | qa | Owner/agent decision | 질의 실행 전후의 `source_tier`, `owner`, `access`, `freshness`, `lineage`, `ambiguity`, `tra… |
| `TASK-AR-211` | in_progress | Action | P0 | Critical | Medium | 16h/2200tok | Medium | 9 | project-context | doc-steward | Execute next | 에이전트 런타임을 여러 프로젝트에서 공통 reuse할 때 프로젝트 고유의 vision/roadmap/조직/연결 문맥을 오버레이로 주입한다. |
| `TASK-AR-203` | planned | Action | P0 | Critical | Medium | 8h/1500tok | Medium | 8 | project-context | doc-steward | Execute next | 지식창고 문서를 `빠른 참조, 차원 설명, 핵심 테이블, 주의사항/패턴, 상위 문맥 링크` 형식으로 표준화해 사람이 즉시 구조를 읽고 판단할 수 있게 한… |

## Archived Task Sets

- Archive rule: completed task sets stay out of the live Action Board but remain visible as workflow-level completion evidence.
| Task Set | Flow | Progress | Evidence |
|---|---|---:|---|
| Quality Sentinel (`TASKSET-AR-QUALITY-LOOP`) | Offline evals, live review, correction loops, and traceable validation. | `7/7` done | `7` completed task files archived |
| Migration Archivist (`TASKSET-AR-MIGRATION-PARITY`) | tag_manual parity, migration evidence, and skill/hook/script provenance. | `6/6` done | `6` completed task files archived |
| Release Steward (`TASKSET-AR-RELEASE-STEWARD`) | Version decisions, release closeout, and consistency checks. | `7/7` done | `7` completed task files archived |
| Console Operator (`TASKSET-AR-UI-CONSOLE`) | Runtime UI console surfaces, command paths, and observability views. | `7/7` done | `7` completed task files archived |
| Planning Architect (`TASKSET-AR-RSI-PLANNING`) | Bounded recursive self-improvement, planning scans, and proposal review. | `10/10` done | `10` completed task files archived |
| Progress Scout (`TASKSET-AR-PANE-PROGRESS`) | Pane/task-set progress, live continuity, claims, and resumable handoffs. | `5/5` done | `5` completed task files archived |
| Concurrency Steward (`TASKSET-AR-COLLAB-CONCURRENCY`) | Real-time pane collaboration, event replay, SSoT ownership, and conflict gates. | `6/6` done | `6` completed task files archived |
| Governance Operator (`TASKSET-AR-GOVERNANCE-OPS`) | Waiver burn-down, lifecycle cleanup, runtime asset usage, sync enforcement, and verification hygiene. | `7/7` done | `7` completed task files archived |
| Repo Custodian (`TASKSET-AR-REPO-HYGIENE`) | Working-tree cleanup, backlog cycle hygiene, and handoff publication. | `1/1` done | `1` completed task files archived |

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
