# MEETING (2026-06-14) - TASK-AR-223 closeout planning

## 참석

- lead-engineer (host)
- independent-auditor
- doc-steward
- qa
- owner

## 논의 배경

- 요구사항 1~16 항목은 221/219/220/222에서 분산되어 있어, 판정이 임계치에서만 충족되고
  운영 루프로 재현되지 않는 구간이 남아 있음.
- 멀티프로젝트에서 공통 런타임 재현용성이 과도하게 코드 커스텀으로 분기되어
  같은 스킬/훅/스크립트가 다른 프로젝트에서 미세 수정되는 문제를 줄이기 위한 통합 규약이 필요.
- 판정 미스에서 hold 사유가 3개 경로로 분리되어 있지만, 재검증 트리에서 closeout bundle이 분산됨.

## 결정

1. `TASK-AR-223`를 `TASK-AR-221`~`TASK-AR-222` closeout 번들의 상위 통합 task로 둔다.
2. 판정 실패 라우팅은 다음 3개로 고정한다.
   - `hold_for_query_contract` (질문 계약/메타 누락)
   - `hold_for_overlay` (오버레이 미설정/오래된 vision/roadmap/org/links 연결)
   - `hold_for_data` (migration/mapping/근거 누락)
3. `AGENTIC_KNOWLEDGE_EVAL_PLAN.md`에 `TASK-AR-223` 실행 계획을 추가하고,
   `TASK-AR-221`/`222`/`219`/`220` 출력물을 하나의 감사 번들 링크로 묶는다.
4. `agents/project/SKILL-GOVERNANCE.md` 기준에 맞춰 스킬 문서·매핑·데이터 변경 동시 반영 여부를
   block 규칙으로 강제한다.

## 다음 액션

- `TASK-AR-223` 문서 본문 완료 및 상태 시작
- BACKLOG, ROADMAP, PROJECT-CONTEXT, LINKS, STATUS에 동기화
- `release-preflight` closeout bundle 템플릿의 `hold_for_*` 증빙 필드 점검
- 오버레이 변경만으로 `vision/roadmap/org/links` 교체 시나리오 1건 이상 dry run
- `MIGRATION-COMPAT-MAP.yml`의 `justification/approved_by/expiry` 미입력 항목을
  `hold_for_data`로 이관
