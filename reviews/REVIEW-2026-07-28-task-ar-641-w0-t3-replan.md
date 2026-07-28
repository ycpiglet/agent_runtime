---
title: TASK-AR-641 W0 T3 Replan
date: 2026-07-28
signal: pass
score: 97
priority: P0
tags: [task-ar-641, w0, t3-replan, brownfield, adoption, bean-wiki, allimbot]
---

# TASK-AR-641 W0 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-641-001`. The registered problem is still present:
the current inventory is an upstream-export classifier, not a brownfield
adoption planner; normal doctor treats a repository with no Agent Runtime
installation as a broken installation; and ignored/generated trees inflate
the review surface.

This unit adds only deterministic read-only planning. It must not create a
configuration, copy a template, write a lock, invoke sync apply, repair a
host, or change Bean Wiki or Allimbot.

## Current Evidence

The baseline was measured from Agent Runtime `main` at `312ed101`.

| Host | Git HEAD | Current inventory | Current doctor | Working tree |
| --- | --- | ---: | --- | --- |
| Bean Wiki | `808309a7` | 11,136 files | 19 blockers, 15 warnings, 1 info | dirty; user editorial work preserved |
| Allimbot | `4f3c2e84` | 2,926 files | 19 blockers, 15 warnings, 1 info | dirty; user implementation work preserved |

The measurements are observations, not fixture inputs. Pilot repositories may
continue changing; tests must reproduce their path shapes in temporary
repositories and never depend on or modify live host state.

Bean Wiki has root `AGENTS.md`, `CLAUDE.md`, Claude agents and skills, editorial
documents, and large ignored/generated trees including `.next`, `node_modules`,
`dist`, `.vinext`, `.wrangler`, and `.vercel`.

Allimbot has no root instruction seam but does have an agent marketplace,
plugin skills, integration/status/security documents, and ignored/generated
trees including `.venv`, `build`, `dist`, nested Next.js/Node trees,
`supabase/.temp`, and worktrees.

## Read-only Adoption Contract

### Public command

Add:

```text
agent_runtime adopt --plan --root <host> [--json]
```

`--plan` is required. There is no `--apply` in this unit. Text and JSON
renderers consume the same immutable plan. Repeated runs over the same
filesystem snapshot must be byte-stable; the plan contains no timestamps,
random identifiers, or unstable iteration order.

The JSON schema is `agent-runtime-adoption-plan/v1` and always contains:

- absolute `root`;
- effective `profiles` and `capabilities`;
- inventory counts, scan strategy, warnings, and sorted detected host assets;
- sorted actions;
- sorted conflicts/findings;
- a readiness summary.

Every action contains `path`, `action`, `ownership`, and `reason`. Action is one
of `add`, `preserve`, `conflict`, or `skip`; ownership is one of `managed`,
`seed_once`, `host_owned`, or `generated`.

### Inventory boundary

Use Git as the source of truth when available:

- tracked and non-ignored untracked paths come from Git's index/ignore
  evaluation;
- ignored paths do not enter host-asset or conflict evaluation;
- well-known generated dependency/build paths are reported separately and do
  not enter adoption actions even if tracked;
- untracked does not imply generated or disposable;
- nested `.gitignore`, negation, and spaces are delegated to Git rather than a
  partial in-process glob implementation.

If Git is absent or its query fails, fall back to a conservative filesystem
walk that prunes only well-known generated roots. Do not silently label other
paths ignored. Record a stable warning and the fallback scan strategy.

Never follow directory symlinks. A symlink that resolves outside the host root
is a finding and cannot become an action target.

### Host asset detection

Detect, without interpreting product semantics:

- root agent instruction files;
- Claude agent and skill files;
- Codex/agent marketplace and plugin skill files when they are source-visible;
- Agent Runtime config/lock-like files;
- source-visible product, status, editorial, integration, and security
  documents under `docs/`.

Template-external host assets appear only in the detected asset inventory.
They are not proposed mutations. A recognized host instruction colliding with
a seed seam is preserved as `host_owned`, not treated as a broken runtime.

### Template and ownership planning

The packaged `templates/project` tree is the current core template baseline.
TASK-AR-643 will introduce dependency-closed profile manifests; this unit must
not claim those manifests already exist. Additional selected profiles remain
visible in effective configuration while their current additional file set is
empty.

Ownership resolution order is:

1. explicit effective v2 ownership, including the v1 unmanaged-to-host-owned
   projection;
2. seed seam defaults for root agent instruction files and initial project
   state;
3. generated defaults for known generated views;
4. managed for remaining packaged template files.

Planning behavior:

- missing managed/seed files: `add`;
- existing seed or host-owned files: `preserve`;
- existing managed file identical to its package template: `skip`;
- existing managed file with different content: `conflict`;
- generated files: `skip` with their producer/lifecycle reason;
- unsafe paths or non-regular collisions: finding plus `conflict`.

No branch above authorizes a write.

## Pre-adoption Doctor Contract

Add `doctor --pre-adoption`. It uses the adoption planner and a separate
read-only check path. It must not call the installed-host doctor path because
that path intentionally checks writability and runtime integrity.

Pre-adoption mode checks repository readability, Git/ignore availability,
template availability, unsafe paths/symlinks, detected host assets, and
adoption conflicts. These are not broken-installation blockers:

- missing `agent_runtime.yml` or lock;
- missing runtime scripts, roles, claims, messages, or stop-file parents;
- unapplied template files.

Normal doctor behavior remains unchanged. `--pre-adoption` and `--repair` are
incompatible.

## Test Matrix

- Git-backed tracked, untracked, ignored, nested-ignore, negation, and
  space-containing paths.
- Generated roots at repository root and nested web/console/supabase paths.
- No-Git and failed-Git conservative fallback.
- External and in-root symlinks without directory traversal.
- Bean Wiki path-shape fixture detecting instructions, Claude agents/skills,
  and editorial docs while excluding generated trees.
- Allimbot path-shape fixture detecting marketplace, plugin skill,
  integrations, and security/status docs while excluding generated trees.
- V1 unmanaged and v2 ownership/profile projection.
- Missing, identical, changed, seed, host-owned, and generated template
  actions with stable reasons.
- Text/JSON stable ordering and repeated-run byte equality.
- Full before/after file-list, content digest, and mtime immutability proof.
- Normal doctor regression plus pre-adoption missing-installation behavior.

## Scope Amendments

The registered target files remain correct:

- `src/agent_runtime/adoption.py` (new)
- `src/agent_runtime/inventory.py`
- `src/agent_runtime/doctor.py`
- `src/agent_runtime/cli.py`
- `tests/test_adoption.py` (new)
- `tests/test_inventory_sync_sanitize.py`
- `tests/test_doctor.py`

Do not add host-specific paths to the reusable template or mutate pilot
repositories. Do not implement apply, profile manifests, ownership-aware sync,
seed transitions, generated producers, or adapter execution in this unit.

## W2 Decision

Dispatch one `worker_standard` implementation agent after this record and its
assumption anchors are committed. Reserve independent W4b for an adversarial
read-only, ignore-boundary, and host-mutation audit. Bean Wiki and Allimbot
remain read-only evidence sources until their dedicated pilot tasks.
