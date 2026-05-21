#!/usr/bin/env python3
"""
Verify that every executed notebook's DataJoint connection banner
matches the version configured in mkdocs.yaml (extra.datajoint_version).

The banner DataJoint prints on connection looks like:
    [2026-02-19 18:32:59] DataJoint 2.2.2 connected to postgres@postgres:5432

We accept any patch within the configured major.minor (e.g., "2.2"
matches 2.2.0, 2.2.1, 2.2.2, ...). Banners with a different major.minor
fail the check.

Notebooks with no banner are skipped (they may not connect to a database).

Exit codes:
    0 - all banners current (or absent)
    1 - one or more notebooks stale
    2 - configuration / parsing error
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BANNER_RE = re.compile(r"DataJoint\s+(\d+)\.(\d+)\.(\d+)\s+connected")
# mkdocs.yaml uses Material-specific YAML tags (!!python/name:...) that PyYAML's
# safe_load rejects, so pull the version line out with a regex instead.
VERSION_KEY_RE = re.compile(
    r'^\s*datajoint_version:\s*["\']?(\d+)\.(\d+)(?:\.\d+)?["\']?',
    re.MULTILINE,
)


def load_target_version(mkdocs_yaml: Path) -> tuple[int, int]:
    text = mkdocs_yaml.read_text()
    m = VERSION_KEY_RE.search(text)
    if not m:
        print(
            f"error: could not find datajoint_version in {mkdocs_yaml}",
            file=sys.stderr,
        )
        sys.exit(2)
    return int(m.group(1)), int(m.group(2))


def iter_banner_versions(notebook_path: Path):
    with notebook_path.open() as f:
        nb = json.load(f)
    for cell in nb.get("cells", []):
        for out in cell.get("outputs", []) or []:
            chunks = []
            text = out.get("text")
            if isinstance(text, list):
                chunks.extend(text)
            elif isinstance(text, str):
                chunks.append(text)
            data = out.get("data", {}) or {}
            plain = data.get("text/plain")
            if isinstance(plain, list):
                chunks.extend(plain)
            elif isinstance(plain, str):
                chunks.append(plain)
            for chunk in chunks:
                for m in BANNER_RE.finditer(chunk):
                    yield (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    mkdocs_yaml = repo / "mkdocs.yaml"
    target_major, target_minor = load_target_version(mkdocs_yaml)

    search_dirs = [repo / "src" / "tutorials", repo / "src" / "how-to"]
    notebooks: list[Path] = []
    for d in search_dirs:
        if d.exists():
            notebooks.extend(p for p in d.rglob("*.ipynb") if ".ipynb_checkpoints" not in str(p))
    notebooks.sort()

    stale: dict[Path, set[tuple[int, int, int]]] = {}
    checked = 0
    for nb in notebooks:
        had_banner = False
        for ver in iter_banner_versions(nb):
            had_banner = True
            if ver[0] != target_major or ver[1] != target_minor:
                stale.setdefault(nb.relative_to(repo), set()).add(ver)
        if had_banner:
            checked += 1

    if stale:
        print(f"Stale DataJoint connection banner(s) (target: {target_major}.{target_minor}.x):")
        for path, vers in sorted(stale.items()):
            for ver in sorted(vers):
                print(f"  {path}: found {ver[0]}.{ver[1]}.{ver[2]}")
        print(f"\nRe-execute notebooks with MODE=EXECUTE or MODE=EXECUTE_PG.")
        return 1

    print(f"OK: {checked} notebook(s) with banners are on DataJoint {target_major}.{target_minor}.x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
