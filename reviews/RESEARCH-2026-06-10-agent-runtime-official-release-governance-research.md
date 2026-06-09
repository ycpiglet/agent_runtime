# RESEARCH (2026-06-10): 공식 가이드 반영 리허설 정합 검토 메모

- 주제: 릴리스 판정(고정일, hold-state, 증적 번들) 기준의 운영 정합성 점검
- 근거 출처 범주:
  - OpenAI Agents/trace-grading 및 안전 가이드
  - Anthropic test/eval/traceability 권고
  - Codex 운영 가이드(제한된 권한·승인 경계·로그)

## 정합 포인트

1. release-state 1차/2차/최종은 단일 템플릿으로 맞춰야 함.
2. 평가 점수는 보조지표, 핵심은 재현 경로(trace + footer + correction path + decision log).
3. 고위험 단계는 승인/리뷰 게이트 없으면 판정 유효성이 약하다는 점을 근거로 `hold_*` 경로를 선제.

## 실행 반영

- `TASK-AR-219` 문구/증적과 `TASK-AR-210` 판정 템플릿 정합 점검용 연구 레퍼런스로 사용.
- `TASK-AR-221`의 `source_tier/tradeoff/ambiguity/review` 정합 항목을 공식 가이드 체크리스트와 맞춤.
- `TASK-AR-220`에서 누락/의도적 제외/보류를 근거 기반으로 정렬해 오버레이와 release-preflight 연결.
