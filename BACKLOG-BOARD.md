---
type: backlog_board
id: BACKLOG-BOARD-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [backlog, decision-board, owner-brief, action-board]
generated_at: 2026-06-14
task_count: 219
open_count: 35
completed_count: 184
task_set_count: 6
completed_task_set_count: 26
---

# Backlog Decision Board

## Bottom Line
- Summary: `35` open or active tasks; `184` completed tasks are archived from this live board.
- Routing rule: choose a task set first, then sort priority, cost, and difficulty inside that task set.

## Signal
- Status: Action `32` / Ask `1` / Review `0` / Later `2` / Done `184`.
- Task Sets: `6` active workflows; `26` completed workflows are hidden from the live action board.
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
| `TASK-AR-373` | INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE | PROJECT-AGENT-RUNTIME-PM-OS | agents/lead_engineer/tasks/units/TASK-AR-373/UNIT-TASK-AR-373-001.md | worker_ready | Action | P3 | Low | Medium | 6h/5000tok | Low | 4 | governance-loop | independent-auditor | Execute next | Make it visible which planned tasks are worker-ready and which still require planner… |
| `TASK-AR-374` | INIT-AR-WORK-HIERARCHY-CONFLICT-CLOSURE | PROJECT-AGENT-RUNTIME-PM-OS | - | planned | Action | P3 | Low | Low | 8h/4000tok | Low | 4 | agent-runtime-core | lead-engineer | Execute next | Prove that the work hierarchy and registration conflict surfaces are actually closed… |

### Host Liaison (`TASKSET-AR-HOST-FEEDBACK-INTAKE`)

