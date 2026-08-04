---
schema_version: agent-runtime-review/v1
work_id: TASK-AR-650
task_id: TASK-AR-650
unit_id: UNIT-TASK-AR-650-001
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
review_kind: runtime-gap-audit
status: complete
created_at: 2026-07-30T11:20:00+09:00
reviewer: codex-root-task-ar-650-001
---

# Agent Runtime 다음 릴리스 하네스 갭 정밀 감사

## 결론

프로젝트마다 별도 하네스를 다시 만드는 방식은 중단하는 것이 맞다.
Agent Runtime의 공통 lifecycle, ownership, claim, Compound, Scribe, routing,
verification을 각 저장소에 **profile + host overlay + 명시적 seam**으로 이식하고,
제품 특성은 host-owned 정책으로 남기는 구조가 Autofolio 3차 리허설에서
실제로 성립했다.

다만 현재 후보를 바로 다음 안정 버전으로 배포하면 안 된다. 마이그레이션
수용 계약은 이번 작업에서 보강됐지만, 사용자가 지적한 세 문제 중
Compound·Scribe·모델 비용은 아직 모두 완결되지 않았다.

- Compound는 claim 전 검색과 closure gate가 있지만, 반복 실패가 선언돼도
  review 또는 retro 하나만 있으면 Compound 없이 종료할 수 있다.
- Scribe는 769개 hot item을 가진 Runtime 자체를 `fresh/ready`로 판정한다.
  projection이 최신이라는 뜻일 뿐 source가 정리됐다는 뜻은 아니다.
- 모델 tier는 선택되지만 여러 provider에서 실제 모델이 합쳐지고, 역할별
  기본 tier와 실제 token/cost receipt가 끝까지 연결되지 않는다.

따라서 다음 안정 버전은 아래 P1 하네스 보강을 선행하고, 세 consumer를 다시
검증한 뒤 RC로 넘어가야 한다.

## 감사 범위와 제외

- 기준 Runtime 후보: `db025d783168b4934ef1260bab0b0b635c9b8f39`
- Autofolio 기준: `ca88433cf155fd03d616584fda7ed4aa3d33fd71`
- 비교 consumer: Bean Wiki green attempt 6, Allimbot green attempt 1,
  Autofolio green attempt 3
- Basketball platform: Owner 지시에 따라 제외
- 외부 provider 호출, credential 접근, package install, deploy, push, tag,
  version 변경, release/publish는 수행하지 않음

## Autofolio가 증명한 공통 구조

Autofolio의 기존 20개 unmanaged path를 새 ownership 모델로 다시 분류한 결과:

| disposition | count | 의미 |
|---|---:|---|
| managed | 6 | downstream patch를 Runtime 정본으로 회수 |
| seed_once | 5 | 초기 seed 뒤 host 운영 데이터로 보존 |
| host_owned | 9 | 제품·역할·보고 정책으로 명시적 분리 |
| generated | 0 | 이번 20개 legacy seam에는 없음 |
| unclassified | 0 | 미분류 없음 |
| temporary conflict | 0 | 임시 충돌 없음 |

추가로 `scripts/status_alias.py`와 `scripts/task_claim_dispatcher.py`도
Runtime managed 상태로 회수했다. 최종 ownership은 managed 229,
seed_once 8, host_owned 14였고, reconcile은 251개 파일에 대해
`safe_updates=0`, `conflicts=0`, `preserved=237`, `excluded=14`로
수렴했다.

이 결과는 “하네스 전체를 각 프로젝트에서 fork”하는 방식이 아니라 다음
3계층을 사용해야 한다는 증거다.

1. Runtime managed core
2. profile/capability 선택
3. host context, role/state/risk overlay와 좁은 ownership 예외

## 이번 작업에서 즉시 보강한 결손

기존 `scripts/pilot_acceptance.py`는 제품 작업을 실행한 파일럿만 표현할 수
있었다. 따라서 Autofolio 같은 migration-only rehearsal에 가짜 completed
task/claim/restart를 만들지 않으면 수용할 수 없었다.

이번 후보에는 다음을 추가했다.

- `agent-runtime-migration-pilot-evidence/v1`
- `agent-runtime-migration-pilot-contract/v1`
- `agent-runtime-migration-seam-ledger/v1`
- exact host/pilot semantic digest 계약
- isolation raw-proof binding
- seam ledger 독립 recount와 before/after digest 검증
- 두 번의 plan/apply snapshot byte equality
- 보호 product byte, zero-effect, no-product-dispatch 검증

