# REVIEW-2026-06-09-agent-runtime-project-context-overlay.md

## Bottom Line

`agent_runtime`을 여러 host 프로젝트에 투입할 때 공통 runtime skill이 host별로 갈라지지 않도록 `agents/project/` 컨텍스트 오버레이를 추가했다. 다음 공개 후보는 `v0.1.6`으로 둘 수 있다.

## Signal

| 항목 | 상태 | 근거 |
|---|---|---|
| project context overlay | pass | `agents/project/README.md`, `PROJECT-CONTEXT.example.yml`, `teams/.gitkeep` 추가 |
| context packet integration | pass | `scripts/agent_context_packet.py`가 `agents/project/*`를 역할 패킷에 자동 포함 |
| missing hook migration | pass | `.githooks/pre-commit` 템플릿 추가 |
| `.agents` source skill | intentionally excluded | sanitize 정책상 `.agents/`는 public package forbidden path |
| focused tests | pass | `tests/test_project_context_overlay.py tests/test_doctor.py -q` => `10 passed` |
| bundle release preflight | pass | `.tmp/release-bundle-context-overlay` 기준 `findings=0` |
| source-root release preflight | blocked | `source=.` 기준 `findings=131`, `sanitize=0`, `.git`/unexpected source files remaining |

## Insight

- host 프로젝트에서 공통 `agents/*/SKILL.md`를 직접 튜닝하면 업데이트 충돌과 role drift가 생긴다.
- 프로젝트 고유 아이디어, 비전, 목적, 로드맵, 조직도, 링크는 host-owned `agents/project/`에 둬야 한다.
- `agent_context_packet.py`가 이 overlay를 자동 포함하면, 공통 스킬은 유지하면서 프로젝트별 맥락만 바뀐다.
- `tag_manual`에서 분리 시 모든 history/state 파일이 이식되지 않은 것은 의도에 가깝다. 다만 `.githooks/pre-commit`은 공통 운영 자산이라 이번에 이식했다.

## Decision

- `v0.1.6`에는 project context overlay, context packet 자동 포함, `.githooks/pre-commit` 이식을 포함한다.
- `.agents/skills/source-command-backlog`는 직접 템플릿 이식하지 않는다. `/backlog`는 `scripts/install_hooks.py`의 로컬 커맨드 설치 경로로 유지한다.
- 실제 publish 전 P0-1(`source=.` 정책) 또는 bundle-only SOP 공식화를 마무리한다.
