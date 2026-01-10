#!/usr/bin/env python3
"""
Generate llms-full.txt from documentation sources.

This script concatenates all markdown documentation into a single file
optimized for LLM consumption.
"""

import json
from pathlib import Path

# Documentation root
DOCS_DIR = Path(__file__).parent.parent / "src"
OUTPUT_FILE = DOCS_DIR / "llms-full.txt"

# Sections in order of importance
SECTIONS = [
    ("Concepts", "explanation"),
    ("Tutorials", "tutorials"),
    ("How-To Guides", "how-to"),
    ("Reference", "reference"),
    ("About", "about"),
]

HEADER = """# DataJoint Documentation (Full)

> DataJoint is a Python framework for building scientific data pipelines with automated computation, integrity constraints, and seamless integration of relational databases with object storage. This documentation covers DataJoint 2.0.

> This file contains the complete documentation for LLM consumption. For an index with links, see /llms.txt

---

"""


def read_markdown_file(filepath: Path) -> str:
    """Read a markdown file and return its content."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return ""


def read_notebook_file(filepath: Path) -> str:
    """Read a Jupyter notebook and extract markdown and code cells."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            nb = json.load(f)

        content_parts = []
        for cell in nb.get("cells", []):
            cell_type = cell.get("cell_type", "")
            source = "".join(cell.get("source", []))

            if cell_type == "markdown":
                content_parts.append(source)
            elif cell_type == "code":
                content_parts.append(f"\n```python\n{source}\n```\n")

        return "\n\n".join(content_parts)
    except Exception as e:
        print(f"Warning: Could not read notebook {filepath}: {e}")
        return ""


def get_doc_files(directory: Path) -> list[Path]:
    """Get all documentation files in a directory, sorted."""
    if not directory.exists():
        return []
    md_files = list(directory.glob("**/*.md"))
    nb_files = list(directory.glob("**/*.ipynb"))
    files = md_files + nb_files
    # Sort by path to ensure consistent ordering
    return sorted(files)


def generate_llms_full():
    """Generate the llms-full.txt file."""
    content_parts = [HEADER]

    for section_name, section_dir in SECTIONS:
        section_path = DOCS_DIR / section_dir
        doc_files = get_doc_files(section_path)

        if not doc_files:
            continue

        content_parts.append(f"\n{'='*60}\n")
        content_parts.append(f"# {section_name}\n")
        content_parts.append(f"{'='*60}\n\n")

        for doc_file in doc_files:
            relative_path = doc_file.relative_to(DOCS_DIR)
            content_parts.append(f"\n---\n")
            content_parts.append(f"## File: {relative_path}\n\n")

            if doc_file.suffix == ".ipynb":
                content_parts.append(read_notebook_file(doc_file))
            else:
                content_parts.append(read_markdown_file(doc_file))
            content_parts.append("\n")

    # Write output
    full_content = "".join(content_parts)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(full_content)

    print(f"Generated {OUTPUT_FILE} ({len(full_content):,} bytes)")


if __name__ == "__main__":
    generate_llms_full()
