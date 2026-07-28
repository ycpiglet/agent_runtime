---
title: TASK-AR-641 UNIT-001 Final Independent W4b Approval
date: 2026-07-28
status: approved
signal: pass
score: 97
verdict: APPROVE
task_id: TASK-AR-641
unit_id: UNIT-TASK-AR-641-001
verified_head: 6dc77d26818cd774494777d8ec3b51628c55b496
verified_by: /root/w4b_task_ar_640_001
verifier_role: independent-verifier
worker_instance: /root/w3_task_ar_640_001
supersedes: reviews/W4B-2026-07-28-unit-task-ar-641-001-final.md
tags: [w4b, independent-verification, adoption, generated-boundary, approved]
---

# TASK-AR-641 UNIT-001 Final Independent W4b Approval

## Verdict

**APPROVE — 97/100.** Exact rebased HEAD
`6dc77d26818cd774494777d8ec3b51628c55b496` resolves the prior six adoption
contract defects and the two generated-boundary blockers. Planning remains
read-only, deterministic for a filesystem snapshot, and has no apply route.

## Independent commands

```text
python -m pytest tests/test_adoption.py tests/test_inventory_sync_sanitize.py \
  tests/test_doctor.py -q
# 120 passed in 8.55s

python -m compileall -q src/agent_runtime
git diff --check
# passed

python -m pytest -q
# 2311 passed, 3 skipped, 4 pre-existing UI escape warnings in 102.17s
```

## Adversarial recheck

All previous blockers now pass independently:

- ignored/generated files no longer leak from public `inventory.analyze()`;
  adoption JSON includes included, ignored, generated, and compact root counts;
- generated members produce no individual actions; explicit generated
  ownership skips, while `CURSOR.md`/`GEMINI.md` root seams preserve;
- external source symlinks and malformed configuration make readiness false and
  fail both CLI and standalone pre-adoption doctor checks;
- plan JSON/text renderers consume the supplied immutable plan without a second
  scan; failure of the second Git ignore query produces the documented
  warning-bearing conservative fallback;
- forced **tracked** `.worktrees`, `.claude/worktrees`, `*.egg-info`,
  `supabase/.branches`, `next-env.d.ts`, and `tsconfig.tsbuildinfo` were all
  generated, never public source. The only source was `src/real.py`; plan was
  `included=1`, `generated=6`, `actions=282`, with correct generated roots;
- template enumeration uses pruned `os.walk`, not template `rglob`.
  `_template_files()` returned exactly 282 cache-independent files and zero
  generated/cache members despite ignored template `__pycache__` files.

Normal `doctor --check` still treats a missing installation as unhealthy,
whereas `doctor --pre-adoption --check` is a separate readiness path and
returns success for an otherwise clean brownfield host.

## Live pilot measurement — read only

Repeated plans were byte-identical. For both pilots, Git status and binary-diff
SHA-256 hashes were identical before and after the probes; no host file was
written.

| Pilot | Included | Ignored | Generated | Actions | Assets | Conflicts | Ready | Public generated leaks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| Bean Wiki | 361 | 40,233 | 40,232 | 282 | 17 | 0 | true | 0 |
| Allimbot | 275 | 34,042 | 34,043 | 282 | 12 | 2 | false | 0 |

Allimbot's two existing template-content conflicts correctly keep that pilot
not-ready; this is planning output, not a runtime installation failure.

## Residual non-blocking watch

The generated-path taxonomy is intentionally explicit. New build systems or
tool-specific cache roots must be added to the shared classifier with a
tracked-artifact regression before relying on the plan for those paths. This
unit still does not authorize apply, template ownership enforcement, sync/lock
mutation, profile manifests, or pilot migration.

No implementation, lifecycle, index, or host file was modified by this
verifier. No commit, push, PR, merge, release, or claim release was performed.
