# PropWeaver

A general-purpose property graph database library built on SQLite.

## Features

- **🗂️ Nodes and edges with arbitrary properties** - Store any Python data type as properties
- **⚡ CRUD operations with bulk mutations** - Individual and mass operations with transaction safety
- **🔒 Transaction support with automatic rollback** - ACID compliance for data integrity
- **🔗 Lazy query evaluation with method chaining** - XPath-inspired fluent API
- **🛡️ Type-safe operations** - Modern Python type hints and comprehensive testing
- **📦 Zero external dependencies** - Pure Python standard library implementation

## Installation

### From PyPI
```bash
pip install propweaver
# or with Pydantic API models:
pip install "propweaver[api]"
```

### Development Setup (with uv)
```bash
git clone https://github.com/mdubinko/propweaver.git
cd propweaver
uv venv
uv pip install -e .
```

### Development Setup (with pip)
```bash
git clone https://github.com/mdubinko/propweaver.git
cd propweaver
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .
```

### Optional: Pydantic API Models

`propweaver.api` provides Pydantic v2 models for validating PropWeaver return values.
Install the extra to use them:
```bash
uv pip install -e ".[api]"
# or
pip install "propweaver[api]"
```

## Quick Start

```python
from propweaver import PropertyGraph

# Create an in-memory graph
with PropertyGraph() as graph:
    # Create nodes with properties
    alice = graph.add_node("User", name="Alice", age=30, active=True)
    bob = graph.add_node("User", name="Bob", age=25, active=False)
    project = graph.add_node("Project", name="Web App", status="active")
    
    # Create relationships
    works_on = graph.add_edge(alice, "WORKS_ON", project, role="Lead", since="2023-01-01")
    
    # Query nodes
    active_users = list(graph.nodes("User", active=True))
    print(f"Found {len(active_users)} active users")
    
    # Bulk operations
    deleted = graph.nodes("User", active=False).delete().execute()
    print(f"Deleted {deleted} inactive users")
```

## Security Note

PropWeaver is designed for **trusted environments**. Before production use with sensitive data or untrusted input, review [SECURITY_AUDIT.md](SECURITY_AUDIT.md) for security considerations including path validation, encryption options, and resource monitoring. Use `graph.resource_stats()` to monitor database size and entity counts.

## Logging Configuration

PropWeaver uses Python's standard logging module and respects your application's logging configuration. As a library, PropWeaver does not configure handlers or formatters - it only emits log messages that your application controls.

### Application Setup

Configure PropWeaver logging through your application's logging setup:

```python
import logging.config

# Example dictConfig for applications using PropWeaver
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
        }
    },
    'loggers': {
        'propweaver': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'propweaver.storage': {  # SQL operations
            'level': 'WARNING',   # Reduce verbosity
        },
        'propweaver.query': {    # Query operations
            'level': 'INFO',
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### Log Levels

PropWeaver provides structured logging with these levels:

- **`SUMMARY` (25)** - Token-efficient emoji messages for key operations
- **`INFO`** - Standard operational messages
- **`DEBUG`** - Detailed SQL queries and performance data
- **`WARNING/ERROR`** - Issues and exceptions

```python
from propweaver import PropertyGraph, SUMMARY

# Quick setup for testing/development
import logging
logging.getLogger('propweaver').setLevel(SUMMARY)

# Your PropertyGraph operations will now emit concise emoji logs
with PropertyGraph() as graph:
    user = graph.add_node("User", name="Alice")  # 💾 INSERT (2.1ms)
```

### Component Loggers

PropWeaver uses hierarchical loggers for different components:

- `propweaver.storage` - Database operations and SQL queries
- `propweaver.query` - Query execution and results
- `propweaver.performance` - Slow operation warnings
- `propweaver.stats` - Graph statistics and metrics

Enable SQL debugging by setting the storage logger to DEBUG level - PropWeaver will automatically log all SQL queries with parameters and timing.

## Core Features

### Basic CRUD Operations

```python
# Create
user = graph.add_node("User", name="Alice", email="alice@example.com")
friendship = graph.add_edge(user1, "FRIENDS", user2, since="2023-01-01")

# Read
name = user.props["name"]  # Dict-like access
active_users = list(graph.nodes("User", active=True))

# Update
user.props["last_login"] = "2023-12-01"  # Dict-like assignment
user.props.update({"verified": True, "score": 95})  # Bulk update

# Delete properties
del user.props["temp_token"]  # Remove specific property
user.props.clear()  # Remove all properties
```

### Dict-like Property Interface

```python
# Rich dict-like operations on properties
user = graph.add_node("User", name="Alice", age=30)

# Check properties
if "age" in user.props:
    print(f"User has {len(user.props)} properties")

# Iterate over properties  
for key in user.props:
    print(f"{key}: {user.props[key]}")

# Get with defaults
role = user.props.get("role", "user")  # Returns "user" if role not set

# Export properties
all_props = user.props.copy()  # Get dict copy
items = list(user.props.items())  # Get key-value pairs

# Property validation
try:
    user.props["invalid"] = None  # Raises ValueError - None not allowed
except ValueError as e:
    print(f"Error: {e}")  # Use 'del props[key]' instead
```

### Bulk Mutations

```python
# Delete all temporary data
temp_deleted = graph.nodes("TempUser").delete().execute()
expired_edges = graph.edges("SESSION", expired=True).delete().execute()

# Chain filters for complex operations
inactive_old_users = (graph.nodes("User")
                     .filter(active=False)
                     .filter(last_login__before="2022-01-01")
                     .delete()
                     .execute())
