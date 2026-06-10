# CLAUDE.md

Claude-specific companion guidance for this repository.

Read `AGENTS.md` first. If this file conflicts with `AGENTS.md` or current
records under `agents/lead_engineer/`, follow the shared protocol.

## Operating Mode

- Treat `AGENTS.md` as the source of truth.
- Use the current `TASK` / `CYCLE` record when implementation is needed.
- Keep edits scoped to the task.
- Preserve user changes.
- Verify before claiming completion.
- Report completed work in BRIEF format.

## Start Checklist

1. Read `agents/project/NEXT-SESSION-POINTER.yml`.
2. Read `AGENTS.md`.
3. Read `README.md`.
4. Read `AGENT_RUNTIME.md`.
5. Read `agents/lead_engineer/STATUS.md`.
6. Read `agents/roles.yml`.
7. Read the relevant role `SKILL.md`.
8. Read the active task or backlog item.

## Live Work Continuity

`agents/project/NEXT-SESSION-POINTER.yml` is the first live work pointer, not
only a next-session note. Read it with `agents/runtime/task_claims/*.json` to
recover active agent, team, pane_id, task, status, phase, progress_pct,
worktree, branch, handoff, next action, and verification status after memory
reset or reconnect.

Update it while work is happening and before final reporting when non-trivial
work changes state, decisions, roles, pane assignment, phase, progress, next
actions, verification, or handoff risk. If it does not need an update, say so in
the closure record.

## Collaboration

Use the repository role model instead of answering every question as a single
generalist.

- Lead Engineer plans and closes work.
- QA verifies behavior.
- Independent Auditor checks evidence and completion.
- Doc Steward checks documentation integrity.
- Scribe cleans records after canonical state is clear.
- Research Agent provides evidence, not final decisions.
- Secretary handles personal desk summaries and reminders, not governance writes.

For substantial work, record which roles or perspectives contributed.

## Implementation Rules

1. Prefer existing local helpers and scripts.
2. Avoid speculative abstractions.
3. Do not widen scope because adjacent code looks messy.
4. Add tests proportional to risk.
5. If a bug is reported, reproduce it before and after the fix when feasible.
6. Do not use external services, deployments, secrets, or destructive git actions
   without the required approval.
7. If the Owner repeats a request or criticism twice, promote it into a
   Repeated Request API: function/API, script, hook, gate, checklist, template,
   or explicit task proposal.

## Measured Improvement

Process and prompt improvements use `Evaluate -> Propose -> Verify -> Merge`.
Define the measurable score, golden set, failure notes, and edge cases before
changing the behavior. Change one variable at a time unless the work is an
explicitly separated parallel experiment.

Owner owns the definition of "better" and the final merge decision. Agents
produce proposals, evidence, and risk notes.

Repeated failures or criticisms must be captured in Compound automatically as a
mandatory closure step when they represent a recurring pattern. Prefer executable
prevention over prose-only reminders.

## Reporting

Final task responses start with:

```text
Bottom Line: ...
```

Then include `Signal`, `Insight`, and `Decision` sections when reporting work,
status, or a plan. Keep updates concise while work is still in progress.

## Time

Use:

```powershell
python scripts/now.py
```

Do not infer timestamps from memory or the chat clock.
