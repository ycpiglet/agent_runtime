---
title: TASK-AR-621 Independent W4b Recheck
date: 2026-07-23
status: approved
signal: pass
score: 99
verdict: APPROVE
task_id: TASK-AR-621
unit_id: UNIT-TASK-AR-621-001
verified_head: c27d3706536bc5e70b58a1d35c4644462ece5199
supersedes_reviewed_head: 02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc
compatibility_fix: 0b5da107
w4a_evidence_commit: c27d3706
verified_by: /root/task_ar_603_auditor
worker: /root/task-ar-621
tags:
  - w4b
  - independent-verification
  - recheck
  - windows
  - terminal-quote
  - createprocess
  - evidence-integrity
---

# TASK-AR-621 Independent W4b Recheck

## Verdict

**APPROVE — 99/100.**

정확한 HEAD `c27d3706536bc5e70b58a1d35c4644462ece5199`를 독립 재검증했다. 첫 승인 HEAD `02e111e18f50c22acb6e550ddab6f7a8c9ccd8fc`의 portable lexer가 기존 frontmatter parser의 terminal-quote 손실과 충돌한다는 skeptic blocker는 해소됐다.

현재 구현은 Windows에서 등록된 command string을 `shell=False`로 직접 `CreateProcess` 경계에 전달하고, POSIX에서는 기존 `shell=True` 계약을 유지한다. Windows caret·공백 경로·backslash·quote grouping·literal metacharacter가 실제 child argv에서 보존됐고, parser가 closing quote를 제거한 기존 command shape도 다시 실행됐다.

## Exact scope and lineage

검토 계보:

```text
c06615ff  test: reproduce Windows verification caret mutation
fcc6121f  fix: preserve verification command arguments
02e111e1  test: record initial TASK-AR-621 W4a evidence
0b5da107  fix: preserve legacy verification compatibility
c27d3706  test: record revised TASK-AR-621 W4a evidence
```

재작업에서 portable lexer와 `shlex` 의존은 제거됐다. `_run_verification_command()`는 command string을 그대로 `subprocess.run()`에 전달하고 다음 platform contract를 사용한다.

```text
Windows: shell=False
POSIX:   shell=True
```

Windows에서 shell 기능이 필요한 명령은 `cmd /c` 또는 `powershell -Command`를 명시해야 한다. `git diff --check main...HEAD`는 통과했다.

## Skeptic blocker closure

이전 blocker의 원인은 production frontmatter parser가 scalar에 `strip("'\"")`을 적용하면서 유효한 command의 마지막 double quote까지 제거하는 기존 동작이었다.

```text
recorded:       python -c "print('legacy-ok')"
parser-visible: python -c "print('legacy-ok')
```

첫 수정의 strict lexer는 parser-visible command를 child launch 전에 unmatched quote로 거절했다. 재작업은 Windows에서 별도 parsing 없이 raw string을 직접 전달하므로 기존 Windows launch behavior를 복원한다.

추가된 실제 frontmatter integration regression은 parser가 closing quote를 제거한 command가 다음 결과를 내는지 확인한다.

- `status=passed`
- `returncode=0`
- `stdout=legacy-ok`

독립 direct probe에서도 같은 terminal-quote shape가 실제 Python child를 실행해 `legacy-ok`를 출력했다. 따라서 skeptic이 지적한 compatibility blocker는 닫혔다.

## Independent verification results

| Check | Threshold | Measured | Result |
| --- | --- | --- | --- |
| Exact HEAD | requested SHA와 동일 | `c27d3706536bc5e70b58a1d35c4644462ece5199` | pass |
| Focused suite | 100% pass | 9 passed in 4.88s | pass |
| Caret/path/quote/metacharacters | child argv 무변형 | 모든 값 보존 | pass |
| Legacy terminal quote | child launch 및 stdout | rc 0, `legacy-ok` | pass |
| Nonzero evidence | original rc/stdout/stderr | rc 7, 두 stream 보존 | pass |
| Timeout evidence | timeout, rc null, 7 fields | 요구값과 일치 | pass |
| Explicit Windows shell | `cmd /c` 실행 | 두 output line 확인 | pass |
| Platform branch | Windows false, POSIX true | mocked call과 일치 | pass |
| Diff hygiene | whitespace error 0 | `git diff --check` 통과 | pass |

