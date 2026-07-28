---
title: TASK-AR-642 W0 T3 Replan
date: 2026-07-28
signal: pass
score: 97
priority: P0
tags: [task-ar-642, w0, t3-replan, sync, ownership, reconcile, autofolio]
---

# TASK-AR-642 W0 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-642-001` as one bounded implementation unit.
Current sync still treats only exact v1 `sync.unmanaged` paths specially and
aborts every update when any managed conflict exists. Config v2 already parses
the four required ownership modes, but sync and lock do not consume that
projection.

This unit makes the existing packaged template ownership-aware, adds a
deterministic read-only reconcile report, and adds an explicit safe-only apply
mode. It does not add automatic merging, mutate a pilot repository, invent
profile-specific file manifests, or solve lifecycle claim cleanup.

The baseline is Agent Runtime `main` at `eecb0dc4`.

## Current Evidence

| Area | Current behavior | Required behavior |
| --- | --- | --- |
| Ownership | Sync and lock read exact `config.unmanaged_paths` only | Consume effective `managed`, `seed_once`, `host_owned`, and `generated` ownership |
| Conflict handling | One conflict makes legacy apply write zero files | Preserve legacy behavior and add opt-in safe-only application |
| Lock | `agent-runtime-lock/v1` records only template and managed digests | Record effective ownership and seed completion in v2 while reading v1 |
| Comparison source | Direct sync uses the package that happens to be running | Exact-ref host update remains the authoritative comparison path |
| Profiles | Config exposes profiles and capabilities | Report them, but use the current packaged template as this unit's file set |

The focused baseline suite passes:

```text
python -m pytest tests/test_inventory_sync_sanitize.py -q
102 passed
```

No baseline or test run writes Bean Wiki, Allimbot, Autofolio, or Tag Manual.

## Consumer Evidence

Autofolio v0.6 is the strongest installed-runtime precedent. Its v1 config has
20 explicit unmanaged seams, including root instructions, role/schema/report
overlays, local governance scripts, compound records, and reporting indexes.
Its lock contains 256 packaged template files. Its integration documentation
correctly separates framework, host overlay, and seam, but also documents the
current all-or-nothing conflict behavior. The earlier taskset research count of
21 unmanaged paths is superseded by this direct count of 20.

Tag Manual has the same architectural need without a runtime config or lock.
Its tracked source includes root agent instructions, `.agents/skills`, and an
`agents/` tree, while local/runtime state such as `.claude`, `.codex`, session
events, schedule runs, generated indexes, evaluation logs, and Supabase
temporary state is ignored. This is evidence for reusable ownership modes, not
a request to encode Tag Manual paths into the core package.

Bean Wiki and Allimbot remain the first dedicated pilots, but they stay
read-only until their pilot tasks. TASK-AR-642 tests consumer-shaped temporary
fixtures instead of importing mutable live repositories.

## Effective Manifest Boundary

For TASK-AR-642, the effective file set is the current packaged
`templates/project` tree after the existing generated-artifact filter.
Profiles and capabilities are reported as effective configuration metadata,
but they do not yet add or remove packaged files. TASK-AR-643 owns clean-host
dependency closure and any later profile-specific file manifest.

Ownership is resolved from config v2 by exact path or descendant path, matching
the projection already used by adoption planning. Config validation continues
to reject reserved paths and cross-mode overlaps. V1 `sync.unmanaged` remains
byte-compatible and projects into effective `host_owned`.

Every packaged path has exactly one effective mode:

1. explicit effective ownership from config, including the v1 projection;
2. existing seed defaults for root agent instructions and the initial session
   pointer;
3. existing generated boundaries;
4. `managed`.

`host_owned` and `generated` paths are visible in reconcile output but can
never enter an apply set.

## Ownership State Machine

| Mode | Host and lock state | Reconcile action | Writable |
| --- | --- | --- | --- |
| managed | target missing | create | yes |
| managed | target equals new template | identical | no |
| managed | target digest equals prior lock digest | update | yes |
| managed | target differs from template and prior lock | conflict | no |
| seed_once | no prior seed evidence and target missing | seed | yes, once |
| seed_once | target exists | preserve and mark seeded on the next valid lock | no |
| seed_once | v2 lock records completion | preserve, including intentional deletion | no |
| seed_once | v1 lock previously managed this path | treat as already seeded | no |
| host_owned | any state | preserve/excluded | never |
| generated | any state | producer-owned/excluded | never |

A v1 lock is valid migration evidence. If its `managed_files` contains a path
newly classified as `seed_once`, that path is already installed even when the
host later deleted it; sync must not recreate it. If a seed path has neither a
target nor prior installation evidence, it may be created once.

Safe application copies canonical source bytes using the existing write
boundary. It does not merge, delete, rename, chmod, follow symlinks, or replace
a non-regular target. Any unsafe or non-regular collision is a conflict.

## Reconcile and Apply Contract

Add these sync modes:

```text
agent_runtime sync --root <host> --reconcile [--json]
agent_runtime sync --root <host> --apply-safe
```

