# RESEARCH-2026-06-09-agent-runtime-official-recommendation-update.md

## Bottom Line

공식 플랫폼에서 제시되는 운영 패턴은 공통 런타임-오버레이 분리, 반복 평가, trace 기반 리뷰, HITL 정책을 중심으로 일치한다. 핵심 리스크는 모델 교체가 아니라 **query 정제·출처 신뢰 계층·강제된 거버넌스 루프의 부재**이다.

## Research Findings

- Anthropic(Claude MCP/Claude Code): 도구 허용 목록, 인증 경계, 실행 맥락을 엄격히 정의해야 런타임 안정성이 높아진다.
- Anthropic(평가/성공기준): 단발성 답변 점수보다 여러 케이스 반복 평가와 실패 재현성이 우선한다.
- OpenAI(Agents SDK/Trace/Grader): trace + grader 루프가 없으면 정확도 개선이 느리고, audit 추적이 깨지기 쉽다.
- OpenAI/Codex 보안 가이드: guardrail, 권한 분리, 승인/로그가 필수.
- 사용자 요청 반영 시 모델 단독 개선보다 **SSoT 랭크 + 질의 필드(범위/시간/오차허용)** 강화가 먼저다.

## 적용 to agent_runtime tasks

- `TASK-AR-201`에서 source_tier/lineage/owner/access_level 메타를 필수 출력으로 고정한다.
- `TASK-AR-202` runbook는 명확화-탐색-실행-적대적검토-검증-기록 순서를 강제하고, 패턴 라이브러리 재사용을 권장한다.
- `TASK-AR-205/206/207/208`는 오프라인 90%, reviewer footer, correction 수집, A2A 추적을 릴리스 전제조건으로 묶는다.
- `TASK-AR-210`의 gate 문서에서 fallback(2026-06-25/2026-06-30)까지 동일 룰로 선명하게 기록한다.
