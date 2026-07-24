---
title: TASK-AR-622 Independent W4b Technical Verification
date: 2026-07-24
status: blocked
signal: block
score: 72
verdict: BLOCK
task_id: TASK-AR-622
unit_id: UNIT-TASK-AR-622-001
verified_head: a1fbacceb4fb605d2436c4a19444c34c5e07cc09
verified_by: /root/task_ar_603_auditor
worker: /root/task-ar-622
tags:
  - w4b
  - independent-verification
  - frontmatter
  - data-integrity
  - fail-closed
  - block
---

# TASK-AR-622 Independent W4b Technical Verification

## Verdict

**BLOCK — 72/100.**

정확한 대상 HEAD `a1fbacceb4fb605d2436c4a19444c34c5e07cc09`에서 등록 scalar encoding, quoted/flow-style 호환성, 일반 `value #274` 접미사 탐지, 탐지된 verify/close 요청의 byte-for-byte 비변경은 통과했다.

그러나 전체 scalar 값이 unquoted hash로 시작하는 `context: #274`와 list item `  - #275`는 raw detector가 놓친다. 두 값 모두 parser에서 빈 list로 축약된 뒤 `work verify`와 `work close`가 return code 0으로 계속 실행되고 원본 work item을 변경한다. 이는 “unsafe legacy raw scalar는 lifecycle rewrite 전에 fail closed”라는 핵심 acceptance를 직접 위반한다.

## Exact scope and lineage

검증 기준:

```text
main: fe615151723ac9a8d5755e05594ba94a6d70dd2d
HEAD: a1fbacceb4fb605d2436c4a19444c34c5e07cc09
```

구현 계보:

```text
b700feea  test: reproduce legacy frontmatter scalar loss
ca3837b3  fix: reject unsafe legacy frontmatter scalars
0e973e66  Merge branch 'main'
a1fbacce  test: record TASK-AR-622 W4a evidence
```

`main...HEAD`는 production 2개, focused tests 3개, unit/evidence/설계/index record를 변경한다. 대상 HEAD에서 `git diff --check main...HEAD`는 통과했다.

## Acceptance assessment

| Requirement | Threshold | Measured at target HEAD | Result |
| --- | --- | --- | --- |
| Registration hash-bearing scalar | parser-visible 값 exact match | focused round-trip pass, encoded prefix 확인 | pass |
| Safe quoted/flow scalar | genuine trailing comment 허용 | detector matrix 및 focused tests pass | pass |
| Plain suffix hash detection | `value #274` fail closed | top-level/list 모두 탐지 | pass |
| Hash-first top-level detection | `key: #274` fail closed | findings `[]`, parsed value `[]` | **block** |
| Hash-first list detection | `  - #275` fail closed | findings `[]`, parsed list `[]` | **block** |
| Verify non-mutation | unsafe raw input에서 child/write 0건 | child 실행, rc 0, work item 변경 | **block** |
| Close non-mutation | unsafe raw input에서 write 0건 | rc 0, work item 변경, board 생성 | **block** |
| Existing record compatibility | canonical false positive 0건 | 358 records, findings 0 | pass |
| Evidence schema | 변경 없음 | production evidence schema diff 없음 | pass |

## Blocking finding

### [P1] Hash-first scalar가 raw boundary detector를 우회한다

관련 구현은 `scripts/backlog_board.py`의 `unsafe_legacy_frontmatter_scalars()`이다.

```text
line 545  uncommented = strip_comment(raw).rstrip()
line 549  list item은 "  - " prefix가 있어야 검사
line 559  empty top-level value는 list 시작으로 취급
```

`strip_comment()`가 unquoted hash부터 나머지를 제거한 뒤 `rstrip()`을 적용하므로 다음 변환이 일어난다.

```text
context: #274  -> context:
  - #275       ->   -
```

첫 번째 줄은 empty value branch에서 `current_list`로 취급되고 finding이 추가되지 않는다. 두 번째 줄은 trailing space가 제거되어 `"  - "` prefix 검사 자체에 진입하지 못한다.

독립 detector matrix:

```text
top_suffix:    findings=[(2, 'context')] parsed={'context': 'Preserve issue'}
top_hash_first: findings=[]              parsed={'context': []}
list_suffix:   findings=[(3, 'acceptance')] parsed={'acceptance': ['Preserve PR']}
list_hash_first: findings=[]                parsed={'acceptance': []}
quoted_comment: findings=[] parsed={'context': 'safe #274'}
flow_comment:   findings=[] parsed={'tags': ['safe', 'value']}
full_line_comment: findings=[] parsed={}
body_hash:         findings=[] parsed={'context': 'safe'}
origin_ref github:#274: findings=[(2, 'origin_ref')]
```

