#!/usr/bin/env python3

"""
Comprehensive tests for PropWeaver functionality.

Tests all core functionality including:
- Basic CRUD operations
- Query building and execution
- Bulk mutation operations
- Transaction support
"""

import os
import sys
import tempfile
import warnings
from datetime import datetime
from pathlib import Path

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from propweaver import PropertyGraph
    from propweaver.logger import configure_test_output
    from propweaver.query import EdgeIterator, NodeIterator, QuerySpec, QueryStep
except ImportError as e:
    print(f"Import error: {e}")
    print("Testing what's available in propweaver...")
    try:
        import propweaver

        print(f"Available: {dir(propweaver)}")
    except:
        pass
    sys.exit(1)


def test_query_spec_construction():
    """Test basic QuerySpec construction"""
    import logging

    logger = logging.getLogger("propweaver.tests")

    logger.info("Testing QuerySpec construction...")

    # Test empty QuerySpec
    spec = QuerySpec()
    assert spec.steps == []
    assert spec.returning == "nodes"
    assert spec.limit is None
    logger.info("✅ Empty QuerySpec works")

    # Test QuerySpec with steps
    steps = [
        QueryStep(type="SOURCE", target="all_nodes"),
        QueryStep(type="FILTER", node_type="User"),
    ]
    spec = QuerySpec(steps=steps, returning="nodes", limit=10)
    assert len(spec.steps) == 2
    assert spec.steps[0].type == "SOURCE"
    assert spec.returning == "nodes"
    assert spec.limit == 10
    logger.info("✅ QuerySpec with steps works")

    logger.summary("✅ QuerySpec construction")


def test_query_step_construction():
    """Test QueryStep construction"""
    print("Testing QueryStep construction...")

    # SOURCE step
    step = QueryStep(type="SOURCE", target="all_nodes")
    assert step.type == "SOURCE"
    assert step.target == "all_nodes"
    print("✅ SOURCE QueryStep works")

    # FILTER step
    step = QueryStep(type="FILTER", node_type="User", properties={"active": True})
    assert step.type == "FILTER"
    assert step.node_type == "User"
    assert step.properties == {"active": True}
    print("✅ FILTER QueryStep works")

    # TRAVERSE step
    step = QueryStep(type="TRAVERSE", edge_type="FRIENDS", direction="out")
    assert step.type == "TRAVERSE"
    assert step.edge_type == "FRIENDS"
    assert step.direction == "out"
    print("✅ TRAVERSE QueryStep works")


def test_node_iterator_query_building():
    """Test NodeIterator query building"""
    print("Testing NodeIterator query building...")

    # Create temporary graph
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        graph = PropertyGraph(db_path)

        # Test basic nodes() call
        iterator = graph.nodes()
        assert len(iterator.query_spec.steps) == 1
        assert iterator.query_spec.steps[0].type == "SOURCE"
        print("✅ Basic nodes() creates SOURCE step")

        # Test nodes with type
        iterator = graph.nodes("User")
        assert len(iterator.query_spec.steps) == 2
        assert iterator.query_spec.steps[1].type == "FILTER"
        assert iterator.query_spec.steps[1].node_type == "User"
        print("✅ nodes(type) adds FILTER step")

        # Test nodes with properties
        iterator = graph.nodes(active=True, department="Engineering")
        assert len(iterator.query_spec.steps) == 2
        assert iterator.query_spec.steps[1].properties == {
            "active": True,
            "department": "Engineering",
        }
        print("✅ nodes(**props) adds FILTER step")

        # Test limit
        iterator = graph.nodes().limit(10)
        assert iterator.query_spec.limit == 10
        print("✅ limit() works")

    finally:
        graph.close()
        os.unlink(db_path)


