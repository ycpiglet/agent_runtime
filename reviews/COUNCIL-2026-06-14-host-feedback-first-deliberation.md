---
type: council
id: COUNCIL-2026-06-14-host-feedback-first-deliberation
audience: owner
status: watch
signal: watch
score: 82
priority: High
tags: [council, deliberation, host-feedback, blind-delphi, intake]
---

# Council — Host Feedback First Deliberation (TASK-AR-527)

First run of the host-feedback intake deliberation (blind Delphi): five independent
viewpoints evaluated the four triaged candidates (529/530/531/532) without seeing
each other first, then synthesis. This is the consumption end of the intake pipeline
(GH #131) proving it runs.

## Bottom Line

- Summary: the council recommends ACCEPT for all four candidates but with material
  scope changes the deliberation itself surfaced — not the candidates as written.
- Result: 529 ACCEPT P1 (split); 531 ACCEPT but SPLIT (wheel sub-gap is the real P1
  live blocker, work_cli REJECTED as already-built); 532 ACCEPT P1 VERIFY-FIRST
  (#21/#20 appear already fixed in v0.2.0); 530 ACCEPT STAGED P2 (build the metric
  harness; keep the RSI self-mutation gate advisory/deferred).
- Boundary: this is a recommendation + priority SIGNAL. The Owner alone sets product
  direction; safety/order is a human (R3); votes never decide direction.

## Signal

| Candidate | Verdict | Priority | Council synthesis |
| --- | --- | --- | --- |
| 529 footprint post-verify (#125) | ACCEPT (split) | P1 | Adopt the read-only post-hoc `actual ⊄ declared` check now (diff vs wave merge-base, not worktree HEAD). DEFER the undeclared watch→BLOCK flip behind an `--enforce-undeclared` flag — flipping it breaks a locked test + stalls the Stop-hook gate chain. |
| 530 self-eval + RSI gate (#128) | ACCEPT (staged) | P2 | Build the held-out fixed/variable metric HARNESS (additive, safe). Keep the RSI self-mutation fitness gate ADVISORY/report-only until a trustworthy, variance-aware baseline exists + R3 sign-off (Goodhart/over-fit risk; it gates the safety-sensitive self-modification surface). |
| 531 host-fit gaps (#121) | ACCEPT (split) | P1 wheel / P3 rest | Wheel-dotfile packaging is a CONFIRMED live blocker (empirical wheel build: 0 of 4 template dotfiles ship) → P1 now, with a built-wheel content assertion. status l10n P3 (alias-additive). read-location = doc-only (substrate `unmanaged_paths` exists). REJECT work_cli (#3): `scripts/work.py` already is the scaffolder. |
| 532 open bugs (#19/#20/#21) | ACCEPT (verify-first) | P1 | #21 cp949 + #20 stale-config appear ALREADY mitigated in v0.2.0 (`sync.py _print_output errors="replace"`, `cli.py` stdout reconfigure, `build_sync_plan` TypeError guard) → reproduce-on-cp949, confirm, add regression tests, reply-back. Fold #19 doc-links into the 531 wheel fix (same root cause). |

## Action

| # | Action | Owner boundary |
| --- | --- | --- |
| 1 | Adopt 529 post-hoc check (W3); defer the hard block behind a flag | local |
| 2 | Adopt 531 wheel packaging (W3) with built-wheel assertion; reject work_cli; descope rest | local |
| 3 | Adopt 532 as verify-first: repro #21/#20 on cp949, regression tests, reply-back | local; external reply-back = owner_review |
| 4 | Build 530 metric harness; keep RSI mutation gate advisory until baseline + R3 | owner_review (direction) |
| 5 | Reply verdicts back to GH #121/#125/#128 + #19/#20/#21 (TASK-AR-528) | owner_review (external post) |

## Risk

- 529 watch→block as written breaks `test_undeclared_footprint_is_watch_not_fail` and the governance Stop-hook chain — MUST be flag-gated, not default.
- 530 fitness gate is the highest-risk, lowest-reversibility item: gating self-mutation on a noisy/gameable metric can rubber-stamp drift or block real gains. Advisory-first is mandatory.
- Candidate severity labels were STALE (minority concern, user-impact + skeptic): acting on "#21 is a live HIGH crash" would re-fix solved code and misinform priority. The real live blocker is packaging (531 wheel), originally mislabeled P2.
- 531 packaging changes what ships to ALL hosts — regression risk; reuse AR-511, do not re-author.

## Decision

- Decision: ACCEPT 529 (P1, split), 531-wheel (P1) + 531-l10n (P3), 532 (P1, verify-first); ACCEPT-STAGED 530 (P2 harness, gate advisory); REJECT 531 work_cli (#3, already exists).
- Decision: defer both hard enforcers (529 BLOCK flip, 530 RSI gate) behind flags/advisory mode until cheap reversible wins land and a baseline exists.
- Decision: queue statuses updated in `HOST-FEEDBACK-QUEUE.json` to reflect these verdicts; reply-back (TASK-AR-528) carries them to the issues after Owner approval of external posting.
- Minority preserved: the systems-thinker rated 530 the single highest-LEVERAGE item (P0) as the RSI fitness function; honored by ACCEPTING the harness now while deferring only the enforcing gate.

## Participating Viewpoints (blind-Delphi raw positions)

Five independent viewpoints evaluated each candidate BEFORE synthesis; the raw
spread is preserved for auditability (this is the blind-Delphi stage, not the
synthesized verdict above).

| Viewpoint | 529 | 530 | 531 | 532 |
| --- | --- | --- | --- | --- |
| skeptic | ACCEPT P1 | DEFER P2 | ACCEPT (wheel P1; REJECT work_cli) | ACCEPT P1 (#21 verify-first) |
| pragmatist | ACCEPT P1 | DEFER P3 | DEFER P2 | ACCEPT P0 |
| systems-thinker | ACCEPT P1 | ACCEPT P0 | ACCEPT P2 | ACCEPT P2 (#21 P1) |
| user-impact-reviewer | ACCEPT P1 | ACCEPT P1 (staged) | ACCEPT P0 wheel / P2 rest | ACCEPT P1 (verify-first) |
| stabilizer | ACCEPT P1 / DEFER P3 (block flip) | DEFER P2 | ACCEPT P2 | ACCEPT P1 |

- Divergence endpoints (preserved, not averaged away): 530 ranged **P0** (systems-thinker — the single highest-leverage item, the RSI fitness function) to **P3** (pragmatist — largest + a host-data dependency it cannot control). Synthesis landed P2: adopt the harness now, defer the enforcing gate — honoring both ends.
- 529 was near-unanimous ACCEPT P1; the only split was stabilizer carving the watch→block flip out to DEFER (which the synthesis adopted).

## Unresolved Assumptions

- 532 #21/#20 are assumed already-fixed in v0.2.0 from code inspection; UNVERIFIED on a live cp949 console — verify-first before claiming closed.
- 530 fitness-gate viability assumes a constructable held-out workset + a stable variance band; both unproven — gate stays advisory until demonstrated.
- 531 wheel fix assumes dot-path enumeration / MANIFEST.in captures all four dotfile subtrees — must be re-verified with a built-wheel content assertion.

## Evidence References

- `scripts/work.py` (scaffolder already exists → 531 work_cli REJECT); `src/agent_runtime/sync.py` (`_print_output` `errors="replace"`; `build_sync_plan` TypeError guard); `src/agent_runtime/cli.py` (stdout reconfigure → 532 verify-first); `tests/test_footprint_conflict_gate.py` (locked `test_undeclared_footprint_is_watch_not_fail` → 529 block deferred); empirical wheel build (0/4 dotfiles ship → 531 wheel confirmed live).

## Next

- W3 execution order (cheapest/safest first): 532 (verify #21/#20 + #19 with wheel) → 531 wheel → 529 post-hoc check → 530 harness (advisory gate).
- TASK-AR-528 posts these verdicts to the GitHub issues once the Owner approves external reply-back.
- Re-run this council for the next intake batch; it is the repeatable consumption end of the pipeline.
