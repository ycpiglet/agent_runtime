---
type: review
title: Agent/skill track consolidation — canonicality criteria
date: 2026-06-22
status: assessed
signal: pass
---

# Agent/skill track consolidation — what to take to main

Similar-role agents and skills were developed on different tracks (root `scripts/`
+ `skills/` + `agents/` vs the `src/agent_runtime/templates/project/**` mirror, plus
parallel branches). This review states the decision rule and applies it.

## Canonicality decision rule

**Root is canonical (the live instance); the template tree is the distribution +
host-customization baseline.** When two versions compete:

1. **Byte-parity + same commit history** → not a conflict. Root is the live
   instance (orchestrator dispatches via `registry_id`); template is the read-only
   distribution copy. Keep them in sync.
2. **Root is newer and adds safety/governance detail** → **root wins**; the
   template is stale and must be regenerated from root.
3. **Root is an operational instance, template is a persona library** → not a
   conflict (different layers: execution vs design). No merge.
4. **Root is evolved, template is an intentional stub** → root is canonical for
   this repo; the stub is correct-by-design for host customization. No merge.
5. **Two competing registries** (e.g. tier-model `ORG-MODEL.yml` vs persona
   `roles.yml`) → pick the one bound by governance/gates as root-of-truth;
   deprecate or demote the other to an optional index.

Tie-breakers, in order: governance/gate-bound > registry-registered > newer +
references a live task/issue > has tests > byte-parity maintained > more complete.

## Findings

| Group | Members | Verdict |
|---|---|---|
| 7 ops skills (release-conductor, independent-verification, merge-integrator, scm-steward, session-closeout, taskset-dispatch, work-analytics) | root ↔ template **byte-identical** | OK — keep in sync (rule 1) |
| **wave-conductor** | root 3993B (TASK-AR-529 footprint safety boundary, GH #125) vs template 3358B (missing it) | **DRIFT** — root canonical; regenerate template (rule 2) → **fixed in this PR** |
| ORG-MODEL.yml | root 132L (full org) vs template 103L (stub) | OK — intentional stub (rule 4) |
| ORG.md / TEAMS.md | root detailed vs template stub | OK — intentional stub (rule 4) |
| Agent defs | root operational (lead_engineer/project/planning/runtime) vs template persona library (16 roles) | OK — orthogonal layers (rule 3) |
| Role registry | root `ORG-MODEL.yml` (tier model, TASK-AR-557, gate-bound) vs template `roles.yml` (388L persona registry) | **DECISION NEEDED** — ORG-MODEL.yml is root-of-truth (rule 5); propose deprecating/demoting `roles.yml` to an optional index — see proposal |

## Actions

- **Applied (this PR):** regenerated `templates/project/skills/wave-conductor/SKILL.md`
  from the canonical root so the footprint post-hoc safety boundary ships to host
  projects; restored root↔template byte-parity; regenerated the host lock fixture
  (template digest changed — see `template-stale-host-lock`).
- **Proposal (governance, not auto-applied):** record in `SKILL-GOVERNANCE.md` /
  `ORG-MODEL.yml` that the tier-model `ORG-MODEL.yml` is the canonical role
  registry; decide whether `roles.yml` is deprecated or kept as an optional
  skill-file index. Owner/governance decision.
- **No action:** the template stubs (ORG.md, TEAMS.md, ORG-MODEL.yml) are
  correct-by-design; only backport when root governance changes.

## Standing rule (feed-forward)
Any change to a root `skills/**` / `scripts/**` file that has a template mirror
MUST regenerate the mirror (byte-parity) AND the host lock in the same change.
The wave-conductor drift existed because a safety fix landed root-only.
