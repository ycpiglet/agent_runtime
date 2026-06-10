# REVIEW-2026-06-10-task-ar-201-context-router.md

## Bottom Line

`TASK-AR-201`의 핵심인 source-tier 기반 컨텍스트 라우팅 계약을 `agent_context_packet.py`에 연결했습니다.

## Signal

- `src/agent_runtime/templates/project/scripts/agent_context_packet.py`
  - `CONTEXT-SOURCES` 후보 파일(`*.yml`, `*.yaml`)을 감지하도록 메타데이터 로더 추가
  - `source_tier / id / owner / access_level / freshness_sla / lineage` 가중치 요약을 패킷에 반영
  - 누락 필드가 있으면 경고 목록으로 노출
  - `--check-only` 실행 시 경고를 함께 출력
- `TASK-AR-201` 상태는 `in_progress` 유지, `TASK-AR-204`는 선행 조건 유지(`blocked_by_PREVIOUS`).

## Decision

`TASK-AR-201`의 1차 요구사항인 `context ranking + missing metadata flags`는 충족.

다음 단계:
- `CONTEXT-SOURCES` 템플릿을 실제 프로젝트 표준 샘플에 맞춰 `access_level`/`lineage`를 강화
- `TASK-AR-204` 시작 시점에 동기화 불일치 감지 정책을 연결.
