---
schema_version: agent-runtime-work-item/v1
work_id: INIT-AR-RELEASE-AUTOMATION
work_uid: e4432a39-3953-4177-bcd2-f44277064102
kind: initiative
id: INIT-AR-RELEASE-AUTOMATION
status: active
owner: lead-engineer
created_at: 2026-06-18T22:26:32+09:00
updated_at: 2026-06-18T22:26:32+09:00
origin_type: owner_request
origin_ref: chat:2026-06-18-release-auto-noncritical
created_by: lead-engineer
summary: Realize the intended tiered release rule: noncritical (additive/patch) releases execute via the agent release council without Owner approval, while major/breaking/critical releases stay Owner-gated. Today only the cadence proposal is automatic and the execution gate is pinned to v0.1.8, so noncritical releases pile up unreleased.
---

# Release Automation (noncritical auto-execution)

## Goal

- Realize the intended tiered release rule: noncritical (additive/patch) releases execute via the agent release council without Owner approval, while major/breaking/critical releases stay Owner-gated. Today only the cadence proposal is automatic and the execution gate is pinned to v0.1.8, so noncritical releases pile up unreleased.
