---
type: research
id: RESEARCH-2026-06-12-work-hierarchy-taxonomy
audience: owner
status: pass
signal: pass
score: 90
priority: High
tags: [project-management, hierarchy, taxonomy, taskset]
---

# Work Hierarchy Taxonomy Research

## Bottom Line

- Summary: use `initiative` as the Owner-facing parent above `taskset`.
- Result: avoid overloading `project`, because this repository already uses it
  for host/repository/product identity.

## Signal

| Source | Signal | Takeaway |
| --- | --- | --- |
| Linear Initiatives | pass | Initiatives group projects by company objective and track progress across longer horizons |
| Linear Projects | pass | Projects are features or large units of work made of issues and documents |
| Shape Up | pass | Shaping should stay at a level of abstraction that identifies elements without over-specifying implementation detail |
| Scrum Guide | pass | Backlogs are ordered work artifacts; selected work is decomposed for execution |

## Insight

- `Project` is too overloaded for this runtime. It can mean the repo, a host
  product, a customer deployment, a product feature, or a bundle of tasksets.
- `Initiative` is a better parent term because it denotes an outcome grouping
  above execution work without colliding with repository identity.
- `Unit` should stay below `task`, because it is not a planning promise; it is a
  worker-ready execution packet with exact files, scope, checks, and handoff.

## Decision

- Decision: canonical Owner-facing hierarchy is
  `initiative -> taskset -> task -> unit`.
- Decision: `project_id` remains a machine/routing field for host or legacy
  project identity.
- Decision: new task records should include `initiative_id` when the work has a
  parent outcome above taskset.

## Action Board

| Layer | Use when Owner says | Record |
| --- | --- | --- |
| Initiative | "상위 묶음/큰 목표/여러 taskset 묶음 작성해줘" | `agents/project/initiatives/<initiative_id>.md` |
| Taskset | "백로그에 할 일 목록 등록해줘" | `docs/superpowers/plans/<date>-<taskset>.md` plus `TASK-*.md` |
| Task | "이 일 하나 태스크로 등록해줘" | `agents/lead_engineer/tasks/TASK-*.md` |
| Unit | "이 태스크를 워커가 바로 실행하게 쪼개줘" | `agents/lead_engineer/tasks/units/<task_id>/UNIT-*.md` |

## Sources

- Linear Initiatives: https://linear.app/docs/initiatives
- Linear Projects: https://linear.app/docs/projects
- Shape Up, Find the Elements: https://basecamp.com/shapeup/1.3-chapter-04
- Scrum Guide: https://scrumguides.org/scrum-guide.html

## Risks / Blockers

- Risk: existing documents still mention `project -> taskset -> task -> unit`;
  migration should be incremental and compatibility-preserving.
- Risk: adding `initiative_id` without an allocator/registration command leaves
  some manual editing risk.
- Blocker: none for registration.

## Next Steps

- Register `TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE`.
- Implement ID reservation and backlog deconfliction before broad multi-pane
  planning resumes.

