---
type: design_spec
id: SPEC-org-chart-load-v1
topic: Org chart legibility — show per-team load & blocked status at a glance
audience: maintainers
status: draft
generated_at: 2026-06-27
references:
  - docs/superpowers/specs/2026-06-27-health-snapshot-design.md
---

# Org Chart Load v1 — Design Spec

## Bottom Line (KO)
조직도(이미 깔끔한 트리)에 **팀별 "지금 무엇을 얼마나 맡고 있고, 막힌 게 있는지"**를 한눈에 얹는다. 비전공자가 조직도만 봐도 "이 팀이 바쁘다 / 막혀있다"를 읽도록. 신규 그래프 엔진 없이 기존 `build_org_chart`/`renderOrgChart` + workload 밴드 + 상태 토큰에 **추가만**. 실시점 카운트만(가짜 추세 금지).

## Problem
The org chart (`build_org_chart` → `renderOrgChart`) renders a clean director→team→role tree with online counts + tier badges, but a non-expert cannot see **who is busy or blocked**: team nodes show "N online", never "N active tasks / M blocked". The data (task→team, task.status) exists but isn't joined onto the chart.

## Goals (iteration 1)
1. Per-TEAM load on the org chart: `active_count`, `blocked_count`, and a `load_band` (idle/normal/busy) reusing the workload band thresholds — so a team's busyness reads at a glance (color + text label, never color-only).
2. A blocked marker on any team with blocked tasks (danger tone + "막힘 N" label).
3. A plain-language summary line above the chart: "N개 팀 · X건 진행 · Y건 막힘" (insight, not a node dump).

## Non-Goals
- Per-role counts (34 roles = too granular for a non-expert; roles keep their online state). No live-map/force-graph changes. No new route/storage. No fabricated trends (counts are point-in-time). No new images.

## Honesty / data
Counts are current-state aggregates over `tasks`; stated as counts, never a trend. Tasks are enriched with `task["assigned_team"]` by `enrich_tasks_with_assignment` (NOT `task["team"]` — red-team correction); the org TEAM node `id` shares that id space (the Workload heatmap already joins on it). Status classification reuses `_status_bucket(task)` (ui_state.py:1961): blocked = bucket `"blocked"`, active = bucket `"in_progress"` — NOT hardcoded strings.

**Bands (red-team fix):** do NOT reuse `_WORKLOAD_*` — those band a *monthly cell* load, so a point-in-time total of 4 would mis-read as "overload". Define separate `_ORG_LOAD_NORMAL_MAX = 4`, `_ORG_LOAD_BUSY_MAX = 8` and `_org_load_band(count)` → idle (0) / normal (1–4) / busy (5–8) / overload (>8).

## Design
### A. Back end (ui_state.py, additive)
- `_org_load_band(count)` (new thresholds above).
- `_org_team_load(tasks)` → `{assigned_team: {"active": int, "blocked": int}}`, grouping by `task["assigned_team"]` using `_status_bucket`.
- `build_org_chart(root, team_agents, now, *, team_load=None)` — optional kwarg (ZERO blast radius: the sole caller is build_state ~line 8059, tasks in scope; no test calls it directly). Each TEAM node gets `active_count`, `blocked_count`, `load_band`. A top-level `load_summary = {teams, active, blocked}` is added.
- A fixture test confirms the join is non-zero (active/blocked land on the matching team node id).

### B. Front end (ui_console_assets.py, additive)
- `renderOrgChart` team-node card: append a compact load line — "{active} 진행 · {blocked} 막힘" with a `load-band-{band}` class (token color) AND the words (label). Blocked>0 adds a danger marker.
- A summary line rendered above the chart from `org_chart.load_summary` ("N개 팀 · X건 진행 · Y건 막힘").
- All strings via i18n (ko+en). Tokens only.

## Testing
- ui_state: `_org_team_load` on a fixture (2 active + 1 blocked task on team X) → correct counts; band reflects thresholds. `build_org_chart` (or the wiring in build_state) stamps `active_count`/`blocked_count`/`load_band` on the team node and a `load_summary`.
- assets: served `/app.js` has the org load render (e.g. `org-team-load`); `/app.css` has the load-band class hook.
- Gates: design_system (`--all-ui`), i18n_literal (ko+en), nav_budget unchanged.

## Risks & Mitigations
1. **Team-id mismatch** between task.team and org node team id → test the join on a fixture; if a task's team has no node, it's counted only in the summary (no crash).
2. **Empty data** → counts 0, band idle, summary "0 진행 · 0 막힘"; no fabricated state.
3. **Design-system gate** → tokens only. **i18n** → ko+en for every string.
4. **Scope** → teams only (not roles); no force-graph work.

## Rollback
Additive; revert restores the count-only org chart. No data migration.
