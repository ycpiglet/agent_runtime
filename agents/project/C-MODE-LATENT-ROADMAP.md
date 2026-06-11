# C-mode Latent Roadmap

## Status

`C-mode` is latent and blocked. It is not an active implementation path for this
checkout.

## Activation Rule

C-mode cannot activate from a single successful run. It may move from latent to
planned only when all of the following are true:

- At least three consecutive B-mode cycles pass with proposal-only output.
- Proposal precision, proposal recall, false-positive proposal rate, eval
  regression rate, and repeated-failure closure rate are measured.
- Release/version steward, guardrail gate, taskset gate, owner-doc gate, and
  task identity gate pass.
- A diversity council record exists for high-impact rule changes.
- Every supported action class has a rollback path and verifier list.
- Owner policy explicitly allows that exact low-risk action class.

## Allowed Future Action Classes

| Action | Requirement |
| --- | --- |
| generated view refresh | deterministic regeneration and clean diff |
| stale local link repair | source exists and verifier confirms link health |
| proposal dedupe | same dedupe key and same evidence hash |
| watch-only reminder | no canonical mutation |
| low-risk plan hygiene | local-only, reversible, verifier-backed |

## Always Prohibited Without Owner Approval

- Release/version bump, tag, push, PR creation, external publication.
- Dependency installation.
- Secret, credential, or production-data changes.
- Destructive filesystem or remote actions.
- Owner-only decisions.
- Gate weakening, policy loosening, or scope expansion.

## Revisit Criteria

Revisit option C only after the RSI operating system has a closeout review with
passing local deterministic evidence and at least one later B-mode operating
cycle that demonstrates proposal quality over real evidence. Until then, C-mode
language in docs must be read as a roadmap boundary, not approval.

