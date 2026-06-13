---
id: TASK-AR-545
display_id: TASK-AR-545
task_uid: 98d79038-827f-41c0-85ec-7a10c152ff05
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
  - documents
  - skill
  - council
  - seminar
---

# TASK-AR-545 - Skill/council/seminar/plan/review/research document surface

## Goal

- Make the product's governance/knowledge documents (skills, council records, seminar records, plans, reviews, research notes, meeting notes) browsable and actionable in the console, completing the Owner's "view and use every meaningful artifact" requirement.

## Scope

- Surface doc classes as catalog entities: skills (from the skill registry), council/seminar/meeting/review/research records (from the TASK-AR-534 reviews index), plans (`docs/superpowers/plans`), briefs.
- Render with the right detail (a council record shows verdict/score/minority concerns/owner_boundary per `DIVERSITY-COUNCIL-PROTOCOL.md`; a plan shows status/anchors); cross-link to the work items they govern.
- Quick actions: open, run/launch a skill, link a record to a task, jump to the deciding council verdict.

## Acceptance Criteria

- Skill/council/seminar/plan/review/research records appear as entities with class-appropriate detail.
- Each doc cross-links to the work items/decisions it relates to.
- Council/seminar verdicts are viewable with their protocol fields.

## Dependency / Footprint

- depends_on: TASK-AR-539 (catalog), TASK-AR-534 (reviews index).
- target_files: console documents module + skill/doc reader. Disjoint from 540-544 modules.

## Evidence Targets

- `reviews/RESEARCH-2026-06-14-unified-decision-console.md` (Backstage TechDocs plugin; Glean content+people+activity graph; Notion databases-as-docs).
- `agents/project/DIVERSITY-COUNCIL-PROTOCOL.md` (council verdict fields surfaced).
