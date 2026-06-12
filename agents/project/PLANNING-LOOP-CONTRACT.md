# Planning Loop Contract

## Bottom Line

The runtime planning loop is a bounded RSI workflow. Its default mode is
proposal-only B-mode: it may scan local evidence, create inspectable proposals,
and draft task files, but it must not mutate canonical project state until a
separate approved apply step runs.

## Lifecycle

`planning_loop` uses these states:

- `idle`: no scan is active.
- `scanning`: local read-only evidence collection is running.
- `proposed`: findings have been converted into proposal records.
- `under_review`: reviewers or the diversity council are recording verdicts.
- `approved`: an owner or delegated reviewer approved a low-risk proposal.
- `applied`: an approved proposal was applied and an audit record exists.
- `rejected`: the proposal was explicitly rejected.
- `superseded`: newer evidence replaced the proposal.
- `blocked`: guardrails, owner boundary, budget, or verification stopped the loop.

## Required Proposal Fields

Every proposal record must include:

- `id`: stable proposal identifier.
- `mode`: `B` for proposal-only or `C` for bounded auto-apply candidate.
- `status`: proposal lifecycle state.
- `action_type`: `new_task`, `plan_update`, `doc_repair`, `eval_expansion`,
  `release_version_consistency`, `retro_compound_follow_up`, `watch_only`, or
  `c_mode_promotion`.
- `risk_tier`: `low`, `medium`, `high`, or `owner`.
- `source_refs`: concrete local source paths and optional line references.
- `trace_id`: trace, eval, grader, correction, or A2A id when available.
- `dedupe_key`: stable key used to collapse duplicate findings.
- `evidence`: short structured evidence snippets.
- `target_files`: files that an approved apply step may change.
- `rollback_path`: local rollback/audit record path.
- `verifier_list`: commands or manual checks required before closure.
- `owner_boundary`: explicit approval boundary and prohibited mutation notes.

## B-mode Boundary

B-mode may:

- read local repo files;
- emit scan JSON under `agents/planning/scans/`;
- write proposal records under `agents/planning/outbox/`;
- write draft task markdown under `agents/planning/drafts/`;
- write planning audit records under `agents/planning/applied/`.

B-mode must not:

- edit canonical backlog/task/status/roadmap/release docs;
- bump versions, create tags, push, publish, or open pull requests;
- install dependencies or touch secrets/prod data;
- weaken owner governance, hooks, or gates.

## C-mode Boundary

C-mode is disabled by default. It can be considered only after the promotion
gate passes and at least three proposal-only cycles have completed without
drift, duplicate churn, unresolved high-risk proposals, or failed verification.

Allowed C-mode actions are limited to:

- generated view refreshes;
- stale local link repair;
- proposal dedupe/supersession;
- watch-only reminders;
- low-risk plan hygiene with rollback and audit records.

Prohibited C-mode actions always require explicit owner approval:

- release/version bump, tag, push, external publication, PR creation;
- dependency install;
- secret or production-data changes;
- destructive filesystem operations;
- owner-only decisions or gate-weakening changes.

## Silence Rules

The scan should stay silent when evidence is weak, duplicated, already resolved,
or below confidence threshold. Weak observations may appear in the scan report
as `proposal_allowed: false`, but they must not create task proposals.

## Trigger Contract

Allowed triggers are `manual`, `hook`, `schedule`, `ui`, `task-complete`, and
`cycle-complete`. Hook, schedule, and UI triggers may request scans and proposal
generation only; they cannot apply canonical mutations.

## Apply Contract

Approved apply must check the proposal status, risk tier, verifier list,
rollback path, owner boundary, and guardrails. Failed verification must leave
canonical docs unchanged or create an explicit reverted audit record.

## Registration Traceability

Planning discussions recorded as planning records in `reviews/` (frontmatter
`type: meeting`/`type: planning` or the `planning-record` tag) must register
their follow-up work, not only describe it: referenced task files must exist,
referenced task sets must appear on `BACKLOG-BOARD.md`, and
`agents/project/NEXT-SESSION-POINTER.yml` must stay consistent. Registration is
complete only when `python scripts/conversation_work_audit.py --check` (also
run inside `scripts/owner_governance_gate.py`) reports no block findings for
the record.
