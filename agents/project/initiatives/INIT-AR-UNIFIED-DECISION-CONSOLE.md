---
type: initiative
id: INIT-AR-UNIFIED-DECISION-CONSOLE
status: planned
owner: lead_engineer
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
priority: High
task_sets:
  - TASKSET-AR-UNIFIED-DECISION-CONSOLE
---

# Unified Decision Console Initiative

## Purpose

Realize the Owner's core-value vision: a UI that lets you browse AND act on every
meaningful artifact the product operates/manages/archives — plan, review, issue,
PR, git log, branch, skill, council, seminar, research, meeting, work items
(initiative/taskset/task/unit), waves, state, and history — optimized for
decision-making and product operation, not just task tracking.

## Decision

- **Adopt the universal "unified browser" formula** found across Backstage,
  Sourcegraph, Glean, Port/Cortex, Linear, Notion, and Obsidian: (1) a typed
  entity graph (typed node envelope + typed directional relations), and (2) an IA
  of faceted index + detail pages with pluggable tabs/cards.
- **Layer the proven decision surfaces on top:** a universal command palette with
  prefix scoping + in-result actions (VS Code/Linear/Raycast), a typed
  activity/provenance timeline + audit stream (GitHub/Datadog/Grafana), and
  faceted saved views + rollups + a needs-attention inbox (Linear/Notion/Jira).
- **Build on the restructured store** (INIT-AR-WORK-STORE-RESTRUCTURE): canonical
  IDs (TASK-AR-535), reviews index (TASK-AR-534), and the manifest-first read
  surface (TASK-AR-537) feed the catalog so the console reads indexes, not raw
  globs.

## Scope

- Unified artifact entity model + catalog manifest (TASK-AR-539, foundation).
- Universal command palette + cross-entity search (TASK-AR-540).
- Entity detail pages + cross-links/backlinks (TASK-AR-541).
- Activity/provenance timeline + audit stream (TASK-AR-542).
- Faceted saved views + rollups + needs-attention inbox (TASK-AR-543).
- Git/PR/branch/issue live SCM surface (TASK-AR-544).
- Skill/council/seminar/plan/review/research document surface (TASK-AR-545).

## Out Of Scope

- Making the console a second source of truth: it reads generated manifests; the
  markdown/records stay canonical.
- Networked multi-tenant access control (single-Owner local console for now;
  permission-aware results are a later concern if shared).

## Source

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md`.
- Owner requirement 2026-06-14: "UI에 plan/review/issue/pr/git log/branch/skill/
  council/seminar ... 모든 유의미한 파일을 전부 조회/활용 — 의사결정/프로덕트 운용 최적화가 핵심 가치."
