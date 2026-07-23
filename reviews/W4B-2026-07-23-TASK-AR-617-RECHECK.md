---
title: TASK-AR-617 Independent W4b Recheck
date: 2026-07-23
signal: fail
score: 74
verdict: REWORK
task_id: TASK-AR-617
verified_head: ed914753e4c2415885195566fa0bd0af63596f50
failure_first_sha: eaeed365fb4c718f43ed13d3f79d8860029fc1d2
verified_implementation: 4c6f2035b7823e12e91d707af68077b422f33a13
verified_by: codex-task-ar-617-independent-auditor-20260723
worker: codex-root-task-ar-617-rework
tags:
  - w4b
  - independent-verification
  - recheck
  - data-integrity
  - frontmatter
---

# TASK-AR-617 Independent W4b Recheck

## 판정

**REWORK — 74/100.** `4c6f2035`는 최초 W4b에서 발견한 모든 `str.splitlines()` 경계를 물리 한 줄 JSON으로 안전하게 인코딩한다. canonical root/template parser와 `work new`, `work verify`, `work close` 안에서는 11종 scalar/list 값이 모두 무손실 왕복했다.

그러나 canonical work item을 읽는 다른 stdlib frontmatter parser들이 reserved marker를 해독하지 않는다. 이 때문에 Owner 화면의 제목과 worker dispatch order의 context·target_files·acceptance가 원값이 아니라 literal marker 문자열로 전달된다. 이는 사용자 표시, 작업 범위, 구현 지시와 검증 기준을 변조하는 P1 데이터 무결성 blocker다.

이 보고서는 정확히 `ed914753e4c2415885195566fa0bd0af63596f50`만 검증한다. 후속 교차 소비자 수정은 평가하지 않았다.

## Blocker: canonical writer와 교차 소비자 parser의 계약 불일치

`scripts/work.py`가 unsafe 값에 쓰는 형식은 다음과 같은 JSON double-quoted reserved-marker scalar다.

```text
"\u001eagent-runtime-work-scalar-v1:<escaped payload>"
```

`scripts/backlog_board.py`와 host template parser는 이를 해독하지만 다음 parser는 외부 따옴표만 제거한다.

- `scripts/org_model_gate.py::parse_frontmatter`
- `scripts/work_schema_gate.py::_frontmatter`

정확한 `ed914753`에서 title, context, target_files, acceptance에 각각 unsafe 값을 넣어 측정했다. canonical parser는 4개 값을 모두 복원했지만 위 두 parser의 **8/8 관측은 모두 실패**했고 `\u001eagent-runtime-work-scalar-v1:...`가 literal 문자열로 남았다.

실제 하위 영향도 재현했다.

- `attention_inbox._load_tasks()` → `_item()`: title이 원문 대신 literal marker로 표시됨.
- `dispatch_gate._front_meta()` → `org_orchestrator.build_order()`: worker context, target_files, acceptance가 모두 literal marker payload가 됨.

특히 target_files 오염은 worker가 잘못된 파일 경로를 받거나 seam/footprint 판단이 실제 수정 범위와 달라질 수 있으므로 단순 표시 결함이 아니다.

## 측정 결과

| 검증 항목 | 결과 | 측정값 |
|---|---:|---|
| 재작업 failure-first | PASS | `eaeed365`의 목표 테스트 1 failed; VT 값이 `left`로 절단됨 |
| 11종 emitter 물리 줄 안전성 | PASS | 11/11, 실제 splitline 문자 0개 |
| `ensure_ascii=True` JSON payload | PASS | 11/11 JSON decode 후 원값 및 marker prefix 확인 |
| canonical root/template scalar·list | PASS | 44/44 assertions |
| register·verify·close lifecycle | PASS | 33/33 경로; 각 결과를 root/template scalar/list로 재확인 |
| marker collision/idempotence | PASS | 5/5 값, root/template, encode-decode-encode 동일 |
| invalid marker JSON | PASS | 3종 × root/template, crash 없음 |
| legacy parser 의미 보존 | PASS | 10종 × baseline/current × root/template 동일 |
| 집중 pytest | PASS | 33 passed in 9.43s |
| work schema gate | PASS | findings=0, warnings=0 |
| host lock | PASS | current |
| 교차 소비자 parser | **FAIL** | 2 parser × 4 fields = 8/8 literal marker 노출 |
| Attention Inbox title | **FAIL** | 원문과 불일치 |
| worker order context/target_files/acceptance | **FAIL** | 3/3 원문과 불일치 |
| 전체 pytest | NOT MEASURED | 이전 15분 timeout을 pass로 간주하지 않음 |

