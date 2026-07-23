---
title: TASK-AR-618 Skeptical W4b Approval
date: 2026-07-23
signal: pass
task_id: TASK-AR-618
verified_head: 73e2f74b620a695d7bb0df343375e46325b7e726
verified_by: codex-task-ar-611-auditor
worker: /root/task-ar-618
role: skeptic
verdict: APPROVE
score: 99
pull_request: 340
ci_run: 29977028574
ci_matrix: 3/3 passed
tags: [task-ar-618, skeptic, w4b, selector-precedence, mutation-integrity]
---

# TASK-AR-618 회의적 W4b 검토

## 판정

**APPROVE — 99/100** at exact HEAD
`73e2f74b620a695d7bb0df343375e46325b7e726`.

blocking finding은 없다. exact `TASK-*` selector는 canonical task 한 개만 선택하고
descendant unit을 후보에 섞지 않는다. exact `UNIT-*` selector는 task로 fall
through하지 않으며, duplicate unit은 네 generic command 모두 stable ambiguity로
실패하고 아무 파일도 변경하지 않았다. explicit relative/absolute path도 기존의
path-first 동작을 유지했다.

`origin/main...HEAD`의 유일한 production 변경은 `scripts/work.py` 공용 resolver의
두 결정이다. task candidate에서 descendant unit glob을 제거하고, 모든 multi-path
결과를 ambiguity로 거부한다. `verify`, `close`, `assign`, `criteria`의 command-specific
production mutation code는 바뀌지 않았다.

PR #340의 head SHA는 검토 HEAD와 정확히 같고 Python 3.10/3.11/3.12가 3/3
성공했다. 독립 확인 시 PR 상태는 `MERGED`였다.

## 측정 결과

| 지표 | 승인 기준 | 측정값 | 출처 | 상태 |
|---|---:|---:|---|---|
| exact task 선택 | task 1개, descendant 후보 0 | 네 command 4/4 task 선택 | end-to-end adversarial probe | PASS |
| exact task의 unit mutation | 0건 | 4/4에서 0건 | before/after byte snapshot | PASS |
| task/unit regex 중첩 | 0개 입력 중첩 | task-only 1, unit-only 1 | fullmatch probe | PASS |
| malformed ID 허용 | 0건 | 4/4 거부 | regex probe | PASS |
| duplicate unit silent selection | 0건 | 네 command 모두 rc=1 ambiguity | end-to-end adversarial probe | PASS |
| duplicate 실패 시 mutation | 0건 | 네 command 모두 전체 snapshot 동일 | byte snapshot | PASS |
| ambiguity path 순서 | 정렬·안정적 | 네 command 모두 901 → 902 순서 | stderr probe | PASS |
| explicit task path | relative/absolute 모두 정확 | 4 commands × 2 forms = 8/8 | path probe | PASS |
| duplicate unit explicit path | 지정 파일만 선택 | 4 commands × 2 forms = 8/8 | path probe | PASS |
| explicit unit sibling mutation | 0건 | 8/8에서 0건 | sibling byte snapshot | PASS |
| focused suite | 전부 통과 | `20 passed in 8.37s` | pytest | PASS |
| schema gate | findings/warnings 0 | pass, 0/0 | work_schema_gate | PASS |
| exact-HEAD CI | Python 3.10/3.11/3.12 성공 | 3/3 success | PR #340, run 29977028574 | PASS |

## 적대적 검증

### selector precedence와 regex 경계

공용 resolver의 두 정규식은 끝 anchor를 포함한다.

```text
TASK_DISPLAY_RE = ^TASK-AR-\d+$
UNIT_DISPLAY_RE = ^UNIT-(TASK-AR-\d+)-\d{3}$
```

`TASK-AR-901`은 task regex만, `UNIT-TASK-AR-901-001`은 unit regex만 통과했다.
suffix가 추가된 task/unit, 불완전 unit, path처럼 보이는 조합 네 개는 양쪽 regex를
모두 통과하지 못했다. unit selector가 parent task로 fall through한 경우는 0건이다.

exact task 아래에 두 descendant unit을 둔 뒤 네 command를 각각 실행했다.

```text
exact-task/verify   -> selected task, descendant mutations 0
exact-task/close    -> selected task, descendant mutations 0
exact-task/assign   -> selected task, descendant mutations 0
exact-task/criteria -> selected task, descendant mutations 0
```

