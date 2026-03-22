# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the PropGraph library.

## Approach

The top goal here is to produce clean, maintainable, readable v3.12 pythonic code that sets the standard for AI-generated projects, and can serve as an example for future generations.

Always make sure tests stay in sync with the implementation.

Use TODO.md to keep track of TODO items across Claude sessions.

## Emoji Style Guide

PropGraph uses a systematic approach to emojis in development output to enhance readability and minimize token usage when working with AI tools. Emojis provide dense visual information that would otherwise require multiple words.

### **Test Results & Status**
- ✅ **Success/Completion**: Test passes, operation successful, task completed
- ❌ **Failure/Error**: Test fails, operation failed, error occurred  
- ⚠️ **Warning/Deprecated**: Warnings, deprecated features, cautions
- 🎯 **Target/Goal**: Achievements, milestones, objectives met

### **Development Operations**
- 🔍 **Search/Analysis**: Finding, investigating, analyzing code
- 🔧 **Build/Modify**: Building, refactoring, updating code
- 🗑️ **Delete/Cleanup**: Removing files, cleaning up data, bulk deletions
- 📊 **Data/Statistics**: Counts, metrics, performance data

### **Examples & Documentation**
- 🎉 **Celebration**: Major completions, releases, celebrations
- 📖 **Documentation**: README updates, doc generation
- 🏗️ **Architecture**: System design, structure changes
- 🚨 **Critical**: Important issues, urgent fixes, breaking changes

### **Usage Guidelines**
- **Token efficiency**: Use emojis to replace verbose status descriptions
- Use sparingly - maximum 1-2 emojis per line
- Prefer at start of line for status indicators
- Avoid in error messages or logs (use in success messages)
- Be consistent across similar operations
- Examples should use ✅ for completion states
- Choose emojis that convey meaning even without context

## Project Overview

PropGraph is a general-purpose property graph database library built on SQLite. It provides:

- **Nodes and edges with arbitrary properties** - Store any Python data type
- **CRUD operations with bulk mutations** - Individual and mass operations  
- **Transaction support with automatic rollback** - ACID compliance
- **Lazy query evaluation with method chaining** - XPath-inspired API and query data model
- **Type-safe operations** - Literal types and comprehensive testing
- **Zero external dependencies** - Pure Python standard library

PropGraph is designed to be reusable for any graph database needs including social networks, knowledge graphs, dependency analysis, and more.

## Architecture

### Core Modules

- **`src/propgraph/storage.py`**: Low-level database operations and type mapping
  - `TypeMapper`: Python type ↔ SQLite storage conversion
  - `StorageLayer`: All SQL operations, schema management, transactions
  
- **`src/propgraph/query.py`**: Declarative query system with lazy evaluation
  - `QuerySpec`/`QueryStep`: Declarative query representation
  - `NodeIterator`/`EdgeIterator`: XPath-style method chaining

- **`src/propgraph/core.py`**: Main user-facing API
  - `PropertyGraph`: Primary database interface
  - `NodeProxy`/`EdgeProxy`: Lightweight entity handles

### Database Schema

SQLite tables with foreign key constraints and cascading deletes:

- **`resource`**: Nodes with id, type, created_at
- **`resource_props`**: Node properties with typed values  
- **`rel`**: Edges with src_id, dst_id, type, created_at
- **`rel_props`**: Edge properties with typed values
- **`graph_metadata`**: Graph-level metadata including schema_version

## Development Commands

### Quick Setup
```bash
# Set up development environment (uv recommended)
./bin/dev.sh setup

# Test basic functionality
./bin/dev.sh basic
```

### Running Tests
```bash
# Run all tests (pytest)
./bin/test.sh brief # AI agents: try this first for token-efficient limited output

# Run specific test types
./bin/test.sh fast          # Fast tests
./bin/test.sh integration   # Integration tests
./bin/test.sh coverage      # With coverage

# Run comprehensive test suite
./bin/test.sh comprehensive
```

### Running Examples
```bash
# Run all examples
./bin/examples.sh

# Run specific examples
./bin/examples.sh social knowledge deps
```

