---
title: TASK-AR-619 Skeptical W4b Review
date: 2026-07-23
signal: fail
task_id: TASK-AR-619
verified_head: 00c94a16f1fcf93fec1511689c7132ce3d4c1f3d
verified_by: codex-task-ar-611-auditor
worker: codex-root-worker
role: skeptic
verdict: REJECT
score: 88
tags: [task-ar-619, skeptic, w4b, ci-flake, test-isolation]
---

# TASK-AR-619 회의적 W4b 검토

## 판정

**REJECT — 88/100** at exact HEAD
`00c94a16f1fcf93fec1511689c7132ce3d4c1f3d`.

코드 수정 자체는 의도한 회귀를 막는다. 독립적인 엄격 응답기에서 선택된 여섯
쿼리는 각각 정확히 3회 실패했고, 두 diff 쿼리는 합계 정확히 6회 실패했다.
실제 subprocess로 빠지는 cadence fallback은 0회였으며 cadence와 release-auto
모두 `git-query-error`/`trigger-error`, `mutated=false`를 유지했다. 기존 세 테스트의
assert AST도 수정 전후 완전히 같아 단언 약화나 프로덕션 범위 확장은 발견되지
않았다.

그러나 작업 기록은 **정확한 변경 HEAD가 지원 Python 전체 매트릭스를 통과할 것**을
명시적인 승인 기준으로 둔다. 현재 HEAD를 포함하는 원격 브랜치는 없고, 따라서
Python 3.10/3.11/3.12 결과는 0/3으로 미측정이다. 과거 두 workflow run의 재실행
성공은 변경 전 SHA의 결과이므로 이 기준의 증거로 대체할 수 없다. 기능적 결함을
발견한 것은 아니지만 release 수준 W4b 증거가 미완성이라 claim release를 승인하지
않는다.

## 측정 결과

| 지표 | 사전 기준 | 측정값 | 출처 | 상태 | 다음 조치 |
|---|---:|---:|---|---|---|
| 선택 쿼리 재시도 | 각 3회 | 6종 모두 각 3회 | 독립 strict responder probe | PASS | 유지 |
| 두 diff 재시도 | 합계 6회 | cadence 6회, release-auto 6회 | 독립 strict responder probe | PASS | 유지 |
| cadence 실제 subprocess fallback | 0회 | 0회 | 전역 `subprocess.run` sentinel probe | PASS | 유지 |
| cadence 오류 의미 | error, false, `git-query-error`, 오류 1개 | 6종 모두 일치 | 독립 strict responder probe | PASS | 유지 |
| 양쪽 diff 오류 의미 | false, 오류 2개, bump/version 없음 | 일치 | 독립 strict responder probe | PASS | 유지 |
| release-auto 종료 의미 | `trigger-error`, `mutated=false`, `executed=false` | 일치, 파일시스템 변화 없음 | 독립 strict responder probe | PASS | 유지 |
| 영향 테스트 반복성 | 독립 3회 모두 통과 | 8 passed × 3회 | `py -3.10 -m pytest ... -q` | PASS | 유지 |
| 기존 단언 보존 | 수정 전후 동일 | 8/8, 9/9, 5/5 exact parity | AST 비교 | PASS | 유지 |
| 프로덕션 변경 | 0개 | 구현 commit은 두 테스트 파일만 변경 | `git show --name-only cac32994` | PASS | 유지 |
| taskset gate / diff 형식 | findings 0 / 오류 0 | pass / pass | gate, `git diff --check` | PASS | 유지 |
| 현재 HEAD 지원 Python 매트릭스 | 3.10/3.11/3.12 모두 pass | **0/3 측정**; 원격에 HEAD 없음 | `git branch -r --contains HEAD`, Actions | **FAIL** | 현재 HEAD를 CI에 올려 3/3 pass 증거 첨부 |
| 테스트 대역의 전체 명령 일치 | 잘못된 range/suffix 거부 | 잘못된 `WRONG..HEAD`를 두 helper 모두 수락 | 직접 helper probe | WARN | prefix가 아니라 완전한 argv tuple 비교 권장 |

## 차단 발견

### [P1] 현재 변경 HEAD의 전체 Python 매트릭스 증거가 없다

`TASK-AR-619`의 Acceptance Criteria와 unit handoff는 full supported Python
matrix 통과를 요구한다. 검토 시점의 현재 HEAD는 어떤 remote branch에도 포함되지
않았다.

