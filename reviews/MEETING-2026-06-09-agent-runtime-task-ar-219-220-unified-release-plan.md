# Bottom Line

다음 버전 업데이트 목표는 `v0.1.8`이며, 공개 판정 1차 일자는 `2026-07-02`,
2차/최종은 각각 `2026-07-09`, `2026-07-16`이다.
이번 판정 이전에는 `TASK-AR-219`로 공식 가이드 동기화+버전 게이트 고정,
`TASK-AR-220`으로 tag_manual 이식 근거 정합/분류 마무리를 반드시 선행한다.

Signal:

- 다음 판정(07-02/07-09/07-16)은 현재 `TASK-AR-216`/`TASK-AR-217`/`TASK-AR-210` 기준을 따른다.
- `MIGRATION-COMPAT-MAP.yml`에는 누락/추가/재구성 항목이 이미 정렬돼 있으나,
  항목별 최종 판단 근거(의도적 제외 vs 누락)와 release-block 연결이 정합해야 한다.
- `TASK-AR-219`/`TASK-AR-220`은 기존 `TASK-AR-214`(질의 계약),
  `TASK-AR-215`(오버레이 패킷), `TASK-AR-204`(co-location), `TASK-AR-218`(migration hardening)과
  직접 연결되어야 한다.

Insight:

- 모델 성능 자체가 아닌 `정의/쿼리/출처/검증/교정/A2A` 루프가 버전 판단의 핵심이라서,
  공식 가이드(Anthropic Claude/MCP, OpenAI Agents/trace-grading, Codex 운영권고) 항목을
  release evidence bundle에 묶는 것이 다음 주기 핵심 작업이다.
- `tag_manual` 이식 누락 이슈는 전부 코드 미이식이 아니라
  "의도적 제외/운영 재구성/검증 미완 미이식"의 혼합이다.
  따라서 `approved_by/justification/expiry` 기반 근거 분류가 있어야 재이식/불필요 제외 구분이 유지된다.
- 오버레이 기반 다중 프로젝트 사용은 런타임 수정보다 컨텍스트 packet 갱신으로
  관리되어야 하며, 누락 시 즉시 `hold_for_overlay` 또는 `clarify_required`로 흘러가야 한다.

Decision:

- `TASK-AR-219`를 `P0`로 생성해 v0.1.8 버전 판정 일정 고정 및 공식 가이드 매핑을 선행한다.
- `TASK-AR-220`를 `P0`로 생성해 tag_manual 이식 이슈를 근거 체인으로 정리하고
  `TASK-AR-218`/`TASK-AR-204`와 통합한다.
- BACKLOG와 STATUS, PLAN 문서는 2026-07-02 / 2026-07-09 / 2026-07-16 판정 일정과
  `release_state` 이관 경로가 일치하도록 갱신한다.
- 다음 실행 세션은 `TASK-AR-219`(가설 정합) → `TASK-AR-220`(이식 근거 마감) →
  `TASK-AR-217`(릴리스 리허설) 순으로 수행한다.

Remaining Risk:

- `TASK-AR-220`에서 근거가 불확정인 항목이 남으면 `TASK-AR-210`가 보류 상태로
  이월되어 2026-07-09/07-16 판단이 밀릴 수 있다.
- `TASK-AR-214`와 `TASK-AR-215`가 완전 동기화되지 않으면 고위험 요청의
  `hold_for_query_contract`/`hold_for_overlay` 경로가 깨질 위험이 있다.
