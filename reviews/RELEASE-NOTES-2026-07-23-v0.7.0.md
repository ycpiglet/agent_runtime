# Agent Runtime v0.7.0

This minor release strengthens safe multi-agent execution, release reliability, host recovery, and cross-machine onboarding. It contains the accumulated, verified work since v0.6.0.

## Highlights

- Safer work orchestration: claim-first taskset and wave dispatch, deterministic exact work selectors, canonical task IDs, preserved dependency order, and terminal taskset-state protection.
- Stronger recovery and state integrity: atomic orchestrator/session writes, self-contained session dashboards, resume checks, quoted-frontmatter preservation, and host status continuity.
- Release and CI hardening: fail-closed auto-merge readback, release-cadence query handling, transient fixture isolation, clean-bundle publication checks, and current-head release preflight.
- Easier onboarding: cross-platform `setup.ps1` / `setup.sh`, development bootstrap checks, editable installation, devcontainer support, and updated contributor guidance.
- Better operations feedback: optional never-blocking allimbot notifications plus expanded knowledge/evaluation instrumentation.

## Validation

- Version `0.7.0` is consistent across all managed cascade references and the host fixture lock.
- Clean public bundle: 704 files, 0 findings.
- Release preflight: 13 checks, 0 findings.
- Exact PR head and exact merged `main` each passed the Python 3.10, 3.11, and 3.12 GitHub Actions matrix.

## Upgrade

Install directly from the immutable release tag:

```text
pip install "git+https://github.com/ycpiglet/agent_runtime.git@v0.7.0"
```

Generated host projects should update their upstream ref to `v0.7.0` and use the existing check-then-apply update flow. This release has no database, data, configuration, or secret migration.

**Full changelog:** https://github.com/ycpiglet/agent_runtime/compare/v0.6.0...v0.7.0
