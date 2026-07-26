---
schema_version: agent-runtime-work-item/v1
id: TASK-AR-638
display_id: TASK-AR-638
task_uid: 7abe9a5e-f091-41ae-b28f-019018cdf315
work_id: TASK-AR-638
work_uid: 7abe9a5e-f091-41ae-b28f-019018cdf315
kind: task
parent_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
registered_at: 2026-07-26T20:41:04+09:00
created_at: 2026-07-26T20:41:04+09:00
updated_at: 2026-07-26T20:41:04+09:00
title: 디자인 패스 1 — KR i18n 전수 + 컬러 상태 문법 + P0 이관 코스메틱
status: planned
priority: P2
difficulty: L
est_hours: 12
est_tokens: 1000
owner: lead_engineer
team: ui-ux
initiative_id: INIT-AR-CONSOLE-OVERHAUL-P1
project_id: PROJECT-AGENT-RUNTIME
task_set_id: TASKSET-AR-CONSOLE-OVERHAUL-P1
reservation_id: RES-20260726-204104-63e72cf5-09
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-26-console-overhaul-owner-decisions.md
created_by: claude-session-overhaul-planner
summary: "\u001eagent-runtime-work-scalar-v1:[1-10+P0 \uc774\uad00] Owner \uacb0\uc815 #15 \ud655\uc815(P1 \ubcd1\ud589). KR i18n \uc815\uc801 \uce74\ud53c \uc804\uc218 \ud655\uc7a5, \uceec\ub7ec 3-\ud2f0\uc5b4 \uc0c1\ud0dc \ubb38\ubc95(attention/progress/quiet), \uc2a4\ud398\uc774\uc2f1 \ub2e4\uc774\uc5b4\ud2b8, P0\uc5d0\uc11c \uc774\uad00\ub41c \ucf54\uc2a4\uba54\ud2f1(Lucide \uc544\uc774\ucf58 \uad50\uccb4\u00b78/9px \ub9ac\ub9e4\ud551\u00b7\ub2e4\ud06c canvas \uc0c1\ud5a5\u00b7\uce78\ubc18 1\ub808\uc778=1\uc5f4), Ctrl+K \ub2e8\uc77c \ud314\ub808\ud2b8. 1-2 \ud648 \uc7ac\uad6c\uc131\uacfc \ud568\uaed8 \uc9c4\ud589\ud574\uc57c \uc7ac\uc791\uc5c5 \ucd5c\uc18c."
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_standard
tags:
  - work-cli-created
---

# TASK-AR-638 - 디자인 패스 1 — KR i18n 전수 + 컬러 상태 문법 + P0 이관 코스메틱

## Goal

- 홈 재구성과 병행해 한국어 단독 Owner와의 언어 불일치를 끝내고, 컬러/토큰/아이콘/칸반의 시각 언어를 '조용한 의사결정 콘솔'로 재정렬한다.

## Scope

- i18n 전수+디자인 토큰 재정렬+코스메틱. 프론트 물리 파일 분리는 P2(2-0).

## Acceptance Criteria

- KR 모드에서 콘솔 정적 카피가 전수 번역 테이블 경유로 표시된다(혼합 언어 화면 해소)
- 고채도 색이 primary 1색+상태 3색(attention/progress/quiet)으로 예약되고 색이름 토큰 신규 사용이 design_system_gate로 차단된다
- P0 이관 4종이 완료된다: 사이드바 재탕 엔티티 아이콘의 Lucide 교체, --font-size-ui-8/9의 11px 리매핑, 다크 canvas 그레이 상향, 칸반 1레인=1열
- 검색/이동 진입점이 Ctrl+K 단일 팔레트로 통합된다

## Verification

- `python -m pytest tests/test_ui_console.py tests/test_ui_state.py -q`
- `python scripts/i18n_literal_gate.py --check`
- `python scripts/design_system_gate.py --check`
