#!/usr/bin/env python3
"""Fail a release that ships something which only works where it was written.

Makes the clauses in `rules/cross-platform.md` executable. Scope, rule table, and why prose is
never matched: `tools/lib/portability.py`.

Usage:
  python3 tools/check_portability.py            # enforce — exit 1 on any finding
  python3 tools/check_portability.py --report   # list findings, exit 0
  python3 tools/check_portability.py --rules    # what every clause is checked for
  python3 tools/check_portability.py --path X   # one path, repo-relative
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import manifest as manifest_lib  # noqa: E402
from lib import portability  # noqa: E402


def main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="list findings and exit 0")
    parser.add_argument("--rules", action="store_true", help="describe every clause and exit")
    parser.add_argument("--path", default="", help="scan one path instead of everything shipped")
    args = parser.parse_args(argv[1:])

    root = manifest_lib.repo_root()

    if args.rules:
        print("Clauses of rules/cross-platform.md this gate enforces:\n")
        for clause, checks in sorted(portability.clauses().items()):
            print("  %s" % clause)
            for why in checks:
                print("      - %s" % why)
        print("\nEscape: an inline `portability-ok: <reason>` on the line or the one above it.")
        return 0

    findings = portability.scan(root, args.path)
    scanned = len(portability.shipped_paths(root))

    if not findings:
        print("check_portability: %d shipped file(s), nothing that would only work here" % scanned)
        return 0

    print("check_portability: %d finding(s) across %d shipped file(s)\n"
          % (len(findings), scanned), file=sys.stderr)
    for finding in findings:
        print(finding, file=sys.stderr)
        print(file=sys.stderr)
    return 0 if args.report else 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except (manifest_lib.ManifestMissing, manifest_lib.UnsafeEntry) as problem:
        # A base whose contract is gone or untrustworthy is exactly the base that needs a
        # recovery command, and a traceback is not one.
        sys.stderr.write(manifest_lib.explain_refusal(problem))
        sys.exit(2)

