---
title: TASK-AR-622 Independent W4b Recheck
date: 2026-07-24
status: blocked
signal: block
score: 86
verdict: BLOCK
task_id: TASK-AR-622
unit_id: UNIT-TASK-AR-622-001
verified_head: 8e2743bca443760ad1d4a7556c1c7f1a88a55a99
supersedes_reviewed_head: a1fbacceb4fb605d2436c4a19444c34c5e07cc09
verified_by: /root/task_ar_603_auditor
worker: /root/task-ar-622
tags:
  - w4b
  - independent-verification
  - recheck
  - frontmatter
  - data-integrity
  - flow-boundary
  - block
---

# TASK-AR-622 Independent W4b Recheck

## Verdict

**BLOCK — 86/100.**

정확한 대상 HEAD `8e2743bca443760ad1d4a7556c1c7f1a88a55a99`에서 이전 blocker였던 top-level hash-first, 2-space list hash-first, 4-space list hash-first의 fail-closed 처리는 모두 통과했다. Verify는 세 경우 모두 verification child를 실행하지 않고 evidence를 만들지 않았으며, close도 board를 만들지 않았다. 두 lifecycle command 모두 전체 임시 파일 트리가 byte-for-byte 동일했다.

그러나 incomplete nested-flow 값 `[[safe] #277]`는 여전히 detector를 우회한다. `work verify`가 child와 evidence를 실행·생성하고 work item을 변경했으며, `work close`도 record와 board를 변경했다. 설계 계약은 **complete** flow-style 값 뒤의 genuine comment만 허용하므로 이 fail-open은 핵심 acceptance 위반이다.

## Exact scope

검증 기준:

```text
main: fe615151723ac9a8d5755e05594ba94a6d70dd2d
HEAD: 8e2743bca443760ad1d4a7556c1c7f1a88a55a99
```

이전 BLOCK 이후 계보:

```text
2a3cb06c  fix: catch hash-first legacy frontmatter values
fceb1774  test: prove unsafe verify does not execute
1591a083  docs: record TASK-AR-622 skeptical blocker
8e2743bc  test: refresh TASK-AR-622 W4a evidence
```

작업트리는 검증 시작 시 깨끗했고 `git diff --check main...HEAD`는 통과했다.

## Previous blocker closure

수정은 comment stripping으로 hash가 제거됐는지를 `has_unquoted_hash`에 보존한다. Empty top-level value는 unsafe finding으로 보고하고, indented list marker는 `^\s+-(?:\s+.*)?$`로 인식한다.

격리된 임시 root에서 실제 CLI를 호출하고, 호출 전후의 모든 directory/file/bytes를 snapshot으로 비교했다.

| Scenario | Detector | Verify | Verify writes | Close | Close writes | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `context: #274` | context finding | rc 1 | tree equal, child false, reviews false | rc 1 | tree equal, board false | pass |
| `  - #275` | acceptance finding | rc 1 | tree equal, child false, reviews false | rc 1 | tree equal, board false | pass |
| `    - #276` | acceptance finding | rc 1 | tree equal, child false, reviews false | rc 1 | tree equal, board false | pass |

측정 원문:

```text
verify/top: detector=[(22, 'context')] rc=1 tree_equal=True child_ran=False reviews=False
verify/list2: detector=[(29, 'acceptance')] rc=1 tree_equal=True child_ran=False reviews=False
verify/list4: detector=[(29, 'acceptance')] rc=1 tree_equal=True child_ran=False reviews=False
close/top: detector=[(22, 'context')] rc=1 tree_equal=True board=False
close/list2: detector=[(29, 'acceptance')] rc=1 tree_equal=True board=False
close/list4: detector=[(29, 'acceptance')] rc=1 tree_equal=True board=False
```

따라서 이전 W4b와 skeptic review가 요구한 hash-first/alternate-indent/child-side-effect blocker는 닫혔다.

## Blocking finding

### [P1] Incomplete nested-flow가 complete flow로 오인되어 lifecycle rewrite를 통과한다

대상 HEAD의 `_is_delimited_frontmatter_scalar()`는 flow value의 첫 문자와 마지막 문자만 비교한다.

```python
return (value[0], value[-1]) in {("[", "]"), ("{", "}")}
```

Raw input:

```yaml
acceptance:
  - [[safe] #277]
```

`strip_comment()` 뒤 item은 `[[safe]`가 된다. Outer `[`는 닫히지 않았지만 첫 문자가 `[`이고 마지막 문자가 inner flow의 `]`이므로 detector가 complete flow로 오판한다.

Pure-function 결과:

```text
incomplete_nested_flow_top:
  findings=[]
  parsed={'context': ['[safe']}

incomplete_nested_flow_list:
  findings=[]
  parsed={'acceptance': ['[[safe]']}
```