`verify`는 선택된 task와 VERIFY evidence/reviews index만 변경했다. `close`는 선택된
task와 기존 close 계약의 board/classification/reviews index만 변경했다.
`assign`과 `criteria`는 이미 충족된 task에서 파일을 변경하지 않았다. 어느 경우에도
`agents/lead_engineer/tasks/units/**`의 byte가 바뀌지 않았다.

### duplicate unit은 네 command 모두 fail-closed

동일한 `UNIT-TASK-AR-901-001.md`를 두 task의 unit 폴더에 배치했다.

```text
duplicate-unit/verify   -> rc=1, ambiguous, mutations=0
duplicate-unit/close    -> rc=1, ambiguous, mutations=0
duplicate-unit/assign   -> rc=1, ambiguous, mutations=0
duplicate-unit/criteria -> rc=1, ambiguous, mutations=0
```

모든 stderr는 두 repo-relative path를 정렬된 순서로 포함했다. 실행 전후 전체 임시
root의 파일명과 bytes가 완전히 같아 첫 번째 unit의 silent selection이나 일부
mutation은 없었다.

### explicit relative/absolute path 회귀

task에 descendant unit이 있는 상태에서 네 command 각각에 relative와 absolute task
path를 전달했다. 8/8 모두 canonical task를 반환하고 unit을 변경하지 않았다.

duplicate unit 두 개가 있는 상태에서는 한 unit의 explicit relative/absolute path를
각각 전달했다. 8/8 모두 지정한 unit만 선택했고 같은 ID를 가진 sibling unit은
변경하지 않았다. exact ID의 ambiguity와 explicit path의 deterministic
single-target semantics가 섞이지 않는다.

## 정식 검증과 CI

```text
py -3.10 -m pytest \
  tests/test_work_verify.py \
  tests/test_work_close.py \
  tests/test_work_assign.py \
  tests/test_work_criteria.py -q
# 20 passed in 8.37s

py -3.10 scripts/work_schema_gate.py --check
# work-schema-gate: pass
# findings=0
# warnings=0
```

PR #340의 `headRefOid`는 exact reviewed HEAD와 동일했다. Actions run
`29977028574`에서 `test (3.10)`, `test (3.11)`, `test (3.12)`가 모두
`COMPLETED/SUCCESS`였고 PR은 이후 merge됐다.

W4a evidence의 `20 passed in 8.31s`와 schema gate 0/0도 내부적으로 일관되며,
독립 실행과 exact-HEAD CI가 이를 재현했다.

## 잔여 위험

### [P3] duplicate-unit 영구 회귀 테스트는 verify에 집중돼 있다

공용 loader 때문에 현재 네 command가 동일하게 fail-closed하고 독립 probe도 이를
4/4 확인했다. 그러나 committed test에서 duplicate unit ambiguity를 직접 만드는
사례는 `verify`에만 있다. 향후 특정 command가 공용 loader를 우회하면 focused suite가
즉시 잡지 못할 수 있다. 네 command parameterization을 추가하면 방어 깊이가 높아진다.

### [P3] explicit path는 의도적으로 ID ambiguity보다 우선한다

기존 계약대로 실제로 존재하는 relative/absolute path는 exact ID 탐색보다 먼저
선택된다. explicit path는 duplicate-ID 경계를 의도적으로 우회하는 privileged
selector다. 운영 호출자는 `--root` 밖 absolute path나 다른 cwd의 relative path를
넘기지 않아야 한다. 이번 변경이 새로 만든 위험은 아니며 exact ID에는 영향이 없다.

### [P3] lifecycle review의 EOF blank line

추가로 실행한 `git diff --check origin/main...HEAD`는
`reviews/REVIEW-2026-07-23-task-ar-618-selector-precedence.md` 끝의 새 빈 줄 한 개를
보고했다. selector 계약·구현·테스트·schema·CI에는 영향이 없는 nonblock 문서
hygiene 잔여다.

## 점수

- selector/regex 정확성: 30/30
- duplicate ambiguity 및 fail-closed: 20/20
- 네 command mutation 격리: 20/20
- explicit path 호환성: 15/15
- focused/schema/exact-HEAD CI: 10/10
- 회귀 방어 깊이와 hygiene: 4/5
- 합계: **99/100**

이 보고서 한 파일만 작성했다. 구현, 테스트, INDEX, task/claim, 기존 evidence,
commit은 수정하지 않았다.
