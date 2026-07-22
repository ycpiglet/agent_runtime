---
type: w4b-independent-verification
title: TASK-AR-600 second rework independent verification
task_id: TASK-AR-600
unit_id: UNIT-TASK-AR-600-001
task_set_id: TASKSET-AR-AUTO-MERGE-INTEGRITY
claim_id: CLAIM-20260722-174820-task-ar-600-fa3d
status: approved
signal: pass
verdict: APPROVE
worker_agent_id: codex-root-task-ar-600-rework2
verifier_agent_id: codex-task-ar-600-auditor-rework2-20260722
verifier_role: independent-w4b
branch: codex/task-ar-600-merge-readback
exact_head: c383302a8b8e5728019177b96cee5181915f9bad
implementation_commit: 31dbcf6a349024c47e37efc55d6575eb17258c5d
w4a_commit: c383302a8b8e5728019177b96cee5181915f9bad
w4a_evidence: reviews/VERIFY-2026-07-22-task-ar-600-20260722181037.json
supersedes: [reviews/W4B-2026-07-22-TASK-AR-600.md, reviews/W4B-2026-07-22-TASK-AR-600-REWORK.md]
verified_at: 2026-07-22T18:13:41+09:00
findings: []
---

# W4b Independent Verification — TASK-AR-600 Second Rework

## Verdict

**APPROVE exact HEAD
`c383302a8b8e5728019177b96cee5181915f9bad`.** PR ref, 원격 title, reason 같은
비신뢰 상태 텍스트는 단일 행으로 escape되고 예약 성공 표지는 제거된다. 이전 세 개
skeptic 차단 사항과 Draft/명령 종료코드/원격 read-back divergence도 모두 통과했다.
실제 `gh`, 네트워크, PR merge 또는 그 밖의 외부 변경은 실행하지 않았다.

기존 `reviews/W4B-2026-07-22-TASK-AR-600.md`는 최초 HEAD `070c05b`만,
`reviews/W4B-2026-07-22-TASK-AR-600-REWORK.md`는 첫 재작업 HEAD `b680fea`만
검토했다. 두 문서는 보존하지만 모두 **superseded**이며 최종 릴리스 증거로 사용하면
안 된다. 이 문서가 두 번째 재작업 최종 HEAD에 적용되는 독립 W4b 증거다.

W4 독립성은 유지됐다. 두 번째 재작업 W4a 작업자는
`codex-root-task-ar-600-rework2`이고, 검증자는 별도
`codex-task-ar-600-auditor-rework2-20260722`로 구현과 W4a 증거를 직접 대조하고
새로운 공격 probe를 구성했다.

## 비신뢰 상태 텍스트 경계

| 공격면 | 최종 통제 | 독립 측정 | 결과 |
| --- | --- | --- | --- |
| PR CLI arg/ref | `_safe_status_text(..., limit=50)`을 거친 뒤 출력 | marker, quote, backslash, CR/LF, ANSI를 함께 주입해도 단일 header 행을 유지하고 예약 marker는 사라짐 | PASS |
| 원격 PR title | 같은 single-line escape 및 50자 제한 | 실패 read-back에서 title이 출력 구조를 바꾸지 못했고 marker 0개, 실제 CR/ESC 0개 | PASS |
| reason/check/file 설명 | 각 reason 전체를 160자로 escape | 제어문자는 literal `\\uXXXX`, quote/backslash는 escape되고 marker는 placeholder로 치환 | PASS |
| 예약 성공 marker provenance | 비신뢰 문자열의 `원격 MERGED 확인됨`을 `[reserved-status-marker]`로 치환 | 실패 출력 marker 0개. 권위 있는 성공 출력은 공격 문자열의 marker가 제거된 상태로 구현 생성 marker만 정확히 1개 | PASS |
| 길이 제한 | 치환·escape 후 제한 | 반복 marker/control 입력도 제한 길이 이하, 실제 제어문자와 완전한 예약 marker 없음 | PASS |

결합 공격은 PR arg, title, reason 각각에 `"`, `\\`, `\r`, `\n`, ANSI ESC와 예약
marker를 동시에 주입했다. 실패 출력은 정확히 4개 구조 행만 남았고, 세 비신뢰 필드는
모두 `[reserved...` placeholder로 관측됐다. 별도 직접 검증은 quote, backslash, CR,
LF, tab, NUL, ANSI ESC, C1 CSI, bidi override, 반복 marker를 포함했다.

