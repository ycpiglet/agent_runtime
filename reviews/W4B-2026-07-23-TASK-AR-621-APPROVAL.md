---
title: TASK-AR-621 Independent W4b Technical Approval
date: 2026-07-23
status: approved
signal: pass
score: 98
verdict: APPROVE
task_id: TASK-AR-621
unit_id: UNIT-TASK-AR-621-001
verified_head: 02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc
failure_first_sha: c06615ff
verified_implementation: fcc6121f
w4a_evidence_commit: 02e111e1
verified_by: /root/task_ar_603_auditor
worker: /root/task-ar-621
tags:
  - w4b
  - independent-verification
  - windows
  - command-arguments
  - evidence-integrity
  - shell-boundary
---

# TASK-AR-621 Independent W4b Technical Approval

## Verdict

**APPROVE — 98/100.**

정확한 HEAD `02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc`에서 Windows caret 변형 결함이 재현 가능한 failure-first 테스트로 고정되고, 수정 후 caret·공백 경로·backslash·single/double quote grouping이 직접 argv로 보존됨을 확인했다. success, nonzero, timeout, executable-not-found 및 empty-command 결과가 같은 evidence field envelope로 반환된다.

암묵적 OS shell 제거는 의도적인 계약 변경이다. 현재 canonical work record의 machine-readable verification 명령 293개에는 implicit pipe/redirection/`&&`/environment/glob 의존이 없어 기존 정상 레코드의 blocker는 발견되지 않았다. shell 기능이 필요한 future/external command는 `cmd /c`, `powershell -Command`, `sh -c` 등을 명시해야 한다.

## Scope and exact lineage

검증 계보:

```text
c06615ff  test: reproduce Windows verification caret mutation
fcc6121f  fix: preserve verification command arguments
02e111e1  test: record TASK-AR-621 W4a evidence
```

`main...HEAD` 변경은 다섯 파일이다.

- production: `scripts/work.py`
- focused tests: `tests/test_work_verify.py`
- unit verification metadata
- W4a evidence JSON
- generated reviews index

production 변경은 `_verification_argv()` 추가와 `_run_verification_command()`의 direct argv execution 및 parse/launch error evidence 처리로 제한된다. template mirror나 두 번째 `work.py` 구현은 저장소에 없다. `git diff --check main...HEAD`는 통과했다.

## Code review

### `_verification_argv`

채택된 portable contract:

- whitespace가 argument를 구분한다.
- single/double quote가 공백 포함 argument를 group한다.
- quote delimiter 자체는 제거된다.
- backslash는 escape로 소비하지 않고 literal로 유지된다.
- `#`는 comment로 해석하지 않는다.
- caret, ampersand, pipe, redirection 같은 shell metacharacter는 literal argument다.
- empty command와 unmatched quote는 `ValueError`로 fail-closed한다.

구현은 `shlex.shlex(command, posix=True)`에 다음 설정을 사용한다.

```text
whitespace_split=True
commenters=""
escape=""
```

Windows path의 backslash를 POSIX escape로 잃지 않으면서 quote grouping을 하나의 cross-platform 규칙으로 고정한다.

### `_run_verification_command`

이전:

```text
subprocess.run(command, shell=True, ...)
```

현재:

```text
argv = _verification_argv(command)
subprocess.run(argv, ...)
```

따라서 `cmd.exe`가 `^`를 escape character로 소비하지 않는다. `cwd`, `capture_output`, `text`, `timeout`, output tail 4,000 characters 및 시작/종료 timestamp는 유지된다.

새로운 fail-closed 결과:

- executable launch `OSError`: `status=failed`, `returncode=127`
- empty/unmatched quote `ValueError`: `status=failed`, `returncode=2`

두 경우에도 command evidence는 기존 7-field envelope를 유지한다.

## Failure-first causality

commit `c06615ff` archive에서 다음 테스트만 독립 실행했다.

```text
python -m pytest tests/test_work_verify.py::test_work_verify_preserves_caret_bearing_revision_argument -q
```

결과:

```text
1 failed in 1.30s
failure-first-exit=1
expected: ["v0.7.0^{}"]
actual:   ["v0.7.0{}"]
```

기존 `shell=True` 경로가 Windows에서 caret을 제거한다는 원래 결함을 정확히 재현한다. 수정 `fcc6121f`는 failure-first 뒤에 있으며 W4a HEAD까지 production blob이 유지된다.

## Independent commands and results

### Required focused test

```text
py -3.10 -m pytest tests/test_work_verify.py -q
```

결과:

```text
8 passed in 4.61s
```

테스트 표면:

