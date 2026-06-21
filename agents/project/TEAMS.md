# Teams (Host Overlay)

- team_id: agent-runtime-core
  purpose: 공통 런타임과 릴리스 게이트의 기술 실행
  lead: lead-engineer
  roles:
    - lead-engineer
    - backend
    - qa
    - doc-steward
    - ci-cd
    - independent-auditor
    - worktree-dispatcher
  canonical_context:
    - agents/project/ROADMAP.md
    - agents/project/ORG.md
    - agents/project/SKILL-DATA-MAP.yml
    - docs/PARALLEL_AGENT_WORKTREE_PROTOCOL.md

- team_id: governance-loop
  purpose: 감사/릴리스 승인/의사결정 기록과 규칙 이관
  lead: managing-partner
  roles:
    - managing-partner
    - independent-auditor
    - doc-steward
    - scribe
  canonical_context:
    - agents/project/LINKS.md
    - agents/lead_engineer/tasks/TASK-AR-210.md
    - agents/lead_engineer/tasks/TASK-AR-204.md

- team_id: project-context
  purpose: 비즈니스 맥락, 조직도, 로드맵 반영
  lead: ceo
  roles:
    - ceo
    - owner
    - secretary
  canonical_context:
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/ORG.md

- team_id: finance-accounting
  purpose: 혼합 수익 모델(B2B SaaS + 콘텐츠/제휴 성장)의 가격, 청구, 비용, 자산, 라이선스, 매출 지표 관리
  lead: finance-controller
  roles:
    - finance-controller
    - accounting-operator
    - asset-steward
    - revenue-analyst
  canonical_context:
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/ORG.md

- team_id: marketing-growth
  purpose: 제품 포지셔닝, 브랜드 메시지, 콘텐츠 캘린더, SEO, 캠페인 실험, 채널별 성과 분석
  lead: marketing-lead
  roles:
    - marketing-lead
    - content-marketer
    - growth-analyst
    - brand-steward
  canonical_context:
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/LINKS.md

- team_id: sales-revenue
  purpose: ICP/리드 정의, CRM 파이프라인, 데모/제안서, 파트너십, 합법적 예약 게시와 홍보 운영
  lead: sales-lead
  roles:
    - sales-lead
    - crm-operator
    - partnership-manager
    - sales-ops
  canonical_context:
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/ORG.md

- team_id: operations-support
  purpose: 운영 런북, 고객/사용자 지원 패킷, 이슈 분류, SLA/응답 품질, 내부 프로세스 개선
  lead: operations-lead
  roles:
    - operations-lead
    - support-operator
    - customer-success-steward
    - process-steward
  canonical_context:
    - agents/project/BUSINESS-OPERATING-SYSTEM.md
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/ORG.md
    - agents/project/ROADMAP.md

- team_id: planning-strategy
  purpose: 사업 전략, 우선순위, 실행 단위 분해, 요구사항 분석, 포트폴리오/로드맵 정합성
  lead: strategy-lead
  roles:
    - strategy-lead
    - planning-architect
    - business-analyst
    - portfolio-steward
  canonical_context:
    - agents/project/BUSINESS-OPERATING-SYSTEM.md
    - docs/superpowers/plans/
    - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
    - reviews/

- team_id: planning-office
  purpose: 사이클 종료/일정/진척도 기반 planning scan과 proposal outbox 운영
  lead: planning-coordinator
  roles:
    - planning-coordinator
    - roadmap-steward
    - task-architect
    - prioritization-analyst
  canonical_context:
    - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
    - BACKLOG.md
    - STATUS.md
    - agents/project/STATE-MACHINES.yml

- team_id: release-integrity
  purpose: 버전, 릴리스 상태, 태그, 승인, release evidence 정합성 점검
  lead: version-steward
  roles:
    - version-steward
    - release-governor
    - compatibility-auditor
    - evidence-librarian
  canonical_context:
    - agents/project/ROADMAP.md
    - agents/project/release/RELEASE-DECISION-v0.1.8.yml
    - agents/project/release/OWNER-APPROVAL-v0.1.8.yml
    - BACKLOG.md

- team_id: rsi-lab
  purpose: 과거 이력, review, compound, retro를 읽고 예방형 개선 제안을 생성
  lead: retro-synthesizer
  roles:
    - retro-synthesizer
    - compound-analyst
    - failure-forecaster
    - improvement-architect
  canonical_context:
    - agents/lead_engineer/compound_log.md
    - reviews/
    - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md

- team_id: evaluation-office
  purpose: trace, grader, eval, correction, live review, A2A 증거를 planning evidence로 연결
  lead: trace-analyst
  roles:
    - trace-analyst
    - grader-designer
    - eval-curator
    - live-reviewer
  canonical_context:
    - AGENTIC_KNOWLEDGE_EVAL_PLAN.md
    - agents/project/evals/
    - agents/project/corrections/
    - agents/project/a2a/

- team_id: risk-and-safety
  purpose: RSI budget, drift, sandbox, approval, kill switch, non-divergence 정책 관리
  lead: drift-guard
  roles:
    - drift-guard
    - sandbox-governor
    - approval-router
    - budget-controller
  canonical_context:
    - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
    - AGENT_RUNTIME_PARALLEL_SESSION_PROTOCOL.md
    - agents/project/STATE-MACHINES.yml
    - .codex/hooks.json

- team_id: diversity-council
  purpose: 같은 주제에 대해 서로 다른 성향의 비판/옹호/탐색/안정화 관점을 제공
  lead: council-facilitator
  roles:
    - skeptic
    - advocate
    - explorer
    - stabilizer
    - pragmatist
    - systems-thinker
    - user-impact-reviewer
    - evidence-librarian
  canonical_context:
    - reviews/RESEARCH-2026-06-10-agent-runtime-rsi-and-planning-loop-research.md
    - AGENT_RUNTIME_RSI_PLANNING_BRIEF.md
    - agents/project/ORG.md
    - agents/project/DIVERSITY-COUNCIL-PROTOCOL.md
