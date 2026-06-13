---
type: review
id: REVIEW-2026-06-13-parallel-wave-500-series-capability-analysis
audience: owner
status: pass
signal: pass
score: 93
priority: High
tags: [analysis, 500-series, capability, verification, applied-state]
---

# 500-Series Capability Analysis — Implemented, Applied, Verified

## Bottom Line

- All 19 implementation tasks of the 500-series (TASK-AR-500..522, plus the
  earlier AR-504/AR-508) are merged to `main`, verified, and closed.
- "Applied" has three honest meanings, and this record makes the distinction
  explicit so the Owner is not misled by "all done": (1) automatic gates that
  run every commit/stop-hook, (2) on-demand tools the orchestrator/dispatcher
  invokes, (3) Owner-gated actions (release execution, gh mutations, host
  live-apply).
- Verification model is W4a (worker self-check: test counts + gate exit 0) plus
  W4b (an independent instance returning APPROVE / REQUEST-CHANGES). There are
  no per-task numeric scores. The objective evidence is: full suite 712
  passed / 0 failed, governance gate exit 0, all 19 W4b APPROVE (AR-501 was
  REQUEST-CHANGES then fixed and re-approved), closeout review scores 88/92/94.

## Signal

| Dimension | State | Evidence |
| --- | --- | --- |
| Implementation | pass | 19/19 tasks merged to main (PRs #45-#82) |
| Verification | pass | full suite 712 passed / 0 failed; all W4b APPROVE |
| Applied (auto gates) | pass | 7 new gates wired into owner_governance chain |
| Applied (tools/CLI/UI) | pass | wave/merge-queue/scm-steward/work-stats/Work-Explorer present |
| Owner-gated remainder | watch | v0.2.0 release execution, gh mutations, autofolio live-apply |

## Verification Model (what "score" means here)

- W4a — worker self-verification: focused tests + full `pytest tests -q` +
  `owner_governance_gate.py` exit 0.
- W4b — independent verification by a distinct instance: APPROVE or
  REQUEST-CHANGES with numbered findings; most W4b agents are read-only and
  cross-check W4a evidence by static analysis.
- Authoritative end-state proof: orchestrator-run full suite on `main` =>
  712 passed / 0 failed; governance gate exit 0.

## Applied-State Classification

| Form | Meaning | Tasks |
| --- | --- | --- |
| Automatic gate (every commit/stop-hook) | wired into owner_governance_gate chain | AR-500, 503, 505(check), 507, 510, 514, 515, 518, 519, 520, 521 |
| Automatic wiring (on register/dispatch) | work.py new -> T0 snapshot; claim create -> T2 drift | AR-506, 504 |
| Tool (invoked, not always-on) | orchestrator/dispatcher calls on demand | AR-501 wave, 502 merge-queue, 505 --clean, 512 scm-steward |
| CLI / UI | human query/use | AR-513, 516(UI), 517(stats/views), 509(notify) |
| Repo config / contract | one-time apply, standing effect | AR-508, 511, 522, 506(W0-W6 contract) |

New gates wired into the chain this series: footprint_conflict, worktree_lifecycle,
attribution, verification_freshness, release_cadence, conversation_work_audit,
work_schema. The four orchestration tools (wave_dispatcher, merge_queue,
scm_steward, inflight_overlay) are intentionally NOT gates.

## Per-Task Summary (deliverable / effect / W4a / W4b)

### Multi-agent collaboration
- AR-500 footprint conflict gate [auto gate]: claim-time target_files
  intersection check; moves conflict discovery from merge-time to claim-time.
  Live proof: refused AR-517/506 work.py double-claim. 22/495, APPROVE.
- AR-503 claim-first enforcement [auto gate]: claim-less worktree + untracked
  claim block; prevents the 2026-06-12 claim-loss recurrence. 20/498, APPROVE.
- AR-507 cross-verification gate [release enforcement]: verifier != worker +
  evidence required at release. 7 claims released with verified_by. 21/627, APPROVE.
- AR-518 instance attribution gate [auto gate]: instance_uid attribution across
  claims/A2A/evidence/pane events; spawn record skill_versions/prompt_hash;
  lifecycle census. 16 tests / exit 0, APPROVE.

### Wave / merge queue / cycle
- AR-501 wave dispatcher [tool, opt-in]: depends_on DAG -> topological waves
  (list scheduling), within-wave footprint disjointness, cascade/parallel modes.
  Plan demo 9 units -> 8 waves. 15/590, APPROVE (after one REQUEST-CHANGES fix).
- AR-502 integrator merge queue [tool, orchestrator]: serial rebase-test-merge,
  failure isolation, never force-push/delete. Encodes the manual PR #45-#82 flow.
  6/582, APPROVE.
- AR-506 W0-W6 lifecycle defaults [auto wiring + doc]: registration auto-records
  T0 plan snapshot; dispatch auto-runs T2 drift check; work.py status W0 entry;
  AGENTS.md lifecycle contract. 11/696, APPROVE.
- AR-504 plan assumption gate [earlier session]: deferred T0-T3 revalidation;
  caught 7 drifts this session, T3 re-recorded.

### Worktree GC / cleanup
- AR-505 worktree lifecycle gate [gate(watch) + tool(--clean)]: zombie verdict
  (ahead=0 + claim released + clean) + retention (7d/PRESERVE/tag) + --clean;
  ahead>0/dirty never cleaned. 20/510, APPROVE.

### Release automation
- AR-509 update-notify [CLI + template hook]: host session-start upstream tag
  vs pinned ref notice; always exit 0; 24h cache. autofolio live-apply deferred
  to next release. 18/508, APPROVE.
- AR-510 release cadence trigger [auto gate, watch]: commits 40+/feat 5+/14d
  threshold -> release proposal; currently proposes v0.2.0 minor. 12/501, APPROVE.

### Work schema / generator / classifier
- AR-515 work metadata schema catalog [applied + auto gate]: provenance/closure/
  relations/governance/verification fields with source + promotion policy;
  anti-bloat (required minimal, rest optional); backward compatible. 21/502, APPROVE.
- AR-517 work stats/query/export/saved views [CLI]: work.py stats --by/--metric/
  --filter, JSON/CSV export, view save/run/list (WORK-VIEWS.json, 4 seeded).
  14/587, APPROVE.
- AR-514 conversation-to-work audit [auto gate]: planning records must map to
  task/board/pointer. 9 records / exit 0, APPROVE (none-sentinel false-positive
  fixed post-merge).

### Backlog UI
- AR-516 Work Explorer tree [UI]: Initiative->Taskset->Task->Unit tree with
  computed-only roll-ups, facet filters, archived-evidence affordance;
  /api/work_explorer. 45/582, APPROVE.
- AR-513 in-flight overlay [CLI + UI]: checkout-free branch-side task status,
  board "planned(main)/in_progress@branch" annotation. 11/499, APPROVE.

### SCM hygiene
- AR-512 scm-steward [tool + skill]: consolidated hygiene report (zombies/stale
  claims/stashes/PR aging/unregistered issues/view drift); report exit 0,
  clean report-approve-execute, gh mutations Owner-gated (--execute-gh).
  Flagged issues #19/20/21. 25/602, APPROVE.
- AR-508 branch namespace preservation [earlier session]: codex/* + claude/*.
- AR-511 .gitattributes normalization [repo config]: text=auto eol=lf + .cmd
  CRLF; eliminated CRLF warnings. 712/712, APPROVE.

### Gate consistency (derived from W4b notes)
- AR-520 board freshness [gate fix]: mask wall-clock tokens only; fixed 6-minute
  staleness flake. 9 tests, APPROVE.
- AR-521 template chain parity [applied + test]: sync template governance chain +
  parity test. 7 tests, APPROVE.
- AR-522 consistency bundle [5 fixes]: schema enum, zombie unknown-dirty,
  GIT_TERMINAL_PROMPT, merge-queue timeout, CSV injection. 88 focused, APPROVE.

## Action Board

| Status | Action | Owner | Evidence |
| --- | --- | --- | --- |
| Done | Implement + dual-verify + merge all 19 500-series tasks | lead-engineer | PRs #45-#82 |
| Done | Wire 7 new gates into governance chain | lead-engineer | owner_governance_gate.py chain |
| Done | Archive this capability analysis | lead-engineer | this record + owner-docs |
| Next | Add convenience automation around the new infrastructure | lead-engineer | follow-on Part 2 |
| Next | Cut v0.2.0 and apply to autofolio | release-steward + Owner | follow-on Part 3 |
| Next | Migrate existing tasks/docs/rules to the 2.0 work model | lead-engineer | follow-on Part 4 |

## Risks / Blockers

- Risk: wave_dispatcher / merge_queue are opt-in tools; without explicit
  invocation the sequential default stands (not auto-parallel).
- Risk: scm-steward clean + gh mutations and update-notify's autofolio
  live-apply are Owner-gated / next-release-deferred (reporting/notice work now).
- Blocker: none for the implemented scope. Registered residuals (not silent
  gaps): case-fold instance-id hardening (AR-507/518 derived), backlog_board.py
  LF output, bugs #19/20/21.

## Decision

- 500-series is implemented, verified, and applied per the classification above.
- The next initiative (this report's follow-on goal) is to (1) add convenience
  automation around the new infrastructure, (2) cut v0.2.0 and apply to autofolio,
  and (3) migrate existing tasks/docs/rules to the 2.0 work model (units, wave
  registration, verification methods, metadata).

## Evidence Pointers

- Final closeout: reviews/REVIEW-2026-06-13-parallel-wave-500-series-final-closeout.md
- Wave 1-2 closeout: reviews/REVIEW-2026-06-13-parallel-wave-1-2-closeout.md
- Replan: reviews/MEETING-2026-06-13-parallel-wave-replan-post-codex-merge.md
- Per-task Completion Evidence + Verification Results blocks in each
  agents/lead_engineer/tasks/TASK-AR-5NN.md.

## Next Steps

- Part 2: add convenience automation (slash commands, session-start hook,
  W4a/W4b + wave-conductor + integrator agents/skills, cadence/hygiene routines).
- Part 3: cut v0.2.0 (version bump, council decision, preflight, Owner-gated
  tag/push) and apply to autofolio (ref bump + update-plan/update).
- Part 4: migrate existing tasks/docs/rules to the 2.0 work model (units, wave
  registration, verification methods, metadata, agent/skill updates).
