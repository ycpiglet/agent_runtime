"""Tool execution + guardrails for claude-agent and codex-agent providers.

The runner exposes a small command surface only, with explicit policy profiles:

- ci: strictest, deterministic, CI-safe baseline
- owner: extra maintenance commands for human/Owner workflow
- research: same safety boundary as ci but non-mutating helper scripts for exploration
"""

from __future__ import annotations

import shlex
import subprocess
import re
import urllib.parse
from pathlib import Path


class GuardrailError(Exception):
    """Raised when a tool call violates a safety guardrail."""


SECRET_NAMES = {".env"}
READONLY_GIT_SUBCMDS = {"status", "diff", "log", "branch", "rev-parse", "show"}
FORBIDDEN_GIT_SUBCMDS = {
    "add", "commit", "checkout", "restore", "stash", "reset", "clean",
    "pull", "push", "fetch", "merge", "rebase", "switch", "rm", "mv",
}
OWNER_GIT_SUBCMDS = frozenset(READONLY_GIT_SUBCMDS | {"add", "restore"})
RESEARCH_GIT_SUBCMDS = frozenset(READONLY_GIT_SUBCMDS)
ALLOWED_INTERPRETERS = {"python", "py"}
ALLOWED_ROOT_SCRIPTS_CI = {
    "scripts/check_agent_docs.py",
    "scripts/check_messages.py",
    "scripts/agent_orchestrator.py",
}
ALLOWED_ROOT_SCRIPTS_RESEARCH = {
    *ALLOWED_ROOT_SCRIPTS_CI,
    "scripts/agent_worker.py",
    "scripts/auto_runner.py",
}
ALLOWED_ROOT_SCRIPTS_OWNER = set(ALLOWED_ROOT_SCRIPTS_CI)
ALLOWED_ORCHESTRATOR_ARGS = ("status", "--json")
ALLOWED_HELP_ONLY_SCRIPTS = {"scripts/agent_worker.py", "scripts/auto_runner.py"}
ALLOWED_PYTEST_FLAGS = {
    "-q", "-x", "--maxfail", "--disable-warnings", "--cov", "--cov-report"
}
FORBIDDEN_PYTHON_ARGS = {"-c", "-", "python", "pip", "import"}
FORBIDDEN_RAW_TOKENS = {";", "&", "|", ">", "<", "`", "&&", "||", "\n", "\r"}
FORBIDDEN_COMMAND_PATTERNS = (
    re.compile(r"%[A-Za-z_][A-Za-z0-9_]*%"),  # CMD-style %VAR%
    re.compile(r"%[0-9A-Fa-f]{2}"),  # percent-encoded byte sequences used for shell escaping
    re.compile(r"\$env:[A-Za-z_][A-Za-z0-9_]*"),  # PowerShell $env:VAR
    re.compile(r"!\w+!"),  # CMD delayed expansion !VAR!
    re.compile(r"\$\([^)]*\)"),  # command substitution / subshell
    re.compile(r"@\("),  # PowerShell invocation pattern
    re.compile(r"\^"),  # PowerShell/CMD escape char
    re.compile(r"\$\{[A-Za-z_][A-Za-z0-9_]*\}"),  # ${VAR} substitution
    re.compile(r"@\""),  # PowerShell here-string start
    re.compile(r"@'"),  # PowerShell here-string single-quoted start
)
MAX_FORBIDDEN_DECODE_PASSES = 3
MAX_OUTPUT = 8000
MAX_AUDIT_ENTRIES = 200

VALID_PROFILES = {"ci", "owner", "research"}


def _profile_policy_summary(profile: str) -> str:
    profile = _normalize_profile(profile)
    if profile == "owner":
        return (
            "git: add/restore (repo-relative args), status/diff/log/rev-parse/show/branch, scripts/check_messages.py, scripts/check_agent_docs.py, "
            "scripts/agent_orchestrator.py status --json"
        )
    if profile == "research":
        return (
            "git: status/diff/log/rev-parse/show/branch + help-only scripts "
            "(agent_worker.py, auto_runner.py), scripts/check_messages.py, "
            "scripts/check_agent_docs.py, scripts/agent_orchestrator.py status --json"
        )
    return (
        "git: status/diff/log/rev-parse/show/branch + scripts/check_messages.py,"
        " scripts/check_agent_docs.py, scripts/agent_orchestrator.py status --json"
    )


def _normalize_profile(profile: str) -> str:
    value = str(profile or "ci").strip().lower()
    if value not in VALID_PROFILES:
        raise GuardrailError(f"unknown command profile: {profile} (allowed: {sorted(VALID_PROFILES)})")
    return value