`--reconcile` is read-only. Its text and JSON renderers consume the same frozen
plan and use stable path ordering. The JSON schema is
`agent-runtime-sync-reconcile/v1`; it contains:

- root, project, effective profiles, and capabilities;
- configured upstream package, remote, and pinned ref;
- comparison template root and digest;
- lock schema and migration state;
- sorted actions with path, ownership, action, reason, and safety;
- counts for safe updates, conflicts, preserved paths, and excluded paths.

The output contains no timestamp, random identifier, or filesystem iteration
order. `--reconcile` exits nonzero when conflicts remain and zero otherwise.
`--json` is valid only with `--reconcile` in this unit.

`--apply-safe` is the only new mutation authorization. It applies managed
creates/updates and first-time seed creates whose plan marks them safe. It
reports every preserved, excluded, and conflicting path. It exits nonzero when
conflicts remain even if safe files were written, and its output states both
the applied count and remaining conflict count.

Existing modes remain compatible:

- `--check` remains read-only and nonzero on conflict;
- `--diff` remains read-only;
- legacy `--apply` remains all-or-nothing and writes zero files on any
  conflict;
- `allow_silent_overwrite: true` remains a blocker in every mode.

No default command silently changes from legacy apply to safe-only apply.

## Lock v2 Contract

Newly written locks use `agent-runtime-lock/v2`. Existing v1 and legacy lock
filenames remain readable for at least this release.

Lock v2 records:

- project and configured upstream package, remote URL, and pinned ref;
- informational package version;
- effective profiles and capabilities;
- template digest and packaged file count;
- deterministic path-to-mode ownership projection;
- managed source digests used for future safe-update comparison;
- seed-completion evidence for existing, newly seeded, and v1-migrated seed
  paths.

Host-owned and generated paths never enter `managed_files`. A lock write is
invalid while reconcile conflicts remain because doing so would bless unresolved
host content as the new baseline. Package version is diagnostic metadata and
must not choose the comparison source.

The lock serializer remains deterministic and preserves current newline and
sorted-key behavior.

## Pinned Source Contract

`host_update` is the authoritative pinned-source workflow. It validates an
immutable release tag or 40-character commit SHA, installs exactly
`remote_url@upstream.ref` into an isolated directory, and executes that
installation's template and CLI.

TASK-AR-642 changes that workflow to expose reconcile and to invoke explicit
safe-only application when requested. The resulting lock records the configured
pinned ref and the digest of the exact isolated template used for comparison.

Direct `agent_runtime sync` continues to support tests and local package use,
including `--template-root`. It must report the configured ref and actual
template root/digest, but it must not claim that an arbitrary currently running
package was verified from the ref. The locally installed `package_version`
never substitutes for `upstream.ref`.

## Required Test Matrix

- V1 unmanaged and v2 host-owned parity.
- Exact and descendant ownership resolution, reserved paths, and overlap
  rejection regressions.
- Managed missing, identical, clean-lock update, host-edited conflict, and
  non-regular collision.
- Seed first creation, existing seed preservation, post-lock deletion without
  recreation, and v1-managed migration without recreation.
- Host-owned and generated paths excluded from every write path.
- Two safe updates plus at least two conflicts: legacy apply writes zero;
  apply-safe writes two, reports both conflicts, and returns nonzero.
- Reconcile text/JSON ordering and repeated-run byte equality.
- V1 lock read compatibility and deterministic v2 lock output.
- Lock refusal while unresolved conflicts exist.
- Host update command construction and execution use the exact pinned install,
  not ambient package version.
- Autofolio-shaped v1 fixture with representative unmanaged seams.
- Template smoke and existing check/diff/apply regressions.

Mutation tests compare before/after file lists and content digests for
host-owned, generated, conflicting, and unrelated files.

## Scope Amendments

Implementation targets:

- `src/agent_runtime/sync.py`
- `src/agent_runtime/lock.py`
- `src/agent_runtime/cli.py`
- `src/agent_runtime/host_update.py`
- `src/agent_runtime/config.py` only if a shared ownership helper is needed
- focused tests in `tests/test_inventory_sync_sanitize.py` and
  `tests/test_template_smoke.py`

Do not modify consumer repositories. Do not add profile-dependent template
files, three-way merging, generated producers, dependency closure, pilot
adoption, lifecycle claim cleanup, or UI work.

The active-claim absolute-path CI failure, synthetic auditor-claim schema gap,
and transient closeout fixture failure observed during TASK-AR-641 are
control-plane compound inputs for TASK-AR-645/TASK-AR-651, not sync scope.

## W2 and W4 Decision

Dispatch one `worker_standard` implementation agent after this record and the
new assumption anchors are committed. Reserve W4b for a different
`reviewer_standard` agent to audit overwrite safety, migration behavior,
determinism, and pinned-source truth.

Do not auto-merge. Release task claims before PR CI so repository-local
worktree paths cannot invalidate remote gates. Bean Wiki and Allimbot remain
unmodified until their dedicated pilot work begins.
