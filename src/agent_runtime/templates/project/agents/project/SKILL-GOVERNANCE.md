# Skill Governance

## Skill Types

Knowledge skills route questions to the right source of truth.

Runbook skills encode expert work process:

1. Clarify the request and tolerance for error.
2. Retrieve the ranked sources of truth.
3. Execute with bounded tools and explicit metadata.
4. Run adversarial review.
5. Verify and record evidence.
6. Reuse validated patterns before creating a new one.

## Warehouse Document Shape

Reusable knowledge documents should use this order:

1. Fast reference.
2. Dimensional explanation.
3. Core tables.
4. Caveats and failure patterns.
5. Links to upstream sources, lineage, history, and related runbooks.

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

## Definition Rule

Agents may propose definitions. Humans or explicitly assigned accountable owners
own final definitions.

## Source Footer

Answers that depend on project context should include:

- source tier
- source path or URL
- confidence
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
