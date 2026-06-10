---
id: TASK-AR-260
display_id: TASK-AR-260
task_uid: 17f86f7a-f7d3-4073-a377-8519544f16ca
registered_at: 2026-06-10
created_at: 2026-06-10
started_at: 2026-06-10
title: Runtime asset usage and reuse lifecycle metrics
status: completed
priority: P0
importance: Critical
difficulty: L
est_hours: 6
est_tokens: 2200
task_set_id: TASKSET-AR-GOVERNANCE-OPS
team: agent-runtime-core
owner: lead-engineer
agent: codex
created: 2026-06-10
updated_at: 2026-06-10T23:55:00+09:00
completed_at: 2026-06-10T23:55:00+09:00
tags: [usage-metrics, skills, hooks, triggers, gates, lifecycle, reuse]
audit_log: [agents/project/RUNTIME-ASSET-REGISTRY.json, scripts/runtime_asset_usage.py]
---

## Goal

Make developed skills, hooks, triggers, gates, and runtime scripts measurable for actual use, reuse, lifecycle state, and deprecation decisions.

## Completion Criteria

- `agents/project/RUNTIME-ASSET-REGISTRY.json` lists active skills, hooks, triggers, gates, and runtime scripts with path, evidence, lifecycle, and usage thresholds.
- `scripts/runtime_asset_usage.py --check` reports pass/watch/block and fails on missing required assets or invalid deprecation decisions.
- Owner governance gate runs `runtime_asset_usage.py --check`.
- Focused tests cover missing registry, missing asset path, usage evidence, and invalid deprecation metadata.
- Template project receives the same registry and gate.

## Execution Notes

- Low usage should be `watch` first, not silent success.
- Assets marked `deprecate` or `remove` must include a replacement or explicit rationale.

## Result

- Added `agents/project/RUNTIME-ASSET-REGISTRY.json` and template copy.
- Added `scripts/runtime_asset_usage.py` and template copy.
- Added focused tests in `tests/test_runtime_asset_usage.py`.
- Wired runtime asset usage gate into Owner governance.
- Verified runtime asset usage: `assets=14`, `usage_total=85`, `block=0`, `watch=0`.
