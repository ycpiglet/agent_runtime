# RESEARCH-2026-06-09-agent-runtime-task-ar-official-guidance

## Bottom Line

공식 가이드는 “도구 정의 정밀화 + 다중턴 평가(trace/체크리스트/지표) + 운영 게이트” 3축을 반복적으로 강조한다.

## Signal

- Anthropic:
  - managed agents는 안정적인 인터페이스(해저드가 적게 노출되는 harness) 중심, 모델 성능 변화로 가정이 빨리 낡을 수 있음.
    Source: https://www.anthropic.com/engineering/managed-agents
  - eval는 task/trial/trace/grader 구조를 권장하고, 다중턴 환경에서 모호성·실패 전파를 다루라고 권고.
    Source: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - tool 정의에서 `name/description/input_schema/input_examples`와 이름공간, 명확한 출력이 성능의 핵심임.
    Source: https://docs.anthropic.com/ko/docs/agents-and-tools/tool-use/define-tools

- OpenAI:
  - eval은 반복 가능한 데이터셋, trace-first 디버깅, 지속적 실행으로 운영해야 함.
    Source: https://developers.openai.com/api/docs/guides/evaluation-best-practices
    Source: https://developers.openai.com/api/docs/guides/agent-evals
  - Agents SDK/가드레일/인적 검토 경로 및 안전 체크를 권장.
    Source: https://developers.openai.com/api/docs/guides/agents-sdk
    Source: https://platform.openai.com/docs/guides/agent-builder-safety
    Source: https://platform.openai.com/docs/guides/safety-checks

## Insight

- 현재 계획의 핵심 공백은 “문서/데이터의 존재”가 아니라 “정합 매핑 + CI 강제”로 보인다.
- 모델 자체보다 정확도 회복력은 context 설계, 질문 정제, trace 추적, release gate로 좌우됨.
- `태그+출처`가 없으면 실서비스에서 오답 수정 비용이 증가한다.

## Decision

- AGENTIC 계획은 공식 가이드를 반영해 P0 게이트(204/205/209)에 우선 투자하고,
  v0.1.7 창구로 버전 일정을 고정한다.