Autofolio exact acceptance는 0 findings로 통과한다. 이는 P0 수용기 결손을
해소하지만, 아래 Runtime 운영 결손을 자동으로 고치지는 않는다.

### Work registration dependency 보존

Operability taskset 등록 직후 입력과 생성물을 대조하면서 두 번째 즉시 수정
대상을 발견했다. 등록 JSON의 TASK-AR-657/658에는 `depends_on`이 있었지만
`work.py new`가 이 필드를 조용히 버렸고, wave planner는 두 작업을 선행
스키마 작업과 함께 1파에 배치했다.

이번 후보는 다음 계약으로 보강했다.

- task `depends_on`을 task와 unit frontmatter에 함께 보존
- 새 taskset 내부 참조와 기존 task 참조 허용
- 누락, 잘못된 ID, 중복, self-dependency, cycle을 write 전에 차단
- already-exists replay가 dependency 차이도 충돌로 판정
- root와 consumer template `work.py` byte parity

수리 후 replay는 `already_exists`로 정확히 수렴하고 wave planner는
TASK-AR-657/658을 모든 선언 선행작업 뒤의 4파에 배치한다.

## 미완성 하네스와 가드레일

### P1 — 모델 routing이 비용 절감을 보장하지 못함

근거:

- `scripts/model_routing.py`의 `codex-agent`와 `codex`는
  worker/planner/reviewer 5개 tier가 모두 `gpt-5.2-codex`로 resolve된다.
- native Codex는 worker low/standard가 모두 `gpt-5.6-terra`,
  planner/reviewer가 모두 `gpt-5.6-sol`이다. reasoning effort는 다르지만
  현재 equivalence 판정은 model name만 묶는다.
- Claude agent도 worker_standard/reviewer_standard,
  planner_high/reviewer_high가 각각 같은 모델이다.
- `resolve_subagent_tier("scribe")`, `doc-steward`, `research-agent`는 모두
  명시적 role mapping이 없어 `worker_standard` 기본값으로 떨어진다.
- pilot evidence는 실제 model/token/cost를 관측하지 못했기 때문에 savings를
  모두 `unavailable`로 기록했다.

필요 작업:

- canonical role → default tier 정책을 등록하고 Scribe/탐색/정리 작업은
  low-cost lane을 기본으로 한다.
- native mapping equivalence는 `(model, reasoning_effort)`를 함께 비교한다.
- dispatcher가 요청 tier, resolve 결과, 실제 model/reasoning, input/output
  token, billed cost를 하나의 immutable execution receipt로 남긴다.
- receipt 없는 savings 주장을 계속 차단한다.
- session-only budget이 아니라 task/claim 단위 누적 ledger와 상한을 둔다.
- high tier escalation은 등록된 risk trigger가 있을 때만 허용하고 이유를
  receipt에 남긴다.

### P1 — Scribe projection과 실제 누적 정리가 분리됨

근거:

- Runtime 자체 `STATUS.md`는 `hot_count=769`, `state=overdue`다.
- projection은 fresh라서 `readiness=ready`, `closure_blocking=false`다.
- 선택된 10개 항목은 TASK-AR-646/647/648을 포함하지만 현재 TASK-AR-650은
  포함하지 않는다.
- Autofolio도 272개 hot item에서 projection만 생성한 뒤 ready가 됐다.
- `agents/scribe/SKILL.md`는 15개 초과 시 실제 archive/compression을
  필수라고 선언하지만 `write_projection()`은 generated projection만 쓰며
  source를 정리하지 않는다.

필요 작업:

- projection freshness와 source debt clearance를 별도 상태로 표시한다.
- 현재 active task/claim coverage를 필수로 검증한다.
- overdue source는 projection만으로 closure를 해제하지 않는다.
- Scribe가 실행할 bounded cleanup plan과 cleanup receipt를 생성하고,
  source hot count 감소 또는 명시적 no-touch/owner decision을 검증한다.
- 최신 active record는 보존하고 cold item만 archive하는 deterministic
  candidate selection을 추가한다.
