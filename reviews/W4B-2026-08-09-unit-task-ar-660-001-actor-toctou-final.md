---
schema_version: agent-runtime-review/v1
id: W4B-2026-08-09-unit-task-ar-660-001-actor-toctou-final
title: TASK-AR-660 Unit 001 Actor TOCTOU Final Independent W4b
date: 2026-08-09
created_at: 2026-08-09T16:51:54+09:00
task_id: TASK-AR-660
unit_id: UNIT-TASK-AR-660-001
claim_id: CLAIM-20260809-125520-task-ar-660-491d
review_claim_id: CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-final
task_set_id: TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION
review_kind: w4b
reviewer: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-final
reviewer_role: independent-auditor
verifier_instance_id: independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-final
worker_instance_id: le-20260809-130000-kst-ar660001
status: blocked
signal: block
score: 35
summary: Exact candidate is blocked by two independently reproduced P1 authority-boundary defects.
verdict: REVISE
priority: P1
finding_counts: {P0: 0, P1: 2, P2: 0}
audited_commit: 02a72e592962af54a848b5e6eba5d3daf218768a
candidate_commit: 02a72e592962af54a848b5e6eba5d3daf218768a
candidate_tree: fe9b7fa4b8f171aa20c2c1580ea6eb6578a0bebb
implementation_range: 6c1f67f4..02a72e592962af54a848b5e6eba5d3daf218768a
independence_status: independent_context_isolated
implementation_reviewed: true
w4b_acceptance: false
release_authorized: false
claim_disposition: remain_claimed_pending_repair_and_fresh_independent_w4b
w4a_ref: reviews/VERIFY-2026-08-09-unit-task-ar-660-001-20260809162712.json
preflight_ref: reviews/ROLE-REVIEW-2026-08-09-TASK-AR-660-INDEPENDENT-AUDITOR-PREFLIGHT.md
t3_ref: reviews/REVIEW-2026-08-09-task-ar-660-unit001-actor-toctou-t3-replan.md
tags: [w4b, task-ar-660, recovery-receipt, actor-registry, attribution, toctou, revise]
---

# TASK-AR-660 Unit 001 actor TOCTOU final independent W4b

## Summary

Exact candidate `02a72e592962af54a848b5e6eba5d3daf218768a`는 독립
검증에서 재현된 두 P1 authority-boundary 결함 때문에 W4b 수용 조건을
충족하지 못한다. 기존 receipt, Owner attribution, historical claim 및
root/template·host-lock 불변식은 유지되지만 판정은 `REVISE`이다.

## Signal

`BLOCK` — `P0: 0, P1: 2, P2: 0`, `w4b_acceptance: false`.

## Action

마지막 actor 재검증을 실제 prepared-receipt publication 경계에 결합하고,
attribution gate가 dispatcher와 동일한 strict canonical registry reader를
사용하도록 수정한다. 세 recovery operation과 세 malformed registry shape에
대한 fail-closed non-mutation 회귀 테스트를 추가한다.

## Risks / Blockers

현재 candidate는 actor registry가 receipt 게시 직전에 사라져도 recovery를
commit할 수 있고, dispatcher가 거부하는 비정규 registry record를 attribution
gate가 canonical authority로 받아들일 수 있다. 두 경로 모두 Unit acceptance의
fail-closed authority 불변식을 직접 위반한다.

## Decision

`REVISE`; Unit 001을 accept, close, merge 또는 release하지 않는다.

## Next Steps

두 P1을 수정한 새 exact candidate에서 fresh Verify와 worker W4a를 생성한 뒤,
다른 verifier instance로 독립 W4b를 다시 수행한다.

## 판정

`REVISE — P0: 0, P1: 2, P2: 0.`

Exact candidate `02a72e592962af54a848b5e6eba5d3daf218768a`는 W4b에서
수용할 수 없다. 기존 양성 회귀 테스트, receipt-first 상태 머신, 기존 두
recovery receipt, Owner provenance, root/template parity 및 host lock은 모두
확인했지만, 독립 임시 fixture에서 현재 acceptance를 직접 위반하는 P1 두
건을 재현했다.

