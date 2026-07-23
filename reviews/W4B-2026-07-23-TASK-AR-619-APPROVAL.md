---
title: TASK-AR-619 Final CI-Aware Independent W4b Approval
date: 2026-07-23
signal: pass
score: 100
verdict: APPROVE
task_id: TASK-AR-619
verified_head: 6dba6858df6cbc70ce7e6815cd650c07785945a4
initial_reviewed_implementation: cac32994b7cb845e3652f7bfd93f0f74d552019e
verified_implementation: 986f1184f34e5f830e26c4affddfb00bbd39470c
verified_by: codex-task-ar-619-independent-auditor-20260723
worker: codex-root-worker
tags:
  - w4b
  - independent-verification
  - approval
  - test-isolation
  - release-cadence
  - ci-matrix
---

# TASK-AR-619 Final CI-Aware Independent W4b Approval

## 판정

**APPROVE — 100/100.** 정확한 current HEAD `6dba6858df6cbc70ce7e6815cd650c07785945a4`에서 구현 범위, hermetic query injection, retry 호출 수, 오류 우선 의미, 무변경 경계, query-range hardening 및 최신 W4a를 독립 검증했다. PR #336 Actions run `29975465431`도 같은 head SHA에서 Python 3.10/3.11/3.12 **3-of-3 success**다. blocker 또는 high-severity 회귀는 발견되지 않았다.

## 범위와 변경 경계

GitHub PR #336의 최종 변경은 11개 파일이다.

- test implementation: 2개
  - `tests/test_release_cadence_trigger.py`
  - `tests/test_release_auto_noncritical.py`
- task/unit 및 W4a evidence/index: 7개
- W4b review records: 2개
- production 파일: **0개**

production script, template, workflow, package source는 변경되지 않았다. 초기 구현 `cac32994b7cb845e3652f7bfd93f0f74d552019e`의 두 deterministic responder와 injection assertion은 현재 HEAD에 유지된다. 이후 `986f1184f34e5f830e26c4affddfb00bbd39470c`가 Git argument prefix 비교를 baseline tag/range/path까지 포함한 exact match로 강화하고 wrong-range rejection test 2개를 추가했다. 초기 구현 삭제나 assertion 완화가 아니다. 두 test 파일의 `cac32994..HEAD` scoped diff check는 통과했다.

## Cadence injection 격리

두 test module의 `_successful_cadence_query()`는 다음 전체 cadence query surface에 deterministic 응답을 제공한다.

1. baseline tag: `git describe --tags --abbrev=0`
2. commit subjects: `git log --format=%s`
3. commit count: `git rev-list --count`
4. tag time: `git log -1 --format=%ct`
5. breaking messages: `git log --format=%s%n%b%x00`
6. template diff: `git diff --name-status`
7. schema diff: `git diff --name-only`

### 실제 Git 차단 probe

cadence per-query injection family를 직접 호출하면서 process-global `subprocess.run`을 실패 sentinel로 교체했다.

- query scenario: selected 6종 + both-diff 1종 = 7개
- forbidden real subprocess calls: **0**
- selected query calls: 각 **3회**
- both-diff calls: **6회**

즉 injection 이후 non-target cadence query는 실제 Git으로 위임되지 않고 deterministic responder에서만 처리됐다. helper가 모르는 query는 `AssertionError`로 즉시 실패하므로 새 production query가 조용히 real Git으로 빠지는 fallback도 없다.

### Release-auto injection family

실제 fixture 저장소는 injection 전에 생성하고, 그 뒤 cadence facade의 모든 명령을 추적했다.

- cadence calls: 11
- deterministic non-target calls: 5
- selected diff retry calls: 6
- real-Git fallback from cadence facade: 0
- result: `trigger-error`
- git query errors: 2
- `mutated`: false
- tags before/after: `[v0.2.0]`로 동일
- `pyproject.toml` version before/after: byte-identical

## 오류 우선 및 무변경 의미

Cadence report는 일부 성공 metric이 있어도 selected query가 모두 실패하면 다음 계약을 유지했다.

- `status=error`
- `triggered=false`
- `finding=None`
- `reason=git-query-error`
- `recommended_bump=None`
- `recommended_version=None`
- query별 구조화된 error evidence 유지

Release-auto는 같은 상황을 `RESULT_TRIGGER_ERROR`로 승격하고 `mutated=false`를 유지했다. 독립 snapshot에서 tag와 version도 실제로 변하지 않았다.

## 호출 수

Parameterized selected query 6종은 각각 retry limit만큼 정확히 3회 호출됐다.

| Query family | 호출 수 | 결과 |
|---|---:|---:|
| subjects | 3 | PASS |
| commit-count | 3 | PASS |
| tag-time | 3 | PASS |
| breaking | 3 | PASS |
| template-diff | 3 | PASS |
| schema-diff | 3 | PASS |
| 양쪽 diff 합계 | 6 | PASS |
| release-auto 양쪽 diff 합계 | 6 | PASS |

## 초기 reviewed implementation 20회 반복 안정성

다음 두 node를 한 묶음으로 20회 연속 실행했다.

```text
tests/test_release_cadence_trigger.py::test_each_partial_query_failure_invalidates_triggered_report
tests/test_release_auto_noncritical.py::test_partial_cadence_query_error_halts_even_when_commit_threshold_fires
```

