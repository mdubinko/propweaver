"""Test the edge_types() and node_types() functionality"""

from propweaver import PropertyGraph


def test_list_types():
    """Test listing all edge types and node types efficiently"""

    with PropertyGraph(':memory:') as graph:
        # Initially empty
        assert graph.node_types() == []
        assert graph.edge_types() == []

        # Add some nodes and edges of different types
        user1 = graph.add_node('User', name='Alice')
        user2 = graph.add_node('User', name='Bob')
        product = graph.add_node('Product', name='Widget')
        category = graph.add_node('Category', name='Electronics')

        # Add different edge types
        graph.add_edge(user1, 'FRIENDS', user2)
        graph.add_edge(user1, 'PURCHASED', product)
        graph.add_edge(product, 'BELONGS_TO', category)
        graph.add_edge(user2, 'FRIENDS', user1)  # Same type as first edge

        # Test the new methods
        node_types = graph.node_types()
        edge_types = graph.edge_types()

        # Verify results - should be sorted alphabetically
        expected_node_types = ['Category', 'Product', 'User']
        expected_edge_types = ['BELONGS_TO', 'FRIENDS', 'PURCHASED']

        assert node_types == expected_node_types
        assert edge_types == expected_edge_types


def test_empty_graph():
    """Test that empty graphs return empty type lists"""
    with PropertyGraph(':memory:') as graph:
        assert graph.node_types() == []
        assert graph.edge_types() == []
