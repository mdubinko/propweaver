"""
PropWeaver Public API Definition

Pydantic models describing the complete public PropWeaver API. Intended for use
by downstream projects to:

- Know the exact shape of data returned by PropWeaver operations
- Validate PropWeaver output against expected types
- Detect breaking API changes across versions

Usage in consuming projects::

    from propweaver import PropertyGraph
    from propweaver.api import NodeModel, EdgeModel, GraphStatsModel

    with PropertyGraph("my_graph.db") as graph:
        node = graph.add_node("User", name="Alice", age=30)
        model = NodeModel.from_proxy(node)  # validated Pydantic model
        print(model.model_dump())

Requires pydantic v2::

    pip install "propweaver[api]"
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# ─── Property Value Types ─────────────────────────────────────────────────────

#: All Python types that may appear as property values on nodes, edges, or graphs.
PropertyValue = Union[str, int, float, bool, datetime, date, list[Any], dict[str, Any]]

#: A dict mapping property names to their values.
PropertyDict = dict[str, PropertyValue]

#: Storage type tags used internally by TypeMapper.
StorageType = Literal["str", "int", "float", "bool", "datetime", "date", "json"]


# ─── Core Entity Models ───────────────────────────────────────────────────────


class NodeModel(BaseModel):
    """Validated representation of a PropWeaver node.

    Mirrors the data returned by :class:`~propweaver.NodeProxy`.
    """

    model_config = ConfigDict(extra="forbid")

    node_id: int = Field(description="Unique integer ID assigned by the database")
    node_type: str = Field(description="Type label (e.g. 'User', 'Product')")
    properties: PropertyDict = Field(default_factory=dict, description="All stored properties")
    created_at: Optional[float] = Field(
        default=None, description="Unix timestamp of creation (from NodeProxy.timestamp())"
    )

    @classmethod
    def from_proxy(cls, proxy: Any, include_timestamp: bool = False) -> "NodeModel":
        """Build a NodeModel from a live :class:`~propweaver.NodeProxy`.

        Args:
            proxy: A ``NodeProxy`` instance returned by the graph.
            include_timestamp: When True, fetches the creation timestamp
                (extra DB round-trip).

        Returns:
            A validated ``NodeModel``.
        """
        return cls(
            node_id=proxy.node_id,
            node_type=proxy.node_type,
            properties=proxy.props.copy(),
            created_at=proxy.timestamp() if include_timestamp else None,
        )

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "NodeModel":
        """Build a NodeModel from the dict returned by ``NodeProxy.to_json()``.

        Args:
            data: Dict with keys ``node_id``, ``node_type``, ``properties``,
                and optionally ``created_at``.

        Returns:
            A validated ``NodeModel``.
        """
        return cls(**data)


class EdgeModel(BaseModel):
    """Validated representation of a PropWeaver edge.

    Mirrors the data returned by :class:`~propweaver.EdgeProxy`.
    """

    model_config = ConfigDict(extra="forbid")

    edge_id: int = Field(description="Unique integer ID assigned by the database")
    edge_type: str = Field(description="Relationship type label (e.g. 'WORKS_ON', 'FRIENDS')")
    src_id: int = Field(description="ID of the source node")
    dst_id: int = Field(description="ID of the destination node")
    properties: PropertyDict = Field(default_factory=dict, description="All stored properties")
    created_at: Optional[float] = Field(
        default=None, description="Unix timestamp of creation (from EdgeProxy.timestamp())"
    )

    @classmethod
    def from_proxy(cls, proxy: Any, include_timestamp: bool = False) -> "EdgeModel":
        """Build an EdgeModel from a live :class:`~propweaver.EdgeProxy`.

        Args:
            proxy: An ``EdgeProxy`` instance returned by the graph.
            include_timestamp: When True, fetches the creation timestamp
                (extra DB round-trip).

        Returns:
            A validated ``EdgeModel``.
        """
        return cls(
            edge_id=proxy.edge_id,
            edge_type=proxy.edge_type,
            src_id=proxy.src_id,
            dst_id=proxy.dst_id,
            properties=proxy.props.copy(),
            created_at=proxy.timestamp() if include_timestamp else None,
        )

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "EdgeModel":
        """Build an EdgeModel from the dict returned by ``EdgeProxy.to_json()``.

        Args:
            data: Dict with keys ``edge_id``, ``edge_type``, ``src_id``,
                ``dst_id``, ``properties``, and optionally ``created_at``.

        Returns:
            A validated ``EdgeModel``.
        """
        return cls(**data)


# ─── Graph-Level Models ───────────────────────────────────────────────────────


class GraphStatsModel(BaseModel):
    """Resource usage statistics returned by ``PropertyGraph.resource_stats()``.

    All counts reflect the state at the time of the call.
    """

    model_config = ConfigDict(extra="forbid")

    db_size_bytes: int = Field(description="Database file size in bytes (0 for in-memory graphs)")
    db_size_mb: float = Field(description="Database file size in megabytes (0 for in-memory graphs)")
    node_count: int = Field(description="Total number of nodes")
    edge_count: int = Field(description="Total number of edges")
    node_property_count: int = Field(description="Total properties stored across all nodes")
    edge_property_count: int = Field(description="Total properties stored across all edges")
    graph_property_count: int = Field(description="Number of graph-level metadata properties")
    total_entities: int = Field(description="Sum of node_count and edge_count")
    total_properties: int = Field(
        description="Sum of node, edge, and graph property counts"
    )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphStatsModel":
        """Build from the dict returned by ``PropertyGraph.resource_stats()``."""
        return cls(**data)


class GraphSummaryStatsModel(BaseModel):
    """Pagination summary embedded in ``GraphSummaryModel``."""

    model_config = ConfigDict(extra="forbid")

    total_nodes: int = Field(description="Total nodes in the graph")
    total_edges: int = Field(description="Total edges in the graph")
    nodes_shown: int = Field(description="Number of nodes included in this summary")
    edges_shown: int = Field(description="Number of edges included in this summary")


class GraphSummaryModel(BaseModel):
    """Full graph summary returned by ``PropertyGraph.to_json()``.

    Contains graph metadata, a sample of nodes and edges, and totals.
    """

    model_config = ConfigDict(extra="forbid")

    metadata: PropertyDict = Field(description="Graph-level metadata properties")
    nodes: list[NodeModel] = Field(description="Sample of nodes (up to the requested limit)")
    edges: list[EdgeModel] = Field(description="Sample of edges (up to the requested limit)")
    summary: GraphSummaryStatsModel = Field(description="Totals and pagination info")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphSummaryModel":
        """Build from the dict returned by ``PropertyGraph.to_json()``.

        Nodes and edges are automatically parsed into their respective models.
        """
        return cls(
            metadata=data["metadata"],
            nodes=[NodeModel.from_json(n) for n in data["nodes"]],
            edges=[EdgeModel.from_json(e) for e in data["edges"]],
            summary=GraphSummaryStatsModel(**data["summary"]),
        )


# ─── Query Spec Models ────────────────────────────────────────────────────────


class QueryStepModel(BaseModel):
    """Validated representation of a single :class:`~propweaver.QueryStep`.

    Mirrors ``QueryStep`` (a ``dataclass``) with full Pydantic validation.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["SOURCE", "FILTER", "TRAVERSE", "ORDER", "DELETE"] = Field(
        description="Operation type"
    )
    target: Optional[str] = Field(
        default=None,
        description="For SOURCE steps: 'all_nodes' or 'all_edges'",
    )
    node_type: Optional[str] = Field(
        default=None,
        description="For FILTER steps: restrict to this node type",
    )
    edge_type: Optional[str] = Field(
        default=None,
        description="For FILTER/TRAVERSE steps: restrict to this edge type",
    )
    properties: Optional[dict[str, Any]] = Field(
        default=None,
        description="For FILTER steps: property equality filters",
    )
    direction: Literal["out", "in", "both"] = Field(
        default="both",
        description="For TRAVERSE steps: traversal direction",
    )
    field: Optional[str] = Field(
        default=None,
        description="For ORDER steps: field name to sort by",
    )
    order: Optional[Literal["asc", "desc"]] = Field(
        default=None,
        description="For ORDER steps: sort direction",
    )