## 기존 blocker 및 권위 matrix

| 조건 | 독립 결과 |
| --- | --- |
| merge stdout/stderr에 marker와 secret sentinel | 실패 출력에 marker·sentinel 없음 |
| merge 예외 메시지에 marker와 sentinel | 예외 클래스만 남고 메시지는 폐기 |
| `gh` nonzero stderr, malformed JSON, timeout | exit code 또는 예외 클래스만 남고 원문·URL 없음 |
| read-back `SystemExit`/runtime exception | 정형화된 non-success, 메시지 sentinel 없음 |
| null/list/string/bool/int payload | 전부 `merged=False` |
| 8개 malformed/unknown state | 전부 `INVALID`, `merged=False` |
| 13개 non-string/no-timezone/invalid `mergedAt` | 전부 `merged=False` |
| 유효한 Z/양·음 offset timestamp + exact `MERGED` | merge rc 0과 cleanup rc 1 모두 성공 |
| rc 0/1 + OPEN/CLOSED/MERGED-without-timestamp | 전부 실패 |
| Draft preflight 및 post-preflight Draft race | merge 사전 차단 또는 원격 실패 |
| dry-run AUTO-MERGE 및 SKIP | merge 함수 미호출, 기존 no-op 동작 보존 |

## 독립 명령과 결과

등록 focused suite:

```text
python -m pytest tests/test_auto_merge_execution.py \
  src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
18 passed in 0.29s
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
RESULT 63/63 adversarial scenarios passed; zero external calls
```

63개 시나리오는 상태 텍스트 경계 13개와 기존 blocker/권위 matrix 50개로 구성됐다.
모든 subprocess, remote read-back, `evaluate()` 및 merge 결과는 필요한 지점에서
in-process mock으로 대체됐다.

두 번째 재작업 target diff hygiene:

```text
git diff --check b680fea40d934cdd7efb533301f945667bbced45..HEAD -- \
  src/agent_runtime/templates/project/scripts/auto_merge.py \
  tests/test_auto_merge_execution.py \
  tests/fixtures/host/agent_runtime.lock.json \
  agents/lead_engineer/tasks/TASK-AR-600.md \
  agents/lead_engineer/tasks/units/TASK-AR-600/UNIT-TASK-AR-600-001.md
PASS (no output)
```

두 번째 재작업 W4a 증거도 직접 확인했다. unit 증거
`reviews/VERIFY-2026-07-22-unit-task-ar-600-001-20260722181034.json`은 2개 명령,
task 증거 `reviews/VERIFY-2026-07-22-task-ar-600-20260722181037.json`은 3개 명령을
모두 통과했고 각각 `codex-root-task-ar-600-rework2`를 작업자로 기록한다.

## 잔여 위험

릴리스 차단 잔여 위험은 없다.

- 두 순차 `gh` 동작은 각각 30초 timeout이므로 최악의 timeout 지연은 약 60초다.
- single-shot read-back은 eventual consistency에서 안전한 false negative를 만들 수 있지만
  모호한 상태를 성공으로 바꾸지는 않는다.
- 다른 actor가 같은 PR을 먼저 머지하면 원격 `MERGED + mergedAt` 권위에 따라 성공으로
  관측한다. 이는 명령 인과가 아니라 원격 최종 상태 확인 정책이다.
- 실패 진단 `state=MERGED, mergedAt=invalid`에는 일반 단어 `MERGED`가 남는다. 호출자는
  일반 부분문자열이 아니라 exit status와 예약 성공 marker 또는 후속 read-back을 사용해야
  한다.
- 실제 GitHub merge는 안전 경계에 따라 실행하지 않았다. PR CI와 실제 merge read-back은
  후속 통합 단계에서 별도 증거가 필요하다.
- 전체 branch의 제품 target 밖 planning review 5개에는 기존 `new blank line at EOF`
  hygiene가 남아 있다. 두 번째 재작업 target과 task/unit diff는 깨끗하고 기능·lock·
  governance에 영향이 없어 비차단으로 분류한다.

이 verifier는 구현, 테스트, task, unit, claim, board, index, lock 또는 외부 상태를
수정하지 않았다. 이 최종 W4b 문서 한 파일만 작성했다.
