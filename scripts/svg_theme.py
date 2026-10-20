"""Make figure SVGs follow the site's palette toggle, not the OS preference.

Every themed figure in ``src/images`` carries its dark palette in an
``@media (prefers-color-scheme: dark)`` block.  That works when the SVG is
viewed on its own (GitHub, a README, a raw link), but the figures are embedded
with ``<img src=...>``, and an SVG loaded that way is a separate document: its
stylesheet sees the *operating system* preference and never sees the
``data-md-color-scheme`` attribute that Material's light/dark toggle flips on
the host page.  A reader on a dark desktop who switches the site to light got a
dark figure on a light page, and vice versa.

This hook keeps one source file per figure and resolves the theme at build
time instead:

* ``on_post_build`` writes two derived variants next to each themed SVG --
  ``<name>.light.svg`` (the dark block dropped) and ``<name>.dark.svg`` (the
  dark block applied unconditionally).
* ``on_post_page`` rewrites each ``<img>`` that points at a themed SVG into a
  pair of ``<img>`` tags marked ``#only-light`` / ``#only-dark``; the rules in
  ``extra.css`` show exactly one of them per scheme.

The original SVG is still published unchanged, so external references to it
keep working and keep adapting to the OS preference.
"""

import re
from pathlib import Path

IMAGES_SUBDIR = "images"

# Tolerates both hand-authored spacing and Mermaid's minified output.
MEDIA_OPEN = re.compile(
    r"@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{", re.IGNORECASE
)

IMG_TAG = re.compile(r"<img\b[^>]*?>", re.IGNORECASE)
IMG_SRC = re.compile(r"""\bsrc\s*=\s*(["'])(.+?)\1""", re.IGNORECASE)

# Figures are keyed by their path under ``images/`` rather than by bare stem, so
# that two figures of the same name in different subdirectories cannot collide.
IMAGES_PREFIX = re.compile(rf"(?:^|/){re.escape(IMAGES_SUBDIR)}/")

# Populated by on_files, consumed by on_post_page: the keys of the figures
# that actually carry a dark block.
_themed: set = set()


def _image_key(path):
    """Return a figure's path relative to the images directory, or None."""
    match = IMAGES_PREFIX.search(path)
    return path[match.end() :] if match else None


def _split_media_block(text):
    """Return (before, inner, after) around the dark block, or None."""
    match = MEDIA_OPEN.search(text)
    if not match:
        return None
    depth = 1
    i = match.end()
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    if depth:
        raise ValueError("unbalanced braces in prefers-color-scheme block")
    return text[: match.start()], text[match.end() : i - 1], text[i:]


def variants(text):
    """Return (light, dark) renderings of a themed SVG, or None if unthemed."""
    split = _split_media_block(text)
    if split is None:
        return None
    before, inner, after = split
    return before + after, before + inner + after


def on_files(files, config):
    _themed.clear()
    for file in files:
        if not file.src_uri.startswith(f"{IMAGES_SUBDIR}/"):
            continue
        if not file.src_uri.endswith(".svg"):
            continue
        if MEDIA_OPEN.search(Path(file.abs_src_path).read_text(encoding="utf-8")):
            _themed.add(file.src_uri[len(IMAGES_SUBDIR) + 1 :])
    return files


def on_post_page(output, page, config):
    if not _themed:
        return output

    def rewrite(match):
        tag = match.group(0)
        src = IMG_SRC.search(tag)
        if not src:
            return tag
        path = src.group(2)
        # Strip any query or fragment before testing and slicing.  The variants
        # carry their own #only-light / #only-dark marker, which the CSS keys on,
        # so whatever the author wrote there cannot survive the rewrite anyway.
        bare = path.split("#", 1)[0].split("?", 1)[0]
        if not bare.lower().endswith(".svg"):
            return tag
        key = _image_key(bare)
        if key is None or key not in _themed:
            return tag
        base = bare[: -len(".svg")]
        light = IMG_SRC.sub(lambda _: f'src="{base}.light.svg#only-light"', tag, count=1)
        dark = IMG_SRC.sub(lambda _: f'src="{base}.dark.svg#only-dark"', tag, count=1)
        return light + dark

    return IMG_TAG.sub(rewrite, output)


def on_post_build(config):
    images = Path(config["site_dir"]) / IMAGES_SUBDIR
    if not images.is_dir():
        return
    for svg in sorted(images.rglob("*.svg")):
        if svg.name.endswith((".light.svg", ".dark.svg")):
            continue
        pair = variants(svg.read_text(encoding="utf-8"))
        if pair is None:
            continue
        light, dark = pair
        svg.with_suffix(".light.svg").write_text(light, encoding="utf-8")
        svg.with_suffix(".dark.svg").write_text(dark, encoding="utf-8")
