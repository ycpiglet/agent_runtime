# Business Operating System

## Purpose

Use this packet when a host project asks agents to continue finance,
marketing, sales, operations, support, planning, or strategy work across
multiple cycles. The packet keeps business work useful while preserving the
claim/worktree lifecycle and preventing unapproved external effects.

Lane-specific operating packets are in:
`agents/project/WORK-LANE-PLAYBOOKS.md`.

## Lanes

| Lane | Lead role | Worker roles | Reviewer roles | Owns |
| --- | --- | --- | --- | --- |
| finance-accounting | finance-controller | accounting-operator | asset-steward, revenue-analyst | pricing, billing policy, cost evidence, vendor/license inventory, revenue assumptions |
| marketing-growth | marketing-lead | content-marketer | growth-analyst, brand-steward | positioning, content drafts, SEO, campaign analysis, approved claim banks |
| sales-revenue | sales-lead | crm-operator | sales-ops, partnership-manager | ICP, lead qualification, proposal/demo packets, CRM hygiene drafts, partnership prep |
| operations-support | operations-lead | support-operator | customer-success-steward, process-steward | runbooks, support-response drafts, issue triage, SLA/quality checks, process improvement |
| planning-strategy | strategy-lead | business-analyst | planning-architect, portfolio-steward | strategy options, requirements, prioritization, next taskset decomposition, roadmap fit |

## Required Artifacts

Before a non-trivial business cycle claims completion, it must link:

1. `review`
2. `seminar`
3. `scribe`
4. `doc-steward review`
5. `compound`
6. `retro`
7. `W4 verification evidence`

Adjacent work discovered mid-cycle must be registered through
`python scripts/work.py new --input <json>` before implementation.

## Safety Boundary

Agents may prepare local drafts, reports, packets, checklists, and evidence.
Owner approval and risk review are required before any write to accounting,
billing, bank, tax, payment, CRM, support desk, email, messaging, social,
marketplace, or advertising systems; before any customer/lead/partner contact;
and before any price, contract, payment, invoice, subscription, or refund
mutation.

Scraping leads, sending spam, generating fake traffic or engagement, evading
terms of service, manipulating platform signals, and running unsupported automation outside the active task unit are prohibited.
