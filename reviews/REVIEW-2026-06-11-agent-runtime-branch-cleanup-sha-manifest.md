# REVIEW-2026-06-11 — Branch Cleanup SHA Manifest

- Bottom Line: 로컬 archive 브랜치 6개와 원격 archive/stashes 17개 + archive 1개 + fix 1개를 삭제하기 전, 복구용 SHA를 영구 기록한다.
- Signal: 모든 UI 아카이브 브랜치는 main 대비 strict subset(구버전 스냅샷)임을 two-dot diff로 검증했다. main이 UI 최종본을 보유한다.
- Insight: closeout 기록 커밋만 main에 들어가고 기능 커밋은 미병합이라는 가설은 틀렸다 — 기능은 81bbd18/PR#7 경유로 main에 흡수됐고, 브랜치는 잔재였다.
- Decision: 전부 삭제 (Owner 지시: 2026-06-11 세션 goal #1). 복구는 아래 SHA로 가능(GitHub dangling object 보존 기간 내) 하다.

## 삭제 대상 로컬 브랜치

| branch | sha |
| --- | --- |
| archive/codex-task-ar-279-ui-design-implementation-20260611 | ab53268 |
| archive/codex-task-ar-280-ui-design-implementation-20260611 | 2107e1f |
| archive/codex-task-ar-281-ui-design-implementation-20260611 | 1807df9 |
| archive/codex-task-ar-283-ui-design-implementation-20260611 | 3583fd4 |
| archive/codex-task-ar-284-ui-design-handoff-20260611 | 373bd0e |
| archive/ui-console-backlog-cleanup-20260611 | 36b1e1a |

## 삭제 대상 원격 브랜치 (origin)

| branch | sha |
| --- | --- |
| archive/stashes/20260611/backlog-ui-operations-4456f2d | 4456f2d9115be4c7478df280f3a18559f069c392 |
| archive/stashes/20260611/late-backlog-board-tasksets-test-9867d85 | 9867d858dc5b1cb497937f0e29193fb633730882 |
| archive/stashes/20260611/late-task-identity-taskset-1df0934 | 1df0934fb0195a922ffc3e54c83ac07cbdcad364 |
| archive/stashes/20260611/post-merge-excluded-generated-320f507 | 320f507dbc8e49ba43b2b7ebaf37fa531ca7ec20 |
| archive/stashes/20260611/post-merge-excluded-tracked-20458c6 | 20458c633718a21929a27cb2ef27c5632e8a2016 |
| archive/stashes/20260611/task-ar-201-context-knowledge-6f308ce | 6f308ce0be2aeec1ee54585143b8fdff4e99db83 |
| archive/stashes/20260611/task-ar-205-quality-loop-216d739 | 216d7393d7299262da1ff48d02fcec30d2afbdfd |
| archive/stashes/20260611/task-ar-207-quality-loop-7430720 | 7430720fd33f3738cdc776a0075fe466a9ee6d61 |
| archive/stashes/20260611/task-ar-209-migration-parity-e37911b | e37911bb926692bc30f95de0cd2e7070c5c57139 |
| archive/stashes/20260611/task-ar-210-release-steward-e72b7f3 | e72b7f3eb522b9262a2ec123590159de71303e10 |
| archive/stashes/20260611/task-ar-217-quality-loop-3717066 | 3717066fee843963680028cc782ee8753afa5ff1 |
| archive/stashes/20260611/task-ar-219-release-steward-b2a8f48 | b2a8f489914ba3490ac314b464ccbad96554c4a8 |
| archive/stashes/20260611/task-ar-222-release-steward-a0a9286 | a0a9286197283fb13a8289c6fcc7a304b193ba49 |
| archive/stashes/20260611/task-ar-223-release-steward-49d8024 | 49d80240a4bbbceec59b0349352a745855c91ba2 |
| archive/stashes/20260611/task-ar-240-release-steward-49d8fbe | 49d8fbe11529347ee24f38efd4d9e77354875c39 |
| archive/stashes/20260611/task-ar-248-pane-progress-5cf3031 | 5cf303193b67e1b646bc39dc14f2e4a40d59da28 |
| archive/stashes/20260611/taskset-4-closeout-untracked-301661b | 301661bca389c3ba9e5c8a62069388b9e0c2f872 |
| archive/ui-console-backlog-cleanup-20260611-36b1e1a | 36b1e1a789376f048129b07d637d153a35847c8e |
| fix/template-clean-install-green (PR #2 CLOSED, task.schema.json은 main에 반영됨) | 677246ca9b58a0615f2848d3d828ef01b847ca08 |

- Action Board: 삭제 실행 후 `git fetch --prune` 확인. 이후 복구 필요 시 `git fetch origin <sha>` 또는 GitHub API로 커밋 조회.
- Next: 세션 closeout 기록(REVIEW-2026-06-11 session feedback)에서 본 매니페스트를 링크.
