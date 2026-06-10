# RESEARCH-2026-06-11-agent-runtime-official-guidance-and-migration-evidence

## Bottom Line

`agent_runtime`의 다음 공개 버전(v0.1.7)은 기능 완성도보다 게이트 정합(강제 규칙 + 증거 + 감사 트리거) 기준으로 판단해야 한다. 공식 플랫폼 문서들은 반복 평가와
출처 정합, tool/권한 경계, human-in-the-loop 중심의 운영 철학을 일관되게 강조한다.

## Research Findings

- Anthropic 공식 가이드류:
  - MCP는 AI 모델-도구 연결을 표준화하고, 프로덕션에서는 툴 허용 목록/인증/transport 제한을 명시적으로 다루는 방향이다.
  - Anthropic eval 관련 문서는 테스트 케이스 생성, 재실행, 버전 간 비교, 기준 기반의 성공 정의를 반복적으로 요구한다.
  - 도구 사용 가이드는 작업 타입에 따라 툴/모델/파라미터를 구분하고, tool 제약을 구성 가능한 경계로 보는 접근을 제시한다.
- OpenAI 문서군:
  - Structured Outputs는 형식 적합성(스키마 일치)을 강제해 검증 가능한 `source_footer`/태그 구조 설계에 직접 연결된다.
  - Agent evals, trace grading, graders는 “한 번 통과”보다 회귀 가능한 trace 기반 점검을 권장한다.
  - Agent builder safety는 guardrail, tool approvals, HITL, trace 리뷰 결합으로 운영적 안정성을 만든다.
  - Codex 문서는 프로젝트/세션 운영에서 RBAC, 사용량/컴플라이언스 맥락을 강조한다.

## Migration Evidence Snapshot

- `tag_manual/scripts`와 `agent_runtime` 스크립트 집합 비교를 파일명 기준으로 보면 현 시점은 다음과 같은 분기다.
  - `tag_manual/scripts`만 존재: 53개
  - `agent_runtime`에서만 존재: 2개
  - 즉시 기능 회귀만으로 판단하지 말고, `SKILL/HOOK/SCRIPT/DOCS` 카테고리 기준의 분류 증거가 필요하다.
- 현재 감사에서 확인된 리스크:
  - "변경"과 "의도적 제외"의 구분이 불명확하면 향후 프로젝트별 튜닝이 runtime 고유 스킬과 충돌한다.
  - 정의/쿼리 품질 책임이 약해지면 모델 교체만으로 해결되는 것으로 오해하기 쉽다.

## Decision-ready Notes

1. `TASK-AR-204`/`TASK-AR-212`에서 `TASK-AR-209` 산출물을 같은 키(`id`, `status`)로 통합하여
   `release-preflight` 차단 포인트에 바로 연결한다.
2. `TASK-AR-211`의 컨텍스트 오버레이(ROADMAP/ORG/LINKS/TEAMS)는 프로젝트별 고유 맥락을 유지하기 위한 기본 입력으로 고정한다.
3. 데이터셋/출처/쿼리 관련 실패는 `TASK-AR-205~207`로 이어지는 교정 루프로 보내어 `90% + 교정` 게이트를 만든다.
4. 공식 가이드 대비해서도 모델은 정책 + 메타데이터 + 증거 체인이 보완되지 않으면 출시 판정을 금지한다.

## Source Links

- https://docs.anthropic.com/en/docs/mcp
- https://docs.anthropic.com/es/docs/agents-and-tools/mcp-connector
- https://docs.anthropic.com/ko/docs/test-and-evaluate/eval-tool
- https://docs.anthropic.com/it/docs/test-and-evaluate/define-success
- https://docs.anthropic.com/ko/docs/agents-and-tools/tool-use/implement-tool-use
- https://platform.openai.com/docs/guides/structured-outputs
- https://platform.openai.com/docs/guides/agents-sdk
- https://platform.openai.com/docs/guides/agent-evals
- https://platform.openai.com/docs/guides/trace-grading
- https://platform.openai.com/docs/guides/graders/
- https://platform.openai.com/docs/guides/agent-builder-safety
- https://help.openai.com/en/articles/11369540-getting-started-with-codex
- https://help.openai.com/en/articles/11369540-codex-in-chatgpt
- https://openai.com/academy/codex-how-to-start
