---
title: TASK-AR-619 Final Skeptical CI-aware W4b Approval
date: 2026-07-23
signal: pass
task_id: TASK-AR-619
verified_head: 6dba6858df6cbc70ce7e6815cd650c07785945a4
verified_by: codex-task-ar-611-auditor
worker: codex-root-worker
role: skeptic
verdict: APPROVE
score: 98
merge_gate: passed
pull_request: 336
ci_run: 29975465431
ci_matrix: 3/3 passed
tags: [task-ar-619, skeptic, w4b, ci-flake, test-isolation]
---

# TASK-AR-619 회의적 W4b 검토

## 판정

**FINAL APPROVE — 98/100** at exact HEAD
`6dba6858df6cbc70ce7e6815cd650c07785945a4`.

코드 수정 자체는 의도한 회귀를 막는다. 독립적인 엄격 응답기에서 선택된 여섯
쿼리는 각각 정확히 3회 실패했고, 두 diff 쿼리는 합계 정확히 6회 실패했다.
실제 subprocess로 빠지는 cadence fallback은 0회였으며 cadence와 release-auto
모두 `git-query-error`/`trigger-error`, `mutated=false`를 유지했다. 기존 세 테스트의
assert AST도 수정 전후 완전히 같아 단언 약화나 프로덕션 범위 확장은 발견되지
않았다.

이전 판정의 두 미해결 항목도 닫혔다. worktree HEAD, PR #336 head, GitHub Actions
run `29975465431`의 head SHA가 모두 위 SHA와 정확히 일치하고 Python
3.10/3.11/3.12가 **3/3 성공**했다. 또한 commit `986f1184`가 deterministic helper를
prefix 비교에서 완전한 argv equality로 강화하고 두 잘못된-range 회귀 테스트를
추가했다. 직접 반례 여섯 개도 6/6 거부됐다. PR #336은 독립 확인 시점에 `MERGED`
상태이므로 이 판정은 조건부가 아닌 최종 CI-aware 승인이다.

## 측정 결과

| 지표 | 사전 기준 | 측정값 | 출처 | 상태 | 다음 조치 |
|---|---:|---:|---|---|---|
| 선택 쿼리 재시도 | 각 3회 | 6종 모두 각 3회 | 독립 strict responder probe | PASS | 유지 |
| 두 diff 재시도 | 합계 6회 | cadence 6회, release-auto 6회 | 독립 strict responder probe | PASS | 유지 |
| cadence 실제 subprocess fallback | 0회 | 0회 | 전역 `subprocess.run` sentinel probe | PASS | 유지 |
| cadence 오류 의미 | error, false, `git-query-error`, 오류 1개 | 6종 모두 일치 | 독립 strict responder probe | PASS | 유지 |
| 양쪽 diff 오류 의미 | false, 오류 2개, bump/version 없음 | 일치 | 독립 strict responder probe | PASS | 유지 |
| release-auto 종료 의미 | `trigger-error`, `mutated=false`, `executed=false` | 일치, 파일시스템 변화 없음 | 독립 strict responder probe | PASS | 유지 |
| 영향 테스트 반복성 | 독립 반복 및 최종 강화 테스트 통과 | 8 passed × 3회, 최종 10 passed | 독립 pytest 실행 | PASS | 유지 |
| 기존 단언 보존 | 수정 전후 동일 | 8/8, 9/9, 5/5 exact parity | AST 비교 | PASS | 유지 |
| 프로덕션 변경 | 0개 | 구현 commit은 두 테스트 파일만 변경 | `git show --name-only cac32994` | PASS | 유지 |
| taskset gate / diff 형식 | findings 0 / 오류 0 | pass / pass | gate, `git diff --check` | PASS | 유지 |
| 현재 HEAD/PR/run SHA 결속 | 세 SHA가 정확히 동일 | 모두 `6dba6858...945a4` | Git, PR #336, run 29975465431 | PASS | 유지 |
| 현재 HEAD 지원 Python 매트릭스 | 3.10/3.11/3.12 모두 pass | **3/3 success** | run 29975465431 | PASS | 완료 |
| 테스트 대역의 전체 명령 일치 | 잘못된 range/suffix/path 거부 | 직접 반례 6/6 거부, 회귀 테스트 2/2 통과 | helper probe, pytest | PASS | 유지 |

## 해소된 이전 차단과 우려

### exact-HEAD 지원 Python 매트릭스 3/3 성공

worktree, PR, Actions를 각각 조회해 동일 SHA 결속과 결과를 확인했다.

```text
worktree HEAD = 6dba6858df6cbc70ce7e6815cd650c07785945a4
PR #336 head  = 6dba6858df6cbc70ce7e6815cd650c07785945a4
run head      = 6dba6858df6cbc70ce7e6815cd650c07785945a4
run status    = completed
run result    = success
test (3.10)   = completed/success
test (3.11)   = completed/success
test (3.12)   = completed/success
matrix        = 3/3 passed
PR state      = MERGED
```

Actions run은 `29975465431`이고 세 package-test job 모두 success다. 이전 REJECT의
0/3 evidence gap은 exact HEAD의 3/3 결과로 완전히 해소됐다.

