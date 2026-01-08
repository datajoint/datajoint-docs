"""Generate API documentation pages from datajoint-python source."""

from pathlib import Path

import mkdocs_gen_files

# Path to datajoint-python source (relative to docs root or absolute)
# This assumes datajoint is installed or PYTHONPATH includes the source
PACKAGE_NAME = "datajoint"

# Modules to document (public API)
PUBLIC_MODULES = [
    "datajoint",
    "datajoint.connection",
    "datajoint.schemas",
    "datajoint.table",
    "datajoint.user_tables",
    "datajoint.expression",
    "datajoint.heading",
    "datajoint.diagram",
    "datajoint.settings",
    "datajoint.errors",
    "datajoint.codecs",
    "datajoint.blob",
    "datajoint.hash",
    "datajoint.jobs",
    "datajoint.admin",
    "datajoint.migrate",
]

# Module display names and descriptions
MODULE_INFO = {
    "datajoint": ("Package", "Main datajoint package exports"),
    "datajoint.connection": ("Connection", "Database connection management"),
    "datajoint.schemas": ("Schema", "Schema and VirtualModule classes"),
    "datajoint.table": ("Table", "Base Table and FreeTable classes"),
    "datajoint.user_tables": ("Table Types", "Manual, Lookup, Imported, Computed, Part"),
    "datajoint.expression": ("Expressions", "Query expressions and operators"),
    "datajoint.heading": ("Heading", "Table heading and attributes"),
    "datajoint.diagram": ("Diagram", "Schema visualization"),
    "datajoint.settings": ("Settings", "Configuration management"),
    "datajoint.errors": ("Errors", "Exception classes"),
    "datajoint.codecs": ("Codecs", "Type codec system"),
    "datajoint.blob": ("Blob", "Binary serialization"),
    "datajoint.hash": ("Hash", "Hashing utilities"),
    "datajoint.jobs": ("Jobs", "Job queue for AutoPopulate"),
    "datajoint.admin": ("Admin", "Administrative functions"),
    "datajoint.migrate": ("Migrate", "Schema migration utilities"),
}

nav = mkdocs_gen_files.Nav()

# Generate index page
with mkdocs_gen_files.open("api/index.md", "w") as f:
    f.write("# API Reference\n\n")
    f.write("Auto-generated documentation from DataJoint source code.\n\n")
    f.write("## Modules\n\n")
    f.write("| Module | Description |\n")
    f.write("|--------|-------------|\n")
    for module in PUBLIC_MODULES:
        if module in MODULE_INFO:
            name, desc = MODULE_INFO[module]
            module_path = module.replace(".", "/")
            f.write(f"| [{name}]({module_path}.md) | {desc} |\n")

nav[("index.md",)] = "index.md"

# Generate page for each module
for module in PUBLIC_MODULES:
    module_path = module.replace(".", "/")
    doc_path = f"api/{module_path}.md"

    with mkdocs_gen_files.open(doc_path, "w") as f:
        if module in MODULE_INFO:
            name, desc = MODULE_INFO[module]
            f.write(f"# {name}\n\n")
            f.write(f"{desc}\n\n")
        else:
            f.write(f"# {module}\n\n")

        f.write(f"::: {module}\n")
        f.write("    options:\n")
        f.write("      show_source: false\n")
        f.write("      show_root_heading: false\n")
        f.write("      members_order: source\n")

    # Add to navigation
    parts = tuple(module_path.split("/"))
    nav[parts] = f"{module_path}.md"

# Write navigation file
with mkdocs_gen_files.open("api/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
