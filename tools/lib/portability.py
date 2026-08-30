#!/usr/bin/env python3
"""Make the cross-platform clauses executable instead of remembered.

`rules/cross-platform.md` is a HARD RULE that was enforced by human memory, and memory does not
scale: an audit of this kit's own PowerShell installer found three faults that each independently
broke a stock Windows machine, and a shell flag that had never worked went unnoticed for as long as
it existed. Every one of them violated a clause already written down.

**Scope is not a new concept.** Tier 1 is exactly what `.engine-manifest.yml` ships — `engine:` plus
`template:`, minus `exclude:`. Nothing is labelled and nothing is decided here; the manifest already
says which paths reach machines nobody in this repository will ever see.

**Rules match code, never prose.** Shell and PowerShell comments, python comments and docstrings are
blanked before matching, and markdown is read only inside fenced blocks that name a language. A
document that *describes* a banned construct — `rules/cross-platform.md` lists every one of them —
is therefore never a finding.

**One escape, and it is loud.** An inline `portability-ok: <reason>` on the offending line or the
line directly above it, with the reason mandatory. There is no allowlist file: a second escape
mechanism is a second place to look, and an exemption nobody reads is how a rule quietly stops
applying.

Two files are not scanned, for the same reason prose is blanked, and they are named rather than
patterned: this module, whose rule table necessarily contains every construct it forbids, and
`tools/tests/`, whose fixtures are wrong on purpose.
"""

from __future__ import annotations

import re
from pathlib import Path

from . import manifest as manifest_lib

# Suffix → the language whose comment syntax and rules apply.
SCOPE_BY_SUFFIX = {".sh": "shell", ".bash": "shell", ".py": "python", ".ps1": "powershell"}
# Fence tag → scope, for code inside markdown.
SCOPE_BY_FENCE = {
    "bash": "shell", "sh": "shell", "shell": "shell",
    "powershell": "powershell", "ps1": "powershell",
    "python": "python", "py": "python",
}
# Text kinds worth reading at all. Anything else is treated as binary and skipped.
TEXT_SUFFIXES = frozenset({".md", ".sh", ".bash", ".py", ".ps1", ".yml", ".yaml", ".json", ".txt"})
NOT_SCANNED = ("tools/lib/portability.py", "tools/tests")
ESCAPE = re.compile(r"portability-ok:\s*\S")


class Rule:
    """One machine-checkable construct, tied to the canon clause that forbids it."""

    def __init__(self, clause, scope, pattern, why, instead, kind="line"):
        self.clause = clause
        self.scope = scope
        self.pattern = re.compile(pattern) if pattern else None
        self.why = why
        self.instead = instead
        self.kind = kind

    def __repr__(self):
        return "Rule(%s, %s)" % (self.clause, self.scope)


class Finding:
    def __init__(self, path, line, rule, text):
        self.path, self.line, self.rule, self.text = path, line, rule, text

    def __str__(self):
        where = "%s:%d" % (self.path, self.line) if self.line else self.path
        return "%s  [%s] %s\n    %s\n    instead: %s" % (
            where, self.rule.clause, self.rule.why, self.text.strip()[:110], self.rule.instead)