### deterministic helper가 완전한 argv를 검증한다

commit `986f1184`는 두 helper의 모든 query branch를 `args == [...]` 완전 비교로
변경했다. tag range뿐 아니라 diff path와 `--` separator까지 고정한다. 잘못된
range, describe 추가 suffix, 잘못된 diff path와 tag를 직접 넣어 모두
`AssertionError`로 거부되는 것을 확인했다.

```text
test_release_cadence_trigger.py: malformed_rejected=3/3
test_release_auto_noncritical.py: malformed_rejected=3/3
```

두 모듈에는 `test_successful_*_query_rejects_wrong_range` 회귀 테스트도 추가됐다.
retry/error 시나리오와 함께 실행한 결과 `10 passed in 7.22s`였다. 강화 commit
이후 현재 HEAD까지 두 대상 test file의 diff가 0이므로 CI가 동일 구현을 검증했다.

## 비차단 발견과 잔여 위험

### [P3] release-auto 시나리오 전체가 process-hermetic한 것은 아니다

release-auto 테스트는 fixture를 만들 때 실제 Git을 사용하고, orchestration은
`_head_sha()`에서 실제 `git rev-parse HEAD`를 호출한다. 이번 변경이 제거한 것은
**cadence query answer의 real-Git fallback**이다. 따라서 “테스트 전체에서 subprocess
0회”라고 주장하면 과장이다.

`_head_sha()` 실패는 cadence 평가를 건너뛰지 않으므로 이번의 selected-call=0
failure path와 같지는 않다. 별도 probe에서 `_head_sha`를 고정하고 cadence 경계에
전역 sentinel을 설치했을 때 real fallback은 0회였고, 오류 결과와 파일 무변경도
확인됐다. 승인·문서 문구는 “cadence query surface가 hermetic하다”로 한정해야 한다.

### [P3] failure-first provenance는 CI log와 diff에 의존한다

구현 commit `cac32994`의 diff는 기존 non-target 경로가 저장해 둔 real
`subprocess.run`으로 위임했다는 원인을 직접 보여 준다. 과거 CI의 최초 실패와
변경 없는 재실행 성공도 비결정성 주장과 부합한다. 별도 단일-purpose
failure-first commit은 없지만 기존 CI 최초 실패, old/new helper diff, 현재
malformed-query regressions가 연속 증거를 구성한다. 기능적 공백은 아니며
provenance 품질의 작은 잔여다.

### [P3] helper 두 벌의 장기 drift 가능성

같은 query surface를 두 테스트 모듈이 각각 구현하며 baseline tag와 subject 응답만
의도적으로 다르다. production query가 변할 때 한쪽만 갱신될 위험이 있다. 공용
test helper나 query table로 모으면 유지보수 위험이 줄어든다.

## 통과한 적대적 확인

- 독립 strict responder는 production의 정확한 query 순서와 인자를 요구했다.
  선택된 query는 3회, 나머지는 각각 1회여서 각 단일 실패 시나리오의 총 query
  호출은 9회였다.
- 두 diff failure에서는 각 diff가 3회씩 총 6회 호출되고 오류 record가 정확히
  2개 생성됐다.
- cadence 결과는 `status=error`, `triggered=false`, `finding=None`,
  `reason=git-query-error`, bump/version 없음이었다.
- release-auto 결과는 `result=trigger-error`, `mutated=false`,
  `executed=false`, 오류 2개였고 probe 전후 파일 목록과 내용이 같았다.
- cadence query 경계에서 실제 `subprocess.run` fallback은 0회였다.
- 영향 범위를 확장한 독립 반복은 세 번 모두 `8 passed`였다:

  ```text
  repeat 1: 8 passed in 14.68s
  repeat 2: 8 passed in 13.60s
  repeat 3: 8 passed in 13.73s
  ```

- W4a evidence는 focused files `84 passed`를 두 번, 대상 7 tests pass를 두 번
  기록한다. 이후 exact-argv 강화 테스트가 추가됐으며 최종 독립 targeted
  `10 passed`와 exact-HEAD CI matrix 3/3가 최종 상태를 검증한다.
- 기존 세 대상 함수의 assert expression은 수정 전후 완전 동일했다. 단언 수는
  각각 8, 9, 5개다.
- 기능 구현·강화 commit은 `tests/test_release_cadence_trigger.py`와
  `tests/test_release_auto_noncritical.py`만 변경했다. production 변경, global pytest
  retry, cadence threshold 변경은 없다.
- `py -3.10 scripts/taskset_work_gate.py --check`는 findings 0으로 통과했고
  `git diff --check`도 통과했다.

## 점수 근거

- 기능 및 정확한 retry/오류 의미: 40/40
- 회귀 격리와 반례 내성: 25/25
- 범위·단언 보존·무변경: 20/20
- release 및 provenance 증거: 13/15
- 합계: **98/100**

승인 임계값 90점과 blocking gate 0개를 모두 충족한다. CI와 exact argv 우려는
해소됐고 위 P3 잔여만 남는다. 이 보고서 외에 구현, 테스트, task/index/claim,
기존 verification evidence는 수정하지 않았다.
