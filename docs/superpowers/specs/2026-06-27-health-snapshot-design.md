---
type: design_spec
id: SPEC-health-snapshot-v1
topic: Work-status Health Snapshot — an insight-first "is the company healthy now?" strip on the Dashboard
audience: maintainers
status: draft
generated_at: 2026-06-27
references:
  - docs/superpowers/specs/2026-06-27-decision-inbox-v1-design.md
  - reviews/RESEARCH-2026-06-20-ui-ux-visual-resources.md (sparklines, Carbon data-viz)
---

# Health Snapshot v1 — Design Spec

## Bottom Line (KO)
Dashboard(ops/dashboard)에 "지금 회사가 건강한가?"에 **한눈에 답하는 인사이트 스트립**을 추가한다. 정보 나열이 아니라 평이언어 한 문장 + (실제 시계열에만) 스파크라인. **가짜 추세 금지** — 추세는 실데이터 시계열 2종(처리량 velocity, 품질 eval_trend)에만, 막힘/예산/과부하는 "현재 상태"로 정직하게. 신규 화면 없이 기존 `componentSparkline` + 데이터뷰 토큰 + ops_metrics 데이터에 **추가만**.

## Problem
Every metrics surface (dashboard/growth/workload/work-state) dumps raw numbers/lists; none answers "is it healthy right now?" with an insight (owner's core ask: "정보 나열이 아니라 인사이트"). The Dashboard's 4-card grid HTML exists but `renderDashboard()` is minimal/unwired.

## Honesty constraint (non-negotiable — anti-theater)
Only TWO real time-series exist in `ops_metrics`: `velocity.weeks[]` (throughput) and `eval_trend.points[]` (quality scores). Blocked-gate count, overload, budget, rework rate are **point-in-time only**. Therefore:
- Trend/sparkline + direction language ("↑ vs last week") ONLY for throughput and quality.
- Risk/budget signals are stated as CURRENT STATE ("막힘 3건"), never as a fabricated trend ("막힘 5→3").

## Goals (iteration 1)
1. A `health_snapshot` derived in `build_ops_metrics()` (read-only; no new storage).
2. An overall health verdict (양호 / 주의 / 위험) with color+label (never color-only).
3. Four signals, each a plain-language insight:
   - **Throughput** — `velocity.weeks` sparkline + WoW direction ("처리량 ↑ 주 8건 (지난주 5건)").
   - **Quality** — `eval_trend.points` sparkline + latest vs avg ("평가 0.82 · 평균 0.79").
   - **Risk** — `gates.blocking` + `workload.totals.overloaded`, current state ("막힘 3 · 과부하 1" / "막힌 것 없음").
   - **Budget** — count of over-budget tasksets, current state ("예산 초과 2" / "예산 내").

## Non-Goals
- No historical tracking for blocked/budget/rework (deferred; would need weekly aggregation). No fabricated trends for them.
- No new nav surface; no cockpit placement this iteration (Dashboard only). No new images.

## Design
### A. Back end (ui_state.py, additive)
`_derive_health_snapshot(ops_metrics, workload)` is a pure module-level function reading already-built `velocity`, `eval_trend`, `gates`, `resources.tasksets` (from `ops_metrics`) and `totals.overloaded` (from `workload`); returns:
```
health_snapshot = {
  "verdict": "healthy|watch|at_risk",     # worst-of the signals (3-state only)
  "signals": [ {key, tone, ...values, series?}... ]   # tone: success|warning|danger|info
}
```
- **Wiring (red-team fix):** computed in `build_state()` right AFTER `ops_metrics` (line ~7978) and `workload` (line ~7952) are built — both in scope — and injected as `ops_metrics["health_snapshot"]`. NOT inside `build_ops_metrics` (workload is out of scope there; signature unchanged).
- verdict: `at_risk` if `gates.blocking > 0` OR `workload.totals.overloaded > 0`; else `watch` if any over-budget taskset OR quality-watch; else `healthy`. **No-data degrades to `healthy`** (no risk signals = not at risk); the 4th "insufficient" state is dropped.
- **Quality-watch (red-team fix):** trigger only when `eval_trend` has ≥2 scored points AND `latest_score < avg_score - HEALTH_QUALITY_WATCH_DELTA` (`= 0.05`, named constant). With <2 points, quality never triggers watch.
- `series` (for the sparkline) present ONLY on throughput (`velocity.weeks[].done`) and quality (`eval_trend.points[].score`, when ≥2). Risk/budget signals carry counts only — NO `series` key (enforced + tested).

### B. Front end (ui_console_assets.py, additive)
`renderHealthSnapshot(data)` renders into the Dashboard:
- A headline row: verdict chip (tone color + text label) + one-line summary.
- Signal tiles (grid): each shows label, the insight sentence, and — for throughput/quality — an inline `componentSparkline(series, {label})`. Risk/budget tiles show the current-state line, no sparkline.
Wire into `renderDashboard()`; reuse data-viz tokens (`--dv-*`, `--success/--warning/--danger`). All strings via i18n (ko+en). Sparklines get `role="img"` + aria-label.

### C. No route change
`health_snapshot` rides inside the existing `ops_metrics` payload.

## Testing
- ui_state: `build_ops_metrics` on a fixture with a velocity series + blocking gate → `health_snapshot.verdict == "at_risk"`, throughput signal has a `series`, risk signal reflects the block count. A clean fixture → `healthy`, no fabricated trend keys on risk/budget signals.
- assets: served `/app.js` contains `renderHealthSnapshot`; `/app.css` has the health tile class hook.
- Gates: design_system (`--all-ui`), i18n_literal (ko+en), nav_budget unchanged.

## Risks & Mitigations
1. **Fabricated trends** → enforced: `series` only on throughput/quality; risk/budget are current-state strings. Tested.
2. **Empty/missing data** (no velocity yet) → signals degrade to "데이터 부족" info tone, no sparkline; verdict defaults to `watch` only if real risk signals present, else `healthy`/insufficient. 
3. **Design-system gate** → tokens only.
4. **Crowding** → Dashboard only; compact tiles; progressive (sparkline only where a real series exists).

## Rollback
Additive; revert restores the minimal dashboard. No data migration.
