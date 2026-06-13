---
name: work-analytics
version: 1.0.0
description: Use when the user asks for work item stats or analytics, to query/aggregate the backlog by dimension and metric, save or run a named work view, export work metadata to CSV/JSON, or browse the Work Explorer.
triggers:
  - stats
  - analytics
  - work query
  - 통계
  - explorer
dependencies:
  - scripts/work.py
  - scripts/work_item_classifier.py
  - scripts/evidence_index_generator.py
registry_id: work-analytics
template_path: src/agent_runtime/templates/project/skills/work-analytics/SKILL.md
---

# Work Analytics

Aggregate and explore v1 Work Item metadata without mutating any files. Wraps
`work.py stats` / `view` / `status` plus the read-only Work Explorer tree in
ui-console (`/api/work_explorer`).

## When To Use

- Owner asks for "통계", "work stats", "how many tasks by status/team", a
  saved report, or a CSV/JSON export of work metadata.
- You want a one-look session-start picture of active claims and worktrees.

## Stats (group-by + metrics, read-only)

```powershell
python scripts/work.py stats --by status,team --metric count
python scripts/work.py stats --by kind --metric count,actual_tokens --json
python scripts/work.py stats --kind task --status in_progress --where team=agent-runtime-core
```

- Dimensions (`--by`): stored, non-derived fields -- kind, status, owner,
  team, priority, risk_tier, project_id, initiative_id, task_set_id, task_id,
  unit_id, model tiers, verification_status, verified_by, and more.
- Metrics (`--metric`): `count`, numeric fields (actual_tokens, actual_hours,
  est/actual cost, rework_count, ...), and computed `lead_time` / `age`.
- Filters: `--kind`/`--status` (repeatable, comma-separated) and
  `--filter`/`--where field=value`. Unknown keys match nothing and warn.
- Never reads computed-only fields (progress_pct, variance, ...) from records.

## Export

```powershell
python scripts/work.py stats --by team --out reports/by-team.csv
python scripts/work.py stats --kind unit --out reports/units.json --format json
```

`--out` writes matched item rows (suffix infers format; `--format` overrides).

## Saved Views (WORK-VIEWS.json)

```powershell
python scripts/work.py view save active-tasks --by status --kind task --status in_progress
python scripts/work.py view run active-tasks --csv
python scripts/work.py view list
```

Views persist a stats query by name in
`agents/project/work-items/WORK-VIEWS.json`; `run` replays it exactly (with
optional `--out`/`--format`/`--csv` overrides). `save` refuses to overwrite
without `--force`.

## Status + Work Explorer UI

```powershell
python scripts/work.py status   # W0: active claims, worktrees, in-flight divergence
```

The Work Explorer tab in ui-console (`/api/work_explorer`) renders the
initiative->taskset->task->unit tree with per-node status buckets and facets.
Its source is `WORK-ITEM-CLASSIFICATION.json`; if the UI reports a stale or
missing snapshot, refresh it with
`python scripts/work_item_classifier.py --write`.

## Safety Boundaries

- `stats`, `view run`, `view list`, and `status` are strictly read-only.
- `view save` only writes WORK-VIEWS.json; exports only write the `--out` path.
- Analytics never edits work-item frontmatter -- to change records use
  `work.py new` / `verify` / `close`.

## W0->W6 Touchpoints

- W0: `work.py status` and the Work Explorer give session-start visibility.
- W1-W6: stats/views track throughput, lead time, rework, and verification
  coverage across the lifecycle without mutating any work item.
