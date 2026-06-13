---
id: TASK-AR-553
display_id: TASK-AR-553
task_uid: c1b3f0c1-b908-453d-9f26-868ae090e748
registered_at: 2026-06-14T08:48:02+09:00
created_at: 2026-06-14T08:48:02+09:00
updated_at: 2026-06-14T08:48:02+09:00
status: planned
priority: P2
difficulty: M
est_hours: 8
est_tokens: 6000
owner: lead_engineer
task_set_id: TASKSET-AR-PRODUCT-MATURITY-UPLIFT
tags:
  - observability
  - metrics
  - ops
---

# TASK-AR-553 - External observability export (metrics from runtime logs)

## Goal

- The runtime captures rich local audit trails (pane_events, stop_counters, hook-logs) but exports nothing to external monitoring. Add a metrics exporter so claim/task/gate/stop state is observable remotely.

## Scope

### Input
- `agents/runtime/pane_events/pane-events.jsonl`, `agents/runtime/stop_counters.json`, hook-logs.
- `scripts/stop_events.py summary` aggregates.

### Process
- Add an exporter that reads these sources and emits metrics (Prometheus text format and/or a JSON push), e.g. claims by status, reaps, goal restarts, gate failures.
- Provide a `--check`/dry-run mode and config for the target.

### Output
- `scripts/metrics_exporter.py` (or similar) + docs; optional gate.

## Acceptance Criteria

- Exporter emits valid Prometheus/JSON metrics from real runtime files.
- Dry-run mode prints metrics without pushing.
- Counts match `stop_events.py summary` and claim-state tallies.

## Evidence Targets

- Exporter + tests + sample output.
- Source: `reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md` (reliability/observability gap).
