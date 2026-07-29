---
schema_version: agent-runtime-work-item/v1
work_id: UNIT-TASK-AR-648-012
work_uid: 8d5cad50-c8de-490c-b056-2160951ef47a
kind: unit
parent_id: TASK-AR-648
unit_id: UNIT-TASK-AR-648-012
task_id: TASK-AR-648
task_set_id: TASKSET-AR-V080-ADOPTION-ENFORCEMENT
initiative_id: INIT-AR-V080-ADOPTION-ENFORCEMENT
project_id: PROJECT-AGENT-RUNTIME
status: blocked
verification_status: failed
owner: lead-engineer
created_at: 2026-07-30T03:38:47+09:00
updated_at: 2026-07-30T04:13:03+09:00
started_at: 2026-07-30T03:42:14+09:00
origin_type: pilot_finding
origin_ref: reviews/W4B-2026-07-30-unit-task-ar-648-011.md
created_by: codex-root-v080-planner
summary: Enforce packaged script mirror parity and replace the live-primary immutability oracle with a causal pilot-isolation contract
horizon: unit
model_tier: worker_standard
claim_refs:
  - agents/runtime/task_claims/CLAIM-20260730-034214-task-ar-648-648012.json
escalation_triggers:
  - cross_cutting
  - data_integrity
  - repeated_failure
context: Bean attempt 4 completed its three local traces and passed the repaired adoption, ownership, continuity, Scribe, Compound, and editorial-preservation boundaries, then independently stopped on two P1s. The packaged taskset gate omitted root ISO-second and attention-field masking, and the unit contract treated unrelated concurrent edits in Bean's live primary checkout as if the pilot had caused them. A read-only source/template audit found 84 common Python/CMD assets: 76 byte-identical and 8 divergent. Five divergences are unsynchronized portable fixes; three are intentional source-versus-consumer implementations that currently have no machine-enforced exception contract.
inputs:
  - reviews/PILOT-BEAN-WIKI-v080-GREEN-ATTEMPT-4.md
  - reviews/W4A-2026-07-30-unit-task-ar-648-011.md
  - reviews/W4B-2026-07-30-unit-task-ar-648-011.md
  - agents/project/knowledge/compounds/records/COMPOUND-20260730-033100-packaged-runtime-mirrors-must-preserve-root-wall-465b16b1da25.json
  - scripts/collaboration_concurrency_gate.py
  - scripts/collaboration_governance_gate.py
  - scripts/footprint_conflict_gate.py
  - scripts/now.py
  - scripts/taskset_work_gate.py
  - scripts/compound_record.py
  - scripts/owner_governance_gate.py
  - scripts/stop_hook_owner_governance.py
  - src/agent_runtime/templates/project/scripts
  - tests/test_owner_governance_chain_parity.py
  - tests/test_taskset_work_gate.py
  - tests/test_template_smoke.py
target_files:
  - new:scripts/template_mirror_gate.py
  - new:agents/project/TEMPLATE-MIRROR-CONTRACT.json
  - src/agent_runtime/templates/project/scripts/collaboration_concurrency_gate.py
  - src/agent_runtime/templates/project/scripts/collaboration_governance_gate.py
  - src/agent_runtime/templates/project/scripts/footprint_conflict_gate.py
  - src/agent_runtime/templates/project/scripts/now.py
  - src/agent_runtime/templates/project/scripts/taskset_work_gate.py
  - scripts/owner_governance_gate.py
  - src/agent_runtime/templates/project/scripts/owner_governance_gate.py
  - new:tests/test_template_mirror_gate.py
  - tests/test_owner_governance_chain_parity.py
  - tests/test_taskset_work_gate.py
  - tests/test_template_smoke.py
  - tests/fixtures/host/agent_runtime.lock.json
  - new:scripts/pilot_isolation_gate.py
  - new:tests/test_pilot_isolation_gate.py
  - new:docs/pilot-isolation-contract.md
  - agents/project/RUNTIME-ASSET-REGISTRY.json
  - src/agent_runtime/templates/project/agents/project/RUNTIME-ASSET-REGISTRY.json
  - new:reviews/W4A-2026-07-30-unit-task-ar-648-012.md
  - new:reviews/W4B-2026-07-30-unit-task-ar-648-012.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-template-mirror-isolation-registration.md
  - new:reviews/REVIEW-2026-07-30-task-ar-648-template-mirror-isolation-t3-replan.md
  - agents/lead_engineer/tasks/TASK-AR-648.md
  - agents/lead_engineer/tasks/units/TASK-AR-648/UNIT-TASK-AR-648-012.md
  - agents/project/NEXT-SESSION-POINTER.yml
  - agents/project/work-items/PLAN-ASSUMPTIONS.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.json
  - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
  - BACKLOG-BOARD.md
  - reviews/INDEX.md
