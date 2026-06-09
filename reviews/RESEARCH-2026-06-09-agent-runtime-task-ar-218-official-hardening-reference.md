# RESEARCH-2026-06-09-agent-runtime-task-ar-218-official-hardening-reference

## Bottom Line

`TASK-AR-218`은 `tag_manual` 누락 항목을 임시 허용이 아니라 `approved_by/justification/expiry`로 묶어서
release-gate에서 강제 차단되도록 정렬해야 하며, 오버레이 문서 신선도/누락도 동일한 차단 축으로 묶는 게 핵심이다.

## Insight

- migration 이식은 “변경 vs 누락 vs 의도적 제외”를 다르게 기록해야 하며, 누락/미정 상태는 즉시 블로커로 반영되어야 한다.
- 오버레이가 stale이거나 mission-critical 항목이 비어 있으면, 실질적으로는 쿼리 라우터가 잘못된 문맥으로 실행될 수 있어 `hold_for_overlay`가 기본 동작이어야 한다.
- 강제 규칙은 기록된 근거가 있을 때만 예외 허용이 가능하다.

## Decision

- TASK-AR-218 완료 조건으로 `MIGRATION-COMPAT-MAP.yml` 미완 항목(TBD) 0건을 요구.
- `TASK-AR-218` 산출은 `TASK-AR-210` 이관 체계에서 `hold_for_data`/`hold_for_overlay`로 매핑.
