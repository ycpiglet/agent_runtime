# Agent Runtime Hardening Implementation Plan

This plan turns the review findings into immediately executable work. It
prioritizes making the distributed host template self-contained, verified in CI,
and safer under multi-agent execution before adding new agent features.

## Goals

- A clean host can install `agent_runtime`, run `sync --apply`, and execute core
  runtime scripts without missing-file failures.
- CI proves the package source and the installed host template both work.
- ToolRunner no longer exposes arbitrary code execution through `python`,
  mutable git commands, or shell escape patterns.
- Message claiming is race-safe enough for parallel workers.
- Optional provider dependencies are explicit and loaded lazily.

## Non-Goals For This Pass

- No public GitHub mutation or release push.
- No new provider family beyond making existing providers load safely.
- No dashboard or full replay UI.
- No native Claude/Codex platform subagent integration beyond smoke-safe hooks
  and documentation placeholders.

## Pass-7 Immediate Execution Plan (Now)

This pass is only for the remaining gaps from `reviews/REVIEW-2026-06-08-agent-runtime-recompare-after-pass-7.md`.

Priority 1 (required before declaring the current loop complete):

1. Add real multi-process concurrency evidence for message claiming
   - Add a test that starts at least two worker threads/processes against the same
     open message and verifies exactly one `claimed` owner exists.
   - Add stale-leader recovery where a second worker can recover a lock only under
     explicit policy (no reply exists + stale lease + source still claimed).
   - Add ownership check in reply path: if claim marker is not owned by caller,
     reply write must fail hard.

2. Add command policy profiles in `ToolRunner`
   - Introduce profile names: `ci`, `owner`, `research`.
   - Keep default as strictest (`ci`): allow-list only deterministic verification commands.
   - `owner` adds explicit dangerous-but-auditable commands with explicit allow-lists
     (e.g., manual repair and diagnostics).
   - `research` may relax non-mutating tools only (no git write/mutable git/pip/python shell execution).
   - Implement clear validation errors that include profile and allowed set diff.
   - Add tests for each profile and at least one negative case per profile.

3. Standardize review artifact formatting
   - New review artifacts must always start with `Bottom Line`.
   - Include `Signal`, `Insight`, `Decision` sections exactly once.
   - Keep an explicit "Remaining Risk" subsection for unresolved high-risk points.

Acceptance checks before closing pass-7:

- `PYTHONPATH=src python -m pytest tests -q` passes.
- New concurrency/recovery test passes deterministically.
- `tests/test_template_agent_tools.py` includes profile split coverage.
- Review artifact for pass-7 references baseline + previous pass and current metrics in one file.

## Phase 0 - Baseline And Failing Evidence

Files to inspect first:

- `.github/workflows/test.yml`
- `pyproject.toml`
- `src/agent_runtime/templates/project/scripts/agent_worker.py`
- `src/agent_runtime/templates/project/scripts/agent_orchestrator.py`
- `src/agent_runtime/templates/project/scripts/auto_runner.py`
- `src/agent_runtime/templates/project/scripts/auto_dispatch.py`
- `src/agent_runtime/templates/project/scripts/providers/__init__.py`
- `src/agent_runtime/templates/project/scripts/providers/agent_tools.py`

