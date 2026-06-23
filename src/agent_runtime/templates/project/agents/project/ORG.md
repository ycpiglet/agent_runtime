# Organization Template (Host Overlay)

## Ownership

- product_owner: owner
- decision_owner: lead-engineer
- escalation_owner: managing-partner
- review_owner: independent-auditor

## Team Structure

- product_core:
  - owner
  - lead-engineer
  - backend
  - uiux
  - qa
- governance:
  - managing-partner
  - independent-auditor
  - doc-steward
  - scribe
- finance_accounting:
  - finance-controller
  - accounting-operator
  - asset-steward
  - revenue-analyst
- marketing_growth:
  - marketing-lead
  - content-marketer
  - growth-analyst
  - brand-steward
- sales_revenue:
  - sales-lead
  - crm-operator
  - partnership-manager
  - sales-ops
- operations_support:
  - operations-lead
  - support-operator
  - customer-success-steward
  - process-steward
- planning_strategy:
  - strategy-lead
  - planning-architect
  - business-analyst
  - portfolio-steward

## Authority and Access

- access_rules:
  - role: owner
    level: secret
    boundary: Final approval for public release, external account writes, contracts, and payment mutations.
  - role: lead-engineer
    level: confidential
    boundary: Product implementation planning, task packaging, and technical integration.
  - role: finance-controller
    level: confidential
    boundary: Pricing, monetization model, billing policy, cost model, and revenue KPI proposals.
  - role: accounting-operator
    level: confidential
    boundary: Books, billing records, accounts receivable/payable, and cost evidence; no external accounting-system writes without approval.
  - role: asset-steward
    level: internal
    boundary: SaaS accounts, licenses, content/data assets, and vendor inventory; never expose secrets.
  - role: revenue-analyst
    level: internal
    boundary: Revenue, conversion, LTV/CAC, and usage-based pricing analysis with explicit assumptions.
  - role: marketing-lead
    level: internal
    boundary: Positioning, messaging, campaign strategy, and channel priorities.
  - role: content-marketer
    level: internal
    boundary: Owned-channel content drafts, SEO drafts, and scheduled-post packages; no unauthorized bulk posting.
  - role: growth-analyst
    level: internal
    boundary: Funnel, campaign, and channel analysis; fake traffic or fake engagement is prohibited.
  - role: brand-steward
    level: internal
    boundary: Brand consistency, trust risk, claims review, and exaggeration checks.
  - role: sales-lead
    level: confidential
    boundary: ICP, lead prioritization, proposals, demos, sales strategy, and deal handoff.
  - role: crm-operator
    level: confidential
    boundary: Consent-based CRM hygiene, follow-up scheduling, and pipeline status; no scraping or spam.
  - role: partnership-manager
    level: confidential
    boundary: Partner candidates, partnership proposals, and joint-campaign preparation; no external commitments without approval.
  - role: sales-ops
    level: internal
    boundary: Sales process, CRM hygiene, reporting, and handoff quality; no revenue metric manipulation.
  - role: operations-lead
    level: internal
    boundary: Operating runbooks, support routing, cycle cadence, and handoff quality; no external-system writes without approval.
  - role: support-operator
    level: confidential
    boundary: User/customer issue triage, support-response drafts, and repro notes; no direct customer send or support-desk mutation.
  - role: customer-success-steward
    level: confidential
    boundary: Onboarding, activation, retention-risk analysis, and success criteria; no commercial commitments.
  - role: process-steward
    level: internal
    boundary: Recurring process checklists and closeout quality; canonical workflow changes require review records.
  - role: strategy-lead
    level: confidential
    boundary: Business strategy, positioning direction, and investment priority proposals; Owner approves final strategic pivots.
  - role: planning-architect
    level: internal
    boundary: Initiative/taskset/task/unit decomposition and worker-ready criteria; no implementation without claim/worktree.
  - role: business-analyst
    level: internal
    boundary: Requirements, KPI, market/customer insight synthesis with explicit source and assumption notes.
  - role: portfolio-steward
    level: internal
    boundary: Roadmap/portfolio priority and duplicate taskset coordination; no unapproved reprioritization.

## Growth Automation Boundary

- allowed: owned-channel scheduled posting, approved API posting, consent-based CRM follow-up, SEO/content analysis, campaign performance reporting
- prohibited: viewbots, fake traffic, fake engagement, unauthorized bulk posting, spam, terms-of-service evasion, platform manipulation, unsourced lead scraping
- escalation: Any automation that writes to an external account or contacts customers/leads requires Owner approval and risk review.

## Business Operating Cycle Boundary

- required_artifacts: review, seminar, scribe, doc-steward review, compound, retro, W4 verification evidence
- cycle_rule: Read `agents/project/BUSINESS-OPERATING-SYSTEM.md` first, register new work through `work.py new`, then execute only inside a claimed worktree.
- external_effects: Accounting systems, CRM, support desks, email/messaging, payments, contracts, and external posting accounts are read-only or draft-only until Owner approval and risk review.

## Escalation Policy

- escalation_condition: missing overlay, rule conflict, unresolved authority, direct customer contact, support desk mutation, external account write, contract/payment mutation, platform manipulation request, or spam-like growth automation request
- response_deadline: 1 business day
- emergency_owner: owner
