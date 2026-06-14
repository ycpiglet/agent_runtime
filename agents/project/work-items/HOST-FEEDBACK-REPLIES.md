---
type: host_feedback_replies
id: HOST-FEEDBACK-REPLIES
audience: owner
---

# Host Feedback Reply-Back Drafts (TASK-AR-528)

## GH #19

**agent_runtime — host-feedback intake decision**

This feedback was run through the host-feedback intake pipeline (GH #131): triaged, deliberated by a blind-Delphi diversity council, and a verdict recorded. Deliberation record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.

- **Decision: ACCEPTED** (priority P3) — tracked as TASK-AR-532, TASK-AR-531.
  - ACCEPT: same unshipped-dotfile root cause as the 531 wheel gap; fix WITH the wheel packaging work, not separately.

Guardrails: this is a recommendation + priority signal; product direction stays with the Owner, safety/order with a human (R3).

## GH #20

**agent_runtime — host-feedback intake decision**

This feedback was run through the host-feedback intake pipeline (GH #131): triaged, deliberated by a blind-Delphi diversity council, and a verdict recorded. Deliberation record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.

- **Decision: ACCEPTED** (priority P2) — tracked as TASK-AR-532.
  - ACCEPT (verify-first): build_sync_plan already has a TypeError path-like guard in v0.2.0; add the stale-config AttributeError guard + a regression test, then reply-back.

Guardrails: this is a recommendation + priority signal; product direction stays with the Owner, safety/order with a human (R3).

## GH #21

**agent_runtime — host-feedback intake decision**

This feedback was run through the host-feedback intake pipeline (GH #131): triaged, deliberated by a blind-Delphi diversity council, and a verdict recorded. Deliberation record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.

- **Decision: ACCEPTED** (priority P1) — tracked as TASK-AR-532.
  - ACCEPT (verify-first): appears already mitigated in v0.2.0 (sync.py _print_output errors='replace'; cli.py stdout reconfigure). Reproduce on a cp949 console, confirm where it still throws, add a regression test, reply-back. Do NOT blindly re-fix solved code.

Guardrails: this is a recommendation + priority signal; product direction stays with the Owner, safety/order with a human (R3).

## GH #121

**agent_runtime — host-feedback intake decision**

This feedback was run through the host-feedback intake pipeline (GH #131): triaged, deliberated by a blind-Delphi diversity council, and a verdict recorded. Deliberation record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.

- **Decision: ACCEPTED** (priority P1) — tracked as TASK-AR-531.
  - ACCEPT (split): wheel-dotfile packaging is a CONFIRMED live blocker -> P1 now (empirical: 0/4 dotfiles ship). status l10n P3 (alias-additive). read-location = doc-only. REJECT work_cli sub-gap (scripts/work.py already is the scaffolder).

Guardrails: this is a recommendation + priority signal; product direction stays with the Owner, safety/order with a human (R3).

## GH #125

**agent_runtime — host-feedback intake decision**

This feedback was run through the host-feedback intake pipeline (GH #131): triaged, deliberated by a blind-Delphi diversity council, and a verdict recorded. Deliberation record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.

- **Decision: ACCEPTED** (priority P1) — tracked as TASK-AR-529.
  - ACCEPT (split): adopt read-only post-hoc actual-vs-declared check now (diff vs wave merge-base); DEFER the undeclared watch->BLOCK flip behind an --enforce-undeclared flag (breaks a locked test + stalls the Stop-hook chain).

Guardrails: this is a recommendation + priority signal; product direction stays with the Owner, safety/order with a human (R3).

## GH #128

**agent_runtime — host-feedback intake decision**

This feedback was run through the host-feedback intake pipeline (GH #131): triaged, deliberated by a blind-Delphi diversity council, and a verdict recorded. Deliberation record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.

- **Decision: ACCEPTED** (priority P2) — tracked as TASK-AR-530.
  - ACCEPT (staged): build the held-out fixed/variable metric HARNESS; keep the RSI self-mutation fitness gate ADVISORY/report-only until a trustworthy variance-aware baseline + R3 sign-off (Goodhart/over-fit risk). Minority: systems-thinker rated this the highest-leverage item (P0).

Guardrails: this is a recommendation + priority signal; product direction stays with the Owner, safety/order with a human (R3).

## GH #131

**agent_runtime — host-feedback intake decision**

This feedback was run through the host-feedback intake pipeline (GH #131): triaged, deliberated by a blind-Delphi diversity council, and a verdict recorded. Deliberation record: `reviews/COUNCIL-2026-06-14-host-feedback-first-deliberation.md`.

- **Decision: ACCEPTED** (priority P1) — tracked as TASK-AR-526, TASK-AR-527, TASK-AR-528.
  - ACCEPT — the intake->deliberate->reply-back pipeline itself; built via 526/527/528 (526 + this deliberation are done).

Guardrails: this is a recommendation + priority signal; product direction stays with the Owner, safety/order with a human (R3).
