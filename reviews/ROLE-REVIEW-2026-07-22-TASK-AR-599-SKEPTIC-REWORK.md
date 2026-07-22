---
title: TASK-AR-599 Skeptical Rework Review
date: 2026-07-22
signal: pass
score: 94
tags: [task-ar-599, skeptic, rework, security, external-effect]
---

# TASK-AR-599 skeptical rework review

## Verdict

**APPROVE.** Rework HEAD
`329389be5f70dbae383e654829cbb58c8ac429bf` closes all five blocking findings
from `ROLE-REVIEW-2026-07-22-TASK-AR-599-SKEPTIC.md`. The implementation
worktree was clean at that exact HEAD during the final check.

No real notification or external network request was made. Every delivery probe
replaced `notify` or `urllib.request.urlopen` with an in-process capture.

## Finding-by-finding resolution

| Original finding | Resolution | Result |
| --- | --- | --- |
| Exception-detail disclosure | `notify_on_complete` now sends the exception class, not `str(exc)`. A synthetic sentinel remained in the re-raised local exception and was absent from every captured outbound field. Package and template clients remain byte-identical. | closed |
| False task-completion signal | `task_completion_is_authoritative` requires an existing task record whose status is closed/completed and whose `verification_status` is `passed`. Missing, missing-verification, pending, failed-verification, and active task cases produced no completion notification. Only `closed + passed` emitted `completed and verified`. | closed |
| Matrix sibling failure missed | Notification moved to one non-matrix `notify_failure` job with `needs: test` and an always-evaluated condition on `needs.test.result == 'failure'`. It remains variable-gated and appears once. | closed |
| Token sent to arbitrary dashboard URL | `_dashboard_trigger_url` accepts only `http`/`https` loopback hosts and rejects remote/link-local hosts, numeric aliases, user-info, query strings, fragments, and unsafe schemes. A rejected URL with a token and no ntfy topic made zero `urlopen` calls. | closed |
| Inert/unsafe `.env` guidance | Documentation and `.env.example` now explicitly say the client does not parse `.env`; operators must use an existing process/service environment loader. `.env.example` is described only as a blank reference, so the previous untracked-file promise is gone. | closed |

## Task outcome boundary

The adversarial task-state matrix produced these results:

| Task lookup/state | Completion notification |
| --- | --- |
| no task record | none |
| completed, verification absent | none |
| completed, verification pending | none |
| completed, verification failed | none |
| active, verification passed | none |
| closed, verification passed | one: `TASK-123 completed and verified` |

An explicit failed outcome for a missing task produced only
`TASK-123 worker session reported failed` with title
`agent_runtime worker failure`. The captured failure text contained none of
`task failed`, `completed`, or `verified`. This preserves a worker report rather
than asserting authoritative task failure or completion.

## URL boundary probe

The loopback validator accepted normal `127.0.0.1`, `localhost`, and `[::1]`
forms. It rejected a no-network corpus containing:

- external and link-local hosts;
- a remote hostname prefixed by `127.0.0.1`;
- decimal and shortened numeric IP aliases;
- URL user-info on both local and remote-looking forms;
- `file://`, query, fragment, trailing-dot hostname, and IPv4-mapped IPv6 forms.

For an invalid link-local `ALLIMBOT_URL`, `notify` returned `False` and did not
call the mocked network function when no ntfy fallback was configured.

## Verification executed

```powershell
git status --short --branch
git rev-parse HEAD
git diff --check 78977c0..329389be5f70dbae383e654829cbb58c8ac429bf

py -3.10 -m pytest tests/test_allimbot.py tests/test_update_notify.py tests/test_orchestrator_atomic_writes.py tests/test_owner_governance_chain_parity.py -q
# 52 passed

py -3.10 -c "import yaml; ... yaml.safe_load('.github/workflows/test.yml') ..."
# yaml_parse=pass; needs=test; aggregate failure condition; 3 steps

py -3.10 scripts/verify_wheel_dotfiles.py --check
py -3.10 scripts/regen_host_lock_if_needed.py --check
git diff --check origin/main...HEAD
git status --short --branch
git rev-parse HEAD
```

Two inline Python probes performed the exception-redaction, URL-corpus, and
task-outcome state-matrix checks described above. The first combined probe
successfully completed its redaction and URL sections, then its test harness
loaded the orchestrator without registering the temporary module in
`sys.modules`, which caused a `dataclass` import error. The corrected harness
registered the module and the full task-outcome probe passed. This was a review
harness error, not a product failure.

`actionlint` was not installed, so GitHub-specific lint was unavailable. The
workflow parsed successfully with PyYAML and its job dependency/condition was
also asserted by the focused test.

## Residual risks

- Completion authority intentionally trusts the canonical task frontmatter.
  Direct tampering with `status` and `verification_status` could forge that
  source of truth, so normal task identity, review, and protected-branch gates
  remain part of the security boundary.
- The local dashboard itself is trusted once a loopback connection is allowed;
  the client cannot prevent a compromised local service from forwarding data.
- The timeout remains a per-attempt socket timeout, not a guaranteed global
  wall-clock deadline, and dashboard plus ntfy fallback can take two sequential
  attempts as documented.
- Aggregate GitHub job behavior was structurally and syntactically verified
  locally, but an actual opt-in failure delivery should be observed after push
  because `actionlint` and a live Actions run were outside this review.

None of these residual risks reopens a TASK-AR-599 acceptance blocker. Final
skeptic verdict: **APPROVE**.
