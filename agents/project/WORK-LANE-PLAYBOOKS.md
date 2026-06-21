# Business Work Lane Playbooks

This packet provides concrete execution templates for the 5 business lanes
defined in `agents/project/BUSINESS-OPERATING-SYSTEM.md`.

## Scope

- Scope: documentation and local planning only. No CRM/accounting/payment/billing/communication
system writes, no customer contact, and no external campaign execution.
- Boundary: this packet is SSoT for cycle-ready lane scopes and evidence expectations.

## Shared Inputs (all lanes)

- `agents/project/BUSINESS-OPERATING-SYSTEM.md`
- `agents/project/ORG.md`
- `agents/project/TEAMS.md`
- `agents/project/PROJECT-CONTEXT.yml`
- Prior reviews/retros/scribes relevant to the same lane

## Shared Required Artifacts (all lanes)

- `review` decision record (under `reviews/`)
- `seminar` notes when assumptions/risks are non-trivial
- `scribe` handoff trace
- `doc-steward` consistency check
- `compound` reusable lesson
- `retro` for next-cycle handoff
- W4 evidence command output or deterministic gate result

## Finance-Accounting Playbook

- **Owner/owner roles:** `finance-controller` / `accounting-operator`
- **Reviewers:** `asset-steward`, `revenue-analyst`

### Scope In
- Build or maintain local pricing/cost evidence models.
- Define revenue assumptions, margin guardrails, and unit-economics analysis structure.
- Prepare billing-policy drafts and external-effect preconditions.

### Scope Out
- Billing system writes, tax filing, invoice dispatch, payment link changes.
- Direct subscription/contract mutation.

### Inputs
- Team-level assumptions and prior revenue KPIs
- Vendor/license list and cost inputs (internal drafts)
- Previous `review` decisions and W4 evidence

### Required Outputs
- `finance-evidence-packet.md` (draft)
- `pricing-assumption-matrix` (draft)
- External-effect risk checklist

### Cadence
- Start at planning boundary.
- Deliver draft packet within one business cycle.
- Hand off only after review + scribe + doc-steward are recorded.

### Decision Trigger
- If pricing/cost assumptions affect roadmaps or external contracts,
register a follow-up taskset for explicit Owner approval and risk review.

### Safety Constraints
- Do not perform accounting writes, billing changes, or tax/payment updates.
- Do not change external pricing/contract state without explicit Owner approval.

#### Finance-Evidence Draft Packet (Draft-only)

- **Owner/owner roles:** `finance-controller` / `accounting-operator`
- **Packet status:** `draft-only` (no pricing/cost stateful writes; no billing mutation)
- **Decision owner:** `lead_engineer` + `finance-controller`, with risk review.

##### Draft Artifact Schema

- `finance-evidence-packet.md`
  - `revenue_model`: `to-be-defined`
  - `unit_pricing`: `to-be-defined`
  - `target_margin_min`: `35%`
  - `pricing_decision_status`: `draft`
- `pricing-assumption-matrix`
  - `assumptions`: explicit `[volume, churn, discount]` entries
  - `sensitivity_plan`: `[low, base, high]` scenario matrix
  - `verified_status`: `draft-only`
- `external-effect-risk-checklist`
  - `contract_mutation_guard`: `owner_approval_required`
  - `payment_link_guard`: `no_direct_change`
  - `customer_impact_guard`: `owner_approved`

##### Decision Triggers

- If pricing/cost assumptions move outside ±10% versus prior quarter, register
  `TASKSET-AR-BUSINESS-LANES-FINANCE-IMPLEMENTATION-RECALIBRATE`.
- If contract terms, payment links, or subscription states are required, register a
  separate Owner-approved implementation taskset before execution.

### Next Taskset Candidates
- `FINANCE-PLAN-IMPLEMENTATION` (pricing policy rollout packet)
- `COST-EVIDENCE-TRACKING` (actual cost capture and variance review)

## Marketing-Growth Playbook

- **Owner/owner roles:** `marketing-lead` / `content-marketer`
- **Reviewers:** `growth-analyst`, `brand-steward`

### Scope In
- Define approved claim banks and campaign analysis structure.
- Produce SEO/content experiment hypotheses and market-positioning drafts.
- Prepare campaign-readiness packets for Owner review.

### Scope Out
- 광고 계정 직접 운영/배포, 대량 발송, 허위 트래픽/신호 조작.

### Inputs
- Product positioning notes and prior roadmap context
- Approved campaign channels list and constraints
- Prior seminar/review outputs

### Required Outputs
- `claim-bank-draft.md` (approved list of claims only)
- `campaign-analysis-notes.md` (hypothesis + metric targets)
- Channel-by-channel constraint matrix

### Cadence
- Cycle-by-cycle with weekly cadence check.
- Hold external channel actions until Owner and risk review approval.

### Decision Trigger
- If campaign execution is needed, register a dedicated implementation taskset for
channel execution with explicit approval gates.

### Safety Constraints
- No external messaging/광고 집행 by agent directly.
- No fabricated engagement, scraping, or unsupported automation.

#### Marketing Readiness Packet (Draft-only)

