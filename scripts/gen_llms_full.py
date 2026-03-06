#!/usr/bin/env python3
"""
Generate llms-full.txt from documentation sources.

This script concatenates all markdown documentation into a single file
optimized for LLM consumption.

The generated file is NOT committed to git - it's auto-generated during
the build process with current version metadata.
"""

import json
import subprocess
from datetime import datetime, timezone
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

Generated: {timestamp}
Commit: {commit}
Branch: {branch}

> DataJoint is a Python framework for building scientific data pipelines with automated computation, integrity constraints, and seamless integration of relational databases with object storage. This documentation covers DataJoint 2.0.

> This file contains the complete documentation for LLM consumption. For an index with links, see /llms.txt

---

"""


def get_git_info() -> dict[str, str]:
    """Get current git commit hash and branch name."""
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).parent.parent,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit = "unknown"

    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=Path(__file__).parent.parent,
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        branch = "unknown"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    return {
        "timestamp": timestamp,
        "commit": commit,
        "branch": branch,
    }


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
    # Get current git info for version metadata
    git_info = get_git_info()
    header = HEADER.format(**git_info)
    content_parts = [header]

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
