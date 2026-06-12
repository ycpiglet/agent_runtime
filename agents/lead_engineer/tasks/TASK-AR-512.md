---
id: TASK-AR-512
display_id: TASK-AR-512
task_uid: 94b7763f-4362-4e53-9bd6-b3459c0140dc
registered_at: 2026-06-12T23:15:32+09:00
created_at: 2026-06-12T23:15:32+09:00
updated_at: 2026-06-13T07:50:00+09:00
started_at: 2026-06-13T02:58:37+09:00
completed_at: 2026-06-13T07:50:00+09:00
title: SCM steward skill — periodic hygiene loop + gh PR/issue automation
status: completed
priority: P1
difficulty: L
est_hours: 10
est_tokens: 8000
owner: lead_engineer
project_id: PROJECT-AGENT-RUNTIME-PM-OS
task_set_id: TASKSET-AR-REPO-HYGIENE
planner_model_tier: planner_high
worker_model_tier: worker_standard
reviewer_model_tier: reviewer_high
escalation_triggers:
  - cross_cutting
  - ambiguity
tags:
  - hygiene
  - steward
  - skill
  - pr-automation
  - issue-sync
---

# TASK-AR-512 - SCM steward skill

## Goal

- 형상관리 산출물(branch/worktree/stash/PR/issue/claim)의 "지저분함"을
  사람이 인지하기 전에 주기 점검 루프가 감지·보고·정리하게 한다. Owner
  요청(2026-06-12): "PR, merge, issue, stash, branch 자동화 트리거/훅 또는
  전문 에이전트·스킬로 깔끔하게 유지."

## Context

- 실측 부채(2026-06-12): 워크트리 13개 중 좀비 3+, 브랜치 12개, 회수 안 된
  stash 1건(원본 클레임 이벤트가 들어있었음 — 복원 완료), 모든 merge에서
  BACKLOG-BOARD 충돌.
- 개별 장치는 등록 완료: AR-505(좀비 정리), AR-502(머지 큐), AR-503
  (claim-first), AR-510(릴리스 케이던스). 본 task는 이들을 **하나의 steward
  루프 + 스킬**로 묶고 PR/issue 자동화를 추가한다.
- 스킬 패키징 선례: `skills/taskset-dispatch`, `session-closeout` 등 4개.
- gh CLI는 샌드박스 해제 완료(Owner 적용, 2026-06-12).

## Preconditions

- AR-505(worktree lifecycle gate) 선행 — steward 루프의 정리 액션이 그
  retention 정책을 소비한다.
- gh 쓰기 작업(PR/issue 생성)은 외부 발행 — 초기 모드는 제안(draft)
  전용으로 하고 Owner 정책 승인 후 자동 생성 전환.

## Scope

- `scripts/scm_steward.py` 점검 루프: (a) 좀비 워크트리/merge된 브랜치
  (AR-505 게이트 소비), (b) stale claim(만료 lease), (c) 미회수 stash
  (dirty-intake 보존물 → 회수 판정 안내), (d) 열린 PR aging/draft 방치,
  (e) BACKLOG-BOARD/INDEX 재생성 드리프트 — 종합 리포트 1장.
- gh 연동: task 브랜치 push 시 `gh pr create --draft` 자동(제목=task id,
  본문=claim handoff 링크), closeout merge 시 PR close/comment, W3 인접문제
  intake와 `gh issue` 양방향 동기(생성/완료 close).
- 트리거: 세션 시작(W0 가시성 보강) + 주기 실행(codex cron 또는 Owner 수동
  `/scm-steward`) — 정리 액션은 보고 후 승인 경유, 보고는 비차단.
- `skills/scm-steward/SKILL.md` 패키징 + 템플릿 전파.

## Out Of Scope

- 머지 자동 실행(AR-502 머지 큐 소관), 릴리스 실행(council/Owner 게이트).
- 원격 push 자동화 — Owner 승인 규약 유지.

## Acceptance Criteria

- steward 리포트 1회 실행으로 현재 실측 부채(좀비 3+, stash 0, PR 현황)가
  정확히 집계된다.
- task 브랜치에서 draft PR이 자동 생성되고 closeout에서 닫힌다(데모 1회).
- 정리 액션은 보고-승인-실행 순서를 지킨다(무승인 삭제 0).
- `pytest tests -q` 통과, 게이트 체인 exit 0, W4b 독립 검증.

## Evidence Targets

- `scripts/scm_steward.py` + 테스트 + `skills/scm-steward/SKILL.md`
- steward 리포트 실데이터 1장 + draft PR 데모
- closeout review record

## Completion Evidence

- PR #57 (f934d2e): scripts/scm_steward.py report/clean/pr-open/pr-close/issue-sync with report-approve-execute discipline, gh mutations Owner-gated behind --execute-gh; skills/scm-steward/SKILL.md; mirrors; 25 tests.

## Verification Results

- pytest tests/test_scm_steward.py -q -> 25 passed
- pytest tests -q -> 602 passed (+1 pre-existing)
- real-repo report: zombies=0, 3 unregistered bug issues flagged
- W4b inst-w4b-ar512-verifier -> APPROVE
