---
type: w4b-independent-verification
title: TASK-AR-599 rework independent verification
task_id: TASK-AR-599
unit_id: UNIT-TASK-AR-599-001
task_set_id: TASKSET-AR-JULY-UPSTREAM-INTAKE-CLOSEOUT
claim_id: CLAIM-20260722-170010-task-ar-599-5d41
status: approved
signal: pass
worker_agent_id: codex-root-task-ar-599-rework
verifier_agent_id: codex-task-ar-599-auditor-rework-20260722
verifier_role: independent-w4b
branch: codex/task-ar-599-allimbot
base_commit: 27c5172f629fd669fbc98d6ad3eec3aeb73c844b
implementation_commit: 9c9c1857dfb26e39055086723e2637b1ca4e14d9
w4a_commit: 329389be5f70dbae383e654829cbb58c8ac429bf
w4a_evidence: reviews/VERIFY-2026-07-22-task-ar-599-20260722172533.json
supersedes: reviews/W4B-2026-07-22-TASK-AR-599.md
verified_at: 2026-07-22T17:28:56+09:00
findings: []
---

# W4b Independent Verification — TASK-AR-599 Rework

## Verdict

**APPROVE final product state
`329389be5f70dbae383e654829cbb58c8ac429bf`.** All five previously blocking
findings are resolved, and no new release-blocking defect was found. No real
notification was sent; all transport behavior was exercised with mocks while
all `ALLIMBOT_*` environment values were blank or synthetic.

The earlier approval in `reviews/W4B-2026-07-22-TASK-AR-599.md` covered
`78977c098b59a7e1c7eefb09ea4ad4f49885956d` and is **superseded**. It must not
be used as release evidence for the reworked implementation. This report is
the applicable independent W4b evidence for final HEAD `329389b`.

W4 independence is preserved: W4a was recorded by
`codex-root-task-ar-599-rework`; this verifier independently inspected the
rework, reran the registered checks, and constructed an additional attack
probe without treating W4a output as an oracle.

## Previously blocking findings

| Blocking point | Final control | Independent measurement | Result |
| --- | --- | --- | --- |
| Exception messages can leak secrets | `notify_on_complete` sends only the exception class name, not `str(exc)` or a traceback, then re-raises the original exception unchanged. | Both package and template clients raised `RuntimeError("TOP-SECRET-RUNTIME-VALUE")`. The captured notification contained `RuntimeError`, contained no `TOP-SECRET`, and the caller received the original message locally. | RESOLVED |
| Unverified work can emit an authoritative completion notice | `task_completion_is_authoritative` requires a canonical task record whose status is closed/completed and whose `verification_status` is exactly `passed`. Failure notices are explicitly labeled as worker-session reports. | Six completion-state combinations were probed: only `completed|closed|done + passed` notified; `in_progress + passed`, `completed + failed`, and missing verification did not. Failure text was exactly `worker session reported failed`. | RESOLVED |
| CI notification observes one matrix leg instead of the aggregate | Notification moved from the matrix steps to one `notify_failure` job with `needs: test` and `always() && needs.test.result == 'failure'`. | Workflow parsed as YAML; exactly one notification step exists, none remains in `jobs.test.steps`, and the follow-up job depends on the aggregate `test` result. | RESOLVED |
| Dashboard token can be sent to a remote URL | `_dashboard_trigger_url` accepts only `http`/`https`, a syntactic hostname in `127.0.0.1`, `::1`, or `localhost`, and no userinfo/query/fragment. Invalid dashboard URLs skip directly to token-free ntfy. | For each client, eight remote/confused-deputy URL forms were rejected; the only mock request was ntfy and its body contained no dashboard token. Three valid loopback forms were accepted and remained mocked locally. | RESOLVED |
| `.env` documentation implies a loader that does not exist | Both the reference file and integration guide now say the client does not parse/read `.env`; values must be exported through an existing environment loader or service configuration. | Normalized prose and `.env.example` comments agree, while token/topic/provider example values remain blank. | RESOLVED |

## Independent commands and results

Focused lifecycle, transport, update-notice, orchestrator, and governance
parity suite:

```text
py -3.10 -m pytest tests/test_allimbot.py tests/test_update_notify.py \
  tests/test_orchestrator_atomic_writes.py \
  tests/test_owner_governance_chain_parity.py -q
52 passed in 0.81s
```

Wheel and generated-host lock verification:

```text
py -3.10 scripts/verify_wheel_dotfiles.py --check
verify-wheel-dotfiles: template dot-file entries in wheel: 6
  agent_runtime/templates/project/.env.example
verify-wheel-dotfiles: pass
findings=0

py -3.10 scripts/regen_host_lock_if_needed.py --check
OK: tests/fixtures/host/agent_runtime.lock.json is up to date.
```

Diff hygiene:

```text
git diff --check 78977c0..HEAD
PASS (no output)
```

Independent attack probe:

```text
rework-independent-attack-probe: PASS
invalid_dashboard_urls_blocked_per_client: 8
valid_loopback_urls_mocked_per_client: 3
completion_state_cases: 6
ci_notification_steps: 1
```

The probe covered both byte-identical clients and used only patched
`urllib.request.urlopen` objects. The rejected dashboard inputs included a
remote host, a `localhost` suffix attack, userinfo host confusion, embedded
credentials, query/fragment smuggling, a disallowed scheme, and a scheme-less
URL. No live socket or notification service was used.

Full Owner governance was rerun at final HEAD with all notification variables
forced blank:

```text
py -3.10 scripts/owner_governance_gate.py
exit code: 0
```

The gate retained existing watch/advisory output, including the non-blocking
compound-cadence obligation, but produced no blocking result.

One initial custom probe exited at a verifier-authored exact-string assertion
because the correct documentation sentence crosses a Markdown line break.
Inspection showed no product mismatch; the probe was corrected to normalize
whitespace and the complete attack probe then passed as recorded above.

## Residual risk

No residual risk is release-blocking.

- Loopback enforcement is intentionally syntactic, as documented. A hostile
  OS hosts-file or resolver configuration for `localhost` is outside this
  client boundary; literal `127.0.0.1` remains the default.
- A configured dashboard failure followed by ntfy fallback can consume up to
  two separately bounded three-second attempts.
- The notifier reports exception class names. It excludes runtime exception
  messages and tracebacks; future changes must preserve that boundary.
- CI was validated by YAML parsing and client mocks. No Actions secret was
  created and no workflow was dispatched.

The verifier modified no implementation, task, claim, board, index, registry,
or release artifact. This rework W4b report is the only verifier-authored
change for this verification pass.
