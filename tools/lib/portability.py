#!/usr/bin/env python3
"""Make the cross-platform clauses executable instead of remembered.

`rules/cross-platform.md` is a HARD RULE that was enforced by human memory, and memory does not
scale: an audit of this kit's own PowerShell installer found three faults that each independently
broke a stock Windows machine, and a shell flag that had never worked went unnoticed for as long as
it existed. Every one of them violated a clause already written down.

**Scope is not a new concept.** Tier 1 is exactly what `.engine-manifest.yml` ships — `engine:` plus
`template:`. Nothing is labelled and nothing is decided here; the manifest already says which paths
reach machines nobody in this repository will ever see. A `template:` entry inside an `exclude:`
directory still ships (`update.py` seeds it onto every base), so `template:` wins: one manifest must
not mean two different things to the updater and to the gate.

**Rules match code, never prose.** Comments are stripped and markdown is read only inside fenced
blocks that name a language, so a document that *describes* a banned construct — and
`rules/cross-platform.md` lists every one of them — is never a finding.

Which string literals count as code differs by language, because the languages differ. Python goes
through the tokenizer, where a **triple-quoted** string is prose (a docstring, a help constant) and a
short literal is data the rules must see — `open(p, "rb")` is legitimate precisely because of what is
inside the quotes. A **shell** string is code: `"${name^^}"` still expands and `sh -c "sed -i ..."`
still runs. A **PowerShell** string is usually a message to a person, so the native-command clause
ignores it — an installer that tells someone to run `git push` is not calling git. The
hardcoded-path clause reads strings in every language, because a path is a string and nothing else.

**One escape, and it is loud.** An inline `portability-ok: <reason>` in a COMMENT on the offending
line or the line directly above it, with the reason mandatory. It has to be a comment: an escape
that a string literal or a line of prose can trigger by accident is the opposite of loud. There is
no allowlist file either — a second escape mechanism is a second place to look, and an exemption
nobody reads is how a rule quietly stops applying.

One directory is not scanned, and it is named rather than patterned: `tools/tests/`, whose fixtures
are wrong on purpose. This module is scanned like everything else, and the one line of it that
matches — the pattern for a hardcoded path — carries the ordinary escape. That is the mechanism
working, not an exception to it.
"""

from __future__ import annotations

import io
import re
import token as token_module
import tokenize
from pathlib import Path

from . import manifest as manifest_lib

# Suffix → the language whose comment syntax and rules apply.
SCOPE_BY_SUFFIX = {
    ".sh": "shell", ".bash": "shell", ".py": "python", ".ps1": "powershell",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
}
# Fence tag → scope, for code inside markdown.
SCOPE_BY_FENCE = {
    "bash": "shell", "sh": "shell", "shell": "shell",
    "powershell": "powershell", "ps1": "powershell",
    "python": "python", "py": "python",
    "javascript": "javascript", "js": "javascript",
}
# The comment marker each language uses, for stripping and for the escape.
COMMENT_MARKER = {"shell": "#", "powershell": "#", "python": "#", "javascript": "//"}
# Text kinds worth reading line by line. Everything else still gets the whole-file rules.
TEXT_SUFFIXES = frozenset({".md", ".sh", ".bash", ".py", ".ps1", ".js", ".mjs", ".cjs",
                           ".yml", ".yaml", ".json", ".txt"})
NOT_SCANNED = ("tools/tests",)
# Build products and caches sitting inside a shipped directory. They are not the kit's content:
# an update carries tracked files, and counting these misreports what ships.
NEVER_SHIPPED = frozenset({"__pycache__", ".venv", ".git", "node_modules", ".DS_Store"})
ESCAPE = re.compile(r"portability-ok:\s*\S")


