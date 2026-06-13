---
type: meeting
id: MEETING-2026-06-14-product-maturity-uplift-taskset-registration
audience: owner
status: watch
signal: watch
score: 80
priority: High
tags: [planning-record, product-maturity, ui-ux, taskset, registration, improvement-backlog]
---

# Product Maturity Uplift — Taskset Registration

## Bottom Line

- Summary: 2026-06-14 프로덕트 성숙도(4/5)·UI(3.5/5) 평가에서 도출된 개선점을 `TASKSET-AR-PRODUCT-MATURITY-UPLIFT`로 등록한다. 10개 task(TASK-AR-546~555)를 캐노니컬 task 파일로 생성했고, 평가 지표(루브릭)·검증 카탈로그도 함께 등록했다.
- Result: task 파일 10건 + 루브릭(`agents/project/PRODUCT-MATURITY-UI-RUBRIC.yml`) + 검증 카탈로그(`docs/product-maturity-ui-verification-catalog.md`) + 평가 리서치(`reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md`) 생성.
- Boundary: 모든 task는 `planned` 후보다. 등록 ≠ 착수/채택. 우선순위·ready lane 이동은 Owner 결정.

## Signal

| Task | 개선점 | 영역 | priority |
| --- | --- | --- | --- |
| TASK-AR-546 | UI e2e 브라우저 테스트(Playwright) | UI 테스트 | P1 |
| TASK-AR-547 | 반응형 레이아웃(tablet/phone) | UI | P2 |
| TASK-AR-548 | 폼 검증·에러 UX(inline/toast/undo) | UI | P1 |
| TASK-AR-549 | 접근성(skip/focus/table/label/대비) | UI | P1 |
| TASK-AR-550 | 실시간 SSE(폴링 대체) | UI | P2 |
| TASK-AR-551 | i18n 심화(에러/로케일 포맷/외부 리소스) | UI | P2 |
| TASK-AR-552 | claim_reaper 동시성·heartbeat 스트레스 | 신뢰성 | P1 |
| TASK-AR-553 | 외부 관측성 export | 관측성 | P2 |
| TASK-AR-554 | 멀티호스트 claim 안전 | 신뢰성 | P2 |
| TASK-AR-555 | 엔드투엔드 릴리스 자동화 | 릴리스 | P3 |

## Action

전체 등록을 마치려면 아래 부킹을 적용한다. **이 레시피는 wave89 closeout(미커밋 TASK-AR-526~545)과 함께 일괄 반영**한다 — 지금 인덱스/분류기를 재생성하면 미커밋 526~545와 충돌하므로, 본 레코드에 레시피만 남기고 task 파일·루브릭·카탈로그·리뷰는 격리 커밋했다.

| # | 부킹 단계 | 파일/명령 |
| --- | --- | --- |
| 1 | taskset 정의 추가 | `agents/project/work-items/TASKSET-DEFINITIONS.json`에 아래 JSON 항목 추가 |
| 2 | owner-docs 등재 | `owner-docs.yml`에 본 리뷰 2건 추가 |
| 3 | BACKLOG 보드 반영 | `BACKLOG-BOARD.md`에 taskset 섹션 + task 목록 추가 |
| 4 | 분류기 재생성 | `python scripts/work_item_classifier.py --output agents/project/work-items/WORK-ITEM-CLASSIFICATION.json` |
| 5 | 인덱스 재생성 | `python scripts/evidence_index_generator.py --root . --output reviews/INDEX.md` |
| 6 | 게이트 검증 | `python scripts/task_identity.py check --check` · `python scripts/work_schema_gate.py --items --check` · `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml` |

TASKSET-DEFINITIONS.json 추가 항목:

| field | value |
| --- | --- |
| task_set_id | TASKSET-AR-PRODUCT-MATURITY-UPLIFT |
| display_name | Product Maturity Uplift |
| summary | 2026-06-14 성숙도/UI 평가 개선점(e2e·a11y·반응형·실시간·i18n·reaper 동시성·관측성·멀티호스트·릴리스 자동화) 후보 백로그 |
| order | 546 |

owner-docs.yml 추가 항목:

| # | path |
| --- | --- |
| 1 | reviews/RESEARCH-2026-06-14-product-maturity-ui-assessment.md |
| 2 | reviews/MEETING-2026-06-14-product-maturity-uplift-taskset-registration.md |

## Risk

- 지금 분류기/인덱스를 재생성하면 wave89 미커밋 항목(TASK-AR-526~545, 미인덱싱 리뷰)을 끌어들여 격리가 깨진다 → 부킹은 closeout과 함께.
- task 파일은 legacy 프론트매터(work_schema_gate 통과 포맷)로 작성했다. v1(`schema_version`) 마이그레이션 시 일괄 변환 대상.
- 후보 등록이 "채택"으로 오독될 위험 → 모든 task에 `status: planned` + 본 레코드의 boundary 명시.

## Decision

- Decision: `TASKSET-AR-PRODUCT-MATURITY-UPLIFT`와 TASK-AR-546~555를 등록한다. 채택/우선순위는 Owner가 결정한다.
- Decision: 평가 지표는 `PRODUCT-MATURITY-UI-RUBRIC.yml`을 단일 기준으로 하고, target 상향은 매핑된 검증 케이스 통과를 조건으로 한다.
- Decision: 등록 부킹(레지스트리/인덱스)은 wave89 closeout과 함께 적용해 격리·정합성을 유지한다.

## Next

- Owner가 후보 중 착수 순서를 정하면 dispatcher claim 후 진행한다(추천 1순위: TASK-AR-546 e2e 토대).
- closeout 시 위 Action 1~6 부킹을 적용하고 owner_governance_gate 통과를 확인한다.
- 다음 정기 재평가에서 루브릭 차원을 재채점한다.
