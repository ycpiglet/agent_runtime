---
type: compound
title: Release-ops + shared-checkout concurrency compound (v0.3.0 / v0.3.1 cycle)
date: 2026-06-22
status: recorded
signal: pass
source_session: 712849dc-2fe1-43a5-ab90-2a6a26ffa1b4
casebook: agents/project/casebooks/failure-and-compound-casebook.md
related: [PR #178, PR #179, PR #180, PR #183, PR #184, PR #187, PR #188, issue #185, issue #128]
---

# Release-ops + shared-checkout concurrency compound

A single session (recover from a PC crash → publish v0.3.0 → patch + publish
v0.3.1 for a consumer bug) surfaced seven recurring failure modes. Each is now a
casebook case (`failure-and-compound-casebook.md`) with a route; this note holds
the cross-cutting reusable lessons and the feed-forward.

## What happened, and why

1. **Releases were structurally un-cuttable.** `release-auto.yml` fired only on a
   weekly cron and its safety gate required `latest-completed-main-test SHA ==
   current main HEAD`. Under the repo's high merge velocity (many autonomous
   agents merging hourly) main HEAD always moved past the validated SHA, so every
   run — cron *and* manual dispatch — skipped with `ci_status=moved`. v0.2.0 sat
   for 8 days / 337 commits with no tag, so the downstream host (autofolio) got
   no `update-notify` (notify keys on *published tags*, not main). **Root cause:
   a time-based + identity-strict (`==HEAD`) trigger is wrong for a fast-moving
   trunk.** (`release-perpetual-skip`)

2. **Semver under-bumped.** The cadence heuristic recommended `patch` unless a
   template was deleted or a schema changed — so 114 `feat` commits proposed
   `0.2.1`. **Root cause: bump derived from file-shape, not change semantics.**

3. **A release is a *cascade*, not one file.** Bumping only `pyproject` left the
   "current public tag" stale across CLI `--tag` defaults (5 files), `test.yml`
   (3), `RELEASE-GATE-TEMPLATE.yml`, the host fixture `ref` + its digest lock,
   and two test constants — discovered via three cascading CI failures.
   (`release-version-cascade`)

4. **Template edits silently staled the host lock.** Editing any
   `templates/**` file without regenerating `tests/fixtures/host/agent_runtime.lock.json`
   reds `test_lock_merge_driver`. (`template-stale-host-lock`)

5. **The shared checkout is a race surface.** A concurrent agent advanced a
   merged branch by 4 commits between two of my git calls; a `git branch -D` on
   the cached (stale) tip deleted unmerged work (recovered via `git branch <name>
   <sha>`). Same class as the earlier `git clean -fd` losses. **Root cause:
   branch refs / HEAD / worktree are all moving targets under concurrency.**
   (`shared-checkout-ref-race`)

6. **Non-hermetic tests polluted a commit.** The suite rewrote `generated_at` in
   tracked `ARCHIVE-INDEX.md` / `BACKLOG-BOARD.md`; a `git add -A` swept that into
   the release commit (amended out). (`nonhermetic-test-tracked-mutation`)

7. **Gates assumed the source-repo layout.** continuity/owner-governance/state-machine
   gates hard-coded `src/agent_runtime/templates/**`, so they failed in consumer
   projects with only root docs — the autofolio dogfooding bug #185, fixed in
   v0.3.1 (#187). (`consumer-project-path-assumption`)

## Reusable lessons (durable)

- **Trigger on the artifact, not the clock; act on the validated SHA, not HEAD.**
  Release/CI automation on a fast trunk must fire from `workflow_run` (the moment
  a green SHA exists) and *check out that SHA* — never require it to still equal a
  moving HEAD.
- **Derive version from change semantics:** feat → minor, breaking (`!` /
  BREAKING CHANGE) → major, fix/chore → patch.
- **A release is a coupled set.** Treat the current-public-tag references as one
  atom; the list lives in `[[agent-runtime-release-cadence-direction]]`.
- **origin is the only durable store** under concurrency; commit+push green work
  immediately, isolate in a worktree, never clean up / delete refs while another
  agent is active, and re-read the live tip right before any destructive ref op
  (`[[agent-runtime-merge-concurrency]]`, `[[agent-runtime-work-branch-isolation]]`).
- **Stage explicit pathspecs** (never `git add -A`) when composing a
  release/version commit; tests must be hermetic (`tmp_path`, never the repo root).
- **Framework code must run in a consumer project**, not just the source repo:
  resolve paths root-OR-template, skip absent source-only paths.

## Feed-forward (routes — release/version/destructive items stay proposals)

- Keep the shipped guards green: the `release-auto` workflow-wiring test
  (`release-perpetual-skip`) and the consumer-gate fixtures
  (`consumer-project-path-assumption`).
- Propose a single `release-version-cascade` bump+verify helper, a template→lock
  auto-regen hook, a `safe-ref-op` wrapper, hermetic board/archive tests, and a
  bounded retry for the flaky temp-git gate tests — see the casebook rows.
- Downstream feedback should ride the existing intake (issue → fix → patch
  release → consumer re-sync + shim drop), as #185 → v0.3.1 did.
