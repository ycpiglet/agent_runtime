# Teams Template (Host Overlay)

## Team Registry

- team_id: product-core
  purpose: Build and verify the core MVP loop.
  lead: lead-engineer
  roles:
    - lead-engineer
    - backend
    - uiux
    - qa
  canonical_context:
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/ORG.md

- team_id: governance
  purpose: Keep decisions, risks, and handoff records consistent.
  lead: managing-partner
  roles:
    - managing-partner
    - independent-auditor
    - doc-steward
    - scribe
  canonical_context:
    - agents/project/ORG.md
    - agents/project/LINKS.md

- team_id: finance-accounting
  purpose: Own monetization, pricing, billing, costs, assets, licenses, vendors, and revenue metrics.
  lead: finance-controller
  roles:
    - finance-controller
    - accounting-operator
    - asset-steward
    - revenue-analyst
  canonical_context:
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/ORG.md

- team_id: marketing-growth
  purpose: Own positioning, brand messaging, content calendar, SEO, campaigns, channel experiments, and performance analysis.
  lead: marketing-lead
  roles:
    - marketing-lead
    - content-marketer
    - growth-analyst
    - brand-steward
  canonical_context:
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/LINKS.md

- team_id: sales-revenue
  purpose: Own ICP, lead qualification, CRM pipeline, demos, proposals, partnerships, and compliant promotional operations.
  lead: sales-lead
  roles:
    - sales-lead
    - crm-operator
    - partnership-manager
    - sales-ops
  canonical_context:
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/VISION.md
    - agents/project/ROADMAP.md
    - agents/project/ORG.md

- team_id: operations-support
  purpose: Own operating runbooks, customer/support packets, issue triage, response quality, and internal process improvement.
  lead: operations-lead
  roles:
    - operations-lead
    - support-operator
    - customer-success-steward
    - process-steward
  canonical_context:
    - agents/project/BUSINESS-OPERATING-SYSTEM.md
    - agents/project/PROJECT-CONTEXT.yml
    - agents/project/ORG.md
    - agents/project/ROADMAP.md

- team_id: planning-strategy
  purpose: Own business strategy, prioritization, task decomposition, requirements analysis, and roadmap/portfolio coherence.
  lead: strategy-lead
  roles:
    - strategy-lead
    - planning-architect
    - business-analyst
    - portfolio-steward
  canonical_context:
    - agents/project/BUSINESS-OPERATING-SYSTEM.md
    - docs/superpowers/plans/
    - agents/project/work-items/WORK-ITEM-CLASSIFICATION.md
    - reviews/

## Growth Automation Boundary

- Allowed: owned-channel scheduled posts, approved API posting, consent-based CRM follow-up, SEO/content analysis, and campaign performance reporting.
- Prohibited: viewbots, fake traffic, fake engagement, unauthorized bulk posting, spam, terms-of-service evasion, platform manipulation, and unsourced lead scraping.
