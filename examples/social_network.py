#!/usr/bin/env python3
"""
Social Network Example for PropWeaver

Demonstrates how to model and query a social network with users, friendships,
and finding mutual connections.
"""

import sys
from pathlib import Path

# Add src to Python path for examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from propweaver import PropertyGraph


def main():
    """Social network example with users and friendships"""
    print("=== Social Network Example ===\n")

    with PropertyGraph() as graph:  # Use in-memory for examples
        # Create users with properties
        print("Creating users...")
        alice = graph.add_node("User", name="Alice", age=25, city="San Francisco")
        bob = graph.add_node("User", name="Bob", age=30, city="New York")
        charlie = graph.add_node("User", name="Charlie", age=28, city="San Francisco")
        diana = graph.add_node("User", name="Diana", age=26, city="New York")

        print(f"✅ Created 4 users")

        # Create friendships with properties
        print("\nCreating friendships...")
        friendship1 = graph.add_edge(alice, "FRIENDS", bob, since="2023-01-01", strength=0.8)
        friendship2 = graph.add_edge(alice, "FRIENDS", charlie, since="2022-06-15", strength=0.9)
        friendship3 = graph.add_edge(bob, "FRIENDS", diana, since="2023-03-10", strength=0.7)
        friendship4 = graph.add_edge(charlie, "FRIENDS", diana, since="2022-11-20", strength=0.85)

        print(f"✅ Created 4 friendships")

        # Query examples
        print("\n=== Query Examples ===")

        # Find all users
        all_users = list(graph.nodes("User"))
        print(f"\nTotal users: {len(all_users)}")
        for user in all_users:
            print(f"  - {user.props['name']} (age {user.props['age']}, {user.props['city']})")

        # Find users by city
        sf_users = list(graph.nodes("User", city="San Francisco"))
        print(f"\nUsers in San Francisco: {len(sf_users)}")
        for user in sf_users:
            print(f"  - {user.props['name']}")

        # Find all friendships
        friendships = list(graph.edges("FRIENDS"))
        print(f"\nAll friendships: {len(friendships)}")
        for friendship in friendships:
            # Find the users involved in this friendship
            src_user = next(u for u in all_users if u.node_id == friendship.src_id)
            dst_user = next(u for u in all_users if u.node_id == friendship.dst_id)
            strength = friendship.props["strength"]
            print(f"  - {src_user.props['name']} ↔ {dst_user.props['name']} (strength: {strength})")

        # Find strong friendships (strength >= 0.8) - done manually since filter() expects properties
        strong_friendships = [e for e in graph.edges("FRIENDS") if e.props["strength"] >= 0.8]
        print(f"\nStrong friendships (≥0.8): {len(strong_friendships)}")

        # Set graph metadata
        graph.props.update(
            {
                "network_type": "social",
                "total_users": len(all_users),
                "created_by": "social_network_example",
            }
        )

        # Show property deletion example
        print("\n=== Property Management Examples ===")
        alice.props["temp_score"] = 95  # Add temporary property
        print(f"Alice properties: {len(alice.props)} items")

        del alice.props["temp_score"]  # Delete property
        print(f"After deletion: {len(alice.props)} items")
        print(f"Has temp_score: {'temp_score' in alice.props}")

        print(f"\n✅ Social network example completed!")
        print(
            f"Graph metadata - Network type: {graph.props['network_type']}, Total users: {graph.props['total_users']}"
        )


if __name__ == "__main__":
    main()
