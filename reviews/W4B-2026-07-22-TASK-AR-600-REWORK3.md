---
type: w4b-independent-verification
title: TASK-AR-600 third remediation independent verification
task_id: TASK-AR-600
unit_id: UNIT-TASK-AR-600-001
task_set_id: TASKSET-AR-AUTO-MERGE-INTEGRITY
claim_id: CLAIM-20260722-174820-task-ar-600-fa3d
status: approved
signal: pass
verdict: APPROVE
worker_agent_id: codex-root-task-ar-600-rework3
verifier_agent_id: codex-task-ar-600-auditor-rework3-20260722
verifier_role: independent-w4b
branch: codex/task-ar-600-merge-readback
exact_head: fe26bed19442ad1ff2d32e1f4ebf0c98b68cd496
implementation_commit: 6683a3e21c5cf3ef376f09cb4536d960c01d5dac
w4a_commit: fe26bed19442ad1ff2d32e1f4ebf0c98b68cd496
w4a_evidence: reviews/VERIFY-2026-07-22-task-ar-600-20260722181559.json
supersedes: [reviews/W4B-2026-07-22-TASK-AR-600.md, reviews/W4B-2026-07-22-TASK-AR-600-REWORK.md, reviews/W4B-2026-07-22-TASK-AR-600-REWORK2.md]
verified_at: 2026-07-22T18:20:07+09:00
findings: []
---

# W4b Independent Verification — TASK-AR-600 Third Remediation

## Verdict

**APPROVE exact HEAD
`fe26bed19442ad1ff2d32e1f4ebf0c98b68cd496`.** PR 식별자는 subprocess 실행
전에 1 이상의 ASCII 십진 정수로 강제되며, CLI·`gh_json()`·`execute_merge()` 세
경계에서 동일한 통제가 적용된다. 이전 status injection, secret disclosure, malformed
read-back, Draft 및 rc divergence 통제도 모두 유지됐다. 실제 `gh`, 네트워크, PR merge
또는 그 밖의 외부 변경은 실행하지 않았다.

기존 세 W4b 문서가 검토한 HEAD는 각각 `070c05b`, `b680fea`, `c383302`이다. 문서는
이력으로 보존하지만 모두 **superseded**이며 최종 릴리스 증거로 사용하면 안 된다. 이
문서가 세 번째 보완 최종 HEAD에 적용되는 독립 W4b 증거다.

W4 독립성은 유지됐다. 최종 W4a 작업자는 `codex-root-task-ar-600-rework3`이고,
검증자는 별도 `codex-task-ar-600-auditor-rework3-20260722`로 구현과 W4a 증거를
직접 대조하고 독립 공격 probe를 구성했다.

## PR 식별자 경계

| 경계 | 통제 | 독립 결과 |
| --- | --- | --- |
| `main()` | unknown option이 없고 positional이 정확히 하나이며 `_normalize_pr_number()`를 통과해야 `evaluate()` 진입 | malformed/option-like/missing/extra 입력은 exit 2, evaluate 및 subprocess 호출 0 |
| `gh_json()` | subprocess 구성 전에 ASCII positive decimal 재검증 | invalid 입력은 `SystemExit("PR 번호 형식 오류")`, subprocess 호출 0 |
| `execute_merge()` | merge subprocess 전에 동일 식별자 검증 | invalid 입력은 `(False, "PR 번호 형식 오류", {})`, merge와 read-back 호출 0 |
| valid read-back | 검증된 값을 argv의 단일 positional 요소로 전달 | 정확히 `gh pr view 123 --json state` 형태로 전달 |
| valid merge | merge와 후속 view 모두 같은 canonical positional 사용 | 두 command argv를 독립 캡처해 `123`이 옵션 아닌 한 요소임을 확인 |

55개 입력 경계 시나리오는 다음 범주를 포함했다.

- `-R`, `-Rattacker/repo`, `-d`, `--repo`, `--repo=owner/repo`, `--`
- `;`, `&&`, `|`, `$()`, backtick 및 CR/LF를 포함한 shell-like 문자열
- 앞뒤 공백·tab·newline, `+1`, `-1`, `0`, leading zero, decimal/exponent 표기
- full-width 및 Arabic Unicode 숫자, superscript 숫자
- GitHub URL, `#1`, `owner/repo#1`, slash/backslash 조합
- missing PR, extra positional, 두 PR, option과 extra 값의 여러 순서
- canonical valid `1`, `123`, 큰 ASCII positive decimal의 무변환 보존

