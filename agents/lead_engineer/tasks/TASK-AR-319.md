---
id: TASK-AR-319
display_id: TASK-AR-319
task_uid: 6c03c440-54dc-4d35-9635-82fa00c55710
registered_at: 2026-06-11T17:58:45+09:00
created_at: 2026-06-11T17:58:45+09:00
started_at: 2026-06-12T02:02:59+09:00
updated_at: 2026-06-12T02:02:59+09:00
completed_at: 2026-06-12T02:02:59+09:00
title: 추적 문서 자동화 (EVIDENCE-INDEX, stale-doc 게이트, 역링크 검증)
status: completed
priority: P2
difficulty: M
est_hours: 6
est_tokens: 4000
owner: lead_engineer
task_set_id: TASKSET-AR-VISION-GAP-CLOSURE
tags:
  - docs
  - traceability
  - automation
---

# TASK-AR-319 - 추적 문서 자동화 (EVIDENCE-INDEX, stale-doc 게이트, 역링크 검증)

## Goal

- 368+개 reviews/ 증거를 수동 탐색에서 자동 색인/검증 체계로 전환해 문서 추적성을 규모에 견디게 만든다.

## Scope

- `scripts/evidence_index_generator.py`: 주제/날짜/결정/결과별 검색 가능한 EVIDENCE-INDEX 자동 생성.
- stale-doc 게이트: 일정 기간(예: 60일) 미갱신 활성 문서를 release-preflight/pre-commit에서 경고.
- 역링크 검증: 태스크 마감 시 이를 인용한 증거 파일의 존재/비고아 상태 확인.

## Acceptance Criteria

- INDEX가 자동 생성되어 reviews/ 전수를 커버하고, 게이트가 owner governance 체인에 등록된다.

## Evidence Targets

- `scripts/evidence_index_generator.py`, `reviews/INDEX.md`
- owner governance gate 체인 등록 기록

## Completion Evidence

- `scripts/evidence_index_generator.py`
- `reviews/INDEX.md`
- `scripts/owner_governance_gate.py`
- `tests/test_evidence_index_generator.py`