11종 경계는 LF, CR, CRLF, VT, FF, FS, GS, RS, NEL, `U+2028`, `U+2029`다.

## 독립 실행 명령과 관측

등록된 검증 명령을 정확한 HEAD에서 다시 실행했다.

```text
py -3.10 -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py -q
py -3.10 scripts/work_schema_gate.py --check
py -3.10 scripts/regen_host_lock_if_needed.py --check
git diff --check a7c5aeda..ed914753
```

결과는 33 passed, schema findings/warnings 0, host lock current, diff check pass였다. `scripts/backlog_board.py`와 template copy는 `84862bf9..ed914753`에서 blob 변경이 없음을 별도로 확인했다.

추가 독립 probe:

1. `eaeed365` archive에서 새 registration 경계 테스트를 실행해 실제 failure-first를 확인했다.
2. 최신 HEAD에서 11종 각각을 `_frontmatter_scalar()`에 넣고 physical line, JSON payload, root/template scalar/list를 측정했다.
3. 11종 각각에 대해 임시 canonical TASK/UNIT을 만들고 `new`, `verify`, `close`를 실행한 뒤 root/template 두 parser로 결과를 재확인했다.
4. quoted hash, escaped quote, flow list, plain comment, apostrophe, 중간 quote, 미종결 quote, non-marker JSON, invalid marker JSON 등 10종을 `451b2604` baseline과 current root/template에서 비교했다.
5. marker-bearing canonical TASK/UNIT을 `org_model_gate`, `work_schema_gate`, Attention Inbox, dispatch gate, org orchestrator에 전달해 literal marker 누출을 측정했다.

W4a evidence:

- `reviews/VERIFY-2026-07-23-task-ar-617-20260723091656.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723091709.json`

W4a actor `codex-root-task-ar-617-rework`와 이 W4b verifier는 서로 다르다.

## 재작업 요구사항

1. canonical TASK/UNIT을 읽는 handwritten frontmatter parser 전체를 inventory하고 reserved-marker decode 계약을 공유해야 한다. 최소한 `org_model_gate.parse_frontmatter`와 `work_schema_gate._frontmatter`가 scalar와 block-list에서 동일 decoder를 사용해야 한다.
2. Attention Inbox title과 dispatch worker order의 context, target_files, acceptance가 unsafe 원문과 정확히 같다는 integration test를 추가해야 한다.
3. target_files 기반 seam/footprint 판단도 decoded path를 사용한다는 회귀 테스트를 추가해야 한다.
4. marker가 없는 기존 quoted/escaped/flow/plain-comment 의미와 invalid-marker fallback은 유지해야 한다.
5. 변경 범위가 기존 T3 parser surface를 넘으므로 재계획/anchor 갱신 후 새 failure-first와 clean HEAD를 제시해야 한다.

## 잔여 위험

- 현재 schema gate 자체는 pass하지만 내부 parser가 marker-bearing 값을 잘못 읽는다. 즉 gate의 0 findings는 consumer compatibility의 증거가 아니다.
- 다른 독립 handwritten parser에도 같은 decoder 누락이 있을 수 있다. 두 parser만 고치기 전에 전체 소비자 inventory가 필요하다.
- reserved marker는 인증 envelope이 아니다. frontmatter 작성 권한이 metadata 제어 권한이라는 현재 위협 모델에서는 별도 권한 상승으로 보지 않았지만 collision/idempotence 테스트는 유지해야 한다.
- 전체 pytest는 미측정 상태이므로 focused 범위 밖 회귀 부재를 주장하지 않는다.
