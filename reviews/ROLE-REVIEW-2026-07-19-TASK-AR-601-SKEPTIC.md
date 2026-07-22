---
type: role-review
task_id: TASK-AR-601
claim_id: CLAIM-REVIEW-TASK-AR-601-skeptic-closeout
role: skeptic
verdict: fail
reviewed_commit: 43a6b9f
replan_commit: 758659d
w4a_commit: 9d0bfae
reviewed_at: 2026-07-19T11:28:24+09:00
verification_commands:
  - "git show --format=fuller 43a6b9f"
  - "git show --stat 758659d 9d0bfae"
  - "py -3.10 -m pytest tests/test_role_routing.py tests/test_role_routing_wiring.py tests/test_task_claim_dispatcher.py -q -p no:cacheprovider"
  - "py -3.10 scripts/regen_host_lock_if_needed.py --check"
  - "git diff --check 758659d..9d0bfae"
  - "Inject OSError from role_routing.atomic_io.write_json_atomic and inspect claim/handoff/log existence in a TemporaryDirectory"
  - "Create the directory-collision fixture used by test_release_routing_failure_never_breaks_release and inspect whether an exception or artifacts occur"
  - "Release overlay fixtures with overlay markers true, 'true', 1, and '1' while AR_ROLE_ROUTING=1; enumerate nested claim IDs"
  - "Exercise role_routing with config missing/true/false and AR_ROLE_ROUTING missing/1/0"
  - "Inspect root agents/runtime/task_claims/CLAIM-REVIEW-TASK-AR-601-*.json plus referenced handoff/log records"
findings:
  - id: SKEPTIC-601-001
    severity: high
    summary: "The recursion guard is bypassed by truthy non-boolean overlay markers and creates nested REVIEW-REVIEW claims."
  - id: SKEPTIC-601-002
    severity: medium
    summary: "Artifact-before-JSON failure leaves orphan handoff/log files, while the claimed routing-fault test never injects a fault."
  - id: SKEPTIC-601-003
    severity: medium
    summary: "The documented AR_ROLE_ROUTING kill switch cannot disable routing when committed config is present and true."
---

# TASK-AR-601 Skeptic Role Review

## 판정

FAIL. 정상 생성 경로와 boolean `overlay: true` 제어군은 통과하지만, release
경계가 overlay marker의 타입을 검증하지 않아 truthy 비-boolean 값으로 재귀
방지를 우회할 수 있습니다. 또한 artifact-before-JSON 순서는 깨진 claim
노출을 막는 대신 부분 실패에서 orphan을 남기며, 현재 fault-tolerance 테스트는
그 실패 경로를 실제로 실행하지 않습니다.

## 차단 Finding

### SKEPTIC-601-001 — truthy overlay marker가 재귀 방지를 우회함 (High)

release 코드는 다음 exact-identity 조건만 사용합니다.

```python
if claim.get("overlay") is not True:
    role_routing.route_review_pass(...)
```

claim schema 또는 release 입력 경계에는 `overlay` 타입 검증이 없습니다.
동일한 정상 overlay claim을 임시 저장소에서 release하되 JSON marker만 바꾼
실측 결과는 다음과 같습니다.

| JSON marker | release 결과 | 최종 claim 수 | nested overlay |
| --- | --- | ---: | --- |
| `true` (boolean control) | exit 0 | 2 | 없음 |
| `"true"` | exit 0 | 3 | 생성됨 |
| `1` | exit 0 | 3 | 생성됨 |
| `"1"` | exit 0 | 3 | 생성됨 |

생성된 nested ID는 다음 형태였습니다.

```text
CLAIM-REVIEW-REVIEW-TASK-AR-507-independent-auditor-independent-auditor-closeout
```

이는 “overlay release succeeds and does not create nested overlays”라는 acceptance
criterion을 입력 타입에 따라 위반합니다. writer가 현재 boolean을 생성한다는
사실만으로 release 경계의 무검증 JSON, 이전 버전 record, 수동 복구 record를
안전하다고 볼 수 없습니다. boolean만 허용하도록 release 전에 거부하거나,
검증된 overlay predicate로 정규화해야 합니다.

## 추가 Findings

### SKEPTIC-601-002 — 부분 실패가 orphan artifact를 남기며 fault 테스트가 무효함 (Medium)

`_write_overlay_claim`은 handoff, log, claim JSON을 각각 원자적으로 쓰지만 세
파일을 하나의 lifecycle transaction으로 만들지는 않습니다. JSON atomic write에
`OSError`를 주입한 측정값은 다음과 같습니다.

