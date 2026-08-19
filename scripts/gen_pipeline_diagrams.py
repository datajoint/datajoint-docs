"""Generate the pipeline diagrams used in the explanation pages.

Three committed figures come from one four-module example pipeline, defined in
``scripts/pipeline_example/``:

- ``pipeline-modules.svg`` — the whole pipeline at the table level, dashed
  clusters grouping each module (``src/explanation/data-pipelines.md``).
- ``pipeline-modules-collapsed.svg`` — the same pipeline at the module level,
  one node per schema, via ``Diagram.collapse()`` (same page).
- ``imaging-schema.svg`` — the ``imaging`` module on its own
  (``src/explanation/relational-workflow-model.md``, ``src/index.md``).

Keeping the pipeline in the repo makes the figures reproducible. The prose
describes specific edges, tiers, and table counts; those claims are only
checkable if the pipeline that produced them can be rebuilt.

Usage
-----
Needs a database and a graphviz ``dot`` on PATH::

    docker compose up -d postgres
    DJ_HOST=localhost DJ_PORT=5432 DJ_USER=postgres DJ_PASS=tutorial \
        DJ_BACKEND=postgresql DJ_USE_TLS=false \
        DJ_DATABASE_NAME=docs_diagrams \
        python scripts/gen_pipeline_diagrams.py

``DJ_DATABASE_NAME`` matters: on PostgreSQL a ``dj.Schema`` is a schema *within*
a database, so giving this example its own database lets it keep unprefixed
schema names without colliding with anything else on the server. Create it once
with ``createdb docs_diagrams``.

``--check`` renders without writing and exits non-zero if any committed figure
differs — suitable for CI. The example schemas are dropped afterwards unless
``--keep-schemas`` is given.

This reproduces the committed figures' nodes, tiers, edges, tooltips, clusters
and labels exactly, with the caveats below.

Reproducibility caveats
-----------------------
- **Give it its own database.** The schema names are unprefixed (``reference``,
  ``lab``, ``session``, ``imaging``) because ``dj.Diagram`` takes each cluster
  label from the Python module name and the two must agree. Unprefixed names are
  safe as long as ``DJ_DATABASE_NAME`` points at a database reserved for this
  example — separate databases can hold same-named schemas. Without it the
  connection lands in the default ``postgres`` database, where a pre-existing
  schema of the same name is picked up silently and rendered instead.
- **Padding entities depend on pydot.** Tooltip padding is emitted as ``&#160;``
  by the pydot that produced the committed figures and as literal spaces by
  4.0.1, which shows up as a whole-file diff with no visual change. Compare
  rendered content, not bytes, when the pydot version moves. Nothing pins pydot.
- **One collapsed edge is traversal-order dependent.** A collapsed edge inherits
  the attributes of whichever foreign key in its bundle is visited first
  (``diagram.py``, ``_collapse_graph``: ``if not new_graph.has_edge(...)``), with
  no aggregation over the bundle. Where a bundle mixes a primary and a secondary
  foreign key — ``lab -> session`` here, which bundles ``Subject -> Session``
  (primary) and ``User -> Session`` (secondary) — the edge renders solid or
  dashed depending on order alone. The committed figure has it solid; this script
  produces dashed. Both are outputs of the same renderer.

A non-empty diff after a DataJoint upgrade is the signal to review the notation
and the surrounding prose together — see issue #246.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

import datajoint as dj

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline_example import imaging, lab, reference, session  # noqa: E402

IMAGES = Path(__file__).resolve().parent.parent / "src" / "images"

MODULES = (reference, lab, session, imaging)

# dj.Diagram labels each node by resolving its table against this context. Passing
# the classes under their bare names keeps node labels unqualified ("Session", not
# "session.Session") while the cluster labels still come from the module names.
CONTEXT = {
    name: obj
    for module in MODULES
    for name, obj in vars(module).items()
    if isinstance(obj, type) and issubclass(obj, dj.Table)
}


def diagram(schema) -> dj.Diagram:
    return dj.Diagram(schema, context=CONTEXT)


def whole_pipeline() -> dj.Diagram:
    """The four modules unioned into one diagram."""
    result = diagram(reference.schema)
    for module in MODULES[1:]:
        result += diagram(module.schema)
    return result


FIGURES = {
    # Whole pipeline, table level: every module expanded.
    "pipeline-modules.svg": whole_pipeline,
    # Same pipeline, module level: one node per schema.
    "pipeline-modules-collapsed.svg": lambda: whole_pipeline().collapse(),
    # The imaging module on its own.
    "imaging-schema.svg": lambda: diagram(imaging.schema),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report figures that differ from the committed SVGs without writing them; "
        "exits 1 if any differ",
    )
    parser.add_argument(
        "--keep-schemas",
        action="store_true",
        help="leave the example schemas in the database (default: drop them)",
    )
    args = parser.parse_args()

    # Left-to-right layout, matching scripts/execute-notebooks.sh.
    with tempfile.TemporaryDirectory() as tmp:
        with dj.config.override(display__diagram_direction="LR"):
            rendered = {}
            for name, build in FIGURES.items():
                staged = Path(tmp) / name
                build().save(str(staged))
                rendered[name] = staged.read_text()

    if not args.keep_schemas:
        for module in reversed(MODULES):
            module.schema.drop(prompt=False)

    differs = []
    for name, svg in rendered.items():
        target = IMAGES / name
        old = target.read_text() if target.exists() else None
        if old == svg:
            print(f"  unchanged  {name}")
        elif args.check:
            differs.append(name)
            print(f"  DIFFERS    {name}")
        else:
            differs.append(name)
            target.write_text(svg)
            print(f"  written    {name}")

    if args.check and differs:
        print(
            f"\n{len(differs)} figure(s) differ from the committed SVGs. Re-run "
            "without --check to update them, then review the notation and the "
            "prose in src/explanation/ together (see #246). If only tooltip "
            "padding moved, check the pydot version first — see the module "
            "docstring.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    os.environ.setdefault("DJ_USE_TLS", "false")
    raise SystemExit(main())
