"""
Core PropWeaver classes - main API and proxy classes.

This module contains the main user-facing classes:
- PropertyGraph: The main graph database class
- NodeProxy: Lightweight proxy for individual nodes
- EdgeProxy: Lightweight proxy for individual edges
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Protocol, Union

from .exceptions import (
    EntityNotFoundError,
    InvalidQueryError,
    PropertyNotFoundError,
    PropertyValueError,
    QueryExecutionError,
)
from .logging_utils import SUMMARY, get_log_level, get_logger, set_log_level, log_error_with_context
from .query import EdgeIterator, NodeIterator, QuerySpec, QueryStep
from .storage import StorageLayer, TypeMapper, deprecated


class PropertyOwner(Protocol):
    """Protocol for objects that can own properties"""

    def _get_property(self, key: str) -> Any: ...
    def _set_property(self, key: str, value: Any) -> None: ...
    def _delete_property(self, key: str) -> None: ...
    def _has_property(self, key: str) -> bool: ...
    def _get_all_properties(self) -> dict: ...
    def _update_properties(self, props: dict) -> None: ...
    def _clear_properties(self) -> None: ...
    def _list_property_keys(self) -> list[str]: ...
    def _count_properties(self) -> int: ...


class PropertyDict:
    """Dict-like interface for properties"""

    def __init__(self, owner: PropertyOwner) -> None:
        self.owner = owner

    def __getitem__(self, key: str) -> Any:
        value = self.owner._get_property(key)
        if not self.owner._has_property(key):
            # Property doesn't exist - get available properties for helpful error
            available_props = self.owner._list_property_keys()
            entity_type = getattr(self.owner, "entity_type", "Entity")
            entity_id = getattr(self.owner, "entity_id", "unknown")
            raise PropertyNotFoundError(key, entity_type, entity_id, available_props)
        return value

    def __setitem__(self, key: str, value: TypeMapper.PropertyValue):
        self.owner._set_property(key, value)

    def __delitem__(self, key: str) -> None:
        if not self.owner._has_property(key):
            raise KeyError(key)
        self.owner._delete_property(key)

    def __contains__(self, key: str) -> bool:
        return self.owner._has_property(key)

    def __len__(self) -> int:
        return self.owner._count_properties()

    def __iter__(self) -> Any:
        return iter(self.owner._list_property_keys())

    def keys(self) -> list[str]:
        """Return property keys"""
        return self.owner._list_property_keys()

    def values(self) -> Any:
        """Return property values"""
        all_props = self.owner._get_all_properties()
        return all_props.values()

    def items(self) -> Any:
        """Return property key-value pairs"""
        all_props = self.owner._get_all_properties()
        return all_props.items()

    def get(self, key: str, default=None) -> Any:
        """Get property with optional default"""
        try:
            return self[key]
        except KeyError:
            return default

    def update(self, other: dict[str, TypeMapper.PropertyValue]) -> None:
        """Update properties from dict"""
        self.owner._update_properties(other)

    def clear(self) -> None:
        """Clear all properties"""
        self.owner._clear_properties()

    def copy(self) -> dict:
        """Return copy as regular dict"""
        return dict(self.owner._get_all_properties())


class PropDict:
    """Base class providing dict-like property access"""

    def __init__(self) -> None:
        self._props = PropertyDict(self)

    @property
    def props(self) -> PropertyDict:
        """Dict-like access to properties"""
        return self._props

    # Abstract methods for subclasses to implement
    def _get_property(self, key: str) -> Any:
        raise NotImplementedError

    def _set_property(self, key: str, value: TypeMapper.PropertyValue) -> None:
        raise NotImplementedError

    def _delete_property(self, key: str) -> None:
        raise NotImplementedError

    def _has_property(self, key: str) -> bool:
        raise NotImplementedError

    def _get_all_properties(self) -> dict:
        raise NotImplementedError

    def _update_properties(self, props: dict[str, TypeMapper.PropertyValue]) -> None:
        raise NotImplementedError

    def _clear_properties(self) -> None:
        raise NotImplementedError

    def _list_property_keys(self) -> list[str]:
        raise NotImplementedError

    def _count_properties(self) -> int:
        raise NotImplementedError


class PropertyGraph:
    """SQLite-backed property graph database

    Example:
        # Create graph and add nodes with properties
        with PropertyGraph() as graph:
            person = graph.add_node("person", name="Alice", age=30)
            city = graph.add_node("city", name="San Francisco")

            # Connect them with a relationship
            lives_in = graph.add_edge(person, "lives_in", city, since=2020)

            # Set graph-level metadata
            graph.props["project_name"] = "Social Network"
            graph.props["version"] = "1.0"

            # Query the graph
            results = list(graph.nodes("person", name="Alice"))
            schema_version = graph.props["schema_version"]  # Always available
        # Automatically closed when exiting with block
    """

    def __init__(
        self, db_path: Optional[str] = None, allowed_base_dir: Optional[str] = None
    ) -> None:
        """Initialize PropertyGraph

        Args:
            db_path: Path to database file. Special values:
                - None: in-memory database (default)
                - "": temporary file (auto-deleted)
                - "/path/to/file.db": persistent database file
            allowed_base_dir: Optional directory to restrict database files to.
                If specified, db_path must be within this directory.
                Use for additional security when paths come from untrusted input.

        Raises:
            ValueError: If db_path contains path traversal or is outside allowed_base_dir

        Security Note:
            Database paths are validated to prevent directory traversal attacks.
            Paths containing ".." are rejected. For additional security with
            untrusted input, specify allowed_base_dir to restrict file locations.

        Example:
            # In-memory database (no file)
            graph = PropertyGraph()

            # Persistent database
            graph = PropertyGraph("my_graph.db")

            # Restricted to specific directory (secure mode)
            graph = PropertyGraph("user_123.db", allowed_base_dir="/var/lib/myapp")
        """
        self._storage = StorageLayer(db_path, allowed_base_dir)
        self._props = PropertyDict(self)

    @property
    def props(self) -> PropertyDict:
        """Dict-like access to graph metadata"""
        return self._props

    # Property interface implementation for graph metadata
    def _get_property(self, key: str) -> Any:
        return self._storage._get_graph_property(key)

    def _set_property(self, key: str, value: Any) -> None:
        self._storage._set_graph_property(key, value)
        self._storage.commit()

    def _delete_property(self, key: str) -> None:
        self._storage._delete_graph_property(key)
        self._storage.commit()

    def _has_property(self, key: str) -> bool:
        return self._storage._has_graph_property(key)

    def _get_all_properties(self) -> dict:
        return self._storage._get_graph_properties()

    def _update_properties(self, props: dict) -> None:
        self._storage._update_graph_properties(props)
        self._storage.commit()

    def _clear_properties(self) -> None:
        self._storage._clear_graph_properties()
        self._storage.commit()

    def _list_property_keys(self) -> list[str]:
        return self._storage._get_graph_property_keys()

    def _count_properties(self) -> int:
        return self._storage._count_graph_properties()

    def add_node(self, node_type: str, **properties) -> NodeProxy:
        """Add a node to the graph with properties

        Example:
            user = graph.add_node("user", name="Bob", email="bob@example.com")
        """
        node_id = self._storage._insert_node(node_type, properties)
        self._storage.commit()
        return NodeProxy(self, node_id, node_type)

    def add_edge(
        self,
        source: Union[NodeProxy, int],
        edge_type: str,
        target: Union[NodeProxy, int],
        **properties,
    ) -> EdgeProxy:
        """Add an edge between two nodes with properties

        Example:
            friendship = graph.add_edge(user1, "friends", user2, since="2023-01-01")
        """
        # Extract node IDs
        src_id = source.node_id if isinstance(source, NodeProxy) else source
        dst_id = target.node_id if isinstance(target, NodeProxy) else target

        edge_id = self._storage._insert_edge(src_id, dst_id, edge_type, properties)
        self._storage.commit()
        return EdgeProxy(self, edge_id, edge_type, src_id, dst_id)

    def nodes(self, node_type: Optional[str] = None, **properties) -> NodeIterator:
        """Start a lazy iterator for nodes (XPath-style)"""
        query_spec = QuerySpec()
        query_spec.steps.append(QueryStep(type="SOURCE", target="all_nodes"))

        if node_type or properties:
            query_spec.steps.append(
                QueryStep(
                    type="FILTER",
                    node_type=node_type,
                    properties=properties if properties else None,
                )
            )

        def factory(row):
            return NodeProxy(self, row["id"], row["type"])

        return NodeIterator(
            query_spec=query_spec,
            executor=self._storage._execute_query_steps,
            factory=factory,
            deleter=self._execute_node_deleter,
        )

    def edges(self, edge_type: Optional[str] = None, **properties) -> EdgeIterator:
        """Start a lazy iterator for edges"""
        query_spec = QuerySpec(returning="edges")
        query_spec.steps.append(QueryStep(type="SOURCE", target="all_edges"))

        if edge_type or properties:
            query_spec.steps.append(
                QueryStep(
                    type="FILTER",
                    edge_type=edge_type,
                    properties=properties if properties else None,
                )
            )

        def factory(row):
            return EdgeProxy(self, row["id"], row["type"], row["src_id"], row["dst_id"])

        return EdgeIterator(
            query_spec=query_spec,
            executor=self._storage._query_edges_by_spec,
            factory=factory,
            deleter=self._execute_edge_deleter,
        )

    def _execute_node_deleter(self, query_spec: QuerySpec) -> int:
        """Deleter function for nodes, managing its own transaction."""
        with self._storage.transaction():
            read_executor = self._storage._execute_query_steps

            def node_factory(row):
                return NodeProxy(self, row["id"], row["type"])

            nodes_to_delete = NodeIterator(
                query_spec, read_executor, node_factory, self._execute_node_deleter
            )

            affected_count = 0
            for node in nodes_to_delete:
                self._storage._delete_node(node.node_id)
                affected_count += 1
            return affected_count

    def _execute_edge_deleter(self, query_spec: QuerySpec) -> int:
        """Deleter function for edges, managing its own transaction."""
        with self._storage.transaction():
            read_executor = self._storage._query_edges_by_spec

            def edge_factory(row):
                return EdgeProxy(self, row["id"], row["type"], row["src_id"], row["dst_id"])

            edges_to_delete = EdgeIterator(
                query_spec, read_executor, edge_factory, self._execute_edge_deleter
            )

            affected_count = 0
            for edge in edges_to_delete:
                self._storage._delete_edge(edge.edge_id)
                affected_count += 1
            return affected_count

    def iter_edges(
        self, edge_type: Optional[str] = None, limit: Optional[int] = None, **properties
    ) -> Any:
        """Iterator over edges with optional filtering.

        This is a convenience method that wraps the main `edges()` query builder.

        Args:
            edge_type: Filter by edge type
            limit: Maximum number of edges to return
            **properties: Property filters

        Example:
            for friendship in graph.iter_edges("friends", active=True):
                print(f"{friendship.src_id} -> {friendship.dst_id}")
        """
        iterator = self.edges(edge_type, **properties)
        if limit is not None:
            iterator = iterator.limit(limit)
        yield from iterator

    def commit(self) -> None:
        """Explicit commit for batch operations"""
        self._storage.commit()

    # Logging control
    def set_log_level(self, level: int) -> None:
        """Set logging level for all PropWeaver operations

        Args:
            level: logging.DEBUG, logging.INFO, logging.SUMMARY (25), etc.

        Example:
            import logging
            from propweaver.logging_utils import SUMMARY

            graph.set_log_level(logging.DEBUG)  # Show all SQL queries
            graph.set_log_level(SUMMARY)        # Token-efficient summaries only
        """
        set_log_level(level)

    def get_log_level(self) -> int:
        """Get current logging level"""
        return get_log_level()

    def close(self) -> None:
        """Close database connection"""
        self._storage.close()

    def __enter__(self) -> "PropertyGraph":
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - automatically close connection"""
        self.close()
        return False  # Don't suppress exceptions

    def __repr__(self) -> str:
        """String representation showing basic graph info"""
        version = self.props.get("schema_version", "unknown")
        return f"PropertyGraph(nodes={self.node_count()}, edges={self.edge_count()}, version={version})"

    def timestamp(self) -> float:
        """Get graph creation timestamp

        Returns:
            Unix timestamp as float
        """
        return self._storage._get_graph_timestamp()

    def node_count(self) -> int:
        """Get total number of nodes in the graph

        Returns:
            Number of nodes as int
        """
        return self._storage._count_nodes()

    def edge_count(self) -> int:
        """Get total number of edges in the graph

        Returns:
            Number of edges as int
        """
        return self._storage._count_edges()

    def node_types(self) -> list[str]:
        """Get list of all distinct node types in the graph

        Returns:
            List of node type strings, sorted alphabetically
        """
        return self._storage._list_node_types()

    def edge_types(self) -> list[str]:
        """Get list of all distinct edge types in the graph

        Returns:
            List of edge type strings, sorted alphabetically
        """
        return self._storage._list_edge_types()

    def resource_stats(self) -> dict:
        """Get resource usage statistics for the graph

        Returns dictionary with database size, entity counts, and property counts.
        Useful for monitoring resource consumption and enforcing limits.

        Returns:
            Dictionary with keys:
            - db_size_bytes: Database file size in bytes (0 for in-memory)
            - db_size_mb: Database file size in MB (0 for in-memory)
            - node_count: Total number of nodes
            - edge_count: Total number of edges
            - node_property_count: Total properties across all nodes
            - edge_property_count: Total properties across all edges
            - graph_property_count: Graph-level property count
            - total_entities: Sum of nodes and edges
            - total_properties: Sum of all properties

        Example:
            stats = graph.resource_stats()
            print(f"Database size: {stats['db_size_mb']:.2f} MB")
            print(f"Total entities: {stats['total_entities']}")

            # Enforce limits
            if stats['node_count'] > MAX_NODES:
                raise ResourceLimitError("Too many nodes")
        """
        import os

        # Get database file size
        db_size = 0
        if self._storage.db_path != ":memory:":
            try:
                db_size = os.path.getsize(self._storage.db_path)
            except (OSError, FileNotFoundError):
                db_size = 0

        # Get entity counts
        node_count = self.node_count()
        edge_count = self.edge_count()

        # Get property counts
        cursor = self._storage._StorageLayer__execute("SELECT COUNT(*) FROM resource_props")
        node_prop_count = cursor.fetchone()[0]

        cursor = self._storage._StorageLayer__execute("SELECT COUNT(*) FROM rel_props")
        edge_prop_count = cursor.fetchone()[0]

        graph_prop_count = self._count_properties()

        return {
            "db_size_bytes": db_size,
            "db_size_mb": db_size / (1024 * 1024),
            "node_count": node_count,
            "edge_count": edge_count,
            "node_property_count": node_prop_count,
            "edge_property_count": edge_prop_count,
            "graph_property_count": graph_prop_count,
            "total_entities": node_count + edge_count,
            "total_properties": node_prop_count + edge_prop_count + graph_prop_count,
        }

    def to_json(self, limit: int = 10) -> dict:
        """Return graph summary as JSON-serializable dictionary

        Shows first 'limit' nodes and edges with all their properties, plus graph metadata.

        Args:
            limit: Maximum number of nodes and edges to include (default: 10)

        Example:
            graph_data = graph.to_json(limit=5)
            print(json.dumps(graph_data, indent=2))
        """
        # Get graph metadata
        metadata = self.props.copy()

        # Get first 'limit' nodes with properties
        nodes = []
        for node in self.nodes().limit(limit):
            node_data = node.to_json()
            node_data["created_at"] = node.timestamp()
            nodes.append(node_data)

        # Get first 'limit' edges with properties
        edges = []
        for edge in self.iter_edges(limit=limit):
            edge_data = edge.to_json()
            edge_data["created_at"] = edge.timestamp()
            edges.append(edge_data)

        # Get total counts
        total_nodes = self.node_count()
        total_edges = self.edge_count()

        return {
            "metadata": metadata,
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "total_nodes": total_nodes,
                "total_edges": total_edges,
                "nodes_shown": len(nodes),
                "edges_shown": len(edges),
            },
        }


