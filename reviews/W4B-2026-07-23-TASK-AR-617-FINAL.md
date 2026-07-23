---
title: TASK-AR-617 Final Independent W4b Verification
date: 2026-07-23
signal: fail
score: 78
verdict: REWORK
task_id: TASK-AR-617
verified_head: dbdb6168599fa17556d1a7c366c86070123b5849
splitline_failure_first_sha: 0bd8c6f9fa5319b4574b8c7fee2e9a2e19c9576b
splitline_fix_sha: fe62c5d1eceeb6e17057faaf2123e1ae9cfe82e4
consumer_failure_first_sha: bbbecb449a6671786ccfa22dbffaea550be147b3
consumer_fix_sha: b27c4754462c1c35266a88dee47801098bd31844
verified_by: codex-task-ar-617-independent-auditor-20260723-final
worker: codex-root-task-ar-617-final
tags:
  - w4b
  - independent-verification
  - final-recheck
  - data-integrity
  - frontmatter
---

# TASK-AR-617 Final Independent W4b Verification

## 판정

**REWORK — 78/100.** 이전 두 REWORK blocker는 정확한 `dbdb6168599fa17556d1a7c366c86070123b5849`에서 해소됐다.

- Python `str.splitlines()`의 11종 경계는 물리 한 줄 JSON으로 인코딩되고 canonical parser, lifecycle, 교차 소비자에서 원값으로 복원된다.
- `org_model_gate`, `work_schema_gate`, Attention Inbox, dispatch/orchestrator의 reserved-marker 누출도 해소됐다.
- marker-prefix 자체로 시작하는 원문은 정확히 한 겹만 decode되어 멱등성을 유지한다.

그러나 writer가 문자열처럼 보이는 boolean/integer 값을 raw scalar로 내보내고 `org_model_gate`는 이를 실제 bool/int로 강제 변환한다. 그 결과 title, context, target_files, acceptance가 canonical parser와 Attention/dispatch 사이에서 타입과 값이 달라진다. 작업 지시와 수정 범위를 오염시키는 새로운 P1 데이터 무결성 blocker이므로 승인할 수 없다.

이 보고서는 `dbdb6168`만 검증한다. 후속 수정은 포함하지 않는다.

## Blocker: type-like 문자열의 비가역 coercion

`scripts/work.py::_frontmatter_scalar()`는 다음 문자열을 unsafe로 분류하지 않고 그대로 출력한다.

```text
true
False
0
-7
007
```

canonical `backlog_board` root/template 및 `work_schema_gate` root/template는 이를 문자열로 읽는다. 반면 `org_model_gate::_coerce()`는 각각 `True`, `False`, `0`, `-7`, `7`로 변환한다.

정확한 최종 HEAD에서 title, context, target_files, acceptance 네 필드에 각 값을 주입해 측정한 결과 type-like 문자열은 **5/5 실패**했다.

| 입력 문자열 | writer 출력 | org_model 결과 | Attention title | dispatch context/list 타입 |
|---|---|---|---|---|
| `true` | raw `true` | `True` | `True` | bool |
| `False` | raw `False` | `False` | falsey여서 task ID로 대체 | bool |
| `0` | raw `0` | `0` | falsey여서 task ID로 대체 | int |
| `-7` | raw `-7` | `-7` | 정수 `-7` | int |
| `007` | raw `007` | `7` | 정수 `7` | int |

`007`은 타입뿐 아니라 선행 0도 영구 손실된다. target_files가 bool/int가 되면 worker order의 수정 대상이 문자열 경로가 아니게 되며, context와 acceptance도 문자열 계약을 잃는다.

## 이전 blocker 재검증

### 1. 모든 splitlines 경계

검증한 11종은 LF, CR, CRLF, VT, FF, FS, GS, RS, NEL, `U+2028`, `U+2029`다.

- emitter physical-line safety: 11/11 pass
- JSON payload decode: 11/11 pass
- root/template backlog parser scalar/list: pass
- `work new`, `work verify`, `work close`: 33/33 pass
- lifecycle 결과를 root/template로 재확인: pass

### 2. 교차 소비자 marker decode

11종 경계를 title, context, target_files, acceptance에 주입했다.

- root/template backlog, org_model, root/template work_schema: **220/220 assertions pass**
- Attention title 및 dispatch context/target_files/acceptance: **44/44 assertions pass**
- marker JSON 안 실제 splitline 문자: 0개

### 3. failure-first 인과성

`bbbecb449a6671786ccfa22dbffaea550be147b3` archive에서 교차 소비자 신규 테스트만 분리 실행했다.

