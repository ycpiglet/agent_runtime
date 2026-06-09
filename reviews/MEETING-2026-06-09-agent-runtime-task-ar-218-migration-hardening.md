# MEETING-2026-06-09-agent-runtime-task-ar-218-migration-hardening

## Bottom Line

`v0.1.8` 공개 판정을 위해 `TASK-AR-218`에서 migration 근거와 오버레이 stale/overlay 정책을 `TASK-AR-210` 블로커로 즉시 연결한다.

## Signal

- `MIGRATION-COMPAT-MAP.yml`에서 `approved_by`가 `TBD`로 남아 있는 항목을 확인.
  - `scripts-source-only`: `approved_by` 미정
  - `scripts-runtime-extra`: `approved_by` 미정
- `tag_manual` 이식 누락/변경은 현재 런타임 동작 영향도가 높아 `release block`으로 유지되어야 함.
- 오버레이 문서 신선도 규칙(30일 초과, 항목 누락)이 v0.1.8 이관 조건에 반영되어야 함.

## Insight

- "모델 성능"보다 "정의 책임 + 소스 근거 + 이관 로그"가 현재 의존 실패의 핵심.
- `TASK-AR-204`가 감지만 하고 실제 통과/차단 분기를 바꾸지 않으면 오버플로우가 재발.
- 오버레이 오염은 release gate에서 즉시 `hold_for_overlay` 또는 `hold_for_query_contract`로 이관되지 않으면 타 프로젝트 투입이 깨짐.

## Decision

- `TASK-AR-218`을 `TASK-AR-216` 다음 우선순위로 고정.
- 완료 조건에서 `approved_by/justification/expiry` 미정 항목을 0건으로 강제.
- stale/오버레이 누락은 `TASK-AR-210` 보류 사유로 직접 라우팅.
