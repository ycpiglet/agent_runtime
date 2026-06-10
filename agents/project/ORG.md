# Organization (Host Overlay)

## Ownership

- product_owner: owner
- decision_owner: lead-engineer
- escalation_owner: managing-partner
- review_owner: independent-auditor

## Team Structure

- engineering_team:
  - ceo
  - lead-engineer
  - backend
  - qa
  - doc-steward
  - independent-auditor
  - owner
- planning_office:
  - planning-coordinator
  - roadmap-steward
  - task-architect
  - prioritization-analyst
- release_integrity:
  - version-steward
  - release-governor
  - compatibility-auditor
  - evidence-librarian
- rsi_lab:
  - retro-synthesizer
  - compound-analyst
  - failure-forecaster
  - improvement-architect
- evaluation_office:
  - trace-analyst
  - grader-designer
  - eval-curator
  - live-reviewer
- risk_and_safety:
  - drift-guard
  - sandbox-governor
  - approval-router
  - budget-controller
- diversity_council:
  - skeptic
  - advocate
  - explorer
  - stabilizer
  - pragmatist
  - systems-thinker
  - user-impact-reviewer

## Authority and Access

- role: owner
  level: secret
  boundary: 변경 승인, 공개 게이트 최종 사인오프
- role: lead-engineer
  level: confidential
  boundary: TASK 패키징, gate 근거 정합
- role: doc-steward
  level: internal
  boundary: 오버레이/리뷰/감사 증적 운영
- role: planning-coordinator
  level: internal
  boundary: planning scan/proposal outbox 운영, canonical apply 전 승인 확인
- role: version-steward
  level: internal
  boundary: 버전/릴리스/태그/승인 정합성 점검, mutation 금지
- role: retro-synthesizer
  level: internal
  boundary: review/compound/retro 기반 예방 task 제안, 직접 적용 금지
- role: trace-analyst
  level: internal
  boundary: trace/eval/grader/correction/A2A 근거 연결
- role: worktree-dispatcher
  level: internal
  boundary: task별 worktree/branch/claim 생성과 해제 제안, shared SSoT 직접 병합 금지
- role: drift-guard
  level: internal
  boundary: RSI 예산/반복/드리프트/kill switch 기준 강제
- role: diversity-council
  level: internal
  boundary: 비판/옹호/탐색/안정화 관점 제공, 최종 승인권 없음

## Escalation Policy

- escalation_condition: 오버레이 누락, 규칙 충돌, 오답률 90% 미달, 정의 미확정, RSI 예산 초과, C-mode 자동 적용 요청, release/version mutation 요청, duplicate task claim, worker in main checkout
- response_deadline: 1 business day
- emergency_owner: owner
