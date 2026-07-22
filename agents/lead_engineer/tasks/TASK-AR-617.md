---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-617
display_id: TASK-AR-617
task_uid: 7db4c284-35c3-41e4-a97c-84f698ebc8a0
work_id: TASK-AR-617
work_uid: 7db4c284-35c3-41e4-a97c-84f698ebc8a0
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
registered_at: 2026-07-22T17:45:34+09:00
created_at: 2026-07-22T17:45:34+09:00
updated_at: 2026-07-22T17:45:34+09:00
title: 프론트 물리 파일 분리 (빌드리스) — Phase 2의 관문
status: planned
priority: P2
difficulty: L
est_hours: 16
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P2
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P2
reservation_id: RES-20260722-174534-069bcc6e-01
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-22-decision-console-overhaul-masterplan.md
created_by: claude-session-overhaul-planner
summary: [D-8 권고안 A] 2-1·2-4의 대규모 마크업/신규 표면 작업을 모놀리스 위에서 하지 않기 위한 선행 투자. 빌드 파이프라인 도입 없이 물리 분리만. (§Decision 14 종속 — 스택 확정 필요)
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-617 - 프론트 물리 파일 분리 (빌드리스) — Phase 2의 관문

## Goal

- 파이썬 문자열 3종에 내장된 16,800줄 프론트를 static/console/ 실파일 + 네이티브 ES modules로 분리해 대규모 작업을 diff/lint 가능하게 만든다.

## Scope

- ui_console_assets/ui_design_assets 문자열을 static 실파일로 분리 + 서버가 정적 서빙. 프레임워크(React/Preact) 도입은 범위 밖(신규 표면 시 재평가).

## Acceptance Criteria

- HTML/CSS/JS가 static/console/ 실파일로 분리되고 ui_console 서버가 이를 서빙한다
- 네이티브 ES modules로 로드되어 빌드 파이프라인 없이 동작한다
- 오프라인 벤더링(Geist/Lucide/dagre) 정책이 유지되고 기존 뷰가 회귀 없이 렌더된다
- 분리 후 파일 단위 diff와 정적 검사가 가능하다

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_console_e2e.py tests/test_ui_state.py -q`
- `python scripts/design_system_gate.py --check`
