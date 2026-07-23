---
title: TASK-AR-620 Skeptical W4b Approval
date: 2026-07-23
signal: pass
task_id: TASK-AR-620
verified_head: 35cf09c01c6fa26650c87115e42066c0306c5069
verified_by: codex-task-ar-611-auditor
worker: codex-root-task-ar-620
role: skeptic
verdict: APPROVE
score: 99
merge_gate: passed
pull_request: 337
ci_run: 29974597205
ci_matrix: 3/3 passed
tags: [task-ar-620, skeptic, w4b, backlog, exact-set, ci-recovery]
---

# TASK-AR-620 회의적 W4b 검토

## 판정

**FINAL APPROVE — 99/100** at exact HEAD
`35cf09c01c6fa26650c87115e42066c0306c5069`.

요구된 회귀 복구 범위는 정확하다. 테스트의 expected set은 59개에서 61개로
늘었고, 추가분은 아래 두 ID뿐이며 삭제된 ID는 없다.

- `TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION`
- `TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY`

`task_set_ids == {...}`의 `Eq` 비교와 두 assert는 그대로 유지됐다. 현재 실제 backlog
classifier 결과도 61개로 expected set과 완전히 같고, recovery task 등록이 새로 만든
자체 taskset도 포함된다. classifier·production·fixture·다른 ID 변경은 없으며 대상
테스트 diff는 두 문자열 리터럴의 `+2/-0`뿐이다.

로컬 W4b 뒤 남아 있던 외부 게이트도 닫혔다. worktree HEAD, PR #337 head, GitHub
Actions run `29974597205`의 head SHA가 모두 위 SHA와 정확히 일치한다. 해당 run은
completed/success이고 Python 3.10/3.11/3.12가 **3/3 성공**했다. PR #337도 독립 확인
시점에 `MERGED` 상태다. 따라서 이 판정은 조건부가 아닌 최종 CI-aware 승인이다.

## 측정 결과

| 지표 | 기준 | 측정값 | 출처 | 상태 | 다음 조치 |
|---|---:|---:|---|---|---|
| expected ID 증가 | 정확히 2개 | 59 → 61, `+2/-0` | parent/HEAD AST 및 numstat 비교 | PASS | 유지 |
| 추가 ID 집합 | 요구된 두 ID와 동일 | 정확히 동일 | AST set difference | PASS | 유지 |
| 기존 ID 보존 | 삭제 0개 | 삭제 0개 | AST set difference | PASS | 유지 |
| exact-set 단언 | `Eq` 유지 | parent/HEAD 모두 `Eq` | AST 비교 | PASS | 유지 |
| 대상 함수 assert 수 | 변경 0 | 2 → 2 | AST 비교 | PASS | 유지 |
| 실제/기대 집합 | 완전 동일 | 61 = 61, 양방향 차집합 0 | 독립 classifier probe | PASS | 유지 |
| recovery 자체 taskset | 실제 집합에 포함 | 포함 | 독립 classifier probe | PASS | 유지 |
| 프로덕션/classifier 변경 | 0개 | 0개 | commit path/diff 검사 | PASS | 유지 |
| focused 반복성 | 반복 모두 통과 | `17 passed` × 3회 | 독립 pytest 실행 | PASS | 유지 |
| taskset gate / diff 형식 | findings 0 / 오류 0 | pass / pass | gate, `git diff --check` | PASS | 유지 |
| W4a 내용 유효성 | schema·명령·rc·상태 일치 | task/unit 모두 일치, 독립 재현 | 두 VERIFY JSON | PASS | 유지 |
| W4a source freshness 결속 | exact source hash 식별 가능 | freshness block 없음, 자동 판정 unknown/watch | freshness gate | WARN | 다음 evidence부터 source hash/freshness 기록 |
| 현재 HEAD/PR/run SHA 결속 | 세 SHA가 정확히 동일 | 모두 `35cf09c01...c5069` | Git, PR #337, run 29974597205 | PASS | 유지 |
| 현재 HEAD Python matrix | 3.10/3.11/3.12 모두 성공 | **3/3 성공** | run 29974597205 | PASS | 완료 |

## 통과한 적대적 확인

### 정확히 두 ID만 추가됐다

parent `34174eac^`와 HEAD의 대상 테스트 함수를 AST로 파싱해 set literal을 직접
비교했다.

```text
before_count=59
after_count=61
added=[
  TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY,
  TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION
]
removed=[]
exact_two_required=true
```

Git numstat도 `tests/test_backlog_board_tasksets.py`에 대해 `2 0`이다. commit의 다른
변경은 task/unit W4a 상태, VERIFY JSON 두 개, reviews index뿐이며 허용된 lifecycle
evidence다. `scripts/`, `src/`, `schemas/`, `.github/`, `pyproject.toml`에는 diff가
없다.

### exact equality가 약화되지 않았다

