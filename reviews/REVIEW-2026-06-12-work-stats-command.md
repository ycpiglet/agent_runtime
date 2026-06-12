---
title: Work Stats Command
date: 2026-06-12
signal: pass
score: 92
tags: [work-cli, stats, metadata, query, task-ar-372]
---

# Work Stats Command

## Bottom Line

`scripts/work.py stats` adds the first deterministic metadata consumer for v1
Work Items. It groups canonical frontmatter by query dimensions and aggregates
numeric or computed metrics without mutating work records.

## Signal

| Check | Result | Evidence |
| --- | --- | --- |
| Group-by stats | pass | `tests/test_work_stats.py` groups `actual_tokens` by `team` |
| Computed metric | pass | `lead_time` is calculated from timestamps instead of stored frontmatter |
| Export surface | pass | CSV and JSON outputs are both covered |
| Migration boundary | pass | legacy files without `schema_version: agent-runtime-work-item/v1` are skipped |
| Safety boundary | pass | invalid metrics return nonzero and do not write files |

## Insight

- The command turns `WORK-SCHEMA.yml` metadata into a usable analysis surface:
  `team`, `origin_type`, `worker_model_tier`, `status`, and similar fields can
  now be grouped directly from records.
- `lead_time` stays computed-only, matching the schema rule that derived values
  should not become hand-edited state.
- CSV output gives the Owner a simple path into spreadsheets or BI tools without
  adding a UI dependency.

## Decision

- Decision: `work stats` reads only v1 Work Item envelopes.
- Decision: `progress_pct`, `age`, rollups, and other derived fields remain
  outside accepted input metrics unless the command computes them.
- Decision: this slice does not implement Work Explorer, saved views, or agent
  identity stats; those should consume the same records in later units.

## Action Board

| Item | Status | Note |
| --- | --- | --- |
| `work stats` CLI | done | supports `--by`, `--metric`, `--kind`, `--status`, and `--where` |
| JSON output | done | includes filters, group keys, counts, sums, averages, min, and max |
| CSV output | done | spreadsheet-friendly export |
| Computed lead time | done | uses `started_at` or `created_at` through `completed_at` |

## Risks / Blockers

- Metrics are deterministic but simple; they do not yet compute percentiles,
  rolling windows, or stale verification after source changes.
- Agent-instance dimensions will need a dedicated `agent stats` or shared
  analytics layer once A2A/evidence attribution has broader instance coverage.

## Next

- Add agent-instance stats after A2A/evidence attribution lands.
- Add saved query views or Work Explorer filters once CLI group-by semantics
  settle.