모든 invalid 값은 직접 normalize, `gh_json()`, `execute_merge()`, CLI 경계를 함께
통과시켜 호출 기록이 빈 배열임을 확인했다.

## 이전 보안·권위 matrix

이전 63개 독립 시나리오도 최종 HEAD에서 다시 통과했다.

- title/reason의 marker, quote, backslash, CR/LF, ANSI/C1/bidi 제어문자 single-line escape
- 실패 출력 예약 marker 0개, 권위 있는 성공 출력의 구현 marker 정확히 1개
- merge stdout/stderr와 merge/read-back 예외 메시지의 secret sentinel 비반사
- `gh` nonzero, malformed JSON, timeout, `SystemExit`, runtime exception의 fail-closed
- 비객체 payload 6개, invalid state 8개, invalid `mergedAt` 13개
- merge rc 0/1과 OPEN/CLOSED/MERGED/유효 timestamp 조합
- Draft preflight, post-preflight Draft race, dry-run 및 SKIP

## 독립 명령과 결과

등록 focused suite:

```text
python -m pytest tests/test_auto_merge_execution.py \
  src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
21 passed in 0.31s
```

생성 host lock:

```text
python scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.
```

Owner governance:

```text
python scripts/owner_governance_gate.py --allow-empty-owner-docs
exit code: 0
```

독립 mock 공격 probe:

```text
RESULT 118/118 adversarial scenarios passed \
  (input-boundary=55, prior-matrix=63); zero external calls
```

세 번째 보완 target diff hygiene:

```text
git diff --check c383302a8b8e5728019177b96cee5181915f9bad..HEAD -- \
  src/agent_runtime/templates/project/scripts/auto_merge.py \
  tests/test_auto_merge_execution.py \
  tests/fixtures/host/agent_runtime.lock.json \
  agents/lead_engineer/tasks/TASK-AR-600.md \
  agents/lead_engineer/tasks/units/TASK-AR-600/UNIT-TASK-AR-600-001.md
PASS (no output)
```

최종 W4a 증거도 직접 확인했다. unit 증거
`reviews/VERIFY-2026-07-22-unit-task-ar-600-001-20260722181556.json`은 2개 명령,
task 증거 `reviews/VERIFY-2026-07-22-task-ar-600-20260722181559.json`은 3개 명령을
모두 통과했고 각각 `codex-root-task-ar-600-rework3`를 작업자로 기록한다.

## 잔여 위험

릴리스 차단 잔여 위험은 없다.

- 인식된 `--execute`가 반복되면 boolean flag로서 멱등 처리된다. unknown option과 extra
  positional은 모두 차단되며, flag 반복은 PR 식별자나 provider 범위를 바꾸지 않는다.
- 두 순차 `gh` 동작은 각각 30초 timeout이므로 최악의 timeout 지연은 약 60초다.
- single-shot read-back은 eventual consistency에서 안전한 false negative를 만들 수 있지만
  모호한 상태를 성공으로 바꾸지는 않는다.
- 다른 actor가 먼저 머지하면 원격 `MERGED + mergedAt` 권위에 따라 성공으로 관측한다.
  이는 명령 인과가 아니라 원격 최종 상태 확인 정책이다.
- 실제 GitHub merge는 안전 경계에 따라 실행하지 않았다. PR CI와 실제 merge read-back은
  후속 통합 단계에서 별도 증거가 필요하다.
- 전체 branch의 제품 target 밖 planning review 5개에는 기존 `new blank line at EOF`
  hygiene가 남아 있다. 세 번째 보완 target과 task/unit diff는 깨끗하고 기능·lock·
  governance에 영향이 없어 비차단으로 분류한다.

이 verifier는 구현, 테스트, task, unit, claim, board, index, lock 또는 외부 상태를
수정하지 않았다. 이 최종 W4b 문서 한 파일만 작성했다.
