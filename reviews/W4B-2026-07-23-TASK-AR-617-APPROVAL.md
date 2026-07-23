---
title: TASK-AR-617 Final W4b Approval Reverification
date: 2026-07-23
signal: pass
score: 96
verdict: APPROVE
task_id: TASK-AR-617
verified_head: 7f7be81a8166498a1dd98437dd82931207bcd66b
failure_first_sha: 4f4f9128795bc33aa1df2c90c6ff037bbb6a2a88
verified_implementation: 1ee8a666dafcfd700eef547b88942ad05fa1b8e2
verified_by: codex-task-ar-617-independent-auditor-20260723-approval
worker: codex-root-task-ar-617-type-rework
tags:
  - w4b
  - independent-verification
  - approval
  - data-integrity
  - frontmatter
---

# TASK-AR-617 Final W4b Approval Reverification

## 판정

**APPROVE — 96/100.** 정확한 clean HEAD `7f7be81a8166498a1dd98437dd82931207bcd66b`에서 이전 세 REWORK blocker가 모두 해소됐다.

1. hash·quote 및 모든 `str.splitlines()` 경계가 물리 한 줄 marker JSON으로 안전하게 저장된다.
2. org_model, work_schema, Attention Inbox, dispatch/orchestrator가 marker-bearing scalar/list를 원값으로 복원한다.
3. type-like 문자열 7종이 title, context, target_files, acceptance에서 끝까지 문자열로 보존된다.
4. 실제 boolean/numeric schema 필드는 native bool/int 의미와 risk 판정을 유지한다.

독립 재검증에서 blocker 또는 high-severity 회귀를 발견하지 못했다. 기존 REWORK 보고서는 역사적 실패 증거로 그대로 보존하며 이 보고서가 새 HEAD의 승인 판정이다.

## Type-like 문자열 계약

검증값:

```text
true
True
false
False
0
-7
007
```

각 값을 title, context, target_files, acceptance 네 필드에 넣고 실제 `work._frontmatter()` 출력부터 다음 소비자까지 확인했다.

- root/template `backlog_board`
- `org_model_gate`
- root/template `work_schema_gate`
- Attention Inbox title
- dispatch → `org_orchestrator.build_order()`의 context, target_files, acceptance

결과:

- 7값 × 4필드 모두 reserved marker로 출력: pass
- 5 parser × 4필드 × 7값: **140/140 assertions pass**
- Attention/dispatch 4필드 × 7값: **28/28 assertions pass**
- 결과 타입이 모두 `str` 또는 `list[str]`: pass
- `007` 선행 0 보존: pass
- falsey 문자열이 Attention title에서 task ID로 대체되지 않음: pass

## Native bool/int 의미

문자열 필드의 type-like 보호가 typed schema 필드를 문자열로 바꾸지 않는지 별도로 측정했다.

### Serialization/parser

실제 Python bool/int 입력:

```text
approval_required=True
security_sensitive=False
est_tokens=7
actual_tokens=-7
order=7
xp_value=0
```

typed schema 문자열 입력:

```text
approval_required="false"
security_sensitive="True"
est_tokens="007"
actual_tokens="-7"
order="007"
xp_value="0"
```

두 경우 모두 org_model 결과가 기대한 native `bool`/`int`와 정확히 일치했다. typed numeric 문자열의 `007`은 schema 숫자 필드에서 의도대로 정수 `7`이 됐다. 같은 문자열이 target_files 같은 텍스트 필드에 들어갈 때만 문자열 `"007"`로 보존된다.

### Risk semantics

`dispatch_gate.risk_mode()`를 직접 확인했다.

| 입력 | 기대 | 결과 |
|---|---|---|
| approval_required=true | owner-gate / approval_required | PASS |
| security_sensitive=true | owner-gate / security_sensitive | PASS |
| 두 bool=false, 7 ≤ budget 10 | auto | PASS |
| 두 bool=false, 12 > budget 10 | owner-gate / over_budget | PASS |

