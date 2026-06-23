# Work Lane Playbooks

Companion to `agents/project/BUSINESS-OPERATING-SYSTEM.md`. That packet defines
the cross-cutting cycle contract and safety boundary; **this file gives the
per-lane operating procedure** — how each business lane turns a request into
safe, draft-only deliverables.

These playbooks describe **process and deliverable shape only**. The actual
business content (prices, contract terms, marketing claims, strategy bets,
customer-facing copy) is the **Owner's decision** and is marked
`OWNER-DECIDES` throughout. Agents produce the structure, evidence, and options;
the Owner approves the substance and any external effect.

## How to use

1. Read `BUSINESS-OPERATING-SYSTEM.md` (cycle contract + safe-effect boundary).
2. Find the lane below that owns the request.
3. Follow that lane's **intake → draft → review → evidence** steps.
4. Stop at the lane's escalation triggers; never cross the safe-effect boundary
   without recorded Owner approval.

## Shared lane procedure

Every lane runs the same skeleton on top of the W0–W6 lifecycle:

| Step | What | Output |
| --- | --- | --- |
| Intake | Confirm the request maps to this lane; check no active claim on the target | claim + scope note |
| Draft | Produce the deliverable as a **draft artifact** under the repo (no external write) | draft file(s) in `reviews/` or `agents/project/` |
| Review | Lead + reviewer roles check accuracy, boundary, and `OWNER-DECIDES` markers | seminar / review record |
| Evidence | Record commands, sources, and a W4 evidence note | `reviews/VERIFY-*` / scribe |
| Handoff | Link review/seminar/scribe/compound/retro; mark Owner-approval items | handoff + retro |

Cross-boundary actions (send, publish, charge, contact, mutate external system)
are **never** part of a lane's normal output — they are a separate, explicit
Owner-approved step.

---

## Lane: finance-accounting

- **Roles:** finance-controller (lead) · accounting-operator (worker) · asset-steward, revenue-analyst (reviewers)
- **Owns:** pricing, billing policy, cost evidence, vendor/license inventory, revenue assumptions.

**Intake triggers:** pricing/packaging question, cost or margin analysis, vendor/license
review, revenue/LTV/CAC modeling, billing-policy drafting.

**Draft deliverables (structure only — `OWNER-DECIDES` the numbers):**
- Pricing/packaging **option table** (tiers, axes, trade-offs) — values `OWNER-DECIDES`.
- Cost-evidence sheet: line items + sources; no estimates without a cited source.
- Vendor/license inventory: tool, plan, owner, renewal — secret values **never** inlined.
- Revenue assumption set: each assumption names its source and confidence.

**Allowed:** organize evidence, propose policies, build models with explicit sources.
**Escalate to Owner (do not perform):** any write to accounting/billing/bank/tax/payment
systems, price/contract/invoice/subscription/refund changes, payment-link creation.

---

## Lane: marketing-growth

- **Roles:** marketing-lead (lead) · content-marketer (worker) · growth-analyst, brand-steward (reviewers)
- **Owns:** positioning, content drafts, SEO, campaign analysis, approved claim banks.

**Intake triggers:** positioning/messaging request, content/SEO drafting, campaign
or funnel analysis, claim-bank curation.

**Draft deliverables (structure only):**
- Positioning/messaging draft — final claims `OWNER-DECIDES`; brand-steward blocks overstatement.
- **Approved-claim bank**: each claim paired with its evidence/source; unverifiable claims flagged.
- Owned-channel content drafts (blog/docs/SEO) — scheduled only after Owner approval.
- Campaign/funnel analysis with real metrics only.

**Allowed:** draft owned-channel content, analyze campaigns, propose channels.
**Escalate to Owner (do not perform):** bulk/unauthorized posting, paid-ad or social/marketplace
writes, fake traffic/engagement, ToS evasion, any platform-signal manipulation.

---

