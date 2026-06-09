# RESEARCH-2026-06-09-agent-runtime-task-ar-214-official-query-contract

## Bottom Line

질의 계약(Task AR-214) 강화를 위해 다음 3개 축을 적용한다.

- 쿼리 메타가 없으면 `clarify_required`로 전환
- 소스 선택은 `CONTEXT-SOURCES.yml`의 4단계 SSoT 우선순위를 따름
- 고위험/고모호 요청은 `reviewer_review` 경유 후 실행

## Signal

- OpenAI 공식 문서(`trace-grading`/`agent-evals`)는 출력 단계를 구조화해 정확도 실패 위치를 재현 가능한 형태로 추적할 것을 권고한다.
- OpenAI Agent Builder Safety 가이드는 도구 승인, 구조화된 출력, guardrail 조합으로 고위험 주입/오염 리스크를 줄이라고 명시한다.
- Anthropic 가이드는 평가 기준을 구체적 지표로 정량화하고, 도구 경계(특히 MCP/승인 범위)를 정책화할 것을 전제한다.

## Insight

- `TASK-AR-214`는 `model/provider change` 이전에도 필수.
- 질문 모호성 해소 전 실행을 허용하면 교정 비용은 줄어들지만 정확도는 악화된다.
- 정확성 실패 원인은 보통 모델이 아니라 메타 누락/근거 결손에서 기인한다.

## Decision

1. `TASK-AR-214`의 강제 필드는 `CONTEXT-SOURCES.yml`의 `required_fields`를 기준으로 일괄 적용한다.
2. `quality`만 보지 않고 `tradeoff_preference`와 `ambiguity_level`도 라우팅 메타에 반영한다.
3. 구현 이전에 `clarify_required`/`reviewer_review` 경로를 `TASK-AR-204`/`210` 블로커 룰에 연결한다.