def _pretty_forbidden_tokens(command: str) -> str:
    found = sorted(_collect_forbidden_tokens(command))
    if not found:
        return "unknown"
    pretty = []
    for token in found:
        if token == "\n":
            pretty.append("\\n")
        elif token == "\r":
            pretty.append("\\r")
        else:
            pretty.append(token)
    return ", ".join(pretty)


def _coerce_path_token(token: str) -> str:
    """Normalize a token for deterministic path/script allowlist comparisons."""
    return str(token).replace("\\", "/").strip()


def _git_allowlist_for_profile(profile: str) -> set[str]:
    if profile == "owner":
        return set(OWNER_GIT_SUBCMDS)
    if profile == "research":
        return set(RESEARCH_GIT_SUBCMDS)
    return set(READONLY_GIT_SUBCMDS)


def _python_script_allowlist(profile: str) -> set[str]:
    if profile == "research":
        return set(ALLOWED_ROOT_SCRIPTS_RESEARCH)
    if profile == "owner":
        return set(ALLOWED_ROOT_SCRIPTS_OWNER)
    return set(ALLOWED_ROOT_SCRIPTS_CI)


def resolve_in_root(root: Path, path: str) -> Path:
    """Resolve `path` under `root`, rejecting escapes and secret files."""
    root = Path(root).resolve()
    p = (root / path).resolve()
    try:
        p.relative_to(root)
    except ValueError:
        raise GuardrailError(f"path escapes repo root: {path}")
    if p.name in SECRET_NAMES:
        raise GuardrailError(f"access to secret file denied: {path}")
    return p


def _has_forbidden_token(text: str) -> bool:
    return bool(_collect_forbidden_tokens(text))


def _decode_percent_u(text: str) -> str:
    """Decode legacy `%uXXXX` escapes used by Windows tooling variants."""

    def _replace(match: re.Match[str]) -> str:
        return chr(int(match.group(1), 16))

    return re.sub(r"%u([0-9A-Fa-f]{4})", _replace, text)


def _decode_unicode_escapes(text: str) -> str:
    """Decode `\\uXXXX` escape sequences in command strings."""

    if "\\u" not in text.lower():
        return text
    try:
        return text.encode("utf-8").decode("unicode_escape")
    except Exception:
        return text


def _forbidden_token_candidates(text: str) -> list[str]:
    """Build token candidates with bounded raw and decode variants."""
    candidates: list[str] = [text]
    frontier: list[str] = [text]

    for _ in range(MAX_FORBIDDEN_DECODE_PASSES):
        next_frontier: list[str] = []
        for candidate in frontier:
            decoded = urllib.parse.unquote(candidate)
            percent_u = _decode_percent_u(candidate)
            unicode_esc = _decode_unicode_escapes(candidate)
            for expanded in (decoded, percent_u, unicode_esc):
                if expanded not in candidates:
                    candidates.append(expanded)
                    next_frontier.append(expanded)
        if not next_frontier:
            break
        frontier = next_frontier

    return candidates


def _collect_forbidden_tokens(text: str) -> set[str]:
    """Collect raw and multi-pass decoded tokens/pattern hits."""
    hits: set[str] = set()
    for candidate in _forbidden_token_candidates(text):
        for token in FORBIDDEN_RAW_TOKENS:
            if token in candidate:
                hits.add(token)
        for pattern in FORBIDDEN_COMMAND_PATTERNS:
            for match in pattern.findall(candidate):
                if isinstance(match, tuple):
                    for item in match:
                        if item:
                            hits.add(item)
                elif isinstance(match, str) and match:
                    hits.add(match)
    return hits


def _is_flag(token: str) -> bool:
    return token.startswith("-")


def _is_repo_path(root: Path, token: str) -> bool:
    # Empty or flag-like tokens are not treated as paths.
    if not token or _is_flag(token):
        return False
    if re.match(r"^[A-Za-z]:[\\/]", token):
        return False
    try:
        resolve_in_root(root, token)
        return True
    except GuardrailError:
        return False