- **Owner/owner roles:** `marketing-lead` / `content-marketer`
- **Packet status:** `draft-only` (no external campaign dispatch; no ad platform writes)
- **Decision owner:** `lead_engineer` + `marketing-lead`, with `growth-analyst` review.

##### Draft Artifact Schema

- `claim-bank-draft.md`
  - `channel_plan`: `[search, seo, referral, partner]` ranked priority list
  - `claim_inventory`: list of approved claim statements with source links
  - `measurement_plan`: `[KPI, baseline, target, review_window]` fields
- `campaign-analysis-notes.md`
  - `audience_segment` hypothesis
  - `message_experiments` list
  - `budget_impact_proxy` (estimated, no budget write)
- `channel-risk-checklist`
  - `messaging_integrity`: `no_false_claims`
  - `channel_risk_level`: `low|mid|high`
  - `owner_approval_required`: `true` when outbound is planned

##### Decision Triggers

- If campaign execution is required, register `TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION-EXECUTION`.
- If any channel needs policy, contract, pricing, or payment-link change, register an Owner-approved
`TASKSET-AR-BUSINESS-LANES-MARKETING-GROWTH-IMPLEMENTATION-IMPACTS`.

### Next Taskset Candidates
- `MARKETING-CLAIM-BANK-OPERATIONS`
- `CAMPAIGN-READINESS-CHECKS`

## Sales-Revenue Playbook

- **Owner/owner roles:** `sales-lead` / `crm-operator`
- **Reviewers:** `sales-ops`, `partnership-manager`

### Scope In
- Prepare ICP, qualification notes, proposal/demo packet drafts.
- Draft CRM hygiene actions and partnership prep playbooks.

### Scope Out
- CRM writes, partner outreach, lead-contact messages, or price commitments.

### Inputs
- Sales funnel assumptions and team feedback
- Product capability constraints and risk boundary docs
- Prior business/legal decision records

### Required Outputs
- `icp-and-qualification-matrix.md`
- `proposal-demo-outline.md` (draft)
- `lead-handoff-checklist.md` (Owner handoff only)

### Cadence
- Triggered by inbound qualified demand signals or initiative planning updates.
- No external dispatch until explicit Owner approval.

### Decision Trigger
- If any external follow-up is needed, register a dedicated sales-ops taskset.

### Safety Constraints
- No outbound contact without approval.
- No contract or payment negotiation changes by default.

### Next Taskset Candidates
- `SALES-OUTBOUND-DRAFT-TO-IMPLEMENT`
- `PARTNERSHIP-REVIEW-PIPELINE`

## Operations-Support Playbook

- **Owner/owner roles:** `operations-lead` / `support-operator`
- **Reviewers:** `customer-success-steward`, `process-steward`

### Scope In
- Build runbook drafts, support templates, process-improvement packets.
- Define issue triage and SLA quality criteria for local execution.

### Scope Out
- 실시간 지원 데스크 처리, 고객 응답 발송, 외부 채널 메시지 발송.

### Inputs
- Customer-incident history (internal notes only)
- Process maps and policy constraints
- Prior retro/retro outputs for recurring failure classes

### Required Outputs
- `support-runbook-draft.md`
- `issue-triage-rules.md`
- `sla-quality-checklist.md`

### Cadence
- Update per recurring incident class and process review cycles.
- Keep drafts and evidence-only flow until approved by Owner and risk review.

### Decision Trigger
- If support draft proves stable for two cycles, register process-automation taskset.

### Safety Constraints
- 모든 사용자 응답은 초안 형태로 유지.
- 외부 고객 통신 채널은 Owner 승인 전 발송 금지.

### Next Taskset Candidates
- `SUPPORT-RESPONSE-REVIEW-AUTOMATION`
- `PROCESS-SLA-IMPROVEMENT`

## Planning-Strategy Playbook

- **Owner/owner roles:** `strategy-lead` / `business-analyst`
- **Reviewers:** `planning-architect`, `portfolio-steward`

### Scope In
- Convert business priorities into taskset/task decomposition.
- Define KPI assumptions, decision criteria, and roadmap fit.

### Scope Out
- 임의의 기능 변경 실행, 제품 스코프 무단 조정.

### Inputs
- `WORK-LANE-PLAYBOOKS.md`
- PRIORITY and roadmap evidence
- Product maturity / risk signals

### Required Outputs
- `prioritization-notes.md`
- `dependency-and-sequencing-map.md`
- `next-taskset-decomposition.md`

### Cadence
- Each cycle begins with `W0` visibility + active-claim check.
- Close only with generated taskset candidates and review evidence.

### Decision Trigger
- If execution-ready tasks emerge, register them via
`python scripts/work.py new --input <json>`.

### Safety Constraints
- Do not create or close large scope changes without taskset registration.
- Keep assumptions explicit and verifiable.

### Next Taskset Candidates
- `TASKSET-AR-BUSINESS-LANE-IMPLEMENTATION` (if lane outputs are ready for execution)
- `TASKSET-AR-BUSINESS-PLAN-REFINEMENT` (if assumptions need rebaseline)