class Rule:
    """One machine-checkable construct, tied to the canon clause that forbids it.

    `strings` says whether the rule reads string literals. Off by default — a banned command named
    inside a message the installer prints to a person is prose, not a call. On for the hardcoded-path
    rules, because a path is a string literal and nothing else.
    """

    def __init__(self, clause, scope, pattern, why, instead, kind="line",
                 strings=False, matcher=None):
        self.clause = clause
        self.scope = scope
        self.pattern = re.compile(pattern) if pattern else None
        self.why = why
        self.instead = instead
        self.kind = kind
        self.strings = strings
        self.matcher = matcher

    def hits(self, code: str) -> bool:
        if self.matcher:
            return self.matcher(code)
        return bool(self.pattern.search(code))

    def __repr__(self):
        return "Rule(%s, %s)" % (self.clause, self.scope)


class Finding:
    def __init__(self, path, line, rule, text):
        self.path, self.line, self.rule, self.text = path, line, rule, text

    def __str__(self):
        where = "%s:%d" % (self.path, self.line) if self.line else self.path
        return "%s  [%s] %s\n    %s\n    instead: %s" % (
            where, self.rule.clause, self.rule.why, self.text.strip()[:110], self.rule.instead)


# --- detectors that a regex cannot express ------------------------------------------------------

_TEXT_CALL = re.compile(r"\b(open|read_text|write_text)\s*\(")
_BINARY_MODE = re.compile(r"[\"'][rwxa+]*b[rwxa+]*[\"']")


def _balanced_args(code: str, start: int) -> str:
    """The argument text of the call whose `(` is at `start`, nesting included."""
    depth, index = 0, start
    while index < len(code):
        if code[index] == "(":
            depth += 1
        elif code[index] == ")":
            depth -= 1
            if depth == 0:
                return code[start + 1:index]
        index += 1
    return code[start + 1:]


def _text_io_without_encoding(code: str) -> bool:
    """A text read or write that lets the platform pick the encoding.

    A regex cannot do this: `open(os.path.join(root, name))` nests, and the argument list may run
    over several lines. Both are the ordinary shape of the call, so both have to be understood
    rather than pattern-matched.
    """
    for match in _TEXT_CALL.finditer(code):
        args = _balanced_args(code, match.end() - 1)
        if "encoding=" in args:
            continue
        if match.group(1) == "open" and _BINARY_MODE.search(args):
            continue
        return True
    return False


# portability-ok: this IS the pattern for a hardcoded path, not one.
_HARDCODED_PATH = r"(/Users/|/home/[a-z]|\b[A-Za-z]:\\{1,2}[^\\/:*?\"<>|\s]+\\{1,2})"

