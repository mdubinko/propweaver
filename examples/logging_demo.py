#!/usr/bin/env python3
"""Test the new logging functionality"""

import logging

from propweaver import PropertyGraph
from propweaver.logger import SUMMARY

# Test different logging levels
print("=== Testing PropWeaver Logging ===")

print("\n1. Testing with DEBUG level (shows SQL):")
with PropertyGraph() as graph:
    graph.set_log_level(logging.DEBUG)
    user = graph.add_node("User", name="Alice", age=30)

print("\n2. Testing with INFO level:")
with PropertyGraph() as graph:
    graph.set_log_level(logging.INFO)
    user = graph.add_node("User", name="Bob", age=25)

print("\n3. Testing with SUMMARY level (token-efficient):")
with PropertyGraph() as graph:
    graph.set_log_level(SUMMARY)
    user = graph.add_node("User", name="Charlie", age=35)
    # Test bulk operation
    graph.nodes("User").delete().execute()

print("\n4. Testing slow operation warning:")
with PropertyGraph() as graph:
    graph.set_log_level(SUMMARY)
    # Create many nodes to simulate slow operation
    for i in range(50):
        graph.add_node("TempUser", id=i)
    # This should show bulk operation timing
    graph.nodes("TempUser").delete().execute()