## Failure-first 인과성

`4f4f9128795bc33aa1df2c90c6ff037bbb6a2a88` archive에서 type-like 신규 테스트 세 개를 분리 실행했다.

```text
3 failed in 1.85s
```

실패 관측:

- registration: title `"true"`가 `True`로 변환
- Attention: title `"true"`가 `True`로 변환
- dispatch: context `"False"`가 `False`로 변환

수정 `1ee8a666dafcfd700eef547b88942ad05fa1b8e2`는 failure-first 뒤에 있고, W4a HEAD `7f7be81a`까지 관련 구현 blob이 변하지 않았음을 ancestry와 diff로 확인했다.

## 기존 회귀 표면 표본 재검증

다음 16종을 title/context/target_files/acceptance에 넣어 root/template, org_model, work_schema, Attention, dispatch 왕복과 encode-decode-encode 멱등성을 측정했다.

- LF, CR, CRLF, VT, FF, FS, GS, RS, NEL, `U+2028`, `U+2029`
- hash와 single/double quote 혼합값
- reserved marker-prefix로 시작하는 원문
- quote 경계값
- 선행·후행 공백
- `[planned, done]` 형태

결과: **16/16 pass**. marker-prefix 원문은 한 겹만 decode되어 다시 인코딩했을 때 동일한 물리 문자열을 생성했다.

root/template parity:

- backlog shared parser surface 5개 함수 AST: 동일
- root/template `work_schema_gate.py`: byte-identical
- 관련 구현 및 host lock blob: `1ee8a666..7f7be81a` 불변

## W4a 증거 확인

최신 evidence:

- `reviews/VERIFY-2026-07-23-task-ar-617-20260723094020.json`
- `reviews/VERIFY-2026-07-23-unit-task-ar-617-001-20260723094101.json`

두 evidence 모두 actor `codex-root-task-ar-617-type-rework`, status/signal pass, command_count 3을 기록한다.

- task evidence: 82 passed in 32.55s
- unit evidence: 82 passed in 13.47s
- schema gate: findings=0, warnings=0
- host lock: current

evidence JSON에는 git HEAD 필드가 없으므로 다음으로 HEAD 연결을 확인했다.

1. evidence 파일이 `7f7be81a` 커밋에 추가됨.
2. `4f4f9128` → `1ee8a666` → `7f7be81a` ancestry가 성립함.
3. task/unit frontmatter가 최신 evidence ref와 worker actor를 가리킴.
4. 관련 구현 blob이 fix부터 W4a HEAD까지 불변임.

## 독립 실행 명령

```text
py -3.10 -m pytest tests/test_work_registration.py tests/test_work_verify.py tests/test_work_close.py tests/test_backlog_board_tasksets.py tests/test_org_model_gate.py tests/test_attention_inbox.py tests/test_dispatch_gate.py tests/test_work_schema_gate.py -q
py -3.10 scripts/work_schema_gate.py --check
py -3.10 scripts/regen_host_lock_if_needed.py --check
git diff --check 4f4f9128..7f7be81a
```

독립 결과:

```text
82 passed in 13.39s
work-schema-gate: pass; findings=0; warnings=0
host lock: current
diff check: pass
```

요청에 따라 전체 suite는 실행하지 않았다. 이 승인은 등록된 집중 범위와 이전 blocker를 직접 겨냥한 adversarial probe에 한정된다.

## 잔여 위험과 유지 조건

- boolean/numeric field allowlist에 새 typed 필드가 추가되면 writer 계약도 함께 갱신해야 한다.
- handwritten parser를 새로 추가할 때 reserved marker decoder와 type-like 문자열 integration test가 필요하다.
- W4a evidence schema가 향후 git HEAD를 직접 기록하면 evidence-to-commit 연결의 감사 가능성이 더 높아진다.

이 항목들은 현재 승인 blocker가 아니며 후속 유지보수 조건이다.
