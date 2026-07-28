---
title: TASK-AR-641 UNIT-001 Final Independent W4b
date: 2026-07-28
status: changes_required
signal: fail
score: 68
verdict: CHANGES_REQUIRED
task_id: TASK-AR-641
unit_id: UNIT-TASK-AR-641-001
verified_head: 0cf91bf31f457f73e766104fd77ad5b63df32ea7
verified_by: /root/w4b_task_ar_640_001
verifier_role: independent-verifier
worker_instance: /root/w3_task_ar_640_001
supersedes: reviews/W4B-2026-07-28-unit-task-ar-641-001.md
tags: [w4b, independent-verification, adoption, generated-boundary, brownfield]
---

# TASK-AR-641 UNIT-001 Final Independent W4b

## Verdict

**CHANGES_REQUIRED — 68/100.** Exact HEAD
`0cf91bf31f457f73e766104fd77ad5b63df32ea7` fixes the six prior W4b blockers,
but two generated-boundary defects remain. They make the supposedly
read-only/deterministic adoption plan depend on tracked worktree metadata and
the local package's Python cache state. Do not release or pilot this unit yet.

## Independent commands

```text
python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py \
  tests/test_doctor.py -q
# 118 passed in 8.44s

python -m compileall -q src/agent_runtime
git diff --check
# passed

python -m pytest -q
# 2309 passed, 3 skipped, 4 pre-existing UI escape warnings in 102.46s
```

Normal doctor regression remains covered by the focused doctor tests. All
adversarial host fixtures and live-pilot probes were read-only.

## Prior six blockers: recheck passed

- Public inventory now uses the Git-aware adoption scan: ignored and ordinary
  generated paths do not appear in `analyze()` output.
- JSON carries `included_count`, `ignored_count`, generated count/root summary;
  generated members no longer become individual actions.
- Explicit generated `AGENTS.md` is a generated `skip`; existing `CURSOR.md`
  and `GEMINI.md` are `seed_once` preserves.
- An arbitrary external source symlink is a finding, makes readiness false,
  and makes CLI pre-adoption doctor return 1.
- A malformed present config sets `config_invalid`, makes readiness false, and
  makes standalone `python -m agent_runtime.doctor --pre-adoption --check`
  return 1.
- Renderers consume the immutable plan without calling `adoption_scan()`; a
  failed second Git ignore query produces the warning-bearing
  `filesystem-conservative` fallback.

## Remaining blockers

### 1. Tracked well-known generated artifacts are classified as source

The Git candidate path is filtered only by `GENERATED_DIRS`, which omits
`.worktrees`, `worktrees`, `*.egg-info`, and `supabase/.branches`
([inventory.py](/home/keti-itp-01/ycpiglet/agent_runtime/.worktrees/TASK-AR-641/src/agent_runtime/inventory.py:18)).

In an isolated committed Git fixture, all four of the following appeared in
public `inventory.analyze()` and in adoption `source_paths`, with
`included=5`, `generated=0`:

```text
.worktrees/task/file.py
.claude/worktrees/task/file.py
src/pkg.egg-info/PKG-INFO
supabase/.branches/a/db
```

This is not an ignored-file edge case: every artifact was tracked deliberately.
W0 requires well-known generated/worktree paths to remain outside source and
action evaluation even when tracked. Add explicit component/pattern rules,
share them across public inventory and adoption, and add the tracked fixture
above to the test matrix.

### 2. Template enumeration proposes local `__pycache__` files as managed

`_template_files()` performs an unconditional `root.rglob("*")` and excludes
only `.git`
([adoption.py](/home/keti-itp-01/ycpiglet/agent_runtime/.worktrees/TASK-AR-641/src/agent_runtime/adoption.py:53)).
After normal test/compile activity, the packaged template contains **186**
`scripts/__pycache__/*.pyc` files. The current adoption plan proposes them as
`managed add`/`managed conflict` actions, for example:

```text
scripts/__pycache__/agent_console.cpython-310.pyc -> add / managed
scripts/__pycache__/agent_live_session.cpython-310.pyc -> conflict / managed
```

That inflates live plans to 468 actions and makes results depend on local test
cache state, despite being byte-stable for one frozen snapshot. Generated
paths must never enter template action enumeration. Filter `_template_files()`
through the shared generated predicate (or an explicit package manifest),
remove cache artifacts from the package tree, and add a cache-state invariance
test. This also satisfies the required removal of unconditional adoption
template walking.

## Live pilots — read-only independent measurement

Both probes used repeated `build_adoption_plan()` calls only. Git status and
binary-diff SHA-256 hashes were identical before and after each probe.

| Pilot | Included | Ignored | Generated | Actions | Assets | Conflicts | Ready |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Bean Wiki | 361 | 40,233 | 40,229 | 468 | 17 | 0 | true |
| Allimbot | 276 | 34,042 | 34,033 | 468 | 12 | 2 | false |

Public inventory generated-like leaks were zero for both pilots, and repeated
plan JSON was byte-identical. These positive measurements do not mitigate the
two tracked/template generated-boundary gaps above.

## Required rework

1. Extend the shared generated classifier to include worktree directories,
   egg-info pattern paths, and `supabase/.branches`, and test them as tracked.
2. Exclude every generated/cache artifact from template enumeration and remove
   unconditional template `rglob`; prove action output is unchanged before and
   after creating Python caches.
3. Rerun W4a and request a fresh W4b only after both failure-first cases pass.

No implementation, lifecycle, index, or host file was modified by this
verifier. No commit, push, PR, merge, release, or claim release was performed.
