"""
Pytest configuration and fixtures for PropWeaver tests.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from propweaver import PropertyGraph


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def graph(temp_db):
    """Create a PropertyGraph instance with temporary database"""
    graph = PropertyGraph(temp_db)
    yield graph
    graph.close()


@pytest.fixture
def populated_graph(graph):
    """Create a graph with sample data for testing"""
    # Add sample nodes
    alice = graph.add_node("User", name="Alice", age=30, active=True)
    bob = graph.add_node("User", name="Bob", age=25, active=False)
    charlie = graph.add_node("User", name="Charlie", age=35, active=True)
    project = graph.add_node("Project", name="Test Project", status="active")

    # Add sample edges
    friendship1 = graph.add_edge(alice, "FRIENDS", bob, since="2020", strength=0.8)
    friendship2 = graph.add_edge(alice, "FRIENDS", charlie, since="2021", strength=0.9)
    works_on1 = graph.add_edge(alice, "WORKS_ON", project, role="Lead", since="2023")
    works_on2 = graph.add_edge(charlie, "WORKS_ON", project, role="Developer", since="2023")

    return {
        "graph": graph,
        "nodes": {"alice": alice, "bob": bob, "charlie": charlie, "project": project},
        "edges": {
            "friendship1": friendship1,
            "friendship2": friendship2,
            "works_on1": works_on1,
            "works_on2": works_on2,
        },
    }