```json
{
  "json_exists": false,
  "handoff_exists": true,
  "log_exists": true
}
```

즉 visible claim이 빠진 대신 두 orphan sidecar가 남습니다. 자동 rollback도,
orphan sidecar cleanup도 없습니다. 오히려 `claim_guard.sweep`은 claim 디렉터리의
untracked 파일을 모두 crash-safety artifact로 커밋할 수 있습니다. 동일 release를
수동 재실행하면 deterministic path를 덮어써 복구할 수 있지만, primary release가
이미 성공한 best-effort routing에는 자동 재시도가 없습니다.

더 중요한 증거 결함은
`test_release_routing_failure_never_breaks_release`가 claim JSON 예상 경로에
디렉터리를 먼저 만든다는 점입니다. `_write_overlay_claim`은 `path.exists()`가
참이면 즉시 `None`을 반환하므로 이 fixture는 atomic write나 예외 경로에 도달하지
않습니다. 실측에서도 exception 없이 `returned=null`, handoff/log 모두 미생성으로
끝났습니다. 따라서 이 테스트는 “routing fault가 release를 깨지 않는다”는 주장을
입증하지 않습니다.

필요한 보정은 staged sidecar를 모두 성공시킨 뒤 publish하고 실패 시 이미 생성한
sidecar를 정리하는 rollback, 또는 orphan을 명시적으로 탐지·복구하는 reconciliation
경로입니다. fault test는 `write_text_atomic`/`write_json_atomic` 예외를 실제로
주입하고 primary release 성공과 orphan 정책을 함께 검증해야 합니다.

### SKEPTIC-601-003 — 실제 config가 있으면 환경 kill switch OFF가 무시됨 (Medium)

모듈 상단은 `AR_ROLE_ROUTING`을 독립 kill switch라고 설명하지만,
`_config_enabled` 결과가 존재하면 환경값은 읽지 않습니다. 임시 root에서 측정한
우선순위는 다음과 같습니다.

| committed config | `AR_ROLE_ROUTING` | enabled | 생성 수 |
| --- | --- | --- | ---: |
| 없음 | 없음 | false | 0 |
| 없음 | `1` | true | 1 |
| 없음 | `0` | false | 0 |
| `true` | `0` | true | 1 |
| `false` | `1` | false | 0 |

실제 root의 `agents/project/role-routing.json`은 `role_routing: true`입니다.
따라서 focused flag-OFF 테스트처럼 config가 없는 fixture에서는 inert하지만,
실제 runtime에서는 `AR_ROLE_ROUTING=0`으로 비상 차단할 수 없습니다. 이 동작이
의도된 config 우선 정책이면 “env override/kill switch” 문서와 검증을 고쳐야 하고,
kill switch가 요구사항이면 환경의 명시적 OFF가 config보다 우선해야 합니다.

## 통과한 증거

| 항목 | 결과 |
| --- | --- |
| Focused suite | `67 passed in 23.19s` |
| Host lock | current |
| Diff quality | `git diff --check 758659d..9d0bfae` exit 0 |
| 정상 boolean overlay release | nested claim 없음, claim 수 2 |
| 실제 root auditor overlay | boolean `overlay: true`, handoff/log 존재 및 pointer 일치 |
| 실제 root skeptic overlay | boolean `overlay: true`, handoff/log 존재 및 pointer 일치 |

root에 실제 생성된 TASK-AR-601 auditor/skeptic overlay 두 건은 정상입니다.
이 결과는 happy path가 동작함을 입증하지만 위 실패 주입과 타입 경계 결함을
상쇄하지 않습니다.

## 재검증 요구

1. overlay marker 타입/의미를 release 전에 검증하고 비정상 값에서 nested claim이
   생기지 않는 회귀 테스트를 추가합니다.
2. handoff/log/JSON 세 단계 각각의 실패를 주입하고 rollback 또는 reconciliation
   정책을 검증합니다.
3. 기존 디렉터리 충돌 테스트를 실제 예외 주입 테스트로 교체합니다.
4. config와 환경 kill switch의 우선순위를 명시하고 실제 root와 동일한 config-on
   fixture에서 ON/OFF를 검증합니다.
5. 수정 후 focused suite, root artifact smoke, taskset gate를 다시 실행합니다.

## 범위 준수

코드, claim, release 상태, `reviews/INDEX.md`, 커밋은 변경하지 않았습니다.
이 skeptic overlay review 문서만 추가했습니다.
