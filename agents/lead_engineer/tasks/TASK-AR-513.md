---
id: TASK-AR-513
display_id: TASK-AR-513
task_uid: 7dcaf575-5835-4dda-94d0-900cc20ad57f
registered_at: 2026-06-12T23:22:49+09:00
created_at: 2026-06-12T23:22:49+09:00
updated_at: 2026-06-12T23:22:49+09:00
title: In-flight overlay — branch-side task status visible from main board
status: planned
priority: P1
difficulty: M
est_hours: 7
est_tokens: 6000
owner: lead_engineer
initiative_id: INIT-AR-PARALLEL-WAVE-EXECUTION
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-PARALLEL-WAVE-EXECUTION
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
tags:
  - parallel
  - observability
  - board
  - in-flight
---

# TASK-AR-513 - In-flight overlay

## Goal

- main 보드가 미머지 브랜치의 진행 상황을 모르는 인식 오류를 없앤다.
  Owner 보고(2026-06-12): "main의 백로그만 보면 아직 진행이 안 된 걸로
  인식돼" — 실측으로 AR-370이 main에선 planned, codex 브랜치 3개에선
  completed(ahead 12~13)였다.

## Context

- 감지 원리 검증 완료(2026-06-12 데모): 체크아웃 없이
  `git show <branch>:agents/lead_engineer/tasks/<id>.md`로 브랜치 내부
  frontmatter 상태를 읽고, `rev-list --count main..<branch>`(ahead) +
  브랜치명/변경파일에서 task id 추출 + main 클레임 상태를 합성하면
  "main상태 vs 브랜치상태" 발산이 즉시 드러난다.
- 클레임(AR-503)은 의도 선언, 본 오버레이는 git 사실 기반 — 클레임 누락
  상황(오늘 AR-372 사례)에서도 작동하는 이중 안전망이다.
- `scripts/backlog_board.py`는 codex 미머지 브랜치가 수정 중 — 보드 직접
  통합은 merge 후, 1단계는 독립 스크립트로.

## Preconditions

- 착수(claim) 전 `python scripts/plan_assumption_gate.py --check --taskset TASKSET-AR-PARALLEL-WAVE-EXECUTION` 실행 — drift 발견 시 replan 리뷰 선행 필수.

## Scope

- 1단계(즉시 가능): `scripts/inflight_overlay.py` — 에이전트 브랜치 전수
  스캔 → task별 {main_status, branch_status, branch, ahead, last_commit,
  claim_status, divergence_flag} JSON + 사람용 표 출력. cp949 안전 출력.
- ui_state/ui-console에 in-flight 리소스 노출 (보드 화면에서 "planned
  (main) / in_progress @branch +N" 표기).
- 2단계(codex merge 후): backlog_board 행에 오버레이 컬럼 통합, scm-steward
  (AR-512) 리포트에 발산 항목 편입.
- W0 세션 시작 출력에 발산 요약 1줄 포함 (AR-506과 연계).
- 템플릿 미러 동기화.

## Out Of Scope

- 브랜치 내부 상태를 main에 자동 반영(상태 정본은 merge로만 이동).
- 워크트리 디렉터리 직접 읽기(git object 경유만 — 작업 중 파일 비간섭).

## Acceptance Criteria

- main상태≠브랜치상태인 task가 발산 플래그와 함께 보고된다
  (실데이터 검증: AR-370 planned/completed, AR-372 planned/in_progress).
- 클레임 없는 브랜치 작업도 감지된다.
- ui-console에서 in-flight 정보가 조회된다.
- `pytest tests -q` 통과, 게이트 체인 exit 0, W4b 독립 검증.

## Evidence Targets

- `scripts/inflight_overlay.py` + 테스트
- ui_state 리소스 + 콘솔 표기
- closeout review record
