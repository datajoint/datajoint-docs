"""Flag Markdown lists that will be swallowed into the preceding paragraph.

A list needs a blank line after a paragraph lead-in. Without one, this:

    **Addressing schemes:**
    - **Hash-addressed**: Path from content hash.
    - **Schema-addressed**: Path mirrors database structure.

renders as a single run-on <p> with literal dashes instead of a <ul>.  The
build does not warn, so the page just quietly looks wrong.

Only top-level lists directly under an ordinary paragraph are reported. A list
already inside a list block -- including one whose previous line is a wrapped
continuation of an earlier item -- is left alone, so tight lists stay tight.

Usage:
    python scripts/check_markdown_lists.py src          # report, exit 1 if any
    python scripts/check_markdown_lists.py src --fix    # insert the blank lines
"""

import re
import sys
from pathlib import Path

MARKER = re.compile(r"^(?:[-*+]\s+|\d+\.\s+)\S")   # top-level item, no indent
FENCE = re.compile(r"^\s*(```|~~~)")
BLOCK = re.compile(r"^\s*(#|>|\||:{3}|!{3}|<|$)")  # heading, quote, table, admonition, html

EXCLUDED_DIRS = {"api", "elements"}


def scan(text: str) -> tuple[str, list[int]]:
    """Return the corrected text and the 1-based line numbers that needed it."""
    lines = text.split("\n")
    out: list[str] = []
    fence: str | None = None
    in_list = False
    hits: list[int] = []

    for number, line in enumerate(lines, start=1):
        if match := FENCE.match(line):
            token = match.group(1)
            if fence is None:
                fence = token
            elif line.strip().startswith(fence):
                fence = None
            out.append(line)
            continue
        if fence is not None:
            out.append(line)
            continue

        blank = not line.strip()
        indented = line[:1].isspace()

        if MARKER.match(line):
            if not in_list and out and out[-1].strip():
                previous = out[-1]
                if not BLOCK.match(previous) and not previous.rstrip().endswith(("\\", "  ")):
                    out.append("")
                    hits.append(number)
            in_list = True
        elif in_list and not (blank or indented):
            # A flush-left paragraph line ends the list block.
            in_list = False

        out.append(line)

    return "\n".join(out), hits


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    apply_fix = "--fix" in sys.argv
    root = Path(args[0] if args else "src")

    total = 0
    touched = 0
    for path in sorted(root.rglob("*.md")):
        if EXCLUDED_DIRS & set(path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        fixed, hits = scan(text)
        if not hits:
            continue
        total += len(hits)
        touched += 1
        if apply_fix:
            path.write_text(fixed, encoding="utf-8")
            print(f"  fixed {len(hits):3d}  {path}")
        else:
            for number in hits:
                print(f"  {path}:{number}: list needs a blank line after the paragraph above")

    if not total:
        print("OK: no swallowed Markdown lists")
        return 0

    if apply_fix:
        print(f"\ninserted {total} blank line(s) across {touched} file(s)")
        return 0

    print(
        f"\n{total} swallowed list(s) in {touched} file(s). These render as run-on\n"
        "paragraphs with literal dashes. Run:\n\n"
        f"    python scripts/check_markdown_lists.py {root} --fix\n"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
