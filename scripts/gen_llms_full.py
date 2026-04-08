#!/usr/bin/env python3
"""
Generate llms.txt and llms-full.txt from documentation sources.

- llms.txt: Index with links derived from mkdocs.yaml nav
- llms-full.txt: Complete documentation concatenated for LLM consumption

Both files are auto-generated during the build process.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import yaml

# Documentation root
PROJECT_DIR = Path(__file__).parent.parent
DOCS_DIR = PROJECT_DIR / "src"
MKDOCS_FILE = PROJECT_DIR / "mkdocs.yaml"
OUTPUT_FILE = DOCS_DIR / "llms-full.txt"
OUTPUT_INDEX = DOCS_DIR / "llms.txt"

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


def source_path_to_url(path: str) -> str:
    """Convert a source file path to a deployed MkDocs URL.

    MkDocs with use_directory_urls=true (default) serves:
      about/whats-new-2.md  ->  /about/whats-new-2/
      tutorials/basics/01-first-pipeline.ipynb  ->  /tutorials/basics/01-first-pipeline/
      index.md  ->  /
      section/index.md  ->  /section/
    """
    # Strip file extension
    url = re.sub(r"\.(md|ipynb)$", "", path)
    # index pages -> parent directory
    url = re.sub(r"/index$", "", url)
    if url == "index":
        return "/"
    # Avoid double slash for paths like "api/"
    if url.endswith("/"):
        return f"/{url}"
    return f"/{url}/"


def extract_nav_entries(nav, section_path=""):
    """Recursively extract (title, url) pairs from mkdocs nav structure."""
    entries = []
    if isinstance(nav, list):
        for item in nav:
            entries.extend(extract_nav_entries(item, section_path))
    elif isinstance(nav, dict):
        for key, value in nav.items():
            if isinstance(value, str):
                # Leaf node: "Title: path.md" or external URL
                if value.startswith("http"):
                    continue  # skip external links
                url = source_path_to_url(value)
                entries.append((key, url))
            elif isinstance(value, list):
                # Section with children
                entries.extend(extract_nav_entries(value, key))
    elif isinstance(nav, str):
        # Bare path without title (e.g., index pages)
        if not nav.startswith("http"):
            url = source_path_to_url(nav)
            entries.append((None, url))
    return entries


def load_mkdocs_nav():
    """Load just the nav section from mkdocs.yaml.

    mkdocs.yaml contains !!python/name tags that standard YAML loaders
    can't resolve without the material theme installed. We add a custom
    constructor that ignores these tags.
    """
    loader = yaml.SafeLoader
    # Handle !!python/name and !!python/object tags by returning None
    loader.add_multi_constructor(
        "tag:yaml.org,2002:python/",
        lambda loader, suffix, node: None,
    )
    with open(MKDOCS_FILE, "r") as f:
        return yaml.load(f, Loader=loader)


def generate_llms_txt():
    """Generate llms.txt index from mkdocs.yaml nav."""
    mkdocs_config = load_mkdocs_nav()

    nav = mkdocs_config.get("nav", [])

    # Map top-level nav sections to llms.txt sections
    # Each top-level nav item is a dict like {"Concepts": [...]}
    lines = [
        "# DataJoint Documentation",
        "",
        "> DataJoint is a Python framework for building scientific data pipelines "
        "with automated computation, integrity constraints, and seamless integration "
        "of relational databases with object storage.",
        "",
        "> For the complete documentation in a single file, see [/llms-full.txt](/llms-full.txt)",
        "",
    ]

    for nav_item in nav:
        if isinstance(nav_item, dict):
            for section_name, section_content in nav_item.items():
                if isinstance(section_content, str):
                    # Skip "Home: index.md" but keep other top-level leaves
                    if section_content == "index.md" or section_content.startswith("http"):
                        continue
                    url = source_path_to_url(section_content)
                    lines.append(f"- [{section_name}]({url})")
                    lines.append("")
                elif isinstance(section_content, list):
                    lines.append(f"## {section_name}")
                    lines.append("")
                    entries = extract_nav_entries(section_content)
                    for title, url in entries:
                        if title:
                            lines.append(f"- [{title}]({url})")
                    lines.append("")

    content = "\n".join(lines) + "\n"
    with open(OUTPUT_INDEX, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated {OUTPUT_INDEX} ({len(content):,} bytes)")


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
    generate_llms_txt()
    generate_llms_full()
