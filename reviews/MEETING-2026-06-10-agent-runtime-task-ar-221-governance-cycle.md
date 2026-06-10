# MEETING-2026-06-10-agent-runtime-task-ar-221-governance-cycle

## Bottom Line

- `TASK-AR-221`를 1차 실행 단계로 오픈하고, 1~16 항목을 한 번에 묶는 거버넌스 통합 작업을 시작한다.
- 오늘 결정: `SKILL-DATA-MAP`/`MIGRATION-COMPAT-MAP`를 먼저 정합해 `TASK-AR-204`의 block 조건을 구동 가능한 형태로 남긴다.

## Signal

- `TASK-AR-221` 현재 상태: `in_progress`, `started_at` 적용.
- 다중 프로젝트 오버레이 쟁점: 공용 런타임 재작성보다 오버레이 고정 우선.
- 모델 변경과 문서 동기화의 선후 경합은 `mapping-doc-changed` 이벤트로 통합.

## Discussion

- lead-engineer, doc-steward, independent-auditor, owner, QA가 참여.
- `SKILL-DATA-MAP.yml`에 `provider-config-changed`, `mapping-doc-changed`, `runtime-script-changed` 트리거를 추가하기로 합의.
- `scripts-source-only`/`scripts-runtime-extra`/`hooks-wrapper`는 `risk_profile`을 붙여 `TASK-AR-218/220`의 근거 추적 품질을 높이기로 합의.
- `TASK-AR-204`의 `block` 조건은 `warn`을 남기지 않도록 `TASK-AR-221` 산출 기준으로 강화.

## Decision

1. `TASK-AR-221` 실행 산출물로 아래 3개 문서를 1회차 커뮤니케이션 기록으로 확정한다.
   - `reviews/SEMINAR-2026-06-10-agent-runtime-task-ar-221-multi-agent-sync-seminar.md`
   - `reviews/CALL-2026-06-10-agent-runtime-task-ar-221-handoff-call.md`
   - `reviews/RESEARCH-2026-06-10-agent-runtime-task-ar-221-official-guide-refresh.md`
2. `TASK-AR-219`/`TASK-AR-220`는 `TASK-AR-221` 정합이 완료된 뒤 1차 진행.
3. `TASK-AR-217` rehearsal는 `TASK-AR-221`의 release gate 정합 반영 후 2차 액션으로 이동.

## Action

- SKILL-DATA-MAP 현재본/템플릿을 동기화.
- MIGRATION-COMPAT-MAP 정합 risk profile 추가.
- 다음 회람 문서에 보완 항목 링크(`TASK-AR-221` → `STATUS`/`BACKLOG`/`ROADMAP`/`TASK-AR-210`) 반영.
