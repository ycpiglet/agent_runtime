# 재개 인수인계 — 2026-09-28 종료 기준

## 기준과 한계

- 기준은 **2026-09-28 23:59:59 KST**이며, 9월 29일의 모든 변경/대화는 제외했다.
- 기준 원격/커밋: `origin/main` `e5cd5142` (2026-08-04, PR #391). 이 문서는 해당 커밋에서 만든 `codex/handoff-pre-20260929` 브랜치에만 있다.
- 원문 채팅 transcript는 없고, `NEXT-SESSION-POINTER.yml`, `STATUS.md`, task/claim/handoff/review와 Git 이력만 보존돼 있다. 아래는 그 기록의 검증 가능한 재구성이다.

## 목표와 직전 결과

목표는 repository 기반 다중 AI 작업을 위한 재사용 런타임이다. claim-first lifecycle, worktree 격리, T0/T2 재검증, W0~W6 closeout, 사람/역할/증거 분리를 템플릿과 CLI로 제공한다.

마지막 완료 묶음은 `TASKSET-AR-V080-OPERABILITY-HARDENING`의 AR-655와 AR-659이다. AR-655는 장기 claim의 liveness 판단을 reaper/gate/lifecycle/UI/console/Doctor에 일관되게 만들었고, AR-659는 자동 경로가 없는 legacy/orchestrator claim의 소유자 귀속 복구 경로를 만들었다. 포인터는 W4b 독립 검증 후 둘 다 released라고 기록하며, main에는 PR #391으로 통합됐다.

## 정확한 중단/재개 지점

포인터(`updated_at: 2026-08-04T14:18+09:00`)의 상태는 `unclaimed`, task set은 12/12·100%다. 다음 등록 작업은 **`TASK-AR-656` (composable lifecycle hooks) 또는 `TASK-AR-657`** 이며 task set은 free다. 새 작업은 반드시 별도 worktree에서 worker-mode claim으로 시작한다.

중요한 미해결 사실: `TASK-AR-648`이 `claim_guard.py` private index 권한 결함을 소유한다. `chmod 0600` 뒤 `git add`가 기본 umask에서 index를 다시 쓰면 `parallel_worktree_gate`가 transaction을 인식하지 못한다. 포인터가 지목한 재현은 `tests/test_claim_guard.py`이며 umask `0002`에서 21 failed/15 passed, `0077`에서는 36 passed였다. 이것을 영구 baseline으로 받아들이거나 AR-656/657에 무단 흡수하지 않는다.

또한 `claude/llm-wiki` (`5846e40`)는 `deferred_branch_preserved`다. 새 구현을 시작하기 전에 integrate/defer/archive 결정을 별도로 내린다. 버전·태그·package·push·publish·deploy·release는 권한이 없다.

## 새 세션 순서

1. `AGENTS.md`, `CLAUDE.md`, `docs/DEV-ENVIRONMENT.md`, `STATUS.md`, `BACKLOG-BOARD.md`, `agents/project/NEXT-SESSION-POINTER.yml`을 읽는다.
2. `python scripts/work.py status`로 claim/worktree/branch divergence를 읽기 전용 확인한다.
3. AR-656 또는 AR-657의 canonical task/unit, T0 anchor, 기존 claim을 먼저 검토한다. 충돌 없을 때만 dispatcher로 claim을 만든다.
4. W3 구현 뒤 W4a와 worker와 다른 W4b를 거쳐 W5/W6를 수행한다. shared board/index는 orchestrator만 갱신한다.

## 대화 재구성 및 정본

- 반복된 대화의 결론: “stale claim이 영구 block이 되면 안 되며, 자동 복구가 불가능한 claim도 owner-bound exit가 있어야 한다.” 결과가 AR-655/659이다.
- 공통 프롬프트: `AGENTS.md`; Claude 세션 보조 프롬프트: `CLAUDE.md`.
- 현재 정본: `agents/project/NEXT-SESSION-POINTER.yml`, `STATUS.md`, `agents/lead_engineer/tasks/`, `agents/runtime/task_claims/`, `reviews/W4B-2026-08-04-unit-task-ar-655-001-lease-truthfulness-final.md`, `reviews/W4B-2026-08-03-unit-task-ar-659-001-recovery-commands-final.md`.
