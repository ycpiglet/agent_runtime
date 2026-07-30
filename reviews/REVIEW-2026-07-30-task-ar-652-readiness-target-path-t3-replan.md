---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-652
task_id: TASK-AR-652
unit_id: UNIT-TASK-AR-652-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-07-30T12:32:00+09:00
reviewer: codex-root-task-ar-652-orchestrator
trigger_ref: scripts/wave_dispatcher.py
---

# TASK-AR-652 준비성 경로·실행 경계 T3 재계획

## 판정

`UNIT-TASK-AR-652-001`의 첫 wave dispatch는 claim 또는 worktree를 만들기
전에 준비성 게이트에서 안전하게 중단됐다. 등록된
`tests/test_auto_dispatch.py`와 `tests/test_eval_harness.py`가 존재하지 않았고,
실제 테스트는 generated-host template의 `scripts/` 경계에 있다.

이 재계획은 두 잘못된 경로를 고치고, 이미 등록된 acceptance인
“선택된 tier가 실제 실행을 바꾸고 하나의 영수증으로 증명됨”을 검증할 수
있도록 native worker와 Codex bridge 경계를 명시한다. live provider 호출,
credential 접근, provider 설정, consumer 변경, release 권한은 추가하지
않는다.

## 실패 전 상태

| 점검 | 결과 |
| --- | --- |
| W0 active claim | 0 |
| in-flight task branch divergence | 0 |
| claim 생성 | 없음 |
| worktree 생성 | 없음 |
| provider 호출 또는 외부 효과 | 없음 |
| 준비성 실패 | 존재하지 않는 테스트 대상 2개 |

## T3 결정

1. `tests/test_auto_dispatch.py`는
   `src/agent_runtime/templates/project/scripts/test_auto_dispatch.py`로
   교정한다.
2. `tests/test_eval_harness.py`는
   `src/agent_runtime/templates/project/scripts/test_eval_harness.py`로
   교정한다.
3. receipt가 계획 설정에 머물지 않고 completion 경계에 기록되는지
   검증하기 위해 `agent_worker.py`, `codex_subagent_bridge.py`와 해당
   테스트를 target에 포함한다.
4. role policy가 native packet까지 보존되는지 검증하기 위해
   `subagent_dispatch.py`와 해당 테스트를 target에 포함한다.
5. root와 generated-host의 claim-time routing 계약이 갈라지지 않도록
   root `scripts/task_claim_dispatcher.py`를 target에 포함한다.
6. 검증은 root orchestration 테스트와 template execution 테스트를
   별도 명령으로 실행하고, runtime asset usage gate로 parity를 확인한다.

## 변경 후 검증 경계

- Root orchestration:
  `python -m pytest tests/test_model_routing.py tests/test_task_claim_dispatcher.py tests/test_doctor.py -q`
- Generated-host execution:
  `python -m pytest src/agent_runtime/templates/project/scripts/test_model_routing.py src/agent_runtime/templates/project/scripts/test_subagent_dispatch.py src/agent_runtime/templates/project/scripts/test_codex_subagent_bridge.py src/agent_runtime/templates/project/scripts/test_agent_worker_routing.py src/agent_runtime/templates/project/scripts/test_auto_dispatch.py src/agent_runtime/templates/project/scripts/test_eval_harness.py -q`
- Asset gate: `python scripts/runtime_asset_usage.py --check`

## 불변 경계

- provider를 실제 호출하지 않는다.
- credentials, account, global Codex configuration을 읽거나 변경하지 않는다.
- consumer primary/control/product를 변경하지 않는다.
- dependency 설치, database migration, broker/order, notification, deploy를
  수행하지 않는다.
- version, tag, push, publish, release를 수행하지 않는다.
- 관측되지 않은 model, reasoning, token, cost를 추론하거나 0으로 기록하지
  않는다.
