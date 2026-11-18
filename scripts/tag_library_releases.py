#!/usr/bin/env python3
"""
Tag this repository's main branch at each datajoint-python release.

For every published datajoint-python release, the docs tag of the same name
(e.g., v2.3.4) marks the last commit on main at the moment the release was
published: the documentation as it stood when that version shipped.

A release is tagged only if it was the newest version at its publish time.
Maintenance releases of an older line (e.g., 0.14.x published after 2.0) are
skipped, because main documented the newer line when they shipped. Releases
before MIN_VERSION predate the documentation on main.

Existing tags are never moved, so the script is safe to rerun; the first run
backfills every eligible release.

Usage:
    python scripts/tag_library_releases.py [--dry-run]

Requires the GitHub CLI (gh), authenticated, and full history of main.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

LIBRARY_REPO = "datajoint/datajoint-python"
MIN_VERSION = (2, 0, 0)
TAG_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def run(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def library_releases() -> list[tuple[str, tuple[int, int, int], str]]:
    """Published, non-prerelease releases as (tag, version, published_at), oldest first."""
    out = run(
        "gh", "release", "list",
        "--repo", LIBRARY_REPO,
        "--exclude-drafts", "--exclude-pre-releases",
        "--limit", "1000",
        "--json", "tagName,publishedAt",
    )
    releases = []
    for r in json.loads(out):
        m = TAG_RE.match(r["tagName"])
        if m and r["publishedAt"]:
            releases.append((r["tagName"], tuple(map(int, m.groups())), r["publishedAt"]))
    return sorted(releases, key=lambda r: r[2])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dry-run", action="store_true", help="print the tags without creating them")
    args = parser.parse_args()

    existing = set(run("git", "tag", "--list").split())
    newest = (0, 0, 0)
    to_push = []
    for tag, version, published_at in library_releases():
        if version <= newest:
            continue  # maintenance release of an older line
        newest = version
        if version < MIN_VERSION or tag in existing:
            continue
        commit = run("git", "rev-list", "-1", "--first-parent", f"--before={published_at}", "origin/main")
        if not commit:
            print(f"warning: no commit on main before {tag} ({published_at})", file=sys.stderr)
            continue
        print(f"{tag}  {commit[:8]}  (library published {published_at})")
        if not args.dry_run:
            run("git", "tag", tag, commit)
            to_push.append(f"refs/tags/{tag}")

    if to_push:
        run("git", "push", "origin", *to_push)
    elif not args.dry_run:
        print("all releases already tagged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
