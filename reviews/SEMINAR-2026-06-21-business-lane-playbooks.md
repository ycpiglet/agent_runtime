---
type: seminar
title: Business Lane Playbooks Seminar
date: 2026-06-21
task_id: TASK-AR-594
unit_id: UNIT-TASK-AR-594-001
task_set_id: TASKSET-AR-BUSINESS-LANE-PLAYBOOKS
status: recorded
signal: pass
participants: [strategy-lead, operations-lead, finance-controller, marketing-lead, sales-lead, doc-steward, risk-controller]
---

# Business Lane Playbooks Seminar

## Bottom Line

Lane execution is now split into concrete, repeatable playbooks for five business
lanes so teams can start with explicit scope boundaries, required artifacts, and
explicit approval triggers before any external action.

## Discussion Notes

| Lane | Position |
| --- | --- |
| finance-controller | Finance lane should stop at evidence/policy drafts and require Owner approval for all external accounting/billing effects. |
| marketing-lead | Marketing claims and campaign drafts should remain explicit and reviewable; no spam/fake-signal actions. |
| sales-lead | CRM follow-up and lead contact are draft-only until explicit Owner and risk approval. |
| operations-lead | Support runbooks are execution-ready templates for internal triage only; external communication stays in draft. |
| strategy-lead | Every execution-ready follow-up from this playbook must be registered as a task/taskset via `work.py new`. |
| doc-steward | The playbook packet must be mirrored into project templates to keep generated hosts aligned. |
| risk-controller | Keep safety boundaries explicit and avoid broadening any external-effect controls in this cycle. |

## Decision

- `TASK-AR-594` proceeds with docs-only delivery and registration-only continuation
  for any execution follow-up.
- Next cycle candidates are pre-registered in the playbook packet for follow-up
  taskset creation.

