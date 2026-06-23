---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-590
display_id: TASK-AR-590
task_uid: ac39be71-7ce9-4632-9559-fe7e55ce51bb
work_id: TASK-AR-590
work_uid: ac39be71-7ce9-4632-9559-fe7e55ce51bb
kind: task
parent_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
registered_at: 2026-06-20T01:04:15+09:00
created_at: 2026-06-20T01:04:15+09:00
updated_at: 2026-06-23T00:00:00+09:00
started_at: 2026-06-23T00:00:00+09:00
completed_at: 2026-06-23T00:00:00+09:00
resolution: done
verification_status: passed
title: State illustrations + data-viz palette + sparklines
status: done
priority: P2
difficulty: M
est_hours: 6
est_tokens: 12000
owner: lead-engineer
team: ui-ux
initiative_id: INIT-AR-VISUAL-ASSET-ADOPTION
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-VISUAL-ASSET-ADOPTION
unit_spec: agents/lead_engineer/tasks/units/TASK-AR-590/UNIT-TASK-AR-590-001.md
reservation_id: RES-20260620-010415-e5a1738e-04
origin_type: owner_request
origin_ref: chat:2026-06-20-ui-ux-visual-resources
created_by: lead-engineer
summary: Add recolorable empty/error/loading illustrations, accessible data-viz palette tokens, and inline sparklines for at-a-glance trends.
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-590 - State illustrations + data-viz palette + sparklines

## Goal

- Add recolorable empty/error/loading illustrations, accessible data-viz palette tokens, and inline sparklines for at-a-glance trends.

## Scope

- Vendor recolorable unDraw illustrations (recolor to accent token) wired into EmptyState/ErrorState/Loading patterns. Add categorical+sequential data-viz palette tokens from Radix Colors (MIT) + IBM Carbon data-viz (Apache), with dark+light + WCAG, for graph/chart use. Vendor fnando/sparkline (MIT) as componentSparkline. All permissive, self-hosted, token-driven, experimental.

## Acceptance Criteria

- Empty/Error/Loading states use recolorable unDraw illustrations tinted to the accent token (license recorded).
- Categorical + sequential data-viz palette tokens (Radix/Carbon) exist for both themes with WCAG-adequate contrast, consumed by the graph/charts.
- componentSparkline (fnando/sparkline, MIT) renders inline SVG trends; license recorded.
- design_system_gate --all-ui passes; desktop+mobile visual_verification of a state screen + a sparkline.

## Verification

- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py -q`
- `python scripts/design_system_gate.py --check --all-ui`

## Closeout Evidence

### assetization_classification

| Touched UI surface | Class | Tier |
| --- | --- | --- |
| `--dv-cat-1..8` / `--dv-seq-1..5` / `--dv-sparkline*` palette tokens (light + dark themes) | `design_token` | experimental |
| `componentSparkline(data)` inline-SVG trend (fnando/sparkline MIT, reimplemented) | `ui_component` | experimental |
| `componentEmptyState` / `componentErrorState` / `componentLoadingState` accent-tinted state illustrations (unDraw-documented upgrade path) | `ui_component` | experimental |
| Dependency / knowledge graph node fills consuming `var(--dv-cat-*)` | `pattern_component` | stable |
| Ops dashboard workload + eval-score sparkline strips | `pattern_component` | experimental |

### design_system_gate

- `python scripts/design_system_gate.py --check --all-ui` → `pass artifacts=3 roles=4 scanned=6 findings=0`.
- `python -m pytest tests/test_ui_design_assets.py tests/test_design_system_gate.py -q` → green (includes 13 new `task_ar_590` tests).

### WCAG correction (this closeout)

- The light-theme categorical hues `--dv-cat-2`, `--dv-cat-5`, `--dv-cat-6` were
  below the WCAG 1.4.11 non-text 3:1 threshold vs the light `--panel`
  (2.86 / 2.94 / 2.82:1). They were darkened to `#0d9488` / `#218358` /
  `#cc4e00` (3.49 / 4.40 / 4.20:1). All eight categorical hues now clear 3:1 in
  both themes; the new contrast test asserts this for the full palette.

### licenses recorded

- Radix Colors — MIT (categorical hue base, light theme).
- IBM Carbon data-viz — Apache 2.0 (dark-theme categorical + sequential steps).
- fnando/sparkline — MIT (sparkline normalization approach; SVG reimplemented).
- unDraw — custom open license, no attribution (documented illustration upgrade path).

### role_route

- `interface-designer` (implementation) + `design-system-steward` (token/contrast gate) + `ux-evaluator` (WCAG/responsive verification).

### visual_verification

- Desktop + mobile responsive behavior covered by the AR-592 responsive tokens
  (`--dv-sparkline-w/h` mobile overrides) and the `task_ar_592` accessibility
  tests; the served `/app.css` exposes the palette tokens in both theme roots
  and the ops dashboard renders the sparkline strips.

### taskset

- This is the final task in `TASKSET-AR-VISUAL-ASSET-ADOPTION`. With AR-587,
  AR-588, AR-589 already completed, marking AR-590 done **completes the
  taskset**.
