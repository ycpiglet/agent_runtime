# AGENTS.md

This repository-level file is the first human-facing behavior contract for
agents working directly in this checkout. The reusable host-project template
continues to live at `src/agent_runtime/templates/project/AGENTS.md`.

## Owner-Facing Language Contract

- 사용자와 직접 대화할 때는 별도 요청이 없는 한 무조건 한국어로 답한다.
- 사용자가 영어로 말해도 "영어로 답해줘"처럼 명시 요청하지 않으면 한국어로 답한다.
- 진행 업데이트, 상태 보고, 질문, 계획, 검토 요약, 최종 보고 모두 한국어가 기본값이다.
- 에이전트 간 메시지, 로그, machine-readable frontmatter, 코드 주석, 테스트명, evidence record는 필요하면 영어를 사용할 수 있다.

## Working Rules

- Keep task work scoped to the active request and existing task records.
- Verify before claiming completion.
- Preserve user changes and do not revert unrelated work.
- For full shared protocol details, mirror updates into
  `src/agent_runtime/templates/project/AGENTS.md` when the rule should apply to
  generated host projects.
