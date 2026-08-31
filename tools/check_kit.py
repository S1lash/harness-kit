#!/usr/bin/env python3
"""Author-side gate: prove this kit can be shipped before anyone runs it.

Every failure below is one a person would otherwise meet on their own machine, where nobody can
see it and they cannot diagnose it. The discipline is the author's tax; the point of paying it
here is that the people running the kit never do.

Structural checks run anywhere, including on a person's base — that is what `/harness-doctor`
calls. The `--authoring` checks compare this working tree against the release branch and only make
sense in the kit's own repository; run them before every release.

The checks themselves live in `tools/lib/kitchecks.py`. This file decides only how a person
hears about them: what to run, how a failure reads, and what to say when the contract that
makes any of it possible is missing.

Usage:
  python3 tools/check_kit.py                  # structural — safe on any base
  python3 tools/check_kit.py --authoring      # everything, before shipping a release
  python3 tools/check_kit.py --authoring --since <ref>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib import kitchecks  # noqa: E402
from lib import manifest as manifest_lib  # noqa: E402


def report(found, counts, authoring: bool) -> int:
    """Say what was found, to the person who is actually reading it."""
    for text in found.notes:
        print("  (%s)" % text)
    if not found:
        scope = "ready to ship" if authoring else "structurally sound"
        print("check_kit: %s — %d engine paths, %d templates, %d retired" % ((scope,) + counts))
        return 0
    # An author is shipping; a person is being told about their own base. The same wording for
    # both reads to the second as though their base were a release candidate.
    verdict = "this kit is not ready to ship" if authoring else "this base has something to fix"
    print("check_kit: %d problem(s) — %s\n" % (len(found), verdict), file=sys.stderr)
    for failure in found:
        where = failure.where
        if failure.line:
            where = "%s:%d" % (where, failure.line)
        print("  x %s %s" % (where, failure.what) if where else "  x %s" % failure.what,
              file=sys.stderr)
        if failure.why:
            print("    %s" % failure.why, file=sys.stderr)
    return 1


def main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default=kitchecks.RELEASE_REF)
    parser.add_argument("--authoring", action="store_true",
                        help="also run the release checks against --since")
    args = parser.parse_args(argv[1:])

    found, counts = kitchecks.run(manifest_lib.repo_root(), args.since, args.authoring)
    return report(found, counts, args.authoring)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except (manifest_lib.ManifestMissing, manifest_lib.UnsafeEntry) as problem:
        # A base whose contract is gone or untrustworthy is exactly the base that needs a
        # recovery command, and a traceback is not one.
        sys.stderr.write(manifest_lib.explain_refusal(problem))
        sys.exit(2)