class NodeProxy:
    """Lightweight proxy for a node in the graph"""

    def __init__(self, graph: PropertyGraph, node_id: int, node_type: str) -> None:
        self.graph = graph
        self.node_id = node_id
        self.node_type = node_type
        # For error messages
        self.entity_type = "Node"
        self.entity_id = node_id
        self._props = PropertyDict(self)

    @property
    def props(self) -> PropertyDict:
        """Dict-like access to node properties"""
        return self._props

    # Property interface implementation for nodes
    def _get_property(self, key: str) -> Any:
        return self.graph._storage._get_node_property(self.node_id, key)

    def _set_property(self, key: str, value: Any) -> None:
        try:
            self.graph._storage._set_node_property(self.node_id, key, value)
            self.graph._storage.commit()
        except ValueError as e:
            # TypeMapper.to_storage raises ValueError for invalid values like None
            if "None values are not allowed" in str(e):
                raise PropertyValueError(
                    key, value, str(e), self.entity_type, self.entity_id
                ) from e
            raise

    def _delete_property(self, key: str) -> None:
        self.graph._storage._delete_node_property(self.node_id, key)
        self.graph._storage.commit()

    def _has_property(self, key: str) -> bool:
        return self.graph._storage._has_node_property(self.node_id, key)

    def _get_all_properties(self) -> dict:
        return self.graph._storage._get_node_properties(self.node_id)

    def _update_properties(self, props: dict) -> None:
        self.graph._storage._update_node_properties(self.node_id, props)
        self.graph._storage.commit()

    def _clear_properties(self) -> None:
        self.graph._storage._clear_node_properties(self.node_id)
        self.graph._storage.commit()

    def _list_property_keys(self) -> list[str]:
        return self.graph._storage._get_node_property_keys(self.node_id)

    def _count_properties(self) -> int:
        return self.graph._storage._count_node_properties(self.node_id)

    def __repr__(self) -> str:
        return f"Node({self.node_id}, {self.node_type})"

    def timestamp(self) -> float:
        """Get node creation timestamp

        Returns:
            Unix timestamp as float
        """
        return self.graph._storage._get_node_timestamp(self.node_id)

    def to_json(self) -> dict:
        """Return node data as JSON-serializable dictionary

        Returns:
            Dictionary with node_id, node_type, and all properties
        """
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "properties": self.props.copy(),
        }