LINE_RULES = (
    # -- shell: constructs absent from the bash 3.2 macOS still ships -----------------------
    Rule("CP-2", "shell", r"\b(mapfile|readarray)\b",
         "a bash 4 builtin; macOS ships bash 3.2 as /bin/bash",
         "read line by line with `while IFS= read -r`"),
    Rule("CP-2", "shell", r"\bdeclare\s+-A\b",
         "associative arrays are bash 4",
         "parallel arrays, or a python helper"),
    Rule("CP-2", "shell", r"\$\{[A-Za-z_][A-Za-z0-9_]*(\^\^|,,)",
         "case conversion in a parameter expansion is bash 4",
         "`tr 'a-z' 'A-Z'`"),
    # -- shell: commands whose flags differ between GNU and BSD -----------------------------
    Rule("CP-2", "shell", r"\breadlink\s+-f\b",
         "`readlink -f` is GNU-only; BSD readlink has no such flag",
         "`cd \"$(dirname \"$0\")\" && pwd`"),
    Rule("CP-2", "shell", r"\bsed\s+-i\b",
         "in-place sed needs an empty argument on BSD and rejects one on GNU",
         "write to a temp file and move it, or use python"),
    Rule("CP-2", "shell", r"\bstat\s+-[cf]\b",
         "`stat -c` is GNU, `stat -f` is BSD, and each rejects the other",
         "python's `Path.stat()`"),
    Rule("CP-2", "shell", r"\bgrep\s+-[A-Za-z]*P\b",
         "`grep -P` is absent from BSD grep",
         "`grep -E`, or python"),
    # -- any code: a path that only exists on the machine it was written on -----------------
    Rule("CP-1", "shell", r"(/Users/|/home/[a-z]|[A-Za-z]:\\\\)",
         "a hardcoded absolute path from one machine",
         "resolve it from HOME, from the script's own location, or from config"),
    Rule("CP-1", "python", r"(/Users/|/home/[a-z]|[A-Za-z]:\\\\)",
         "a hardcoded absolute path from one machine",
         "`Path.home()`, `Path(__file__).resolve()`, or config"),
    # -- python: text decoded through whatever the platform happens to default to -----------
    Rule("CP-5", "python", r"\.(read_text|write_text)\(\s*\)",
         "no encoding given, so Windows decodes through its ANSI code page",
         "`encoding=\"utf-8\"`"),
    Rule("CP-5", "python", r"\.(read_text|write_text)\((?![^()]*encoding=)[^()]+\)",
         "no encoding given, so Windows decodes through its ANSI code page",
         "`encoding=\"utf-8\"`"),
    Rule("CP-5", "python", r"\bopen\((?![^()]*(encoding=|[\"']\w*b\w*[\"']))[^()]*\)",
         "no encoding given and not opened as binary",
         "`encoding=\"utf-8\"`, or an explicit binary mode"),
    # -- powershell: the two faults that made this kit's installer unrunnable ----------------
    Rule("CP-5", "powershell", r"Get-Content(?![^\n]*-Encoding)",
         "Windows PowerShell 5.1 reads through the ANSI code page without -Encoding, so a "
         "read-modify-write corrupts every non-ASCII character",
         "`Get-Content -Raw -Encoding UTF8`"),
    Rule("CP-6", "powershell", r"(?:^|[ (\t=])(git|gh)\s+-?[A-Za-z]",
         "a native command writes ordinary progress to stderr, which a stop-on-error shell "
         "turns into a terminating error",
         "route it through the helper that relaxes $ErrorActionPreference for the call"),
)

FILE_RULES = (
    Rule("CP-3", "any", None,
         "CRLF line endings; bash and python from a Windows checkout break on them",
         "LF, which `.gitattributes` enforces", kind="file"),
    Rule("CP-5", "powershell", None,
         "non-ASCII in a .ps1 with no byte-order mark; Windows PowerShell 5.1 then parses its "
         "own literals through the ANSI code page",
         "save the file as UTF-8 with a BOM", kind="file"),
)

# Lines whose native call is the helper itself, or a check for the command's existence.
_NATIVE_EXEMPT = re.compile(r"Git-Q|Invoke-Native|Get-Command")


def strip_comments(line: str, scope: str) -> str:
    """Blank the commented tail of one line, respecting quotes.

    A `#` inside a string is data, not a comment — blanking it would hide a real finding, and
    treating a quoted `#` as a comment would hide the rest of the line from every rule.
    """
    if scope not in ("shell", "python", "powershell"):
        return line
    out, quote = [], None
    for index, char in enumerate(line):
        if quote:
            out.append(char)
            if char == quote and (index == 0 or line[index - 1] != "\\"):
                quote = None
            continue
        if char in "'\"":
            quote = char
            out.append(char)
            continue
        if char == "#":
            break
        out.append(char)
    return "".join(out)


