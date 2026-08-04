---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-650
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
review_kind: t3-replan
status: accepted
created_at: 2026-07-30T11:58:00+09:00
reviewer: codex-root-task-ar-650-001
trigger_ref: reviews/W4B-2026-07-30-unit-task-ar-650-001.md
---

# TASK-AR-650 W4 계약 순환 차단 재계획

## 판정

독립 W4b의 `REVISE`는 정확하다. Autofolio migration-only contract는
통과하지만, 기존 TASK-AR-650 acceptance가 모든 Runtime P1을 650 종료 전에
0건으로 요구했다. 같은 계획은 그 P1을 TASK-AR-652~657로 분리하고
TASK-AR-651의 선행조건으로 등록했다. 따라서 650 claim을 해제해야 652를
claim할 수 있는데 652를 끝내야 650 claim을 해제할 수 있는 순환 차단이
발생했다.

이 재계획은 P1을 면제하지 않는다. TASK-AR-650의 migration rehearsal
acceptance와 다음 RC의 operability acceptance를 서로 다른 게이트에 배치한다.

## 독립 검증이 잡은 충돌

- Candidate `a224d43c8a42386ac319874754526c911727a932` /
  tree `db619042eafcddaa6cee560c405adafa8e088811`의 exact isolation,
  protected bytes, idempotence, strict migration acceptance는 통과했다.
- pinned evidence는 `model-tier-execution-equivalence`와
  `scribe-source-overdue-active-task-unverified`를 P1으로 정직하게 남겼다.
- 기존 TASK-AR-650 문구는 fresh W4b에서 Runtime P0/P1이 전부 0이어야
  한다고 요구했다.
- TASK-AR-651은 이미 TASK-AR-650과 TASK-AR-652~657을 모두
  `depends_on`으로 가진다.

## T3 결정

1. TASK-AR-650은 Autofolio migration rehearsal 범위에서 새로 발생한
   P0/P1이 없고 exact migration contract가 통과할 때 종료할 수 있다.
2. migration evidence에 정직하게 남긴 공통 operability P1은
   TASK-AR-652~657의 입력이며 삭제하거나 낮추지 않는다.
3. TASK-AR-651과 다음 RC는 TASK-AR-652~657이 모두 독립 W4b를 통과하기
   전까지 계속 차단한다.
4. TASK-AR-658 UI는 P2이며 schema가 안정된 뒤 실행한다.
5. 기존 독립 W4b `REVISE` 기록은 보존한다. 이 재계획 후보에 대해 별도의
   fresh independent W4b를 수행한다.

## 변경되는 계약

TASK-AR-650의 마지막 acceptance는 다음 의미로 좁힌다.

> Canonical W4a와 fresh independent W4b가 exact migration candidate에
> 대해 task-scope Runtime P0/P1이 없음을 확인한다. 발견된 cross-cutting
> operability P1은 등록된 TASK-AR-652~657과 TASK-AR-651 dependency gate로
> 보존하며, 650 종료가 RC readiness를 의미하지 않는다.

## 불변 경계

- Autofolio evidence의 P1/P2 finding을 편집하거나 숨기지 않는다.
- TASK-AR-651 dependency를 제거하거나 약화하지 않는다.
- consumer primary/control/product를 변경하지 않는다.
- version, tag, package, push, publish, deploy, release를 수행하지 않는다.
- claim JSON을 수동 수정하거나 독립 W4b 없이 release하지 않는다.

## 다음 순서

1. task/unit/W4a 계약을 이 결정과 일치시킨다.
2. adoption taskset T0 anchor를 다시 기록한다.
3. fresh independent W4b가 재계획 후보를 검증한다.
4. 승인된 경우 TASK-AR-650 claim을 정상 release하고 W5/W6를 끝낸다.
5. 새 operability taskset에서 TASK-AR-652부터 별도 claim과 W4b로 실행한다.
