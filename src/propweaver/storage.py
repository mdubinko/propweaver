"""
Storage layer for PropWeaver - handles all database operations.

This module contains the low-level database operations including:
- TypeMapper for Python type to SQL conversion
- StorageLayer for all SQL operations
- Transaction management
"""

from __future__ import annotations

import functools
import json
import sqlite3
import time
import warnings
from contextlib import contextmanager
from datetime import date, datetime
from typing import Any, Literal, Optional, Union

from .logging_utils import get_logger, log_storage_operation, log_sql_query, log_error_with_context


def deprecated(reason: str):
    """Mark functions as deprecated with a warning message

    TODO: Pre-release deprecation decorator to help identify API methods
    that should be considered for removal before v1.0 release. This forces
    us to make conscious decisions about which legacy methods to keep.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated: {reason}", DeprecationWarning, stacklevel=2
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


class TypeMapper:
    """Maps between Python types and storage format"""

    MappedType = Literal["str", "int", "float", "bool", "datetime", "date", "json"]

    # Python types that can be stored as properties (excludes None)
    PropertyValue = Union[str, int, float, bool, datetime, date, list, dict]

    @staticmethod
    def to_storage(value: Any) -> tuple[str, TypeMapper.MappedType]:
        """Convert Python value to (string_value, datatype) for storage"""
        if value is None:
            raise ValueError(
                "None values are not allowed as property values. Use 'del props[key]' to remove properties."
            )

        match value:
            case bool():  # Check bool before int (bool is subclass of int)
                return ("true" if value else "false", "bool")
            case int():
                return (str(value), "int")
            case float():
                return (str(value), "float")
            case datetime():
                return (value.isoformat(), "datetime")
            case date():
                return (value.isoformat(), "date")
            case list() | dict():
                return (json.dumps(value), "json")
            case _:
                return (str(value), "str")

    @staticmethod
    def from_storage(str_value: str, datatype: TypeMapper.MappedType) -> Any:
        """Convert stored string back to Python value using datatype"""
        match datatype:
            case "str":
                return str_value
            case "int":
                return int(str_value)
            case "float":
                return float(str_value)
            case "bool":
                return str_value == "true"
            case "datetime":
                return datetime.fromisoformat(str_value)
            case "date":
                return date.fromisoformat(str_value)
            case "json":
                return json.loads(str_value)
            case _:
                # Fallback for unknown types
                return str_value


class StorageLayer:
    """Internal storage layer - handles all SQL operations"""

    def __init__(self, db_path: Optional[str] = None, allowed_base_dir: Optional[str] = None):
        # None -> in-memory, "" -> temp file (auto-deleted), "path" -> persistent file
        raw_path = ":memory:" if db_path is None else db_path
        self.db_path = self._validate_db_path(raw_path, allowed_base_dir)
        self.logger = get_logger("storage")

        start_time = time.time()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

        # Enable foreign key constraints (required for CASCADE behavior)
        self.__execute("PRAGMA foreign_keys = ON")

        # Only initialize schema if needed (new/empty database)
        needs_init = self._needs_initialization()
        if needs_init:
            self._initialize_schema()
            self._create_indexes()
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.summary(f"🏗️ Database initialized: 6 tables, 4 indexes ({elapsed_ms:.0f}ms)")
        else:
            elapsed_ms = (time.time() - start_time) * 1000
            self.logger.info(f"📊 Database connected ({elapsed_ms:.1f}ms): {self.db_path}")

    def _validate_db_path(self, db_path: str, allowed_base_dir: Optional[str] = None) -> str:
        """Validate database path to prevent directory traversal attacks

        Args:
            db_path: Path to validate
            allowed_base_dir: Optional base directory to restrict paths to

        Returns:
            Validated path (absolute path for files, unchanged for special paths)

        Raises:
            ValueError: If path contains traversal attempts or is outside allowed directory

        Security Notes:
            - Special SQLite paths (":memory:", "") are allowed unchanged
            - File paths are resolved to absolute paths
            - Path traversal sequences ("../") are detected and rejected
            - Optional restriction to a specific base directory
        """
        from pathlib import Path

        # Special SQLite paths are allowed unchanged
        if db_path in [":memory:", ""]:
            return db_path

        # Convert to Path object and resolve to absolute path
        # This normalizes the path and resolves symlinks
        try:
            path_obj = Path(db_path).resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid database path: {e}")

        # Check for path traversal attempts in the original path
        # Even though resolve() normalizes, we check the input for security
        if ".." in db_path:
            raise ValueError(
                f"Path traversal detected in database path: {db_path}. "
                "Use absolute paths or paths without '..' sequences."
            )

        # If base directory is specified, ensure path is within it
        if allowed_base_dir is not None:
            base_path = Path(allowed_base_dir).resolve()

            # Check if the resolved path is within the base directory
            try:
                path_obj.relative_to(base_path)
            except ValueError:
                raise ValueError(
                    f"Database path must be within {base_path}. "
                    f"Attempted path: {path_obj}"
                )

        return str(path_obj)

    def __execute(self, sql: str, params: Any = None):
        """Execute SQL with logging"""
        start_time = time.time()

        if params is None:
            result = self.conn.execute(sql)
        else:
            result = self.conn.execute(sql, params)

        elapsed_ms = (time.time() - start_time) * 1000
        self.logger.sql(sql, params, elapsed_ms)

        return result

    def _needs_initialization(self) -> bool:
        """Check if database needs schema initialization"""
        cursor = self.__execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='resource'"
        )
        return cursor.fetchone() is None

    # Schema operations
    def _initialize_schema(self):
        """Create tables and schema if they don't exist"""

        # Nodes (resources)
        self.__execute(
            """
            CREATE TABLE IF NOT EXISTS resource (
                id INTEGER PRIMARY KEY,
                type TEXT NOT NULL,
                created_at REAL NOT NULL
            )
        """
        )

        # Node properties
        self.__execute(
            """
            CREATE TABLE IF NOT EXISTS resource_props (
                res_id INTEGER NOT NULL,
                k TEXT NOT NULL,
                v TEXT NOT NULL,
                datatype TEXT NOT NULL CHECK (datatype IN ('str', 'int', 'float', 'bool', 'datetime', 'date', 'json')),
                PRIMARY KEY (res_id, k),
                FOREIGN KEY (res_id) REFERENCES resource(id) ON DELETE CASCADE
            )
        """
        )

        # Edges (relationships)
        self.__execute(
            """
            CREATE TABLE IF NOT EXISTS rel (
                id INTEGER PRIMARY KEY,
                src_id INTEGER NOT NULL,
                dst_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                created_at REAL NOT NULL,
                FOREIGN KEY (src_id) REFERENCES resource(id) ON DELETE CASCADE,
                FOREIGN KEY (dst_id) REFERENCES resource(id) ON DELETE CASCADE
            )
        """
        )

        # Edge properties
        self.__execute(
            """
            CREATE TABLE IF NOT EXISTS rel_props (
                rel_id INTEGER NOT NULL,
                k TEXT NOT NULL,
                v TEXT NOT NULL,
                datatype TEXT NOT NULL CHECK (datatype IN ('str', 'int', 'float', 'bool', 'datetime', 'date', 'json')),
                PRIMARY KEY (rel_id, k),
                FOREIGN KEY (rel_id) REFERENCES rel(id) ON DELETE CASCADE
            )
        """
        )

        # Graph metadata (single row table)
        self.__execute(
            """
            CREATE TABLE IF NOT EXISTS graph_metadata (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                created_at REAL NOT NULL
            )
        """
        )

        # Graph properties
        self.__execute(
            """
            CREATE TABLE IF NOT EXISTS graph_metadata_props (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL,
                datatype TEXT NOT NULL CHECK (datatype IN ('str', 'int', 'float', 'bool', 'datetime', 'date', 'json'))
            )
        """
        )

        self.conn.commit()

        # Ensure graph metadata row exists with schema version
        cursor = self.__execute("SELECT COUNT(*) FROM graph_metadata")
        if cursor.fetchone()[0] == 0:
            created_at = time.time()
            self.__execute(
                "INSERT INTO graph_metadata (id, created_at) VALUES (1, ?)", (created_at,)
            )
            self.__execute(
                "INSERT INTO graph_metadata_props (k, v, datatype) VALUES (?, ?, ?)",
                ("schema_version", "1", "int"),
            )
            self.conn.commit()

    def _create_indexes(self):
        """Create performance indexes"""

        # Resource indexes
        self.__execute("CREATE INDEX IF NOT EXISTS idx_resource_type ON resource(type)")
        self.__execute("CREATE INDEX IF NOT EXISTS idx_resource_created ON resource(created_at)")

        # Property indexes for common lookups
        self.__execute("CREATE INDEX IF NOT EXISTS idx_resource_props_k ON resource_props(k)")
        self.__execute("CREATE INDEX IF NOT EXISTS idx_resource_props_v ON resource_props(v)")
        self.__execute("CREATE INDEX IF NOT EXISTS idx_resource_props_kv ON resource_props(k, v)")

        # Relationship indexes
        self.__execute("CREATE INDEX IF NOT EXISTS idx_rel_type ON rel(type)")
        self.__execute("CREATE INDEX IF NOT EXISTS idx_rel_src ON rel(src_id)")
        self.__execute("CREATE INDEX IF NOT EXISTS idx_rel_dst ON rel(dst_id)")
        self.__execute("CREATE INDEX IF NOT EXISTS idx_rel_src_type ON rel(src_id, type)")
        self.__execute("CREATE INDEX IF NOT EXISTS idx_rel_dst_type ON rel(dst_id, type)")

        self.conn.commit()

    # Node operations
    def _insert_node(self, node_type: str, properties: dict) -> int:
        """Insert node and return node_id"""
        created_at = time.time()

        cursor = self.__execute(
            "INSERT INTO resource (type, created_at) VALUES (?, ?)", (node_type, created_at)
        )
        node_id = cursor.lastrowid

        # Insert properties
        for key, value in properties.items():
            str_value, datatype = TypeMapper.to_storage(value)
            self.__execute(
                "INSERT INTO resource_props (res_id, k, v, datatype) VALUES (?, ?, ?, ?)",
                (node_id, key, str_value, datatype),
            )

        return node_id

    def _insert_edge(self, src_id: int, dst_id: int, edge_type: str, properties: dict) -> int:
        """Insert edge and return edge_id"""
        created_at = time.time()

        cursor = self.__execute(
            "INSERT INTO rel (src_id, dst_id, type, created_at) VALUES (?, ?, ?, ?)",
            (src_id, dst_id, edge_type, created_at),
        )
        edge_id = cursor.lastrowid

        # Insert properties
        for key, value in properties.items():
            str_value, datatype = TypeMapper.to_storage(value)
            self.__execute(
                "INSERT INTO rel_props (rel_id, k, v, datatype) VALUES (?, ?, ?, ?)",
                (edge_id, key, str_value, datatype),
            )

        return edge_id

    # --- Generic Property Helpers (Internal) ---

    def __get_properties_from_table(
        self, table_name: str, owner_id_col: str, owner_id: int
    ) -> dict:
        """Generic helper to get all properties from a specified table."""
        sql = f"SELECT k, v, datatype FROM {table_name} WHERE {owner_id_col} = ?"
        cursor = self.__execute(sql, (owner_id,))

        result = {}
        for row in cursor.fetchall():
            key = row["k"]
            value = TypeMapper.from_storage(row["v"], row["datatype"])
            result[key] = value
        return result

    def __get_property_from_table(
        self, table_name: str, owner_id_col: str, owner_id: int, key: str
    ) -> Any:
        """Generic helper to get a property from a specified table."""
        properties = self.__get_properties_from_table(table_name, owner_id_col, owner_id)
        return properties.get(key)

    def __set_property_in_table(
        self, table_name: str, owner_id_col: str, owner_id: int, key: str, value: Any
    ):
        """Generic helper to set a property in a specified table."""
        str_value, datatype = TypeMapper.to_storage(value)
        sql = f"INSERT OR REPLACE INTO {table_name} ({owner_id_col}, k, v, datatype) VALUES (?, ?, ?, ?)"
        self.__execute(sql, (owner_id, key, str_value, datatype))

    def __delete_property_from_table(
        self, table_name: str, owner_id_col: str, owner_id: int, key: str
    ):
        """Generic helper to delete a property from a specified table."""
        sql = f"DELETE FROM {table_name} WHERE {owner_id_col} = ? AND k = ?"
        cursor = self.__execute(sql, (owner_id, key))
        if cursor.rowcount == 0:
            raise KeyError(f"Property '{key}' not found")

    def __has_property_in_table(
        self, table_name: str, owner_id_col: str, owner_id: int, key: str
    ) -> bool:
        """Generic helper to check for a property in a specified table."""
        sql = f"SELECT 1 FROM {table_name} WHERE {owner_id_col} = ? AND k = ?"
        cursor = self.__execute(sql, (owner_id, key))
        return cursor.fetchone() is not None

    def __get_timestamp_from_table(self, table_name: str, id_col: str, entity_id: int) -> float:
        """Generic helper to get created_at timestamp from any table."""
        sql = f"SELECT created_at FROM {table_name} WHERE {id_col} = ?"
        cursor = self.__execute(sql, (entity_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Entity not found in {table_name}")
        return row[0]

    # --- Node Property Wrappers ---

    def _get_node_property(self, node_id: int, key: str) -> Any:
        """Get single node property."""
        return self.__get_property_from_table("resource_props", "res_id", node_id, key)

    def _set_node_property(self, node_id: int, key: str, value: Any):
        """Set single node property."""
        self.__set_property_in_table("resource_props", "res_id", node_id, key, value)

    def _delete_node_property(self, node_id: int, key: str):
        """Delete a specific node property."""
        self.__delete_property_from_table("resource_props", "res_id", node_id, key)

    def _has_node_property(self, node_id: int, key: str) -> bool:
        """Check if node has a specific property."""
        return self.__has_property_in_table("resource_props", "res_id", node_id, key)

    # --- Edge Property Wrappers ---

    def _get_edge_property(self, edge_id: int, key: str) -> Any:
        """Get single edge property."""
        return self.__get_property_from_table("rel_props", "rel_id", edge_id, key)

    def _set_edge_property(self, edge_id: int, key: str, value: Any):
        """Set single edge property."""
        self.__set_property_in_table("rel_props", "rel_id", edge_id, key, value)

    def _delete_edge_property(self, edge_id: int, key: str):
        """Delete a specific edge property."""
        self.__delete_property_from_table("rel_props", "rel_id", edge_id, key)

    def _has_edge_property(self, edge_id: int, key: str) -> bool:
        """Check if edge has a specific property."""
        return self.__has_property_in_table("rel_props", "rel_id", edge_id, key)

    # --- Timestamp Operations ---

    def _get_node_timestamp(self, node_id: int) -> float:
        """Get node creation timestamp."""
        return self.__get_timestamp_from_table("resource", "id", node_id)

    def _get_edge_timestamp(self, edge_id: int) -> float:
        """Get edge creation timestamp."""
        return self.__get_timestamp_from_table("rel", "id", edge_id)

    def _get_graph_timestamp(self) -> float:
        """Get graph creation timestamp."""
        return self.__get_timestamp_from_table("graph_metadata", "id", 1)

    # --- Graph Property Operations ---

    def _get_graph_property(self, key: str) -> Any:
        """Get graph-level property."""
        cursor = self.__execute("SELECT v, datatype FROM graph_metadata_props WHERE k = ?", (key,))
        row = cursor.fetchone()
        return TypeMapper.from_storage(row["v"], row["datatype"]) if row else None

    def _set_graph_property(self, key: str, value: Any):
        """Set graph-level property."""
        str_value, datatype = TypeMapper.to_storage(value)
        self.__execute(
            "INSERT OR REPLACE INTO graph_metadata_props (k, v, datatype) VALUES (?, ?, ?)",
            (key, str_value, datatype),
        )

    def _delete_graph_property(self, key: str):
        """Delete a specific graph property."""
        cursor = self.__execute("DELETE FROM graph_metadata_props WHERE k = ?", (key,))
        if cursor.rowcount == 0:
            raise KeyError(f"Property '{key}' not found on graph")

    def _has_graph_property(self, key: str) -> bool:
        """Check if graph has a specific property."""
        cursor = self.__execute("SELECT 1 FROM graph_metadata_props WHERE k = ?", (key,))
        return cursor.fetchone() is not None

    def _clear_node_properties(self, node_id: int) -> None:
        """Clear all properties for a node"""
        self.__execute(
            """
            DELETE FROM resource_props WHERE res_id = ?
        """,
            (node_id,),
        )

    def _clear_edge_properties(self, edge_id: int) -> None:
        """Clear all properties for an edge"""
        self.__execute(
            """
            DELETE FROM rel_props WHERE rel_id = ?
        """,
            (edge_id,),
        )

    def _clear_graph_properties(self) -> None:
        """Clear all properties for the graph"""
        self.__execute("DELETE FROM graph_metadata_props")

    def _count_node_properties(self, node_id: int) -> int:
        """Get count of properties for a node"""
        cursor = self.__execute(
            """
            SELECT COUNT(*) FROM resource_props 
            WHERE res_id = ?
        """,
            (node_id,),
        )
        return cursor.fetchone()[0]

    def _count_edge_properties(self, edge_id: int) -> int:
        """Get count of properties for an edge"""
        cursor = self.__execute(
            """
            SELECT COUNT(*) FROM rel_props 
            WHERE rel_id = ?
        """,
            (edge_id,),
        )
        return cursor.fetchone()[0]

    def _count_graph_properties(self) -> int:
        """Get count of properties for the graph"""
        cursor = self.__execute("SELECT COUNT(*) FROM graph_metadata_props")
        return cursor.fetchone()[0]

    def _get_node_property_keys(self, node_id: int) -> list[str]:
        """Get all property keys for a node"""
        cursor = self.__execute(
            """
            SELECT k FROM resource_props 
            WHERE res_id = ?
        """,
            (node_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    def _get_edge_property_keys(self, edge_id: int) -> list[str]:
        """Get all property keys for an edge"""
        cursor = self.__execute(
            """
            SELECT k FROM rel_props 
            WHERE rel_id = ?
        """,
            (edge_id,),
        )
        return [row[0] for row in cursor.fetchall()]

    def _get_graph_property_keys(self) -> list[str]:
        """Get all property keys for the graph"""
        cursor = self.__execute("SELECT k FROM graph_metadata_props")
        return [row[0] for row in cursor.fetchall()]

    def _get_node_properties(self, node_id: int) -> dict:
        """Get all properties for a node"""
        return self.__get_properties_from_table("resource_props", "res_id", node_id)

    def _get_edge_properties(self, edge_id: int) -> dict:
        """Get all properties for an edge"""
        return self.__get_properties_from_table("rel_props", "rel_id", edge_id)

    def _get_graph_properties(self) -> dict:
        """Get all properties for the graph"""
        # Graph properties don't have an owner_id, so use a special case
        cursor = self.__execute("SELECT k, v, datatype FROM graph_metadata_props")

        result = {}
        for row in cursor.fetchall():
            key = row["k"]
            value = TypeMapper.from_storage(row["v"], row["datatype"])
            result[key] = value
        return result

    def _update_node_properties(
        self, node_id: int, props: dict[str, TypeMapper.PropertyValue]
    ) -> None:
        """Bulk update multiple node properties"""
        for key, value in props.items():
            storage_value, datatype = TypeMapper.to_storage(value)
            self.__execute(
                """
                INSERT OR REPLACE INTO resource_props (res_id, k, v, datatype)
                VALUES (?, ?, ?, ?)
            """,
                (node_id, key, storage_value, datatype),
            )

    def _update_edge_properties(
        self, edge_id: int, props: dict[str, TypeMapper.PropertyValue]
    ) -> None:
        """Bulk update multiple edge properties"""
        for key, value in props.items():
            storage_value, datatype = TypeMapper.to_storage(value)
            self.__execute(
                """
                INSERT OR REPLACE INTO rel_props (rel_id, k, v, datatype)
                VALUES (?, ?, ?, ?)
            """,
                (edge_id, key, storage_value, datatype),
            )

    def _update_graph_properties(self, props: dict[str, TypeMapper.PropertyValue]) -> None:
        """Bulk update multiple graph properties"""
        for key, value in props.items():
            storage_value, datatype = TypeMapper.to_storage(value)
            self.__execute(
                """
                INSERT OR REPLACE INTO graph_metadata_props (k, v, datatype)
                VALUES (?, ?, ?)
            """,
                (key, storage_value, datatype),
            )

    @contextmanager
    def transaction(self):
        """Transaction context manager for atomic operations

        Example:
            with storage.transaction():
                storage._delete_node(1)
                storage._delete_node(2)
                # Commits automatically on successful exit
                # Rolls back on exception
        """
        try:
            # SQLite transactions start automatically with first write
            # We just need to manage commit/rollback
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self):
        """Close connection"""
        self.conn.close()

    def commit(self):
        """Commit transaction"""
        self.conn.commit()

    def _execute_query_steps(self, query):
        """Execute step-based query specification"""
        if not query.steps:
            # No steps - return empty result
            return []

        # Convert steps to parameters for existing query methods
        node_type = None
        properties = {}
        limit = query.limit

        for step in query.steps:
            if step.type == "SOURCE":
                continue  # All nodes source
            elif step.type == "FILTER":
                if step.node_type:
                    node_type = step.node_type
                if step.properties:
                    properties.update(step.properties)
            elif step.type == "TRAVERSE":
                # TODO: Implement traversal - for now just return nodes
                pass

        # Execute as simple node query
        if query.returning in ["nodes", "target_nodes", "source_nodes"]:
            return self.query_nodes(node_type, limit, properties)
        else:
            return []

    def query_nodes(
        self,
        node_type: Optional[str] = None,
        limit: Optional[int] = None,
        properties: Optional[dict] = None,
    ):
        """Query nodes with filtering"""
        properties = properties or {}

        # Build query
        query_parts = ["SELECT id, type FROM resource r"]
        conditions = []
        parameters = []

        if node_type:
            conditions.append("r.type = ?")
            parameters.append(node_type)

        # Add property filters
        for key, value in properties.items():
            alias = f"p{len(parameters)}"
            query_parts.append(f"JOIN resource_props {alias} ON r.id = {alias}.res_id")
            str_value, _ = TypeMapper.to_storage(value)
            conditions.append(f"{alias}.k = ? AND {alias}.v = ?")
            parameters.extend([key, str_value])

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY r.id")

        if limit:
            query_parts.append("LIMIT ?")
            parameters.append(limit)

        query = " ".join(query_parts)
        cursor = self.__execute(query, parameters)
        return cursor.fetchall()

    def query_edges(
        self,
        edge_type: Optional[str] = None,
        limit: Optional[int] = None,
        properties: Optional[dict] = None,
    ):
        """Query edges with filtering"""
        properties = properties or {}

        # Build query
        query_parts = ["SELECT id, src_id, dst_id, type FROM rel r"]
        conditions = []
        parameters = []

        if edge_type:
            conditions.append("r.type = ?")
            parameters.append(edge_type)

        # Add property filters
        for key, value in properties.items():
            alias = f"p{len(parameters)}"
            query_parts.append(f"JOIN rel_props {alias} ON r.id = {alias}.rel_id")
            str_value, _ = TypeMapper.to_storage(value)
            conditions.append(f"{alias}.k = ? AND {alias}.v = ?")
            parameters.extend([key, str_value])

        if conditions:
            query_parts.append("WHERE " + " AND ".join(conditions))

        query_parts.append("ORDER BY r.id")

        if limit:
            query_parts.append("LIMIT ?")
            parameters.append(limit)

        query = " ".join(query_parts)
        cursor = self.__execute(query, parameters)
        return cursor.fetchall()

    def _query_edges_by_spec(self, query):
        """Execute edge query by spec"""
        if not query.steps:
            # No steps - return empty result
            return []

        # Convert steps to parameters for existing query methods
        edge_type = None
        properties = {}
        limit = query.limit

        for step in query.steps:
            if step.type == "SOURCE":
                continue  # All edges source
            elif step.type == "FILTER":
                if hasattr(step, "edge_type") and step.edge_type:
                    edge_type = step.edge_type
                if hasattr(step, "node_type") and step.node_type:
                    edge_type = step.node_type  # Treat as edge type for compatibility
                if step.properties:
                    properties.update(step.properties)
            elif step.type == "TRAVERSE":
                # TODO: Implement traversal - for now just return edges
                pass

        # Execute as simple edge query
        if query.returning in ["edges", "relationships"]:
            return self.query_edges(edge_type, limit, properties)
        else:
            return []

    def _count_nodes(self) -> int:
        """Count total number of nodes"""
        cursor = self.__execute("SELECT COUNT(*) FROM resource")
        return cursor.fetchone()[0]

    def _count_edges(self) -> int:
        """Count total number of edges"""
        cursor = self.__execute("SELECT COUNT(*) FROM rel")
        return cursor.fetchone()[0]

    def _list_node_types(self) -> list[str]:
        """List all distinct node types in the graph"""
        cursor = self.__execute("SELECT DISTINCT type FROM resource ORDER BY type")
        return [row[0] for row in cursor.fetchall()]

    def _list_edge_types(self) -> list[str]:
        """List all distinct edge types in the graph"""
        cursor = self.__execute("SELECT DISTINCT type FROM rel ORDER BY type")
        return [row[0] for row in cursor.fetchall()]

    def _delete_node(self, node_id: int):
        """Delete a node and all its properties and edges"""

        # Delete node (CASCADE will handle properties and edges)
        self.__execute("DELETE FROM resource WHERE id = ?", (node_id,))

    def _delete_edge(self, edge_id: int):
        """Delete an edge and all its properties"""

        # Delete edge (CASCADE will handle properties)
        self.__execute("DELETE FROM rel WHERE id = ?", (edge_id,))