검증자
`independent-auditor-CLAIM-REVIEW-TASK-AR-660-independent-auditor-w4b-final`은
작업자 `le-20260809-130000-kst-ar660001`과 다른 instance이며 작업자 대화와
분리된 문맥에서 exact HEAD를 검토했다. 이 문서가 검증자의 유일한 repository
write이다. 코드, 테스트, claim, task/unit, index, commit, merge, release 및
외부 상태는 변경하지 않았다.

## P1-1 — Final actor revalidation is not bound to receipt publication

`cmd_adopt`와 `cmd_terminalize`는 actor record를 마지막으로 다시 읽은 뒤
`_persist_claim_recovery()`를 호출하고, 그 뒤에야
`recovery_receipt.execute_recovery()`가 prepared receipt를 게시한다.
`activate-store`도 precommit callback 안에서 actor를 다시 읽은 다음 별도
호출로 prepared receipt를 게시한다. 따라서 마지막
`_revalidate_recovery_actor()`와 실제 receipt publication 사이에는 registry
authority가 다시 사라질 수 있는 창이 남아 있다. Cooperative claim-store
lock은 instance registry 파일 자체를 고정하거나 그 inode/digest를 receipt
publisher에 전달하지 않는다.

독립 임시 fixture는 실제 dispatcher와 claim-store를 사용하고 오직
`prepare_recovery_receipt` 호출을 감싸, 마지막 actor 재검증이 끝난 직후
해당 instance record를 unlink했다. 결과는 다음과 같았다.

| Operation | rc | Actor after hook | Durable result |
| --- | ---: | --- | --- |
| `adopt` | 0 | absent | subject changed; pane event changed; `prepared`, `committed` receipts |
| `terminalize` | 0 | absent | subject changed; pane event changed; `prepared`, `committed` receipts |
| `activate-store` | 0 | absent | outer marker `absent -> present`; pane event changed; `prepared`, `committed` receipts |

Probe summary output:

```text
operation=adopt rc=0 actor_present=False prepare_injections=1 subject_changed=True events_changed=True receipts=[prepared, committed]
operation=terminalize rc=0 actor_present=False prepare_injections=1 subject_changed=True events_changed=True receipts=[prepared, committed]
operation=activate-store rc=0 actor_present=False prepare_injections=1 events_changed=True receipts=[prepared, committed]
operation=activate-store rc=0 actor_present=False outer_before=False outer_after=True receipt_count=2
```

유지된 회귀 테스트
`test_recovery_revalidates_actor_registry_inside_the_commit_transaction`는
통과하므로 preflight가 지적한 최초 lookup 직후의 단순 drift 창은 좁혀졌다.
그러나 더 강한 receipt-publication 경계 probe는 동일 acceptance invariant를
다시 깨뜨린다. 즉 preliminary P1을 문서만 신뢰해 닫은 것이 아니라, 수정된
경계에서 독립적으로 재검증한 결과 residual P1이 남아 있다.

필수 수정은 actor record의 direct/canonical byte authority를 실제 prepared
receipt publication precommit까지 결합하는 것이다. Actor disappearance,
replacement 또는 field/digest drift가 그 경계까지 발생하면 claim/marker,
receipt store 및 pane events가 모두 unchanged여야 한다. 세 operation의 위
hook 위치를 고정한 non-mutation regressions가 필요하다.

## P1-2 — Attribution gate accepts registry records the dispatcher rejects as noncanonical

Post-cutoff recovery attribution은 dispatcher가 인정하는 동일한 canonical
instance authority를 요구해야 한다. 그러나 attribution gate의 registry
collector는 ordinary `json.loads`, final-file `lstat`, trimmed text 비교를
사용하며 dispatcher의 duplicate-member, ancestor-alias 및 bounded canonical
text 규칙을 공유하지 않는다.

독립 black-box fixture는 각 malformed registry record와 정확히 일치하는
`claim_recovery_terminalize` event를 cutoff 이후에 만들고 실제
`scripts/attribution_gate.py --check`를 실행했다.

