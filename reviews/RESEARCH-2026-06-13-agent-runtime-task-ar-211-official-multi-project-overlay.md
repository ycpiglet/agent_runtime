# RESEARCH-2026-06-13-agent-runtime-task-ar-211-official-multi-project-overlay

## Bottom Line

공식 플랫폼 가이드는 멀티 프로젝트 멀티 에이전트 운영에서 공통 런타임과 host overlay 분리를 일관되게 지지한다. 따라서 오버레이만 바뀌고 런타임 핵심은 정합되도록 한 번에 관리하는 방식이 release 안전성을 높인다.

## Research Findings

- Anthropic MCP/Claude Code 계열: 모델-도구 경계는 구성 가능한 허용 목록과 인증 경계로 운영해야 하며, 컨텍스트/출처의 신뢰 경계가 정합되어야 한다.
- OpenAI Agents SDK/Agent eval: 모델/도구/트레이스의 반복 검증이 일회성 성능보다 신뢰성에서 우선.
- 운영 가이드: guardrail, HITL, trace review는 모델 교체 자체보다 정책/감사 체인을 통한 지속성에 강점이 있음.
- 기존 tag_manual 비교 사례: 이름만 이식/누락 분류보다, 의도적 제외(deprecated/dropped)와 기능 누락(missing) 분리가 핵심.

## Application to TASK-AR-211/209/212

- 다중 프로젝트는 런타임 문맥 계층을 `agents/project/*`에서만 바꾸는 방향이 명확함.
- 오버레이는 `ROADMAP/ORG/LINKS/TEAMS`와 `CONTEXT-SOURCES` 간 상호 참조로만 처리.
- migration evidence는 5분류 + 승인/결정일로 audit trace를 유지.
