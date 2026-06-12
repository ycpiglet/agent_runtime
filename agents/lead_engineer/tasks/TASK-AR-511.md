---
id: TASK-AR-511
display_id: TASK-AR-511
task_uid: bf47ce08-f7a8-44e9-8590-14bc9eeabbcf
registered_at: 2026-06-12T23:15:32+09:00
created_at: 2026-06-12T23:15:32+09:00
updated_at: 2026-06-12T23:15:32+09:00
title: Cross-environment normalization — .gitattributes line-ending and encoding policy
status: planned
priority: P1
difficulty: S
est_hours: 3
est_tokens: 3000
owner: lead_engineer
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-REPO-HYGIENE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
tags:
  - hygiene
  - cross-platform
  - gitattributes
  - encoding
---

# TASK-AR-511 - Cross-environment normalization

## Goal

- 서로 다른 OS/LLM/페인에서 작업한 파일이 줄바꿈·인코딩 차이로 가짜 diff와
  경고를 만드는 것을 차단한다. 현재 `.gitattributes`가 없고
  `core.autocrlf=true`라 모든 커밋에서 LF/CRLF 경고가 발생 중(2026-06-12
  세션 전체 실측).

## Context

- 가짜 diff는 footprint 충돌 게이트(AR-500)와 머지 큐(AR-502)의 신호를
  오염시킨다 — 정규화는 병렬 협업 스택의 기반층이다.
- Windows(cp949 콘솔) ↔ POSIX 페인 혼용 환경: 텍스트 파일은 repo 내 LF
  단일화가 표준 해법(checkout은 .gitattributes `text=auto eol=lf`가 통제,
  core.autocrlf 개인설정 의존 제거).

## Preconditions

- codex 미머지 브랜치들과의 대규모 재정규화 충돌 방지: 정규화 커밋
  (`git add --renormalize .`)은 codex 브랜치 merge 완료 후 1회 수행.
  .gitattributes 파일 추가 자체는 선행 가능.

## Scope

- `.gitattributes`: `* text=auto eol=lf` + 바이너리/예외(cmd 파일은
  `*.cmd text eol=crlf` — Windows 배치는 CRLF 필요) 명시.
- UTF-8 정책: 훅/스크립트의 콘솔 출력 인코딩 가드(PYTHONIOENCODING 또는
  cp949-safe 출력) 점검 — 기존 §14 Windows encoding notice와 정합.
- merge 후 `git add --renormalize .` 1회 + 검증 커밋.
- 템플릿에 동일 .gitattributes 전파 (호스트 프로젝트도 같은 문제).

## Out Of Scope

- 기존 커밋 이력 재작성(이력은 그대로, 워킹트리만 정규화).

## Acceptance Criteria

- 커밋 시 LF/CRLF 경고 0건.
- `.cmd` 훅 파일이 CRLF로 유지되어 Windows에서 정상 실행.
- `pytest tests -q` 통과, 게이트 체인 exit 0, W4b 독립 검증.

## Evidence Targets

- `.gitattributes` + 템플릿 미러
- 재정규화 커밋 + 경고 0 실증
- closeout review record
