"""Tests for migration validation using AST parsing."""

import tempfile
from pathlib import Path

from src.database.migration_validator import MigrationValidator


class TestMigrationValidator:
    """Test suite for migration file validation using AST parsing."""

    def test_parse_create_index_operations(self):
        """Test parsing of create_index operations from migration file."""
        # Create a temporary migration file
        migration_content = '''"""Test migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_index("idx_test", "test_table", ["column1"], unique=False)
    op.create_index("idx_test2", "test_table", ["column2", "column3"], unique=True)

def downgrade():
    op.drop_index("idx_test", table_name="test_table")
    op.drop_index("idx_test2", table_name="test_table")
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)
            validator.parse()

            # Check that create_index operations are detected
            assert validator.has_operation("create_index", function="upgrade")
            assert validator.has_operation("drop_index", function="downgrade")

            # Check number of operations
            create_ops = validator.get_operations("create_index", function="upgrade")
            assert len(create_ops) == 2

            # Check operation details
            assert create_ops[0]["args"][0] == "idx_test"
            assert create_ops[0]["args"][1] == "test_table"

            # Check that we don't get false positives
            assert not validator.has_operation("create_table")
            assert not validator.has_operation("add_column")

        finally:
            Path(migration_file).unlink()

    def test_parse_add_column_operations(self):
        """Test parsing of add_column operations."""
        migration_content = '''"""Add columns migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("users", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("age", sa.Integer(), nullable=False))

def downgrade():
    op.drop_column("users", "age")
    op.drop_column("users", "email")
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)

            # Check add_column operations
            assert validator.has_operation("add_column", function="upgrade")
            assert validator.has_operation("drop_column", function="downgrade")

            add_ops = validator.get_operations("add_column", function="upgrade")
            assert len(add_ops) == 2
            assert add_ops[0]["args"][0] == "users"
            assert add_ops[1]["args"][0] == "users"

            # Check table modifications
            assert validator.has_table_modification("users")
            assert not validator.has_table_modification("posts")

        finally:
            Path(migration_file).unlink()

    def test_parse_create_table_operations(self):
        """Test parsing of create_table operations."""
        migration_content = '''"""Create table migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        "new_table",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False)
    )

def downgrade():
    op.drop_table("new_table")
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)

            assert validator.has_operation("create_table", function="upgrade")
            assert validator.has_operation("drop_table", function="downgrade")

            create_ops = validator.get_operations("create_table", function="upgrade")
            assert len(create_ops) == 1
            assert create_ops[0]["args"][0] == "new_table"

        finally:
            Path(migration_file).unlink()

    def test_ignores_comments_with_operation_names(self):
        """Test that comments mentioning operations don't create false positives."""
        migration_content = '''"""Migration with comments"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # This comment mentions create_index but it's just a comment
    # We should not create_index here, just add_column
    op.add_column("users", sa.Column("field", sa.String(50)))

    # Another comment: op.create_table would be wrong here

def downgrade():
    # Drop the column we added, not create_index anything
    op.drop_column("users", "field")
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)

            # Should only find the actual operations, not the ones in comments
            assert validator.has_operation("add_column")
            assert validator.has_operation("drop_column")
            assert not validator.has_operation("create_index")
            assert not validator.has_operation("create_table")

        finally:
            Path(migration_file).unlink()

    def test_get_modified_tables(self):
        """Test getting all tables modified in a migration."""
        migration_content = '''"""Multi-table migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("users", sa.Column("field1", sa.String(50)))
    op.create_index("idx_posts", "posts", ["created_at"])
    op.add_column("comments", sa.Column("field2", sa.Integer()))

def downgrade():
    op.drop_column("comments", "field2")
    op.drop_index("idx_posts", table_name="posts")
    op.drop_column("users", "field1")
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)

            modified_tables = validator.get_modified_tables()
            assert "users" in modified_tables
            assert "posts" in modified_tables
            assert "comments" in modified_tables
            assert len(modified_tables) >= 3

        finally:
            Path(migration_file).unlink()

    def test_validates_index_creation(self):
        """Test validating index creation with specific names."""
        migration_content = '''"""Composite indexes migration"""
from alembic import op

def upgrade():
    op.create_index("idx_fingerprints_video_time", "audio_fingerprints", ["video_id", "start_time"], unique=False)
    op.create_index("idx_fingerprints_hash_video", "audio_fingerprints", ["fingerprint_hash", "video_id"], unique=False)

def downgrade():
    op.drop_index("idx_fingerprints_hash_video", table_name="audio_fingerprints")
    op.drop_index("idx_fingerprints_video_time", table_name="audio_fingerprints")
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)

            # Validate specific index names
            assert validator.validates_index_creation(index_name="idx_fingerprints_video_time")
            assert validator.validates_index_creation(index_name="idx_fingerprints_hash_video")
            assert not validator.validates_index_creation(index_name="idx_nonexistent")

            # Validate by table name
            assert validator.validates_index_creation(table_name="audio_fingerprints")
            assert not validator.validates_index_creation(table_name="other_table")

        finally:
            Path(migration_file).unlink()

    def test_real_migration_file(self):
        """Test with actual migration file from the project."""
        project_root = Path(__file__).parent.parent.parent
        migrations_dir = project_root / "alembic" / "versions"

        # Test the composite indexes migration
        composite_migration = (
            migrations_dir / "b9532a7d8c7a_add_composite_indexes_for_performance.py"
        )

        if composite_migration.exists():
            validator = MigrationValidator(composite_migration)

            # Should detect create_index operations
            assert validator.has_operation("create_index", function="upgrade")
            assert validator.has_operation("drop_index", function="downgrade")

            # Should detect modifications to specific tables
            assert validator.has_table_modification("audio_fingerprints")
            assert validator.has_table_modification("match_results")
            assert validator.has_table_modification("processing_jobs")

            # Should find specific indexes
            assert validator.validates_index_creation(index_name="idx_fingerprints_video_time")
            assert validator.validates_index_creation(index_name="idx_processing_jobs_type_status")

    def test_validates_column_addition_basic(self):
        """Test basic column addition validation."""
        migration_content = '''"""Add column migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column("audio_fingerprints", sa.Column("n_fft", sa.Integer(), nullable=True))
    op.add_column("audio_fingerprints", sa.Column("hop_length", sa.Integer(), nullable=True))

def downgrade():
    op.drop_column("audio_fingerprints", "hop_length")
    op.drop_column("audio_fingerprints", "n_fft")
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)

            # Validate that columns are being added to the table
            assert validator.validates_column_addition("audio_fingerprints", "n_fft")
            assert validator.validates_column_addition("audio_fingerprints", "hop_length")
            assert not validator.validates_column_addition("other_table", "n_fft")

        finally:
            Path(migration_file).unlink()

    def test_empty_migration(self):
        """Test handling of migration with no operations."""
        migration_content = '''"""Empty migration"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    pass

def downgrade():
    pass
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(migration_content)
            f.flush()
            migration_file = f.name

        try:
            validator = MigrationValidator(migration_file)

            assert len(validator.operations) == 0
            assert not validator.has_operation("create_index")
            assert len(validator.get_modified_tables()) == 0

        finally:
            Path(migration_file).unlink()
