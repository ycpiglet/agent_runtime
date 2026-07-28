---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-645-002
work_uid: 59b89d59-21b0-43ba-b82f-0604e2543614
kind: unit
parent_id: TASK-AR-645
unit_id: UNIT-TASK-AR-645-002
task_id: TASK-AR-645
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-28T16:36:01+09:00
updated_at: 2026-07-29T04:59:49+09:00
started_at: 2026-07-29T04:59:49+09:00
origin_type: owner_request
origin_ref: reviews/RESEARCH-2026-07-28-v080-adoption-enforcement-scope.md
created_by: codex-root-v080-planner
summary: Add configurable scribe state adapters and generated projections
horizon: unit
model_tier: worker_standard
escalation_triggers:
  - ambiguity
  - data_integrity
context: At main 8cff865b Unit 001 is integrated and closed, but scribe_due still reports ok with zero hot items for Agent Runtime's 1688-line STATUS because it recognizes one exact Korean heading. Config v2 records scalar state_adapters but no runtime consumes them. Bean Wiki uses BACKLOG.md, Allimbot uses docs/PROJECT_STATUS.ko.md, and Autofolio retains a 1460-line host STATUS. Unit 002 must add the scribe obligation without weakening Unit 001's task-linked closure behavior.
inputs:
  - reviews/REVIEW-2026-07-29-task-ar-645-unit-002-t3-replan.md
  - reviews/REVIEW-2026-07-29-task-ar-645-w0-t3-replan.md
  - scripts/scribe_due.py
  - src/agent_runtime/templates/project/scripts/scribe_due.py
  - ../bean-wiki/BACKLOG.md
  - ../allimbot/docs/PROJECT_STATUS.ko.md
  - ../autofolio/agents/lead_engineer/STATUS.md
target_files:
  - new:src/agent_runtime/state_projection.py
  - scripts/scribe_due.py
  - src/agent_runtime/templates/project/scripts/scribe_due.py
  - scripts/closure_gate.py
  - src/agent_runtime/templates/project/scripts/closure_gate.py
  - scripts/session_start_hook.py
  - src/agent_runtime/templates/project/scripts/session_start_hook.py
  - src/agent_runtime/config.py
  - src/agent_runtime/doctor.py
  - docs/configuration-v2.md
  - src/agent_runtime/templates/project/agents/scribe/SKILL.md
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - new:tests/test_scribe_due.py
  - tests/test_config_v2.py
  - tests/test_doctor.py
  - tests/test_session_continuity_hooks.py
  - tests/test_closure_gate.py
  - tests/test_inventory_sync_sanitize.py
  - tests/test_template_smoke.py
  - tests/fixtures/host/agent_runtime.lock.json
  - new:tests/fixtures/state_projection/agent-runtime-status.md
  - new:tests/fixtures/state_projection/bean-wiki-backlog.md
  - new:tests/fixtures/state_projection/allimbot-project-status.ko.md
  - new:tests/fixtures/state_projection/autofolio-status.md
  - new:tests/fixtures/state_projection/generic-state.json
scope: Consume config v2 state_adapters or bounded conventional fallbacks, parse generic Markdown and JSON sources, and atomically emit a bounded generated scribe projection without editing host canonical state. Surface missing/stale sources in doctor and SessionStart, and block only substantial closeout when an overdue projection remains unresolved.
acceptance:
  - No exact Korean heading is required.
  - Agent Runtime STATUS, Bean Wiki BACKLOG, Allimbot docs/PROJECT_STATUS.ko.md, and Autofolio STATUS fixtures produce bounded deterministic summaries from the same adapter API.
  - Missing optional or stale configured sources produce visible structured warnings and never a false ok.
  - The projection stores only derived headings/items, source paths, digests, counts, and timestamps; it excludes prompt, transcript, secret, and arbitrary file content.
  - A fresh projection satisfies the bounded-context obligation even when a canonical source stays large; overdue stale or missing projection blocks substantial closeout while mini work remains advisory.
  - SessionStart and doctor read/report state only and never modify a host source or projection.
verification:
  - python -m pytest tests/test_scribe_due.py tests/test_config_v2.py tests/test_doctor.py tests/test_session_continuity_hooks.py tests/test_closure_gate.py tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q
  - python scripts/runtime_asset_usage.py --check
  - python -m agent_runtime.cli sanitize --root . --check
handoff: Provide fixture outputs for runtime, Bean Wiki, Allimbot, and Autofolio; prove projection freshness, bounded/redacted content, read-only doctor/start, substantial closeout enforcement, and mini-task exemption.
stop_condition: Stop before changing host status/backlog files, embedding host product semantics in core, persisting prompt/transcript content, or mutating consumer repositories.
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260729-045949-task-ar-645-645002.json
---

# UNIT-TASK-AR-645-002 - Add configurable scribe state adapters and generated projections

