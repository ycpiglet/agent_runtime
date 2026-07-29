---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-013
work_uid: b55e1994-e8e0-4149-94ed-d6908e486d23
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-013
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: in_progress
verification_status: pending
owner: lead-engineer
created_at: 2026-07-30T04:19:04+09:00
updated_at: 2026-07-30T04:22:40+09:00
started_at: 2026-07-30T04:22:40+09:00
origin_type: pilot_finding
origin_ref: reviews/W4B-2026-07-30-unit-task-ar-648-012.md
created_by: codex-root-v080-planner
summary: Pin the exact expected common script inventory so source or packaged-side deletion cannot disappear from mirror enforcement
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-042240-task-ar-648-961f.json
escalation_triggers:
  - cross_cutting
  - data_integrity
  - repeated_failure
context: Independent W4b blocked exact product f49ff61bb7dcac7466ae76b6cfc775864d1a83ab because template_mirror_gate.py derives its governed surface from the current source/template intersection. An eligible script missing from either side therefore disappears from the comparison and returns zero findings. The current product has 84 expected common Python/CMD paths, of which 81 are identical and 3 are intentional digest-pinned variants. Existing legitimate root-only and template-only populations must remain allowed.
inputs:
  - reviews/W4A-2026-07-30-unit-task-ar-648-012.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-012.md
  - scripts/template_mirror_gate.py
  - agents/project/TEMPLATE-MIRROR-CONTRACT.json
  - tests/test_template_mirror_gate.py
  - scripts/owner_governance_gate.py
  - tests/test_owner_governance_chain_parity.py
target_files:
  - scripts/template_mirror_gate.py
  - agents/project/TEMPLATE-MIRROR-CONTRACT.json
  - tests/test_template_mirror_gate.py
  - new:agents/project/knowledge/compounds/records/COMPOUND-*.json
  - agents/project/knowledge/compounds/INDEX.json
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-013.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-013.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-mirror-expected-inventory-registration.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-mirror-expected-inventory-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-013.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: Repair only UNIT-012's missing-side blind spot. Evolve the mirror contract to carry a unique, safe, sorted, exact expected-common list for all 84 currently portable Python/CMD paths. Block when an expected path is missing from source, missing from the packaged template, or when a new actual common path is absent from the reviewed inventory. Preserve existing root-only and template-only assets outside the expected-common list. Keep the three intentional divergences digest-pinned and subordinate to the expected inventory. Do not modify pilot isolation, portable script bodies, consumers, or release surfaces.
acceptance:
  - The contract contains exactly the 84 current common eligible paths as explicit entries, not a count, wildcard, directory prefix, or dynamically derived baseline.
  - Every expected path is a unique safe relative Python/CMD path; duplicate, path-traversal, wrong-type, malformed, or unsorted inventory data blocks.
  - An expected path missing from source blocks with a stable source-missing finding, and an expected path missing from the packaged template blocks with a stable template-missing finding.
  - Deleting either side of a formerly common path blocks even though the path no longer belongs to the current intersection.
  - A newly common eligible path that is not in the reviewed inventory blocks and requires a contract update.
  - Existing legitimate root-only and template-only eligible assets outside the expected inventory remain allowed.
  - Intentional divergence entries must be members of the expected inventory and continue to require bounded reasons plus exact source and template SHA-256 digests.
  - The exact product reports 84 expected, 84 current common, 81 identical, 3 intentional, and zero findings.
  - RED coverage proves both missing-side cases, formerly-common deletion, unexpected-common addition, invalid inventory data, and legitimate one-sided populations before implementation.
  - Focused mirror and Owner-chain tests, source Owner governance, sanitizer, and the complete Runtime suite pass at one exact product before a fresh independent W4b.
  - Bean Wiki, Allimbot, Autofolio, all prior pilot worktrees, versions, tags, packages, remotes, credentials, and external systems remain untouched.
verification:
  - python -m pytest tests/test_template_mirror_gate.py -q
  - python scripts/template_mirror_gate.py --check --json
  - python -m pytest tests/test_template_mirror_gate.py tests/test_owner_governance_chain_parity.py -q
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Return the rejected and repaired exact commits and trees, the explicit expected-common count and census, every stable RED finding, proof that legitimate one-sided assets remain allowed, the Compound record, complete verification counts, no-touch consumer snapshots, W4a, and fresh independent W4b.
stop_condition: Stop on a dynamically derived expected baseline, count-only assertion, wildcard or directory exception, blocking of known legitimate one-sided populations, weakening of the three digest pins, any pilot-isolation or unrelated portable-script change, Bean/Allimbot/Autofolio mutation, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-013 - Expected Common Mirror Inventory Enforcement

## Context

UNIT-012 correctly detects drift only while both files remain present. Its
independent W4b demonstrated that deletion from either side removes the path
from the current intersection and therefore from governance. The expected
portable surface needs an independent, reviewed identity.

## Inputs

- UNIT-012 exact product and W4a/W4b evidence
- The current 84-path root/template common inventory
- The existing three digest-pinned intentional variants
- Source Owner-governance mirror-gate wiring

## Target Files

- Mirror contract, gate, and focused tests
- One task-linked Compound record
- Unit lifecycle, verification, and review evidence

## Scope

Add an exact expected-common inventory to the contract and validate both the
inventory itself and the actual source/template trees against it. Do not turn
all one-sided Runtime scripts into portable assets: only paths explicitly
listed as expected common are governed as two-sided.

## Steps

1. Commit RED cases for source missing, template missing, formerly-common
   deletion, unexpected common addition, invalid inventory entries, and
   legitimate one-sided assets.
2. Record the intersection-derived fail-open cause in Compound.
3. Evolve the contract and gate to enforce an independently pinned 84-path
   inventory.
4. Run focused and complete verification on one exact product.
5. Obtain a fresh independent W4b before creating Bean attempt 5.

## Acceptance Criteria

- A previously portable asset cannot disappear silently from either side.
- A new common asset cannot enter governance without a reviewed contract
  update.
- Existing intentional variants retain exact digest pins.
- Existing intentional one-sided populations are unaffected.
- No consumer or release surface is touched.

## Verification

- Focused mirror and source/template Owner-chain tests
- Source Owner-governance chain
- Runtime sanitizer and complete test suite
- Exact-product W4a and independent W4b

## Handoff

Report exact provenance, the 84-path contract census, negative finding codes,
one-sided compatibility, Compound evidence, full verification, no-touch
snapshots, and both review stages.

## Stop Boundary

Do not infer the baseline from the trees being checked. Do not modify Bean,
Allimbot, Autofolio, prior attempts, pilot isolation, releases, or remotes.
