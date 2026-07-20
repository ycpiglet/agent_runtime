---
schema_version: agent-runtime-work-item/v1
work_id: INIT-AR-HOOK-PORTABILITY-CLEANUP
work_uid: b066a694-4417-4197-8d78-2a0f3f50dd1e
kind: initiative
id: INIT-AR-HOOK-PORTABILITY-CLEANUP
status: completed
owner: lead_engineer
created_at: 2026-07-20T12:56:05+09:00
updated_at: 2026-07-20T13:24:53+09:00
completed_at: 2026-07-20T13:24:53+09:00
resolution: done
closed_by: codex-root
verification_status: passed
verified_at: 2026-07-20T13:24:35+09:00
verified_by: codex-root
evidence_refs:
  - reviews/VERIFY-2026-07-20-task-ar-601-20260720132429.json
  - reviews/W4B-2026-07-20-TASK-AR-601.md
origin_type: owner_request
origin_ref: reviews/REVIEW-2026-07-20-hook-portability-and-worktree-cleanup.md
created_by: codex-root
summary: Make Codex and Git hooks executable on Linux and leave the checkout synchronized and clean.
---

# Hook portability and checkout hygiene

## Goal

- Make Codex and Git hooks executable on Linux and leave the checkout synchronized and clean.

## Closeout

- `TASK-AR-601` and `UNIT-TASK-AR-601-001` completed with W4a and independent W4b evidence.
- Portable Codex hook commands, executable Git hook modes, bootstrap wiring, serial merge-queue integration, and worktree/branch cleanup are complete.
- Evidence: `reviews/VERIFY-2026-07-20-task-ar-601-20260720132429.json`, `reviews/W4B-2026-07-20-TASK-AR-601.md`, and `reviews/RETRO-2026-07-20-hook-portability-cleanup.md`.
