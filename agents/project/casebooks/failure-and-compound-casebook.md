# Failure and Compound Casebook

## Purpose

This casebook is the query surface for repeated failures and compound issues.
It does not replace `agents/lead_engineer/compound_log.md`; it indexes entries
into a form the proposal engine can use.

## Seed Cases

| Case | Dedupe Key | Sources | Prevention Status | Next Route |
| --- | --- | --- | --- | --- |
| BRIEF output drift | `brief-format-drift` | `COMPOUND-2026-06-09-001`, `COMPOUND-2026-06-10-002` | gate | keep response-contract and owner-doc gates current |
| Continuity pointer gap | `continuity-pointer-gap` | `COMPOUND-2026-06-10-003` | gate | keep `NEXT-SESSION-POINTER.yml` in taskset handoffs |
| Taskset completion inferred from claims | `taskset-completion-claim-only` | `COMPOUND-2026-06-10-004` | gate | use named taskset gate before completion claims |
| RSI operating evidence scattered | `rsi-evidence-scattered` | `REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration` | verified | `TASKSET-AR-RSI-OPERATING-SYSTEM` closeout |
| Low-frequency self-improvement debt | `self-improvement-low-frequency-debt` | `reviews/REVIEW-2026-06-17-self-improvement-cycle.md`, `COMPOUND-2026-06-17-001` | watch | route dormant roles and low-reuse assets into the next cycle |
| Release perpetual-skip (no tag despite backlog) | `release-perpetual-skip` | `COMPOUND-2026-06-22-001`, PR #183 | gate+fixture | metric (`workflow_run`) trigger + green-SHA checkout shipped; keep workflow-wiring test |
| Release version-cascade incomplete | `release-version-cascade` | `COMPOUND-2026-06-22-001`, PR #184 | tooling | `scripts/release_version_cascade.py --check/--write` (shipped) bumps+verifies all 12 current-tag refs in one pass |
| Template change leaves stale host lock | `template-stale-host-lock` | `COMPOUND-2026-06-22-001`, PR #183, PR #256 | gate+hook | `test_lock_merge_driver` catches; pre-commit auto-regen SHIPPED (PR #256: staged templates → lock regenerated + staged before the commit exists) |
| Green pipeline, missing product (cross-step file contract untested) | `silent-cross-step-wiring` | `COMPOUND-2026-07-04`, PR #240, issue #241 | gate+fixture | mkdir-before-tee + loud missing-artifact failure + workflow contract test shipped; apply the same pattern to any step-to-step file handoff |
| Open issues/board drift from merged reality | `stale-open-state-debt` | `COMPOUND-2026-07-04`, PR #239/#242 + sweep PR #249/#251/#257/#259/#260 | tooling+scheduled | open_state_sweep v1.3 SHIPPED: stale issues, dangling lanes, merged-branch debris, untriaged stashes (ledger `agents/project/archive-stash-triage.json`); weekly workflow surfaces findings as a dedup'd issue |
| Shared-checkout ref race (concurrent agents) | `shared-checkout-ref-race` | `COMPOUND-2026-06-22-001` | proposal | verify live tip before destructive ref ops; no cleanup during concurrency |
| Non-hermetic test mutates tracked files | `nonhermetic-test-tracked-mutation` | `COMPOUND-2026-06-22-001`, PR #258 | partial | fixture-lock freshness assert is now read-only (PR #258; the old form rewrote the tracked fixture exactly when failing); board/archive hermeticity + explicit pathspec on release commits remain open |
| CI flaky temp-git gate tests | `ci-flaky-temp-git` | `COMPOUND-2026-06-22-001`, `COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction`, PR #252/#254, run 30350865552 | needs enforcement | recurrence 3+; TASK-AR-651 must harden or remove the remaining release-critical temp-git boundary |
| Query failure classified as "no data" in a decision path | `silent-query-error-as-no-data` | `COMPOUND-2026-07-04`, PR #254/#255, CI run 28680340240 | gate+fixture | trigger records git query errors; `git-query-error` → `trigger-error` (exit 5) fails the run red instead of a quiet `not-triggered`; contract tests pin both layers |
| Consumer-project path assumption | `consumer-project-path-assumption` | issue #185, PR #187 | gate+fixture | gates resolve root-OR-template; v0.3.1 shipped |
| Work concentrates on lead-engineer | `role-concentration` | `REVIEW-2026-06-22-system-health-rsi-diagnosis`, self_improvement_cycle assess | tooling+proposal | `role_concentration_gate` flags it (advisory); dispatch rebalance to dormant review/skeptic/scout roles is an Owner-tier proposal |
| Lessons reviewed but rarely compounded | `compound-under-cadence` | `REVIEW-2026-06-22-system-health-rsi-diagnosis` | tooling+proposal | `compound_cadence_gate` flags review≫compound; make compound a per-N-reviews cadence obligation (proposal) |
| A2A built but not wired into live dispatch | `a2a-dormant-not-wired` | `REVIEW-2026-06-22-subsystem-verification-audit` | proposal | router complete + tested, 0 runtime traffic; wire emit_message into claim/handoff/decision (TASK-AR-518 intent) |
| Asset-prune loop detect-only | `asset-prune-detect-only` | `REVIEW-2026-06-22-subsystem-verification-audit` | tooling | `asset_lifecycle.py` (shipped) closes detect→action via reversible keep→observe; deprecate/remove Owner-gated |
| beta_tester role dormant | `beta-tester-dormant` | `REVIEW-2026-06-22-subsystem-verification-audit` | proposal | advisory beta_tester_due only; activate scheduled exploration rounds → BTC-* → QA bugs |
| W4a green but cross-surface acceptance incomplete | `w4-green-cross-surface-gap` | `COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction`, TASK-AR-639 | process+proposal | require independent W4b plus root/template/worker/overlay/taskset/pointer/read-model matrix for tuple changes |
| Authorization parser differs from consumed semantics | `authorization-boundary-parser-differs-from-rendered-document-semantics` | `COMPOUND-20260729-145000-authorization-boundary-accepted-normalized-or-no-581ab8448ac0`, TASK-AR-647 W4b r1-r8 | gate+fixture | bind exact typed canonical inputs and installed code; validate rendered semantics; adversarially probe adjacent states |
| Mandatory W4b evidence cannot be consumed by closeout | `closeout-evidence-producer-consumer-gap` | `COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction`, TASK-AR-639 | needs enforcement | TASK-AR-645 first-class task-linked review evidence; TASK-AR-651 no-manual-edit lifecycle smoke |
| Released unit conflated with completed taskset | `released-unit-taskset-phase-conflation` | `COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction`, TASK-AR-639 | needs enforcement | TASK-AR-645 split phase semantics; RC blocks if honest intermediate close still needs a waiver |
| Economic eligibility trusts caller-controlled state | `economic-eligibility-caller-state-trust` | TASK-AR-652 W4b chain, `RETRO-2026-07-30-task-ar-652-economic-routing-integrity` | gate+fixture | keep exact observed receipt, immutable provenance, ordered identity, and container-sealing regressions |
| Merge queue cannot consume an attached worker branch | `merge-queue-checked-out-worktree-ordering` | TASK-AR-652 W5, `RETRO-2026-07-30-task-ar-652-economic-routing-integrity` | task proposal | TASK-AR-657 scope amendment: worktree-aware preflight and one canonical cleanup/integration order |
| Closeout review omits canonical work identifiers | `closeout-review-canonical-linkage` | TASK-AR-652 additive audit, existing producer/consumer gap | task proposal | TASK-AR-657 skill templates must emit canonical `task_id`/`unit_id` and closure-contract fixtures |

