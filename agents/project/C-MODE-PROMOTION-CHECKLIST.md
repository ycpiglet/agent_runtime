# C-mode Promotion Checklist

## Status

`block` until every prerequisite below is met.

## Prerequisites

- Three consecutive B-mode proposal-only cycles have `status: pass`.
- Proposal precision is acceptable: duplicates collapse and weak evidence does
  not create tasks.
- Trace, eval, grader, correction, or A2A evidence is linked when available.
- Release/version consistency steward status is `pass`.
- Guardrail gate status is `pass`.
- Rollback proof exists for every supported auto-apply action.
- Owner policy explicitly allows the exact C-mode action class.
- Diversity council review exists for high-impact planning rule changes.

## Allowed C-mode Actions

- Generated view refresh.
- Stale local link repair.
- Proposal dedupe and supersession.
- Watch-only reminders.
- Low-risk plan hygiene with verifier list and rollback audit.

## Prohibited C-mode Actions

- Release/version bump, tag, push, external publication, or PR creation.
- Dependency installation.
- Secret or production-data changes.
- Destructive changes.
- Owner-only decisions.
- Gate weakening or policy loosening.

## Demotion

C-mode demotes to B-mode immediately when a guardrail fails, owner rejects a
proposal, verification fails, churn increases, or a high-risk proposal appears.
