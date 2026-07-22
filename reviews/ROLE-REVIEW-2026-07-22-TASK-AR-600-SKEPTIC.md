---
title: TASK-AR-600 Skeptical High-Risk and External-Effect Review
date: 2026-07-22
signal: block
score: 58
tags: [task-ar-600, skeptic, auto-merge, external-effect, security]
---

# TASK-AR-600 skeptical high-risk and external-effect review

## Bottom line

**BLOCK.** Reviewed exact implementation HEAD
`070c05b3df1a35336546a375b739af4892066769`. The authoritative-state decision
works for the ordinary combinations requested: `MERGED` without `mergedAt`
fails, command exit `0` with remote `OPEN` fails, and command exit `1` with a
remote `MERGED` plus timestamp succeeds. Draft preflight and a Draft race also
fail closed.

However, the command and read-back diagnostics are emitted as untrusted raw
text. A mocked command can therefore print the exact `원격 MERGED 확인됨`
success marker while the remote PR remains `OPEN`, and token-like values from
merge/read-back errors reach console output unchanged. Parsed but malformed
read-back fields can also satisfy the success predicate because `mergedAt` is
only tested for truthiness. These are blocking defects in a merge-authority
surface.

No PR was merged and no network, GitHub, branch, or repository setting was
changed during this review. Every merge command and remote read-back was
replaced with an in-process `subprocess.run` or `gh_json` mock.

## Scope

- Worktree: `C:\Users\ycpig\agent_runtime\.worktrees\TASK-AR-600`
- Exact HEAD: `070c05b3df1a35336546a375b739af4892066769`
- Primary implementation:
  `src/agent_runtime/templates/project/scripts/auto_merge.py`
- Focused tests: `tests/test_auto_merge_execution.py` and
  `src/agent_runtime/templates/project/scripts/test_auto_merge.py`
- Review focus: authoritative read-back, return-code divergence, malformed and
  exceptional read-back, Draft races, misleading diagnostics, secret leakage,
  and preservation of dry-run / `SKIP` / `ESCALATE` behavior.

## Blocking findings

### 1. High — untrusted command output can forge the authoritative success marker

**Affected:** `auto_merge.py:124`, `auto_merge.py:131-139`, and
`auto_merge.py:158-165`.

`execute_merge()` copies either raw stdout or raw stderr into `detail`, and
`main()` prints it before its own failure line. In an independent probe, the
mock merge command returned exit `0` with stdout
`→ 원격 MERGED 확인됨(mergedAt=FAKE).`, while read-back returned
`state=OPEN, mergedAt=None`. The process correctly returned `1`, but output
contained both the exact success marker and `머지 미확정`. A human or a parser
that keys on the success phrase can therefore observe a false merge-success
signal despite the authoritative failure decision.

**Required remediation:** never render raw child-process output as an
unqualified status line. Emit success wording only from the validated remote
branch, and either omit diagnostics or escape/prefix bounded, sanitized text so
it cannot be confused with an agent-runtime status marker. Add a regression
where both stdout and stderr contain the exact success marker and assert that
the final CLI output contains no merge-success marker when read-back is not
validly `MERGED`.

### 2. High — merge and read-back errors disclose secrets verbatim

**Affected:** `auto_merge.py:124-128` and `auto_merge.py:131-139`.

The merge command's stdout/stderr and the caught `SystemExit` message from
`gh_json` are copied directly into returned detail and then printed. Mocked
sentinels `MERGE_SECRET` and `READBACK_SECRET` were both reproduced unchanged
in output. GitHub CLI errors can include request details, URLs, headers, or
other operational data, so this is an avoidable credential/error-data leakage
path introduced into the second authoritative read-back.

**Required remediation:** report only a controlled failure category, command
return code, and exception class. Do not include raw stdout, stderr, exception
messages, URLs, or payloads in owner-facing status. If detailed diagnostics are
needed, retain them in a separately controlled local evidence channel with
explicit redaction. Add sentinel tests asserting the secret is absent from
every returned and printed field.

### 3. High — malformed read-back can crash or be accepted as a confirmed merge

**Affected:** `auto_merge.py:125-130`.

Only `SystemExit` is caught. `JSONDecodeError`, transport/runtime exceptions,
and non-object JSON propagate out of `execute_merge()`; list and null payloads
raise `AttributeError` at `.get`. More seriously, the success predicate accepts
any truthy `mergedAt`: both `True` and `['not-a-timestamp']` produced
`merged=True` with `state=MERGED`. This violates the stated requirement that a
malformed read-back fail closed under the function's deterministic result
contract.

**Required remediation:** catch the bounded read-back/parse exception set,
return a sanitized non-success result, require an object payload, and validate
`state` and `mergedAt` types and timestamp shape before success. Add negative
tests for invalid JSON, a raised runtime/transport exception, list/null payloads,
boolean/list/non-timestamp `mergedAt`, and missing fields.

## Adversarial results that passed

- Command exit `0` + remote `state=MERGED` + `mergedAt=None` returned failure.
- Command exit `0` + remote `state=OPEN` returned failure.
- Command exit `1` + remote `state=MERGED` + a timestamp returned success,
  preserving the intended local-cleanup divergence behavior.
- Draft preflight returns `ESCALATE`; a mocked post-preflight Draft race returns
  exit `1` and emits no implementation-generated success marker.
- Dry-run `AUTO-MERGE` did not invoke `execute_merge`.
- `SKIP` retained exit `0` and did not invoke `execute_merge`, even with
  `--execute` present.
- The existing focused suite passed: `9 passed in 0.19s`.

## Commands and independent probes

```powershell
git status --short
git rev-parse HEAD
git show --stat --oneline --decorate HEAD
git diff 5bede3c^..070c05b -- src/agent_runtime/templates/project/scripts/auto_merge.py tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py

$env:PATH='C:\Users\ycpig\AppData\Local\Programs\Python\Python310;'+$env:PATH
python -m pytest tests/test_auto_merge_execution.py src/agent_runtime/templates/project/scripts/test_auto_merge.py -q
```

Two inline Python probes loaded the exact worktree module and replaced both
`subprocess.run` and `gh_json`. The first exercised return-code/remote-state
cross-products, Draft racing, dry-run, `SKIP`, malformed/exceptional read-back,
secret sentinels, and a forged success marker. The second exercised malformed
payload shapes and non-string `mergedAt` values. No probe opened a socket or
invoked `gh`.

## Residual risks after required fixes

- The read-back is single-shot. GitHub eventual consistency can cause a safe
  false negative after a real merge; any retry must remain bounded and must
  never turn an ambiguous state into success.
- Neither the merge command nor the read-back command currently has an explicit
  timeout, so a hung `gh` process can block the automation path indefinitely.
- A remote `MERGED` state can reflect a concurrent actor rather than this
  command. Treating the desired authoritative end state as success is a valid
  policy, but evidence should describe it as remote-state confirmation rather
  than command causation.
- Exit `0` on `SKIP` is preserved. Callers must distinguish idempotent/no-op
  completion from an actual merge by verdict or structured evidence, not exit
  code alone.

## Approval condition

Resolve all three findings, add the adversarial regressions above, and rerun an
independent review on the new exact HEAD. Until then, the skeptic verdict is
**BLOCK**.