## Lane: sales-revenue

- **Roles:** sales-lead (lead) · crm-operator (worker) · sales-ops, partnership-manager (reviewers)
- **Owns:** ICP, lead qualification, proposal/demo packets, CRM hygiene drafts, partnership prep.

**Intake triggers:** ICP/qualification definition, proposal/demo prep, CRM hygiene,
partnership candidate research.

**Draft deliverables (structure only):**
- ICP + qualification rubric (firmographic/behavioral signals) — thresholds `OWNER-DECIDES`.
- Proposal/demo packet **template** — pricing & commitments `OWNER-DECIDES`.
- CRM hygiene draft: dedup/stage-cleanup plan against a **consent-based** list only.
- Partnership candidate brief: fit, mutual value, risks — no outreach attached.

**Allowed:** draft qualification logic, packets, and consent-based CRM workflow plans.
**Escalate to Owner (do not perform):** any CRM/email/messaging write, unsolicited outreach
or spam, lead scraping, contract/commitment to a partner, deal-desk price changes.

---

## Lane: operations-support

- **Roles:** operations-lead (lead) · support-operator (worker) · customer-success-steward, process-steward (reviewers)
- **Owns:** runbooks, support-response drafts, issue triage, SLA/quality checks, process improvement.

**Intake triggers:** new/updated runbook, support-response drafting, issue triage,
SLA/quality review, process-improvement proposal.

**Draft deliverables (structure only):**
- Operating runbook: trigger → steps → checks → escalation.
- Support-response **templates** by issue class — `OWNER-DECIDES` any commitment/SLA promise.
- Triage rubric: severity, routing, response-time targets (targets `OWNER-DECIDES`).
- Activation/retention risk analysis — no customer commitment implied.

**Allowed:** draft runbooks/templates, triage, analyze activation/retention, propose process changes.
**Escalate to Owner (do not perform):** sending any support reply, support-desk mutation,
customer commitment/refund/credit, external system writes; workflow changes need a review record.

---

## Lane: planning-strategy

- **Roles:** strategy-lead (lead) · business-analyst (worker) · planning-architect, portfolio-steward (reviewers)
- **Owns:** strategy options, requirements, prioritization, next-taskset decomposition, roadmap fit.

**Intake triggers:** strategy/direction question, requirements/KPI synthesis,
prioritization/roadmap fit, decomposition of an approved direction into work.

**Draft deliverables (structure only):**
- Strategy **option set**: options, trade-offs, risks — the chosen bet is `OWNER-DECIDES`.
- Requirements/KPI brief: each item names sources and assumptions.
- Prioritization proposal: scoring rubric + ranking — no arbitrary reprioritization.
- Decomposition: `initiative → taskset → task → unit` records via `scripts/work.py new`
  (planning-architect; never claim-less implementation).

**Allowed:** draft options, requirements, prioritization, and decomposition records.
**Escalate to Owner (do not perform):** committing a strategic direction, investment, or
roadmap reorder as final; any external announcement of strategy.

---

## Cross-lane handoff & escalation

- A request that spans lanes is split by `strategy-lead`/`planning-architect` into
  per-lane units; each unit is claimed and worked independently.
- Any deliverable that reaches the **safe-effect boundary** stops and is handed to the
  Owner with: the draft, the exact external action requested, and a risk note.
- Brand/legal/compliance risk (marketing/sales) escalates to `brand-steward` then Owner.

## Per-lane completion checklist

- [ ] Deliverable is a **draft artifact in-repo**; no external system was mutated.
- [ ] Every business value is either evidenced (with source) or marked `OWNER-DECIDES`.
- [ ] Lane lead + reviewer roles signed off; seminar/review recorded.
- [ ] W4 evidence + scribe linked from the handoff.
- [ ] Owner-approval items listed explicitly and left **unexecuted**.
- [ ] Next taskset candidates registered or deferred; indexes regenerated.
