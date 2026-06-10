# RESEARCH: TASK-AR-223/217 Closeout and Rehearsal Integration

## Bottom Line

The release rehearsal should treat release artifact hygiene, eval correctness, reviewer safety, correction capture, and A2A trace continuity as separate evidence lanes. A single green release-preflight is necessary but not sufficient for `v0.1.8` readiness.

## Sources Checked

- OpenAI Agent evals: https://platform.openai.com/docs/guides/agent-evals
- OpenAI Trace grading: https://platform.openai.com/docs/guides/trace-grading
- OpenAI Agent safety: https://platform.openai.com/docs/guides/agent-builder-safety
- Anthropic Claude Code security: https://docs.anthropic.com/en/docs/claude-code/security
- Anthropic eval tool: https://docs.anthropic.com/ko/docs/test-and-evaluate/eval-tool
- A2A Life of a Task: https://a2aproject.github.io/A2A/latest/topics/life-of-a-task/

## Findings

- Agent evals should be reproducible and dataset-backed; trace grading is useful because it scores the decision/tool/reasoning path, not just the final answer.
- Safety guidance converges on approvals, guardrails, structured inputs, audit logs, and explicit handling of high-risk tool use.
- Claude Code security guidance emphasizes permission boundaries, project-specific permissions, prompt-injection protection, and auditing permission settings.
- A2A task continuity depends on stable task/context identifiers and task states such as `input-required`, `completed`, and failure states.

## Mapping to agent_runtime

- `release-preflight`: proves package hygiene only.
- `offline_eval`: proves dataset-backed domain correctness and must record query type, ambiguity, access level, and correction outcome.
- `trace_grading`: proves workflow-level behavior and should grade request, retrieval, tool use, reviewer decision, and correction event.
- `live_reviewer`: proves high-risk response governance and must require source footer/risk/confidence/ambiguity/freshness.
- `a2a_trace`: proves multi-agent reconstruction and must preserve `contextId`/`taskId` or local equivalents.
- `hold_routing`: ambiguous query -> `hold_for_query_contract`; stale/missing overlay -> `hold_for_overlay`; migration/evidence gap -> `hold_for_data`.

## Decision

Use `TASK-AR-225` as release artifact evidence, then continue `TASK-AR-217` on the remaining validation lanes rather than rerunning root-source checks as if they represented public release readiness.
