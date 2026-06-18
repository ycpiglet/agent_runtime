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
  - evidence-librarian
- finance_accounting:
  - finance-controller
  - accounting-operator
  - asset-steward
  - revenue-analyst
- marketing_growth:
  - marketing-lead
  - content-marketer
  - growth-analyst
  - brand-steward
- sales_revenue:
  - sales-lead
  - crm-operator
  - partnership-manager
  - sales-ops

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
- role: evidence-librarian
  level: internal
  boundary: planning proposal source refs, trace ids, verifier evidence 정합성 점검
- role: finance-controller
  level: confidential
  boundary: 가격, 수익화 모델, 청구 기준, 비용 구조, 매출 KPI 제안; 결제/계약 mutation은 Owner 승인 필요
- role: accounting-operator
  level: confidential
  boundary: 장부, 청구, 미수/미지급, 비용 증빙 정리; 외부 회계 시스템 쓰기 작업은 승인 전 금지
- role: asset-steward
  level: internal
  boundary: SaaS 계정, 라이선스, 데이터/콘텐츠 자산, 벤더 목록 관리; secret 값 직접 노출 금지
- role: revenue-analyst
  level: internal
  boundary: 매출, 전환, LTV/CAC, 사용량 기반 과금 지표 분석; 수치 출처와 가정 명시
- role: marketing-lead
  level: internal
  boundary: 포지셔닝, 메시지, 채널 전략, 캠페인 우선순위 제안; 브랜드/법무 리스크는 escalation
- role: content-marketer
  level: internal
  boundary: 소유 채널 콘텐츠 초안, SEO 초안, 예약 게시 패키지 준비; 무단 대량 게시 금지
- role: growth-analyst
  level: internal
  boundary: 캠페인 실험, 퍼널, 채널 성과 분석; 가짜 트래픽/조회수/참여 지표 사용 금지
- role: brand-steward
  level: internal
  boundary: 브랜드 일관성, 금칙 표현, 고객 신뢰 리스크 검토; 과장 광고 차단
- role: sales-lead
  level: confidential
  boundary: ICP, 리드 우선순위, 제안서, 데모 흐름, 영업 전략; 계약 조건 변경은 Owner 승인 필요
- role: crm-operator
  level: confidential
  boundary: 동의 기반 CRM 정리, 후속 연락 일정, 파이프라인 상태 관리; 무단 수집/스팸 발송 금지
- role: partnership-manager
  level: confidential
  boundary: 파트너 후보, 제휴 제안, 공동 캠페인 준비; 외부 약정 체결은 Owner 승인 필요
- role: sales-ops
  level: internal
  boundary: 영업 프로세스, CRM hygiene, 리포트, handoff 품질 점검; 매출 지표 조작 금지

## Growth Automation Boundary

- allowed: 소유 채널 예약 게시, 승인된 API 기반 게시, 동의 기반 CRM 후속 연락, SEO/콘텐츠 분석, 캠페인 성과 리포트
- prohibited: viewbot, 가짜 조회수/트래픽/참여, 무단 대량 게시, 스팸, 약관 위반 자동화, 플랫폼 조작, 출처 없는 리드 수집
- escalation: 자동화가 외부 계정에 쓰기 작업을 하거나 고객/리드에게 직접 발송되면 Owner 승인과 risk-and-safety 검토가 필요하다.

## Escalation Policy

- escalation_condition: 오버레이 누락, 규칙 충돌, 오답률 90% 미달, 정의 미확정, RSI 예산 초과, C-mode 자동 적용 요청, release/version mutation 요청, duplicate task claim, worker in main checkout, 외부 계정 쓰기 작업, 결제/계약 mutation, 플랫폼 조작 또는 스팸성 성장 자동화 요청
- response_deadline: 1 business day
- emergency_owner: owner
