---
title: TASK-AR-620 Skeptical W4b Approval
date: 2026-07-23
signal: pass
task_id: TASK-AR-620
verified_head: 34174eacb6d3048672286c6159efca6c5f6f0bd0
verified_by: codex-task-ar-611-auditor
worker: codex-root-task-ar-620
role: skeptic
verdict: APPROVE
score: 96
merge_gate: supported-python-matrix-pending
tags: [task-ar-620, skeptic, w4b, backlog, exact-set, ci-recovery]
---

# TASK-AR-620 회의적 W4b 검토

## 판정

**APPROVE — 96/100** at exact HEAD
`34174eacb6d3048672286c6159efca6c5f6f0bd0`.

요구된 회귀 복구 범위는 정확하다. 테스트의 expected set은 59개에서 61개로
늘었고, 추가분은 아래 두 ID뿐이며 삭제된 ID는 없다.

- `TASKSET-AR-RELEASE-CADENCE-INJECTION-TEST-ISOLATION`
- `TASKSET-AR-CADENCE-ISOLATION-BACKLOG-EXPECTATION-RECOVERY`

`task_set_ids == {...}`의 `Eq` 비교와 두 assert는 그대로 유지됐다. 현재 실제 backlog
classifier 결과도 61개로 expected set과 완전히 같고, recovery task 등록이 새로 만든
자체 taskset도 포함된다. classifier·production·fixture·다른 ID 변경은 없으며 대상
테스트 diff는 두 문자열 리터럴의 `+2/-0`뿐이다.

이 승인은 로컬 W4b 승인이다. 정확한 현재 HEAD의 Python 3.10/3.11/3.12 CI matrix는
아직 실행되지 않았으므로 **병합 전 필수 외부 게이트**로 남는다. 3/3 성공 전에는 이
승인을 통합 가능 판정으로 확대해서는 안 된다.

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
| 현재 HEAD Python matrix | 3.10/3.11/3.12 모두 성공 | 아직 0/3; 원격에 HEAD 없음 | remote containment, Actions | PENDING | 병합 전 3/3 성공 필수 |

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

### [P2] 현재 HEAD의 지원 Python matrix는 아직 없다

검토 시점에 `git branch -r --contains HEAD` 결과가 비어 있어 exact HEAD의 CI 결과는
없다. 이 작업은 test-only set literal 변경이고 Python 3.10에서 반복 통과했지만,
task acceptance는 supported matrix 통과를 요구한다. 브랜치를 원격 CI에 올린 뒤
Python 3.10/3.11/3.12가 모두 성공해야 병합할 수 있다. 실패하면 이 승인은 자동으로
보류되고 재검토해야 한다.

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
- release/provenance 증거: 6/10
- 합계: **96/100**

기능·범위 blocking finding은 0개다. matrix 3/3은 병합 전 필수 조건이며, 이 보고서
외에 구현, 테스트, task/index/claim, 기존 verification evidence는 수정하지 않았다.
