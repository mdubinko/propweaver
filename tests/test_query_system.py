"""
Tests for PropWeaver query system functionality.
"""

import pytest

from propweaver.query import EdgeIterator, NodeIterator, QuerySpec, QueryStep


class TestQuerySpec:
    """Tests for QuerySpec construction"""

    def test_empty_query_spec(self):
        """Test empty QuerySpec construction"""
        spec = QuerySpec()
        assert spec.steps == []
        assert spec.returning == "nodes"
        assert spec.limit is None

    def test_query_spec_with_steps(self):
        """Test QuerySpec with predefined steps"""
        steps = [
            QueryStep(type="SOURCE", target="all_nodes"),
            QueryStep(type="FILTER", node_type="User"),
        ]
        spec = QuerySpec(steps=steps, returning="nodes", limit=10)
        assert len(spec.steps) == 2
        assert spec.steps[0].type == "SOURCE"
        assert spec.returning == "nodes"
        assert spec.limit == 10


class TestQueryStep:
    """Tests for QueryStep construction"""

    def test_source_step(self):
        """Test SOURCE QueryStep creation"""
        step = QueryStep(type="SOURCE", target="all_nodes")
        assert step.type == "SOURCE"
        assert step.target == "all_nodes"

    def test_filter_step(self):
        """Test FILTER QueryStep creation"""
        step = QueryStep(type="FILTER", node_type="User", properties={"active": True})
        assert step.type == "FILTER"
        assert step.node_type == "User"
        assert step.properties == {"active": True}

    def test_traverse_step(self):
        """Test TRAVERSE QueryStep creation"""
        step = QueryStep(type="TRAVERSE", edge_type="FRIENDS", direction="out")
        assert step.type == "TRAVERSE"
        assert step.edge_type == "FRIENDS"
        assert step.direction == "out"


class TestNodeIterator:
    """Tests for NodeIterator query building"""

    def test_basic_nodes_query(self, graph):
        """Test basic nodes() call creates SOURCE step"""
        iterator = graph.nodes()
        assert len(iterator.query_spec.steps) == 1
        assert iterator.query_spec.steps[0].type == "SOURCE"

    def test_nodes_with_type(self, graph):
        """Test nodes(type) adds FILTER step"""
        iterator = graph.nodes("User")
        assert len(iterator.query_spec.steps) == 2
        assert iterator.query_spec.steps[1].type == "FILTER"
        assert iterator.query_spec.steps[1].node_type == "User"

    def test_nodes_with_properties(self, graph):
        """Test nodes(**props) adds FILTER step"""
        iterator = graph.nodes(active=True, department="Engineering")
        assert len(iterator.query_spec.steps) == 2
        assert iterator.query_spec.steps[1].properties == {
            "active": True,
            "department": "Engineering",
        }

    def test_limit_query(self, graph):
        """Test limit() sets query limit"""
        iterator = graph.nodes().limit(10)
        assert iterator.query_spec.limit == 10


class TestQueryExecution:
    """Tests for query execution"""

    def test_basic_iteration(self, populated_graph):
        """Test basic node iteration works"""
        graph = populated_graph["graph"]
        all_nodes = list(graph.nodes())
        assert len(all_nodes) == 4

    def test_type_filtering(self, populated_graph):
        """Test node type filtering"""
        graph = populated_graph["graph"]
        users = list(graph.nodes("User"))
        assert len(users) == 3

        projects = list(graph.nodes("Project"))
        assert len(projects) == 1

    def test_property_filtering(self, populated_graph):
        """Test property-based filtering"""
        graph = populated_graph["graph"]
        active_users = list(graph.nodes("User", active=True))
        assert len(active_users) == 2

        inactive_users = list(graph.nodes("User", active=False))
        assert len(inactive_users) == 1

    def test_limit_functionality(self, populated_graph):
        """Test query limit functionality"""
        graph = populated_graph["graph"]
        limited = list(graph.nodes().limit(2))
        assert len(limited) == 2