def _py_allowlist_valid(argv: list[str], root: Path, *, profile: str) -> bool:
    """Validate allowed python command profiles."""
    if len(argv) < 2:
        return False
    if any(t in FORBIDDEN_PYTHON_ARGS for t in argv[1:]):
        return False

    profile = _normalize_profile(profile)
    if argv[1] == "-m":
        # allow `python -m pytest ...`
        if len(argv) < 3 or argv[2] != "pytest":
            return False
        for token in argv[3:]:
            if _has_forbidden_token(token):
                return False
            if _is_flag(token):
                # allow known pytest flags only; unknown flags must be added
                # intentionally to keep execution bounded.
                if token.startswith("--") and token.split("=")[0] not in ALLOWED_PYTEST_FLAGS and token not in {"-q", "-x"}:
                    return False
                continue
            if not _is_repo_path(root, token):
                return False
        return True

    script = argv[1].replace("\\", "/")
    if not script.endswith(".py"):
        return False
    if script not in _python_script_allowlist(profile):
        return False
    if script == "scripts/agent_orchestrator.py":
        return tuple(argv[2:]) == ALLOWED_ORCHESTRATOR_ARGS
    if script in ALLOWED_HELP_ONLY_SCRIPTS:
        return tuple(argv[2:]) in {("--help",), ("-h",)}
    return argv[2:] == []


def _git_allowlist_valid(argv: list[str], *, root: Path, profile: str) -> bool:
    profile = _normalize_profile(profile)
    subcmd = argv[1] if len(argv) > 1 else ""
    allowed = _git_allowlist_for_profile(profile)
    if subcmd not in allowed:
        return False
    if subcmd in {"add", "restore"}:
        args = [t for t in argv[2:] if t and not t.startswith("-")]
        if not args:
            return False
        return all(_is_repo_path(root, t) for t in args)
    return True


