#!/usr/bin/env sh
# agent_runtime one-shot setup (macOS/Linux) — run from the repo root after clone:
#   ./setup.sh
set -e

PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
    echo "Python >= 3.10 is required: https://www.python.org/downloads/" >&2
    exit 1
fi

"$PY" scripts/bootstrap_dev_env.py --apply --ssh-push

if command -v gh >/dev/null 2>&1; then
    if ! gh auth status >/dev/null 2>&1; then
        echo "GitHub CLI is not authenticated - starting 'gh auth login'..."
        gh auth login
    fi
else
    echo "GitHub CLI (gh) is not installed: https://cli.github.com (needed for issue/PR automation)"
fi

echo ""
echo "setup: done. Details: docs/DEV-ENVIRONMENT.md"
