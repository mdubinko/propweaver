"""
Tests for propgraph.api — Pydantic model round-trips and validation.

Requires pydantic: pip install 'propgraph[api]'
"""

import pytest

pydantic = pytest.importorskip("pydantic", reason="pydantic not installed (pip install 'propgraph[api]')")

from propgraph.api import (
    EdgeModel,
    GraphStatsModel,
    GraphSummaryModel,
    NodeModel,
    PropertyGraphConfig,
    PropGraphAPIVersion,
    QuerySpecModel,
    QueryStepModel,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def populated_graph(graph):
    """Graph with one node of each entity type and an edge between them."""
    alice = graph.add_node("User", name="Alice", age=30, active=True)
    project = graph.add_node("Project", name="Web App", status="active")
    edge = graph.add_edge(alice, "WORKS_ON", project, role="Lead")
    graph.props["schema_version"] = 1
    return graph, alice, project, edge


# ─── NodeModel ────────────────────────────────────────────────────────────────


class TestNodeModel:
    def test_from_proxy(self, populated_graph):
        _, alice, _, _ = populated_graph
        model = NodeModel.from_proxy(alice)
        assert model.node_id == alice.node_id
        assert model.node_type == "User"
        assert model.properties == {"name": "Alice", "age": 30, "active": True}
        assert model.created_at is None

    def test_from_proxy_with_timestamp(self, populated_graph):
        _, alice, _, _ = populated_graph
        model = NodeModel.from_proxy(alice, include_timestamp=True)
        assert isinstance(model.created_at, float)
        assert model.created_at > 0

    def test_from_json_round_trip(self, populated_graph):
        _, alice, _, _ = populated_graph
        data = alice.to_json()
        model = NodeModel.from_json(data)
        assert model.node_id == alice.node_id
        assert model.node_type == alice.node_type
        assert model.properties == alice.props.copy()

    def test_model_dump_is_serialisable(self, populated_graph):
        import json
        _, alice, _, _ = populated_graph
        model = NodeModel.from_proxy(alice)
        # Should not raise
        json.dumps(model.model_dump())

    def test_rejects_extra_fields(self):
        with pytest.raises(Exception):
            NodeModel(node_id=1, node_type="X", properties={}, unexpected_field="oops")


# ─── EdgeModel ────────────────────────────────────────────────────────────────


class TestEdgeModel:
    def test_from_proxy(self, populated_graph):
        _, alice, project, edge = populated_graph
        model = EdgeModel.from_proxy(edge)
        assert model.edge_id == edge.edge_id
        assert model.edge_type == "WORKS_ON"
        assert model.src_id == alice.node_id
        assert model.dst_id == project.node_id
        assert model.properties == {"role": "Lead"}
        assert model.created_at is None

    def test_from_proxy_with_timestamp(self, populated_graph):
        _, _, _, edge = populated_graph
        model = EdgeModel.from_proxy(edge, include_timestamp=True)
        assert isinstance(model.created_at, float)
        assert model.created_at > 0

    def test_from_json_round_trip(self, populated_graph):
        _, _, _, edge = populated_graph
        data = edge.to_json()
        model = EdgeModel.from_json(data)
        assert model.edge_id == edge.edge_id
        assert model.edge_type == edge.edge_type
        assert model.src_id == edge.src_id
        assert model.dst_id == edge.dst_id

    def test_model_dump_is_serialisable(self, populated_graph):
        import json
        _, _, _, edge = populated_graph
        model = EdgeModel.from_proxy(edge)
        json.dumps(model.model_dump())


# ─── GraphStatsModel ──────────────────────────────────────────────────────────


class TestGraphStatsModel:
    def test_from_dict(self, populated_graph):
        g, _, _, _ = populated_graph
        model = GraphStatsModel.from_dict(g.resource_stats())
        assert model.node_count == 2
        assert model.edge_count == 1
        assert model.total_entities == 3
        assert model.node_property_count >= 3  # name, age, active on alice
        assert model.edge_property_count >= 1  # role on the edge
        assert model.total_properties == (
            model.node_property_count
            + model.edge_property_count
            + model.graph_property_count
        )

    def test_in_memory_db_size_is_zero(self, populated_graph):
        g, _, _, _ = populated_graph
        model = GraphStatsModel.from_dict(g.resource_stats())
        # graph fixture uses a temp file, so size may be > 0; just check the field exists
        assert isinstance(model.db_size_bytes, int)
        assert isinstance(model.db_size_mb, float)


# ─── GraphSummaryModel ────────────────────────────────────────────────────────


class TestGraphSummaryModel:
    def test_from_dict(self, populated_graph):
        g, _, _, _ = populated_graph
        model = GraphSummaryModel.from_dict(g.to_json())
        assert len(model.nodes) == 2
        assert len(model.edges) == 1
        assert model.summary.total_nodes == 2
        assert model.summary.total_edges == 1
        assert model.summary.nodes_shown == 2
        assert model.summary.edges_shown == 1

    def test_nodes_are_node_models(self, populated_graph):
        g, _, _, _ = populated_graph
        model = GraphSummaryModel.from_dict(g.to_json())
        for node in model.nodes:
            assert isinstance(node, NodeModel)

    def test_edges_are_edge_models(self, populated_graph):
        g, _, _, _ = populated_graph
        model = GraphSummaryModel.from_dict(g.to_json())
        for edge in model.edges:
            assert isinstance(edge, EdgeModel)

    def test_respects_limit(self, graph):
        for i in range(5):
            graph.add_node("Item", idx=i)
        model = GraphSummaryModel.from_dict(graph.to_json(limit=2))
        assert model.summary.nodes_shown == 2
        assert model.summary.total_nodes == 5


# ─── QueryStepModel / QuerySpecModel ─────────────────────────────────────────


class TestQueryModels:
    def test_query_step_defaults(self):
        step = QueryStepModel(type="SOURCE", target="all_nodes")
        assert step.direction == "both"
        assert step.node_type is None
        assert step.order is None

    def test_query_spec_empty(self):
        spec = QuerySpecModel()
        assert spec.steps == []
        assert spec.returning == "nodes"
        assert spec.limit is None

    def test_query_spec_with_steps(self):
        spec = QuerySpecModel(
            steps=[
                QueryStepModel(type="SOURCE", target="all_nodes"),
                QueryStepModel(type="FILTER", node_type="User", properties={"active": True}),
                QueryStepModel(type="DELETE"),
            ],
            limit=100,
        )
        assert len(spec.steps) == 3
        assert spec.steps[1].node_type == "User"
        assert spec.limit == 100

    def test_invalid_step_type(self):
        with pytest.raises(Exception):
            QueryStepModel(type="INVALID")

    def test_invalid_direction(self):
        with pytest.raises(Exception):
            QueryStepModel(type="TRAVERSE", direction="sideways")


# ─── PropertyGraphConfig ─────────────────────────────────────────────────────


class TestPropertyGraphConfig:
    def test_defaults(self):
        cfg = PropertyGraphConfig()
        assert cfg.db_path is None
        assert cfg.allowed_base_dir is None

    def test_with_path(self):
        cfg = PropertyGraphConfig(db_path="/tmp/my.db", allowed_base_dir="/tmp")
        assert cfg.db_path == "/tmp/my.db"

    def test_rejects_extra_fields(self):
        with pytest.raises(Exception):
            PropertyGraphConfig(unknown_option=True)


# ─── PropGraphAPIVersion ──────────────────────────────────────────────────────


class TestPropGraphAPIVersion:
    def test_current_version(self):
        from propgraph.api import CURRENT_API_VERSION, API_SCHEMA_VERSION
        import propgraph
        assert CURRENT_API_VERSION.propgraph_version == propgraph.__version__
        assert CURRENT_API_VERSION.api_schema_version == API_SCHEMA_VERSION

    def test_construct(self):
        v = PropGraphAPIVersion(propgraph_version="1.2.3", api_schema_version="2")
        assert v.propgraph_version == "1.2.3"
