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
  canonical_context:
    - agents/project/ROADMAP.md
    - agents/project/ORG.md
    - agents/project/SKILL-DATA-MAP.yml

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
