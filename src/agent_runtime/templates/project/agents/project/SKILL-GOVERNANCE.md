# Skill Governance

## Skill Types

Knowledge skills route questions to the right source of truth.

Runbook skills encode expert work process. A runbook item is complete only
when all six evidence stages are present:

1. clarify: capture question, business_scope, time_window, tolerance, query_tolerance, and tradeoff_preference.
2. retrieve: use `CONTEXT-SOURCES.yml` source_tier priority and access_level.
3. execute: record scope, mutation boundary, and a verified_pattern when one exists.
4. review: run adversarial review or reviewer_review for risky or ambiguous work.
5. verify: record commands, scores, failure/warning counts, and source_footer.
6. record: link evidence, review_verdict, verified_pattern, and correction_path to task/review/status records.

Required completion evidence:

- `source_footer`
- `review_verdict`
- `evidence`
- `verified_pattern`
- `correction_path`
- `record_path`

## Warehouse Document Shape

Reusable knowledge documents should use this order and preserve the Korean
section labels for gate checks:

1. 빠른 참조 (Fast reference)
2. 차원설명 (Dimensional explanation)
3. 핵심 테이블 (Core tables)
4. 주의사항/패턴 (Caveats and failure patterns)
5. 연결고리 (Links to upstream sources, lineage, history, and related runbooks)

Each warehouse document includes `source tier`, `lineage`, `history`,
`context knowledge`, `freshness_sla`, `owner`, and `updated_at`. Stale or
missing metadata produces a pre-check warning and repeated warnings escalate
through `TASK-AR-204`.

## Co-Location Rule

When a skill depends on data, schemas, scripts, or source definitions, keep the
skill document and governance metadata near the owned artifact. Use
`agents/project/SKILL-DATA-MAP.example.yml` for mapping, and keep source
mapping references in `agents/project/CONTEXT-SOURCES.yml`.
For multi-project reuse, keep vision, roadmap, org, links, and team context in
`agents/project/ROADMAP.md`, `agents/project/ORG.md`, `agents/project/LINKS.md`,
and `agents/project/TEAMS.md`; keep skill logic and execution behavior in
`agents/*/SKILL.md` and runtime scripts.

If a model, tool, schema, or dataset changes, the related skill/runbook context
must be reviewed in the same change. CI should block releases when the mapping
is stale. `TASK-AR-204` defines the hard enforcement policy.
Query contract violations route to `hold_for_query_contract`; stale, risky, or
access-unclear requests route to `clarify_required` or `reviewer_review` before
execution.

## Definition Rule

Agents may propose definitions. Humans or explicitly assigned accountable owners
own final definitions.

## Source Footer

Answers that depend on project context should include:

- source tier
- source path or URL
- confidence
- access level
- ambiguity score
- freshness SLA
- reviewer verdict
- lineage
- unresolved ambiguity, if any

## Autonomous Delivery and Release Governance

Branch, commit, PR, and merge automation should be treated as the normal path
for routine, reversible work. Owner approval is reserved for critical
boundaries: secrets, production data, billing/legal exposure, destructive
operations, failed critical gates, untrusted external publication, or
major/breaking releases.

Routine patch/minor releases may be approved by an agent release council:

1. Lead Engineer validates scope, version, and release notes.
2. QA validates focused checks, regression risk, and smoke evidence.
3. Independent Auditor validates evidence integrity and critical-risk absence.
4. Doc Steward validates concise reports, metadata, tags, and handoff records.

The council decision must be machine-readable, linked from release evidence,
and blocked when a critical boundary is present.

## Executive BRIEF Output Contract

Plan, report, review, release, and handoff documents should use a
human-centered, machine-readable executive brief shape:

1. frontmatter first: `type`, `id`, `audience`, `status`, `priority`, `tags`,
   `actions`, and `evidence`;
2. `Bottom Line` first in the visible body;
3. compact tables for signal, action, owner, and trigger;
4. concise bullets with clear hierarchy and no decorative emoji;
5. footer or final section for evidence, unresolved risks, and next action.