## Detailed Cases

### CASE-BRIEF-FORMAT-DRIFT

| Field | Value |
| --- | --- |
| `case_id` | `CASE-BRIEF-FORMAT-DRIFT` |
| `dedupe_key` | `brief-format-drift` |
| `symptom` | Owner-facing backlog/report output collapses into an unstructured task list. |
| `trigger` | User asks for backlog, plan, report, or status. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/owner_doc_format_gate.py`, response contract checks |
| `recurrence_count` | 2+ |
| `source_refs` | `agents/lead_engineer/compound_log.md`, `reviews/REVIEW-2026-06-09-backlog-brief-format-drift-compound.md` |
| `reproduction` | Run owner-doc format gate against listed owner docs. |
| `linked_regression_fixture` | `tests/test_backlog_board_tasksets.py` and owner-doc gate manifest |
| `task_proposal` | completed governance/board follow-up |
| `prevention_status` | gate |

### CASE-CONTINUITY-POINTER-GAP

| Field | Value |
| --- | --- |
| `case_id` | `CASE-CONTINUITY-POINTER-GAP` |
| `dedupe_key` | `continuity-pointer-gap` |
| `symptom` | Resume state becomes ambiguous across panes and tasksets. |
| `trigger` | Session closeout or taskset handoff. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/continuity_contract_gate.py`, `scripts/taskset_work_gate.py` |
| `recurrence_count` | 1+ |
| `source_refs` | `COMPOUND-2026-06-10-003`, `agents/project/NEXT-SESSION-POINTER.yml` |
| `reproduction` | Run continuity gate after pointer or claim changes. |
| `linked_regression_fixture` | continuity gate tests and taskset gate |
| `task_proposal` | completed continuity/session-closeout automation |
| `prevention_status` | gate |

### CASE-TASKSET-COMPLETION-CLAIM-ONLY

