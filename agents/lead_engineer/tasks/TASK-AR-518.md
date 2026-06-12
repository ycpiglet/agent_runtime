---
id: TASK-AR-518
display_id: TASK-AR-518
task_uid: 93485297-6326-4af3-86d2-03e2e968860f
registered_at: 2026-06-12T23:34:00+09:00
created_at: 2026-06-12T23:34:00+09:00
updated_at: 2026-06-13T00:05:00+09:00
title: Agent instance attribution across A2A evidence and commits
status: planned
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
initiative_id: INIT-AR-WORK-METADATA-ANALYTICS
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-WORK-METADATA-ANALYTICS
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - attribution_gap
  - multi_agent
tags:
  - agent-identity
  - a2a
  - evidence
  - attribution
---

# Agent instance attribution across A2A evidence and commits

## Goal
- Require instance_uid actor attribution across claims, A2A messages, evidence, closeout records, and commit trailers instead of role-only attribution.

## Context

- Agent skill/persona is class-like; live agents are instances. Owner wants
  `qa1/qa2`-style ambiguity replaced by instance-level traceability.
- Agent identity work exists, but downstream enforcement across all artifacts is
  not yet explicit enough for statistics or incident analysis.

## Scope

- Require `instance_uid` actor attribution in claims, A2A messages, evidence
  records, closeout records, and optional commit trailers.
- Gate role-only attribution as watch/block depending on artifact criticality.
- Preserve role/team/callsign/model/skill_version as query dimensions, not as
  the primary actor ID.
- Add causal links: parent_instance, on_behalf_of claim/unit, and
  decision_cycle_id where applicable.
- Extend the spawn record with `skill_versions` and `prompt_config_hash` so
  instance behavior can be traced to the class (skill) version that spawned it
  (registration-audit gap vs `record.txt` 2026-06-12 discussion).
- Record lifecycle events (spawn/heartbeat/terminate) into pane events so
  point-in-time instance census queries work (multipane census extension).

## Out Of Scope

- Changing historical commits.
- Networked external A2A transport.

## Acceptance Criteria

- Fixtures with `actor: qa` fail/watch while `actor_instance_uid` passes.
- A2A and evidence records can be grouped by instance, role, team, and model.
- Commit trailer guidance exists for future worker commits.

## Evidence Targets

- Attribution gate + tests.
- A2A/evidence fixture updates.
- Owner review showing role-only ambiguity is closed for new artifacts.
