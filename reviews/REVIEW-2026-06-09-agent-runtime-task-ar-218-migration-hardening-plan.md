# REVIEW-2026-06-09-agent-runtime-task-AR-218-migration-hardening-plan

## Bottom Line

`TASK-AR-218`은 릴리스 유효성의 마지막 가드로, migration-map 승인 공백과 오버레이 문맥 누락을 차단 규칙으로 통합한다.

## Signal

- `TASK-AR-216` 요청서(보류 사유 이관)에서 `release-state`는 이미 4종(`hold`, `hold_for_data`, `hold_for_query_contract`, `hold_for_overlay`, `ready`)로 정리됨.
- `TASK-AR-217` rehearsal는 release-state 정합 없이 성립하지 않음.
- `MIGRATION-COMPAT-MAP.yml`에는 `approved_by` 미정 항목이 남아 있어 현재는 강제 거부 사유로 남겨야 함.

## Plan

1. `MIGRATION-COMPAT-MAP.yml` 미완 항목별로 승인 주체/근거/만료일 기록 생성.
2. `TASK-AR-204` 규칙 문서와 `TASK-AR-213` 정규화 결과를 연동해 approval 누락 상태를 즉시 block으로 리턴.
3. `ROADMAP/CONTEXT-SOURCES/LINKS` stale/누락 감지 규칙을 `TASK-AR-204`/`TASK-AR-210`로 매핑.
4. `TASK-AR-217` rehearsal trace bundle에 migration hardening 로그와 blocker evidence를 묶어 업로드.

## Recommendation

- 다음 세션은 `TASK-AR-218` 우선 종료 후에만 `TASK-AR-217` 결과를 최종 Gate 판정으로 사용.
- `TASK-AR-218`에서 누락 항목이 남으면 `release-preflight --source .`/`--source .tmp/release-bundle` 모두 block 결과를 남기고 종료.
