---
type: review
id: REVIEW-2026-06-12-agent-runtime-live-structure-two-layer-decision
audience: owner
status: pass
signal: pass
score: 92
priority: High
tags: [structure, agents, roles, two-layer, governance]
---

# Live Structure Two-Layer Decision Review

## Bottom Line

- Summary: Owner가 "멀티 에이전트 역할(qa/designer/ceo/audit)이 다 사라졌나,
  tag_manual 제거 때문인가"를 질문해 라이브 구조를 전수 조사했고, 사라진 것이
  없음을 확인한 뒤 2층 구조를 계약으로 명문화했다.
- Result: 라이브 체크아웃은 flat 4-lane(`lead_engineer`/`planning`/`project`/
  `runtime`) + 역할=클레임 메타데이터를 유지하고, 역할별 디렉터리 스캐폴드와
  `agents/roles.yml` 정본은 템플릿(`src/agent_runtime/templates/project/agents/`)
  에만 둔다. 라이브 `roles.yml` 복제는 이중 SSoT라서 금지한다.
- Boundary: 문서 정비만 수행(README 2행, AGENTS.md 신규 섹션, 본 기록).
  코드/스키마/게이트 변경 없음. 오케스트레이터 신규 구축 없음 — codex
  멀티페인 관측은 기존 ui-console + task_claims/pane_events로 수행한다.

## Signal

| Check | Signal | Evidence |
| --- | --- | --- |
| 역할 디렉터리 삭제 이력 | pass | `git log --diff-filter=D -- 'agents/<role>/**'` 0건 — 최초 커밋(7d6cbc0)부터 flat |
| tag_manual 제거 영향 | pass | 8579a2/24f3f20은 문구 치환·태스크 등록만, 역할 정의 미접촉 |
| 역할 로스터 생존 | pass | `scripts/release_council_gate.py` REQUIRED_ROLES, `agents/project/MULTIPANE-PROCESS-POLICY.yml` required/monitored roles |
| roles.yml 정본 위치 | pass | 템플릿 19개 역할 디렉터리 + `roles.yml`; `PROJECT-CONTEXT.yml` `do_not_customize_for_project`가 보호 |
| doctor/orchestrator 성격 | pass | `doctor.py --root`는 host runtime health check; `agent_orchestrator.py`는 템플릿 scripts에 실재 |
| 멀티페인 협력 동작 | pass | `agents/runtime/pane_events/pane-events.jsonl` seq 1-12, 클레임 lease/heartbeat 정상, 활성 클레임 0건(전부 released) |

## Insight

- Owner 혼란의 근본 원인은 구조 결함이 아니라 **읽기 경로 문서화 부재**였다.
  라이브 README가 호스트 레이아웃 표를 그대로 노출해 `agents/roles.yml`이
  라이브에 있는 것처럼 읽혔다.
- 라이브 멀티페인은 중앙 오케스트레이터 없이 claim/lease/worktree 규약 기반
  분산 협력으로 동작한다. 규약을 모르는 생짜 세션이 끼어들면 merge-time
  게이트만 사후 방어한다는 리스크는 유효하며, 이는 기존
  TASKSET-AR-WORK-HIERARCHY-CONFLICT-CLOSURE(TASK-AR-370 ID 예약 원장 등)의
  범위에 이미 등록되어 있다.
- 같은 질문이 반복되면 문서가 아니라 구조를 의심하게 되므로, README의
  Repeated Request API 원칙에 따라 채팅 답변을 계약 문서(AGENTS.md 섹션)로
  승격했다.

## Decision

- Decision: 라이브는 flat 유지. 역할별 디렉터리 복원(gstack 방식 라이브 적용)
  기각 — PM 계약("role is a metadata axis")과 lean dogfooding 의도에 위배.
- Decision: 라이브 `agents/roles.yml` 생성 기각 — 템플릿 정본과의 이중 SSoT
  드리프트를 만들고 `do_not_customize_for_project` 정책 취지에 반함.
- Decision: README 역할 행 2곳에 템플릿 정본 경로 병기, AGENTS.md에
  "Live Checkout Layout vs Host Scaffold" 섹션 신설로 재발 방지.
- Decision: 멀티 에이전트 신규 오케스트레이션 구축 없음. codex 페인 관측은
  `python -m agent_runtime.cli ui-console --root <repo> --port 8765` +
  `agents/runtime/task_claims/`·`pane_events/`로 수행한다.

## Risks / Blockers

- Risk: AR-324(Team 조직도 뷰)가 `agents/roles.yml`을 데이터 소스로 명시 —
  구현 시 템플릿 정본 경로로 읽도록 본 결정을 반영해야 한다.
- Blocker: 없음.

## Next Steps

- ui-console 기동으로 codex 페인 관측 표면 검증 (본 세션에서 수행).
- AR-324 구현 착수 시 본 기록을 required input으로 링크.
