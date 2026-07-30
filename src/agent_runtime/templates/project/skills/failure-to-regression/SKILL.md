---
name: failure-to-regression
description: Convert a repeated failure, defect signature, review finding, or Owner correction into a current-work Compound record with a durable regression, gate, task proposal, or accepted watch. Use whenever work declares repeated_failure, carries defect_signatures, or must prevent the same mistake from recurring.
---

# Failure to Regression

Work from the repository root. Preserve Compound history as append-only.

## Required workflow

1. Normalize a stable, non-secret defect signature:

   ```bash
   python scripts/compound_record.py --root . signature "short stable failure description"
   ```

2. Search before acting or claiming work:

   ```bash
   python scripts/compound_record.py --root . search \
     --work-id WORK_ID \
     --signature "short stable failure description" \
     --json
   ```

   Treat matches as prior knowledge, not as a current-work closure record.

3. Choose at least one durable prevention destination:

   - a file under `tests/`, or a repository test script under `scripts` whose
     filename starts with `test_`;
   - an executable `*_gate.py`;
   - a task or unit spec under `agents/lead_engineer/tasks/`;
   - an accepted-watch review under `reviews/`.

   Every declared prevention ref must be repository-relative, remain inside the
   repository after symlink resolution, and already exist. Supplementary docs
   are allowed only when at least one supported destination is present.

4. For an accepted watch, record all of:

   ```yaml
   status: accepted
   decision: accepted_watch
   reviewed_by: REVIEWER_ID
   work_id: CURRENT_WORK_ID
   ```

   `approved` is also valid for `status`. The reviewer must be explicit, and
   the review must link the current task or unit.

5. Create a new canonical Compound linked to the current work:

   ```bash
   python scripts/compound_record.py --root . create \
     --work-id WORK_ID \
     --signature "short stable failure description" \
     --title "Prevent the repeated failure" \
     --summary "What recurred and why it matters." \
     --cause "The bounded root cause." \
     --prevention "How the destination prevents recurrence." \
     --source-ref reviews/SOURCE.md \
     --prevention-ref tests/regressions/test_failure.py \
     --verification-ref reviews/VERIFY-WORK.json \
     --created-by AGENT_INSTANCE_ID
   ```

6. Link the returned record when closing work:

   ```bash
   python scripts/work.py close WORK_ID \
     --compound-ref agents/project/knowledge/compounds/records/COMPOUND-ID.json \
     --defect-signature "short stable failure description" \
     --actual-hours HOURS \
     --actual-tokens TOKENS
   ```

7. Validate the store and the work-linked Stop gate:

   ```bash
   python scripts/compound_record.py --root . check
   python scripts/closure_gate.py --root . --work-id WORK_ID --check
   ```

## Boundaries

- Do not rewrite, delete, or silently repair legacy Compound history.
- Do not satisfy current work with a signature-only match from another task.
- Never place secrets, credentials, private payloads, or absolute paths in a
  signature or record.
- For Owner-only, external, destructive, release/version, production-data, or
  cost-bearing actions, create the prevention task proposal and stop before
  executing the action.