def test_current_read_functionality():
    """Test that current read functionality works"""
    print("Testing current read functionality...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        graph = PropertyGraph(db_path)

        # Add test data
        alice = graph.add_node("User", name="Alice", active=True)
        bob = graph.add_node("User", name="Bob", active=False)
        proj = graph.add_node("Project", name="Test")

        # Test iteration
        all_nodes = list(graph.nodes())
        assert len(all_nodes) == 3
        print("✅ Basic iteration works")

        # Test type filtering
        users = list(graph.nodes("User"))
        assert len(users) == 2
        print("✅ Type filtering works")

        # Test property filtering
        active_users = list(graph.nodes("User", active=True))
        assert len(active_users) == 1
        print("✅ Property filtering works")

        # Test limit
        limited = list(graph.nodes().limit(2))
        assert len(limited) == 2
        print("✅ Limit works")

    finally:
        graph.close()
        os.unlink(db_path)


def test_delete_functionality():
    """Test the delete functionality"""
    print("Testing delete functionality...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        graph = PropertyGraph(db_path)

        # Add test data
        temp1 = graph.add_node("TempUser", name="temp1")
        temp2 = graph.add_node("TempUser", name="temp2")
        user1 = graph.add_node("User", name="user1", active=True)
        user2 = graph.add_node("User", name="user2", active=False)

        initial_count = graph.node_count()
        assert initial_count == 4
        print("✅ Test data created")

        # Test delete by type
        deleted_count = graph.nodes("TempUser").delete().execute()
        assert deleted_count == 2
        assert graph.node_count() == 2
        print("✅ Delete by type works")

        # Verify TempUser nodes are gone
        remaining_temp = list(graph.nodes("TempUser"))
        assert len(remaining_temp) == 0
        print("✅ TempUser nodes completely removed")

        # Test delete by property
        deleted_count = graph.nodes("User", active=False).delete().execute()
        assert deleted_count == 1
        assert graph.node_count() == 1
        print("✅ Delete by property works")

        # Verify only active user remains
        remaining_users = list(graph.nodes("User"))
        assert len(remaining_users) == 1
        assert remaining_users[0].props["active"] == True
        print("✅ Property-based deletion works correctly")

    finally:
        graph.close()
        os.unlink(db_path)


def test_delete_transaction_rollback():
    """Test that delete transactions roll back on errors"""
    print("Testing transaction rollback...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        graph = PropertyGraph(db_path)

        # Add test data
        graph.add_node("User", name="user1")
        graph.add_node("User", name="user2")
        initial_count = graph.node_count()

        # Test transaction rollback by causing an error during delete
        try:
            with graph._storage.transaction():
                # Delete first user
                graph._storage._delete_node(1)
                # Simulate error
                raise Exception("Simulated error")
        except Exception as e:
            if "Simulated error" not in str(e):
                raise

        # Count should be unchanged due to rollback
        assert graph.node_count() == initial_count
        print("✅ Transaction rollback works")

    finally:
        graph.close()
        os.unlink(db_path)


def test_edge_functionality():
    """Test edge reading and deletion functionality"""
    print("Testing edge functionality...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        graph = PropertyGraph(db_path)

        # Add test nodes
        alice = graph.add_node("User", name="Alice")
        bob = graph.add_node("User", name="Bob")
        charlie = graph.add_node("User", name="Charlie")

        # Add test edges
        friendship1 = graph.add_edge(alice, "friends", bob, active=True, since="2023")
        friendship2 = graph.add_edge(alice, "friends", charlie, active=False, since="2022")
        temp_edge1 = graph.add_edge(bob, "temp_relation", charlie, temp=True)
        temp_edge2 = graph.add_edge(charlie, "temp_relation", alice, temp=True)

        initial_edge_count = graph.edge_count()
        assert initial_edge_count == 4
        print("✅ Test edge data created")

        # Test edge iteration
        all_edges = list(graph.edges())
        assert len(all_edges) == 4
        print("✅ Basic edge iteration works")

        # Test edge filtering by type
        friendships = list(graph.edges("friends"))
        assert len(friendships) == 2
        print("✅ Edge type filtering works")

        # Test edge filtering by properties
        active_friendships = list(graph.edges("friends", active=True))
        assert len(active_friendships) == 1
        print("✅ Edge property filtering works")

        # Test edge deletion by type
        deleted_count = graph.edges("temp_relation").delete().execute()
        assert deleted_count == 2
        assert graph.edge_count() == 2
        print("✅ Edge deletion by type works")

        # Verify temp edges are gone
        remaining_temp = list(graph.edges("temp_relation"))
        assert len(remaining_temp) == 0
        print("✅ Temp edges completely removed")

        # Test edge deletion by property
        deleted_count = graph.edges("friends", active=False).delete().execute()
        assert deleted_count == 1
        assert graph.edge_count() == 1
        print("✅ Edge deletion by property works")

        # Verify only active friendship remains
        remaining_friendships = list(graph.edges("friends"))
        assert len(remaining_friendships) == 1
        assert remaining_friendships[0].props["active"] == True
        print("✅ Property-based edge deletion works correctly")

    finally:
        graph.close()
        os.unlink(db_path)


def test_edge_transaction_rollback():
    """Test that edge deletion transactions roll back on errors"""
    print("Testing edge transaction rollback...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        graph = PropertyGraph(db_path)

        # Add test data
        alice = graph.add_node("User", name="Alice")
        bob = graph.add_node("User", name="Bob")
        edge = graph.add_edge(alice, "friends", bob)
        initial_count = graph.edge_count()

        # Test transaction rollback by causing an error during delete
        try:
            with graph._storage.transaction():
                # Delete edge
                graph._storage._delete_edge(edge.edge_id)
                # Simulate error
                raise Exception("Simulated error")
        except Exception as e:
            if "Simulated error" not in str(e):
                raise

        # Count should be unchanged due to rollback
        assert graph.edge_count() == initial_count
        print("✅ Edge transaction rollback works")

    finally:
        graph.close()
        os.unlink(db_path)


def test_basic_crud_operations():
    """Test basic create, read, update operations"""
    print("Testing basic CRUD operations...")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        graph = PropertyGraph(db_path)

        # Test node creation
        user = graph.add_node("User", name="Alice", age=30, active=True)
        assert user.node_type == "User"
        assert user.props["name"] == "Alice"
        assert user.props["age"] == 30
        assert user.props["active"] == True
        print("✅ Node creation and property retrieval works")

        # Test property updates
        user.props["age"] = 31
        assert user.props["age"] == 31
        print("✅ Property updates work")

        # Test chainable property updates
        user.props["name"] = "Alice Smith"
        user.props["verified"] = True
        assert user.props["name"] == "Alice Smith"
        assert user.props["verified"] == True
        print("✅ Chainable property updates work")

        # Test edge creation
        project = graph.add_node("Project", name="Web App")
        works_on = graph.add_edge(user, "WORKS_ON", project, role="Lead", since="2023")
        assert works_on.edge_type == "WORKS_ON"
        assert works_on.props["role"] == "Lead"
        print("✅ Edge creation and properties work")

        # Test graph metadata
        graph.props["version"] = 1
        graph.props["created_by"] = "test"
        assert graph.props["version"] == 1
        assert graph.props["created_by"] == "test"
        print("✅ Graph metadata works")

    finally:
        graph.close()
        os.unlink(db_path)


def main():
    """Run all tests"""
    import logging

    # Check for --brief flag
    brief_mode = "--brief" in sys.argv

    # Configure logging based on mode
    configure_test_output(brief=brief_mode, suppress_warnings=True)
    logger = logging.getLogger("propweaver.tests")

    if brief_mode:
        logger.summary("=== PropWeaver Tests ===")
    else:
        logger.info("=== PropWeaver Comprehensive Test Suite ===")
        logger.info("")

    try:
        if not brief_mode:
            logger.info("=== Phase 0: Query System Tests ===")
            logger.info("")

        test_query_spec_construction()
        if not brief_mode:
            logger.info("")

        test_query_step_construction()
        print()

        test_node_iterator_query_building()
        print()

        test_current_read_functionality()
        print()

        print("=== Phase 1: Basic CRUD Tests ===\n")

        test_basic_crud_operations()
        print()

        print("=== Phase 2: Node Deletion Tests ===\n")

        test_delete_functionality()
        print()

        test_delete_transaction_rollback()
        print()

        print("=== Phase 3: Edge Operations Tests ===\n")

        test_edge_functionality()
        print()

        test_edge_transaction_rollback()
        print()

        logger.summary("🎉 All tests PASSED!")
        if not brief_mode:
            logger.info("✅ PropWeaver library is fully functional!")
            logger.info("✅ Ready for use as standalone library!")

    except Exception as e:
        logger.summary(f"❌ Test failed: {e}")
        if not brief_mode:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