```

### Transaction Safety

```python
# Automatic transactions for bulk operations
try:
    count = graph.nodes("BadData").delete().execute()
    print(f"Cleaned up {count} items")
except Exception as e:
    print("Cleanup failed, no data was modified")
    # Automatic rollback on error

# Manual transaction control  
with graph._storage.transaction():
    user = graph.add_node("User", name="Alice")
    project = graph.add_node("Project", name="New Project")
    graph.add_edge(user, "OWNS", project)
    # All committed together, or all rolled back on error
```

### Query Chaining

```python
# XPath-style lazy evaluation
senior_engineers = (graph.nodes("User")
                   .filter(department="Engineering")
                   .filter(level="Senior")
                   .filter(active=True))

# Execute only when iterating
for engineer in senior_engineers:
    print(f"Senior Engineer: {engineer.props['name']}")

# Get a count of the results
count = len(list(senior_engineers))
```

## More Examples

See the `examples/` directory for real-world usage patterns:

```bash
# Run all examples
./bin/examples.sh

# Run specific examples
./bin/examples.sh social      # Social network modeling
./bin/examples.sh knowledge   # Knowledge graph patterns  
./bin/examples.sh deps        # Dependency analysis
```

## API Contract

`contract.json` in the repo root is a machine-readable description of the complete public API — every class, method signature, parameter type, and return type. It is generated from the source and committed so that breaking changes are visible as diffs in pull requests.

Consuming projects (including AI coding assistants) can read this file to verify they are calling APIs correctly without having to inspect source code.

To regenerate after making API changes:
```bash
uv run --extra api python bin/build_contract.py
```

## API Reference

### PropertyGraph Class

The main interface to the graph database.

#### Constructor
- `PropertyGraph(db_path: Optional[str] = None)` - Create graph (in-memory if no path)

#### Node Operations  
- `add_node(node_type: str, **properties) -> NodeProxy` - Create node
- `nodes(node_type: Optional[str] = None, **properties) -> NodeIterator` - Query nodes

#### Edge Operations
- `add_edge(source, edge_type: str, target, **properties) -> EdgeProxy` - Create edge  
- `edges(edge_type: Optional[str] = None, **properties) -> EdgeIterator` - Query edges

#### Graph Operations
- `node_count() -> int` - Total number of nodes
- `edge_count() -> int` - Total number of edges
- `node_types() -> list[str]` - List all distinct node types
- `edge_types() -> list[str]` - List all distinct edge types
- `resource_stats() -> dict` - Get database size and entity counts (for monitoring)
- `props` - Dict-like property interface (see PropertyDict below)

### NodeProxy Class

Lightweight proxy for individual nodes.

- `props` - Dict-like property interface (see PropertyDict below)
- `to_json() -> dict` - Export as dictionary
- `timestamp() -> float` - Creation timestamp

### EdgeProxy Class

Lightweight proxy for individual edges.

- `props` - Dict-like property interface (see PropertyDict below)
- `to_json() -> dict` - Export as dictionary
- `src_id` / `dst_id` - Source and destination node IDs

### PropertyDict Class

Dict-like interface for properties (accessed via `.props` on graph/node/edge):

- `props[key]` - Get property value (raises KeyError if missing)
- `props[key] = value` - Set property value
- `del props[key]` - Delete property (raises KeyError if missing)
- `key in props` - Check if property exists
- `len(props)` - Number of properties
- `props.keys()` - Property names
- `props.values()` - Property values  
- `props.items()` - Property (key, value) pairs
- `props.get(key, default=None)` - Get with optional default
- `props.update(dict)` - Bulk update from dictionary
- `props.clear()` - Remove all properties
- `props.copy()` - Export as regular dict

## Testing

```bash
# Run all tests (pytest)
./bin/test.sh

# Run specific test suites
./bin/test.sh fast           # Fast tests only
./bin/test.sh integration    # Integration tests  
./bin/test.sh coverage       # With coverage report

# Run comprehensive test suite
./bin/test.sh comprehensive
```

## Development

### Quick Start
```bash
# Set up development environment (uv recommended)
./bin/dev.sh setup

# Test basic functionality 
./bin/dev.sh basic

# Run all tests
./bin/test.sh

# Format code and run checks
./bin/dev.sh lint
```

### Requirements
- Python 3.10+
- SQLite 3.7.11+ (for foreign key support)
- Zero external runtime dependencies
- [uv](https://docs.astral.sh/uv/) recommended for development

### Development Scripts
- `./bin/test.sh` - Run tests with various options
- `./bin/examples.sh` - Run examples
- `./bin/dev.sh` - Development utilities (setup, lint, check, etc.)
- `uv run --extra api python bin/build_contract.py` - Regenerate `contract.json`

### Running Tests with Optional Extras
```bash
# Core tests (no extras needed)
uv run --extra dev pytest

# Including api model tests
uv run --extra dev --extra api pytest
```

### Architecture
- **`src/propweaver/storage.py`**: SQLite operations and type mapping
- **`src/propweaver/query.py`**: Query building and lazy evaluation
- **`src/propweaver/core.py`**: Main API and proxy classes

### Contributing
1. Fork the repository
2. Create a feature branch
3. Run `./bin/dev.sh setup` for development environment
4. Add tests for new functionality
5. Run `./bin/dev.sh check` to verify all checks pass
6. Submit a pull request

## Release Process

See [docs/RELEASE.md](docs/RELEASE.md) for the TestPyPI dry run and tagged PyPI release flow.
