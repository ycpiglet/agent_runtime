---
title: TASK-AR-599 Skeptical Security and External-Effect Review
date: 2026-07-22
signal: block
score: 54
tags: [task-ar-599, skeptic, security, external-effect, allimbot]
---

# TASK-AR-599 skeptical security and external-effect review

## Bottom line

**BLOCK.** The blank-configuration and never-fail mechanics are sound, but the
current change can disclose exception details, can announce an unverified task
completion, does not observe failures from the whole CI matrix, and permits a
dashboard token to be sent to an arbitrary cleartext endpoint. The documented
`.env` setup path is also neither loaded by these notification entry points nor
guaranteed to be ignored by Git.

No real notification was sent during this review. Network behavior was tested
only by replacing `urllib.request.urlopen` with an in-process capture function.

## Review scope and trust boundaries

- Compared `codex/task-ar-599-allimbot` at `78977c0` with `origin/main`.
- Inspected the package and template clients, task lifecycle wiring, governance
  gates, Stop hook, update notice, CI workflow, packaging, documentation, and
  focused tests.
- Treated process environment, repository-controlled CI configuration, local
  dashboard, public `ntfy.sh`, exception text, and task/session records as
  separate trust boundaries.

## Blocking findings

### 1. High — confirmed exception-detail disclosure

**Affected:** `src/agent_runtime/allimbot.py:95-101` and the byte-identical
template client.

`notify_on_complete` embeds `str(exc)` in the outbound failure message. Exception
text commonly contains URLs, request bodies, private prompts, account data, or
authorization material. This directly conflicts with
`docs/ALLIMBOT-INTEGRATION.md:18-19`, which says those values must not be placed
in notifications. A no-network mock using a synthetic authorization value
confirmed that the full exception string reaches `notify` unchanged.

**Required remediation:** send a generic failure message containing only an
approved identifier, duration, and at most the exception class. Keep detailed
exception text in local logs. Add a test with a sentinel secret and assert that
the sentinel is absent from every captured outbound field.

### 2. High — confirmed false task-completion signal

**Affected:**
`src/agent_runtime/templates/project/scripts/agent_orchestrator.py:589-603`.

`kill --outcome completed` immediately changes the session to `closed` and sends
`<task_id> completed`. It does not check that the task exists, that verification
passed, or that an independent release/closeout occurred. In fact,
`tests/test_orchestrator_atomic_writes.py` constructs only a temporary session
record for `TASK-123`—without any task record—and expects the completion alert.
The explicit CLI flag prevents an accidental default completion, but it is not
authoritative completion evidence.

**Required remediation:** either describe and notify this as an
operator-reported *session outcome*, or emit a task-completion notification only
from the authoritative verified task release/close path. Add a negative test
showing that an unverified or nonexistent task cannot produce a message claiming
task completion.

### 3. High — CI notification misses sibling matrix failures

**Affected:** `.github/workflows/test.yml:270-278`.

The notification is a step inside the Python 3.12 matrix job. GitHub's
`failure()` at that location reflects earlier steps in that particular job; a
failure confined to Python 3.10 or 3.11 does not make the successful 3.12 job's
step run. Default matrix fail-fast can also cancel 3.12 before it reaches the
step. The current string-presence test proves opt-in and deduplication text, but
not overall workflow failure coverage.

**Required remediation:** move delivery to one non-matrix job that depends on
the complete matrix job and uses an always-evaluated job-level condition for a
failed dependency. Keep the repository-variable opt-in and topic secret. Add a
structural workflow test proving that the notifier is outside the matrix and
depends on the matrix result.

### 4. High — dashboard token can be posted to an arbitrary HTTP endpoint

**Affected:** `src/agent_runtime/allimbot.py:55-66` and the template mirror.

