# REVIEW-2026-06-08-agent-runtime-recompare-after-pass-18

Bottom Line: PASS-17에서 남아 있던 병렬 처리의 핵심 위험 중 하나(권한 상실 상태에서의 중복 reply/write)가 줄었고, 메시지 소유권 체크를 보강해 worker/dispatch 경로의 idempotency를 한 단계 높였습니다.

## Signal

| Item | State | Evidence |
|---|---|---|
| PASS-17 대비 변경 | Y | `test_has_active_claim_reflects_owner` / `test_mark_answered_accepts_existing_reply_as_completed` 신규 추가 |
| 메시지 큐 오너 가드 | Y | `has_active_claim` 추가 및 owner mismatch/claim staleness 체크 강화 |
| worker/dispatch reply 가드 | Y | `agent_worker.py`, `auto_dispatch.py`에서 claim/기존 reply 존재 확인 후 reply 작성/상태 전이 |
| 테스트 회귀 | Y | `C:\\Users\\ycpig\\AppData\\Local\\Programs\\Python\\Python310\\python.exe -m pytest tests -q` → `129 passed` |
| 잔존 Top-3 | R | 분산/원격 FS claim 경합, 셸 우회 시나리오, 지속적 self-improvement 루프는 여전히 미해결 |

## Insight

1. `message_queue.mark_answered`는 reply가 이미 존재할 때 완료 처리로 되돌리는 동작을 갖게 되었고, claim 소유권이 유실된 worker가 소란스러운 상태로 남지 않도록 idempotency를 강화했습니다.
2. `agent_worker`는 claim 획득 직후, 처리 직전, reply 작성 직후의 소유권 상태를 분기별로 점검하고, 중복/미완료 reply를 줄이는 쪽으로 흐름을 바꿨습니다.
3. 이 단계의 정량 개선은 분산 FS의 극단 시나리오까지 보장하지는 못하므로, 다음 사이클은 분산/원격 저장소 특성을 모사한 claim 경합 테스트와 command profile bypass 테스트 확장으로 가야 합니다.

## Decision

1. PASS-18은 **실행 중 claim 소유권 기반 duplicate-write 방지**를 닫은 것으로 분류.
2. 남은 2개+항목(분산 FS 경합, 셸 우회/우회 패턴, self-improvement loop)은 다음 패스에서 별도 리뷰/실험으로 분리해 진행한다.
