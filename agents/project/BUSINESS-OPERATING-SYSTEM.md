# Business Operating System

## Purpose

This packet turns business-side work into repeatable agent-runtime cycles. It
covers finance/accounting, marketing/growth, sales/revenue,
operations/support, and planning/strategy work without letting agents skip the
normal work lifecycle or mutate external systems.

Lane-specific execution packets live in:
`agents/project/WORK-LANE-PLAYBOOKS.md`.

## Lanes

| Lane | Lead role | Worker roles | Reviewer roles | Owns |
| --- | --- | --- | --- | --- |
| finance-accounting | finance-controller | accounting-operator | asset-steward, revenue-analyst | pricing, billing policy, cost evidence, vendor/license inventory, revenue assumptions |
| marketing-growth | marketing-lead | content-marketer | growth-analyst, brand-steward | positioning, content drafts, SEO, campaign analysis, approved claim banks |
| sales-revenue | sales-lead | crm-operator | sales-ops, partnership-manager | ICP, lead qualification, proposal/demo packets, CRM hygiene drafts, partnership prep |
| operations-support | operations-lead | support-operator | customer-success-steward, process-steward | runbooks, support-response drafts, issue triage, SLA/quality checks, process improvement |
| planning-strategy | strategy-lead | business-analyst | planning-architect, portfolio-steward | strategy options, requirements, prioritization, next taskset decomposition, roadmap fit |

## Cycle Contract

Every non-trivial business cycle uses the standard W0-W6 lifecycle and records
these artifacts before claiming completion:

1. `review`: planning or implementation decision record under `reviews/`.
2. `seminar`: multi-role argument, objections, and decision notes.
3. `scribe`: concise timeline of claims, files, commands, and evidence.
4. `doc-steward review`: source-of-truth and index hygiene check.
5. `compound`: reusable lesson or failure-prevention note.
6. `retro`: what to repeat, stop, or register as the next taskset.
7. `W4 evidence`: command output, browser/API evidence, or deterministic gate result.

If a cycle discovers adjacent work, the agent registers it through
`python scripts/work.py new --input <json>` instead of editing outside the
claimed unit.

## Role Routing

- Strategy questions go to `strategy-lead` first, then `planning-architect`
  turns decisions into `initiative -> taskset -> task -> unit` records.
- Requirements, KPI, market, or customer insight synthesis goes to
  `business-analyst` and must name sources and assumptions.
- Operating runbooks, support drafts, and process cleanup go to
  `operations-lead` and `process-steward`.
- Support replies are draft-only until Owner approval; no support desk or
  outbound message mutation is allowed by default.
- CRM and sales follow-up are draft-only unless the Owner approves the exact
  target, channel, message, and safety review.
- Finance/accounting work may organize evidence and propose policies but must
  not write to external accounting, banking, tax, payment, or billing systems.

## Safe External-Effect Boundary

Agents may prepare drafts, packets, checklists, reports, and local verification
evidence. The following require explicit Owner approval and risk review:

- writing to accounting, billing, bank, tax, payment, CRM, support desk, email,
  messaging, social, marketplace, or advertising systems;
- contacting a customer, lead, partner, regulator, vendor, or platform account;
- changing prices, contract terms, payment links, invoices, subscriptions, or
  refund state;
- scraping leads, sending bulk messages, generating fake traffic/engagement,
  evading terms of service, or manipulating platform signals;
- running unsupported automation outside the active task unit.

## Next-Taskset Pattern

Use this sequence for repeated cycles:

1. Read this packet, `agents/project/ORG.md`, `agents/project/TEAMS.md`, and
   the relevant prior review/retro.
2. Run W0 visibility and confirm there is no active claim for the same target.
3. Register the smallest next taskset with explicit acceptance criteria,
   target files, verification commands, and handoff format.
4. Claim one worker-ready unit and implement only that unit.
5. Verify with the recorded commands and independent W4b evidence when the
   claim is released.
6. Regenerate indexes/boards and write retro/compound notes for the next cycle.

## Completion Checklist

- [ ] Current task/unit record says what is in and out of scope.
- [ ] Review, seminar, scribe, doc-steward, compound, retro, and W4 evidence
      are linked from the handoff.
- [ ] No external system was mutated without Owner approval.
- [ ] Next taskset candidates are registered or explicitly deferred.
- [ ] `taskset_work_gate`, org model checks, and relevant focused tests pass.