실제 lifecycle 결과:

```text
verify/nested_flow:
  detector=[]
  returncode=0
  tree_equal=False
  child_ran=True
  reviews=True

close/nested_flow:
  detector=[]
  returncode=0
  tree_equal=False
  board=True
```

이는 malformed input validation만의 문제가 아니다. Lightweight parser가 해당 raw record를 읽고 lifecycle rewrite를 수행하여 unquoted hash suffix를 영구 삭제한다. TASK/UNIT acceptance는 parser가 이미 버린 suffix를 추론하지 말고 rewrite 전에 fail closed 하도록 요구한다.

설계 문서도 quoted 또는 **complete flow-style** value 뒤의 genuine YAML comment만 허용한다고 명시한다. Outer delimiter가 닫히지 않은 위 값은 그 허용 범위가 아니다.

## Focused tests

독립 실행:

```text
py -3.10 -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q
25 passed in 17.58s
```

새 regressions는 다음을 확인한다.

- top-level `context: #274 ...` 거절
- 4-space list `    - #275 ...` 거절
- verify command side-effect sentinel 미생성
- verify work item bytes 동일 및 reviews 미생성
- close work item bytes 동일 및 board 미생성

2-space hash-first list는 독립 임시 CLI probe로 추가 확인했다. Committed suite가 green이지만 nested-flow counterexample은 포함하지 않는다.

## Governance and canonical compatibility

독립 governance:

```text
py -3.10 scripts/owner_governance_gate.py
exit=0
```

Release cadence와 compound cadence는 non-blocking advisory만 보고했다.

Production parser/detector로 canonical task/unit corpus를 전수 조사했다.

```text
canonical parsed records: 358
detector findings: 0
```

따라서 현재 canonical records에서 새 indentation 처리로 인한 false positive는 발견되지 않았다.

## Revised W4a evidence

검토한 fresh evidence:

```text
reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724155415.json
```

- status/signal: `passed/pass`
- actor: `/root/task-ar-622`
- focused suite: 25 passed in 15.76s
- Owner governance gate: exit 0
- unit `verified_at`, `verified_by`, evidence ref와 일치

W4a worker와 이 W4b verifier는 서로 다른 identity다.

## Commands and results

| Command/check | Result |
| --- | --- |
| `py -3.10 scripts/work.py status` | active claim/worktree 일치, inflight 0 |
| `git rev-parse HEAD` | exact full HEAD 일치 |
| `git diff --check main...HEAD` | pass |
| focused pytest command | 25 passed in 17.58s |
| Owner governance gate | exit 0 |
| canonical detector scan | 358 records, findings 0 |
| top/2-space/4-space full CLI matrix | 6/6 refusal 및 complete-tree non-mutation |
| verify child sentinel | 3/3 미생성 |
| incomplete nested-flow detector | 2/2 false negative |
| incomplete nested-flow lifecycle | verify/close 2/2 fail-open 및 mutation |

## Required correction

승인을 위해 최소한 다음이 필요하다.

1. Quoted/flow-style value를 first/last character만으로 complete하다고 판단하지 않는다.
2. Flow delimiter nesting과 quote/escape 상태를 끝까지 확인하거나, parser가 exact round-trip을 보장할 수 없는 nested flow를 fail closed 한다.
3. Top-level과 list의 `[[safe] #277]` 형태를 raw-record regression으로 추가한다.
4. 해당 verify regression에서 command sentinel 미생성, evidence 미생성, complete-tree byte equality를 검증한다.
5. 해당 close regression에서 closeout/board 미생성과 complete-tree byte equality를 검증한다.
6. 수정된 exact HEAD에서 fresh focused/W4a/W4b를 수행한다.

## Concurrent worktree note

본 verdict와 위 모든 측정은 깨끗한 exact HEAD `8e2743bc`에서 수행했다. Nested-flow blocker를 상위 agent에 알린 뒤 shared worktree에 `scripts/backlog_board.py`, `tests/test_work_registration.py`, `tests/test_work_verify.py`, `tests/test_work_close.py`의 concurrent uncommitted 변경이 나타났다. 이는 대상 HEAD에 포함되지 않으므로 평가에서 제외했고 되돌리지 않았다.

## Final assessment

이전 blocker 수정은 정확하며 top-level 및 2/4-space hash-first lifecycle 비변경 보장을 회복했다. 그러나 complete-flow 판정의 구조적 false negative 때문에 다른 raw hash-bearing value가 같은 silent rewrite를 일으킨다. 핵심 fail-closed acceptance가 아직 완전하지 않으므로 현재 HEAD는 통합할 수 없다.

**Verdict: BLOCK.**
