"""Validate internal links in the built site.

The source-level link check (lychee, see .github/workflows/linkcheck.yml)
resolves links relative to the *source* tree, so a link written as
``../explanation/entity-integrity.md`` passes -- that file does exist.  But
MkDocs serves pages from rewritten URLs, and mkdocs-jupyter does *not* rewrite
relative links inside notebook markdown cells.  Such a link therefore reaches
the browser verbatim and 404s.

This checker works on the built output instead, so it sees exactly what a
reader's browser would request: every ``<a href>`` must resolve to a real file
in the build, and any fragment must match an ``id`` on the target page.

Usage:
    python scripts/check_links.py [site_dir]
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urldefrag

# Pages generated from external sources; their internal anchors are not ours to fix.
EXCLUDED_PREFIXES = ("api/", "elements/")

EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.IGNORECASE)

# site_url is set, so MkDocs emits root-absolute links on some pages (e.g. 404.html).
ROOT_ABSOLUTE = "/"


class PageParser(HTMLParser):
    """Collect outgoing hrefs and available anchor ids from one page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if (value := attrs.get("id")) is not None:
            self.ids.add(value)
        # <a name="..."> is a legacy anchor form still emitted by some tooling.
        if tag == "a" and (value := attrs.get("name")) is not None:
            self.ids.add(value)
        if tag == "a" and (href := attrs.get("href")):
            self.hrefs.append(href)


def parse(path: Path) -> PageParser:
    parser = PageParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return parser


def resolve(site: Path, page: Path, href: str) -> Path:
    """Resolve href the way a browser would, from the page's served URL."""
    href = unquote(href)
    base = site if href.startswith(ROOT_ABSOLUTE) else page.parent
    target = (base / href.lstrip(ROOT_ABSOLUTE)).resolve()
    # A directory URL is served by its index.html.
    return target / "index.html" if target.is_dir() else target


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
    if not site.is_dir():
        print(f"error: no build output at {site}; run `mkdocs build` first")
        return 2

    pages = sorted(site.rglob("*.html"))
    if not pages:
        print(f"error: no HTML pages under {site}")
        return 2

    # Anchor ids are needed for link targets, so parse every page once up front.
    parsed = {page: parse(page) for page in pages}
    failures: list[str] = []

    for page, doc in parsed.items():
        rel_page = page.relative_to(site)
        if str(rel_page).startswith(EXCLUDED_PREFIXES):
            continue
        for href in doc.hrefs:
            if EXTERNAL.match(href):
                continue
            path, fragment = urldefrag(href)
            if not path:
                continue
            target = resolve(site, page, path)
            if str(Path(target).relative_to(site) if target.is_relative_to(site) else "").startswith(
                EXCLUDED_PREFIXES
            ):
                continue
            if not target.is_file():
                failures.append(f"{rel_page}: '{href}' -> no such page")
                continue
            if fragment:
                target_doc = parsed.get(target) or parse(target)
                if fragment not in target_doc.ids:
                    failures.append(f"{rel_page}: '{href}' -> no anchor '#{fragment}'")

    if failures:
        print(f"{len(failures)} broken internal link(s) in the built site:\n")
        for failure in failures:
            print(f"  {failure}")
        print(
            "\nNote: links in notebook markdown cells are NOT rewritten by "
            "mkdocs-jupyter.\nWrite them as built-site URLs: directory-style, no "
            ".md/.ipynb extension,\nwith depth counted from the page URL."
        )
        return 1

    print(f"OK: internal links resolve across {len(pages)} built pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
