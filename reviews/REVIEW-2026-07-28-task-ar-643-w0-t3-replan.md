---
title: TASK-AR-643 W0 T3 Replan
date: 2026-07-28
signal: pass
score: 97
priority: P0
tags: [task-ar-643, w0, t3-replan, dependency-closure, clean-host, profiles]
---

# TASK-AR-643 W0 T3 Replan

## Bottom Line

Proceed with `UNIT-TASK-AR-643-001` as one bounded implementation unit.
The registered defect is still present, but the current gate and smoke suite
cannot see it: the source checkout passes while the installed host advertises
skills and documentation whose executable dependencies are absent.

The unit will introduce one authoritative profile manifest, make sync,
adoption, lock, dependency validation, and wheel smoke consume the same
selection, ship only generic lifecycle helpers, and remove product-specific
release commands from the consumer-facing skill. Bean Wiki, Allimbot,
Autofolio, and Tag Manual remain unmodified.

The baseline is Agent Runtime `main` at `b41fec24`.

## Failure-First Evidence

The recorded focused suite passes despite the defect:

```text
python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_wheel_dotfiles_packaging.py -q
11 passed
```

An actual sync into a temporary fixture host reports `applied=282`, but these
advertised command paths remain absent:

- `scripts/work.py`
- `scripts/session_baseline.py`
- `scripts/dirty_intake.py`
- `scripts/save_report.py`
- `scripts/release_readiness_summary.py`
- `scripts/release_council_gate.py`
- `scripts/release_version_consistency_steward.py`
- `scripts/release_auto_noncritical.py`

The first four are generic work, closeout, and report dependencies that the
consumer template promises. The last four are Agent Runtime release-project
implementation details and must not be copied into every host.

Running the shipped `scripts/runtime_asset_usage.py --check` in that installed
fixture also fails for two independent registry defects:

- `scripts/planning_trigger.py` is registered but absent.
- `skill.taskset_dispatch` points back into
  `src/agent_runtime/templates/project/**`, which does not exist in a host.

The source-side gate passes because it checks the development repository, not
the selected consumer projection.

## Effective Profile Manifest

Add one versioned, packaged manifest for the project template. It is the shared
source of truth for sync, adoption, lock serialization, dependency closure,
and profile-reduction tests.

- `core` remains mandatory.
- `web-content` is additive and starts with no invented product-specific
  files; Bean Wiki supplies its editorial overlay in its pilot.
- `security-service` owns the existing legacy Allimbot helper files until
  TASK-AR-647 replaces them with the native adapter.
- Root-only `scripts/test_*.py` development tests are packaged for source
  verification but are not installed into consumer hosts.
- Core hook configuration must not reference a security-service-only helper.
- Unknown manifest schemas, profiles, patterns, missing files, and
  cross-profile dependency edges fail closed.

V1 configuration still expands to full runtime. V2 selects `core` plus its
declared additive profiles. A selected-template digest and lock record must
cover the same paths sync would install.

## Dependency Closure Contract

Extend the root/template `runtime_asset_usage.py` gate to validate the
consumer projection, not only the development registry:

1. Resolve the selected path set from the profile manifest.
2. Parse every selected `skills/*/SKILL.md` frontmatter dependency.
3. Parse executable `scripts/*.py` and `scripts/*.cmd` references from selected
   skill bodies, declared bootstrap/reporting surfaces, and hook commands.
4. Require each referenced file to exist and belong to the same effective
   profile set.
5. Validate host-relative registry paths and declared root/template mirrors.
6. Report deterministic dependency and selected-file counts for `core`,
   `core+web-content`, `core+security-service`, and full runtime.

The gate must catch a missing physical dependency and a physically present
dependency excluded by the selected profile as distinct blockers.

## Helper Decisions

- Ship an exact consumer mirror of `scripts/work.py` and its already-shipped
  imports.
- Ship generic `session_baseline.py` and `dirty_intake.py` mirrors.
- Add a bounded `save_report.py` helper that writes schema-valid BRIEF/PLAN
  records, updates `reports/INDEX.md`, and refreshes report views.
- Rewrite only the shipped `release-conductor` skill as generic host guidance
  backed by available commands. Keep Agent Runtime's root release skill and
  its product-specific scripts in the development repository.
- Repair the shipped runtime-asset registry to use host-relative paths and
  remove dangling development-only registrations.

Do not copy release decision records, Agent Runtime release scripts, current
task records, reviews, tests, or product roles into core.

## Clean-Host and Wheel Proof

From the exact packaged template, the smoke must:

1. install/sync a clean Git fixture;
2. run `work.py status`;
3. register a minimal initiative/taskset/task/unit with `work.py new`;
4. verify and close the unit and task with real generated evidence;
5. run session baseline and dirty-intake commands;
6. save and index one schema-valid report;
7. run the installed host dependency gate with zero blockers.

The wheel inspection must assert the profile manifest, selected skills,
dotfiles/hooks, `work.py`, session helpers, and `save_report.py` are present.
It must use built-wheel contents rather than only checking `pyproject.toml`
strings.

## Scope Amendment

The registered targets remain primary, with these necessary shared consumers
added:

- `src/agent_runtime/template_profiles.py`
- `src/agent_runtime/sync.py`
- `src/agent_runtime/adoption.py`
- `src/agent_runtime/lock.py`
- the packaged profile manifest, host asset registry, and core hook config
- `scripts/verify_wheel_dotfiles.py`
- focused sync/adoption tests required to prove all consumers select the same
  paths

This is not authorization for automatic merging, deletion of stale host files,
cross-platform continuity redesign, native Allimbot events, compound/scribe
redesign, model routing, pilot mutation, release, tag, push, or publish.

## Verification

- `python -m pytest tests/test_runtime_asset_usage.py tests/test_template_smoke.py tests/test_wheel_dotfiles_packaging.py tests/test_adoption.py tests/test_inventory_sync_sanitize.py -q`
- `python scripts/runtime_asset_usage.py --check`
- `python scripts/verify_wheel_dotfiles.py --check`
- `python -m pytest -q`
- Root/template mirror checks for shared lifecycle and dependency-gate scripts.
- Independent W4b against the exact implementation head.

## W2 Decision

Dispatch one `worker_standard` implementation agent after this review and the
refreshed T3 assumption snapshot are committed. Reserve W4b for a different
agent instance and require an adversarial missing-file, cross-profile,
installed-wheel, and clean-host lifecycle audit before claim release.
