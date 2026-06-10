# RSI And Planning Loop Research

## Bottom Line

The planning loop should be a bounded organizational learning system, not an
unrestricted self-modifying agent. The useful pattern is: trace/eval evidence
finds a gap, graders classify the gap, a proposal writer creates reversible
tasks and plan diffs, diverse reviewers critique it, and gates decide whether
it remains a proposal or becomes canonical work.

## Source Map

| Area | Source | Planning implication |
| --- | --- | --- |
| Agent evals | https://developers.openai.com/api/docs/guides/agent-evals | Start with traces for workflow debugging, then move to repeatable datasets and eval runs. |
| Trace grading | https://developers.openai.com/api/docs/guides/trace-grading | Grade end-to-end decisions, tool calls, and reasoning steps so task creation is grounded in failures, regressions, and improvements. |
| Eval best practices | https://developers.openai.com/api/docs/guides/evaluation-best-practices | Use task-specific evals, production/historical data, continuous evaluation, and human calibration rather than vibe-based success. |
| Graders | https://developers.openai.com/api/docs/guides/graders | Use structured grader outputs as machine-readable evidence for proposal priority, regression class, and acceptance criteria. |
| Agents SDK tracing | https://openai.github.io/openai-agents-python/tracing/ | Preserve spans for model calls, tool calls, guardrails, and handoffs; long-running workers need reliable export/flush handling. |
| Codex automations | https://developers.openai.com/codex/app/automations | Scheduled background tasks can report findings to an inbox; repo-local work should prefer isolated worktrees when changing files. |
| Codex safety | https://openai.com/index/running-codex-safely/ | Keep low-risk actions frictionless, but require sandbox, approvals, constrained execution, and telemetry for higher-risk actions. |
| Claude hooks | https://code.claude.com/docs/en/hooks-guide | Deterministic hooks are appropriate for enforcement; deny decisions must win over permissive signals. |
| A2A task lifecycle | https://a2a-protocol.org/latest/topics/life-of-a-task/ | Use `contextId`, `taskId`, immutable task units, and follow-up tasks to preserve continuity across planning cycles. |
| A2A specification | https://a2a-protocol.org/latest/specification/ | Context/task identity mismatch must be rejected; stateful work needs explicit lifecycle and update delivery mechanisms. |
| NIST AI RMF | https://www.nist.gov/itl/ai-risk-management-framework | Treat RSI as risk-managed governance: govern, map, measure, manage, then repeat. |
| RSI theory | https://arxiv.org/abs/1502.06512 | RSI research emphasizes definitions, limits, convergence behavior, and security implications; uncontrolled recursion is a risk, not a product goal. |
| STOP | https://arxiv.org/abs/2310.02304 | Self-improving scaffolds can improve code generation but must be evaluated for sandbox bypass and unsafe strategy emergence. |
| Premortem | https://hbr.org/2007/09/performing-a-project-premortem | Before applying a plan, ask reviewers to assume it failed and identify likely causes. |
| Double-loop learning | https://hbr.org/1991/05/teaching-smart-people-how-to-learn | The loop should revisit assumptions and decision rules, not only patch individual tasks. |
| Delphi method | https://www.rand.org/pubs/papers/P3558.html | Structured multi-round expert review can combine diverse opinions and surface polarization instead of forcing premature consensus. |
| Cognitive diversity | https://arxiv.org/abs/2402.01427 | Diverse initial idea pools and probing discussion can improve group deliberation. |

## Project Interpretation

- `agent_runtime` already has task files, Owner BRIEFs, state machines,
  release gates, correction/eval/A2A evidence, and a read/write UI console.
- The next improvement is not another free-running pane. It is a runtime-owned
  `planning_loop` with read-only scan, proposal outbox, approval/apply, and
  promotion gates.
- `doc-steward` covers document consistency. New stewards should cover version
  and release consistency, history/retro/compound synthesis, eval/trace
  evidence, risk/stability, and diversity of viewpoints.
- The loop should create new tasks when evidence shows one of these conditions:
  stale plan, missing link, repeated failure, eval regression, release/version
  inconsistency, unresolved compound pattern, repeated user correction, missing
  trace, unowned risk, or blocked dependency.
- The loop should not create work from a single weak signal. Require at least
  source evidence plus one of: repeated occurrence, gate failure, reviewer
  finding, trace/eval regression, release inconsistency, or explicit owner input.

## Stability Rules

- Bounded autonomy: scan and proposal generation are autonomous; canonical
  mutation is gated.
- Diversity without chaos: reviewers may advocate, criticize, forecast failure,
  or defend stability, but every output must collapse into a structured verdict.
- Non-divergence: cap proposal count per cycle, require dedupe keys, link every
  proposal to source evidence, and block self-weakening gate changes.
- Recursion hygiene: every RSI change must state what it improves, what it may
  degrade, how it will be measured, and how it can be reverted.
