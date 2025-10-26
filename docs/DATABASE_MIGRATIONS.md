# Database Migrations Guide for Developers

This guide explains how to work with database migrations in SoundHash.

## Overview

SoundHash uses [Alembic](https://alembic.sqlalchemy.org/) for database schema management. All schema changes must be versioned through migrations.

## Quick Start

### When You Clone the Repository

```bash
# Apply all migrations to set up the database
alembic upgrade head
```

### When You Pull Changes

```bash
# Always run migrations after pulling
alembic upgrade head
```

### When You Modify Database Models

If you change anything in `src/database/models.py`, you **must** create a migration:

```bash
# 1. Make your changes to src/database/models.py

# 2. Generate a migration
alembic revision --autogenerate -m "Add field to Video model"

# 3. Review the generated file in alembic/versions/
#    Make sure it looks correct!

# 4. Test the migration
alembic upgrade head

# 5. Commit both the model changes AND the migration file
git add src/database/models.py alembic/versions/*.py
git commit -m "Add new field to Video model"
```

## Common Scenarios

### Adding a New Column

```python
# In src/database/models.py
class Video(Base):
    # ... existing fields ...
    new_field = Column(String(100))  # Add this
```

Then:
```bash
alembic revision --autogenerate -m "Add new_field to Video"
alembic upgrade head
```

### Adding a New Table

```python
# In src/database/models.py
class NewTable(Base):
    __tablename__ = 'new_table'
    id = Column(Integer, primary_key=True)
    # ... other fields ...
```

Then:
```bash
alembic revision --autogenerate -m "Add NewTable"
alembic upgrade head
```

### Adding an Index

```python
# In src/database/models.py
Index('idx_custom_index', Video.some_field)
```

Then:
```bash
alembic revision --autogenerate -m "Add index on Video.some_field"
alembic upgrade head
```

## Useful Commands

### Check Status

```bash
# Show current migration version
alembic current

# Show migration history
alembic history --verbose

# Check if migrations are up to date
python scripts/check_migrations.py
```

### Testing Migrations

```bash
# Apply a migration
alembic upgrade head

# Test rollback
alembic downgrade -1

# Reapply
alembic upgrade head
```

### Manual Migrations

Sometimes auto-generation doesn't capture everything. Create an empty migration:

```bash
alembic revision -m "Custom data migration"
```

Then edit the generated file to add custom SQL or Python code.

## CI/CD Integration

### Pre-Commit Check

Before pushing your changes, verify migrations are in sync:

```bash
python scripts/check_migrations.py
```

This check runs automatically in CI. If it fails, you need to create a migration.

### PR Checklist

When submitting a PR that changes models:

- [ ] Created a migration with `alembic revision --autogenerate`
- [ ] Reviewed the generated migration file
- [ ] Tested upgrade and downgrade
- [ ] Ran `python scripts/check_migrations.py` successfully
- [ ] Committed both model changes and migration file

## Best Practices

1. **Always review auto-generated migrations** - They're not perfect
2. **Test migrations before committing** - Run upgrade and downgrade
3. **Keep migrations focused** - One logical change per migration
4. **Use descriptive messages** - Future developers will thank you
5. **Never modify deployed migrations** - Create new ones instead
6. **Include downgrade logic** - Make rollbacks possible

## Troubleshooting

### "Target database is not up to date"

```bash
alembic upgrade head
```

### "Can't locate revision"

The migration file might be missing. Check:
```bash
ls alembic/versions/
```

### "Migrations are out of sync with models" (CI failure)

You changed models without creating a migration:
```bash
alembic revision --autogenerate -m "Sync models"
```

### Multiple migration heads

This happens when migrations branch. Merge them:
```bash
alembic merge -m "Merge migrations" <rev1> <rev2>
```

### Need to rollback

```bash
# Go back one migration
alembic downgrade -1

# Go to specific version
alembic downgrade <revision>

# Nuclear option - rollback everything (DANGEROUS!)
alembic downgrade base
```

## Example Workflow

Let's say you want to add a `tags` field to the Video model:

```bash
# 1. Edit the model
vim src/database/models.py
# Add: tags = Column(String(500))

# 2. Generate migration
alembic revision --autogenerate -m "Add tags field to Video"

# 3. Review the generated file
cat alembic/versions/*_add_tags_field_to_video.py

# 4. Apply migration
alembic upgrade head

# 5. Test it
python -c "from src.database.models import Video; print(Video.tags)"

# 6. Test rollback
alembic downgrade -1
alembic upgrade head

# 7. Verify CI check passes
python scripts/check_migrations.py

# 8. Commit changes
git add src/database/models.py alembic/versions/*_add_tags_field_to_video.py
git commit -m "Add tags field to Video model"
git push
```

## Migration Validation

### Robust Validation Using AST Parsing

SoundHash provides a robust migration validator that parses Python AST instead of using naive string searching. This avoids false positives from comments or unrelated context.

**Using the MigrationValidator:**

```python
from pathlib import Path
from src.database.migration_validator import MigrationValidator

# Load a migration file
migration_file = Path("alembic/versions/abc123_my_migration.py")
validator = MigrationValidator(migration_file)

# Check for specific operations
if validator.has_operation("create_index", function="upgrade"):
    print("Migration creates an index")

# Get all create_index operations
indexes = validator.get_operations("create_index", function="upgrade")
for idx in indexes:
    print(f"Creates index: {idx['args']}")

# Check if migration modifies a specific table
if validator.has_table_modification("audio_fingerprints"):
    print("Migration modifies audio_fingerprints table")

# Get all tables modified by this migration
tables = validator.get_modified_tables()
print(f"Modified tables: {tables}")

# Validate specific index creation
if validator.validates_index_creation(index_name="idx_my_index"):
    print("Migration creates idx_my_index")
```

**Why AST Parsing Instead of String Search:**

❌ **Naive approach (produces false positives):**
```python
# Bad: Matches comments and strings
migration_content = Path("migration.py").read_text()
if "create_index" in migration_content:  # Matches comments!
    print("Has index")
```

✅ **Robust approach (parses actual code):**
```python
# Good: Only matches actual operations
validator = MigrationValidator("migration.py")
if validator.has_operation("create_index"):
    print("Has index")
```

**Example: Validating a Migration Has Required Operations**

```python
from pathlib import Path
from src.database.migration_validator import MigrationValidator

def validate_composite_index_migration():
    """Validate that composite index migration has all required indexes."""
    migration = Path("alembic/versions/b9532a7d8c7a_add_composite_indexes_for_performance.py")
    validator = MigrationValidator(migration)
    
    required_indexes = [
        "idx_fingerprints_video_time",
        "idx_fingerprints_hash_video",
        "idx_match_results_query_fp",
        "idx_match_results_matched_fp",
        "idx_processing_jobs_type_status",
        "idx_processing_jobs_target",
    ]
    
    for index_name in required_indexes:
        assert validator.validates_index_creation(index_name=index_name), \
            f"Migration should create {index_name}"
    
    print("✓ All required indexes present in migration")

validate_composite_index_migration()
```

### Testing Migration Validators

See `tests/database/test_migration_validator.py` for comprehensive examples of using the validator in tests.

## More Information

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Auto-generate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Project INSTALL.md](INSTALL.md) - Installation and setup
- [alembic/README](alembic/README) - Detailed migration reference
- [MigrationValidator API](../src/database/migration_validator.py) - Robust migration validation utilities