```text
4 failed in 1.26s
```

실패는 org_model scalar/list, Attention title, dispatch worker order, root/template work_schema에 각각 발생했다. 수정 `b27c4754462c1c35266a88dee47801098bd31844`가 그 뒤에 있고, W4a HEAD `dbdb6168`까지 구현 blob이 변하지 않았음을 ancestry와 diff로 확인했다.

## Marker 및 legacy 호환성

- marker-prefix 원문 5종 × 5 parser × 4 fields: **100/100 assertions pass**
- 동일 5종의 Attention/dispatch: **20/20 assertions pass**
- encode → decode → encode: 5/5 byte-identical
- 비표식 legacy 13종을 `bbbecb44` 기준과 current org_model/root-template work_schema에서 비교: 모두 unchanged
- invalid marker JSON 및 near-marker 문자열: 기존 fallback 유지
- backlog shared parser surface 5개 함수의 root/template AST: 동일
- root/template `work_schema_gate.py`: 파일 전체 byte-identical

비표식 legacy 동작이 유지됐다는 사실은 새 blocker를 해소하지 않는다. 오히려 org_model의 기존 bool/int coercion과 writer의 raw 문자열 출력 사이에 계약이 없다는 점을 확인한다.

## 등록된 W4a 증거와 독립 재실행

최종 task/unit evidence:

- `reviews/VERIFY-2026-07-23-task-ar-617-20260723093020.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723093043.json`

두 파일 모두 actor `codex-root-task-ar-617-final`, status/signal pass, command_count 3을 기록한다. task evidence는 80 passed in 14.90s, unit evidence는 80 passed in 15.67s를 기록한다. 둘 다 schema findings/warnings 0 및 host lock current를 기록한다.

evidence JSON 자체에는 git HEAD 필드가 없다. 따라서 HEAD 연결은 다음으로 독립 확인했다.

1. 두 evidence가 `dbdb6168` 커밋에 추가됨.
2. `bbbecb44` → `b27c4754` → `dbdb6168` ancestry가 성립함.
3. consumer 수정 및 관련 parser/writer/lock blob은 `b27c4754..dbdb6168`에서 불변임.
4. task/unit frontmatter가 최신 evidence refs와 worker actor를 가리킴.

기록된 집중 명령을 같은 HEAD에서 다시 실행했다.

```text
py -3.10 -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py tests/test_org_model_gate.py tests/test_attention_inbox.py tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q
py -3.10 scripts/work_schema_gate.py --check
py -3.10 scripts/regen_host_lock_if_needed.py --check
git diff --check bbbecb44..dbdb6168
```

독립 결과:

```text
80 passed in 15.07s
work-schema-gate: pass; findings=0; warnings=0
host lock: current
diff check: pass
```

80개 집중 테스트에는 type-like 문자열 adversarial case가 없으므로 기존 통과와 blocker는 모순되지 않는다. 요청에 따라 전체 suite는 실행하지 않았고 pass로 주장하지 않는다.

## 재작업 요구사항

1. 실제 입력이 `str`이고 org_model coercion 문법과 충돌하는 값은 reserved marker로 인코딩해야 한다. 최소 범위는 `true`, `True`, `false`, `False`, 그리고 `-?\d+` 전체이며 선행 0도 포함한다.
2. 실제 bool/int 입력은 문자열과 구분해 의도된 typed scalar 계약을 유지해야 한다. 단순히 모든 값을 quote하거나 모든 coercion을 제거하면 기존 schema 의미가 달라질 수 있으므로 입력 타입 또는 필드 schema에 기반해야 한다.
3. title, context, target_files, acceptance 각각에 대해 type-like 문자열을 `new`부터 Attention/dispatch까지 end-to-end 검증해야 한다.
4. falsey 변환값 때문에 Attention title이 ID로 대체되는 케이스와 `007` 선행 0 손실을 명시적으로 회귀 테스트해야 한다.
5. marker-prefix 멱등성, 11종 splitlines, invalid marker fallback, legacy 비표식 의미, root/template parity를 재실행해야 한다.

## 잔여 위험

- handwritten parser마다 typed coercion 정책이 다르다. writer/parser 계약을 공통 함수만이 아니라 필드 타입까지 명시하지 않으면 유사한 ambiguity가 재발할 수 있다.
- schema gate가 pass해도 Attention/dispatch consumer 의미가 동일하다는 보장은 없다. 교차 소비자 integration test가 release gate에 필요하다.
- 전체 suite는 미측정이다. 이 보고서는 집중 범위 밖 회귀 부재를 주장하지 않는다.
