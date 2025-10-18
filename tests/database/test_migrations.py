"""Tests for Alembic database migrations."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config as AlembicConfig
from sqlalchemy import create_engine, inspect, text


class TestMigrations:
    """Test suite for database migrations."""

    def test_migrations_apply_cleanly(self):
        """Test that migrations apply cleanly on a fresh database."""
        # Create a temporary SQLite database for testing
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Set up environment variable for the test database
            old_db_url = os.environ.get("DATABASE_URL")
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent

            # Run alembic upgrade head
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )

            # Check that migration succeeded
            assert result.returncode == 0, f"Migration failed: {result.stderr}"

            # Verify all expected tables were created
            engine = create_engine(f"sqlite:///{db_path}")
            inspector = inspect(engine)
            table_names = inspector.get_table_names()

            expected_tables = [
                "channels",
                "videos",
                "audio_fingerprints",
                "match_results",
                "processing_jobs",
                "alembic_version",
            ]

            for table in expected_tables:
                assert table in table_names, f"Table {table} not found in database"

            # Verify alembic_version table has a record
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.fetchone()
                assert version is not None, "No version found in alembic_version table"
                assert len(version[0]) > 0, "Version number is empty"

            engine.dispose()

        finally:
            # Clean up
            if old_db_url:
                os.environ["DATABASE_URL"] = old_db_url
            elif "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_migration_downgrade(self):
        """Test that migrations can be downgraded."""
        # Create a temporary SQLite database for testing
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Set up environment variable for the test database
            old_db_url = os.environ.get("DATABASE_URL")
            os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent

            # Run alembic upgrade head
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Upgrade failed: {result.stderr}"

            # Run alembic downgrade base
            result = subprocess.run(
                ["alembic", "downgrade", "base"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Downgrade failed: {result.stderr}"

            # Verify all tables were dropped except alembic_version
            engine = create_engine(f"sqlite:///{db_path}")
            inspector = inspect(engine)
            table_names = inspector.get_table_names()

            # Only alembic_version should remain
            assert "channels" not in table_names
            assert "videos" not in table_names
            assert "audio_fingerprints" not in table_names

            engine.dispose()

        finally:
            # Clean up
            if old_db_url:
                os.environ["DATABASE_URL"] = old_db_url
            elif "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_alembic_config_loads(self):
        """Test that Alembic configuration loads without errors."""
        project_root = Path(__file__).parent.parent.parent
        alembic_ini = project_root / "alembic.ini"

        assert alembic_ini.exists(), "alembic.ini not found"

        # Try to load the config
        config = AlembicConfig(str(alembic_ini))
        script_location = config.get_main_option("script_location")

        assert script_location is not None
        assert "alembic" in script_location

    def test_current_models_match_migrations(self):
        """Test that current models match the latest migration state."""
        # This test ensures that if someone changes models without creating a migration,
        # we catch it. It creates two databases: one from migrations and one from models,
        # then compares their schemas.

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp1:
            db_from_migrations = tmp1.name
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp2:
            db_from_models = tmp2.name

        try:
            old_db_url = os.environ.get("DATABASE_URL")
            project_root = Path(__file__).parent.parent.parent

            # Create database from migrations
            os.environ["DATABASE_URL"] = f"sqlite:///{db_from_migrations}"
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0, f"Migration failed: {result.stderr}"

            # Create database from models directly
            from src.database.models import Base

            engine = create_engine(f"sqlite:///{db_from_models}")
            Base.metadata.create_all(engine)
            engine.dispose()

            # Compare table structures
            engine1 = create_engine(f"sqlite:///{db_from_migrations}")
            engine2 = create_engine(f"sqlite:///{db_from_models}")

            inspector1 = inspect(engine1)
            inspector2 = inspect(engine2)

            tables1 = set(inspector1.get_table_names()) - {"alembic_version"}
            tables2 = set(inspector2.get_table_names())

            # Both should have the same tables (excluding alembic_version)
            assert tables1 == tables2, f"Table mismatch: {tables1} vs {tables2}"

            # For each table, compare columns
            for table in tables1:
                cols1 = {col["name"]: col["type"].__class__.__name__ for col in inspector1.get_columns(table)}
                cols2 = {col["name"]: col["type"].__class__.__name__ for col in inspector2.get_columns(table)}

                assert cols1.keys() == cols2.keys(), (
                    f"Column mismatch in table {table}: {cols1.keys()} vs {cols2.keys()}"
                )

            engine1.dispose()
            engine2.dispose()

        finally:
            # Clean up
            if old_db_url:
                os.environ["DATABASE_URL"] = old_db_url
            elif "DATABASE_URL" in os.environ:
                del os.environ["DATABASE_URL"]
            for path in [db_from_migrations, db_from_models]:
                if os.path.exists(path):
                    os.unlink(path)