```text
CURRENT_HEAD_REMOTE_CONTAINS=NONE
HEAD=00c94a16f1fcf93fec1511689c7132ce3d4c1f3d
required=Python 3.10, 3.11, 3.12
measured_on_exact_head=0/3
```

Actions run `29970171133`과 `29970914790`은 attempt 1에서 각각 Python 3.10
package test가 실패하고 다른 matrix job이 취소된 사실을 확인했다. 각 run의 현재
재실행은 3.10/3.11/3.12가 모두 성공했지만 SHA는 각각
`56203757dc296e85f8856333b255adb354b96da9`,
`9818a9eaf2b69b084338d4c590360520b4e93ead`로, 이번 수정 HEAD가 아니다. 이는 기존
테스트의 비결정성을 뒷받침하지만 수정의 cross-version 완료 증거는 아니다.

재승인 조건은 단순하다. 정확한 현재 구현 SHA를 원격 CI에서 실행해 Python
3.10/3.11/3.12가 모두 통과한 링크 또는 machine-readable evidence를 남기면 된다.
코드 재작업은 이 발견의 필수 조건이 아니다.

## 비차단 발견과 잔여 위험

### [P2] deterministic helper가 명령 전체가 아니라 prefix만 검증한다

두 `_successful_cadence_query()` helper는 describe를 제외한 대부분의 쿼리를
`args[:2]` 또는 `args[:3]`으로 분기한다. 직접 반례에서
`log --format=%s WRONG..HEAD`와 `rev-list --count WRONG..HEAD`가 성공 응답을
받았다. 따라서 미래에 production이 잘못된 tag range, path suffix, query option을
보내도 이 테스트들은 감지하지 못할 수 있다.

이 약점은 현재 수정의 반례는 아니다. 독립 검증은 production의 현재 일곱 가지
정확한 argv tuple만 허용하는 별도 strict responder로 수행했고 모두 통과했다.
다만 영구 회귀 테스트의 민감도를 높이려면 helper도 완전한 argv tuple 또는 명시적
query key를 비교해야 한다.

### [P2] release-auto 시나리오 전체가 process-hermetic한 것은 아니다

release-auto 테스트는 fixture를 만들 때 실제 Git을 사용하고, orchestration은
`_head_sha()`에서 실제 `git rev-parse HEAD`를 호출한다. 이번 변경이 제거한 것은
**cadence query answer의 real-Git fallback**이다. 따라서 “테스트 전체에서 subprocess
0회”라고 주장하면 과장이다.

`_head_sha()` 실패는 cadence 평가를 건너뛰지 않으므로 이번의 selected-call=0
failure path와 같지는 않다. 별도 probe에서 `_head_sha`를 고정하고 cadence 경계에
전역 sentinel을 설치했을 때 real fallback은 0회였고, 오류 결과와 파일 무변경도
확인됐다. 승인·문서 문구는 “cadence query surface가 hermetic하다”로 한정해야 한다.

### [P3] 독립된 failure-first artifact가 없다

구현 commit `cac32994`의 diff는 기존 non-target 경로가 저장해 둔 real
`subprocess.run`으로 위임했다는 원인을 직접 보여 준다. 과거 CI의 최초 실패와
변경 없는 재실행 성공도 비결정성 주장과 부합한다. 그러나 unit handoff가 요구한
별도 failure-first guard/실패 evidence는 독립 artifact로 남아 있지 않다. 현재의
strict probe가 동작 증거를 보강하지만 provenance 품질에는 작은 공백이 남는다.

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
  기록한다. 해당 evidence 이후 HEAD까지 두 대상 test file의 내용은 변하지 않았다.
- 기존 세 대상 함수의 assert expression은 수정 전후 완전 동일했다. 단언 수는
  각각 8, 9, 5개다.
- 구현 commit은 `tests/test_release_cadence_trigger.py`와
  `tests/test_release_auto_noncritical.py`만 변경했다. production 변경, global pytest
  retry, cadence threshold 변경은 없다.
- `py -3.10 scripts/taskset_work_gate.py --check`는 findings 0으로 통과했고
  `git diff --check`도 통과했다.

## 점수 근거

- 기능 및 정확한 retry/오류 의미: 40/40
- 회귀 격리와 반례 내성: 21/25
- 범위·단언 보존·무변경: 20/20
- release 및 provenance 증거: 7/15
- 합계: **88/100**

승인 임계값은 90점과 blocking gate 0개다. 현재는 전체 Python matrix 증거가 없어
두 조건을 모두 충족하지 못한다. 이 보고서 외에 구현, 테스트, task/index/claim,
기존 verification evidence는 수정하지 않았다.