각 회차는 parameterized 7 tests이며 첫 실패 시 즉시 중단하도록 실행했다.

- 반복: **20/20 pass**
- 합계: **140/140 tests pass**
- 회차별 시간 범위: 8.92s ~ 16.56s
- zero-call 또는 retry-count flake: 0

별도 worker-side 20회 transcript는 W4a JSON에 포함되어 있지 않아 원 기록 자체의 회차 로그는 추적할 수 없었다. 대신 초기 reviewed W4a HEAD `00c94a16`에서 독립적으로 20회를 재실행해 해당 안정성 주장을 직접 확인했다. 현재 HEAD는 그 responder를 제거하지 않고 exact-range guard를 강화했으며, 최신 focused/W4a/CI 결과는 아래에 별도로 기록한다.

## W4a evidence 검토

### 최신 Task

`reviews/VERIFY-2026-07-23-task-ar-619-20260723110846.json`

- actor: `codex-root-worker`
- focused files: 86 passed in 269.85s
- selected nodes: 7 passed in 10.34s
- taskset gate: pass, findings=0

### 최신 Unit

`reviews/VERIFY-2026-07-23-unit-task-ar-619-001-20260723110342.json`

- actor: `codex-root-worker`
- focused files: 86 passed in 274.47s
- selected nodes: 7 passed in 8.09s
- taskset gate: pass, findings=0

### 초기 Task

`reviews/VERIFY-2026-07-23-task-ar-619-20260723103734.json`

- actor: `codex-root-worker`
- focused files: 84 passed in 264.99s
- selected nodes: 7 passed in 13.32s
- taskset gate: pass, findings=0

### 초기 Unit

`reviews/VERIFY-2026-07-23-unit-task-ar-619-001-20260723103124.json`

- actor: `codex-root-worker`
- focused files: 84 passed in 273.21s
- selected nodes: 7 passed in 8.97s
- taskset gate: pass, findings=0

초기 evidence는 `00c94a16`에, 최신 evidence는 exact-range hardening 이후 현재 HEAD ancestry에 포함된다. task/unit frontmatter의 최신 evidence ref 및 actor와 일치한다. evidence JSON 자체에는 git HEAD 필드가 없으므로 commit inclusion, ancestry, PR head OID 및 CI run head SHA로 최종 HEAD 연결을 확인했다.

## 현재 HEAD 독립 실행 결과

```text
py -3.10 -m pytest tests/test_release_cadence_trigger.py::test_successful_cadence_query_rejects_wrong_range tests/test_release_auto_noncritical.py::test_successful_release_auto_cadence_query_rejects_wrong_range tests/test_release_cadence_trigger.py::test_each_partial_query_failure_invalidates_triggered_report tests/test_release_auto_noncritical.py::test_partial_cadence_query_error_halts_even_when_commit_threshold_fires -q
py -3.10 scripts/taskset_work_gate.py --check
git diff --check cac32994..HEAD -- tests/test_release_cadence_trigger.py tests/test_release_auto_noncritical.py
```

결과:

```text
9 passed in 12.41s
taskset-work-gate: pass
findings=0
scoped diff check: pass
```

현재 두 test 파일은 초기 helper surface를 유지하면서 exact range/path만 더 엄격히 검증한다. source inspection에서 selected call `== 3`, both-diff `== 6`, `RESULT_TRIGGER_ERROR`, `mutated is False`, deterministic non-target responder delegation assertion도 모두 유지됨을 확인했다.

## GitHub PR 및 CI matrix 독립 확인

### PR #336

- title: `test: isolate release cadence query-failure injection`
- base: `main`
- head branch: `codex/task-ar-619-cadence-injection-isolation`
- head OID: `6dba6858df6cbc70ce7e6815cd650c07785945a4`
- state: `MERGED`
- URL: `https://github.com/ycpiglet/agent_runtime/pull/336`

PR head OID, origin branch HEAD 및 로컬 `git rev-parse HEAD`는 모두 일치한다.

### Actions run 29975465431

- workflow/event: `test` / `pull_request`
- status/conclusion: `completed` / `success`
- head SHA: `6dba6858df6cbc70ce7e6815cd650c07785945a4`
- URL: `https://github.com/ycpiglet/agent_runtime/actions/runs/29975465431`

| Job | Job ID | 결론 |
|---|---:|---:|
| test (3.10) | 89106179431 | SUCCESS |
| test (3.11) | 89106179413 | SUCCESS |
| test (3.12) | 89106179387 | SUCCESS |

지원 Python matrix는 **3/3 success**다. `notify_failure` job은 세 test job이 성공했으므로 의도대로 skipped됐다. 각 matrix job의 package tests, template smoke, CLI, sanitization, publish readiness 및 release preflight도 success로 완료됐다.

## 잔여 위험과 승인 조건

- deterministic responder는 production cadence query surface와 함께 유지해야 한다. 새 Git query가 추가되면 두 helper 또는 공유 fixture를 갱신하고 unexpected-query guard를 유지해야 한다.
- tests-only 변경이므로 production retry count와 cadence threshold는 이번 W4b에서 코드 변경 대상으로 다루지 않았다.

로컬 focused 검증, 초기 20회 반복, 최신 W4a 86개, PR head SHA 및 원격 Python 3.10/3.11/3.12 matrix가 모두 통과했다. 위 유지 조건은 현재 승인 판정을 막지 않는다.