class ToolRunner:
    """Executes one tool call at a time against `root`, tracking changed files."""

    def __init__(self, root: Path, *, max_output: int = MAX_OUTPUT,
                 command_timeout: float = 120.0,
                 command_profile: str = "ci"):
        self.root = Path(root).resolve()
        self.max_output = max_output
        self.command_timeout = command_timeout
        self.command_profile = _normalize_profile(command_profile)
        self.changed_files: list[str] = []
        self.command_audit: list[str] = []

    def command_audit_tail(self, *, n: int = 20) -> list[str]:
        limit = max(1, int(n))
        return self.command_audit[-limit:]

    def _audit_command(self, command: str, status: str, details: str = "") -> None:
        entry = f"{status}|{self.command_profile}|{command}"
        if details:
            entry += f"|{details}"
        self.command_audit.append(entry)
        if len(self.command_audit) > MAX_AUDIT_ENTRIES:
            self.command_audit = self.command_audit[-MAX_AUDIT_ENTRIES:]

    def _track(self, path: str) -> None:
        if path not in self.changed_files:
            self.changed_files.append(path)

    def read_file(self, path: str) -> str:
        p = resolve_in_root(self.root, path)
        if not p.is_file():
            return f"ERROR: not a file: {path}"
        return p.read_text(encoding="utf-8", errors="replace")[: self.max_output]

    def list_dir(self, path: str = ".") -> str:
        p = resolve_in_root(self.root, path)
        if not p.is_dir():
            return f"ERROR: not a directory: {path}"
        return "\n".join(sorted(
            c.name + ("/" if c.is_dir() else "") for c in p.iterdir()
        ))

    def write_file(self, path: str, content: str) -> str:
        p = resolve_in_root(self.root, path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        self._track(path)
        return f"OK: wrote {len(content)} chars to {path}"

    def edit_file(self, path: str, old: str, new: str) -> str:
        p = resolve_in_root(self.root, path)
        if not p.is_file():
            return f"ERROR: not a file: {path}"
        text = p.read_text(encoding="utf-8")
        count = text.count(old)
        if count == 0:
            return f"ERROR: old string not found in {path}"
        if count > 1:
            return f"ERROR: old string not unique in {path} ({count} matches)"
        p.write_text(text.replace(old, new, 1), encoding="utf-8")
        self._track(path)
        return f"OK: edited {path}"

    def run_command(self, command: str) -> str:
        command = str(command).strip()
        if not command:
            self._audit_command(command, "error", "empty-command")
            return "ERROR: empty command"
        if "\x00" in command:
            self._audit_command(command, "error", "null-byte")
            return "ERROR: command contains null byte"
        if _has_forbidden_token(command):
            self._audit_command(command, "blocked", "forbidden-token")
            return (
                f"ERROR: forbidden command token for profile='{self.command_profile}': "
                f"{_pretty_forbidden_tokens(command)}. "
                f"Allowed for profile='{self.command_profile}': {_profile_policy_summary(self.command_profile)}"
            )
        argv = shlex.split(command)
        if not argv:
            self._audit_command(command, "error", "empty-argv")
            return "ERROR: empty command"
        if argv[0] in {"git"}:
            if not _git_allowlist_valid(argv, root=self.root, profile=self.command_profile):
                self._audit_command(command, "blocked", "git-policy")
                return (
                    f"ERROR: git subcommand not allowed in profile='{self.command_profile}': "
                    f"{(argv[1] if len(argv) > 1 else '(none)')}. "
                    f"Allowed: {_git_allowlist_for_profile(self.command_profile)}. "
                    f"Allowed for profile='{self.command_profile}': {_profile_policy_summary(self.command_profile)}"
                )
        elif argv[0] in ALLOWED_INTERPRETERS:
            if _coerce_path_token(argv[0]) not in ALLOWED_INTERPRETERS:
                self._audit_command(command, "blocked", "interpreter-whitelist")
                return (
                    f"ERROR: interpreter not allowed in profile='{self.command_profile}': "
                    f"{argv[0]}. Allowed for profile='{self.command_profile}': {_profile_policy_summary(self.command_profile)}"
                )
            if not _py_allowlist_valid(argv, self.root, profile=self.command_profile):
                self._audit_command(command, "blocked", "python-policy")
                return (
                    f"ERROR: python execution profile not allowed: {argv}. "
                    f"Allowed for profile='{self.command_profile}': {_profile_policy_summary(self.command_profile)}"
                )
        else:
            self._audit_command(command, "blocked", "interpreter-unknown")
            return (
                f"ERROR: command not allowed in profile '{self.command_profile}': "
                f"{argv[0]}. Allowed for profile='{self.command_profile}': {_profile_policy_summary(self.command_profile)}"
            )
        if argv[0] in ALLOWED_INTERPRETERS and any(a == "-c" or a == "-" for a in argv[1:]):
            self._audit_command(command, "blocked", "python-stdin")
            return (
                f"ERROR: python -c / stdin-style execution blocked in profile='{self.command_profile}'. "
                f"Allowed for profile='{self.command_profile}': {_profile_policy_summary(self.command_profile)}"
            )
        if argv[0] in ALLOWED_INTERPRETERS and any(a == "pip" for a in argv):
            self._audit_command(command, "blocked", "python-pip")
            return (
                f"ERROR: pip is not allowed in profile='{self.command_profile}'. "
                f"Allowed for profile='{self.command_profile}': {_profile_policy_summary(self.command_profile)}"
            )
        try:
            proc = subprocess.run(
                argv, cwd=str(self.root), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=self.command_timeout,
            )
        except subprocess.TimeoutExpired:
            self._audit_command(command, "error", "timeout")
            return f"ERROR: command timed out after {self.command_timeout}s"
        except FileNotFoundError as exc:
            self._audit_command(command, "error", "command-not-found")
            return f"ERROR: command not found: {exc}"
        self._audit_command(command, "allowed", f"exit={proc.returncode}")
        out = (proc.stdout or "") + (proc.stderr or "")
        return f"[exit {proc.returncode}]\\n{out[: self.max_output]}"

    def dispatch(self, name: str, args: dict) -> str:
        try:
            if name == "read_file":
                return self.read_file(args["path"])
            if name == "list_dir":
                return self.list_dir(args.get("path", "."))
            if name == "write_file":
                return self.write_file(args["path"], args["content"])
            if name == "edit_file":
                return self.edit_file(args["path"], args["old"], args["new"])
            if name == "run_command":
                return self.run_command(args["command"])
            return f"ERROR: unknown tool: {name}"
        except GuardrailError as exc:
            return f"GUARDRAIL: {exc}"
        except KeyError as exc:
            return f"ERROR: missing argument {exc}"


TOOLS = [
    {
        "name": "read_file",
        "description": "Read a UTF-8 text file inside the repo. Returns file contents.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "repo-relative path"}},
            "required": ["path"],
        },
    },
    {
        "name": "list_dir",
        "description": "List entries of a directory inside the repo.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "repo-relative path (default '.')"}},
            "required": [],
        },
    },
    {
        "name": "write_file",
        "description": "Create or overwrite a file inside the repo with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": "Replace one unique occurrence of `old` with `new` in a repo file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "old": {"type": "string"},
                "new": {"type": "string"},
            },
            "required": ["path", "old", "new"],
        },
    },
    {
        "name": "run_command",
        "description": (
            "Run a profile-scoped allowlist of commands in the repo root. "
            "Default profile='ci' allows read-only git commands and bounded "
            "python verification commands. owner profile additionally allows "
            "git add/restore with explicit in-repo paths."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"],
        },
    },
]

