---
schema_version: agent-runtime-review/v1
id: REVIEW-2026-07-31-task-ar-654-compound-closure-t3-replan
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
task_set_id: TASKSET-AR-V080-OPERABILITY-HARDENING
review_kind: t3-replan
status: accepted
created_at: 2026-07-31T04:02:36+09:00
reviewer: codex-root-task-ar-654-orchestrator
trigger_ref: reviews/RESEARCH-2026-07-30-agent-runtime-next-release-gap-audit.md
tags: [task-ar-654, t3, compound, repeated-failure, consumer-skill]
---

# TASK-AR-654 Compound closure T3 replan

## Why replan

TASK-AR-653 legitimately changed shared closure and template surfaces after the
taskset's previous assumption snapshot. The registered TASK-AR-654 unit also
named the nonexistent `tests/test_compound_record.py`, omitted the authoritative
`src/agent_runtime/knowledge_records.py`, and did not include the root/template
`work.py`, registries, mirror contract, or derived host lock that the acceptance
criteria require.

The root-only `failure-to-regression` skill additionally declares dependencies
on Runtime repository casebooks and proposal documents that are not shipped to
consumer hosts. Copying that file unchanged would create a discoverable but
unusable consumer skill.

## Decision

Amend the worker-ready unit before claim creation.

1. Treat either a normalized `defect_signatures` value or
   `escalation_triggers: repeated_failure` on the current unit or its parent
   task as a mandatory Compound lane.
2. Require a canonical Compound ref linked to the current task/unit identity.
   A prior record that merely matches the signature is lookup context, not
   current-work closure evidence.
3. Validate every declared prevention ref as an existing repository-contained
   path and require at least one supported prevention destination:
   - a regression fixture under `tests/` (or a repository test script);
   - an executable `*_gate.py`;
   - a canonical task/unit proposal under `agents/lead_engineer/tasks/`; or
   - an accepted-watch review whose frontmatter explicitly records accepted
     status, `decision: accepted_watch`, reviewer identity, and current work
     linkage.
4. Apply the same repeated-failure predicate in `work.py close` and the
   work-linked Stop closure gate. Preserve the existing review/retro alternative
   for ordinary substantial work.
5. Keep claim-time canonical knowledge lookup before claim persistence and add
   regression coverage rather than weakening that path.
6. Rewrite the root skill into a concise, consumer-safe procedure, copy it into
   the core template, and register it in both product and consumer asset
   registries. Do not depend on root-only casebook files.
7. Preserve append-only canonical Compound records and the legacy Compound log.
   Enforcement occurs when a record is used for repeated-failure closure; this
   task does not rewrite historical records.

## Safety and compatibility boundaries

- Reject traversal, absolute paths, missing paths, and symlink escapes when
  resolving prevention destinations.
- Supplementary prevention refs may point to documentation, but at least one
  supported executable/proposal/watch destination is mandatory.
- Do not require Compound for ordinary work that declares neither a defect
  signature nor the repeated-failure escalation trigger.
- Do not create provider calls, external side effects, releases, tags, pushes,
  or consumer-repository writes in this unit.

## Verification contract

- Use the actual `tests/test_compound_records.py`.
- Cover defect-signature and escalation-trigger negatives, task-to-unit
  inheritance, invalid/missing/escaping prevention refs, supported destination
  kinds, ordinary review/retro compatibility, claim lookup ordering, core
  profile selection, skill structure, template parity, and host-lock freshness.
- Run an independent W4b against the exact final implementation commit before
  claim release or merge.
