---
id: TASK-AR-215
status: completed
started_at: 2026-06-09T11:00:00+09:00
owner: lead-engineer
priority: P0
difficulty: M
est_hours: 18
est_tokens: 3000
tags:
  - project-overlay
  - cross-project
  - context-identity
  - migration-evidence
trigger_meeting: yes
created: 2026-06-09
audit_log:
  - BACKLOG.md
  - STATUS.md
  - agents/project/PROJECT-CONTEXT.yml
  - agents/project/ROADMAP.md
  - agents/project/ORG.md
  - agents/project/TEAMS.md
  - agents/project/LINKS.md
  - reviews/MEETING-2026-06-09-agent-runtime-task-ar-215-overlay-packet.md
  - reviews/SEMINAR-2026-06-09-agent-runtime-task-ar-215-overlay-scenario.md
  - reviews/CALL-2026-06-09-agent-runtime-task-ar-215-context-packet-sync-call.md
---

## 목표
다른 프로젝트로 에이전트를 투입할 때 공용 런타임은 유지하고 오버레이만 교체해
vision, roadmap, 조직도, 팀, 링크, 협의기록을 즉시 맥락에 반영하도록 `context packet`을 표준화한다.

## 작업 내용

- `PROJECT-CONTEXT`, `ROADMAP`, `ORG`, `TEAMS`, `LINKS`, `VISION`을 연결한 오버레이 계약 템플릿 고정
- 오버레이 누락/불일치 시 `TASK-AR-204` release-block 경로로 치환
- 오버레이 항목 변경 시 `TASK-AR-204`와 `TASK-AR-213` 규칙으로 승인 근거(`approved_by`, `expiry`, `justification`)를 강제
- 타 프로젝트 시뮬레이션(가상 1건)에서 `task routing`이 `vision/roadmap/org/links/team` 맥락을 반영해 동작하는지 검증

## 완료 조건

- 다른 프로젝트의 컨텍스트 문서 1종류 변경만으로도 런타임 코어를 건드리지 않고 실행 가능한지 검증
- context packet 항목 누락 시 즉시 block 또는 escalation 경로가 남아 있어야 함
- `agents/project/LINKS.md`에 cross-project overlay 링크와 승인 로그를 기록
- 오버레이 패턴(`vision`, `roadmap`, `organization`, `team`, `links`, `communication`)은
  요청마다 query routing output에 반영됨을 최소 1회 증빙
- `TASK-AR-216` 이관 규칙에 맞춰 `hold_for_overlay` 라우팅이 남아야 함

## 증빙

- `agents/project/ROADMAP.md`
- `agents/project/LINKS.md`
- `agents/project/PROJECT-CONTEXT.yml`
- `agents/lead_engineer/tasks/TASK-AR-204.md`/`TASK-AR-210.md`/`TASK-AR-213.md` 교차 링크

## Completion Log: Cross-Project Overlay Simulation (2026-06-09)

- Executable gate: `scripts/overlay_simulation_gate.py`.
- Simulation packet: `agents/project/overlays/simulations/mvp-client-2026-06-09/context-packet-simulation.json`.
- Pass case: `mvp-client-overlay-swap` proves vision/roadmap/organization/team/links/communication can route through overlay files without runtime core edits.
- Hold case: `mvp-client-missing-communication` routes to `hold_for_overlay`, escalates through `TASK-AR-204`, and hands off through `TASK-AR-216`.
- Approval fields are enforced for overlay changes: `approved_by`, `decision_date`, `expiry`, `justification`.
- Evidence report: `reviews/OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215.json`.
- Release artifact check: `publish-bundle --source . --dest .tmp/release-bundle-verify-20260609-overlay-simulation --check` returned `findings=0`.
