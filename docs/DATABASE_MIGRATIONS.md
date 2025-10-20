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

## More Information

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Alembic Auto-generate](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)
- [Project INSTALL.md](INSTALL.md) - Installation and setup
- [alembic/README](alembic/README) - Detailed migration reference