### Development Tools
```bash
# Format code and run linting
./bin/dev.sh lint

# Run all pre-commit checks
./bin/dev.sh check

# Clean up artifacts
./bin/dev.sh clean
```

### Common Development Patterns
```bash
# Test basic functionality
./bin/dev.sh basic

# Test bulk operations  
./bin/dev.sh bulk

# See examples/ directory for real-world patterns
./bin/examples.sh
```

### Python Environment
- Python 3.10+ (uses match expressions and modern type hints)
- Zero external dependencies - uses only standard library
- Compatible with SQLite 3.7.11+ (for foreign key support)

## API Reference

### Basic Operations

#### Creating Nodes and Edges
```python
from propgraph import PropertyGraph

with PropertyGraph("my_graph.db") as graph:
    # Create nodes with properties
    user = graph.add_node("User", name="Alice", email="alice@example.com", active=True)
    project = graph.add_node("Project", name="Web App", status="active")
    
    # Create relationships with properties  
    works_on = graph.add_edge(user, "WORKS_ON", project, role="Lead", since="2023-01-01")
```

#### Reading and Filtering
```python
# Query nodes with filtering
for user in graph.nodes("User", active=True):
    print(f"Active user: {user.props['name']}")

# Query edges with filtering
for edge in graph.edges("WORKS_ON", role="Lead"):
    print(f"Lead on project: {edge.dst_id}")

# Chain filters for complex queries
senior_engineers = graph.nodes("User").filter(active=True).filter(role="Senior")
```

### Bulk Mutation Operations

#### Bulk Node Deletion
```python
# Delete all nodes of a specific type
deleted_count = graph.nodes("TempUser").delete().execute()
print(f"Deleted {deleted_count} temporary users")

# Delete nodes matching properties
deleted_count = graph.nodes("User", active=False).delete().execute()

# Chain filters before deletion
deleted_count = graph.nodes("User").filter(department="Legacy").delete().execute()
```

#### Bulk Edge Deletion
```python
# Delete all edges of a specific type
deleted_count = graph.edges("temp_relation").delete().execute()

# Delete edges matching properties
deleted_count = graph.edges("WORKS_ON", active=False).delete().execute()

# Chain filters before deletion
deleted_count = graph.edges("FRIENDS").filter(status="inactive").delete().execute()
```

### Transaction Support

All bulk operations are automatically wrapped in transactions:

```python
# Automatic transaction on bulk operations
try:
    deleted_count = graph.nodes("TempData").delete().execute()
    # If this succeeds, all deletes are committed
    print(f"Successfully deleted {deleted_count} items")
except Exception as e:
    # If this fails, all changes are rolled back automatically
    print(f"Operation failed, all changes rolled back: {e}")

# Manual transaction control
with graph._storage.transaction():
    graph.add_node("User", name="Bob")
    graph.add_node("User", name="Carol") 
    # Both nodes committed together, or both rolled back on error
```

### Property Operations

```python
# Individual node/edge property updates
user.props["last_login"] = "2023-12-01"
edge.props["strength"] = 0.85

# Batch updates
user.props.update({"name": "Alice Smith", "verified": True, "score": 95})

# Reading properties
name = user.props["name"]
name = user.props.get("name")        # Returns None if missing (no exception)
all_props = user.props.copy()        # Returns regular dict of all properties
```

### Graph Metadata

```python
# Set graph-level properties
graph.props["schema_version"] = 2
graph.props["created_by"] = "migration_script"

# Read graph metadata
version = graph.props["schema_version"]   # Always available
version = graph.props.get("schema_version")  # Safe read with default None
```

### Schema Inspection

```python
# List all node types in the graph (sorted alphabetically)
node_types = graph.node_types()  # ['Category', 'Product', 'User']

# List all edge types in the graph (sorted alphabetically)
edge_types = graph.edge_types()  # ['BELONGS_TO', 'FRIENDS', 'PURCHASED']

# Get counts
node_count = graph.node_count()
edge_count = graph.edge_count()

# Use for schema validation or exploration
if 'User' in graph.node_types():
    users = graph.nodes('User')

# Efficient discovery of relationship patterns
for edge_type in graph.edge_types():
    count = len(list(graph.edges(edge_type)))
    print(f"{edge_type}: {count} relationships")
```

