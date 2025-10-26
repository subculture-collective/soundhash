#!/usr/bin/env python3
"""
Example script demonstrating robust migration validation using AST parsing.

This shows how to validate migration files properly without false positives
from comments or unrelated context.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.migration_validator import MigrationValidator


def validate_composite_indexes_migration():
    """
    Example: Validate that the composite indexes migration contains all expected indexes.

    This demonstrates the proper way to validate migrations using AST parsing
    instead of naive string searching.
    """
    print("=" * 80)
    print("Example: Validating Composite Indexes Migration")
    print("=" * 80)

    # Path to the migration file
    project_root = Path(__file__).parent.parent
    migration_file = (
        project_root
        / "alembic"
        / "versions"
        / "b9532a7d8c7a_add_composite_indexes_for_performance.py"
    )

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    # Create validator
    validator = MigrationValidator(migration_file)

    # Define expected indexes
    expected_indexes = {
        "idx_fingerprints_video_time": "audio_fingerprints",
        "idx_fingerprints_hash_video": "audio_fingerprints",
        "idx_match_results_query_fp": "match_results",
        "idx_match_results_matched_fp": "match_results",
        "idx_processing_jobs_type_status": "processing_jobs",
        "idx_processing_jobs_target": "processing_jobs",
    }

    print(f"\n✓ Loaded migration: {migration_file.name}")
    print(f"\n  Checking for {len(expected_indexes)} expected indexes...")

    # Validate each index
    all_valid = True
    for index_name, table_name in expected_indexes.items():
        if validator.validates_index_creation(index_name=index_name):
            print(f"  ✓ Found index: {index_name} on {table_name}")
        else:
            print(f"  ❌ Missing index: {index_name} on {table_name}")
            all_valid = False

    # Show all operations found
    print(f"\n  Found {len(validator.operations)} total operations in migration")

    # Get modified tables
    modified_tables = validator.get_modified_tables()
    print(f"  Modified tables: {', '.join(sorted(modified_tables))}")

    # Summary
    if all_valid:
        print("\n✅ SUCCESS: Migration validation passed!")
    else:
        print("\n❌ FAILED: Some expected indexes are missing!")

    return all_valid


def demonstrate_false_positive_protection():
    """
    Demonstrate how AST parsing avoids false positives from comments.

    This shows why AST parsing is superior to naive string searching.
    """
    print("\n" + "=" * 80)
    print("Example: Protection Against False Positives from Comments")
    print("=" * 80)

    # Create a test migration with operations mentioned in comments
    test_migration = '''"""Test migration with misleading comments"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # This comment mentions create_index but we won't actually create one
    # We also mention add_column here in the comment
    op.drop_column("users", "old_field")  # Only actual operation

def downgrade():
    # Downgrade should create_table users, right? No, just add the column back
    op.add_column("users", sa.Column("old_field", sa.String(50)))
'''

    # Write to temp file
    import tempfile

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(test_migration)
        f.flush()
        temp_file = Path(f.name)

    try:
        # Using naive string search (BAD - produces false positives)
        content = temp_file.read_text()
        print("\n❌ Naive string search results (WRONG - false positives):")
        print(f"   'create_index' in content: {'create_index' in content}")
        print(f"   'add_column' in content: {'add_column' in content}")
        print(f"   'create_table' in content: {'create_table' in content}")

        # Using AST parsing (GOOD - no false positives)
        validator = MigrationValidator(temp_file)
        print("\n✅ AST parsing results (CORRECT - no false positives):")
        print(f"   has_operation('create_index'): {validator.has_operation('create_index')}")
        print(f"   has_operation('add_column'): {validator.has_operation('add_column')}")
        print(f"   has_operation('create_table'): {validator.has_operation('create_table')}")
        print(f"   has_operation('drop_column'): {validator.has_operation('drop_column')}")

        print("\n  The AST parser correctly identifies only the actual operations,")
        print("  ignoring mentions in comments!")

    finally:
        temp_file.unlink()


if __name__ == "__main__":
    # Run examples
    result1 = validate_composite_indexes_migration()
    demonstrate_false_positive_protection()

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)

    if result1:
        print("\n💡 Use MigrationValidator in your validation scripts to avoid false positives!")
    print()
