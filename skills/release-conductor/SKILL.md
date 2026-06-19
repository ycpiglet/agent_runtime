---
name: release-conductor
version: 1.0.0
description: Use when the user asks about cutting a release, version bump/cadence, the v0.1.9/v0.2.0 release plan, the council/Owner-gated release flow, or notifying host projects of a new upstream release (배포/version).
triggers:
  - release
  - 배포
  - version
  - cadence
dependencies:
  - scripts/release_cadence_trigger.py
  - scripts/release_readiness_summary.py
  - scripts/release_council_gate.py
registry_id: release-conductor
template_path: src/agent_runtime/templates/project/skills/release-conductor/SKILL.md
---

# Release Conductor

Detect-and-propose is automated; execution is tiered by criticality. The
cadence trigger watches accumulated change since the last tag and proposes a
bump. For a **noncritical** release (no CRITICAL_FLAGS) the **agent release
council** can approve AND execute the tag/push without Owner approval, after the
readiness summary, council vote, and execution gates pass. A **critical /
major_or_breaking / secret / destructive** release halts and requires **explicit
Owner approval** before any tag/push.

## When To Use

- Owner asks "배포 준비", whether it's time to release, a version bump, or to
  execute the v0.1.9 / v0.2.0 plan.
- Session start: surface the non-blocking cadence finding.

## Cadence Trigger (watch-only, never mutates)

```powershell
python scripts/release_cadence_trigger.py --check            # silent below thresholds, exit 0
python scripts/release_cadence_trigger.py --check --verbose  # show metrics anyway
python scripts/release_cadence_trigger.py --json
```

Thresholds: commits>=40, feat>=5, or days>=14 since the latest tag. When
triggered it emits a `release-cadence:proposal` finding with a recommended
bump (minor if templates were deleted/renamed or `schemas/**` changed, else
patch) and target files. It NEVER bumps, tags, pushes, publishes, or releases.

## Version Policy + Cadence (from the v0.1.9/v0.2.0 plan)

- patch (0.1.N): additive template/gate/doc changes (non-breaking).
- minor (0.x+1.0): host-facing schema/contract breaking changes.
- Cadence: cut a patch at a taskset closeout wave (W6) boundary OR every 2
  weeks, whichever comes first.
- v0.1.9 = current main snapshot (excludes the unmerged codex work-schema
  branches). v0.2.0 = after the codex work-schema / registration CLI /
  identity merge lands (host contract change) and a T1/T2 replan.

## Release Flow (execution tier depends on criticality)

1. `python -m pytest tests -q` + `python scripts/owner_governance_gate.py` exit 0.
2. Bump `pyproject.toml`; confirm version refs with
   `python scripts/release_version_consistency_steward.py`.
3. `python scripts/release_readiness_summary.py --out reviews/RELEASE-READINESS-SUMMARY-<date>-vX.Y.Z.json`.
4. Write the readiness review + council vote in
   `agents/project/release/RELEASE-DECISION-vX.Y.Z.yml` -- apply W4b:
   qa/independent-auditor votes come from an instance other than the worker.
5. `release_council_gate.py` -> `release_execution_gate` -> `pending_release_guard` pass.
6. `agent_runtime release-preflight` -> `publish-check` -> `publish-bundle` ->
   `publish-tag-smoke`.
7. Tag + push: **noncritical** (criticality=noncritical, no CRITICAL_FLAGS) ->
   the agent release council approves and executes (no Owner); **critical /
   major_or_breaking / secret / destructive** -> ONLY after explicit Owner
   approval. The cadence-bound `scripts/release_auto_noncritical.py` automates
   the noncritical tier end-to-end on green main; it halts the critical tier
   with `owner-approval-required` and mutates nothing.
8. autofolio: bump `agent_runtime.yml` ref -> `update-plan` -> `update` -> `doctor`.

## Host Update Notify (downstream, non-blocking)

```powershell
agent_runtime update-notify            # one-line notice if a newer upstream tag exists
agent_runtime update-notify --verbose
```

Host projects pin the upstream in `agent_runtime.yml`; `update-notify`
compares the latest upstream release tag against the pinned ref and prints a
hint. Same pattern as release execution: detect automatically, apply
(`update-plan` / `update --apply`) by Owner decision.

## Release Tier Rule (who can execute)

Execution authority depends on criticality, mirroring the code in
`release_council_gate.py` / `release_execution_gate.py`:

- **Noncritical -> agent release council (no Owner).** When criticality is
  `noncritical` and NO CRITICAL_FLAG is set, the agent release council can
  approve and execute the tag/push without Owner approval. `release_council_gate`
  passes only for `criticality: noncritical` with empty `critical_flags`, and
  `release_execution_gate` accepts `owner_approval_status: agent_council_approved`
  as a valid no-Owner execution route. `scripts/release_auto_noncritical.py`
  drives this tier automatically on green main.
- **Critical / major / secret / destructive -> explicit Owner approval.** If
  criticality is `critical`, or ANY CRITICAL_FLAG is set
  (`major_or_breaking_release`, `secret_or_credential_change`,
  `production_data_write`, `billing_or_legal_impact`,
  `failed_or_missing_critical_gate`, `destructive_or_irreversible_operation`,
  `untrusted_external_publication_target`), tag/push/publish are Owner-gated --
  never run them without explicit Owner approval. The orchestrator halts this
  tier with `owner-approval-required` and mutates nothing.
- Council votes are always required and must respect W4b independence
  (qa / independent-auditor / doc-steward votes come from an instance other than
  the worker).
- The cadence trigger and update-notify only detect and propose; they mutate
  nothing.

## W0->W6 Touchpoints

- W0: cadence trigger + update-notify surface release timing at session start.
- W6: the closeout-wave boundary is a cadence checkpoint; run the release flow
  from there when triggered.