## Query Architecture

The PropGraph uses a declarative query system with lazy evaluation:

- **QuerySpec**: Declarative query specification with steps
- **QueryStep**: Individual operations (SOURCE, FILTER, TRAVERSE, DELETE, etc.)
- **NodeIterator/EdgeIterator**: Lazy evaluation with method chaining
- **Execution Engine**: Converts query plans to SQL operations

### Query Steps
```python
# SOURCE: Start query from all nodes/edges
# FILTER: Filter by type/properties 
# TRAVERSE: Follow edges to related nodes
# ORDER: Sort results by field
# DELETE: Delete matching nodes/edges
```

### Extending the Query System

To add new QueryStep types:

1. **Add to Literal type** in `query.py`:
   ```python
   type: Literal["SOURCE", "FILTER", "TRAVERSE", "ORDER", "DELETE", "YOUR_NEW_TYPE"]
   ```

2. **Handle in execution engine** in `storage.py`:
   ```python
   elif step.type == "YOUR_NEW_TYPE":
       # Implementation here
       pass
   ```

3. **Add methods to iterators** in `query.py`:
   ```python
   def your_operation(self, params):
       new_spec = QuerySpec()
       new_spec.steps = self.query_spec.steps.copy()
       new_spec.steps.append(QueryStep(type="YOUR_NEW_TYPE", ...))
       return NodeIterator(self.graph, new_spec)
   ```

## Best Practices

### Context Managers
```python
# Use context managers for automatic cleanup
with PropertyGraph("database.db") as graph:
    # Operations here
    pass  # Database connection automatically closed
```

### Performance 
```python
# Prefer bulk operations for performance
# Good: Delete many items at once
graph.nodes("TempUser").delete().execute()

# Avoid: Deleting items one by one
for user in graph.nodes("TempUser"):
    graph._storage._delete_node(user.node_id)  # Don't do this

# Use transactions for related operations
with graph._storage.transaction():
    user1 = graph.add_node("User", name="Alice")
    user2 = graph.add_node("User", name="Bob")
    graph.add_edge(user1, "FRIENDS", user2)
    # All operations committed together
```

### Error Handling
```python
# Bulk operations provide transaction safety
try:
    deleted = graph.nodes("BadData").delete().execute()
    print(f"Cleaned up {deleted} items")
except Exception as e:
    print(f"Cleanup failed, no changes made: {e}")
    # Database state is unchanged due to transaction rollback
```

### Type Safety
```python
# Use type hints for better IDE support
from propgraph import PropertyGraph, NodeProxy, EdgeProxy

def process_user(user: NodeProxy) -> None:
    name: str = user.props["name"]
    age: int = user.props.get("age") or 0

def create_relationship(graph: PropertyGraph, user1: NodeProxy, user2: NodeProxy) -> EdgeProxy:
    return graph.add_edge(user1, "FRIENDS", user2, created=datetime.now())
```

## Common Use Cases

Look in the examples/ directory for some common usage patterns.

## API Contract

`contract.json` in the repo root is a machine-readable description of the complete public API. It is the primary reference for other Claude Code instances and consuming projects to verify they are calling PropGraph APIs correctly.

**Regenerate after any API change:**
```bash
uv run --extra api python bin/build_contract.py
```

**Bump `propgraph_version` in `src/propgraph/__init__.py` when making compatibility-breaking changes** (removed methods, renamed parameters, changed return types). This signals to consumers that they need to re-verify their usage against the updated contract.

Non-breaking additions (new methods, new optional parameters) do not require a version bump but the contract should still be regenerated and committed.

## Integration with Other Projects

### As a Dependency
Add to `pyproject.toml`:
```toml
[dependencies]
propgraph = {path = "../propgraph", develop = true}  # Local development
# or
propgraph = ">=0.1.0"  # When published to PyPI
```

### Import Patterns
```python
# Recommended imports
from propgraph import PropertyGraph  # Main class
from propgraph import NodeProxy, EdgeProxy  # For type hints

# Internal APIs (advanced usage)
from propgraph.query import QuerySpec, QueryStep
from propgraph.storage import StorageLayer, TypeMapper
```