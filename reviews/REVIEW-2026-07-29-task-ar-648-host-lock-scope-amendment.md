---
type: planning
title: TASK-AR-648 host lock scope amendment
date: 2026-07-29
task_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-002
signal: pass
score: 99
priority: P0
tags: [planning-record, task-ar-648, scope-amendment, host-lock]
---

# TASK-AR-648 host lock scope amendment

## Bottom Line

The five focused P0 regressions and the three required focused suites passed.
The first full-suite run then correctly reported that changing the default
ownership of `owner-docs.yml` requires regenerating
`tests/fixtures/host/agent_runtime.lock.json`. The registered unit and active
claim omitted that deterministic artifact. No lock fixture edit occurred
before this amendment.

After regeneration, two hermetic stale-lock tests exposed the corresponding
fixture defect: the installed-host fixture carried seed evidence in its lock
but did not contain the canonical `owner-docs.yml` seed. Once their temporary
copies intentionally discarded the old lock, that missing host file became
observable. No fixture seed edit occurred before adding it to this amendment.

## Decision

- Add `tests/fixtures/host/agent_runtime.lock.json` to the
  `UNIT-TASK-AR-648-002` and active claim footprints.
- Add the canonical `tests/fixtures/host/owner-docs.yml` seed so the fixture
  represents a self-contained installed host and remains reproducible after
  its lock is deliberately discarded.
- Add `tests/test_lock_merge_driver.py` so its stale-lock recovery copies the
  complete fixture host instead of reconstructing only its configuration.
- Re-record T0/T3 assumptions with this amendment and the lock fixture as
  anchors before regenerating the lock.
- Limit the lock diff to the mechanically derived `owner-docs.yml` ownership,
  managed-file, and seeded-state changes; the four repaired packaged-script
  digests; and the resulting aggregate template digest.
- Keep the Bean replay, external-effect stop boundary, P1 deferrals, and all
  other implementation scope unchanged.

## Evidence

- Focused dispatch/registration/claim/classifier/state suite: `196 passed`.
- Adoption/config/sync suite: `171 passed`.
- Template/pilot-validator suite: `23 passed`.
- Full suite stopped at
  `tests/test_lock_merge_driver.py::test_regenerate_noop_when_current`, where
  the committed fixture differed from `build_lock_plan(...).record`.
- After completing the fixture amendment: `2577 passed, 3 skipped`.
