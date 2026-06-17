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

## Growth Automation Boundary

- Allowed: owned-channel scheduled posts, approved API posting, consent-based CRM follow-up, SEO/content analysis, and campaign performance reporting.
- Prohibited: viewbots, fake traffic, fake engagement, unauthorized bulk posting, spam, terms-of-service evasion, platform manipulation, and unsourced lead scraping.