Commands:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests -q
python -m agent_runtime.cli sanitize --root . --check
python -m agent_runtime.cli publish-check --root . --check
python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check
```

Expected baseline:

- Package tests pass.
- Full repo `pytest` may fail because host-template tests are collected from
  package data. Keep this as evidence, but do not fix by hiding template tests
  until host-template smoke coverage exists.

## Phase 1 - Make Host Templates Self-Contained

Purpose: eliminate missing-file runtime failures after `sync --apply`.

Add or repair these template artifacts:

- `src/agent_runtime/templates/project/scripts/orchestrator_safety_gate.py`
- `src/agent_runtime/templates/project/scripts/pipeline.py`
- `src/agent_runtime/templates/project/schemas/task.schema.json`
- Referenced docs that are required by checks, or remove/soften stale hard
  references where the docs are not part of the reusable runtime contract.

Implementation notes:

- Reconstruct `orchestrator_safety_gate.py` as a small local safety primitive:
  `SafetyDecision`, `evaluate_spawn`, `evaluate_call`, `evaluate_kill`,
  `check_emergency_stop`, and `write_evidence`.
- Keep the safety module dependency-free and deterministic.
- `write_evidence` should write under `agents/runtime/evidence/` and never
  require existing host state.
- `pipeline.py` should support the behavior already assumed by
  `agent_worker.py`: `compute_next(meta, reply_text, changed_files)` and
  `write_stage_message(next_stage, inbox)`.
- Pipeline behavior should be conservative: no pipeline metadata means no-op;
  missing or malformed fields should no-op, not crash the worker.
- `task.schema.json` should match the current TASK frontmatter fields used by
  template scripts, with required fields kept minimal for reusable hosts.

Tests to add:

- Package-level test that every imported script dependency exists in
  `templates/project`.
- Template smoke test that copies templates to a temp host and runs:
  `scripts/agent_orchestrator.py --help`,
  `scripts/auto_runner.py --json`,
  `scripts/agent_worker.py --help`,
  `scripts/check_messages.py`.
- Unit tests for safety gate decisions and evidence write path.
- Unit tests for pipeline no-op and basic `VERDICT:` handoff.

Acceptance:

- A clean synced host can run the core help/status commands.
- No `ModuleNotFoundError` for `orchestrator_safety_gate`, `pipeline`, or
  `scripts`.
- No `FileNotFoundError` for `schemas/task.schema.json`.

## Phase 2 - Add Installed Host Template Smoke CI

Purpose: CI must verify the distributed artifact, not only package internals.

Implementation:

- Add `tests/test_template_smoke.py` or equivalent package test.
- Create a temp host directory with an `agent_runtime.yml`.
- Invoke `agent_runtime sync --root <host> --apply`.
- Run scripts from the generated host with `cwd=<host>` and `PYTHONPATH` set to
  `<host>` or `<host>/scripts` as needed.
- Exercise a dummy-provider message flow:
  create one open inbox message addressed to `qa`,
  run `python scripts/agent_worker.py --role qa --provider dummy --once`,
  assert original message is answered,
  assert one reply exists,
  assert an event log exists.

CI changes:

- Keep existing package test job.
- Add a step after package tests:

```bash
PYTHONPATH=src python -m pytest tests -q
PYTHONPATH=src python -m pytest tests/test_template_smoke.py -q
```

Acceptance:

- CI fails if a required template file is missing.
- CI fails if a clean host cannot process one dummy inbox message.

## Phase 3 - Tighten ToolRunner Command Policy

Purpose: make `run_command` an allowlisted verifier, not an arbitrary execution
backdoor.

Current risky surface:

- `python`, `py` are broadly allowed.
- `git add`, `git commit`, `git checkout`, `git restore`, and `git stash` are
  allowed.
- `python -c`, arbitrary script execution, and subprocess-based bypasses are
  possible.

Implementation:

- Replace `ALLOWED_CMDS = {"pytest", "python", "py"}` with exact command
  profiles.
- Allow read-only git by default: `status`, `diff`, `log`, `rev-parse`.
- Deny mutable git by default: `add`, `commit`, `checkout`, `restore`, `stash`,
  `reset`, `push`, `pull`, `merge`, `rebase`, `clean`.
- Allow `pytest` only with bounded, repo-relative paths and no shell control
  syntax.
- Allow Python only for exact safe forms:
  `python -m pytest ...`,
  `python scripts/check_agent_docs.py`,
  `python scripts/check_messages.py`,
  `python scripts/agent_orchestrator.py status --json`.
- Deny `python -c`, `python -`, `pip`, module installs, and paths outside the
  repo.
- Keep all command execution through `subprocess.run(argv, shell=False)`.

Tests to add:

- `python -c "..."` denied.
- `py -c "..."` denied.
- `python -m pip install ...` denied.
- `git commit`, `git checkout`, `git restore`, `git stash` denied.
- `git status`, `git diff`, `python -m pytest tests -q` allowed.
- Path traversal in command args denied where a command accepts paths.

Acceptance:

- ToolRunner can still run deterministic verification.
- ToolRunner cannot mutate git history or execute arbitrary Python.

## Phase 4 - Race-Safe Message Claiming

Purpose: prevent duplicate claim/reply under parallel workers.

Design:

- Move from in-place `status: open -> claimed` writes to a lease-based claim
  primitive.
- Keep compatibility with existing flat inbox files.
- Use atomic claim marker creation first, then update message frontmatter.

Implementation:

- Add `scripts/message_queue.py` in the template.
- Claim algorithm:
  create `agents/runtime/claims/<message_id>.claim` with exclusive create mode,
  including role, pid, hostname, claimed_at, expires_at, and source path.
  If marker already exists and is not stale, claim fails.
  Re-read source message after marker creation and confirm `status: open`.
  Update frontmatter to `claimed`, adding claim metadata.
  If status changed before update, remove marker and fail.
- Answer algorithm:
  write reply with idempotency key `in_reply_to=<message_id>`,
  mark original answered only if this worker owns the claim marker,
  move or mark claim as completed.
- Stale lease:
  default TTL 30 minutes,
  stale claim can be recovered only if source is still `claimed` and no reply
  exists for `in_reply_to`.

Migration:

- `agent_worker.claim_message` delegates to `message_queue.claim_message`.
- `auto_dispatch._claim_source` delegates to the same primitive.
- Preserve old parser/serializer behavior.

Tests to add:

- Two claim attempts on same message: exactly one succeeds.
- Losing claimant does not write reply.
- Existing reply prevents duplicate reply after stale recovery.
- Stale claim can be recovered when no reply exists.
- `check_messages.py` still passes for claimed/answered messages.

Acceptance:

- Parallel worker race test is deterministic.
- A message cannot get two reply files from concurrent claimers.

## Phase 5 - Dependency Contract And Lazy Providers

Purpose: clean installs should work with dummy/local commands; live providers
should fail with clear optional-extra guidance.

Implementation:

- Update `pyproject.toml` with optional extras:
  `codex = ["requests", "python-dotenv"]`,
  `claude = ["anthropic", "python-dotenv"]`,
  `watch = ["watchdog"]`,
  `dev = ["pytest"]`.
- Keep base dependencies empty unless a package is required by the package CLI
  itself.
- Refactor `providers/__init__.py` to avoid importing live provider modules at
  top level.
- Replace provider class registry with lazy import factories.
- Ensure `get_provider("dummy")` works without `requests`, `anthropic`,
  `python-dotenv`, or `watchdog`.
- Error messages should say which extra to install.

Tests to add:

- Import provider package in a clean dependency environment and get dummy.
- `get_provider("codex")` without requests gives a clear `ProviderError`.
- `agent_worker.py --provider dummy --once` works without optional extras.

Acceptance:

- Public package can be installed with no extras and still run dummy smoke.
- Live provider failures are actionable, not import-time crashes.

## Phase 6 - Doctor Command

Purpose: give host users one command that explains runtime health.

Implementation:

- Add `agent_runtime doctor --root <host> --check`.
- Checks:
  required template files present,
  `agent_runtime.yml` valid,
  lock present/fresh when expected,
  core scripts import/help works,
  optional dependency status for selected providers,
  unsafe ToolRunner policy not present,
  message queue directories writable,
  stale claims detected,
  stop files present,
  sync conflicts detected.

Tests:

- Missing `orchestrator_safety_gate.py` is reported.
- Missing optional provider deps are warnings unless provider is configured.
- Stale claim is reported.
- `--check` exits nonzero only for blockers.

Acceptance:

- A user can run one command before trying live agents and see blockers.

## Phase 7 - Verification Matrix

Run after each phase:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests -q
python -m agent_runtime.cli sanitize --root . --check
python -m agent_runtime.cli publish-check --root . --check
python -m agent_runtime.cli publish-bundle --source . --dest .tmp/public-source --check
```

