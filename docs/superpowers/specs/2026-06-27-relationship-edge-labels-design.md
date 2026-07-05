---
type: design_spec
id: SPEC-relationship-edge-labels-v1
topic: Relationship map legibility — label block/review edges with WHY
audience: maintainers
status: draft
generated_at: 2026-06-27
references:
  - docs/superpowers/specs/2026-06-27-org-chart-load-design.md
---

# Relationship Edge Labels v1 — Design Spec

## Bottom Line (KO)
라이브맵(관계도)의 block/review edge에 **"왜"**(막힘 사유 `blocked_reason`, 이미 데이터에 있으나 미표시)를 mid-edge 라벨로 노출한다. 비전공자가 빨간 선만 보고 끝나지 않고 "막힘: API 스키마 대기"를 읽도록. 신규 그래프 엔진 없이 `renderLiveMap`에 라벨만 추가(+ 백엔드 edge에 `reason_label` 1필드). assignment/message edge는 과밀이라 라벨 없음.

## Problem
`build_live_map` already carries `blocked_reason` on block edges, but `renderLiveMap` draws block/review edges as silent colored lines — the human reason is never rendered. A non-expert sees a red line, not "why".

## Goals (iteration 1)
1. Backend: block edges carry `reason_label` (= `blocked_reason`). (review edges need no reason — a generic localized label suffices.)
2. Front end: `renderLiveMap` draws a mid-edge label for block ("막힘[: reason]") and review ("검토 중") edges only; assignment/message stay unlabeled. Label has a background rect for legibility; color via kind class (danger/warning) + the text itself (never color-only).
3. i18n `livemap.blocked` / `livemap.review` (ko+en).

## Non-Goals
- No labels on assignment/message edges (clutter). No transitive blocking-chain view. No new route/storage/images. No force-layout changes.

## Honesty / safety
`reason_label` is the real `blocked_reason`; when absent the label is the generic kind word only (no fabrication). Reason text is rendered via `textContent` (SVG `<text>`), never innerHTML → no XSS.

## Testing
- ui_state: `build_live_map` on a blocked task with a reason → block edge has `reason_label == reason`.
- assets: served `/app.js` + `/app.css` contain `live-map-edge-label` and the i18n key `livemap.blocked`.
- Gates: design_system / i18n_literal / nav_budget green.

## Risks & Mitigations
1. **Clutter** if many block/review edges → labels limited to those two kinds (typically few); text truncated to 28 chars.
2. **XSS** from reason text → `textContent` only.
3. **Design-system / i18n** → tokens only; ko+en.

## Rollback
Additive; revert restores the unlabeled edges.