이 입력이 진짜 YAML comment인지 legacy literal data인지 detector가 알 수 없다는 것이 본 task의 fail-closed 결정 이유다. 따라서 값 앞에 plain text가 없다는 이유로 허용하면 안 된다.

### Lifecycle impact

격리된 임시 root에서 실제 CLI를 호출했다.

Verify input:

```text
context: #274
acceptance:
  - #275
```

관측값:

```text
returncode=0
verification child executed=True
work item mutated=True
stderr=""
```

Close input도 같은 hash-first shape를 사용했다.

```text
returncode=0
work item mutated=True
BACKLOG-BOARD.md created=True
stderr=""
```

따라서 이 결함은 detector 함수의 이론적 false negative에 그치지 않고 verify command 실행과 evidence rewrite, closeout 및 generated-view write까지 허용하는 lifecycle data-integrity 결함이다.

## Passing behavior and compatibility

### Focused suite

```text
py -3.10 -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py -q
25 passed in 11.18s
```

기존 tests는 다음을 올바르게 확인한다.

- registration이 hash, single/double quote, splitline 문자를 versioned encoded scalar로 기록하고 exact value로 parse한다.
- quoted scalar와 quoted list item의 hash를 verify rewrite 뒤에도 보존한다.
- quoted/flow-style 값 뒤의 genuine YAML comment를 허용한다.
- `value #274` 형태의 unsafe top-level/list suffix를 거절한다.
- 탐지된 verify 요청은 work item과 reviews를 변경하지 않는다.
- 탐지된 close 요청은 work item과 board를 변경하지 않는다.
- 기존 verify/close 정상 경로는 유지된다.

하지만 unsafe regressions가 모두 hash 앞에 plain text를 두어, 전체 값이 `#`로 시작할 때의 empty-value/list-marker 축약을 포함하지 않는다.

### Current corpus scan

production parser와 detector로 canonical task/unit records를 조사했다.

```text
parsed work records: 358
unsafe detector findings: 0
```

따라서 현재 저장된 canonical corpus에서 새 detector가 정상 record를 차단하는 false positive는 발견되지 않았다.

## Recorded and independent evidence

검토한 W4a evidence:

```text
reviews/VERIFY-2026-07-24-unit-task-ar-622-001-20260724154051.json
```

- status/signal: `passed/pass`
- actor: `/root/task-ar-622`
- focused suite: 25 passed in 11.65s
- Owner governance gate: exit 0
- unit metadata와 evidence ref 일치

독립 실행:

| Command/check | Result |
| --- | --- |
| `py -3.10 scripts/work.py status` | active claim/worktree 일치, inflight 0 |
| `git rev-parse HEAD` | exact target HEAD 일치 |
| `git diff --check main...HEAD` | pass |
| focused pytest command | 25 passed in 11.18s |
| `py -3.10 scripts/owner_governance_gate.py` | exit 0; compound cadence advisory only |
| raw detector matrix | suffix/safe cases pass, hash-first 2건 fail |
| isolated verify probe | rc 0, child 실행, mutation 발생 |
| isolated close probe | rc 0, mutation 및 board 생성 |

## Required correction

승인을 위해 최소한 다음이 필요하다.

1. `strip_comment(raw)`가 hash를 제거했다는 사실을 value가 empty가 된 뒤에도 유지한다.
2. top-level `key: #274`를 해당 key의 unsafe scalar로 보고한다.
3. list marker가 `rstrip()` 뒤 `"  -"`만 남은 `  - #275`도 current list key의 unsafe item으로 보고한다.
4. top-level과 list hash-first shape를 실제 raw work record regression으로 추가한다.
5. 각 regression에서 verify command 미실행, evidence 미생성, closeout/board 미생성, 원본 bytes 동일을 검증한다.
6. 수정된 exact HEAD에서 focused suite와 fresh W4a/W4b를 다시 수행한다.

## Concurrent worktree note

본 판정과 모든 위 측정은 요청된 exact HEAD의 깨끗한 worktree에서 수행했다. blocker를 상위 agent에 알린 뒤 작업트리에 `scripts/backlog_board.py`, `tests/test_work_verify.py`, `tests/test_work_close.py`의 concurrent uncommitted 변경이 나타났다. 해당 변경은 `a1fbacce`에 포함되지 않으므로 이 verdict에서 평가하거나 승인하지 않았고, 되돌리지도 않았다.

## Final assessment

구현 방향과 대부분의 호환성 표면은 적절하지만, raw scalar가 hash로 시작하는 가장 작은 legacy form이 verify와 close 모두에서 silent data loss를 계속 허용한다. 핵심 fail-closed 및 비변경 acceptance를 충족하지 못하므로 현재 HEAD는 통합할 수 없다.

**Verdict: BLOCK.**
