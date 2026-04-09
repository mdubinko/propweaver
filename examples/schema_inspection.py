#!/usr/bin/env python3
"""
Schema Inspection Example

Demonstrates efficient schema discovery using edge_types() and node_types()
methods to analyze graph structure and relationship patterns.
"""

import sys
from pathlib import Path

# Add src to path for running directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from propweaver import PropertyGraph

def main():
    """Demonstrate efficient schema inspection"""

    with PropertyGraph(':memory:') as graph:
        print("📊 PropWeaver Edge/Node Type Listing Demo")
        print("=" * 45)

        # Start with empty graph
        print("\n🔍 Empty graph:")
        print(f"  Node types: {graph.node_types()}")
        print(f"  Edge types: {graph.edge_types()}")

        # Add various nodes and edges
        print("\n🏗️ Building sample graph...")
        user1 = graph.add_node('User', name='Alice', role='Admin')
        user2 = graph.add_node('User', name='Bob', role='User')
        user3 = graph.add_node('User', name='Carol', role='Moderator')

        product1 = graph.add_node('Product', name='Laptop', category='Electronics')
        product2 = graph.add_node('Product', name='Book', category='Education')

        company = graph.add_node('Company', name='TechCorp')
        category = graph.add_node('Category', name='Electronics')

        # Create various relationships
        graph.add_edge(user1, 'FRIENDS', user2, since='2020-01-01')
        graph.add_edge(user2, 'FRIENDS', user3, since='2021-06-15')
        graph.add_edge(user1, 'PURCHASED', product1, date='2023-03-15', price=1200)
        graph.add_edge(user2, 'PURCHASED', product2, date='2023-04-20', price=25)
        graph.add_edge(user1, 'WORKS_FOR', company, position='Engineer', since='2019-05-01')
        graph.add_edge(user3, 'WORKS_FOR', company, position='Designer', since='2020-08-15')
        graph.add_edge(product1, 'BELONGS_TO', category)
        graph.add_edge(user1, 'FOLLOWS', user3, platform='twitter')

        # Show the results
        print(f"\n✅ Graph populated:")
        print(f"  Total nodes: {graph.node_count()}")
        print(f"  Total edges: {graph.edge_count()}")

        node_types = graph.node_types()
        edge_types = graph.edge_types()

        print(f"\n🎯 Node types ({len(node_types)}):")
        for i, node_type in enumerate(node_types, 1):
            count = len(list(graph.nodes(node_type)))
            print(f"  {i}. {node_type}: {count} nodes")

        print(f"\n🎯 Edge types ({len(edge_types)}):")
        for i, edge_type in enumerate(edge_types, 1):
            count = len(list(graph.edges(edge_type)))
            print(f"  {i}. {edge_type}: {count} edges")

        # Show efficiency - these are single SQL queries each
        print(f"\n⚡ Performance: Each type listing requires only one SQL query!")
        print(f"   SQL: SELECT DISTINCT type FROM resource ORDER BY type")
        print(f"   SQL: SELECT DISTINCT type FROM rel ORDER BY type")

        # Show usage patterns
        print(f"\n🔍 Usage patterns:")
        print(f"  Schema validation: 'User' in graph.node_types() = {'User' in node_types}")
        print(f"  Relationship discovery: Found {len(edge_types)} relationship patterns")

        # Demonstrate with filtering
        print(f"\n📈 Relationship analysis:")
        for edge_type in edge_types:
            edges = list(graph.edges(edge_type))
            if edges:
                sample_edge = edges[0]
                print(f"  {edge_type}: {len(edges)} relationships (e.g., Node {sample_edge.src_id} -> Node {sample_edge.dst_id})")

if __name__ == '__main__':
    main()