"""
Tests for PropWeaver CRUD operations.
"""

from datetime import datetime

import pytest


class TestNodeOperations:
    """Tests for node CRUD operations"""

    def test_node_creation(self, graph):
        """Test node creation with properties"""
        user = graph.add_node("User", name="Alice", age=30, active=True)
        assert user.node_type == "User"
        assert user.props["name"] == "Alice"
        assert user.props["age"] == 30
        assert user.props["active"] == True

    def test_property_updates(self, graph):
        """Test node property updates"""
        user = graph.add_node("User", name="Alice", age=30)
        user.props["age"] = 31
        assert user.props["age"] == 31

    def test_chainable_property_updates(self, graph):
        """Test chainable property updates"""
        user = graph.add_node("User", name="Alice", age=30)
        user.props["name"] = "Alice Smith"
        user.props["verified"] = True
        assert user.props["name"] == "Alice Smith"
        assert user.props["verified"] == True

    def test_get_all_properties(self, graph):
        """Test retrieving node properties individually"""
        user = graph.add_node("User", name="Alice", age=30, active=True)
        assert user.props["name"] == "Alice"
        assert user.props["age"] == 30
        assert user.props["active"] == True


class TestEdgeOperations:
    """Tests for edge CRUD operations"""

    def test_edge_creation(self, graph):
        """Test edge creation with properties"""
        alice = graph.add_node("User", name="Alice")
        project = graph.add_node("Project", name="Web App")
        works_on = graph.add_edge(alice, "WORKS_ON", project, role="Lead", since="2023")

        assert works_on.edge_type == "WORKS_ON"
        assert works_on.src_id == alice.node_id
        assert works_on.dst_id == project.node_id
        assert works_on.props["role"] == "Lead"
        assert works_on.props["since"] == "2023"

    def test_edge_property_updates(self, graph):
        """Test edge property updates"""
        alice = graph.add_node("User", name="Alice")
        bob = graph.add_node("User", name="Bob")
        friendship = graph.add_edge(alice, "FRIENDS", bob, strength=0.5)

        friendship.props["strength"] = 0.8
        assert friendship.props["strength"] == 0.8

    def test_chainable_edge_updates(self, graph):
        """Test chainable edge property updates"""
        alice = graph.add_node("User", name="Alice")
        bob = graph.add_node("User", name="Bob")
        friendship = graph.add_edge(alice, "FRIENDS", bob)

        friendship.props["strength"] = 0.8
        friendship.props["status"] = "active"
        assert friendship.props["strength"] == 0.8
        assert friendship.props["status"] == "active"


class TestGraphMetadata:
    """Tests for graph-level metadata"""

    def test_graph_properties(self, graph):
        """Test graph metadata operations"""
        graph.props["version"] = 1
        graph.props["created_by"] = "test"
        assert graph.props["version"] == 1
        assert graph.props["created_by"] == "test"

    def test_graph_created_at(self, graph):
        """Test that created_at is automatically set"""
        created_at = graph.timestamp()
        assert isinstance(created_at, float)

    def test_schema_version(self, graph):
        """Test that schema_version is available"""
        schema_version = graph.props["schema_version"]
        assert schema_version is not None
        assert isinstance(schema_version, int)


class TestCounts:
    """Tests for counting operations"""

    def test_node_count(self, populated_graph):
        """Test node counting"""
        graph = populated_graph["graph"]
        assert graph.node_count() == 4

    def test_edge_count(self, populated_graph):
        """Test edge counting"""
        graph = populated_graph["graph"]
        assert graph.edge_count() == 4

    def test_count_after_additions(self, graph):
        """Test counts update after adding nodes/edges"""
        initial_nodes = graph.node_count()
        initial_edges = graph.edge_count()

        alice = graph.add_node("User", name="Alice")
        bob = graph.add_node("User", name="Bob")
        friendship = graph.add_edge(alice, "FRIENDS", bob)

        assert graph.node_count() == initial_nodes + 2
        assert graph.edge_count() == initial_edges + 1
