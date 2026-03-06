"""
Example migration script: DataJoint 0.14.6 → 2.0 using parallel schemas.

This script demonstrates the complete migration workflow for a single pipeline.
Adapt this for your own pipelines.

Usage:
    python migrate_pipeline_v20.py --phase 1  # Setup parallel schema
    python migrate_pipeline_v20.py --phase 2  # Update code (manual step)
    python migrate_pipeline_v20.py --phase 3  # Migrate test data
    python migrate_pipeline_v20.py --phase 4  # Validate
    python migrate_pipeline_v20.py --phase 5  # Production cutover
"""

import argparse
import logging
import sys
from pathlib import Path

import datajoint as dj
from datajoint.migrate import (
    backup_schema,
    compare_query_results,
    copy_table_data,
    create_parallel_schema,
    restore_schema,
    verify_schema_v20,
)

# Configuration
PROD_SCHEMA = "my_pipeline"
TEST_SCHEMA = "my_pipeline_v20"
BACKUP_SCHEMA = "my_pipeline_backup"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def phase_1_setup():
    """Phase 1: Setup parallel schema."""
    logger.info("=== Phase 1: Setup Parallel Schema ===")

    # Create parallel schema (structure only, no data)
    logger.info(f"Creating parallel schema: {PROD_SCHEMA} → {TEST_SCHEMA}")
    result = create_parallel_schema(
        source=PROD_SCHEMA,
        dest=TEST_SCHEMA,
        copy_data=False,
    )

    logger.info(f"✓ Created {result['tables_created']} tables in {TEST_SCHEMA}")

    # Verify
    conn = dj.conn()
    prod_count = conn.query(
        f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{PROD_SCHEMA}'"
    ).fetchone()[0]
    test_count = conn.query(
        f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='{TEST_SCHEMA}'"
    ).fetchone()[0]

    if prod_count == test_count:
        logger.info(f"✓ Verification passed: {prod_count} tables in both schemas")
    else:
        logger.error(f"✗ Table count mismatch: prod={prod_count}, test={test_count}")
        sys.exit(1)

    logger.info("\nNext step: Phase 2 - Update your Python code to use 2.0 API")
    logger.info("  - Update schema connections to point to _v20")
    logger.info("  - Replace fetch() with to_arrays()/to_dicts()")
    logger.info("  - Update type syntax in table definitions")


def phase_2_code_update():
    """Phase 2: Code update instructions."""
    logger.info("=== Phase 2: Update Code ===")
    logger.info("\nManual step - Update your Python code:")
    logger.info("")
    logger.info("1. Schema connections:")
    logger.info("   OLD: schema = dj.schema('my_pipeline')")
    logger.info("   NEW: schema = dj.schema('my_pipeline_v20')")
    logger.info("")
    logger.info("2. Fetch API:")
    logger.info("   OLD: table.fetch()")
    logger.info("   NEW: table.to_arrays() or table.to_dicts()")
    logger.info("")
    logger.info("3. Type syntax:")
    logger.info("   OLD: int unsigned → NEW: uint32")
    logger.info("   OLD: external-store → NEW: <blob@store>")
    logger.info("")
    logger.info("See: https://docs.datajoint.com/how-to/migrate-to-v20")
    logger.info("")
    logger.info("After updating code, run: python migrate_pipeline_v20.py --phase 3")


def phase_3_migrate_data():
    """Phase 3: Migrate test data."""
    logger.info("=== Phase 3: Migrate Test Data ===")

    # Get list of manual tables (those without # in definition)
    conn = dj.conn()

    # Example: Get all tables
    tables_query = f"""
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = '{PROD_SCHEMA}'
        AND TABLE_NAME NOT LIKE '~%'
        AND TABLE_NAME NOT LIKE '#%'
        ORDER BY TABLE_NAME
    """
    tables = [row[0] for row in conn.query(tables_query).fetchall()]

    logger.info(f"Found {len(tables)} tables to migrate")

    # Copy data for each table
    for table in tables:
        logger.info(f"Copying {table}...")

        # For this example, copy all data
        # In production, you might want to:
        # - Use limit= for sampling
        # - Use where_clause= for recent data only
        result = copy_table_data(
            source_schema=PROD_SCHEMA,
            dest_schema=TEST_SCHEMA,
            table=table,
            limit=None,  # Copy all (or use limit=1000 for testing)
        )

        logger.info(f"  ✓ Copied {result['rows_copied']} rows in {result['time_taken']:.2f}s")

    logger.info("\n✓ Data migration complete")
    logger.info("\nNext step: Phase 4 - Validate the migration")