## Context

At Agent Runtime `main` `8cff865b`, Unit 001 is integrated and closed, but
`scribe_due.py` still reports `ok` with zero hot
items for Agent Runtime's 1,688-line `STATUS.md` because it recognizes one
exact Korean heading. Config v2 already records scalar `state_adapters`, but
no runtime consumes them. Bean Wiki uses `BACKLOG.md`, Allimbot uses
`docs/PROJECT_STATUS.ko.md`, and Autofolio retains a 1,460-line host
`STATUS.md`. Unit 002 must add the scribe obligation without weakening Unit
001's task-linked closure behavior.

## Inputs

- reviews/REVIEW-2026-07-29-task-ar-645-unit-002-t3-replan.md
- reviews/REVIEW-2026-07-29-task-ar-645-w0-t3-replan.md
- scripts/scribe_due.py
- src/agent_runtime/templates/project/scripts/scribe_due.py
- ../bean-wiki/BACKLOG.md
- ../allimbot/docs/PROJECT_STATUS.ko.md
- ../autofolio/agents/lead_engineer/STATUS.md

## Target Files

- new:src/agent_runtime/state_projection.py
- scripts/scribe_due.py
- src/agent_runtime/templates/project/scripts/scribe_due.py
- scripts/closure_gate.py
- src/agent_runtime/templates/project/scripts/closure_gate.py
- scripts/session_start_hook.py
- src/agent_runtime/templates/project/scripts/session_start_hook.py
- src/agent_runtime/config.py
- src/agent_runtime/doctor.py
- docs/configuration-v2.md
- src/agent_runtime/templates/project/agents/scribe/SKILL.md
- agents/project/RUNTIME-ASSET-REGISTRY.json
- src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
- new:tests/test_scribe_due.py
- tests/test_config_v2.py
- tests/test_doctor.py
- tests/test_session_continuity_hooks.py
- tests/test_closure_gate.py
- tests/test_inventory_sync_sanitize.py
- tests/test_template_smoke.py
- tests/fixtures/host/agent_runtime.lock.json
- new:tests/fixtures/state_projection/agent-runtime-status.md
- new:tests/fixtures/state_projection/bean-wiki-backlog.md
- new:tests/fixtures/state_projection/allimbot-project-status.ko.md
- new:tests/fixtures/state_projection/autofolio-status.md
- new:tests/fixtures/state_projection/generic-state.json

## Scope

Consume config v2 `state_adapters` or bounded conventional fallbacks, parse
generic Markdown and JSON sources, and atomically emit a bounded generated
scribe projection without editing host canonical state. Surface missing/stale
sources in doctor and `SessionStart`, and block only substantial closeout when
an overdue projection remains unresolved.

## Steps

1. Define configured state sources, a fixed safe generated-projection default,
   and ownership/freshness semantics.
2. Parse generic Markdown headings, bullets, checklists, and bounded JSON
   collections without depending on one language or product layout.
3. Atomically generate a latest-ten bounded projection with source
   path/digest/count metadata and explicit missing/stale findings.
4. Make doctor and `SessionStart` report the projection read-only.
5. Let substantial closure require a fresh projection when raw state is
   overdue while keeping mini work and absent optional sources advisory.
6. Test Agent Runtime, Bean Wiki, Allimbot, and Autofolio fixture layouts.

## Acceptance Criteria

- No exact Korean heading is required.
- Agent Runtime `STATUS.md`, Bean Wiki `BACKLOG.md`, Allimbot
  `docs/PROJECT_STATUS.ko.md`, and Autofolio `STATUS.md` fixtures produce
  bounded deterministic summaries from the same adapter API.
- Missing optional or stale configured sources produce visible structured
  warnings and never a false `ok`.
- The projection stores only derived headings/items, source paths, digests,
  counts, and timestamps; it excludes prompt, transcript, secret, and
  arbitrary file content.
- A fresh projection satisfies the bounded-context obligation even when a
  canonical source stays large; overdue stale or missing projection blocks
  substantial closeout while mini work remains advisory.
- `SessionStart` and doctor read/report state only and never modify a host
  source or projection.

## Verification

- `python -m pytest tests/test_scribe_due.py tests/test_config_v2.py tests/test_doctor.py tests/test_session_continuity_hooks.py tests/test_closure_gate.py tests/test_inventory_sync_sanitize.py tests/test_template_smoke.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python -m agent_runtime.cli sanitize --root . --check`

## Handoff

Provide fixture outputs for Agent Runtime, Bean Wiki, Allimbot, and Autofolio;
prove projection freshness, bounded/redacted content, read-only doctor/start,
substantial closeout enforcement, and mini-task exemption.

## Stop Boundary

Stop before changing host status/backlog files, embedding host product
semantics in core, persisting prompt/transcript content, or mutating consumer
repositories.