| Registry shape | Attribution gate | Dispatcher actor resolver |
| --- | --- | --- |
| duplicate JSON member (`role`) | `rc=0`, findings 0 | `ValueError: duplicate JSON member 'role'` |
| symlinked `agents/runtime/instances` parent, direct regular entry | `rc=0`, findings 0 | `ValueError: must not use symlink/reparse alias` |
| canonical-looking 161-character role | `rc=0`, findings 0 | `ValueError: invalid canonical role` |

Probe summary output:

```text
CASE=duplicate-member-registry rc=0 findings=0 block=0 watch=0
CASE=symlinked-registry-parent rc=0 findings=0 block=0 watch=0
CASE=oversized-canonical-role rc=0 findings=0 block=0 watch=0
```

각 event의 `actor`, `agent_instance_id`, `actor_role`, `display_name`,
`callsite_id`는 attribution gate가 parse한 record와 정확히 일치했다. 따라서
이는 단순 event mismatch가 아니라 두 authority consumer 사이의 canonicality
분기다. Source와 installed-project template의 attribution gate는
byte-identical이므로 같은 fail-open 경로가 template에도 존재한다.

필수 수정은 attribution gate가 dispatcher와 동일한 bounded strict JSON 및
모든 ancestor no-alias 규칙으로 direct instance record를 읽도록 하는 것이다.
위 세 fixture는 post-cutoff recovery event가 block finding을 내는 regression으로
고정해야 한다.

## 기존 recovery audit 및 불변식

기존 receipt 네 파일은 생성 commit `7b98b69f`부터 exact HEAD까지
byte-unchanged이다. `python scripts/recovery_receipt.py --check`도 pass했다.
독립적으로 persisted/predicted subject bytes를 재구성한 결과 receipt의 길이,
raw digest 및 semantic digest와 정확히 일치했다.

| Transaction image | Bytes | Raw SHA-256 | Semantic SHA-256 |
| --- | ---: | --- | --- |
| activation before | 101 | `b28e59d52bc6da90eb5fd2c761e201e179e3bc45cf29c97483326826557ddb89` | same |
| activation after | 314 | `00159905d9cd2caea54d52aa373381c15779420396497af83afe44c7c3954741` | same |
| adopt before (`d04c1abf` persisted claim) | 5056 | `19dec73e5933e3dcfacadd3b39113eff8fa9cf1197387b43fdaa3003a0eaa775` | `8c15f0dc07d4f372611f3313ef2fa412ebda78c2991bb6bef875fe05289e4921` |
| adopt predicted after | 5925 | `707ca4cdd7201c07f4df2cf97aef51f9ec54502f660bb00d06d37d055eb8e24c` | `478b9481a21d4e3fc3ac85132068df51e9eb098948602c80dc5b665dd9e7d74c` |

Receipt files' SHA-256 values are:

```text
550edb5bcafece81b3d35af7717e777e9ed8564975d9be6bb33ad121d1fa560e  activate-store committed
edace69d36e162b83c922a570e105886e77ac789455556b829347ca12b2b990e  activate-store prepared
5a1b79d4998173da21d94c92f2b01d3c526adac4f05e54727065639c9eb13eed  adopt committed
f13a14092ce28dbbcf95ec2cf677e6260c033803a14d9422084dd2137252b6ef  adopt prepared
```

두 receipt pair의 `owner_id`, pane events 668/669의 `owner_id`, adopt claim의
`recovered_by`는 모두 정확히
`ycpiglet <68498184+ycpiglet@users.noreply.github.com>`이다. Events 668/669의
runtime `actor`, role, display name 및 callsite는 현재 direct registry record
`le-20260809-130000-kst-ar660001.json`과 일치한다. 즉 기존 두 recovery의
Owner attribution invariant는 유지된다. P1은 이 기존 기록을 부정하는 것이
아니라 향후 transaction과 attribution gate가 같은 invariant를 fail closed로
강제하지 못한다는 점이다.

Historical `CLAIM-20260803-002651-task-ar-655-5f27`의 JSON, handoff 및 log는
`6c1f67f4..HEAD`에서 diff가 없었다. Exact HEAD SHA-256은 각각 다음과 같다.

