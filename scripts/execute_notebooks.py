#!/usr/bin/env python3
"""
Execute all Jupyter notebooks against a specified database backend.

Usage:
    python execute_notebooks.py --backend mysql
    python execute_notebooks.py --backend postgresql

This script:
1. Configures DataJoint for the specified backend
2. Finds all .ipynb files in src/tutorials and src/how-to
3. Executes each notebook in-place, saving output
4. Reports success/failure for each notebook
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def setup_backend(backend: str) -> dict:
    """
    Configure environment variables for the specified backend.

    Parameters
    ----------
    backend : str
        Either 'mysql' or 'postgresql'

    Returns
    -------
    dict
        Environment variables to set
    """
    env = os.environ.copy()

    if backend == "postgresql":
        env["DJ_BACKEND"] = "postgresql"
        env["DJ_HOST"] = env.get("DJ_HOST", "127.0.0.1")
        env["DJ_USER"] = "postgres"
        env["DJ_PASS"] = "tutorial"
        env["DJ_PORT"] = "5432"
        env["DJ_USE_TLS"] = "false"  # Tutorial containers don't use SSL
    else:  # mysql (default)
        env["DJ_BACKEND"] = "mysql"
        env["DJ_HOST"] = env.get("DJ_HOST", "127.0.0.1")
        env["DJ_USER"] = "root"
        env["DJ_PASS"] = "tutorial"
        env["DJ_PORT"] = "3306"
        env["DJ_USE_TLS"] = "false"  # Tutorial containers don't use SSL

    return env


def find_notebooks(base_path: Path) -> list[Path]:
    """
    Find all Jupyter notebooks in the tutorials and how-to directories.

    Parameters
    ----------
    base_path : Path
        Base path to search from (typically /main or project root)

    Returns
    -------
    list[Path]
        List of notebook paths
    """
    notebooks = []

    # Search directories
    search_dirs = [
        base_path / "src" / "tutorials",
        base_path / "src" / "how-to",
    ]

    for search_dir in search_dirs:
        if search_dir.exists():
            notebooks.extend(search_dir.rglob("*.ipynb"))

    # Filter out checkpoint files
    notebooks = [nb for nb in notebooks if ".ipynb_checkpoints" not in str(nb)]

    # Sort for consistent ordering
    notebooks.sort()

    return notebooks


def execute_notebook(notebook_path: Path, env: dict, timeout: int = 600) -> tuple[bool, str]:
    """
    Execute a single notebook using nbconvert.

    Parameters
    ----------
    notebook_path : Path
        Path to the notebook
    env : dict
        Environment variables
    timeout : int
        Timeout in seconds for notebook execution

    Returns
    -------
    tuple[bool, str]
        (success, error_message)
    """
    cmd = [
        "jupyter", "nbconvert",
        "--to", "notebook",
        "--execute",
        "--inplace",
        "--ExecutePreprocessor.timeout", str(timeout),
        str(notebook_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout + 60  # Extra buffer for nbconvert overhead
        )

        if result.returncode == 0:
            return True, ""
        else:
            return False, result.stderr

    except subprocess.TimeoutExpired:
        return False, f"Timeout after {timeout} seconds"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(
        description="Execute notebooks against a database backend"
    )
    parser.add_argument(
        "--backend",
        choices=["mysql", "postgresql"],
        default="mysql",
        help="Database backend to use (default: mysql)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Timeout per notebook in seconds (default: 600)"
    )
    parser.add_argument(
        "--base-path",
        type=Path,
        default=Path("/main"),
        help="Base path to search for notebooks (default: /main)"
    )

    args = parser.parse_args()

    print(f"=" * 60)
    print(f"Executing notebooks against {args.backend.upper()}")
    print(f"=" * 60)

    # Setup environment
    env = setup_backend(args.backend)
    print(f"\nBackend configuration:")
    print(f"  DJ_BACKEND: {env.get('DJ_BACKEND')}")
    print(f"  DJ_HOST: {env.get('DJ_HOST')}")
    print(f"  DJ_PORT: {env.get('DJ_PORT')}")
    print(f"  DJ_USER: {env.get('DJ_USER')}")

    # Find notebooks
    notebooks = find_notebooks(args.base_path)
    print(f"\nFound {len(notebooks)} notebooks to execute\n")

    if not notebooks:
        print("No notebooks found!")
        sys.exit(1)

    # Execute each notebook
    results = {"success": [], "failed": []}

    for i, notebook in enumerate(notebooks, 1):
        rel_path = notebook.relative_to(args.base_path)
        print(f"[{i}/{len(notebooks)}] {rel_path}...", end=" ", flush=True)

        success, error = execute_notebook(notebook, env, args.timeout)

        if success:
            print("OK")
            results["success"].append(rel_path)
        else:
            print("FAILED")
            results["failed"].append((rel_path, error))

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY ({args.backend.upper()})")
    print(f"{'=' * 60}")
    print(f"  Successful: {len(results['success'])}")
    print(f"  Failed: {len(results['failed'])}")

    if results["failed"]:
        print(f"\nFailed notebooks:")
        for path, error in results["failed"]:
            print(f"  - {path}")
            if error:
                # Print first few lines of error
                error_lines = error.strip().split("\n")[-5:]
                for line in error_lines:
                    print(f"      {line}")
        sys.exit(1)

    print(f"\nAll notebooks executed successfully against {args.backend.upper()}!")


if __name__ == "__main__":
    main()
