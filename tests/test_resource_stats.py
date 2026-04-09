"""
Tests for resource statistics reporting
"""

import tempfile
from pathlib import Path

import pytest

from propweaver import PropertyGraph


def test_resource_stats_in_memory():
    """Test resource stats for in-memory database"""
    with PropertyGraph() as graph:
        # Empty graph
        stats = graph.resource_stats()
        assert stats["db_size_bytes"] == 0
        assert stats["db_size_mb"] == 0
        assert stats["node_count"] == 0
        assert stats["edge_count"] == 0
        assert stats["total_entities"] == 0

        # Add some data
        user1 = graph.add_node("User", name="Alice", age=30)
        user2 = graph.add_node("User", name="Bob", age=25)
        graph.add_edge(user1, "FRIENDS", user2, since="2023-01-01")

        stats = graph.resource_stats()
        assert stats["node_count"] == 2
        assert stats["edge_count"] == 1
        assert stats["total_entities"] == 3
        assert stats["node_property_count"] == 4  # 2 props per node
        assert stats["edge_property_count"] == 1  # 1 prop on edge
        assert stats["total_properties"] > 0


def test_resource_stats_with_file():
    """Test resource stats for file-based database"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        with PropertyGraph(db_path) as graph:
            # Add data
            for i in range(10):
                graph.add_node("User", name=f"User{i}", index=i)

            stats = graph.resource_stats()
            assert stats["db_size_bytes"] > 0, "File should have size"
            assert stats["db_size_mb"] > 0, "File should have size in MB"
            assert stats["node_count"] == 10
            assert stats["node_property_count"] == 20  # 2 props per node

            # Verify file size is reasonable
            assert stats["db_size_bytes"] < 1024 * 1024, "Small graph should be < 1MB"

    finally:
        Path(db_path).unlink(missing_ok=True)


def test_resource_stats_with_properties():
    """Test resource stats accounts for all properties correctly"""
    with PropertyGraph() as graph:
        # Set graph-level properties
        graph.props["version"] = "1.0"
        graph.props["author"] = "test"

        # Add nodes with properties
        user = graph.add_node("User", name="Alice", email="alice@example.com", active=True)
        project = graph.add_node("Project", name="Test", status="active")

        # Add edge with properties
        edge = graph.add_edge(user, "OWNS", project, role="Owner", created="2023-01-01")

        stats = graph.resource_stats()

        # Verify counts
        assert stats["node_count"] == 2
        assert stats["edge_count"] == 1
        assert stats["node_property_count"] == 5  # 3 + 2
        assert stats["edge_property_count"] == 2
        assert stats["graph_property_count"] == 3  # version, author, + schema_version
        assert stats["total_properties"] == 10  # 5 + 2 + 3


def test_resource_stats_monitoring_example():
    """Example of using resource_stats for monitoring and limits"""
    MAX_NODES = 5
    MAX_DB_SIZE_MB = 10

    with PropertyGraph() as graph:
        # Add nodes up to limit
        for i in range(MAX_NODES):
            graph.add_node("User", index=i)

        stats = graph.resource_stats()

        # Check limits
        assert stats["node_count"] <= MAX_NODES, "Node limit exceeded"
        assert stats["db_size_mb"] < MAX_DB_SIZE_MB, "Database size limit exceeded"

        # Example: Enforce limit before adding more
        if stats["node_count"] >= MAX_NODES:
            # Would raise error in production
            print(f"⚠️ Node limit reached: {stats['node_count']}/{MAX_NODES}")


def test_resource_stats_fields():
    """Verify all expected fields are present in resource_stats"""
    with PropertyGraph() as graph:
        graph.add_node("Test", value=1)

        stats = graph.resource_stats()

        # Verify all expected keys exist
        expected_keys = {
            "db_size_bytes",
            "db_size_mb",
            "node_count",
            "edge_count",
            "node_property_count",
            "edge_property_count",
            "graph_property_count",
            "total_entities",
            "total_properties",
        }

        assert set(stats.keys()) == expected_keys, "Missing or extra fields"

        # Verify all values are integers or floats
        for key, value in stats.items():
            assert isinstance(value, (int, float)), f"{key} should be numeric"
