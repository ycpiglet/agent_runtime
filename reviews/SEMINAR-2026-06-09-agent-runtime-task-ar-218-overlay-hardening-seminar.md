# SEMINAR-2026-06-09-agent-runtime-task-ar-218-overlay-hardening-seminar

## Bottom Line

`TASK-AR-218`은 migration-map 승인 공백과 오버레이 stale/누락을 release-gate hold 체인에 묶는 작업으로,
문서화 완료 후 다음 리허설에서 차단 증적이 자동 재현되어야 한다.

## Discussion

- 주제: `TASK-AR-218` 미승인 항목 정리와 오버레이 문서 stale 규칙의 gate 통합
- 참가: lead-engineer, doc-steward, independent-auditor, owner
- 합의:
  - `MIGRATION-COMPAT-MAP.yml`의 `approved_by` 미정 항목은 모두 임시값이 아닌 `TASK-AR-218`로 정리.
  - approval이 없으면 `hold_for_data` 또는 `hold_for_overlay`로 즉시 이관.
  - `ROADMAP/CONTEXT-SOURCES/LINKS` 30일 초과는 hold 전이 규칙에 포함.

## Action

1. `MIGRATION-COMPAT-MAP.yml` 업데이트
2. `TASK-AR-204`/`TASK-AR-210`에서 미승인/미정 항목이 block이 되는지 문서 정합
3. `TASK-AR-217` rehearsal evidence bundle에 hold 리스트를 덧붙임
