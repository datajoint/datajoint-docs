"""Generate the fan-out ingestion figure for ``src/explanation/fan-out-ingestion.md``.

Why this figure is hand-built when every other diagram in the docs is ``dj.Diagram``
output
-----------------------------------------------------------------------------------
Because ``dj.Diagram`` cannot draw it. The subject of the page is a ``make()`` that
inserts into tables it holds **no foreign key to**, so there is no dependency for the
renderer to find: point ``dj.Diagram`` at this schema and ``Subject``, ``Session`` and
``Recording`` come out as three unconnected nodes. That absence is exactly what the page
is about, and a figure has to show the write that the dependency graph does not record.

So the notation is borrowed rather than emitted. Everything a reader already knows how
to read is kept identical to generated diagrams -- see ``src/images/rwm-legend.svg`` and
``how-to/read-diagrams.ipynb``:

* **Tier by shape and color.** ``Manual`` is a green rounded box, ``Imported`` a blue
  ellipse. Fills, strokes and text are the tier colors ``dj.Diagram`` itself emits
  (datajoint-python #1544), light and dark.
* **Dependency edges are navy and carry no arrowheads** -- direction follows the layout.
* **Edge weight is cardinality.** ``RecordingFile -> Ingest`` is thick: ``Ingest``
  declares only ``-> RecordingFile``, so the foreign key covers its whole primary key.
* **An underlined name introduces a primary-key attribute of its own.** ``Ingest`` is not
  underlined -- it inherits its entire key -- while the three fanned-to tables are.

The one departure, and it is the point of the figure: **the fan-out writes are drawn
dashed and with arrowheads.** A real dependency edge has no arrowhead, so the arrowhead
is what tells the reader this is not one. The bronze used for renamed foreign keys is
deliberately avoided; these are not foreign keys at all.

The tables and the ``source_file`` attribute match the code sample on the page, so the
figure and the snippet can be read against each other.

Usage
-----
No database and no graphviz needed, unlike ``gen_pipeline_diagrams.py``::

    python scripts/gen_fanout_diagram.py

Writes ``src/images/fan-out-ingestion.svg``. Idempotent.

Known limitation, shared with every committed figure here: the dark palette is selected
by ``prefers-color-scheme``, so it follows the reader's operating system rather than the
site's own light/dark toggle. An ``<img>``-embedded SVG cannot see the page's
``data-md-color-scheme``. Consistent with the other diagrams; not solved here.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "src" / "images" / "fan-out-ingestion.svg"

W, H = 900, 400

# Tier colors as dj.Diagram emits them (fill, stroke, text) -- datajoint-python #1544.
TIER = {
    "manual":   ("#E8F0E9", "#3E7A52", "#28513A"),
    "imported": ("#E0F4FC", "#00A0DF", "#00537A"),
}
TIER_DARK = {
    "manual":   ("#16281F", "#6BBF94", "#BCE6CF"),
    "imported": ("#0F2433", "#33B8E8", "#BEE7F9"),
}
EDGE, EDGE_DARK = "#171C39", "#AEB6C2"      # navy, and its dark counterpart
GREY, GREY_DARK = "#808285", "#9DA0A4"      # annotations
BG, BG_DARK = "#FFFFFF", "#161A21"

FONT = "Helvetica, sans-serif"              # the face dj.Diagram emits; never monospace

svg = []


def name(x, y, text, tier, size=15, underline=False):
    """A table name. Carries the tier class so the dark block can restyle it -- a CSS
    rule outranks a presentation attribute, so the inline fill stays the light default.
    """
    svg.append(f'<text class="t-{tier}" x="{x}" y="{y}" text-anchor="middle" '
               f'font-size="{size}" font-weight="600" fill="{TIER[tier][2]}">{text}</text>')
    if underline:
        half = len(text) * size * 0.55 / 2
        svg.append(f'<line class="u-{tier}" x1="{x - half:.1f}" y1="{y + 3.5}" '
                   f'x2="{x + half:.1f}" y2="{y + 3.5}" stroke="{TIER[tier][2]}" '
                   f'stroke-width="1.1"/>')


def manual(cx, cy, label, w=168, h=46, underline=True):
    f, s, _ = TIER["manual"]
    svg.append(f'<rect class="f-manual" x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" '
               f'height="{h}" rx="7" fill="{f}" stroke="{s}" stroke-width="1.6"/>')
    name(cx, cy + 5, label, "manual", underline=underline)


def imported(cx, cy, label, rx=70, ry=26, underline=False):
    f, s, _ = TIER["imported"]
    svg.append(f'<ellipse class="f-imported" cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" '
               f'fill="{f}" stroke="{s}" stroke-width="1.6"/>')
    name(cx, cy + 5, label, "imported", underline=underline)


def main():
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
               f'viewBox="0 0 {W} {H}" font-family="{FONT}">')

    dark = "\n".join(
        f'    .f-{k} {{ fill: {v[0]}; stroke: {v[1]}; }}\n'
        f'    .t-{k} {{ fill: {v[2]}; }}\n'
        f'    .u-{k} {{ stroke: {v[2]}; }}' for k, v in TIER_DARK.items())
    svg.append(f"""<style>
  svg {{ background-color: {BG}; }}
  .edge {{ stroke: {EDGE}; fill: none; }}
  .note {{ fill: {GREY}; font-size: 12.5px; }}
  .arrow {{ fill: {EDGE}; }}
