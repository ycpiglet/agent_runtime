# MEETING: TASK-AR-220/222 closeout 동기화 정합 미팅

일시: 2026-06-14
채널: 멀티에이전트 동기화
참여: lead-engineer, doc-steward, independent_auditor, owner
관련 태스크: `TASK-AR-220`, `TASK-AR-222`, `TASK-AR-221`, `TASK-AR-210`

## 결정

- `MIGRATION-COMPAT-MAP.yml`에서 `scripts-core-kept`, `scripts-core-changed`, `scripts-runschedule-legacy`, `skills-pack`에 `justification`/`expiry`를 보강하여
  `TASK-AR-220` 완료 조건의 `justification 0건` 문제를 해소한다.
- `TASK-AR-222` closeout 번들 산출을 위한 다음 증적 경로를 확정:
  - `reviews/RESEARCH-2026-06-14-agent-runtime-task-ar-222-cross-project-overlay-and-governance-research.md`
  - `reviews/REVIEW-2026-06-14-agent-runtime-task-ar-222-closeout-log.md`
  - `reviews/MEETING-2026-06-14-agent-runtime-task-ar-222-migration-closeout-sync.md`
- `MIGRATION-COMPAT-MAP.yml`의 누락 항목은 더 이상 미정 상태로 두지 않고 `TASK-AR-204` 라우트와 `TASK-AR-204` 블록 규칙 증거를 즉시 연결.

## 실행 항목(이번 사이클)

1. `TASK-AR-220` 산출 로그에 migration-map 갱신 이력(수정일/근거/승인/만료)을 남긴다.
2. `TASK-AR-222` 다음 액션으로 `TASK-AR-221`/`219` 증적 번들 1:1 링크 항목을 고정한다.
3. `TASK-AR-210` 판정 템플릿으로 `hold_for_*` 분기와 release-state 일관성 문구를 재확인한다.