scope: Repair only the two P1 boundaries independently confirmed in Bean attempt 4. Add a source-repository mirror gate that compares every common Python/CMD script in root scripts and the packaged project template. Synchronize the five stale portable copies. Permit only three intentional source/consumer divergences through an explicit contract whose reason and both current SHA-256 digests are validated, so an exception cannot hide later drift. Add a reusable pilot-isolation gate that treats disposable targets, frozen controls, and concurrently live observations differently: only the disposable target is an authorized write root; frozen changes or observed writes outside it block; unrelated live-observation drift is recorded as a watch and cannot be presented as pilot-caused without write-surface evidence. Do not mutate Bean, Allimbot, Autofolio, any frozen pilot, or any release surface.
acceptance:
  - The pre-repair audit is reproduced as 84 common eligible assets, 76 identical, and 8 divergent; the five unsynchronized portable scripts are collaboration_concurrency_gate.py, collaboration_governance_gate.py, footprint_conflict_gate.py, now.py, and taskset_work_gate.py.
  - After repair, all common Python/CMD assets are byte-identical except exactly compound_record.py, owner_governance_gate.py, and stop_hook_owner_governance.py.
  - Each intentional divergence has a nonempty bounded reason plus exact source and template SHA-256 digests; a missing side, path traversal, duplicate/stale exception, digest mismatch, newly divergent unlisted asset, or newly identical allowlisted asset blocks.
  - The source Owner-governance chain executes the mirror gate. The consumer chain omits it with a documented source-only reason, and chain-parity tests enforce that omission rather than weakening installed-host governance.
  - The packaged taskset gate masks ISO-second generated_at and wall-clock attention exactly like root; a real packaged-script regression advances the board timestamp across seconds and remains fresh while record-derived drift still blocks.
  - The packaged now.py exposes the API required by packaged work.py; a clean installed-host invocation of python scripts/work.py now returns one timezone-aware ISO-second timestamp.
  - Packaged collaboration concurrency, collaboration governance, and footprint postverify behavior has focused parity coverage and no root-only portable feature loss.
  - The pilot-isolation contract requires one or more disposable targets, disjoint canonical roots, and an observed write set contained by the authorized disposable roots.
  - A frozen-control HEAD, status, or tracked-diff change blocks. A live-observation change with no observed write targeting that root is reported as external/unattributed watch evidence and does not fail the pilot. A live root included in the observed write set blocks.
  - Pilot evidence cannot claim causation from snapshot inequality alone; immutable evidence roots and disposable product/consumer worktrees remain strict.
  - Focused mirror, installed-host, taskset, isolation, adoption, owner-governance, sanitizer, and full Runtime suites pass at one exact product commit before independent W4b.
  - Bean Wiki, Allimbot, Autofolio, prior pilot worktrees, versions, tags, packages, remotes, credentials, and external systems remain untouched.
verification:
  - python scripts/template_mirror_gate.py --check
  - python -m pytest tests/test_template_mirror_gate.py tests/test_owner_governance_chain_parity.py -q
  - python -m pytest tests/test_taskset_work_gate.py tests/test_template_smoke.py tests/test_now.py -q
  - python -m pytest tests/test_collaboration_concurrency_gate.py tests/test_collaboration_governance_gate.py tests/test_footprint_conflict_gate.py tests/test_footprint_postverify.py -q
  - python -m pytest tests/test_pilot_isolation_gate.py tests/test_pilot_acceptance.py -q
  - python -m pytest tests/test_adoption.py tests/test_config_v2.py tests/test_inventory_sync_sanitize.py tests/test_owner_governance_consumer_host.py -q
  - python scripts/runtime_asset_usage.py --check
  - python scripts/owner_governance_gate.py
  - PYTHONPATH=src python -m agent_runtime.cli sanitize --root . --check
  - python -m pytest -q