- Scribe 역할은 low-cost lane으로 선택 호출하되 의미 판단은 Doc Steward
  또는 Lead Engineer로 되돌린다.

### P1 — 반복 실패인데도 Compound 없이 종료 가능

근거:

- task claim은 `defect_signatures`와 work ID로 canonical Compound를
  claim persistence 전에 검색한다.
- `closure_gate.decide()`는 compound/review/retro 중 하나만 있으면
  `closure-record-present`로 승인한다.
- 따라서 `repeated_failure` trigger 또는 defect signature가 있는 작업도
  review만 남기고 canonical Compound record 없이 닫을 수 있다.
- root의 `failure-to-regression` skill은 존재하지만 consumer template에는
  출하되지 않는다.

필요 작업:

- `repeated_failure` 또는 defect signature가 있는 task/unit은 linked
  canonical Compound record를 closure 필수조건으로 삼는다.
- record의 prevention ref가 실제 regression/gate/task proposal 중 하나에
  연결됐는지 검증한다.
- `failure-to-regression` skill을 consumer core profile에 출하한다.
- 일반 substantial work는 review/retro 중 하나로 닫을 수 있지만 반복 실패
  lane은 Compound를 생략할 수 없게 분리한다.

### P1 — task claim은 생성 후 갱신 경로가 없음

근거:

- 현재 TASK-AR-650 claim은 08:36 생성, 09:06 만료로 기록됐고 이후
  Compound/Scribe 증거는 10:45까지 이어졌다.
- `task_claim_dispatcher.py` public command는 create, projection, release뿐이다.
- release 때만 `last_heartbeat`가 갱신된다.
- 별도 `claim_lease.py`에는 heartbeat primitive가 있지만 message/lease
  계층이며 task claim JSON lifecycle과 연결되지 않는다.

필요 작업:

- task claim `heartbeat/renew` 명령을 atomic owner-checked mutation으로 추가한다.
- orchestrator progress update와 heartbeat를 한 경로로 묶는다.
- expired active claim은 state sync, doctor, UI에서 같은 severity로 보인다.
- claim, pointer, instance, pane event의 timestamp를 한 receipt로 검증한다.

### P1 — hook 이식은 seed_once 수동 merge에 의존

근거:

- canonical dispatcher는 5개 event, 6개 Runtime command를 제공한다.
- Autofolio의 Owner authority hook은 보존해야 한다.
- 기존 host test와 동작을 지키기 위해 taskset/stop legacy command 두 개를
  canonical dispatcher와 함께 남겼고 Doctor가 duplicate warning 2개를 낸다.
- `.codex/hooks.json`은 seed_once라 upstream이 안전하게 구조를 회수할 수 없다.

필요 작업:

- Runtime lifecycle hook과 host extension hook을 별도 registry로 표현한다.
- install/sync가 semantic identity로 중복을 제거하고 event ordering을 보존한다.
- host authority hook은 extension으로 남기고 Runtime과 동등한 legacy command는
  migration 후 제거한다.
- POSIX/Windows command parity와 timeout budget을 함께 검증한다.

### P1 — consumer용 adoption skill이 없음

근거:

- root에는 `failure-to-regression`, `grill`, `enable`, `scaffold`,
  `rsi-planning-loop` skill이 있으나 consumer template에는 8개 운영 skill만
  출하된다.
- brownfield adopt/sync/migration은 CLI와 문서로는 존재하지만, exact baseline,
  protected manifest, seam ledger, W4a/W4b 순서를 강제하는 trigger skill이 없다.

필요 작업:

- `runtime-adoption` skill을 core profile에 추가한다.
- skill은 pre-adoption doctor → exact baseline/control → ownership plan →
  safe apply → idempotence → protected bytes → isolation/acceptance → rollback
  순서를 강제한다.
- 제품별 하네스를 만들지 않고 host overlay 작성만 요청한다.

### P2 — UI에 Runtime health 표면이 없음

근거:

- UI state resource에는 tasks, claims, ops metrics, notification routing은 있으나
  model execution receipt, Scribe debt, Compound recurrence, migration pilot,
  hook duplicate를 묶은 Runtime health resource가 없다.
- `model_tier`는 task facet으로만 노출되고 실제 model/token/cost 검증 상태는
  owner가 한 화면에서 볼 수 없다.

필요 작업:

- read-only `runtime_health` resource를 추가한다.
- 최소 카드: routing intent vs observation, token/cost budget, Scribe debt와
  active-task coverage, Compound recurrence/coverage, claim expiry, hook health,
  latest pilot/acceptance identity.
- UI는 실행 권한을 얻지 않고 proposal/read-only를 유지한다.

## 필요한 skill과 agent 판단

### 새로 출하할 skill

1. `runtime-adoption` — brownfield 이식과 upgrade rehearsal 전용
2. `failure-to-regression` — 현재 root-only skill을 consumer core로 승격

### 강화할 기존 skill/agent

- `agents/scribe/SKILL.md`: projection이 cleanup 완료가 아님을 명시하고
  cleanup receipt 및 active-task coverage를 추가
- `independent-verification`: migration contract와 exact Runtime receipt를
  W4b 입력으로 추가
- `release-conductor`: 세 consumer exact contract와 P1=0을 RC 선행조건으로 추가

### 새 agent는 지금 필요하지 않음

Scribe, Doc Steward, Independent Auditor, QA, Lead Engineer 역할은 이미 있다.
현재 문제는 agent 수가 아니라 다음 세 연결이 빠진 것이다.

- 역할 → 경제적 model tier
- trigger → 선택적 dispatch
- 실행 → immutable receipt

별도 “cost agent”나 “migration agent”를 추가하면 책임만 중복된다. 비용 검증은
dispatcher/receipt gate가, migration 검증은 `runtime-adoption` skill과
Independent Auditor가 맡는 편이 낫다.

## 다음 릴리스 실행 순서

1. TASK-AR-650
   - Autofolio exact evidence와 migration acceptance를 final commit으로 고정
   - 전체 Runtime suite
   - W4a
   - fresh independent W4b
2. Harness hardening taskset
   - model routing receipt/budget
   - Scribe cleanup loop
   - repeated-failure Compound enforcement
   - task claim heartbeat
   - composable host hooks
   - consumer adoption/failure skills
3. Consumer replay
   - Bean Wiki: editorial/content profile 회귀
   - Allimbot: security-service 및 zero-effect 회귀
   - Autofolio: exact migration replay와 protected-byte 회귀
4. RC 준비
   - final exact product SHA와 template tree
   - clean-tag install/browser/UI smoke
   - release council/W4b
   - Owner 승인 전에는 version, tag, push, publish, deploy를 수행하지 않음

## 등록된 실행 작업

감사 결과는
`TASKSET-AR-V080-OPERABILITY-HARDENING`으로 등록했다. 현재 dispatcher가
선택하는 첫 작업은 TASK-AR-652이며, 등록 순서는 다음과 같다.

| 순서 | 작업 | 우선순위 | 종료 조건 |
| ---: | --- | --- | --- |
| 1 | TASK-AR-652 model execution receipt와 persistent budget | P1 | 실제 관측 없는 비용·절감 주장 불가 |
| 2 | TASK-AR-653 Scribe source debt와 active-work coverage | P1 | projection만으로 overdue 해제 불가 |
| 3 | TASK-AR-654 repeated-failure Compound와 skill 출하 | P1 | 반복 실패가 review만으로 종료 불가 |
| 4 | TASK-AR-655 task-claim heartbeat/renewal | P1 | claim·pointer·UI 만료 해석 일치 |
| 5 | TASK-AR-656 composable lifecycle/host hooks | P1 | semantic dedupe와 ordering 검증 |
| 6 | TASK-AR-657 consumer adoption/failure skills | P1 | clean brownfield migration 절차 강제 |
| 7 | TASK-AR-658 read-only Runtime health UI | P2 | receipt/debt/coverage/expiry/pilot 가시화 |

TASK-AR-651 RC 준비 작업은 TASK-AR-650뿐 아니라 TASK-AR-652부터
TASK-AR-657까지를 선행조건으로 갖도록 갱신했다. UI 작업 TASK-AR-658은
필요하지만 핵심 하네스 안정화와 RC 증거 생성을 막지는 않는다.

## 현재 판정

- Autofolio migration rehearsal: 기술적으로 pass
- migration acceptance harness: pass
- 다음 안정 버전 release readiness: blocked
- 차단 사유:
  - TASK-AR-650 fresh independent W4b 미실행
  - model routing, Scribe, Compound, task-claim, hook, adoption skill P1 미해소
