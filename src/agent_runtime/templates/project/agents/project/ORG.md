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

## Growth Automation Boundary

- allowed: owned-channel scheduled posting, approved API posting, consent-based CRM follow-up, SEO/content analysis, campaign performance reporting
- prohibited: viewbots, fake traffic, fake engagement, unauthorized bulk posting, spam, terms-of-service evasion, platform manipulation, unsourced lead scraping
- escalation: Any automation that writes to an external account or contacts customers/leads requires Owner approval and risk review.

## Escalation Policy

- escalation_condition: missing overlay, rule conflict, unresolved authority, external account write, contract/payment mutation, platform manipulation request, or spam-like growth automation request
- response_deadline: 1 business day
- emergency_owner: owner
