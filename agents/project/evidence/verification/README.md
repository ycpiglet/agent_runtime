# Verification Evidence Registry

## Purpose

This registry stores the command-level proof needed before taskset closeout,
Owner handoff, or C-mode promotion claims.

## Verification Record Shape

| Field | Meaning |
| --- | --- |
| `record_id` | Stable identifier for query, dedupe, and closeout references. |
| `command` | Exact command that was run. |
| `source_command` | Same command in normalized evidence form for cross-registry queries. |
| `source_path` | Script, gate, or report path that produced the verification. |
| `cwd` | Working directory. |
| `result` | pass, watch, or block. |
| `exit_code` | Process exit code when applicable. |
| `findings` | Count or list of findings. |
| `task_ref` | Task or taskset verified. |
| `evidence_path` | JSON, markdown, or log output path. |
| `scope_boundary` | `local_deterministic`, `template_local`, `provider_live`, `remote_ci`, `release`, or `external`. |

## Freshness Block (optional, `agent-runtime-work-verification/v1`)

Verification evidence written to `reviews/VERIFY-*.json` may carry an optional
`freshness` block recorded at verification time so
`scripts/verification_freshness_gate.py` can detect stale evidence
deterministically:

```json
"freshness": {
  "commit_ref": "<git HEAD commit hash when the commands ran>",
  "source_paths": [
    { "path": "scripts/example.py", "sha256": "<sha256 hex of file bytes>" }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `freshness.commit_ref` | Commit checked out when the verification ran. Any commit in `git log <commit_ref>..HEAD -- <source paths>` marks the record stale. |
| `freshness.source_paths[].path` | Repo-relative input the verification depended on (script, test, schema, doc). |
| `freshness.source_paths[].sha256` | SHA-256 of the file bytes at verification time. A mismatch or a missing file marks the record stale. |

Staleness rules consumed by `python scripts/verification_freshness_gate.py --check`:

- A record with a `freshness` block is STALE when any tracked input moved after
  verification: source hash mismatch, missing source file, commits touching the
  tracked paths after `commit_ref`, or the verified work item's `updated_at`
  moving past `verified_at` while the item is still open.
- Stale evidence referenced by an open or closing work item blocks closeout;
  stale evidence on completed or archived items is watch-only.
- Legacy records without a `freshness` block report `freshness-unknown` as a
  watch finding and never block.
- Claim updates after `verified_at` are advisory (watch-only) because claims
  mutate during normal progress reporting.

## Required Closeout Commands

| Scope | Command |
| --- | --- |
| Taskset state | `python scripts/taskset_work_gate.py --task-set-id TASKSET-AR-RSI-OPERATING-SYSTEM --check` |
| Owner docs | `python scripts/owner_doc_format_gate.py --manifest owner-docs.yml` |
| Owner governance | `python scripts/owner_governance_gate.py` |
| Worktree safety | `python scripts/parallel_worktree_gate.py --check` |
| Task identity | `python scripts/task_identity.py check --check` |

## How To Add

1. Run the real command, gate, wrapper, or browser verification flow.
2. Record `record_id`, `source_command`, `source_path`, `cwd`, `exit_code`, `result`, `findings`, `task_ref`, and `scope_boundary`.
3. Keep `local_deterministic` verification separate from `provider_live`, `remote_ci`, `release`, or `external` evidence.
4. Link failed verification to the evidence inbox or casebook before turning it into a proposal.

## Rule

Do not claim completion from an old verification record. A closeout report must
state the command, date, result, and any residual watch items. Future proposal
scoring should consume normalized verification records instead of free-form review scraping.
