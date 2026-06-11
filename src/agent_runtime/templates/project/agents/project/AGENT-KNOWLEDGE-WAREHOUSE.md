---
schema: agent-runtime-knowledge-warehouse/v1
owner: doc-steward
source_tier: context-knowledge
access_level: internal
freshness_sla: 14d
updated_at: YYYY-MM-DDTHH:MM:SS+09:00
---

# Agent Knowledge Warehouse Template

## 빠른 참조

- purpose: reusable role/project knowledge that can be checked before execution
- required metadata: owner, updated_at, source tier, lineage, history, context knowledge, freshness_sla
- stale route: warn first, repeat warning routes to `TASK-AR-204`

## 차원설명

| Dimension | Required Meaning |
| --- | --- |
| source tier | Ranked SSoT tier used for the claim |
| lineage | Upstream source chain and transformation path |
| history | Prior task, review, meeting, or correction evidence |
| context knowledge | Project intent, roadmap, organization, links, and team context |

## 핵심 테이블

| Field | Required | Failure Route |
| --- | --- | --- |
| owner | yes | reviewer_review |
| updated_at | yes | stale warning |
| source tier | yes | clarify_required |
| lineage | yes | block-or-reject |
| freshness_sla | yes | reviewer_review |

## 주의사항/패턴

- Do not answer from context knowledge alone when a certified semantic layer or lineage source exists.
- Do not infer missing overlay goals; route missing project dimensions to `hold_for_overlay`.
- Do not treat high confidence as complete without lineage and reviewer verdict.

## 연결고리

- agents/project/CONTEXT-SOURCES.yml
- agents/project/SKILL-GOVERNANCE.md
- agents/project/PROJECT-CONTEXT.yml
- agents/project/ROADMAP.md
- agents/project/ORG.md
- agents/project/LINKS.md
- agents/project/TEAMS.md