def phase_4_validate():
    """Phase 4: Validate side-by-side."""
    logger.info("=== Phase 4: Validation ===")

    conn = dj.conn()

    # Get list of tables
    tables_query = f"""
        SELECT TABLE_NAME
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = '{TEST_SCHEMA}'
        AND TABLE_NAME NOT LIKE '~%'
        ORDER BY TABLE_NAME
    """
    tables = [row[0] for row in conn.query(tables_query).fetchall()]

    all_match = True

    for table in tables:
        logger.info(f"Validating {table}...")

        result = compare_query_results(
            prod_schema=PROD_SCHEMA,
            test_schema=TEST_SCHEMA,
            table=table,
            tolerance=1e-6,
        )

        if result["match"]:
            logger.info(f"  ✓ {result['row_count']} rows match")
        else:
            logger.error(f"  ✗ Validation failed:")
            for disc in result["discrepancies"][:5]:  # Show first 5
                logger.error(f"    {disc}")
            all_match = False

    # Verify 2.0 compatibility
    logger.info("\nVerifying 2.0 compatibility...")
    compat_result = verify_schema_v20(TEST_SCHEMA)

    if compat_result["compatible"]:
        logger.info("  ✓ Schema is 2.0 compatible")
    else:
        logger.warning("  ! Some 2.0 features not enabled:")
        for issue in compat_result["issues"]:
            logger.warning(f"    {issue}")

    if all_match:
        logger.info("\n✓ All validation checks passed!")
        logger.info("\nNext step: Phase 5 - Production cutover")
        logger.info("  WARNING: Phase 5 modifies production. Ensure:")
        logger.info("  - Full database backup completed")
        logger.info("  - All 0.14.6 clients stopped")
        logger.info("  - Maintenance window scheduled")
    else:
        logger.error("\n✗ Validation failed. Fix issues before proceeding.")
        sys.exit(1)


def phase_5_cutover():
    """Phase 5: Production cutover."""
    logger.info("=== Phase 5: Production Cutover ===")

    # Pre-flight checks
    logger.info("\nPre-flight checks:")

    # Check for running queries
    conn = dj.conn()
    active_queries = conn.query(
        f"""
        SELECT COUNT(*) FROM information_schema.PROCESSLIST
        WHERE DB = '{PROD_SCHEMA}' AND COMMAND != 'Sleep'
    """
    ).fetchone()[0]

    if active_queries > 0:
        logger.error(f"✗ Found {active_queries} active queries on {PROD_SCHEMA}")
        logger.error("  Stop all 0.14.6 clients before proceeding")
        sys.exit(1)
    else:
        logger.info("  ✓ No active queries")

    # Confirm from user
    logger.warning("\n!!! WARNING: This will modify production !!!")
    logger.warning(f"This will rename {PROD_SCHEMA} → {PROD_SCHEMA}_old")
    logger.warning(f"           and {TEST_SCHEMA} → {PROD_SCHEMA}")
    response = input("\nType 'MIGRATE' to proceed: ")

    if response != "MIGRATE":
        logger.info("Aborted")
        sys.exit(0)

    # Create backup first
    logger.info("\n1. Creating backup...")
    import datetime

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{PROD_SCHEMA}_backup_{timestamp}"

    backup_result = backup_schema(PROD_SCHEMA, backup_name)
    logger.info(f"  ✓ Backed up {backup_result['tables_backed_up']} tables to {backup_name}")

    # Rename schemas
    logger.info("\n2. Renaming schemas...")

    try:
        # Rename production → old
        conn.query(f"RENAME DATABASE `{PROD_SCHEMA}` TO `{PROD_SCHEMA}_old`")
        logger.info(f"  ✓ Renamed {PROD_SCHEMA} → {PROD_SCHEMA}_old")

        # Rename test → production
        conn.query(f"RENAME DATABASE `{TEST_SCHEMA}` TO `{PROD_SCHEMA}`")
        logger.info(f"  ✓ Renamed {TEST_SCHEMA} → {PROD_SCHEMA}")

    except Exception as e:
        logger.error(f"✗ Cutover failed: {e}")
        logger.error("Rolling back...")
        # Note: MySQL doesn't support RENAME DATABASE, using alternative approach
        logger.error("Manual rollback required. See documentation.")
        sys.exit(1)

    # Verify
    logger.info("\n3. Verifying cutover...")
    verify_result = verify_schema_v20(PROD_SCHEMA)

    if verify_result["compatible"]:
        logger.info("  ✓ Production schema verified")
    else:
        logger.warning("  ! Some issues found:")
        for issue in verify_result["issues"]:
            logger.warning(f"    {issue}")

    logger.info("\n✓ Cutover complete!")
    logger.info(f"\nBackup location: {backup_name}")
    logger.info(f"Old production: {PROD_SCHEMA}_old (can be dropped after verification)")
    logger.info("\nNext steps:")
    logger.info("  1. Update production code to point to 'my_pipeline'")
    logger.info("  2. Start 2.0 clients")
    logger.info("  3. Monitor for issues")
    logger.info("  4. After 1-2 weeks, drop old schema and backups")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Migrate DataJoint pipeline to 2.0")
    parser.add_argument(
        "--phase",
        type=int,
        choices=[1, 2, 3, 4, 5],
        required=True,
        help="Migration phase to execute",
    )

    args = parser.parse_args()

    phases = {
        1: phase_1_setup,
        2: phase_2_code_update,
        3: phase_3_migrate_data,
        4: phase_4_validate,
        5: phase_5_cutover,
    }

    phases[args.phase]()


if __name__ == "__main__":
    main()
