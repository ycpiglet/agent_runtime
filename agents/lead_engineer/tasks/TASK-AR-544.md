---
id: TASK-AR-544
display_id: TASK-AR-544
task_uid: 0b16b05d-c8ad-43cc-a2df-ac33ab4cd903
registered_at: 2026-06-14T03:22:33+09:00
created_at: 2026-06-14T03:22:33+09:00
updated_at: 2026-06-14T03:22:33+09:00
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5500
owner: lead_engineer
task_set_id: TASKSET-AR-UNIFIED-DECISION-CONSOLE
tags:
  - console
  - scm
  - git
  - pr
  - branch
---

# TASK-AR-544 - Git/PR/branch/issue live SCM surface

## Goal

- Bring SCM artifacts the Owner listed (git log, branches, PRs, issues) into the catalog as browsable, cross-linked entities (Sourcegraph-style navigation + GitHub cross-references), so code/PR/branch state is part of the same decision surface as work items.

## Scope

- Read git log + branches (incl. in-flight `claude/*`/`codex/*`) and `gh` PRs/issues into the TASK-AR-539 catalog as entities with relations to tasks/claims.
- Cross-link: `T-###`/`TASK-AR-###` mentions in commits/PRs/issues resolve to work-item entities and back (GitHub "Closes/Fixes" + cross-referenced model).
- Surface branch/PR/issue status (ahead/behind, checks, open/merged) with go-to-source actions.

## Acceptance Criteria

- Git log, branches, PRs, and issues appear as catalog entities cross-linked to work items.
- Commit/PR/issue references resolve bidirectionally to tasks.
- Status (ahead/behind, checks, state) is visible with drill-to-source.

## Dependency / Footprint

- depends_on: TASK-AR-539 (catalog).
- target_files: console SCM module + git/gh reader script. Disjoint from 540/541/542/543/545 modules.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md` (Sourcegraph cross-repo navigation; GitHub timeline cross-referenced/connected events, "Closes #" automation).
