---
id: TASK-AR-213
status: completed
owner: agent-runtime
priority: P0
difficulty: M
est_hours: 12
est_tokens: 2400
task_set_id: TASKSET-AR-MIGRATION-PARITY
tags:
  - migration-parity
  - migration-lock
  - tag-manual
  - release-block
  - skill-hook-script
trigger_meeting: yes
created: 2026-06-18
started_at: 2026-06-18T09:30:00+09:00
audit_log:
  - BACKLOG.md
  - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
  - agents/project/MIGRATION-COMPAT-MAP.yml
  - agents/project/MIGRATION-COMPAT-MAP.example.yml
  - agents/project/SKILL-DATA-MAP.yml
  - TASK-AR-209
  - TASK-AR-212
  - TASK-AR-204
  - TASK-AR-210
---

## 목표
`tag_manual` 이식에서 `skill / hook / script` 항목을 `kept/changed/deprecated/dropped/missing` 5분류로 고정하고, 모든 분류에 누락/의도적 제외 근거를 붙여 `TASK-AR-204`/`TASK-AR-212`/`TASK-AR-210`에서 바로 차단 규칙으로 재사용한다.

## 작업 내용

- 비교 기준 재정의:
  - scripts: 171개 baseline(`__pycache__`, `.pyc` 제외) 기준으로 `kept/changed/missing` 산출
  - scripts 변경점: 공통 118개 중 `kept 59`, `changed 59`
  - scripts 누락: `only_src 53`, 런타임 추가: `only_dst 2`
  - `run_schedule_task.cmd`: `dropped + deprecated`로 명시
  - skills: 공통 `16`개 중 `changed 15`, `kept 1`
  - hooks: src/hooks는 `.gitkeep` placeholder이며 runtime hook 스크립트 4개로 매핑
- `agents/project/MIGRATION-COMPAT-MAP.yml`을 2026-06-18 버전 상태로 갱신
- `scripts/summary` 항목에 승인 근거(오너/승인자/만료일/사유)를 강제
- `TASK-AR-204`가 요구하는 `approved_by/expiry/justification` 체크에 맞춰 block 조건 정합
- `TASK-AR-210` 릴리스 게이트 레코드에 `parity lock` 결과를 연결

## 완료 조건

- `TASK-AR-209`에서 생성한 분류 근거를 `TASK-AR-213`이 정규화해 재활용할 수 있음
- `MIGRATION-COMPAT-MAP`의 항목이 `TASK-AR-204`와 `TASK-AR-212` release-path에서 해석 가능
- `TASK-AR-204`의 `SKILL-DATA-MAP`/release-preflight에서 `approved_by/expiry/justification` 미완 항목은 block
- `TASK-AR-210` matrix의 블로커 사유로 `TASK-AR-213` 항목이 직접 참조됨
- `scripts-source-only`, `scripts-runtime-extra`의 `approved_by/expiry/justification` 미정 항목은 `TASK-AR-218`까지 `MIGRATION-COMPAT-MAP`를 미완 상태로 유지하여 릴리스 금지

## 현재 상태 메모

- 진행 중: 스크립트 카운트 정합(171/120/53/2) 및 해시 기반 changed 기준(59/59) 확보 완료
- 다음 단계: `TASK-AR-204`와 `TASK-AR-210` 템플릿에 `TASK-AR-213` 항목 링크를 넣고, release-block 근거 문서(리뷰/회의 기록)와 교차 링크
- 연동 추가: `TASK-AR-214`/`TASK-AR-215`의 질의 및 오버레이 계약 정책이 승인되지 않으면 `TASK-AR-210` 판정 블로커로 자동 전이