Focused command:

```text
py -3.10 -m pytest tests/test_work_verify.py -q
9 passed in 4.88s
```

Windows direct probe는 공백이 포함된 임시 경로에서 실제 subprocess를 실행했다. 다음 값이 child argv에 그대로 도달했다.

```text
value with spaces
C:\Program Files\Agent Runtime\check.py
v0.7.0^{}
left|right
%TEMP%
&&
```

`|`, `%TEMP%`, `&&`는 implicit shell 연산이나 확장 없이 literal 값으로 유지됐다. 명시적 shell command:

```text
cmd.exe /d /s /c "echo explicit-shell-ok^&echo explicit-shell-second"
```

도 정상 실행되어 두 output line을 반환했다.

## Evidence schema

독립 probe에서 success 외 경로도 확인했다.

- nonzero: `status=failed`, `returncode=7`, stdout `out-7`, stderr `err-7`
- timeout: `status=timeout`, `returncode=null`
- 두 경로 모두 command result의 기존 7-field envelope 유지
- platform mock: Linux branch는 exact string과 `shell=True`, Windows branch는 exact string과 `shell=False`

Windows child launch의 `OSError`는 기존 7-field envelope 안에서 `status=failed`, `returncode=127`로 구조화된다.

## Revised W4a evidence

검토한 revised evidence:

```text
reviews/VERIFY-2026-07-23-unit-task-ar-621-001-20260723160351.json
```

- status/signal: `passed/pass`
- actor: `/root/task-ar-621`
- verified_at: `2026-07-23T16:03:51+09:00`
- focused tests: 9 passed in 5.03s
- Owner governance gate: exit 0
- unit evidence ref와 revised JSON 일치

W4a worker와 이 W4b verifier identity는 서로 다르다.

## Registered command inventory

production frontmatter parser로 canonical task/unit records의 machine-readable verification command를 다시 조사했다.

```text
records with commands: 111
commands total: 293
python: 276
pytest: 11
git: 6
implicit Windows shell dependency candidates: 0
legacy terminal-quote shapes: 1
```

legacy shape는 다음 기존 unit이다.

```text
agents/lead_engineer/tasks/units/TASK-AR-586/UNIT-TASK-AR-586-002.md
```

parser-visible command의 closing quote가 없지만, 이번 재작업의 Windows direct string execution과 새 regression은 이 호환성 요구를 명시적으로 보존한다.

## Findings

### Blockers

없음.

### Residual risk

1. **Parser root cause remains**

   terminal quote를 제거하는 frontmatter scalar parsing은 TASK-AR-622 범위로 남아 있다. 현재 Windows Python legacy shape는 호환되지만, malformed command line을 다른 executable이 동일하게 해석한다고 일반화할 수는 없다.

2. **Explicit Windows shell boundary**

   Windows implicit shell dependency는 canonical 293 commands에서 0건이지만, future command가 pipe, redirection, environment expansion 또는 shell builtin을 필요로 하면 `cmd /c`나 `powershell -Command`를 명시해야 한다.

3. **Intentional platform asymmetry**

   POSIX는 기존 `shell=True` 의미를 유지하고 Windows만 `shell=False`를 사용한다. 이는 현재 scope의 compatibility 선택이며 cross-platform command grammar를 하나로 통합하지 않는다.

## Final assessment

Windows caret 변형 결함은 고정됐고, skeptic이 발견한 terminal-quote legacy 회귀도 실제 frontmatter integration test와 독립 child-process probe로 닫혔다. rc/stdout/stderr/timeout schema, explicit `cmd /c`, platform branching, revised W4a 및 전체 등록 명령 inventory가 모두 승인 기준을 충족한다.

**Verdict: APPROVE.**
