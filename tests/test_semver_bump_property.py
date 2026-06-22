"""Property-based beachhead (hypothesis) for the semver bumper.

Starts the testing-uplift from the 2026-06-22 audit (hypothesis was unused).
Targets the pure `release_cadence_trigger._bump_version`, which the release
cascade relies on: for ANY valid semver and ANY bump kind, the result must
re-parse, be strictly greater, and have the correct component semantics.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings, strategies as st

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import release_cadence_trigger as rct  # noqa: E402

_versions = st.tuples(
    st.integers(min_value=0, max_value=9999),
    st.integers(min_value=0, max_value=9999),
    st.integers(min_value=0, max_value=9999),
).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}")

_bumps = st.sampled_from(["major", "minor", "patch"])


def _parse(v: str) -> tuple[int, int, int]:
    a, b, c = v.split(".")
    return int(a), int(b), int(c)


# database=None: do not persist an example DB, so no `.hypothesis/` cache dir is
# created in the repo (it would trip the public-sanitization gate's local-path scan).
@settings(database=None)
@given(version=_versions, bump=_bumps)
def test_bump_reparses_is_strictly_greater_and_correct(version: str, bump: str) -> None:
    out = rct._bump_version(version, bump)
    assert out is not None, (version, bump)
    parts = out.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts), out

    major, minor, patch = _parse(version)
    assert _parse(out) > (major, minor, patch), (version, bump, out)  # strictly greater

    if bump == "major":
        assert _parse(out) == (major + 1, 0, 0), out  # resets minor + patch
    elif bump == "minor":
        assert _parse(out) == (major, minor + 1, 0), out  # resets patch
    else:
        assert _parse(out) == (major, minor, patch + 1), out
