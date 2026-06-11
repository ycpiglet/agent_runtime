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
