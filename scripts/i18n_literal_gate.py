"""Un-keyed-literal i18n gate for Agent Runtime UI work.

Backs RFC-2026-06-23-i18n-en-schema-ko-ui (phase P3). The shipped model is
EN-canonical schema + KO UI localization served from a Python-side string
table (``ui_state.I18N_STRINGS``) and resolved in the browser via ``t(key)``
(see ``TASK-AR-341``). Phase P1 extends the table to cover error / toast /
empty-state copy; this gate keeps that coverage from silently regressing.

What it does
------------
Scans the UI layer (the ``ui_*.py`` files that carry the console HTML/CSS/JS as
string constants) for user-facing string literals in three *targeted
categories* -- **error**, **toast**, **empty-state** -- that bypass the i18n
table. Detection is deliberately narrow: it inspects only a fixed set of
render *sinks*, so it never false-positives on already-keyed strings, CSS,
element ids, ARIA contract tokens, or runtime data identifiers.

Sinks (the only places a finding can originate)
-----------------------------------------------
- ``pushUndoToast(<arg>, ...)`` / ``pushActivityToast(kind, <title>, <body>)``
  -- toast copy (visible message/title/body).
- ``emptyState(<title>, ...)`` -- empty-state copy.
- ``errorState(<title>, ...)`` -- error-state copy.
- ``$("status-line").textContent = <expr>`` and ``inboxHint(<expr>, ...)``
  -- inline error/status copy.

A sink argument is **OK** when it is a ``t("key")`` call (optionally
concatenated/templated with dynamic data), an empty/whitespace string (a
region clear), a bare identifier/expression (already-resolved value), or the
ASCII glyph fallbacks. It is a **finding** when it is a non-empty raw string
literal (``"..."`` / ``'...'`` / a template literal whose text is real copy).

The ASCII-only-app.js invariant (TASK-AR-341) is preserved structurally rather
than re-scanned here: KO values live Python-side in ``ui_state.I18N_STRINGS``
and reach the browser as JSON, so routing copy through ``t(key)`` is exactly
what keeps the served JS ASCII-only. This gate enforces that routing.

Usage::

    python scripts/i18n_literal_gate.py --check        # exit 1 on findings
    python scripts/i18n_literal_gate.py --check --json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# UI source files that carry the console JS as Python string constants. These
# are the only files scanned -- the gate is scoped to the UI render layer.
UI_SOURCE_FILES = (
    Path("src/agent_runtime/ui_console_assets.py"),
    Path("src/agent_runtime/ui_design_assets.py"),
)

# A "key call" routes copy through the i18n table; treated as already covered.
_T_CALL = r"t\(\s*[\"'][^\"']+[\"']\s*\)"

# A JS string literal: single/double quoted (no escaped-quote handling needed
# for our copy) or a backtick template literal.
_STR = r"(?:\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)"


class Finding:
    def __init__(self, code: str, path: str, line: int, category: str, message: str) -> None:
        self.code = code
        self.path = path
        self.line = line
        self.category = category
        self.message = message

    def __eq__(self, other: object) -> bool:  # makes ``== []`` assertions ergonomic
        return isinstance(other, Finding) and self.__dict__ == other.__dict__

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return f"Finding({self.code!r}, {self.path!r}, {self.line}, {self.category!r}, {self.message!r})"


def _literal_text(token: str) -> str:
    """Return the inner text of a JS string/template literal token."""
    if not token:
        return ""
    inner = token[1:-1]
    if token[0] == "`":
        # Drop ${...} interpolations; what remains is the literal copy.
        inner = re.sub(r"\$\{[^}]*\}", "", inner)
    return inner.strip()


def _is_keyed_or_dynamic(expr: str) -> bool:
    """True when an argument expression is already routed through t() or is a
    bare (already-resolved) value rather than a raw copy literal."""
    expr = expr.strip()
    if not expr:
        return True
    if re.search(_T_CALL, expr):
        # t("key") anywhere in the expression (incl. concatenation/templating).
        return True
    # A template/string literal whose only "copy" is punctuation/glyphs or is
    # empty after stripping interpolation is not user copy worth keying.
    return False


def _string_args(after: str) -> list[str]:
    """Return the leading comma-separated argument expressions of a call,
    given the text immediately after the opening ``(``. Shallow paren-aware."""
    args: list[str] = []
    depth = 0
    cur = ""
    in_str = ""
    i = 0
    while i < len(after):
        ch = after[i]
        if in_str:
            cur += ch
            if ch == "\\" and i + 1 < len(after):
                cur += after[i + 1]
                i += 2
                continue
            if ch == in_str:
                in_str = ""
            i += 1
            continue
        if ch in "\"'`":
            in_str = ch
            cur += ch
            i += 1
            continue
        if ch in "([{":
            depth += 1
            cur += ch
        elif ch in ")]}":
            if depth == 0:
                args.append(cur)
                return args
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            args.append(cur)
            cur = ""
        else:
            cur += ch
        i += 1
    if cur.strip():
        args.append(cur)
    return args


def _flag_literal_arg(arg: str) -> bool:
    """A finding fires when the arg is a non-empty raw string literal that is
    not routed through t()."""
    arg = arg.strip()
    if _is_keyed_or_dynamic(arg):
        return False
    m = re.match(rf"^({_STR})", arg)
    if not m:
        # Not a leading raw literal (identifier/expression) -> already a value.
        return False
    text = _literal_text(m.group(1))
    if not text:
        return False  # empty string / region-clear
    # Pure punctuation / single-glyph placeholders (e.g. "-", "...") are not copy.
    if not re.search(r"[A-Za-z가-힣]", text):
        return False
    return True


# (sink regex, category). Each regex captures the user-facing argument region
# starting right after the call's ``(`` (or after ``=`` for assignments).
_CALL_SINKS = (
    (re.compile(r"\bpushUndoToast\("), "toast", 0),
    (re.compile(r"\bpushActivityToast\("), "toast", 1),  # title is 2nd arg
    (re.compile(r"\bemptyState\("), "empty-state", 0),
    (re.compile(r"\berrorState\("), "error", 0),
)

_STATUS_ASSIGN = re.compile(
    r"""\$\(\s*["']status-line["']\s*\)\s*\.textContent\s*=\s*(?P<rhs>.+?);"""
)
_INBOX_HINT = re.compile(r"\binboxHint\(")


def scan_js_text(rel: str, text: str) -> list[Finding]:
    """Scan a blob of JS source for un-keyed copy in the targeted sinks."""
    findings: list[Finding] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        # Skip comment-only lines.
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        for pat, category, arg_index in _CALL_SINKS:
            for m in pat.finditer(line):
                args = _string_args(line[m.end():])
                if arg_index >= len(args):
                    continue
                if _flag_literal_arg(args[arg_index]):
                    findings.append(
                        Finding(
                            "unkeyed-literal", rel, idx, category,
                            f"un-keyed {category} literal in sink",
                        )
                    )

        for m in _STATUS_ASSIGN.finditer(line):
            if _flag_literal_arg(m.group("rhs")):
                findings.append(
                    Finding(
                        "unkeyed-literal", rel, idx, "error",
                        "un-keyed status-line error literal",
                    )
                )

        for m in _INBOX_HINT.finditer(line):
            args = _string_args(line[m.end():])
            if args and _flag_literal_arg(args[0]):
                findings.append(
                    Finding(
                        "unkeyed-literal", rel, idx, "error",
                        "un-keyed inbox-hint literal",
                    )
                )
    return findings


def scan_file(path: Path, root: Path = ROOT) -> list[Finding]:
    try:
        rel = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    return scan_js_text(rel, text)


def cmd_check(*, root: Path = ROOT, json_output: bool = False) -> int:
    findings: list[Finding] = []
    scanned = 0
    for rel in UI_SOURCE_FILES:
        path = root / rel
        if not path.exists():
            continue
        scanned += 1
        findings.extend(scan_file(path, root))

    payload = {
        "status": "fail" if findings else "pass",
        "scanned": scanned,
        "findings": [f.__dict__ for f in findings],
    }
    if json_output:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for f in findings:
            print(f"i18n-literal-gate: {f.code}: {f.path}:{f.line}: [{f.category}] {f.message}")
        print(
            f"i18n-literal-gate: {payload['status']} scanned={scanned} "
            f"findings={len(findings)}"
        )
    return 1 if findings else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Un-keyed-literal i18n gate")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    return cmd_check(json_output=args.json)


if __name__ == "__main__":
    raise SystemExit(main())