대상 함수의 비교 연산자는 수정 전후 모두 `Eq`이고 assert 수는 2개로 같다.
subset, membership, 길이 비교, allowlist 필터로의 변경은 없다. 실제
`backlog_board.load_tasks()` 결과를 별도로 계산했을 때도 다음과 같았다.

```text
actual_count=61
expected_count=61
exact_actual_match=true
actual_minus_expected=[]
expected_minus_actual=[]
```

두 신규 ID는 `TASKSET-DEFINITIONS.json`에도 등록돼 있고 각각 TASK-AR-619와
TASK-AR-620의 `task_set_id`/`parent_id`와 일치한다. 특히 이번 recovery task의
등록 자체가 만드는 두 번째 mismatch를 미리 포함했다.

### 실패 원인과 복구 범위가 대응한다

GitHub Actions run `29973935786`, attempt 1, SHA
`03177549e242c96ab6297b9c183cbba5f9ff122a`의 Python 3.10 log를 직접 확인했다.
package suite는 `1 failed, 2193 passed, 4 skipped`였고 유일한 extra item은
`TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION`이었다. 3.11/3.12는 matrix
fail-fast로 취소됐다. 현재 변경은 그 missing expectation과 recovery 등록으로 생긴
추가 ID만 보충하므로 원인과 diff가 일치한다.

### W4a 증거는 내용상 유효하고 독립 재현된다

task/unit VERIFY JSON 모두 다음을 만족한다.

- schema는 `agent-runtime-work-verification/v1`이다.
- 기록된 명령 2개는 task/unit verification 명령과 정확히 같다.
- 각 command status는 `passed`, return code는 0이다.
- focused suite 결과는 각각 `17 passed`, gate는 findings 0이다.
- `verified_by=codex-root-task-ar-620`으로 두 레코드가 일관된다.

독립 W4b는 동일 focused suite를 세 번 실행해 각각 `17 passed in 0.97s`,
`17 passed in 0.98s`, `17 passed in 0.87s`를 얻었고 gate findings 0도 재현했다.

다만 두 JSON은 생성 당시 source SHA/blob 또는 `freshness` block을 담지 않는다.
repository freshness gate는 이를 block이 아닌 `unknown/watch`로 분류한다. 따라서
증거 내용은 독립 재현으로 신뢰할 수 있지만 artifact만으로 exact-source freshness를
증명하지는 못한다. 이 작업의 기능 승인을 막지는 않되 다음 verification record의
provenance 개선 항목으로 남긴다.

## 비차단 잔여 위험

### 닫힌 외부 게이트: exact-HEAD Python matrix 3/3 성공

PR #337의 `statusCheckRollup`과 Actions run을 각각 조회했다. PR head와 run head는
모두 exact verified HEAD와 같고 결과는 다음과 같다.

```text
worktree HEAD = 35cf09c01c6fa26650c87115e42066c0306c5069
PR #337 head  = 35cf09c01c6fa26650c87115e42066c0306c5069
run head      = 35cf09c01c6fa26650c87115e42066c0306c5069
run status    = completed
run result    = success
test (3.10)   = completed/success
test (3.11)   = completed/success
test (3.12)   = completed/success
matrix        = 3/3 passed
PR state      = MERGED
```

초기 W4b 뒤의 merge commit에서도 대상 테스트 파일은 구현 commit `34174eac`과
동일함을 `git diff --exit-code 34174eac..HEAD -- tests/test_backlog_board_tasksets.py`로
확인했다. 따라서 CI는 감사한 exact test implementation을 그대로 검증했다.

### [P3] W4a artifact가 source hash에 결속되지 않는다

현재 VERIFY schema 사용 방식은 command output을 보존하지만 실행 대상 blob/HEAD를
기록하지 않는다. 독립 재현이 이번 공백을 보완했다. 향후 evidence 생성기가
`verified_head`, target blob hashes, dirty-tree 여부 또는 freshness block을 기록하면
W4a 신뢰성을 자동 검증할 수 있다.

### [P3] hand-maintained exact set의 구조적 유지보수 비용

이번 실패는 classifier 결함이 아니라 등록된 taskset과 수동 expected set 사이의
expectation drift다. exact equality는 의도한 회귀 계약이므로 이번 작업에서
완화해서는 안 된다. 장기적으로는 등록 명령이 이 테스트 기대값 변경 필요성을
명시적으로 안내하거나 생성 검사를 제공하면 같은 CI 복구 작업을 줄일 수 있다.

## 점수 근거

- 두-ID diff 정확성 및 기존 ID 보존: 30/30
- exact assertion 및 실제 classifier 일치: 25/25
- 범위·프로덕션 무변경: 20/20
- focused 반복·gate·W4a 재현: 15/15
- exact-HEAD CI matrix 및 release 증거: 9/10
- 합계: **99/100**

기능·범위·CI blocking finding은 0개다. freshness source 결속 watch만 P3 잔여로
유지한다. 이 보고서 외에 구현, 테스트, task/index/claim, 기존 verification
evidence는 수정하지 않았다.
