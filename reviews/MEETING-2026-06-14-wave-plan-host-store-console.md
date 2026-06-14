---
type: meeting
id: MEETING-2026-06-14-wave-plan-host-store-console
audience: owner
status: watch
signal: watch
score: 80
priority: High
tags: [planning-record, wave-plan, host-feedback, work-store, console, dispatch]
---

# Wave Execution Plan — Host Feedback + Work Store + Decision Console

## Bottom Line

- Summary: Owner approved all three tasksets; this record sequences the 20 open tasks (TASK-AR-526..545) into dependency tiers W1/W2/W3 so they can be dispatched in linked order, with pairwise-disjoint `target_files` footprints inside each tier.
- Mechanism: waves are NOT hand-numbered. `wave_dispatcher.py --plan` computes them from unit `depends_on` (DAG) + pairwise-disjoint `target_files`; overlapping footprints defer to a later wave. This record is the planning intent the dispatcher materializes once units carry footprints.
- Boundary: registration + plan only. Host-feedback candidates (529/530/531/532) are still gated on the TASK-AR-527 first deliberation; nothing here claims implementation or adoption.

## Signal

| Wave | Tasks | Why this tier (deps) | Footprint disjointness |
| --- | --- | --- | --- |
| W1 foundations | 526, 533, 534, 535 | no dependencies | queue / backlog_board.py / reviews+index / classifier+docs |
| W2 build-on-foundations | 527, 536, 537, 538, 539 | 527<-526; 536<-535; 537<-533,534; 538<-533,526; 539<-535 | harness / task_identity.py / work_index.py / backlog_board.py(after W1) / entity_catalog.py |
| W3 leaves | 528, 529, 530, 531, 532, 540, 541, 542, 543, 544, 545 | 528<-527; 529-532<-527 deliberation; 540-545<-539 | distinct gates/scripts + distinct console modules |

## Action

| # | Action | Owner boundary |
| --- | --- | --- |
| 1 | Decompose W1 tasks into units with `target_files`+`depends_on`, then `wave_dispatcher.py --plan` | local |
| 2 | Dispatch W1 in parallel (4 disjoint footprints); W4a self-verify + W4b independent verify per task | owner_review (PR/merge) |
| 3 | On W1 merge, run TASK-AR-527 first deliberation to decide 529/530/531/532 adoption before W3 | owner_review (direction) |
| 4 | Proceed W2 then W3; dispatcher auto-defers any console-module footprint overlap to a follow wave | local |

## Risk

- W3 is wide (11 tasks). The console leaves (540-545) may share ui-console router/registry files; if unit footprints overlap, the dispatcher defers them into W3b/W3c (graceful, not a conflict). Decompose each to a distinct module/pane file.
- 532(#19 template docs) overlaps 531(wheel/dotfile packaging) — coordinate so the dotfile-shipping fix is not duplicated.
- 538 edits `backlog_board.py` after 533 — must NOT run in the same wave as 533 (same file); placed in W2.
- Candidate adoption (529-532) depends on the 527 deliberation; dispatching them before that verdict risks building deferred work.

## Decision

- Decision: adopt the W1/W2/W3 dependency tiers above as the dispatch order for TASK-AR-526..545.
- Decision: gate the host-feedback candidates (529-532) behind the TASK-AR-527 first deliberation; build pipeline canon (526/527/528) regardless.
- Decision: keep waves footprint-computed by `wave_dispatcher.py`; this record is intent, not a hand-assigned wave id.
- Decision: each task uses W4a (worker self-verify) + W4b (independent verifier ≠ worker) before merge, per the 500-series rule.

## Next

- Create unit specs for W1 (526/533/534/535) with `target_files`+`depends_on`; run `wave_dispatcher.py --plan` to confirm the computed wave matches this intent.
- Dispatch W1; on merge, run the TASK-AR-527 deliberation; then W2; then W3 (let the dispatcher split console overlaps).
- Registration does not move the ready lane; Owner approves PR/merge/push.
