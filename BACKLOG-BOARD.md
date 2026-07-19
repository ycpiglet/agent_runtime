---
type: backlog_board
id: BACKLOG-BOARD-agent-runtime
audience: owner
status: pass
signal: pass
score: 100
priority: High
tags: [backlog, decision-board, owner-brief, action-board]
generated_at: 2026-07-19
task_count: 265
open_count: 7
completed_count: 258
task_set_count: 2
completed_task_set_count: 47
---

# Backlog Decision Board

## Bottom Line
- Summary: `7` open or active tasks; `258` completed tasks are archived from this live board.
- Routing rule: choose a task set first, then sort priority, cost, and difficulty inside that task set.

## Signal
- Status: Action `7` / Ask `0` / Review `0` / Later `0` / Done `258`.
- Task Sets: `2` active workflows; `47` completed workflows are hidden from the live action board.
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

### Upstream Intake Closer (`TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT`)

- Flow: Fix the four open host-reported defects, integrate crash recovery and allimbot notifications, synchronize project state, then cut and verify v0.7.0.
- Progress: `1/7` done; `6` open or active.
- WIP: active `0/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-600` | INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-600/UNIT-TASK-AR-600-001.md | planned | Action | P0 | Critical | High | 5h/12000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | Resolve GitHub #280 after every intake unit is merged by refreshing current-state rec… |
| `TASK-AR-597` | INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-597/UNIT-TASK-AR-597-001.md | planned | Action | P2 | Medium | Low | 1h/2500tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Resolve GitHub #285 so transient Git setup failures include actionable stdout/stderr… |
| `TASK-AR-596` | INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-596/UNIT-TASK-AR-596-001.md | planned | Action | P1 | High | Low | 2h/4500tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Resolve GitHub #290 so active pointers find canonical TASK files with descriptive slu… |
| `TASK-AR-595` | INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-595/UNIT-TASK-AR-595-001.md | planned | Action | P1 | High | Medium | 3h/6500tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Resolve GitHub #287 so host updates honor pyproject build-system requirements instead… |
| `TASK-AR-598` | INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-598/UNIT-TASK-AR-598-001.md | planned | Action | P1 | High | Medium | 3h/7000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Resolve GitHub #274 and supersede or merge PR #277 by shipping the host-proven sessio… |
| `TASK-AR-599` | INIT-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-599/UNIT-TASK-AR-599-001.md | planned | Action | P1 | High | High | 7h/15000tok | Low | 6 | agent-runtime-core | lead-engineer | Execute next | Resolve GitHub #279 by shipping an optional, zero-dependency notification client and… |

### Role Routing Closeout Reliability (`TASKSET-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY`)

- Flow: Repair the overlay claim lifecycle gap discovered while closing TASK-AR-594.
- Progress: `0/1` done; `1` open or active.
- WIP: active `2/3`; oldest `0.0h`; stale `0`.
| Task | Initiative | Project | Unit | Status | Lane | P | Imp | Diff | Cost | Value | Score | Team | Agent | Decision | Summary |
|---|---|---|---|---|---|---:|---|---|---|---|---:|---|---|---|---|
| `TASK-AR-601` | INIT-AR-ROLE-ROUTING-CLOSEOUT-RELIABILITY | PROJECT-AGENT-RUNTIME | agents/lead_engineer/tasks/units/TASK-AR-601/UNIT-TASK-AR-601-001.md | planned | Action | P0 | Critical | Low | 2h/5000tok | Low | 7 | agent-runtime-core | lead-engineer | Execute next | Ensure role_routing overlay claims carry required lifecycle artifacts and releasing a… |

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
- Needs attention: `0` — triage awaiting `0`, owner-decision (Ask) `0` (TASK-AR-538).
- Triage: `0` awaiting accept/defer.
- Active: `7` open across `2` task sets (see Action Board above).
- Archived task sets: `47` (see Archived Task Sets above).
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
