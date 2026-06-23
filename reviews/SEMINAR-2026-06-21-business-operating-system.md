---
type: seminar
title: Business Operating System Seminar
date: 2026-06-21
task_id: TASK-AR-593
unit_id: UNIT-TASK-AR-593-001
task_set_id: TASKSET-AR-BUSINESS-OPERATING-SYSTEM
status: recorded
signal: pass
participants: [strategy-lead, operations-lead, finance-controller, marketing-lead, sales-lead, doc-steward, risk-controller]
---

# Business Operating System Seminar

## Bottom Line

The next useful business-side cycle is not another ad hoc discussion. The
runtime needs explicit operating lanes and a packet that forces review,
seminar, scribe, doc-steward, compound, retro, and W4 evidence before business
work is called complete.

## Arguments

| Role | Position |
| --- | --- |
| strategy-lead | Add planning/strategy as a first-class lane so recurring business decisions become tasksets instead of chat-only plans. |
| operations-lead | Add operations/support so support drafts, runbooks, and process cleanup have a safe owner without contacting users directly. |
| finance-controller | Keep finance/accounting draft-only for policies, evidence, pricing, and cost models; external accounting writes need approval. |
| marketing-lead | Marketing can draft claims and campaigns, but growth automation must keep the existing anti-spam and anti-manipulation boundary. |
| sales-lead | CRM and outreach must remain consent-based and draft-only until the Owner approves target, channel, and message. |
| doc-steward | A reusable packet should be mirrored into the host template so generated projects inherit the same operating behavior. |
| risk-controller | The packet must make external effects explicit because business workflows are more likely to touch customers, payments, or accounts. |

## Decision

Proceed with `TASK-AR-593` as a metadata, template, documentation, and test
unit. Do not implement integrations, outbound messaging, payment changes, CRM
sync, support desk writes, or platform posting in this unit.
