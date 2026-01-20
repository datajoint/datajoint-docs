#!/usr/bin/env python3
"""
Drop all tutorial schemas from the database.

Usage:
    python drop_tutorial_schemas.py --backend mysql
    python drop_tutorial_schemas.py --backend postgresql

This script drops all schemas matching the 'tutorial_%' pattern,
preparing for a fresh notebook execution run.
"""

import argparse
import os
import sys


def get_connection(backend: str):
    """
    Create a database connection for the specified backend.

    Parameters
    ----------
    backend : str
        Either 'mysql' or 'postgresql'

    Returns
    -------
    connection
        Database connection object
    """
    if backend == "postgresql":
        import psycopg2

        return psycopg2.connect(
            host=os.environ.get("DJ_HOST", "127.0.0.1"),
            port=int(os.environ.get("DJ_PORT", "5432")),
            user=os.environ.get("DJ_USER", "postgres"),
            password=os.environ.get("DJ_PASS", "tutorial"),
            dbname="postgres",
        )
    else:  # mysql
        import pymysql

        return pymysql.connect(
            host=os.environ.get("DJ_HOST", "127.0.0.1"),
            port=int(os.environ.get("DJ_PORT", "3306")),
            user=os.environ.get("DJ_USER", "root"),
            password=os.environ.get("DJ_PASS", "tutorial"),
        )


def drop_tutorial_schemas(backend: str, dry_run: bool = False) -> list[str]:
    """
    Drop all tutorial schemas from the database.

    Parameters
    ----------
    backend : str
        Either 'mysql' or 'postgresql'
    dry_run : bool
        If True, only list schemas without dropping

    Returns
    -------
    list[str]
        List of dropped schema names
    """
    conn = get_connection(backend)
    cursor = conn.cursor()

    # Find tutorial schemas
    if backend == "postgresql":
        cursor.execute(
            """
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name LIKE 'tutorial_%'
            ORDER BY schema_name
            """
        )
    else:  # mysql
        cursor.execute(
            """
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name LIKE 'tutorial_%'
            ORDER BY schema_name
            """
        )

    schemas = [row[0] for row in cursor.fetchall()]

    if not schemas:
        print("No tutorial schemas found.")
        return []

    print(f"Found {len(schemas)} tutorial schema(s):")
    for schema in schemas:
        print(f"  - {schema}")

    if dry_run:
        print("\nDry run - no schemas dropped.")
        return schemas

    print("\nDropping schemas...")

    for schema in schemas:
        if backend == "postgresql":
            # PostgreSQL uses double quotes for identifiers
            cursor.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        else:  # mysql
            # MySQL uses backticks for identifiers
            cursor.execute(f"DROP DATABASE IF EXISTS `{schema}`")
        print(f"  Dropped: {schema}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\nDropped {len(schemas)} schema(s).")
    return schemas


def main():
    parser = argparse.ArgumentParser(
        description="Drop all tutorial schemas from the database"
    )
    parser.add_argument(
        "--backend",
        choices=["mysql", "postgresql"],
        default="mysql",
        help="Database backend (default: mysql)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List schemas without dropping them",
    )

    args = parser.parse_args()

    print(f"{'=' * 60}")
    print(f"Drop Tutorial Schemas ({args.backend.upper()})")
    print(f"{'=' * 60}\n")

    try:
        drop_tutorial_schemas(args.backend, args.dry_run)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
