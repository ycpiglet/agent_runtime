# REVIEW-2026-06-08-agent-runtime-baseline

## Purpose

This is the baseline critical review before the runtime hardening work in
`IMPLEMENTATION_PLAN.md`.

Use this document after implementation to compare:

- what materially improved,
- what is still weak,
- whether the project moved from a distribution/governance core toward a real
  multi-agent runtime.

## Bottom Line

`agent_runtime` is already a strong public distribution, sync, and release
governance core. Its safest parts are the package boundary, host sync safety,
publish/sanitize checks, and the explicit distinction between autonomous and
Owner-gated work.

It is not yet strong enough to call a robust multi-agent operating system. The
main gaps are runtime executability from a clean install, CI coverage for the
installed host template, command-tool isolation, parallel claim safety, and
provider dependency hygiene.

## Current Evidence Snapshot

Observed before implementation:

| Check | Result |
|---|---|
| Package tests | `PYTHONPATH=src pytest tests -q` passed with 94 tests |
| Public sanitization | `sanitize --check` passed with 0 findings |
| Publish readiness | `publish-check --check` passed with 0 findings |
| Publish bundle plan | `publish-bundle --check` passed with 0 findings |
| Root `pytest` | failed because package-data host template tests were collected |
| Template direct execution | core scripts can fail on missing template dependencies |
| Clean dependency story | provider modules can import optional dependencies too early |

The important distinction: package-core checks pass, but the installed runtime
template is not yet proven as a clean, self-contained host artifact.

## Primary Findings

### 1. Host Template Is Not Self-Contained

Severity: critical.

The distributed template references files that are not currently present or not
guaranteed in a clean host install.

Examples:

- `scripts/orchestrator_safety_gate.py`
- `scripts/pipeline.py`
- `schemas/task.schema.json`
- docs referenced by reusable scripts or role guidance

Impact:

A user can install the package and sync the template, then hit immediate runtime
failures when running core scripts. This is a release-quality issue because the
project value is in shipping a reusable host runtime, not only a package CLI.

Success condition after implementation:

- Clean host `sync --apply` creates every required file.
- `agent_orchestrator.py --help`, `agent_worker.py --help`,
  `auto_runner.py --json`, and `check_messages.py` execute in that clean host.

### 2. CI Does Not Yet Prove The Distributed Runtime

Severity: critical.

The current CI validates package internals and public-source hygiene, but not
the template after installation into a host.

Impact:

The package can stay green while the actual runtime artifact is broken.

Success condition after implementation:

- CI creates a clean temp host.
- CI runs `agent_runtime sync --apply`.
- CI executes core template scripts from the generated host.
- CI processes one dummy-provider inbox message end to end.

### 3. ToolRunner Command Guard Is Not A Sandbox

Severity: high.

`ToolRunner` currently narrows some commands but still allows broad `python` /
`py` execution and mutable git operations. That means an agent can route around
file-level guardrails by using `python -c`, arbitrary scripts, or git mutation.

Impact:

Prompt instructions such as "do not commit" or "stay inside safe tools" are not
enforced by the command policy. The command tool becomes a policy bypass.

Success condition after implementation:

- `python -c`, `python -`, `pip`, arbitrary Python scripts, and mutable git
  commands are denied.
- Only exact verification command profiles are allowed.
- Negative security tests cover the denied cases.

### 4. Message Claiming Is Race-Prone

Severity: high.

The current claim model is close to read-check-write frontmatter mutation. Two
workers can observe the same open message and both attempt to claim or reply.

Impact:

The runtime has the shape of a message bus, but parallel execution can produce
duplicate replies or ambiguous ownership.

Success condition after implementation:

- Claim ownership is created with an atomic marker or equivalent file-lock
  primitive.
- Claims include owner/session/pid and lease metadata.
- Stale claims are recoverable under explicit rules.
- Concurrent claim tests prove exactly one claimant wins.

### 5. Optional Dependencies Are Not A Clean Contract

Severity: medium.

The base package declares no dependencies, but some provider paths reference
`requests`, `python-dotenv`, `anthropic`, or `watchdog`. The desired behavior is
that dummy/local runtime paths work without live-provider extras, while live
providers fail with clear installation guidance.

Impact:

Clean installs can fail in surprising ways, or optional provider availability is
unclear to host users.

Success condition after implementation:

- Base install supports package CLI and dummy runtime smoke.
- Extras are explicit: `codex`, `claude`, `watch`, `dev`.
- Provider modules load lazily.
- Missing optional dependencies produce actionable provider errors.

## Comparative Assessment

What is currently strong:

- Public package hygiene.
- Host sync is hash/lock based and avoids silent overwrites.
- Release planning separates local checks from Owner-approved external mutation.
- Runtime documentation correctly treats panes as views, not agents.
- The architecture has a useful role/message/event vocabulary.

What is currently weak:

- Clean host runtime executability.
- Installed-template CI.
- Real command sandboxing.
- Parallel worker correctness.
- Native platform integration depth.
- Replay/eval/dashboard loops.
- Doctor/install/repair UX.
- Worktree-per-agent isolation.

## Baseline Scorecard

| Area | Baseline |
|---|---|
| Public release hygiene | B+ |
| Sync/update safety | B+ |
| Template execution completeness | D |
| Real multi-agent parallelism | C- |
| Claude/Codex native integration | C |
| Command/tool security | D+ |
| Collaboration/governance design | B |
| Self-improvement loop | C- |
| Open-source product competitiveness | C |

## Review After Implementation

When the hardening work is complete, re-run this comparison:

| Area | Baseline | After | Evidence |
|---|---:|---:|---|
| Public release hygiene | B+ | TBD | sanitize, publish-check, publish-bundle |
| Sync/update safety | B+ | TBD | sync conflict tests, lock freshness |
| Template execution completeness | D | TBD | clean host smoke |
| Real multi-agent parallelism | C- | TBD | concurrent claim tests |
| Claude/Codex native integration | C | TBD | provider smoke and docs |
| Command/tool security | D+ | TBD | ToolRunner negative tests |
| Collaboration/governance design | B | TBD | doctor/reporting flow |
| Self-improvement loop | C- | TBD | eval/replay evidence |
| Open-source product competitiveness | C | TBD | install + doctor + smoke UX |

## Minimum Bar To Reclassify The Project

The project should not be described as a strong multi-agent runtime until all of
these are true:

- A clean host template runs without missing files.
- CI validates the installed template, not only package source.
- ToolRunner cannot execute arbitrary Python or mutable git operations.
- Parallel workers cannot duplicate-claim the same message.
- Optional provider dependencies are explicit and lazy.

Once those are true, the project can credibly move from "safe distribution and
governance core" toward "practical local multi-agent runtime."