- Flow: Treat host (autofolio) dogfooding feedback as first-class input: intake/triage, blind-Delphi council/seminar deliberation with diversity + Owner-boundary guardrails, decision reply-back to issues, plus the feedback-derived footprint-gate, self-eval/RSI fitness, host-fit, and open-bug candidates whose adoption the first deliberation decides.
- Progress: `0/7` done; `7` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-526` | - | - | - | planned | Action | P1 | High | Medium | 5h/4000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Treat host (autofolio) feedback issues as first-class, non-ignorable input: ingest th… |
| `TASK-AR-529` | - | - | - | planned | Action | P1 | High | Medium | 5h/4500tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Close the parallel-wave conflict-safety weak link: `footprint_conflict_gate --check`… |
| `TASK-AR-527` | - | - | - | planned | Action | P1 | High | High | 8h/7000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Reactivate the currently-dormant council/seminar device so queued host feedback is ac… |
| `TASK-AR-530` | - | - | - | planned | Action | P1 | High | High | 10h/9000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Give the platform an objective, quantitative self-eval so each version can prove it i… |
| `TASK-AR-528` | - | - | - | planned | Action | P2 | Medium | Medium | 4h/3500tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Close the loop so a deliberation outcome is written back to the originating host issu… |
| `TASK-AR-532` | - | - | - | planned | Action | P2 | Medium | Medium | 5h/4000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Route the standing open bug issues through the same intake/triage pipeline (category… |
| `TASK-AR-531` | - | - | - | planned | Action | P2 | Medium | Medium | 6h/5500tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Close the host-fit gaps that block deep adoption of agent_runtime as a reusable platf… |

### Store Architect (`TASKSET-AR-WORK-STORE-RESTRUCTURE`)

- Flow: Stop the board from dumping the archive and reviews from accumulating unbounded: board attention-lanes (Triage/Active/Rollup) + extracted archive manifest, reviews date-shard + compacted index, classifier ordinal as canonical human ID with cosmetic TASK-AR-NNN gaps, UUIDv7/ULID stable keys, a manifest-first derived read-index + repo perf config, and a triage intake status. Single store + status field + views; no lifecycle directories.
- Progress: `2/6` done; `4` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-534` | - | - | - | planned | Action | P1 | High | Medium | 6h/5500tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Treat `reviews/` (402 files, 2.4MB, pure append, never transitions state) as a logs/e… |
| `TASK-AR-538` | - | - | - | planned | Action | P2 | Medium | Low | 4h/3500tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Add an explicit intake state so new items wait in a triage inbox (excluded from the a… |
| `TASK-AR-536` | - | - | - | planned | Action | P2 | Medium | Medium | 5h/4500tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Make the permanent key collision-free AND time-sortable so multiple agents mint IDs w… |
| `TASK-AR-537` | - | - | - | planned | Action | P2 | Medium | Medium | 6h/5500tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Keep the agent read surface small and fast as the store grows toward thousands of fil… |

### Decision Cartographer (`TASKSET-AR-UNIFIED-DECISION-CONSOLE`)

- Flow: A decision/operations-optimized console over a typed entity catalog of every artifact (plan/review/issue/pr/git-log/branch/skill/council/seminar/work-items/waves/state/history): catalog model + manifest, universal command palette + cross-entity search, entity detail + backlinks, activity/provenance timeline + audit, faceted saved views + rollups + needs-attention inbox, live SCM surface, and governance-document surface.
- Progress: `0/7` done; `7` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-540` | - | - | - | planned | Action | P1 | High | Medium | 7h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | One fuzzy input to jump to / act on ANY entity in the catalog — the proven universal-… |
| `TASK-AR-541` | - | - | - | planned | Action | P1 | High | Medium | 7h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Make any entity a rich detail surface with pluggable tabs/cards (Backstage `EntityCon… |
| `TASK-AR-543` | - | - | - | planned | Action | P1 | High | Medium | 7h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Give the decision-maker reusable lenses over the catalog and an exception-only attent… |
| `TASK-AR-539` | - | - | - | planned | Action | P1 | High | High | 10h/9000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Make every meaningful artifact the product operates/archives a first-class, browsable… |
| `TASK-AR-544` | - | - | - | planned | Ask | P2 | Medium | Medium | 6h/5500tok | Low | 5 | agent-runtime-core | lead-engineer | Owner/agent decision | Bring SCM artifacts the Owner listed (git log, branches, PRs, issues) into the catalo… |
| `TASK-AR-545` | - | - | - | planned | Action | P2 | Medium | Medium | 6h/5500tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Make the product's governance/knowledge documents (skills, council records, seminar r… |
| `TASK-AR-542` | - | - | - | planned | Action | P2 | Medium | Medium | 7h/6000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Answer "who/what/when/why did this change" for any entity by unifying scattered histo… |

### Maturity Steward (`TASKSET-AR-PRODUCT-MATURITY-UPLIFT`)

- Flow: Close product-maturity gaps from the UI/quality assessment: end-to-end browser tests (Playwright), responsive layout, form validation + error UX, accessibility uplift, SSE real-time updates, i18n hardening, claim_reaper concurrency stress, observability export, multi-host claim safety, and owner-gated release automation.
- Progress: `0/10` done; `10` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-548` | - | - | - | planned | Action | P1 | High | Medium | 6h/5000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Form errors currently surface in a single global list and a failed submit can reset t… |
| `TASK-AR-552` | - | - | - | planned | Action | P1 | High | Medium | 6h/5000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | The deadlock guardrails (claim_reaper/goal_supervisor) are unit-tested on the happy p… |
| `TASK-AR-546` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Close the highest-impact UI testing gap: there are ~326 Python-side UI tests but **no… |
| `TASK-AR-549` | - | - | - | planned | Action | P1 | High | Medium | 8h/6000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | The console has broad ARIA usage but misses several WCAG essentials. Add skip-to-cont… |
| `TASK-AR-551` | - | - | - | planned | Action | P2 | Medium | Medium | 6h/5000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | i18n covers UI chrome (ko/en) but error messages are hardcoded English and there is n… |
| `TASK-AR-553` | - | - | - | planned | Action | P2 | Medium | Medium | 8h/6000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | The runtime captures rich local audit trails (pane_events, stop_counters, hook-logs)… |
| `TASK-AR-547` | - | - | - | planned | Action | P2 | Medium | High | 12h/9000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | The console is single-column with fixed widths and a fixed sidebar; it breaks below d… |
| `TASK-AR-554` | - | - | - | planned | Action | P2 | Medium | High | 12h/9000tok | Low | 5 | agent-runtime-core | lead-engineer | Execute next | Claim reaping/recovery assumes a single checkout (single-writer). Multiple hosts or C… |
| `TASK-AR-550` | - | - | - | planned | Later | P2 | Medium | High | 16h/12000tok | Low | 5 | agent-runtime-core | lead-engineer | Wait for dependency | The console polls every 5-10s, adding latency and wasted bandwidth. Add Server-Sent E… |
| `TASK-AR-555` | - | - | - | planned | Action | P3 | Low | High | 12h/9000tok | Low | 4 | agent-runtime-core | lead-engineer | Execute next | Release stages are validated locally in `--check` mode only; remote tag/PR/merge/publ… |

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
| Agent Identity Contract (`TASKSET-AR-AGENT-IDENTITY-CONTRACT`) | Add role/instance/display identity records, spawn provenance, and attribution gates for multi-agent work. | `1/1` done | `1` completed task files archived |
| Work Metadata Analyst (`TASKSET-AR-WORK-METADATA-ANALYTICS`) | Conversation-to-work traceability, Work Item metadata, Explorer roll-ups, query/export, agent attribution, and stale verification evidence. | `6/6` done | `6` completed task files archived |
| Wave Conductor (`TASKSET-AR-PARALLEL-WAVE-EXECUTION`) | Claim-time footprint conflict gate, wave dispatcher with cascade/parallel modes, integrator merge queue, and claim-first enforcement. | `10/10` done | `10` completed task files archived |
| Ops Ergonomics (`TASKSET-AR-OPS-ERGONOMICS`) | Make the 500-series infrastructure easy to operate: session-start W0 dashboard hook, trigger-based skills for wave/merge/verify/work-analytics/release, asset registry entries, and an ops command reference. | `3/3` done | `3` completed task files archived |

## Rollups
- Overview-first: this board is an attention surface. Bulk archives are summarized here as counts + pointers, not dumped inline (TASK-AR-533).
- Triage: `0` awaiting accept/defer.
- Active: `35` open across `6` task sets (see Action Board above).
- Archived task sets: `26` (see Archived Task Sets above).
- Archived task files: `184` — see `ARCHIVE-INDEX.md`.

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