LINE_RULES = (
    # -- shell: constructs absent from the bash 3.2 macOS still ships -----------------------
    Rule("CP-2", "shell", r"\b(mapfile|readarray)\b",
         "a bash 4 builtin; macOS ships bash 3.2 as /bin/bash",
         "read line by line with `while IFS= read -r`", strings=True),
    Rule("CP-2", "shell", r"\bdeclare\s+(-[A-Za-z]*A|--[a-z])",
         "associative arrays are bash 4",
         "parallel arrays, or a python helper", strings=True),
    Rule("CP-2", "shell", r"\$\{[A-Za-z_][A-Za-z0-9_]*(\[[^]]*\])?(\^|,)",
         "case conversion in a parameter expansion is bash 4",
         "`tr 'a-z' 'A-Z'`", strings=True),
    # -- shell: commands whose flags differ between GNU and BSD -----------------------------
    # Each allows flags before the offending one (`sed -E -i`) and after it in the same cluster
    # (`grep -Pq`), and names the GNU long form, which BSD rejects outright.
    Rule("CP-2", "shell", r"\breadlink\s+(-\S+\s+)*(-[A-Za-z]*f|--canonicalize)",
         "`readlink -f` is GNU-only; BSD readlink has no such flag",
         "`cd \"$(dirname \"$0\")\" && pwd`", strings=True),
    Rule("CP-2", "shell", r"\bsed\s+(-\S+\s+)*(-[A-Za-z]*i|--in-place)",
         "in-place sed needs an empty argument on BSD and rejects one on GNU",
         "write to a temp file and move it, or use python", strings=True),
    Rule("CP-2", "shell", r"\bstat\s+(-\S+\s+)*(-[A-Za-z]*[cf]|--format|--printf)",
         "`stat -c` is GNU, `stat -f` is BSD, and each rejects the other",
         "python's `Path.stat()`", strings=True),
    Rule("CP-2", "shell", r"\bgrep\s+(-\S+\s+)*(-[A-Za-z]*P|--perl-regexp)",
         "`grep -P` is absent from BSD grep",
         "`grep -E`, or python", strings=True),
    # -- any code: a path that only exists on the machine it was written on -----------------
    # These read string literals: a hardcoded path is a string and nothing else.
    Rule("CP-1", "shell", _HARDCODED_PATH,
         "a hardcoded absolute path from one machine",
         "resolve it from HOME, from the script's own location, or from config", strings=True),
    Rule("CP-1", "python", _HARDCODED_PATH,
         "a hardcoded absolute path from one machine",
         "`Path.home()`, `Path(__file__).resolve()`, or config", strings=True),
    Rule("CP-1", "powershell", _HARDCODED_PATH,
         "a hardcoded absolute path from one machine",
         "`$HOME`, `$PSScriptRoot`, or the manifest", strings=True),
    Rule("CP-1", "javascript", _HARDCODED_PATH,
         "a hardcoded absolute path from one machine",
         "`os.homedir()`, `import.meta.url`, or config", strings=True),
    # -- python: text decoded through whatever the platform happens to default to -----------
    Rule("CP-5", "python", None,
         "no encoding given, so Windows decodes through its ANSI code page",
         "`encoding=\"utf-8\"`, or an explicit binary mode", matcher=_text_io_without_encoding),
    # -- powershell: the two faults that made this kit's installer unrunnable ----------------
    Rule("CP-5", "powershell", r"\b(Get-Content|gc)\b(?![^\n]*-Encoding)",
         "Windows PowerShell 5.1 reads through the ANSI code page without -Encoding, so a "
         "read-modify-write corrupts every non-ASCII character",
         "`Get-Content -Raw -Encoding UTF8`"),
    Rule("CP-6", "powershell", r"(?:^|[ (\t=;&|])(git|gh)(\.exe)?\s+[-$@A-Za-z`]",
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

# The helper that makes a native call safe, and the existence check that is not a call at all.
# Matched against the invoked word only, never the whole line: a message mentioning `Get-Command`
# must not disarm the rule for a bare `git push` sitting beside it.
_NATIVE_EXEMPT = re.compile(r"\b(Git-Q|Invoke-Native|Get-Command)\b")


# --- turning a file into lines a rule can be run against ----------------------------------------

def split_comment(line: str, scope: str):
    """(code, comment) for one line, respecting quotes.

    A `#` inside a string is data, not a comment — treating it as one would hide the rest of the
    line from every rule. Backslash escaping applies inside double quotes only: POSIX single quotes
    have none, so `tr -d '\\'` closes its quote where a naive one-character lookback would not.
    """
    marker = COMMENT_MARKER.get(scope)
    if not marker:
        return line, ""
    quote, index = None, 0
    while index < len(line):
        char = line[index]
        if quote:
            if char == "\\" and quote == '"' and scope != "powershell":
                index += 2
                continue
            if char == "`" and quote == '"' and scope == "powershell":
                index += 2
                continue
            if char == quote:
                quote = None
            index += 1
            continue
        if char in "'\"":
            quote = char
            index += 1
            continue
        if line.startswith(marker, index):
            return line[:index], line[index:]
        index += 1
    return line, ""


def blank_strings(code: str, scope: str) -> str:
    """Replace the contents of every string literal with spaces, keeping the line's length.

    Length is preserved so a rule that reads strings and one that does not can be run against the
    same line and report the same line number.
    """
    if scope not in COMMENT_MARKER:
        return code
    out, quote = [], None
    index = 0
    while index < len(code):
        char = code[index]
        if quote:
            if char == "\\" and quote == '"' and scope != "powershell":
                out.append("  ")
                index += 2
                continue
            if char == quote:
                quote = None
                out.append(char)
            else:
                out.append(" ")
            index += 1
            continue
        if char in "'\"":
            quote = char
            out.append(char)
            index += 1
            continue
        out.append(char)
        index += 1
    return "".join(out)


class Line:
    """One place a finding can be reported, with the two views a rule may ask for."""

    def __init__(self, number, code, raw, scope, comment=""):
        self.number = number
        self.code = code            # comment stripped, strings intact
        self.raw = raw
        self.scope = scope
        self.comment = comment

    def view(self, with_strings: bool) -> str:
        # Python arrives already masked by the tokenizer, which knows a docstring from a mode
        # string. Re-blanking it here would hide the `"rb"` that makes an unencoded open() fine.
        if with_strings or self.scope == "python":
            return self.code
        return blank_strings(self.code, self.scope)

    @property
    def escaped(self) -> bool:
        return bool(ESCAPE.search(self.comment))


def _python_lines(text: str):
    """Python read through the tokenizer: every string and comment blanked, calls joined.

    The line-based approach this replaces could not tell a one-line docstring from code, treated a
    triple-quoted help constant as executable, and could not see a call whose arguments ran over
    more than one line — the ordinary shape of `open(...)`. All three are the tokenizer's job.
    """
    lines = text.splitlines()
    masked = [list(line) for line in lines]
    comments = [""] * len(lines)
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # A shipped .py that will not tokenize is a bigger problem than this gate; fall back to
        # the honest approximation rather than silently scanning nothing.
        for number, raw in enumerate(lines, 1):
            code, comment = split_comment(raw, "python")
            yield Line(number, code, raw, "python", comment)
        return

    # The tokenizer's NEWLINE and ENDMARKER can sit a row past the last line of text.
    depth_at_end = [0] * (len(lines) + 3)
    depth = 0
    for tok in tokens:
        if tok.type == token_module.OP and tok.string in "([{":
            depth += 1
        elif tok.type == token_module.OP and tok.string in ")]}":
            depth -= 1
        prose = tok.type == tokenize.COMMENT or (
            tok.type == token_module.STRING
            and tok.string.lstrip("rbfuRBFU")[:3] in ('"""', "'''"))
        if prose:
            (srow, scol), (erow, ecol) = tok.start, tok.end
            if tok.type == tokenize.COMMENT:
                comments[srow - 1] = tok.string
            for row in range(srow, erow + 1):
                line = masked[row - 1]
                begin = scol if row == srow else 0
                end = ecol if row == erow else len(line)
                for col in range(begin, min(end, len(line))):
                    line[col] = " "
        if tok.end[0] < len(depth_at_end):
            depth_at_end[tok.end[0]] = depth

    # Join a call that spans lines onto the line it starts on, so a rule sees the whole call.
    number, total = 1, len(lines)
    while number <= total:
        code = "".join(masked[number - 1])
        last = number
        while last < total and depth_at_end[last] > 0:
            last += 1
            code += " " + "".join(masked[last - 1])
        yield Line(number, code, lines[number - 1], "python", comments[number - 1])
        for skipped in range(number + 1, last + 1):
            yield Line(skipped, "", lines[skipped - 1], "python", comments[skipped - 1])
        number = last + 1


def _fenced_lines(lines):
    """Only fenced blocks that name a language are code; everything else in a document is prose.

    The opening fence's length and tag are both remembered: a four-backtick block demonstrating a
    three-backtick one is a document about authoring, not shell to be run, and a fence that is
    never closed must not turn the rest of the file into code.
    """
    scope, opener = None, ""
    for number, raw in enumerate(lines, 1):
        fence = re.match(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_-]*)", raw)
        if fence:
            marks, tag = fence.group(1), fence.group(2).lower()
            if scope is None:
                scope, opener = SCOPE_BY_FENCE.get(tag), marks
                if scope is None:
                    opener = marks
                    scope = ""       # a fenced block we do not read, but must see closed
            elif len(marks) >= len(opener) and marks[0] == opener[0] and not tag:
                scope, opener = None, ""
            continue
        if scope:
            code, comment = split_comment(raw, scope)
            yield Line(number, code, raw, scope, comment)


def file_lines(text: str, scope: str):
    if scope == "python":
        yield from _python_lines(text)
    elif scope == "markdown":
        yield from _fenced_lines(text.splitlines())
    else:
        yield from _continued_lines(text.splitlines(), scope)


CONTINUATION = {"powershell": "`", "shell": "\\", "javascript": "\\"}


def _continued_lines(lines, scope):
    """A command continued onto the next line is still one command.

    Reading the halves separately is how correct code gets flagged — `Get-Content` whose
    `-Encoding` sits on the following line — and how a construct split mid-word escapes.
    """
    marker = CONTINUATION.get(scope)
    number, total = 1, len(lines)
    while number <= total:
        code, comment = split_comment(lines[number - 1], scope)
        last = number
        while marker and not comment and code.rstrip().endswith(marker) and last < total:
            code = code.rstrip()[:-1]
            last += 1
            more, comment = split_comment(lines[last - 1], scope)
            code += more
        yield Line(number, code, lines[number - 1], scope, comment)
        for skipped in range(number + 1, last + 1):
            yield Line(skipped, "", lines[skipped - 1], scope, "")
        number = last + 1


def scan_file(root: Path, relpath: str) -> list:
    """Every finding in one shipped file."""
    if any(relpath == skip or relpath.startswith(skip + "/") for skip in NOT_SCANNED):
        return []
    path = root / relpath
    if not path.is_file():
        return []
    suffix = path.suffix.lower()
    raw_bytes = path.read_bytes()
    findings = []

    # The whole-file rules run on EVERY shipped path, whatever its suffix. A CRLF in .gitattributes
    # — the file that enforces LF — or in a shipped .js is the same fault as one in a .sh.
    if b"\0" not in raw_bytes:
        for rule in FILE_RULES:
            if rule.clause == "CP-3" and b"\r\n" in raw_bytes:
                findings.append(Finding(relpath, 0, rule, "the file's bytes"))
            if rule.clause == "CP-5" and suffix == ".ps1":
                if any(b > 127 for b in raw_bytes) and not raw_bytes.startswith(b"\xef\xbb\xbf"):
                    findings.append(Finding(relpath, 0, rule, "the file's first bytes"))

    if suffix not in TEXT_SUFFIXES:
        return findings
    scope = SCOPE_BY_SUFFIX.get(suffix, "markdown" if suffix == ".md" else None)
    if scope is None:
        return findings

    previous = None
    for line in file_lines(raw_bytes.decode("utf-8-sig", errors="replace"), scope):
        escaped = line.escaped or (previous is not None and previous.escaped)
        previous = line
        if not line.code.strip() or escaped:
            continue
        for rule in LINE_RULES:
            if rule.scope != line.scope:
                continue
            code = line.view(rule.strings)
            if not rule.hits(code):
                continue
            if rule.clause == "CP-6" and _NATIVE_EXEMPT.search(code):
                continue
            findings.append(Finding(relpath, line.number, rule, line.raw))
    return findings


def shipped_paths(root: Path) -> list:
    """Tier 1: every path the manifest ships.

    `template:` beats `exclude:`. A template entry inside an excluded directory is still seeded onto
    every base by `update.py`, so treating it as the person's space here would let one manifest mean
    two different things to the updater and to this gate — and the files it ships would reach
    strangers unchecked.
    """
    templates = set(manifest_lib.read_section("template", root))
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
    return sorted(p for p in shipped
                  if not NEVER_SHIPPED & set(p.split("/"))
                  and (p in templates or not manifest_lib.covers(excluded, p)))


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
