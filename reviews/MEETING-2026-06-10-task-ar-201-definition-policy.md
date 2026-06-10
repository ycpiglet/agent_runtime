# MEETING-2026-06-10-task-ar-201-definition-policy.md

## Participants
- runtime lead
- policy steward
- doc steward

## Agenda
- source-tier metadata 필수성의 최소 기준 합의
- `agent_runtime` upstream 파일과 host overlay 파일의 분리 경계 재확인

## Decisions
- 필수 필드로 `source_tier`, `owner`, `access_level`, `freshness_sla`, `lineage`를 요구한다.
- 이 값 부재 시 즉시 실패는 아니고, warning 출력으로 남겨 후속 `meeting` 또는 `call`에서 정합성 논의.
- `definition_policy`/`query_policy` 부재 시 warning 후 태스크 이슈로 이관.

## Action Items
- doc-steward: 샘플 `agents/project/CONTEXT-SOURCES.example.yml`에 `access_level`, `lineage` 가이드 주석 확장
- lead-engineer: 다음 TASK `TASK-AR-204`에서 경고를 CI 차단 항목으로 승격할지 테스트/판단
