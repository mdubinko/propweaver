# PropWeaver Examples

This directory contains practical examples demonstrating how to use PropWeaver for various use cases.

## Running the Examples

All examples are standalone Python scripts that can be run directly:

```bash
# From the project root directory
python3 examples/social_network.py
python3 examples/knowledge_graph.py
python3 examples/dependency_analysis.py
python3 examples/schema_inspection.py
```

## Examples Overview

### 1. Social Network (`social_network.py`)
Demonstrates modeling social connections with:
- Users with profiles (name, age, city)
- Friendship relationships with metadata (since, strength)
- Querying users by attributes
- Finding relationship patterns

### 2. Knowledge Graph (`knowledge_graph.py`)
Shows how to build a programming knowledge base with:
- Programming languages and their properties
- Frameworks and libraries
- Language-framework relationships
- Cross-language influences
- Querying by time periods and categories

### 3. Dependency Analysis (`dependency_analysis.py`)
Illustrates code dependency tracking with:
- Source files with metadata (path, language, lines, type)
- Import relationships with line numbers
- Dependency analysis and metrics
- Bulk cleanup of temporary files
- Most-imported file analysis

### 4. Schema Inspection (`schema_inspection.py`)
Demonstrates efficient schema discovery and analysis with:
- Listing all node types and edge types in the graph
- Schema validation patterns
- Relationship pattern analysis
- Performance characteristics (single SQL query per operation)
- Usage patterns for graph exploration

## Key Patterns Demonstrated

### Context Manager Usage
All examples use the recommended context manager pattern:
```python
with PropertyGraph("database.db") as graph:
    # Operations here
    pass  # Database automatically closed
```

### Property-Rich Entities
Examples show how to store rich metadata:
```python
user = graph.add_node("User", name="Alice", age=25, city="San Francisco")
friendship = graph.add_edge(alice, "FRIENDS", bob, since="2023-01-01", strength=0.8)
```

### Bulk Operations
Dependency analysis demonstrates efficient bulk deletion:
```python
deleted_count = graph.nodes("File", type="temp").delete().execute()
```

### Graph Metadata
All examples use graph-level properties for metadata:
```python
graph.props["project_type"] = "social_network"
total_users = graph.props["total_users"]
```

## Database Files

Each example creates its own SQLite database file:
- `social_network_example.db`
- `knowledge_graph_example.db`
- `dependency_analysis_example.db`

These files persist after running the examples, so you can inspect the data or run additional queries.

## Next Steps

After running these examples, you can:
1. Modify the examples to match your specific use case
2. Run the comprehensive test suite: `python3 tests/test_propweaver.py`
3. Explore the API documentation in `CLAUDE.md`
4. Build your own graph applications using PropWeaver