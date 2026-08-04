---
schema_version: agent-runtime-review/v1
id: AUDIT-2026-08-02-task-ar-654-windows-native-evidence-final
task_id: TASK-AR-654
unit_id: UNIT-TASK-AR-654-001
claim_id: CLAIM-20260801-000156-task-ar-654-ar654repair001
review_kind: independent-audit
reviewer: codex-task-ar-654-windows-native-evidence-auditor
reviewer_role: independent-auditor
status: revise
signal: fail
verdict: REVISE
finding_counts: {P0: 0, P1: 1, P2: 1}
candidate_commit: 2f4ec606ad460efd556780c905240b26571c1986
candidate_tree: 5dc072f194adedc024e98eb2259bbc0a1459931f
independence_status: independent
release_authorized: false
created_at: 2026-08-02T14:31:04+09:00
tags: [task-ar-654, independent-audit, windows, junction, scandir, release-evidence, revise]
---

# TASK-AR-654 Windows native-evidence final audit

## Verdict

`REVISE — P0: 0, P1: 1, P2: 1.`

The candidate's Python 3.10-compatible implementation is semantically correct
for the modeled Windows metadata: it retains `lstat()` metadata, recognizes
the `0x20000000` name-surrogate tag bit, rejects mount-point/symlink aliases,
and converts `os.scandir()` open and iteration errors into store-integrity
findings. Release evidence still does not exercise the native platform defect,
and one important regression is environment-dependent.

## P1-1 — Native Windows junction closeout remains unverified

The portable test injects
`st_file_attributes=FILE_ATTRIBUTE_REPARSE_POINT` and
`st_reparse_tag=IO_REPARSE_TAG_MOUNT_POINT`, then calls private
`_active_claims()`. It binds the detector: muting the detector changes the
result from `active-claim-store-integrity-invalid` to an empty clean result.
It does not exercise native Windows `lstat()`, live or broken `mklink /J`
junctions, actual `work close`, bounded output, or closeout non-mutation.

The repository CI matrix currently runs Python 3.10, 3.11, and 3.12 only on
Ubuntu. Because the original defect is platform-representation-specific,
release requires a Windows-only actual-close regression for at least the
broken junction case, safe junction cleanup, and a targeted Windows CI job or
equivalent native artifact. Live junction coverage is also required when it
can be made reliable without destructive cleanup.

## P2-1 — `scandir` regression is not deterministic on every platform

The real permission test is correctly retained as a POSIX integration case,
but it always skips on Windows and skips for users whose directory permissions
are not enforced. Cross-platform unit tests must monkeypatch `os.scandir()` to
raise at open time and during iteration, and require the bounded
`active-claim-store-integrity-invalid` result in both cases. This prevents a
future return to silent `Path.glob()` behavior even where chmod cannot express
the original failure.

## Confirmed implementation properties

- Modeled junction metadata was rejected at all three store components.
- Modeled `scandir` open and iteration failures were bounded.
- Seven focused component tests passed on Python 3.10.
- Source/template bytes, host lock, and template mirror were aligned.
- `Path.is_junction()` is not used, preserving Python 3.10/3.11 support.

## Release decision

Do not treat the modeled Linux-only test as final proof of the Windows defect.
Commit the native conditional regression and targeted CI route, add
deterministic `scandir` failures, then obtain fresh machine and independent
review evidence on the exact repaired candidate.
