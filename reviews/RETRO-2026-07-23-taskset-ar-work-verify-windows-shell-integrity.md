---
status: complete
origin_type: taskset_closeout
origin_ref: reviews/REVIEW-2026-07-23-task-ar-621-verification-command-contract.md
tags:
  - retrospective
  - work-cli
  - windows
  - verification
  - taskset-closeout
---

# TASKSET-AR-WORK-VERIFY-WINDOWS-SHELL-INTEGRITY Retrospective

## Outcome

The one-task taskset is complete. Registered verification commands retain
literal shell metacharacters on Windows without breaking the native parsing
behavior already used by legacy task metadata.

## What Worked

- Failure-first coverage exercised the complete `work.py verify` boundary and
  made the caret corruption observable in persisted evidence.
- The first independent approval did not end review: the skeptic inspected real
  registered commands and found a compatibility blocker before merge.
- Replanning at the execution boundary produced a smaller contract than a
  cross-platform lexer: direct Windows process creation plus unchanged POSIX
  behavior.
- The final PR and post-merge matrices validated the exact integration on all
  three supported Python versions.

## Friction and Corrections

- Tokenizing commands with a portable lexer appeared safer but changed terminal
  quote behavior used by a real worker-ready task. The implementation was
  replaced rather than patched around individual strings.
- Releasing the worker claim before integration left W5 without an active owner.
  A bounded integration-only claim restored claim-first accountability and was
  released after main CI passed.
- The derived board became stale when task metadata was closed. Regenerating
  derived records before the final task-level W4a restored the canonical state.

## Durable Rules

1. Cross-platform command execution must be tested against real registered
   command shapes, not only synthetic tokens.
2. On Windows, an implicit `cmd.exe` boundary is a data-integrity decision;
   shell semantics must be explicit in the registered command.
3. Independent review remains open until all skeptical compatibility findings
   are resolved against a fresh exact head.
4. W5 integration must retain a live bounded owner until post-merge main CI is
   complete.

## Evidence

- `reviews/VERIFY-2026-07-23-task-ar-621-20260723161245.json`
- `reviews/W4B-2026-07-23-TASK-AR-621-RECHECK.md`
- `reviews/ROLE-REVIEW-2026-07-23-TASK-AR-621-SKEPTIC-RECHECK.md`
- `reviews/W4B-2026-07-23-TASK-AR-621-RELEASE.md`
- PR #344; pull-request run `29988050884`; post-merge run `29988207028`
