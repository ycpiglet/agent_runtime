# TASK-AR-654 — Host-required merge gates

## Outcome

Make product-level contract, ownership, and rendered-output checks mandatory at
W5 without changing existing hosts that have no merge-gate policy.

## Authority and compatibility

- Optional policy source: `agents/host/MERGE-GATES.json`
- Schema: `agent-runtime-merge-gates/v1`
- No policy or an empty gate list preserves the existing queue entry shape and
  verification behavior.
- Enqueue binds the canonical policy digest and ordered gate IDs to the queue
  entry.
- Process reads policy from the integration base, not the worker branch.
- A nonempty gate list requires `protected_paths`, including the policy file.
  Every repository-controlled launcher, config, test, baseline, and manifest
  that can weaken a gate belongs in this integration-base-owned set.
- A missing binding or digest/ID drift blocks before rebase or merge and
  requires re-enqueue.
- A worker branch cannot change any protected gate-control path through the
  queue. Policy and gate-control evolution are owner-controlled
  integration-base operations.

## Gate contract

Each gate has a unique lowercase `id`, a non-empty command, and optional
`include_paths` / `exclude_paths` globs. Required gates run after the entry's
narrow/default verification and before merge or PR handoff. They cannot be
removed with `--verify`.

Commands are parsed with `shlex` and executed as argv without a shell.
`{task_id}`, `{branch}`, and `{base}` are the only supported placeholders.
Path applicability is calculated from the rebased `base...HEAD` diff,
including deletions.

## Failure behavior

- Invalid policy: enqueue fails without writing queue state.
- Policy drift/unbound legacy entry: process stops before branch mutation.
- Required command failure, launch error, or timeout: entry becomes `failed`,
  feedback names the gate and command, and the integration branch is restored.
- Dry-run remains read-only, reads the same effective integration ref as real
  processing, and reports applied/skipped gate IDs.

## Bean Wiki vertical slice

Bean Wiki supplies two host gates through this policy:

1. `design-contract` — canonical token generation/drift and ownership manifest
2. `design-visual` — pinned-browser reviewed screenshot baselines

Its `protected_paths` cover the policy, package scripts/lock, CI workflow,
design gate implementation, Playwright configuration/specs, and approved
screenshots so a worker cannot weaken the judge in the same change being
judged.

The same commands run in GitHub CI because PR handoff does not control the
later remote merge. GitHub required checks, rather than the local queue alone,
are the remote enforcement boundary.

## Out of scope

- No `agent_runtime.yml` schema change.
- No modification to adoption, sync, doctor, or TASK-AR-648 pilot files.
- No automatic baseline acceptance.
- No claim that path ownership replaces human design judgment.
