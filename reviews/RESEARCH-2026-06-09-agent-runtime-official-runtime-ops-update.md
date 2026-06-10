# RESEARCH-2026-06-09-agent-runtime-official-runtime-ops-update

## Bottom Line

현재 후보 판정(계획 기준)은 **2026-07-02 1차**, **2026-07-09 2차**, **2026-07-16 최종**이다.
`agent_runtime` 릴리스는 모델 스코어보다 `쿼리 정제 + SSoT 우선순위 + 리뷰/교정/추적 루프 + 강제 게이트`를 통과해야 공개로 간주한다.

## Signal

- OpenAI 문서군: trace-grading/에이전트 평가/가드레일 가이드는 단계별 증거가 가능한 평가 흐름을 권고한다.
  - https://platform.openai.com/docs/guides/trace-grading
  - https://platform.openai.com/docs/guides/agent-evals
  - https://platform.openai.com/docs/guides/agent-builder-safety
  - https://platform.openai.com/docs/guides/graders/
- OpenAI Codex 운영 가이드와 고위험 정책은 승인 경계·로깅·인간 개입 경로를 별도 강제해야 함을 전제로 한다.
  - https://openai.com/index/running-codex-safely/
  - https://openai.com/index/introducing-lockdown-mode-and-elevated-risk-labels-in-chatgpt/
- Anthropic 문서군은 도구 경계(MCP), 성공 기준 고정, 반복 가능한 운영 정책 버전 관리를 함께 고려한다.
  - https://docs.anthropic.com/en/docs/mcp
  - https://docs.anthropic.com/en/docs/test-and-evaluate/define-success
  - https://docs.anthropic.com/en/docs/test-and-evaluate/eval-tool

## Insight

- 정답이 항상 증명 가능한 데이터셋으로 고정되지 않기 때문에, 쿼리 정의(범위/오류허용/모호성/트레이드오프)가 정확도의 시작점이다.
- 오버레이가 프로젝트별 컨텍스트를 담는 장치가 아니면 같은 런타임 재사용이 빠르게 오동작한다.
- 문서 스키마/메타가 stale 되면, 모델은 좋아도 운영 판단은 실패한다.

## Decision

1. `TASK-AR-216`에서 v0.1.7 미통과 사유를 v0.1.8 판정 체인(`release-state`)으로 정규 이관한다.
2. `TASK-AR-217`에서 release-preflight, 오프라인/라이브/교정/A2A 증적을 한 번에 녹여 `rehearsal bundle`을 남긴다.
3. `TASK-AR-214`/`TASK-AR-215`가 미충족 시 `hold_for_query_contract` 또는 `hold_for_overlay`로 즉시 전이한다.