| Field | Value |
| --- | --- |
| `case_id` | `CASE-TASKSET-COMPLETION-CLAIM-ONLY` |
| `dedupe_key` | `taskset-completion-claim-only` |
| `symptom` | A taskset is claimed complete while one or more canonical task files remain planned/open. |
| `trigger` | Claim release or closeout report. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/taskset_work_gate.py --require-complete` |
| `recurrence_count` | 2+ |
| `source_refs` | `COMPOUND-2026-06-10-004`, `TASKSET-AR-VISION-GAP-CLOSURE`, `TASKSET-AR-RSI-OPERATING-SYSTEM` |
| `reproduction` | Run named taskset gate with `--require-complete`. |
| `linked_regression_fixture` | `tests/test_taskset_work_gate.py` |
| `task_proposal` | no new proposal; closeout gate is now required |
| `prevention_status` | gate |

### CASE-RSI-EVIDENCE-SCATTERED

| Field | Value |
| --- | --- |
| `case_id` | `CASE-RSI-EVIDENCE-SCATTERED` |
| `dedupe_key` | `rsi-evidence-scattered` |
| `symptom` | Trace, eval, A2A, correction, review, and retro evidence cannot reliably become proposals. |
| `trigger` | RSI operating-system registration and follow-up closeout. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/verify_rsi_operating_system_taskset.py` |
| `recurrence_count` | 1 |
| `source_refs` | `reviews/REVIEW-2026-06-11-agent-runtime-rsi-operating-system-registration.md` |
| `reproduction` | Run RSI verification wrapper and inspect evidence registries. |
| `linked_regression_fixture` | `tests/test_rsi_operating_system_docs.py`, `tests/test_a2a_lifecycle_gate.py` |
| `task_proposal` | `TASK-AR-297` through `TASK-AR-305` |
| `prevention_status` | verified |

## Rules

- A case with recurrence count greater than one cannot stay `note_only` without an accepted watch decision.
- A case with deterministic reproduction should gain a regression fixture or a task proposal.
- A case touching Owner-only boundaries must stay proposal-only until the Owner decision is explicit.
- `needs enforcement` entries must route to a task proposal or an explicit `accepted_watch` decision before closeout.

### CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT

| Field | Value |
| --- | --- |
| `case_id` | `CASE-SELF-IMPROVEMENT-LOW-FREQUENCY-DEBT` |
| `dedupe_key` | `self-improvement-low-frequency-debt` |
| `symptom` | Low-frequency roles and runtime assets stay visible as watch debt. |
| `trigger` | `scripts/self_improvement_cycle.py assess` reports immature/watch. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/collaboration_governance_gate.py`, `scripts/runtime_asset_usage.py` |
| `recurrence_count` | role gaps `6`; asset gaps `17` |
| `source_refs` | `reviews/REVIEW-2026-06-17-self-improvement-cycle.md`, `COMPOUND-2026-06-17-001` |
| `reproduction` | Run `python scripts/self_improvement_cycle.py assess --json`. |
| `linked_regression_fixture` | `tests/test_self_improvement_cycle.py` |
| `task_proposal` | `TASK-AR-571`, then `TASK-AR-572` maturity reporting |
| `prevention_status` | watch |

### CASE-RELEASE-PERPETUAL-SKIP

| Field | Value |
| --- | --- |
| `case_id` | `CASE-RELEASE-PERPETUAL-SKIP` |
| `dedupe_key` | `release-perpetual-skip` |
| `symptom` | 337 commits / 114 feat accumulated since v0.2.0 but no new tag was cut, so the downstream host (autofolio) never received an `update-notify` (notify keys on published tags). |
| `trigger` | A release is "due" (cadence triggered) but `release-auto.yml` ran only on a weekly cron AND its safety gate required `latest-completed-main-test SHA == current main HEAD`; under high merge velocity main HEAD always moved past, so every run hit `ci_status=moved` and skipped. Manual dispatch (run 27903117824) skipped for the same reason. |
| `owner_boundary` | release/version |
| `affected_gate` | `.github/workflows/release-auto.yml`, `scripts/release_auto_noncritical.py`, `scripts/release_cadence_trigger.py` |
| `recurrence_count` | 1 (structural — would recur every release until fixed) |
| `source_refs` | `COMPOUND-2026-06-22-001`, PR #183, `[[agent-runtime-release-cadence-direction]]` |
| `reproduction` | Pre-fix: `gh workflow run release-auto.yml -f dry_run=false` on a busy main → log shows `moved past the CI-validated <sha>; skipping`. |
| `linked_regression_fixture` | `tests/test_release_auto_noncritical.py::test_release_auto_workflow_fires_on_test_completion_and_releases_validated_sha` |
| `task_proposal` | shipped (PR #183): `workflow_run` trigger + checkout the CI-validated green SHA (don't require it to equal a moving HEAD) + semver fix |
| `prevention_status` | gate |

### CASE-RELEASE-VERSION-CASCADE

| Field | Value |
| --- | --- |
| `case_id` | `CASE-RELEASE-VERSION-CASCADE` |
| `dedupe_key` | `release-version-cascade` |
| `symptom` | A version bump that touches only `pyproject.toml`/`__init__.py` leaves the "current public tag" stale in coupled files → CI red (found via 3 cascading failures during the v0.3.0 cut). |
| `trigger` | Cutting a release without bumping every current-tag reference atomically. |
| `owner_boundary` | release/version |
| `affected_gate` | `tests/test_inventory_sync_sanitize.py`, `tests/test_release_execution_gate.py`, `release-preflight` (host-upstream-match), `tests/test_lock_merge_driver.py` |
| `recurrence_count` | 2 (v0.3.0 cut + every future cut) |
| `source_refs` | `COMPOUND-2026-06-22-001`, PR #184, `[[agent-runtime-release-cadence-direction]]` (cascade file list) |
| `reproduction` | Bump only pyproject + run `pytest tests/test_inventory_sync_sanitize.py` → version/tag-mismatch failures. |
| `linked_regression_fixture` | `tests/test_release_version_cascade.py` (new) + existing inventory/execution-gate/preflight tests |
| `task_proposal` | SHIPPED: `scripts/release_version_cascade.py` — `--check` (one-pass consistency across all 12 refs) + `--write <ver>` (atomic bump + best-effort host-lock regen) + `--json`. Source-repo release tool, intentionally NOT in `owner_governance_gate` (consumer projects lack these refs → would reintroduce `consumer-project-path-assumption`). |
| `prevention_status` | tooling |

### CASE-TEMPLATE-STALE-HOST-LOCK

| Field | Value |
| --- | --- |
| `case_id` | `CASE-TEMPLATE-STALE-HOST-LOCK` |
| `dedupe_key` | `template-stale-host-lock` |
| `symptom` | Editing any `src/agent_runtime/templates/**` file without regenerating `tests/fixtures/host/agent_runtime.lock.json` → `test_lock_merge_driver::test_regenerate_noop_when_current` fails in CI. |
| `trigger` | Template change committed without lock regen. |
| `owner_boundary` | local |
| `affected_gate` | `tests/test_lock_merge_driver.py`, `agent_runtime lock --check` |
| `recurrence_count` | 2+ (hit this session; previously noted in `[[agent-runtime-merge-concurrency]]`) |
| `source_refs` | `COMPOUND-2026-06-22-001`, PR #183 |
| `reproduction` | Edit a template file, run `pytest tests/test_lock_merge_driver.py`. Fix: `lock_merge_driver.regenerate(Path('tests/fixtures/host'))`. |
| `linked_regression_fixture` | `tests/test_lock_merge_driver.py` (already the gate) |
| `task_proposal` | propose a pre-commit / PostToolUse hook that auto-regenerates the host lock when a `templates/**` file changes |
| `prevention_status` | gate |

### CASE-SHARED-CHECKOUT-REF-RACE

| Field | Value |
| --- | --- |
| `case_id` | `CASE-SHARED-CHECKOUT-REF-RACE` |
| `dedupe_key` | `shared-checkout-ref-race` |
| `symptom` | A destructive ref op (`git branch -D`) deleted a branch whose tip a concurrent agent had advanced (4 unmerged TASK-AR-593 commits); recovered via `git branch <name> <sha>`. Concurrent agents also move HEAD / `git clean -fd` away untracked work in the shared checkout. |
| `trigger` | Running branch/worktree/tree cleanup in the shared checkout while another autonomous agent is active; trusting a cached SHA across the race window. |
| `owner_boundary` | local (destructive) |
| `affected_gate` | none (behavioral) — `parallel_worktree_gate` covers commit-time, not ad-hoc cleanup |
| `recurrence_count` | 2+ (ref delete this session; prior `clean -fd` losses in `[[agent-runtime-merge-concurrency]]`) |
| `source_refs` | `COMPOUND-2026-06-22-001`, `[[agent-runtime-merge-concurrency]]`, `[[agent-runtime-work-branch-isolation]]` |
| `reproduction` | non-repro (timing-dependent across concurrent sessions). |
| `linked_regression_fixture` | n/a (behavioral) |
| `task_proposal` | propose a `safe-ref-op` wrapper that re-reads the live tip immediately before `branch -D/-f`/`push --delete`/`reset` and refuses if it moved; default to worktree isolation + no cleanup during concurrency |
| `prevention_status` | proposal |

### CASE-NONHERMETIC-TEST-TRACKED-MUTATION

| Field | Value |
| --- | --- |
| `case_id` | `CASE-NONHERMETIC-TEST-TRACKED-MUTATION` |
| `dedupe_key` | `nonhermetic-test-tracked-mutation` |
| `symptom` | The full test suite mutated tracked files in the worktree (`ARCHIVE-INDEX.md` / `BACKLOG-BOARD.md` `generated_at: 6-20 -> 6-21`); a `git add -A` then swept that churn into an unrelated release commit. |
| `trigger` | A non-hermetic test writes board/archive docs against the repo root instead of a tmp dir; a broad `git add -A` after running tests. |
| `owner_boundary` | local |
| `affected_gate` | none yet |
| `recurrence_count` | 1 (this session) |
| `source_refs` | `COMPOUND-2026-06-22-001` |
| `reproduction` | Run `pytest tests -q` in a clean checkout, then `git status` → ARCHIVE-INDEX/BACKLOG-BOARD show date-only diffs. |
| `linked_regression_fixture` | n/a |
| `task_proposal` | (1) make the board/archive-generating test write to `tmp_path`; (2) practice: stage explicit pathspecs (never `git add -A`) when composing a release/version commit |
| `prevention_status` | proposal |

### CASE-CI-FLAKY-TEMP-GIT

| Field | Value |
| --- | --- |
| `case_id` | `CASE-CI-FLAKY-TEMP-GIT` |
| `dedupe_key` | `ci-flaky-temp-git` |
| `symptom` | `test_release_auto_noncritical`/`test_release_cadence_trigger` intermittently fail in CI despite exact PR/local passes. Outcomes include false `not-triggered`, `trigger-error`, and a fixture commit exhausting six retries with `fatal: could not parse HEAD`. |
| `trigger` | Temp-git-repo gate tests under CI runner load; a flaky `git` subprocess can make tag/count reads empty or leave fixture `HEAD` unreadable beyond the current bounded retry. |
| `owner_boundary` | local |
| `affected_gate` | `.github/workflows/test.yml` (`Run package tests`) |
| `recurrence_count` | 4+ (two earlier PR runs, main run 30350865552, and TASK-AR-646 main run 30406516812) |
| `source_refs` | `COMPOUND-2026-06-22-001`, `reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md`, `agents/project/knowledge/compounds/records/COMPOUND-20260729-081348-temp-git-fixture-head-corruption-survives-bounde-2514bdcf5f65.json`, main runs `30350865552` and `30406516812` |
| `reproduction` | non-deterministic; not reproduced locally (full suite + deterministic order both green). |
| `linked_regression_fixture` | n/a |
| `task_proposal` | TASK-AR-651: add observable recovery plus a deterministic fixture at every remaining temp-git boundary, or remove the unstable mechanism from release-critical decisions; a bare rerun is not prevention |
| `prevention_status` | needs enforcement |

### CASE-W4-GREEN-CROSS-SURFACE-GAP

| Field | Value |
| --- | --- |
| `case_id` | `CASE-W4-GREEN-CROSS-SURFACE-GAP` |
| `dedupe_key` | `w4-green-cross-surface-gap` |
| `symptom` | Focused implementation tests pass, but independent W4b finds lifecycle tuple disagreements across overlay, taskset, pointer, root/template schema, or read-model consumers. |
| `trigger` | A task changes a durable tuple consumed by multiple runtime surfaces and W4a tests only the implementation-local path. |
| `owner_boundary` | local |
| `affected_gate` | independent W4b; root/template parity and lifecycle integration suites |
| `recurrence_count` | 2 in TASK-AR-639 |
| `source_refs` | `reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md`, TASK-AR-639 W4b/recheck evidence |
| `reproduction` | Exercise the same tuple as an active worker, explicit overlay, taskset member, pointer target, root record, template record, and UI/read-model input. |
| `linked_regression_fixture` | pending cross-surface matrix under TASK-AR-643 or TASK-AR-651 |
| `task_proposal` | Keep independent W4b mandatory for TASK-AR-640 through TASK-AR-647; add the matrix to clean-host release evidence. |
| `prevention_status` | process+proposal |

### CASE-AUTHORIZATION-BOUNDARY-SEMANTIC-PARSER-GAP

| Field | Value |
| --- | --- |
| `case_id` | `CASE-AUTHORIZATION-BOUNDARY-SEMANTIC-PARSER-GAP` |
| `dedupe_key` | `authorization-boundary-parser-differs-from-rendered-document-semantics` |
| `symptom` | A green security gate accepts caller-shaped values, substituted snapshots, malformed typed metadata, missing or shadowed gate code, or a required heading that the Markdown renderer does not render. |
| `trigger` | A security or authorization decision is implemented with permissive normalization, local line matching, or an unbound caller-supplied representation instead of the canonical consumed grammar and snapshot. |
| `owner_boundary` | local security boundary |
| `affected_gate` | `src/agent_runtime/security_service.py`, `scripts/task_claim_dispatcher.py`, root/template claim-time security-service enforcement |
| `recurrence_count` | 7 adjacent blocker rounds during TASK-AR-647 W4b |
| `source_refs` | `reviews/W4B-2026-07-29-unit-task-ar-647-001.md`, `reviews/W4B-2026-07-29-unit-task-ar-647-001-r7.md`, `agents/project/knowledge/compounds/records/COMPOUND-20260729-145000-authorization-boundary-accepted-normalized-or-no-581ab8448ac0.json` |
| `reproduction` | Present a risky unit through an adjacent representation: unsupported or quoted scalar metadata, identity/path substitution, symlink or unstable snapshot, missing/shadowed gate module, or an H2-looking line inside a non-rendered Markdown block. |
| `linked_regression_fixture` | `tests/test_security_service.py`, `tests/test_task_claim_dispatcher.py` |
| `task_proposal` | shipped in TASK-AR-647: exact typed metadata, canonical identity binding, bounded stable regular-file snapshot, registered-target union, exact-worktree import, required installed-gate proof, and Markdown block-state validation |
| `prevention_status` | gate+fixture |

### CASE-CLOSEOUT-EVIDENCE-PRODUCER-CONSUMER-GAP

| Field | Value |
| --- | --- |
| `case_id` | `CASE-CLOSEOUT-EVIDENCE-PRODUCER-CONSUMER-GAP` |
| `dedupe_key` | `closeout-evidence-producer-consumer-gap` |
| `symptom` | Mandatory Markdown W4b evidence exists but `work close` cannot consume its reference, requiring a temporary omission and manual restoration. |
| `trigger` | Close a verified unit using the artifact format emitted by the independent-review phase. |
| `owner_boundary` | local |
| `affected_gate` | `scripts/work.py close`, W4b evidence contract |
| `recurrence_count` | 2 (TASK-AR-639 UNIT-001 and UNIT-002) |
| `source_refs` | `reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md` |
| `reproduction` | Attach the emitted `reviews/W4B-*.md` path to a unit and run the normal close transition without manually editing the projection. |
| `linked_regression_fixture` | pending no-manual-edit lifecycle smoke |
| `task_proposal` | TASK-AR-645 consumes task-linked compound/review records; TASK-AR-651 proves the complete lifecycle in a clean host. |
| `prevention_status` | needs enforcement |

### CASE-RELEASED-UNIT-TASKSET-PHASE-CONFLATION

| Field | Value |
| --- | --- |
| `case_id` | `CASE-RELEASED-UNIT-TASKSET-PHASE-CONFLATION` |
| `dedupe_key` | `released-unit-taskset-phase-conflation` |
| `symptom` | A legitimately released unit claim is warned unless it says `taskset-completed`, even though sibling tasks in the taskset remain planned. |
| `trigger` | Release and close one unit inside a still-active multi-task taskset. |
| `owner_boundary` | local |
| `affected_gate` | collaboration governance and claim lifecycle projection |
| `recurrence_count` | 2+ tasksets |
| `source_refs` | `reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md`, `reviews/RETRO-2026-07-23-taskset-ar-work-cli-integrity.md` |
| `reproduction` | Release a verified unit with `progress_pct: 100` while its parent taskset remains active, then run collaboration governance. |
| `linked_regression_fixture` | pending phase-state matrix |
| `task_proposal` | TASK-AR-645 separates unit/task/claim/taskset terminal facts; TASK-AR-651 rejects an RC that still needs a false phase or waiver. |
| `prevention_status` | needs enforcement |

### CASE-CONSUMER-PATH-ASSUMPTION

| Field | Value |
| --- | --- |
| `case_id` | `CASE-CONSUMER-PATH-ASSUMPTION` |
| `dedupe_key` | `consumer-project-path-assumption` |
| `symptom` | `continuity_contract_gate` / `owner_governance_gate` / `state_machine_gate` assumed `src/agent_runtime/templates/project/**` exists, so they failed (`protocol-doc-missing`) in generated consumer projects (autofolio) that ship only root `AGENTS.md`/`CLAUDE.md`. |
| `trigger` | Running a gate that hard-codes source-repo template paths inside a consumer project. |
| `owner_boundary` | local (host-fit) |
| `affected_gate` | `scripts/continuity_contract_gate.py`, `scripts/owner_governance_gate.py`, `scripts/state_machine_gate.py` (+ template copies) |
| `recurrence_count` | 1 (issue #185) |
| `source_refs` | `COMPOUND-2026-06-22-001`, issue #185, PR #187, released in v0.3.1 |
| `reproduction` | Run `continuity_contract_gate.py --root <consumer-with-root-docs-only> --check`; pre-fix raised `protocol-doc-missing`. |
| `linked_regression_fixture` | `tests/test_continuity_contract_gate.py`, `tests/test_state_machine_gate.py` |
| `task_proposal` | shipped (PR #187): protocol docs resolve root-OR-template; `state_machine_gate --optional-path`; consumers skip absent `src/**` paths |
| `prevention_status` | gate |

### CASE-ROLE-CONCENTRATION

| Field | Value |
| --- | --- |
| `case_id` | `CASE-ROLE-CONCENTRATION` |
| `dedupe_key` | `role-concentration` |
| `symptom` | One role (lead-engineer) holds 85/112 task claims (76%); review/verify/scout roles (council, skeptic, progress-scout = 0; reviewer/scribe/release-steward = 1; independent-auditor = 2) are dormant. Costs −15 maturity (monitored_role_gaps). |
| `trigger` | Autonomous dispatch (wave_dispatcher / task_claim_dispatcher / org_orchestrator) defaults work to the lead-engineer worker; ORG-MODEL defines review/skeptic/scout roles but nothing routes work to them — they are monitored, never dispatched. |
| `owner_boundary` | local (advisory) / dispatch-architecture (proposal) |
| `affected_gate` | `scripts/role_concentration_gate.py` (new, advisory), `scripts/self_improvement_cycle.py assess` (collaboration) |
| `recurrence_count` | structural (every window until dispatch rebalances) |
| `source_refs` | `REVIEW-2026-06-22-system-health-rsi-diagnosis.md`, self_improvement_cycle assess |
| `reproduction` | `python scripts/role_concentration_gate.py --check` (after it ships) → watch when a role share > threshold. |
| `linked_regression_fixture` | `tests/test_role_concentration_gate.py` |
| `task_proposal` | (1) shipped: advisory `role_concentration_gate`; (2) PROPOSAL (Owner-tier, touches dispatch): route a fraction of work to skeptic/independent-auditor (high-risk merges), progress-scout (per wave), council (W6). |
| `prevention_status` | tooling+proposal |

### CASE-COMPOUND-UNDER-CADENCE

| Field | Value |
| --- | --- |
| `case_id` | `CASE-COMPOUND-UNDER-CADENCE` |
| `dedupe_key` | `compound-under-cadence` |
| `symptom` | Reviews are over-produced and lessons under-compounded: this month ~294 REVIEW vs 1 COMPOUND vs 4 RETRO. The failure→regression loop runs only when a human triggers it. |
| `trigger` | Review is a cheap auto-emitted artifact (W4b votes per task); compounding needs the deliberate failure-to-regression step, and no cadence signal forces it. |
| `owner_boundary` | local (advisory) / process (proposal) |
| `affected_gate` | `scripts/compound_cadence_gate.py` (new, advisory) |
| `recurrence_count` | structural |
| `source_refs` | `REVIEW-2026-06-22-system-health-rsi-diagnosis.md` |
| `reproduction` | `python scripts/compound_cadence_gate.py --check` → watch when REVIEW:COMPOUND ratio exceeds the threshold. |
| `linked_regression_fixture` | `tests/test_compound_cadence_gate.py` |
| `task_proposal` | (1) shipped: advisory `compound_cadence_gate`; (2) PROPOSAL: make "compound >= 1 lesson per N reviews" a cycle obligation (W6 / session-closeout). |
| `prevention_status` | tooling+proposal |

### CASE-A2A-DORMANT-NOT-WIRED

| Field | Value |
| --- | --- |
| `case_id` | `CASE-A2A-DORMANT-NOT-WIRED` |
| `dedupe_key` | `a2a-dormant-not-wired` |
| `symptom` | A2A messaging (router + lifecycle/trace gates) is complete and tested (4/4) but has ZERO runtime traffic: `agents/runtime/a2a/messages.jsonl` doesn't exist, only a static 2026-06-09 baseline; gates pass vacuously. Cross-team and same-role-multi-instance comms therefore never happen at runtime. |
| `trigger` | A2A landed as PoC-complete (TASK-AR-311); the dispatcher/orchestrator were never wired to `emit_message()` on real work. |
| `owner_boundary` | dispatch-architecture (proposal) |
| `affected_gate` | `scripts/a2a_message_router.py`, `a2a_lifecycle_gate.py`, `a2a_trace_gate.py` |
| `recurrence_count` | 1 (structural) |
| `source_refs` | `REVIEW-2026-06-22-subsystem-verification-audit.md`, TASK-AR-311, TASK-AR-518 |
| `reproduction` | `ls agents/runtime/a2a/` → no live messages.jsonl; grep for `emit_message(` callers → only tests. |
| `linked_regression_fixture` | `tests/test_a2a_message_router.py` (PoC), `test_a2a_*` gates |
| `task_proposal` | PROPOSAL (Owner-tier): wire `emit_message` into claim/handoff/decision in the dispatch path (TASK-AR-518 intent); this also activates cross-team + same-role-instance comms. |
| `prevention_status` | proposal |

### CASE-BETA-TESTER-DORMANT

| Field | Value |
| --- | --- |
| `case_id` | `CASE-BETA-TESTER-DORMANT` |
| `dedupe_key` | `beta-tester-dormant` |
| `symptom` | The beta_tester role has a spec + advisory `beta_tester_due.py` but is never activated — no automated exploration rounds, no BTC-* test-case artifacts. Edge/concurrency tests are strong; exploratory beta testing is absent. |
| `trigger` | beta_tester_due only emits a cadence signal (exit 0); nothing dispatches a beta exploration round. |
| `owner_boundary` | dispatch-architecture (proposal) |
| `affected_gate` | `scripts/beta_tester_due.py`, `agents/beta_tester/` |
| `recurrence_count` | 1 (structural) |
| `source_refs` | `REVIEW-2026-06-22-subsystem-verification-audit.md` |
| `reproduction` | `python scripts/beta_tester_due.py` → due/overdue signal; no BTC-* artifacts produced. |
| `linked_regression_fixture` | n/a |
| `task_proposal` | PROPOSAL: schedule beta exploration rounds (BTC-* → QA bug intake), same as routing other dormant roles into the loop. |
| `prevention_status` | proposal |

### CASE-ECONOMIC-ELIGIBILITY-CALLER-STATE-TRUST

| Field | Value |
| --- | --- |
| `case_id` | `CASE-ECONOMIC-ELIGIBILITY-CALLER-STATE-TRUST` |
| `dedupe_key` | `economic-eligibility-caller-state-trust` |
| `symptom` | A syntactically valid report could treat request intent, replaceable provenance, mutated receipt values, or duplicate/mutated container membership as observed savings evidence. |
| `trigger` | Economic eligibility reads caller-owned configuration, row objects, or collection structure after validation without binding the exact observed terminal receipt and immutable membership. |
| `owner_boundary` | local economic evidence; no live provider authority |
| `affected_gate` | `src/agent_runtime/templates/project/scripts/eval_harness.py` and its W4b eligibility boundary |
| `recurrence_count` | 6 adjacent trust-boundary repair rounds in TASK-AR-652 |
| `source_refs` | `reviews/W4B-2026-07-30-unit-task-ar-652-001-receipt-attestation-approval.md`, `reviews/W4B-2026-07-30-unit-task-ar-652-001-attested-container-sealing-approval.md`, `reviews/RETRO-2026-07-30-task-ar-652-economic-routing-integrity.md` |
| `reproduction` | Start from one valid synthetic baseline/actual ledger, then copy or mutate a receipt, replace authority, duplicate membership, invoke direct base-list mutation, reinitialize, or supply a forged subclass; every changed view must report zero economic eligibility. |
| `linked_regression_fixture` | `src/agent_runtime/templates/project/scripts/test_eval_harness.py` receipt-attestation and container-integrity matrix |
| `task_proposal` | shipped in TASK-AR-652: observed terminal identity, canonical receipt digests, immutable snapshots, exact ordered membership, sealed authority, and fail-closed report-time validation |
| `prevention_status` | gate+fixture |

### CASE-MERGE-QUEUE-CHECKED-OUT-WORKTREE-ORDERING

| Field | Value |
| --- | --- |
| `case_id` | `CASE-MERGE-QUEUE-CHECKED-OUT-WORKTREE-ORDERING` |
| `dedupe_key` | `merge-queue-checked-out-worktree-ordering` |
| `symptom` | A clean, verified, released branch fails merge-queue processing before verification because Git will not check it out in the integrator while it remains attached to its worker worktree. |
| `trigger` | Follow the documented order `integrate -> cleanup` with `merge_queue.py`, whose local mode first runs `git checkout <worker-branch>` in the integrator checkout. |
| `owner_boundary` | local SCM cleanup and integration |
| `affected_gate` | `scripts/merge_queue.py`, `skills/merge-integrator/SKILL.md`, Work Model W5 ordering |
| `recurrence_count` | 1 deterministic TASK-AR-652 integration failure |
| `source_refs` | `reviews/RETRO-2026-07-30-task-ar-652-economic-routing-integrity.md`, local merge commit `1a18a3a6` |
| `reproduction` | Keep a clean worker branch attached to `.worktrees/<task>`, enqueue it, and run `python scripts/merge_queue.py process --all --base main`; Git returns `already checked out`. |
| `linked_regression_fixture` | proposed addition to `tests/test_merge_queue.py` covering attached clean worktrees and actionable dry-run/preflight output |
| `task_proposal` | TASK-AR-657 scope amendment: make the merge-integrator skill and executable preflight agree on detach-before-checkout or integrate through the existing worktree |
| `prevention_status` | task proposal |

### CASE-CLOSEOUT-REVIEW-CANONICAL-LINKAGE

| Field | Value |
| --- | --- |
| `case_id` | `CASE-CLOSEOUT-REVIEW-CANONICAL-LINKAGE` |
| `dedupe_key` | `closeout-review-canonical-linkage` |
| `symptom` | Independently approved audit reports are indexed and human-readable but `work close` rejects them because they carry `parent_task_id` instead of canonical `task_id`/`unit_id`. |
| `trigger` | A review-producing agent or skill invents a near-equivalent frontmatter key rather than consuming the work-close evidence schema. |
| `owner_boundary` | local work closeout |
| `affected_gate` | `scripts/work.py close`, `scripts/closure_gate.py`, independent-verification report templates |
| `recurrence_count` | 3 (two TASK-AR-639 units plus TASK-AR-652 additive closeout) |
| `source_refs` | `reviews/COMPOUND-2026-07-28-v080-lifecycle-and-closeout-friction.md`, `reviews/INDEPENDENT-AUDIT-2026-07-30-task-ar-652-closeout.md`, `reviews/QA-REVIEW-2026-07-30-task-ar-652-additive-closeout.md` |
| `reproduction` | Create an approved review with only `parent_task_id: TASK-AR-652`, pass it via `work.py close --review-ref`, and observe `closeout:review-work-mismatch`. |
| `linked_regression_fixture` | `tests/test_closure_gate.py` plus a proposed skill-template contract test in TASK-AR-657 |
| `task_proposal` | TASK-AR-657: require runtime-adoption and independent-verification templates to emit closeout-consumable canonical identifiers and test the generated report against `work close` |
| `prevention_status` | task proposal |