- normal success 및 evidence/frontmatter update
- nonzero exit code 7
- nonzero stdout/stderr capture
- caret-bearing revision argument
- timeout status 및 `returncode=null`
- exact result field set
- quoted hash metadata preservation
- duplicate selector fail-closed 등 기존 verify behavior

### Direct Windows argv/evidence probe

임시 디렉터리 이름과 script path 자체에 공백을 넣고 실제 subprocess를 실행했다.

입력 argument:

```text
dir with spaces/check args.py
value with spaces
single grouped value
C:\Program Files\Agent Runtime\check.py
v0.7.0^{}
```

child process가 관측한 argv는 위 다섯 값과 byte-for-byte 의미상 일치했다.

추가 결과:

| Scenario | Required | Measured | Result |
| --- | --- | --- | --- |
| success | passed, rc 0, stdout | passed, rc 0 | pass |
| nonzero | failed, original rc/stdout/stderr | rc 7, both streams retained | pass |
| timeout | timeout, rc null, 7 fields | timeout, null, 7/7 fields | pass |
| missing executable | structured failure | failed, rc 127, 7/7 fields | pass |
| empty command | structured failure | failed, rc 2, 7/7 fields | pass |
| explicit Windows shell | `cmd /c` works | `cmd.exe /d /s /c "echo explicit-shell-ok"` passed | pass |
| implicit shell builtin | must not execute silently | `echo ...` failed rc 127 | pass |
| caret | literal child argv | `v0.7.0^{}` retained | pass |
| quoted path/value | one argv item each | retained | pass |
| backslash | literal | retained | pass |

## W4a evidence

검토한 evidence:

`reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723155106.json`

- status/signal: passed/pass
- actor: `/root/task-ar-621`
- verified_at: `2026-07-23T15:51:06+09:00`
- command count: 2
- focused tests: 8 passed in 4.68s
- Owner governance: exit 0
- unit frontmatter actor/timestamp/evidence ref: JSON과 일치

W4a worker와 이 W4b verifier identity는 서로 다르다.

## Compatibility inventory

canonical task/unit frontmatter를 parser로 읽어 machine-readable verification 명령을 전수 조사했다.

```text
records with commands: 111
commands total: 293
python: 275
pytest: 11
git: 6
implicit shell-operator dependencies: 0
environment/glob/builtin dependencies: 0
```

한 개의 pre-existing malformed 명령이 발견됐다.

```text
agents/lead_engineer/tasks/units/TASK-AR-586/UNIT-TASK-AR-586-002.md
```

frontmatter parser 결과에 closing quote가 없어 `_verification_argv`는 `ValueError: No closing quotation`을 반환한다. 원본 command도 기존 implicit shell에서 올바르게 실행될 수 없는 malformed 상태였으므로 이번 변경으로 정상 behavior가 회귀한 사례는 아니다. 현재 구현은 이를 crash나 silent mutation 대신 rc 2 evidence로 남긴다.

## Findings

### Blockers

없음.

### Non-blocking findings and residual risk

1. **Implicit-shell compatibility boundary**

   pipe, redirection, `&&`, environment expansion, glob expansion 및 shell builtin은 더 이상 자동 실행되지 않는다. 현재 canonical inventory에는 의존 명령이 없지만 외부/미등록 레코드가 과거 implicit contract에 의존하면 실패할 수 있다. 명시적 shell prefix로 migration해야 한다.

2. **Literal embedded quote limitation**

   single/double quote는 grouping delimiter이며 backslash escape는 의도적으로 비활성화된다. 따라서 argument 내부에 literal quote 문자를 직접 표현하는 복잡한 command string은 이 portable grammar의 대상이 아니다. script file 또는 명시적 shell을 사용해야 한다.

3. **Return-code normalization**

   missing executable 및 parse error는 각각 127/2로 새로 정규화된다. evidence schema는 호환되지만 과거 OS-shell별 “command not found” return code와 문구를 정확히 재현하지는 않는다.

4. **Documentation surface**

   계약은 production docstring과 task/review evidence에 설명된다. 향후 사용자-facing work CLI 문서에도 explicit-shell requirement를 포함하면 external record 작성자의 migration 위험을 줄일 수 있다.

## Final assessment

성공/비정상 종료/timeout evidence 의미는 유지됐고, Windows caret 및 일반 path/quote argument는 직접 subprocess 경계에서 보존된다. implicit shell 제거는 현재 canonical command corpus와 호환되며 shell injection·metacharacter mutation 표면을 줄인다.

**Verdict: APPROVE.** 위 residual risk는 명시적 shell opt-in 계약으로 관리 가능하며 TASK-AR-621 통합을 막지 않는다.