class EdgeProxy:
    """Lightweight proxy for an edge in the graph"""

    def __init__(
        self, graph: PropertyGraph, edge_id: int, edge_type: str, src_id: int, dst_id: int
    ) -> None:
        self.graph = graph
        self.edge_id = edge_id
        self.edge_type = edge_type
        self.src_id = src_id
        self.dst_id = dst_id
        # For error messages
        self.entity_type = "Edge"
        self.entity_id = edge_id
        self._props = PropertyDict(self)

    @property
    def props(self) -> PropertyDict:
        """Dict-like access to edge properties"""
        return self._props

    # Property interface implementation for edges
    def _get_property(self, key: str) -> Any:
        return self.graph._storage._get_edge_property(self.edge_id, key)

    def _set_property(self, key: str, value: Any) -> None:
        try:
            self.graph._storage._set_edge_property(self.edge_id, key, value)
            self.graph._storage.commit()
        except ValueError as e:
            # TypeMapper.to_storage raises ValueError for invalid values like None
            if "None values are not allowed" in str(e):
                raise PropertyValueError(
                    key, value, str(e), self.entity_type, self.entity_id
                ) from e
            raise

    def _delete_property(self, key: str) -> None:
        self.graph._storage._delete_edge_property(self.edge_id, key)
        self.graph._storage.commit()

    def _has_property(self, key: str) -> bool:
        return self.graph._storage._has_edge_property(self.edge_id, key)

    def _get_all_properties(self) -> dict:
        return self.graph._storage._get_edge_properties(self.edge_id)

    def _update_properties(self, props: dict) -> None:
        self.graph._storage._update_edge_properties(self.edge_id, props)
        self.graph._storage.commit()

    def _clear_properties(self) -> None:
        self.graph._storage._clear_edge_properties(self.edge_id)
        self.graph._storage.commit()

    def _list_property_keys(self) -> list[str]:
        return self.graph._storage._get_edge_property_keys(self.edge_id)

    def _count_properties(self) -> int:
        return self.graph._storage._count_edge_properties(self.edge_id)

    def __repr__(self) -> str:
        return f"Edge({self.src_id} --{self.edge_type}--> {self.dst_id})"

    def timestamp(self) -> float:
        """Get edge creation timestamp

        Returns:
            Unix timestamp as float
        """
        return self.graph._storage._get_edge_timestamp(self.edge_id)

    def to_json(self) -> dict:
        """Return edge data as JSON-serializable dictionary

        Returns:
            Dictionary with edge_id, edge_type, src_id, dst_id, and all properties
        """
        return {
            "edge_id": self.edge_id,
            "edge_type": self.edge_type,
            "src_id": self.src_id,
            "dst_id": self.dst_id,
            "properties": self.props.copy(),
        }


# Convenience alias
Graph = PropertyGraph