Despite the documentation calling this route a *local* dashboard,
`ALLIMBOT_URL` is concatenated without scheme, host, user-info, redirect, or
loopback validation. A no-network mock set an RFC 3927 address and confirmed
that the client built that URL, included the token in the JSON body, and treated
a mocked 204 response as success. Plain HTTP is also accepted for non-loopback
hosts. Environment control is required to exploit this, but a typo or injected
runtime configuration is enough to redirect the credential and message.

**Required remediation:** default to and enforce loopback for the local route.
If remote dashboards are an intentional feature, require a separate explicit
opt-in, HTTPS, no URL user-info, and redirect-target validation. Add rejection
tests for non-loopback HTTP, link-local/private metadata targets, user-info, and
unsafe redirects.

### 5. Medium — documented `.env` configuration is inert and not safely ignored

**Affected:** `docs/ALLIMBOT-INTEGRATION.md:23-24`, template `.env.example`, and
both allimbot clients.

The document tells operators to copy values into an untracked `.env`, but the
clients read only `os.environ`; the Stop hook, governance gate, orchestrator,
and update-notify path do not load the host `.env` for allimbot. The template
does not ship a `.gitignore`, and `git check-ignore --no-index .env` in this
checkout confirmed that `.env` is not ignored by the repository rules. This is
both a broken setup instruction and an avoidable secret-commit hazard.

**Required remediation:** either implement a narrowly scoped, optional and
tested loader for only the `ALLIMBOT_*` keys and guarantee `.env` is ignored, or
remove the `.env` instruction and document exact process/service environment
configuration. Never introduce blanket dotenv loading into governance or CI.

## Controls that passed

- `48` focused tests passed for package/template parity, silent no-op,
  per-attempt timeout capping, fallback, exception swallowing, update notice,
  orchestrator writes, and governance-chain parity.
- With all four `ALLIMBOT_*` variables removed, the actual Windows Stop wrapper
  exited `0` and emitted no output.
- Missing notification configuration returns before `urlopen`; the package and
  template clients are byte-identical.
- Each `urlopen` receives a timeout capped at three seconds. Dashboard plus ntfy
  fallback can still consume up to two sequential attempts (nominally six
  seconds total), which the documentation currently states.
- The CI path is opt-in and written only once in the 3.12 matrix definition; it
  does not send when the repository variable is disabled or the secret is blank.
- Wheel dot-file verification includes `.env.example`, the host lock is current,
  `git diff --check` passed, and the implementation worktree was clean.

## Commands and non-network probes executed

```powershell
git status --short --branch
git log -5 --oneline --decorate
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git diff --check origin/main...HEAD

py -3.10 -m pytest tests/test_allimbot.py tests/test_update_notify.py tests/test_orchestrator_atomic_writes.py tests/test_owner_governance_chain_parity.py -q
py -3.10 scripts/verify_wheel_dotfiles.py --check
py -3.10 scripts/regen_host_lock_if_needed.py --check

# With ALLIMBOT_* removed from the child environment:
cmd.exe /d /c src\agent_runtime\templates\project\scripts\allimbot_stop_hook.cmd
git check-ignore -v --no-index .env
git check-ignore -v --no-index src/agent_runtime/templates/project/.env
```

An inline Python probe replaced `notify` to capture the decorator's failure
payload and replaced `urllib.request.urlopen` to capture an arbitrary dashboard
request. It performed no socket operation and confirmed findings 1 and 4.

## Residual risks after the required fixes

- `urllib`'s timeout argument is not a strict end-to-end wall-clock budget for
  every resolver/platform behavior. If the three-second wall-clock guarantee is
  strict, the implementation needs a stronger isolation/deadline mechanism.
- Delivery is synchronous. Even when bounded, dashboard failure plus fallback
  delays the calling path by two attempts. This is acceptable only if the
  documented six-second worst case remains an explicit product decision.
- Public ntfy topics behave like bearer capabilities. Repository policy must
  retain the topic as a masked secret and rotate it if exposed.

## Approval condition

Rework all five findings and add the listed adversarial tests before W4b
approval. Until then, the skeptic verdict is **BLOCK**.
