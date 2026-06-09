# RESEARCH: TASK-AR-223 hold-routing + overlay-edge risk 반영 (2026-06-15)

수집일: 2026-06-15

## 배경

- `TASK-AR-223` closeout 번들에서 가장 많이 반복되는 실패 원인은 `query contract` 미정의, overlay stale, migration 근거 미기재였다.
- 공식 권고와 운영 실무 모두 동일하게 `재현성`, `근거`, `승인 경계`, `감사 추적`을 판정의 기본축으로 본다.
- 멀티프로젝트 투입의 품질은 런타임 코드 변경보다 오버레이/근거 사슬 보존이 좌우한다.

## 연구 요약

1. **Hold 경로 정합**
   - `hold_for_query_contract`: 질문 계약/메타 누락 시 즉시 분리하고 query contract 보강 항목을 생성해야 함.
   - `hold_for_overlay`: vision/roadmap/org/links/team/context 패킷 누락 시 분리.
   - `hold_for_data`: migration 이식 근거(`approved_by/expiry/justification/owner`) 미기재 또는 분쟁 시 분리.

2. **오버레이 재사용 운영**
   - 시나리오형 리허설(새 프로젝트 1건 이상)을 통해 코드 변경 없이 overlay 교체만으로 동작이 복구되는지 확인.
   - overlay stale는 단순 경고가 아니라 block 처리되어 다음 판정에서 이관 사유로 남아야 함.

3. **cross-project 근거 체인**
   - `MIGRATION-COMPAT-MAP`의 분류군별 미이식 이유를 task/hold로 분해하고, `TASK-AR-204` 및 `TASK-AR-210`에서 재이관 추적이 남아야 함.

## 결론

- 다음 사이클은 `TASK-AR-223` closeout에서 아래를 꼭 남겨야 함:
  1) hold 항목별 경로 증적
  2) overlay-only 시뮬레이션 1건 이상
  3) migration 근거(미입력 항목) 이관 경로
  4) TASK/REVIEW/MEETING/SEMINAR 링크의 단일 closeout 번들