Run before declaring done:

```powershell
$env:PYTHONPATH='src'
python -m pytest tests -q
python -m agent_runtime.cli release-preflight --source . --host-root tests/fixtures/host --remote-url https://github.com/example/agent_runtime.git --tag v0.1.5 --check
```

Manual smoke boundary:

- Do not claim public release readiness from local tests alone.
- Real GitHub publish and workflow evidence remain Owner-approved external
  mutation boundaries.

## Suggested Commit Slices

1. `template-self-contained`: add missing safety, schema, pipeline artifacts and
   smoke tests.
2. `template-smoke-ci`: wire clean host template smoke into CI.
3. `toolrunner-policy`: restrict command policy and add negative security tests.
4. `message-lease`: add race-safe queue claim primitive and worker/dispatch
   integration.
5. `provider-extras`: optional dependencies and lazy provider imports.
6. `doctor-command`: host runtime health checks.

## Definition Of Done

- `pytest tests -q` passes with `PYTHONPATH=src`.
- Clean host template smoke passes in tests and CI.
- `sanitize`, `publish-check`, `publish-bundle --check`, and `release-preflight`
  pass.
- ToolRunner negative security tests prove arbitrary Python, mutable git, pip,
  and path escapes are denied.
- Concurrent claim test proves exactly one worker owns a message.
- README documents the safe install, smoke, optional extras, and doctor flow.