class QuerySpecModel(BaseModel):
    """Validated representation of a :class:`~propweaver.QuerySpec`.

    Mirrors ``QuerySpec`` (a ``dataclass``) with full Pydantic validation.
    """

    model_config = ConfigDict(extra="forbid")

    steps: list[QueryStepModel] = Field(
        default_factory=list, description="Ordered sequence of query steps"
    )
    returning: Literal["nodes", "edges", "target_nodes", "source_nodes"] = Field(
        default="nodes",
        description=(
            "What entity type to return: "
            "'nodes' from node queries, 'edges' from edge queries, "
            "'target_nodes' after outgoing traversal, 'source_nodes' after incoming traversal"
        ),
    )
    limit: Optional[int] = Field(
        default=None, description="Maximum number of results to return"
    )


# ─── Constructor Config ───────────────────────────────────────────────────────


class PropertyGraphConfig(BaseModel):
    """Parameters accepted by the :class:`~propweaver.PropertyGraph` constructor.

    Use to validate configuration before opening a graph, or to document
    graph instantiation in consuming projects.
    """

    model_config = ConfigDict(extra="forbid")

    db_path: Optional[str] = Field(
        default=None,
        description=(
            "Path to the SQLite database file. "
            "None = in-memory (default), '' = auto-deleted temp file, "
            "'/path/to/file.db' = persistent file"
        ),
    )
    allowed_base_dir: Optional[str] = Field(
        default=None,
        description=(
            "Optional directory restriction for db_path. "
            "When set, db_path must resolve inside this directory. "
            "Raises ValueError for path traversal or out-of-bounds paths."
        ),
    )


# ─── API Version Manifest ─────────────────────────────────────────────────────


class PropWeaverAPIVersion(BaseModel):
    """Version metadata for the PropWeaver public API.

    Embed this in downstream projects to record which API version was
    targeted when the integration was written, enabling change detection.
    """

    model_config = ConfigDict(extra="forbid")

    propweaver_version: str = Field(
        description="propweaver package version string (e.g. '0.2.1')"
    )
    api_schema_version: str = Field(
        default="1",
        description="Version of this api.py schema module, incremented on breaking changes",
    )


#: Current API schema version — bump when making breaking changes to this module.
API_SCHEMA_VERSION = "1"

#: Convenience constant for constructing :class:`PropWeaverAPIVersion` records.
CURRENT_API_VERSION = PropWeaverAPIVersion(
    propweaver_version="0.2.1",
    api_schema_version=API_SCHEMA_VERSION,
)
