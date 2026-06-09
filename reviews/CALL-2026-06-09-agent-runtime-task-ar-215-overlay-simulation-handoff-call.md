# CALL: TASK-AR-215 Overlay Simulation Handoff

## Summary

The cross-project overlay simulation is ready for gate execution. The handoff target is `TASK-AR-204` because co-location enforcement must now prevent teams from tuning common runtime skills for project-specific ideas.

## Handoff Items

- Gate report: `reviews/OVERLAY-SIMULATION-GATE-2026-06-09-task-ar-215.json`
- Runtime boundary: do not customize `agents/*/SKILL.md`, `agents/roles.yml`, or `scripts/**` for a single project.
- Overlay boundary: project-specific definitions live under `agents/project/**` or a project overlay simulation folder.
- Release route: `TASK-AR-210` can be re-evaluated only after `TASK-AR-204` closes or is owner-approved.

## Verification Result

- `TASK-AR-215` handoff evidence is verified.
- Next boundary: `TASK-AR-204` co-location enforcement executable gate.