@media (prefers-color-scheme: dark) {{
    svg {{ background-color: {BG_DARK}; }}
    .edge {{ stroke: {EDGE_DARK}; }}
    .note {{ fill: {GREY_DARK}; }}
    .arrow {{ fill: {EDGE_DARK}; }}
{dark}
}}
</style>""")
    svg.append('<defs><marker id="wr" markerWidth="7" markerHeight="7" refX="6" '
               'refY="2.4" orient="auto">'
               '<path class="arrow" d="M0,0 L6,2.4 L0,4.8 Z"/></marker></defs>')

    CY = 150

    # the source record, and a genuine dependency: Ingest declares only -> RecordingFile,
    # so the foreign key covers its whole primary key -- a thick edge, no arrowhead.
    manual(112, CY, "RecordingFile")
    svg.append(f'<line class="edge" x1="198" y1="{CY}" x2="266" y2="{CY}" '
               f'stroke-width="3.2"/>')
    imported(336, CY, "Ingest")

    # the fan-out: three entry-point tables with no foreign key back to Ingest
    for label, yy in zip(["Subject", "Session", "Recording"], [56, CY, 244]):
        manual(752, yy, label)
        svg.append(f'<path class="edge" d="M410,{CY} C520,{CY} 556,{yy} 662,{yy}" '
                   f'stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#wr)"/>')
    svg.append(f'<text class="note" x="536" y="26" text-anchor="middle" '
               f'font-weight="600">insert + source_file</text>')
    svg.append(f'<text class="note" x="536" y="{CY + 118}" text-anchor="middle" '
               f'font-style="italic">no foreign key back to Ingest</text>')

    # legend
    ly = 330
    svg.append(f'<line class="edge" x1="24" y1="{ly - 26}" x2="{W - 24}" y2="{ly - 26}" '
               f'stroke-width="0.8" opacity="0.28"/>')
    f, s, _ = TIER["imported"]
    svg.append(f'<ellipse class="f-imported" cx="42" cy="{ly - 5}" rx="16" ry="8" '
               f'fill="{f}" stroke="{s}" stroke-width="1.4"/>')
    svg.append(f'<text class="note" x="68" y="{ly}">Imported</text>')
    f, s, _ = TIER["manual"]
    svg.append(f'<rect class="f-manual" x="152" y="{ly - 13}" width="32" height="16" '
               f'rx="7" fill="{f}" stroke="{s}" stroke-width="1.4"/>')
    svg.append(f'<text class="note" x="192" y="{ly}">Manual</text>')

    svg.append(f'<line class="edge" x1="300" y1="{ly - 5}" x2="340" y2="{ly - 5}" '
               f'stroke-width="3.2"/>')
    svg.append(f'<text class="note" x="348" y="{ly}">dependency (no arrowhead)</text>')
    svg.append(f'<line class="edge" x1="546" y1="{ly - 5}" x2="586" y2="{ly - 5}" '
               f'stroke-width="1.5" stroke-dasharray="6 4" marker-end="url(#wr)"/>')
    svg.append(f'<text class="note" x="594" y="{ly}">a write, not a dependency</text>')
    svg.append(f'<text class="note" x="68" y="{ly + 26}" font-style="italic">'
               f'an underlined name introduces a primary-key attribute of its own</text>')

    svg.append("</svg>")
    OUT.write_text("\n".join(svg) + "\n")
    print(f"{OUT.relative_to(Path.cwd())}: written")


if __name__ == "__main__":
    main()