def code_lines(text: str, scope: str):
    """Yield (line number, code-only text, raw text) for every line that can hold a finding."""
    lines = text.splitlines()
    if scope == "markdown":
        yield from _fenced_code(lines)
        return
    in_docstring = None
    for number, raw in enumerate(lines, 1):
        if scope == "python":
            stripped = raw.strip()
            if in_docstring:
                if in_docstring in stripped:
                    in_docstring = None
                yield number, "", raw
                continue
            for marker in ('"""', "'''"):
                if stripped.startswith(marker) and stripped.count(marker) == 1:
                    in_docstring = marker
                    yield number, "", raw
                    break
            else:
                yield number, strip_comments(raw, scope), raw
                continue
            continue
        yield number, strip_comments(raw, scope), raw


def _fenced_code(lines):
    """Only fenced blocks that name a language are code; everything else in a document is prose."""
    scope, number = None, 0
    for number, raw in enumerate(lines, 1):
        fence = re.match(r"^\s*```+\s*([A-Za-z0-9_-]*)", raw)
        if fence:
            scope = None if scope else SCOPE_BY_FENCE.get(fence.group(1).lower())
            continue
        if scope:
            yield number, strip_comments(raw, scope), raw, scope


def _escaped(raw_lines, index) -> bool:
    """An inline `portability-ok: <reason>` on the line, or the line directly above it."""
    if ESCAPE.search(raw_lines[index]):
        return True
    return index > 0 and ESCAPE.search(raw_lines[index - 1]) is not None


def scan_file(root: Path, relpath: str) -> list:
    """Every finding in one shipped file."""
    if any(relpath == skip or relpath.startswith(skip + "/") for skip in NOT_SCANNED):
        return []
    path = root / relpath
    suffix = path.suffix.lower()
    if suffix not in TEXT_SUFFIXES or not path.is_file():
        return []

    raw_bytes = path.read_bytes()
    findings = []

    for rule in FILE_RULES:
        if rule.clause == "CP-3" and b"\r\n" in raw_bytes:
            findings.append(Finding(relpath, 0, rule, "the file's bytes"))
        if rule.clause == "CP-5" and suffix == ".ps1":
            if any(byte > 127 for byte in raw_bytes) and not raw_bytes.startswith(b"\xef\xbb\xbf"):
                findings.append(Finding(relpath, 0, rule, "the file's first bytes"))

    text = raw_bytes.decode("utf-8-sig", errors="replace")
    raw_lines = text.splitlines()
    scope = SCOPE_BY_SUFFIX.get(suffix, "markdown" if suffix == ".md" else None)
    if scope is None:
        return findings

    for entry in code_lines(text, scope):
        if len(entry) == 4:
            number, code, raw, line_scope = entry
        else:
            number, code, raw = entry
            line_scope = scope
        if not code.strip() or _escaped(raw_lines, number - 1):
            continue
        for rule in LINE_RULES:
            if rule.scope != line_scope or not rule.pattern.search(code):
                continue
            if rule.clause == "CP-6" and _NATIVE_EXEMPT.search(code):
                continue
            findings.append(Finding(relpath, number, rule, raw))
    return findings


def shipped_paths(root: Path) -> list:
    """Tier 1: what the manifest ships, with the person's space subtracted."""
    shipped = set()
    for section in ("engine", "template"):
        for entry in manifest_lib.read_section(section, root):
            target = root / entry.rstrip("/")
            if target.is_dir():
                shipped |= {str(p.relative_to(root)).replace("\\", "/")
                            for p in target.rglob("*") if p.is_file()}
            elif target.is_file():
                shipped.add(entry)
    excluded = manifest_lib.read_section("exclude", root)
    return sorted(p for p in shipped if not manifest_lib.covers(excluded, p))


def scan(root: Path, only: str = "") -> list:
    """Every finding across tier 1, or under one path when `only` is given."""
    paths = shipped_paths(root)
    if only:
        prefix = only.rstrip("/")
        paths = [p for p in paths if p == prefix or p.startswith(prefix + "/")]
    findings = []
    for relpath in paths:
        findings.extend(scan_file(root, relpath))
    return findings


def clauses() -> dict:
    """Every canon clause this gate enforces, with what it checks for."""
    table = {}
    for rule in LINE_RULES + FILE_RULES:
        table.setdefault(rule.clause, []).append(rule.why)
    return table