```text
42e536db4e5f5729a9d96fa1e7d5966257a0d47f7882ccb7275523ac9393afd5  .json
72c02cf97d7b105e7306d827ec1acb4279c380ad76f3f729a4f866d7801dcb7f  .handoff.md
21281f4b1974744072874057aea84f425bb41e3f5b21ab7936a9c4a0f4637f29  .log.md
```

## Commands and results

| Command/check | Independent result |
| --- | --- |
| `git rev-parse HEAD HEAD^{tree}` | commit `02a72e592962af54a848b5e6eba5d3daf218768a`; tree `fe9b7fa4b8f171aa20c2c1580ea6eb6578a0bebb` |
| `git diff --stat 6c1f67f4..HEAD` | 54 files; 15074 insertions; 1479 deletions |
| `git diff --check 6c1f67f4..HEAD` | pass |
| Focused actor/attribution regression selection | `18 passed in 3.63s` |
| `PYTHONPATH=src python -m pytest tests/test_recovery_receipt.py tests/test_atomic_io.py tests/test_claim_store.py tests/test_claim_reaper.py tests/test_task_claim_dispatcher.py tests/test_attribution_gate.py tests/test_role_routing.py -q` | `740 passed, 6 skipped in 132.27s` |
| `PYTHONPATH=src python -m pytest tests/test_template_mirror_gate.py tests/test_regen_host_lock_if_needed.py tests/test_template_smoke.py -q` | `36 passed in 20.13s` |
| `python scripts/recovery_receipt.py --check` | pass |
| `python scripts/template_mirror_gate.py --check` | pass; expected/common 87, identical 84, intentional 3, findings 0 |
| Direct `cmp` for dispatcher and attribution source/template pairs | both byte-identical |
| `python scripts/regen_host_lock_if_needed.py --check` | host lock up to date |
| `python scripts/attribution_gate.py --check` | pass; block 0, 907 legacy watch findings; independent malformed-record matrix above still passes incorrectly |
| `python scripts/parallel_worktree_gate.py --check` | pass; one reviewer-bootstrap persistence watch |
| `python scripts/agent_identity_gate.py --check` | pass; findings 0 |
| `python scripts/task_identity.py check --check` | pass; findings 0 |
| `python scripts/plan_assumption_gate.py --taskset TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION --check` | pass; findings 0 |
| `python scripts/rbac_write_gate.py --check` | live overlay exit 1: reviewer claim missing active pointer; exact-HEAD archive pass, findings 0 |
| `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-CLAIM-RECOVERY-WORK-IDENTITY-CORRECTION --check` | live overlay exit 1 due reviewer overlay projection; exact-HEAD archive pass, findings 0 |
| `python scripts/taskset_boundary_gate.py --check` | live overlay exit 1 with 18 reviewer-claim boundary findings; exact-HEAD archive pass, findings 0 |
| `python scripts/owner_governance_gate.py` | live reviewer overlay exit 1; candidate-isolated component checks above distinguish this from exact-HEAD product bytes |
| `git diff --exit-code 7b98b69f..HEAD -- agents/runtime/recovery_receipts` | pass; four existing receipt files unchanged |
| Historical AR-655 claim/handoff/log diff from `6c1f67f4` | pass; unchanged |

양성 suites는 receipt-before-subject, subject-failure state, no-op activation,
RBAC, template mirror 및 host-lock 회귀를 폭넓게 확인한다. 그러나 P1 probe는
그 suites가 고정하지 않은 두 authority 경계를 직접 통과하므로 양성 결과가
판정을 상쇄하지 않는다. Current worktree의 세 governance failure는 검증을
위해 추가된 uncommitted reviewer claim/event overlay에서만 발생했고, 동일
exact HEAD archive에서는 모두 pass했다. 이는 candidate P1로 계상하지 않았다.

## Release decision

**TASK-AR-660 Unit 001을 accept, close, merge 또는 release하지 않는다.**
`w4b_acceptance: false`이며 claim은 repair와 fresh Verify/W4a/독립 W4b가 끝날
때까지 유지해야 한다. 이 기록은 claim release, task/unit completion, commit,
merge, push, tag, publish, deploy 또는 external CI 권한을 부여하지 않는다.