handoff: Return the exact rejected and repaired product commits and trees, the before/after mirror census, every intentional-divergence reason and pinned digest, packaged taskset ISO-time proof, clean installed work.py now proof, portable feature parity proof, pilot-isolation decision matrix, Bean/Allimbot/Autofolio no-touch snapshots, complete verification counts, W4a, and fresh independent W4b.
stop_condition: Stop on any broad copy that erases an intentional source/consumer boundary, unpinned or wildcard mirror exception, consumer-side skip of a portable gate, taskset freshness weakening, pilot isolation fail-open, live-primary drift presented as causal without write-surface evidence, Bean/Allimbot/Autofolio mutation, unsupported provider/model/cost claim, release, version bump, tag, package, push, publish, deploy, credential access, or network delivery.
---

# UNIT-TASK-AR-648-012 - Packaged Mirror Parity and Causal Pilot Isolation

## Context

Attempt 4 proved that individual root regressions are insufficient when the
packaged template silently retains older code. It also proved that a live
owner checkout cannot serve as a global immutable oracle while unrelated work
continues. Both defects must be repaired in Runtime before another consumer
replay.

## Inputs

- Attempt-4 pilot, W4a, independent W4b, and Compound evidence
- Root and packaged common-script inventories
- Existing owner-chain parity and clean-host smoke tests
- The exact rejected Runtime product
  `dd279cd5613578c87ed6c4c24b37325084449d82`
- Frozen Bean attempt 4 and all earlier pilot evidence, read-only

## Target Files

- A root-only, fail-closed template-mirror gate and digest-pinned contract
- Five stale packaged portable scripts
- Root/template Owner-governance wiring and parity tests
- Packaged taskset and installed-work regressions
- A reusable pilot-isolation gate, tests, and contract documentation
- W4a, independent W4b, and lifecycle projections

## Scope

Close the exact two P1s without changing a consumer repository. The mirror
contract covers the whole common Python/CMD script intersection, not a
hand-maintained list of only today's five failures. The isolation contract
separates authorized disposable targets, immutable frozen controls, and
concurrently live observations.

## Steps

1. Reproduce the 84/76/8 census and add RED mirror, packaged-timestamp,
   packaged-work-now, and isolation tests.
2. Implement digest-pinned mirror exceptions and synchronize the five portable
   scripts.
3. Wire mirror enforcement only into the Runtime source Owner gate and
   document the consumer omission.
4. Implement the pilot-isolation decision matrix and fail-closed evidence
   validation.
5. Run focused, installed-host, governance, sanitizer, and full verification
   on one exact product, then obtain fresh independent W4b.

## Acceptance Criteria

- Common portable scripts cannot drift silently again.
- Intentional source/consumer variants cannot change behind a stale allowlist.
- Packaged taskset freshness and `work.py now` reproduce root behavior.
- Frozen and disposable pilot boundaries stay strict while unrelated
  live-primary drift is recorded without false causation.
- No consumer or release surface changes before exact-product approval.

## Verification

- Mirror and owner-chain parity tests
- Packaged taskset, timestamp, collaboration, and footprint regressions
- Pilot-isolation and existing pilot-acceptance tests
- Clean-host adoption and Owner-governance tests
- Runtime asset, sanitizer, Owner-governance, and full test suites

## Handoff

Report exact product provenance, mirror census and exception hashes, installed
regressions, isolation matrix, no-touch evidence, all verification counts, W4a,
and independent W4b.

## Stop Boundary

Do not edit Bean, Allimbot, Autofolio, any frozen pilot, or any release/version
surface. Stop on an unbounded exception or a weakened consumer guard.

## Independent W4b Result

Exact product `f49ff61bb7dcac7466ae76b6cfc775864d1a83ab` is blocked with
P0 0, P1 1, and P2 1. The gate compares only the source/template intersection,
so deleting an eligible portable script from either side removes it from the
checked surface and returns zero findings. See
`reviews/W4B-2026-07-30-unit-task-ar-648-012.md`.

Freeze this product. Repair the missing-side inventory boundary in a separate
unit before any Bean attempt 5 or Allimbot work.
