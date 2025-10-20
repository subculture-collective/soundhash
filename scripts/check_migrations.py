#!/usr/bin/env python3
"""
CI script to check that database migrations are up to date.

This script verifies that:
1. The current models match the latest migration state
2. No new model changes exist that haven't been migrated

Exit codes:
- 0: Migrations are up to date
- 1: Migrations are out of sync with models (need to create a new migration)
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect


def check_migrations() -> int:
    """Check if migrations are in sync with models."""
    print("Checking database migrations...")

    # Create two temporary databases
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp1:
        db_from_migrations = tmp1.name
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp2:
        db_from_models = tmp2.name

    try:
        # Save original DATABASE_URL
        old_db_url = os.environ.get("DATABASE_URL")
        project_root = Path(__file__).parent.parent

        # 1. Create database from migrations
        print("1. Applying migrations to test database...")
        os.environ["DATABASE_URL"] = f"sqlite:///{db_from_migrations}"
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("ERROR: Failed to apply migrations:")
            print(result.stderr)
            return 1

        print("   ✓ Migrations applied successfully")

        # 2. Create database from current models
        print("2. Creating database from current models...")
        from src.database.models import Base

        engine = create_engine(f"sqlite:///{db_from_models}")
        Base.metadata.create_all(engine)
        engine.dispose()
        print("   ✓ Models applied successfully")

        # 3. Compare schemas
        print("3. Comparing schemas...")
        engine1 = create_engine(f"sqlite:///{db_from_migrations}")
        engine2 = create_engine(f"sqlite:///{db_from_models}")

        inspector1 = inspect(engine1)
        inspector2 = inspect(engine2)

        # Get table names (excluding alembic_version)
        tables1 = set(inspector1.get_table_names()) - {"alembic_version"}
        tables2 = set(inspector2.get_table_names())

        if tables1 != tables2:
            print("   ✗ ERROR: Table mismatch detected!")
            print(f"     Tables in migrations: {sorted(tables1)}")
            print(f"     Tables in models: {sorted(tables2)}")
            print(f"     Missing in migrations: {sorted(tables2 - tables1)}")
            print(f"     Extra in migrations: {sorted(tables1 - tables2)}")
            return 1

        print(f"   ✓ Found {len(tables1)} tables in both")

        # Compare columns for each table
        schema_diff = False
        for table in sorted(tables1):
            cols1 = {
                col["name"]: col["type"].__class__.__name__ for col in inspector1.get_columns(table)
            }
            cols2 = {
                col["name"]: col["type"].__class__.__name__ for col in inspector2.get_columns(table)
            }

            if cols1.keys() != cols2.keys():
                print(f"   ✗ ERROR: Column mismatch in table '{table}'")
                print(f"     Columns in migrations: {sorted(cols1.keys())}")
                print(f"     Columns in models: {sorted(cols2.keys())}")
                print(f"     Missing in migrations: {sorted(cols2.keys() - cols1.keys())}")
                print(f"     Extra in migrations: {sorted(cols1.keys() - cols2.keys())}")
                schema_diff = True
                continue

            # Check column types
            for col_name in cols1.keys():
                if cols1[col_name] != cols2[col_name]:
                    print(f"   ✗ WARNING: Type difference in {table}.{col_name}")
                    print(f"     Migration: {cols1[col_name]}, Model: {cols2[col_name]}")
                    # Note: SQLite type mapping can be imprecise, so we warn but don't fail

        engine1.dispose()
        engine2.dispose()

        if schema_diff:
            print("\n❌ FAILED: Migrations are out of sync with models!")
            print("   Please run: alembic revision --autogenerate -m 'Your migration message'")
            return 1

        print("\n✅ SUCCESS: Migrations are up to date with models!")
        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    finally:
        # Restore original DATABASE_URL
        if old_db_url:
            os.environ["DATABASE_URL"] = old_db_url
        elif "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        # Clean up temporary files
        for path in [db_from_migrations, db_from_models]:
            if os.path.exists(path):
                os.unlink(path)


if __name__ == "__main__":
    sys.exit(check_migrations())
