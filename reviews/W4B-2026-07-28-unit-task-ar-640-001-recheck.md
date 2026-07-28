---
title: TASK-AR-640 UNIT-001 Independent W4b Recheck
date: 2026-07-28
status: approved
signal: pass
score: 97
verdict: APPROVE
task_id: TASK-AR-640
unit_id: UNIT-TASK-AR-640-001
verified_head: ebf56c5abe3ed30243661fae66b7ff9df182b003
verified_by: /root/w4b_task_ar_640_001
verifier_role: independent-verifier
worker_instance: le-20260728-194821-kst-640001
supersedes: reviews/W4B-2026-07-28-unit-task-ar-640-001.md
tags: [w4b, independent-verification, config-v2, doctor-json, recheck]
---

# TASK-AR-640 UNIT-001 Independent W4b Recheck

## Verdict

**APPROVE — 97/100.** Exact HEAD
`ebf56c5abe3ed30243661fae66b7ff9df182b003` resolves every blocker in the
earlier independent review. The implementation remains diagnostic-only: this
verification observed no sync, lock, template, real-host, PR, merge, release,
or claim-release mutation.

## Evidence reviewed

Reviewed worker W4a evidence
`reviews/VERIFY-2026-07-28-unit-task-ar-640-001-20260728202444.json`:

- focused suite: 147 passed in 10.03s;
- full suite: 2,300 passed, 3 skipped, 4 pre-existing UI escape warnings;
- compileall: passed;
- worker identity: `le-20260728-194821-kst-640001`, distinct from this W4b
  verifier.

## Independent commands

```text
python -m pytest tests/test_config_v2.py tests/test_doctor.py \
  tests/test_host_context_read_location.py tests/test_inventory_sync_sanitize.py \
  tests/test_project_context_overlay.py -q
# 147 passed in 8.61s

python -m pytest -q
# 2300 passed, 3 skipped, 4 warnings in 103.59s
```

`git status --short` was clean before this report; all adversarial fixtures
were temporary directories outside the worktree.

## Reproduced former blockers

| Earlier blocker | Independent recheck | Result |
| --- | --- | --- |
| v1 backslash compatibility | `agents\\host\\NOTES.md` projects as `agents/host/NOTES.md` in both `unmanaged_paths` and effective `host_owned` | pass |
| v2 typo / malformed input | unknown root, sync, upstream, host, and ownership keys all raise; fully indented top-level documents raise | pass |
| unsafe path / namespace bypass | absolute, drive-qualified, backslash, dot, traversal, `.git`, config/lock, empty component, and exact/child `agents/host` under managed/seed-once/generated all raise | pass |
| host-context scalar coercion | mapping `purpose`, list `domain`, and nested `role_mapping` values all raise rather than stringifying | pass |
| doctor source path portability | valid, invalid, missing, and legacy projection use root-relative POSIX paths (`agent_runtime.yml` or `ralph.yml`) | pass |

## Additional parser and projection probes

- Unquoted apostrophe plus whitespace comment preserves `world's coffee`.
- Quoted `#` remains literal; a whitespace-delimited trailing comment is
  accepted.
- Tight quoted tail (`"x"#tight`), tail junk (`"x" tail`), and an unclosed
  quote all fail closed.
- v2 defaults to `core`; `full-runtime` expands to the complete registered
  order; reversed requested profiles and additive capability selection project
  deterministically in registry order.
- Mixed-mode ownership ancestor/descendant overlap blocks.
- On a fully prepared temporary host, `doctor --json --check` returned 0;
  two independent calls were byte-identical and findings were sorted;
  `doctor --repair --json --check` returned a single JSON document containing
  `repair_actions` and returned 0.

## Residual risk

The intentionally bounded parser is not a general YAML implementation: it
does not support YAML escape semantics or arbitrary compound values. That is
the documented v0.8 contract, and unsupported shapes visibly block rather than
being silently reinterpreted. V1 `sync.unmanaged` retains its established
backslash-to-POSIX normalization; legacy entries outside the documented safe
relative-path set now fail closed when projected into ownership, so such hosts
should normalize those entries before adopting v2 diagnostics.

## Approval scope

This approval covers only `UNIT-TASK-AR-640-001` at the exact HEAD above. It
does not approve later sync/lock enforcement, profile manifests, scribe adapter
execution, security enforcement, product migration, or release publication.
