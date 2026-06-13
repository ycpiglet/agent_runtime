---
schema_version: agent-runtime-work-item/v1
work_id: TASK-AR-366
work_uid: 07e182d9-a171-409b-b978-9edd86625bb5
kind: task
parent_id: TASKSET-AR-DOC-TO-PLAN
origin_type: planning_proposal
origin_ref: TASKSET-AR-DOC-TO-PLAN
created_by: planner
id: TASK-AR-366
display_id: TASK-AR-366
task_uid: 07e182d9-a171-409b-b978-9edd86625bb5
registered_at: 2026-06-12T00:09:43+09:00
created_at: 2026-06-12T00:09:43+09:00
updated_at: 2026-06-12T00:09:43+09:00
title: 문서→플랜 파이프라인 — pitch deck/기획서 인입 → task 자동 분해 등록
status: planned
priority: P1
difficulty: XL
est_hours: 16
est_tokens: 12000
owner: lead_engineer
task_set_id: TASKSET-AR-DOC-TO-PLAN
tags:
  - doc-to-plan
  - intake
  - planning
  - autoplan
---

# TASK-AR-366 - 문서→플랜 파이프라인 — pitch deck/기획서 인입 → task 자동 분해 등록

## Goal

- pitch deck/기획서/아이디어 문서(PPT, PDF, Word, HTML, md)를 넣으면 시스템이 스스로 분석해 plan을 짜고 실현 가능한 task로 분해해 자동 등록하는 파이프라인을 만든다 (Owner 비전; Paperclip에 없는 차별 영역).

## Scope

- 파싱 레이어: PDF/PPTX/DOCX/HTML → 정규화 md (로컬 라이브러리, 외부 서비스 금지).
- 분석: 목표/기능/제약/이해관계자 추출 → plan 초안(milestone/taskset 제안) → task 분해(unit spec 수준 — PM-OPERATING-SYSTEM 계층·readiness gate 재사용).
- 등록 경로: B-mode planning 제안으로 제출 → Owner 승인 시 taskset/task 레지스트리 자동 등록 (자동 적용 금지, 게이트 경유).
- UI: 문서 드롭 존(AR-332 첨부 기반) → 분석 진행 표시 → 제안 plan 미리보기/수정 → 승인.
- 사업 단계(AR-363) 입력 연계: 인입 문서를 성숙도 평가 증거로 활용.

## Acceptance Criteria

- 샘플 pitch deck 1건이 승인 가능한 taskset 제안(plan+task 분해)으로 변환되고, 승인 시 레지스트리·보드·게이트와 정합한다.

## Evidence Targets

- 파이프라인 모듈, planning 제안 샘플, `reviews/RESEARCH-2026-06-12-agent-runtime-paperclip-and-doc-to-plan.md`
