#!/usr/bin/env python3
"""
Data migration and export/import tools for SoundHash.

Handles database migrations, data export, and import operations.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.logging_config import setup_logging
from config.settings import Config


class MigrationError(Exception):
    """Custom exception for migration errors."""

    pass


class DataMigration:
    """Handles data export, import, and migration operations."""

    def __init__(self, output_dir: str = "./migrations"):
        """
        Initialize data migration handler.

        Args:
            output_dir: Directory for export files
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export_table(
        self,
        table_name: str,
        format: str = "csv",
        output_file: Path | None = None,
    ) -> Path:
        """
        Export a database table to file.

        Args:
            table_name: Name of the table to export
            format: Export format ('csv', 'json', 'sql')
            output_file: Output file path (default: auto-generated)

        Returns:
            Path to the exported file

        Raises:
            MigrationError: If export fails
        """
        if not output_file:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"{table_name}_{timestamp}.{format}"

        self.logger.info(f"Exporting table '{table_name}' to {output_file}")

        try:
            if format == "csv":
                self._export_csv(table_name, output_file)
            elif format == "json":
                self._export_json(table_name, output_file)
            elif format == "sql":
                self._export_sql(table_name, output_file)
            else:
                raise MigrationError(f"Unsupported export format: {format}")

            file_size = output_file.stat().st_size
            self.logger.info(
                f"Export complete: {output_file} ({file_size / 1024 / 1024:.2f} MB)"
            )

            return output_file

        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            if output_file and output_file.exists():
                output_file.unlink()
            raise MigrationError(f"Table export failed: {str(e)}") from e

    def _export_csv(self, table_name: str, output_file: Path) -> None:
        """Export table to CSV format using COPY command."""
        query = f"\\COPY (SELECT * FROM {table_name}) TO '{output_file}' WITH CSV HEADER"

        cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", Config.DATABASE_NAME,
            "-c", query,
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise MigrationError(f"CSV export failed: {result.stderr}")

    def _export_json(self, table_name: str, output_file: Path) -> None:
        """Export table to JSON format."""
        query = f"SELECT row_to_json({table_name}) FROM {table_name}"

        cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", Config.DATABASE_NAME,
            "-t",  # Tuples only
            "-A",  # Unaligned
            "-c", query,
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise MigrationError(f"JSON export failed: {result.stderr}")

        # Parse and write as JSON array
        rows = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        with open(output_file, "w") as f:
            json.dump(rows, f, indent=2, default=str)

    def _export_sql(self, table_name: str, output_file: Path) -> None:
        """Export table to SQL dump format."""
        cmd = [
            "pg_dump",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", Config.DATABASE_NAME,
            "-t", table_name,
            "--no-owner",
            "--no-acl",
            "-f", str(output_file),
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise MigrationError(f"SQL export failed: {result.stderr}")

    def import_csv(
        self,
        table_name: str,
        csv_file: Path,
        truncate: bool = False,
    ) -> int:
        """
        Import data from CSV file into a table.

        Args:
            table_name: Target table name
            csv_file: Path to CSV file
            truncate: Whether to truncate table before import

        Returns:
            Number of rows imported

        Raises:
            MigrationError: If import fails
        """
        if not csv_file.exists():
            raise MigrationError(f"CSV file not found: {csv_file}")

        self.logger.info(f"Importing CSV into table '{table_name}'")

        try:
            # Truncate if requested
            if truncate:
                self._truncate_table(table_name)

            # Import using COPY
            query = f"\\COPY {table_name} FROM '{csv_file}' WITH CSV HEADER"

            cmd = [
                "psql",
                "-h", Config.DATABASE_HOST,
                "-p", str(Config.DATABASE_PORT),
                "-U", Config.DATABASE_USER,
                "-d", Config.DATABASE_NAME,
                "-c", query,
            ]

            env = os.environ.copy()
            if Config.DATABASE_PASSWORD:
                env["PGPASSWORD"] = Config.DATABASE_PASSWORD

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                raise MigrationError(f"CSV import failed: {result.stderr}")

            # Count rows
            row_count = self._count_rows(table_name)
            self.logger.info(f"Import complete: {row_count} rows")

            return row_count

        except Exception as e:
            self.logger.error(f"Import failed: {str(e)}")
            raise MigrationError(f"CSV import failed: {str(e)}") from e

    def _truncate_table(self, table_name: str) -> None:
        """Truncate a table."""
        self.logger.warning(f"Truncating table: {table_name}")

        cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", Config.DATABASE_NAME,
            "-c", f"TRUNCATE TABLE {table_name} CASCADE;",
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise MigrationError(f"Truncate failed: {result.stderr}")

    def _count_rows(self, table_name: str) -> int:
        """Count rows in a table."""
        cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", Config.DATABASE_NAME,
            "-t",
            "-A",
            "-c", f"SELECT COUNT(*) FROM {table_name};",
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)

        return int(result.stdout.strip())

    def export_schema(self, output_file: Path | None = None) -> Path:
        """
        Export database schema only (no data).

        Args:
            output_file: Output file path (default: auto-generated)

        Returns:
            Path to the schema file
        """
        if not output_file:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_file = self.output_dir / f"schema_{timestamp}.sql"

        self.logger.info(f"Exporting database schema to {output_file}")

        cmd = [
            "pg_dump",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", Config.DATABASE_NAME,
            "--schema-only",
            "--no-owner",
            "--no-acl",
            "-f", str(output_file),
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True)

        if result.returncode != 0:
            raise MigrationError(f"Schema export failed: {result.stderr}")

        self.logger.info(f"Schema exported: {output_file}")
        return output_file

    def create_migration_package(
        self,
        include_tables: list[str] | None = None,
        format: str = "csv",
    ) -> Path:
        """
        Create a complete migration package with schema and data.

        Args:
            include_tables: List of tables to include (default: all)
            format: Data format ('csv', 'json', 'sql')

        Returns:
            Path to the migration package directory
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        package_dir = self.output_dir / f"migration_package_{timestamp}"
        package_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"Creating migration package: {package_dir}")

        try:
            # Export schema
            schema_file = package_dir / "schema.sql"
            self.export_schema(schema_file)

            # Get table list
            if not include_tables:
                include_tables = self._get_table_list()

            # Export each table
            for table in include_tables:
                try:
                    output_file = package_dir / f"{table}.{format}"
                    self.export_table(table, format=format, output_file=output_file)
                except Exception as e:
                    self.logger.warning(f"Failed to export table {table}: {str(e)}")

            # Create manifest
            manifest = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "database": Config.DATABASE_NAME,
                "format": format,
                "tables": include_tables,
                "schema_file": "schema.sql",
            }

            manifest_file = package_dir / "manifest.json"
            with open(manifest_file, "w") as f:
                json.dump(manifest, f, indent=2)

            self.logger.info(f"Migration package created: {package_dir}")
            return package_dir

        except Exception as e:
            self.logger.error(f"Failed to create migration package: {str(e)}")
            raise MigrationError(f"Migration package creation failed: {str(e)}") from e

    def _get_table_list(self) -> list[str]:
        """Get list of all tables in the database."""
        query = """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
        """

        cmd = [
            "psql",
            "-h", Config.DATABASE_HOST,
            "-p", str(Config.DATABASE_PORT),
            "-U", Config.DATABASE_USER,
            "-d", Config.DATABASE_NAME,
            "-t",
            "-A",
            "-c", query,
        ]

        env = os.environ.copy()
        if Config.DATABASE_PASSWORD:
            env["PGPASSWORD"] = Config.DATABASE_PASSWORD

        result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)

        tables = [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        return tables


def main():
    """Main data migration process."""
    parser = argparse.ArgumentParser(
        description="Database migration and data export/import tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export a table to CSV
  python scripts/data_migration.py --export-table channels --format csv

  # Export all tables to JSON
  python scripts/data_migration.py --export-table channels videos fingerprints --format json

  # Export schema only
  python scripts/data_migration.py --export-schema

  # Create complete migration package
  python scripts/data_migration.py --create-package

  # Import CSV data
  python scripts/data_migration.py --import-csv channels ./data/channels.csv

  # Import with table truncation
  python scripts/data_migration.py --import-csv channels ./data/channels.csv --truncate
        """,
    )

    parser.add_argument(
        "--export-table",
        nargs="+",
        metavar="TABLE",
        help="Export one or more tables",
    )

    parser.add_argument(
        "--export-schema",
        action="store_true",
        help="Export database schema only",
    )

    parser.add_argument(
        "--create-package",
        action="store_true",
        help="Create complete migration package",
    )

    parser.add_argument(
        "--import-csv",
        nargs=2,
        metavar=("TABLE", "FILE"),
        help="Import CSV file into table",
    )

    parser.add_argument(
        "--truncate",
        action="store_true",
        help="Truncate table before import",
    )

    parser.add_argument(
        "--format",
        choices=["csv", "json", "sql"],
        default="csv",
        help="Export format (default: csv)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./migrations",
        help="Output directory for exports (default: ./migrations)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set logging level",
    )

    parser.add_argument(
        "--no-colors",
        action="store_true",
        help="Disable colored output",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(
        log_level=args.log_level,
        log_file="data_migration.log",
        use_colors=not args.no_colors,
    )
    logger = logging.getLogger(__name__)

    try:
        migrator = DataMigration(output_dir=args.output_dir)

        if args.export_table:
            # Export tables
            for table in args.export_table:
                output_file = migrator.export_table(table, format=args.format)
                print(f"Exported: {output_file}")

        elif args.export_schema:
            # Export schema
            output_file = migrator.export_schema()
            print(f"Schema exported: {output_file}")

        elif args.create_package:
            # Create migration package
            package_dir = migrator.create_migration_package(format=args.format)
            print(f"Migration package created: {package_dir}")

        elif args.import_csv:
            # Import CSV
            table_name, csv_file = args.import_csv
            row_count = migrator.import_csv(
                table_name,
                Path(csv_file),
                truncate=args.truncate,
            )
            print(f"Imported {row_count} rows into {table_name}")

        else:
            parser.print_help()
            sys.exit(1)

        sys.exit(0)

    except MigrationError as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("Migration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
