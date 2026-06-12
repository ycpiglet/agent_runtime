---
id: TASK-AR-510
display_id: TASK-AR-510
task_uid: 9da9903c-2508-4dc5-92cc-6f73ee4a374e
registered_at: 2026-06-12T22:55:34+09:00
created_at: 2026-06-12T22:55:34+09:00
updated_at: 2026-06-12T22:55:34+09:00
title: Release cadence trigger — release-lag watch and version policy check
status: planned
priority: P2
difficulty: M
est_hours: 6
est_tokens: 5000
owner: lead_engineer
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-RELEASE-STEWARD
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
tags:
  - release
  - cadence
  - trigger
  - version-policy
---

# TASK-AR-510 - Release cadence trigger

## Goal

- 릴리스 타이밍을 사람이 기억하는 대신 트리거가 감지하게 한다: 마지막 릴리스
  태그 이후 누적 변경이 임계치를 넘거나 taskset closeout wave(W6)가 닫히면
  거버넌스 체인에 비차단 "릴리스 제안" finding을 띄운다. Owner 우려
  (2026-06-12) "0.1.5→0.1.9식 급작스러운 점프"의 구조적 원인인 케이던스
  부재를 닫는다.

## Context

- 실측: v0.1.8 이후 main 81커밋 미릴리스 — 감지 장치가 없어 조용히 누적.
- 결정 기록: `reviews/REVIEW-2026-06-12-agent-runtime-release-plan-v019-v020.md`
  (버전 정책 patch/minor 기준, 2단계 릴리스, 알림 전용 자동화 경계).
- AR-509(호스트 업데이트 알림)와 쌍: 510은 업스트림 측 "릴리스 할 때",
  509는 호스트 측 "받을 때". 실행은 양쪽 모두 승인 경유 유지.

## Preconditions

- 거버넌스 체인(owner_governance_gate.py) 편입은 codex 미머지 브랜치가 해당
  파일을 수정 중이므로 merge 후 배선. 트리거 스크립트 자체는 선행 구현 가능.

## Scope

- `scripts/release_cadence_trigger.py`: (a) `git describe --tags` 기준
  마지막 릴리스 태그 대비 커밋 수/feat·fix 수 집계, (b) 임계치(기본: 커밋
  40 또는 feat 5 또는 14일) 초과 시 watch finding + 권장 버전(patch/minor)
  제안, (c) minor 판정 휴리스틱: 템플릿 파일 삭제/이름변경 또는 schemas/**
  변경 존재 시 minor 권고.
- 버전 일관성: `release_version_consistency_steward.py`와 연계해 bump 대상
  파일 목록 출력.
- merge 후: owner_governance 체인 + stop hook에 watch 전용 편입.
- 템플릿 미러 동기화.

## Out Of Scope

- 릴리스 실행 자동화(태그/푸시) — council/Owner 게이트 유지.
- 호스트 측 알림(AR-509 소관).

## Acceptance Criteria

- 임계치 초과 상태에서 트리거가 권장 버전과 함께 watch를 보고한다
  (현 repo 실데이터로 데모: 81커밋 → v0.1.9 patch 제안).
- 임계치 미만이면 침묵(비차단, 세션 영향 0).
- `pytest tests -q` 통과, 게이트 체인 exit 0, W4b 독립 검증 기록.

## Evidence Targets

- `scripts/release_cadence_trigger.py` + 테스트
- 실데이터 데모 출력
- closeout review record
