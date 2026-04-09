#!/usr/bin/env python3
"""
Resource Monitoring Example

Demonstrates how to use resource_stats() to monitor database
size and entity counts, useful for enforcing limits in production.
"""

from propweaver import PropertyGraph


def format_bytes(bytes_val):
    """Format bytes as human-readable string"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} TB"


def main():
    print("=== Resource Monitoring Example ===\n")

    with PropertyGraph() as graph:
        # Empty graph stats
        print("📊 Empty Graph:")
        stats = graph.resource_stats()
        print(f"  Nodes: {stats['node_count']}")
        print(f"  Edges: {stats['edge_count']}")
        print(f"  Total properties: {stats['total_properties']}")
        print(f"  DB size: {format_bytes(stats['db_size_bytes'])}")
        print()

        # Add some data
        print("➕ Adding 100 users with properties...")
        for i in range(100):
            graph.add_node("User", name=f"User{i}", index=i, active=i % 2 == 0)

        # Add relationships
        print("➕ Adding 50 friendships...")
        users = list(graph.nodes("User").limit(100))
        for i in range(50):
            graph.add_edge(users[i], "FRIENDS", users[i + 1], strength=0.5 + i * 0.01)

        # Check stats after adding data
        print("\n📊 After Adding Data:")
        stats = graph.resource_stats()
        print(f"  Nodes: {stats['node_count']}")
        print(f"  Edges: {stats['edge_count']}")
        print(f"  Total entities: {stats['total_entities']}")
        print(f"  Node properties: {stats['node_property_count']}")
        print(f"  Edge properties: {stats['edge_property_count']}")
        print(f"  Total properties: {stats['total_properties']}")
        print(f"  DB size: {format_bytes(stats['db_size_bytes'])}")
        print()

        # Example: Enforce limits
        MAX_NODES = 200
        MAX_EDGES = 100
        MAX_DB_SIZE_MB = 10

        print("🔍 Checking Resource Limits:")
        print(f"  Max nodes: {MAX_NODES} (current: {stats['node_count']}) ", end="")
        if stats["node_count"] < MAX_NODES:
            print("✅")
        else:
            print("❌ LIMIT EXCEEDED")

        print(f"  Max edges: {MAX_EDGES} (current: {stats['edge_count']}) ", end="")
        if stats["edge_count"] < MAX_EDGES:
            print("✅")
        else:
            print("❌ LIMIT EXCEEDED")

        print(
            f"  Max DB size: {MAX_DB_SIZE_MB}MB (current: {stats['db_size_mb']:.2f}MB) ",
            end="",
        )
        if stats["db_size_mb"] < MAX_DB_SIZE_MB:
            print("✅")
        else:
            print("❌ LIMIT EXCEEDED")

        print()

        # Calculate efficiency metrics
        if stats["total_entities"] > 0:
            avg_props_per_entity = stats["total_properties"] / stats["total_entities"]
            print("📈 Efficiency Metrics:")
            print(f"  Average properties per entity: {avg_props_per_entity:.2f}")

            if stats["db_size_bytes"] > 0:
                bytes_per_entity = stats["db_size_bytes"] / stats["total_entities"]
                print(f"  Bytes per entity: {bytes_per_entity:.0f}")
                bytes_per_property = stats["db_size_bytes"] / stats["total_properties"]
                print(f"  Bytes per property: {bytes_per_property:.0f}")

        print("\n✅ Resource monitoring complete!")


if __name__ == "__main__":
    main()
