---
title: TASK-AR-618 Final Independent W4b Approval
date: 2026-07-23
signal: pass
score: 100
verdict: APPROVE
task_id: TASK-AR-618
verified_head: 73e2f74b620a695d7bb0df343375e46325b7e726
failure_first_sha: 858ac9f2
verified_implementation: c4b384ff
verified_by: codex-task-ar-618-independent-auditor-20260723
worker: /root/task-ar-618
tags:
  - w4b
  - independent-verification
  - approval
  - selector-precedence
  - data-integrity
  - ci-matrix
---

# TASK-AR-618 Final Independent W4b Approval

## 판정

**APPROVE — 100/100.** 정확한 HEAD `73e2f74b620a695d7bb0df343375e46325b7e726`에서 exact TASK 선택자가 하위 UNIT과 경쟁하지 않고, 중복 exact UNIT 선택자는 정렬된 후보 목록과 함께 fail-closed하며, 기존 명시적 상대·절대 경로 선택이 보존됨을 독립 검증했다. blocker 또는 선택자 의미 회귀는 발견되지 않았다.

## 구현 및 범위

production 변경은 `scripts/work.py`의 공통 선택자 경계에 한정된다.

1. exact TASK ID 후보에서 하위 UNIT glob을 제거해 canonical task 파일만 선택한다.
2. 모든 다중 후보에 동일한 ambiguity 오류를 적용해 duplicate UNIT ID도 조용히 첫 후보를 선택하지 못하게 한다.
3. UNIT glob은 `sorted(...)`를 유지하므로 ambiguity 후보 목록이 안정적으로 정렬된다.
4. 기존 파일을 가리키는 명시적 상대·절대 경로는 ID 패턴 탐색보다 먼저 단일 파일로 해석된다.

`verify`, `close`, `assign`, `criteria` 네 소비자는 같은 `_load_work_item()` 경계를 사용하며, 각 명령의 exact TASK 회귀 테스트가 추가됐다. 명령 고유의 상태 변경 의미나 hierarchy 계약은 수정되지 않았다.

## Failure-first 인과성

failure-first 커밋 `858ac9f2` archive에서 신규 핵심 테스트 다섯 개를 독립 실행했다.

```text
5 failed in 2.93s
```

관측된 수정 전 결함:

- `verify`, `close`, `assign`, `criteria`에서 exact TASK ID가 canonical task와 하위 UNIT을 동시에 후보로 만들어 ambiguous로 실패했다.
- duplicate exact UNIT ID가 두 경로에 존재해도 첫 번째 정렬 후보를 선택해 성공했다.

수정 커밋 `c4b384ff`는 이 실패 증거 뒤에 있으며, W4a 기록을 포함한 검증 HEAD `73e2f74b`까지 선택자 구현이 유지된다.

## 독립 실행 결과

```text
py -3.10 -m pytest tests/test_work_verify.py tests/test_work_close.py tests/test_work_assign.py tests/test_work_criteria.py -q
py -3.10 scripts/work_schema_gate.py --check
```

결과:

```text
20 passed in 8.28s
work-schema-gate: pass
findings=0
warnings=0
```

별도 임시 저장소 probe로 공통 선택자 경계를 직접 호출했다.

- exact TASK + 하위 UNIT: canonical task 하나만 반환 — pass
- explicit relative task path: 같은 task 하나만 반환 — pass
- explicit absolute task path: 같은 task 하나만 반환 — pass
- duplicate exact UNIT: `TASK-AR-901`, `TASK-AR-902` 순으로 안정 정렬 — pass
- duplicate exact UNIT load: 정렬된 두 경로를 포함한 ambiguity finding으로 fail-closed — pass

## W4a 및 작업 기록

다음 기록을 구현 및 검증 계약과 대조했다.

- `agents/lead_engineer/tasks/TASK-AR-618.md`
- `agents/lead_engineer/tasks/units/TASK-AR-618/UNIT-TASK-AR-618-001.md`
- `reviews/REVIEW-2026-07-23-task-ar-618-t3-selector-replan.md`
- `reviews/REVIEW-2026-07-23-task-ar-618-selector-precedence.md`
- `reviews/VERIFY-2026-07-23-unit-task-ar-618-001-20260723122800.json`

W4a unit evidence는 actor `/root/task-ar-618`, status/signal `passed/pass`, command count 2를 기록한다.

- focused tests: 20 passed in 8.31s
- schema gate: pass, findings=0, warnings=0

TASK-AR-618은 smallest worker-ready unit 하나로 구현·검증됐고, task 자체의 별도 VERIFY JSON은 생성되지 않았다. unit frontmatter의 verified actor, timestamp, evidence ref는 W4a JSON과 일치한다.

## GitHub PR 및 CI

PR #340과 Actions run `29977028574`를 독립 확인했다.

- PR: `fix: make exact work selectors deterministic`
- base/head: `main` / `codex/task-ar-618-selector-precedence`
- PR head OID: `73e2f74b620a695d7bb0df343375e46325b7e726`
- state: `MERGED`
- run status/conclusion: `completed` / `success`
- run head SHA: `73e2f74b620a695d7bb0df343375e46325b7e726`
- Python 3.10: pass
- Python 3.11: pass
- Python 3.12: pass

로컬 검증 HEAD, PR head OID, CI run head SHA가 모두 byte-for-byte 일치한다.

## 잔여 위험

- 저장소에 duplicate UNIT display ID가 생기는 근본 원인은 이 변경 범위 밖이다. 현재 구현은 이를 안정적으로 차단하고 두 후보를 모두 노출하지만, 중복 자체의 예방은 별도 등록 무결성 계약에 의존한다.
- 명시적 절대 경로는 공통 resolver probe로 검증했지만 전용 command-level 회귀 테스트는 없다. 상대 경로는 committed `criteria` 테스트가 있고 네 명령은 같은 공통 resolver를 사용한다.
- 구현 인계 문서 끝의 추가 빈 줄 때문에 scoped `git diff --check`는 해당 문서의 `new blank line at EOF`를 보고한다. runtime, schema, selector 계약, CI 결과에는 영향이 없는 비차단 문서 서식 잔여사항이다.

위 항목은 현재 승인 판정을 막지 않는다. exact TASK precedence, duplicate UNIT fail-closed, explicit path 보존이라는 등록 계약과 모든 지정 검증은 충족됐다.
