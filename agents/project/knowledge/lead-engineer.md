---
schema: agent-runtime-knowledge-warehouse/v1
role: lead-engineer
owner: lead-engineer
source_tier: context-knowledge
access_level: internal
freshness_sla: 14d
updated_at: 2026-06-11T00:00:00+09:00
lineage: agents/project/CONTEXT-SOURCES.yml -> agents/project/SKILL-GOVERNANCE.md -> lead-engineer task execution
history:
  - agents/lead_engineer/tasks/TASK-AR-201.md
  - agents/lead_engineer/tasks/TASK-AR-202.md
  - agents/lead_engineer/tasks/TASK-AR-203.md
  - agents/lead_engineer/tasks/TASK-AR-211.md
  - agents/lead_engineer/tasks/TASK-AR-214.md
---

# Lead Engineer Knowledge Warehouse

## 빠른 참조

- source tier: context knowledge, backed by lineage and certified semantic layer when available
- owner: lead-engineer
- path match: role `lead-engineer` uses `agents/project/knowledge/lead-engineer.md`
- freshness_sla: 14d

## 차원설명

| Dimension | Lead Engineer Rule |
| --- | --- |
| source tier | Start from certified contracts, then lineage, then history, then context knowledge |
| lineage | Link runtime scripts, gates, task files, and review records before closing work |
| history | Treat prior task/review/status records as evidence, not completion by themselves |
| context knowledge | Use roadmap, org, teams, links, and communication context only as project overlay |

## 핵심 테이블

| Query Need | Required Source | Required Footer |
| --- | --- | --- |
| taskset closeout | task files, taskset gate, backlog board | source_tier, source, confidence, reviewer_verdict |
| overlay routing | PROJECT-CONTEXT, ROADMAP, ORG, TEAMS, LINKS | access_level, ambiguity_score, freshness_sla |
| release routing | RELEASE-GATE-TEMPLATE, SKILL-GOVERNANCE | lineage, hold route, correction_path |

## 주의사항/패턴

- Missing query contract fields route to `clarify_required` or `hold_for_query_contract`.
- Missing overlay dimensions route to `hold_for_overlay` and `TASK-AR-204` handoff.
- Stale context knowledge cannot override newer lineage or certified semantic layer evidence.

## 연결고리

- agents/project/CONTEXT-SOURCES.yml
- agents/project/SKILL-GOVERNANCE.md
- agents/project/AGENT-KNOWLEDGE-WAREHOUSE.md
- scripts/context_knowledge_gate.py
- scripts/taskset_work_gate.py
