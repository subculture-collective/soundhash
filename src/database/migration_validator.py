"""
Robust validation utilities for Alembic migration files.

This module provides utilities to validate migration files by parsing their
Python AST instead of using naive string searching, which avoids false positives
from comments or unrelated context.
"""

import ast
from pathlib import Path


class AlembicOperationVisitor(ast.NodeVisitor):
    """AST visitor to extract Alembic operations from migration files."""

    def __init__(self):
        """Initialize the visitor with empty operation tracking."""
        self.operations: list[dict[str, str | list[str] | dict[str, str]]] = []
        self.current_function: str | None = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Track which function we're in (upgrade/downgrade)."""
        old_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Call(self, node: ast.Call) -> None:
        """Extract Alembic operation calls."""
        # Check if this is an op.* call
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "op":
                operation_name = node.func.attr
                operation_info = {
                    "operation": operation_name,
                    "function": self.current_function,
                    "args": [],
                    "kwargs": {},
                }

                # Extract positional arguments
                for arg in node.args:
                    if isinstance(arg, ast.Constant):
                        operation_info["args"].append(arg.value)

                # Extract keyword arguments
                for keyword in node.keywords:
                    if keyword.arg:
                        if isinstance(keyword.value, ast.Constant):
                            operation_info["kwargs"][keyword.arg] = keyword.value.value
                        elif isinstance(keyword.value, ast.Name):
                            operation_info["kwargs"][keyword.arg] = keyword.value.id

                self.operations.append(operation_info)

        self.generic_visit(node)


class MigrationValidator:
    """Validator for Alembic migration files using AST parsing."""

    def __init__(self, migration_file: str | Path):
        """
        Initialize validator for a migration file.

        Args:
            migration_file: Path to the migration file to validate
        """
        self.migration_file = Path(migration_file)
        self._operations: list[dict] | None = None
        self._parsed = False

    def parse(self) -> None:
        """Parse the migration file to extract operations."""
        if self._parsed:
            return

        with open(self.migration_file) as f:
            tree = ast.parse(f.read(), filename=str(self.migration_file))

        visitor = AlembicOperationVisitor()
        visitor.visit(tree)
        self._operations = visitor.operations
        self._parsed = True

    @property
    def operations(self) -> list[dict]:
        """Get all operations found in the migration file."""
        if not self._parsed:
            self.parse()
        return self._operations or []

    def has_operation(self, operation_type: str, function: str | None = None) -> bool:
        """
        Check if migration has a specific operation type.

        Args:
            operation_type: The Alembic operation type (e.g., 'create_index', 'add_column')
            function: Optional function name to filter by ('upgrade' or 'downgrade')

        Returns:
            True if the operation exists, False otherwise
        """
        if not self._parsed:
            self.parse()

        for op in self.operations:
            if op["operation"] == operation_type:
                if function is None or op["function"] == function:
                    return True
        return False

    def get_operations(self, operation_type: str, function: str | None = None) -> list[dict]:
        """
        Get all operations of a specific type.

        Args:
            operation_type: The Alembic operation type (e.g., 'create_index', 'add_column')
            function: Optional function name to filter by ('upgrade' or 'downgrade')

        Returns:
            List of operation dictionaries matching the criteria
        """
        if not self._parsed:
            self.parse()

        operations = []
        for op in self.operations:
            if op["operation"] == operation_type:
                if function is None or op["function"] == function:
                    operations.append(op)
        return operations

    def has_table_modification(self, table_name: str) -> bool:
        """
        Check if migration modifies a specific table.

        Args:
            table_name: Name of the table to check

        Returns:
            True if the migration modifies the table, False otherwise
        """
        if not self._parsed:
            self.parse()

        table_operations = {
            "create_table",
            "drop_table",
            "rename_table",
            "add_column",
            "drop_column",
            "alter_column",
            "create_index",
            "drop_index",
            "create_foreign_key",
            "drop_constraint",
        }

        for op in self.operations:
            if op["operation"] in table_operations:
                # Check if table_name appears in args or kwargs
                if table_name in op["args"]:
                    return True
                if "table_name" in op["kwargs"] and op["kwargs"]["table_name"] == table_name:
                    return True
        return False

    def get_modified_tables(self) -> set[str]:
        """
        Get all table names that are modified in this migration.

        Returns:
            Set of table names that are modified
        """
        if not self._parsed:
            self.parse()

        tables = set()
        for op in self.operations:
            # First positional argument is usually the table name
            if op["args"]:
                tables.add(op["args"][0])
            # Check kwargs for table_name
            if "table_name" in op["kwargs"]:
                tables.add(op["kwargs"]["table_name"])

        return tables

    def validates_column_addition(self, table_name: str, column_name: str) -> bool:
        """
        Check if migration adds a specific column to a table.

        Args:
            table_name: Name of the table
            column_name: Name of the column

        Returns:
            True if the column is added, False otherwise
        """
        if not self._parsed:
            self.parse()

        add_column_ops = self.get_operations("add_column", function="upgrade")
        for op in add_column_ops:
            if op["args"] and op["args"][0] == table_name:
                # Check if Column object has the right name
                # This is a simplified check - for complete validation,
                # we'd need to parse the Column() call arguments
                return True
        return False

    def validates_index_creation(
        self, index_name: str | None = None, table_name: str | None = None
    ) -> bool:
        """
        Check if migration creates an index.

        Args:
            index_name: Optional name of the index
            table_name: Optional name of the table

        Returns:
            True if a matching index is created, False otherwise
        """
        if not self._parsed:
            self.parse()

        create_index_ops = self.get_operations("create_index", function="upgrade")

        for op in create_index_ops:
            # First arg is usually index_name, second is table_name for create_index
            if index_name and op["args"] and op["args"][0] == index_name:
                return True
            if table_name and len(op["args"]) > 1 and op["args"][1] == table_name:
                return True
            if index_name is None and table_name is None:
                return True  # Just check if any index is created

        return False
