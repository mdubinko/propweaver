# PropWeaver Design Decisions: Deep Dives

This document provides deeper exploration of key architectural decisions in PropWeaver. Each decision represents a trade-off between different approaches. Understanding these trade-offs helps you:

1. Know when to follow the pattern vs. when to break it
2. Understand why the code is structured as it is
3. Make informed decisions about future extensions
4. Evaluate whether the codebase is appropriate for your use case

## Table of Contents

1. [The Three-Layer Architecture](#the-three-layer-architecture)
2. [Property Storage Strategy](#property-storage-strategy)
3. [Lazy Evaluation & QuerySpec](#lazy-evaluation--queryspec)
4. [Proxy Objects Over Direct References](#proxy-objects-over-direct-references)
5. [Dict-Like Properties vs. Alternatives](#dict-like-properties-vs-alternatives)
6. [SQLite Over Alternatives](#sqlite-over-alternatives)
7. [Type Serialization](#type-serialization)
8. [Zero Dependencies Philosophy](#zero-dependencies-philosophy)
9. [Comprehensive Test Coverage](#comprehensive-test-coverage)
10. [Module-Private APIs](#module-private-apis)

---

## The Three-Layer Architecture

### The Decision

PropWeaver separates code into three distinct layers:
- **Core API Layer** (core.py): User-facing interface
- **Query Layer** (query.py): Declarative query building
- **Storage Layer** (storage.py): Database operations

### Why This Design

**Separation of Concerns**:
Each layer handles one job:
- Core: "What does the user want to do?"
- Query: "How do we specify that?"
- Storage: "How do we make it happen in the database?"

**Testability**:
```python
## EXAMPLE
# Can test storage layer without a graph
storage = StorageLayer(":memory:")
storage._add_node("User", {"name": "Alice"})

# Can test query building without database
iterator = graph.nodes("User").filter(active=True)
assert len(iterator.query_spec.steps) == 2
# No database access yet!
```

**Maintainability**:
When you need to fix something:
1. Is it about the user API? → core.py
2. Is it about how queries work? → query.py
3. Is it about SQL? → storage.py

No need to search everywhere.

**AI Collaboration**:
Clear boundaries mean AI modifications stay focused:
- "Add ordering to queries" → changes in query.py + storage.py, not core.py
- "Change the API" → changes in core.py only
- "Optimize SQL" → changes in storage.py only

### The Trade-off

**Benefits**:
- ✅ Clear responsibility (easy to understand)
- ✅ Easy to test individual layers
- ✅ Can reason about data flow top-to-bottom
- ✅ Adding features doesn't require changing unrelated code

**Costs**:
- ❌ More files to understand (3 instead of 1)
- ❌ More method calls (overhead, though negligible)
- ❌ Slightly more complex for small use cases

### When You Might Do It Differently

- **Tiny project**: 200 lines of code → single file might be fine
- **Different database backend**: You might collapse Storage layer differently
- **Different query model**: You might remove QuerySpec entirely

### Related Decisions

This decision enables and is enabled by:
- Lazy evaluation (makes Query layer make sense)
- Clear contracts between layers
- Module-private APIs (prefixed with `_`)

---

## Property Storage Strategy

### The Decision

Properties are stored in separate tables (`resource_props`, `rel_props`), not as JSON columns.

**The Schema**:
```sql
CREATE TABLE resource (
    id INTEGER PRIMARY KEY,
    type TEXT,
    created_at REAL
)

CREATE TABLE resource_props (
    resource_id INTEGER,
    key TEXT,
    value TEXT,  -- JSON-encoded
    type TEXT,   -- type metadata
    FOREIGN KEY (resource_id) REFERENCES resource(id) ON DELETE CASCADE
)
```

### Why This Design

**Schema Flexibility**:
```python
## EXAMPLE
# Without knowing property names in advance:
user = graph.add_node("User", name="Alice", age=30, tags=["python", "ai"])
# Same node can have different properties

project = graph.add_node("Project", title="Web App", deadline="2024-12-31")
# Different property set, no migrations needed
```

**Property Queryability**:
```python
## EXAMPLE
# Can query properties directly
results = list(graph.nodes("User").filter(age__gt=25))
# With JSON column approach, you'd need JSON extraction functions
# With separate columns, not possible without knowing property names
```

**Type Preservation**:
Each property remembers its type:
```python
## EXAMPLE
value = user.props["age"]  # Returns int (30), not string ("30")
```

With a JSON column, you'd lose type information or need extra metadata.

**Efficient Nullability**:
Missing properties are just absent rows:
```python
## EXAMPLE
# Alice has age, Bob doesn't
user1 = graph.add_node("User", name="Alice", age=30)
user2 = graph.add_node("User", name="Bob")  # No age property

# This works without NULL handling
```

### The Trade-off

**Benefits**:
- ✅ Flexible schema (add properties anytime)
- ✅ Queryable properties (can filter)
- ✅ Type preservation (round-trip fidelity)
- ✅ Efficient null handling (absence = NULL)

**Costs**:
- ❌ More database tables (more complex schema)
- ❌ More queries (JOIN on properties each time)
- ❌ More storage overhead (one row per property)
- ❌ Slower "get all properties" (multiple rows to fetch and combine)

### When You Might Do It Differently

- **Mostly document-like data**: JSON column with `.props` instead of queryable properties
- **Fixed schema**: Individual columns per property (faster, but less flexible)
- **Large graphs with few property queries**: JSON column reduces storage

### Related Decisions

This enables:
- Schema-flexible queries (no migrations)
- Flexible type handling (via TypeMapper)

---

## Lazy Evaluation & QuerySpec

### The Decision

Queries are specified declaratively in a QuerySpec, then executed lazily.

```python
## EXAMPLE
# Building (no database access)
query = graph.nodes("User").filter(active=True)

# Executing (database accessed here)
for user in query:
    print(user.props["name"])
```

### Why This Design

**For Humans**:
```python
## EXAMPLE
# Reads like intent, not like execution
senior_engineers = (
    graph.nodes("User")
    .filter(department="Engineering")
    .filter(level="Senior")
    .order_by("hire_date")
)
```

**For Composability**:
```python
## EXAMPLE
# Build queries piece by piece
base_query = graph.nodes("User")
if include_active:
    base_query = base_query.filter(active=True)
if department_filter:
    base_query = base_query.filter(department=department_filter)

for user in base_query:
    # ...
```

**For AI Tools**:
```python
## EXAMPLE
# AI can reason about this structure
QuerySpec(steps=[
    QueryStep(type="SOURCE", source_type="User"),
    QueryStep(type="FILTER", properties={"active": True}),
    QueryStep(type="ORDER", field="hire_date")
])
# Rather than having to understand SQL string generation
```

**For Inspectability**:
```python
## EXAMPLE
# You can see what will be executed before it runs
query = graph.nodes("User").filter(active=True)
print(query.query_spec.steps)

# Output shows the exact structure:
# [
#   QueryStep(type="SOURCE", source_type="User"),
#   QueryStep(type="FILTER", properties={"active": True})
# ]

# Useful for debugging complex queries
complex_query = (graph.nodes("User")
                .filter(active=True)
                .filter(department="Engineering"))
print(complex_query.query_spec.steps)
# [
#   QueryStep(type="SOURCE", source_type="User"),
#   QueryStep(type="FILTER", properties={"active": True}),
#   QueryStep(type="FILTER", properties={"department": "Engineering"})
# ]

# You can see exactly what filters are applied and in what order
# before the database is touched
```

**For Extensibility**:
Adding a new query operation is straightforward:
1. Add a new QueryStep type
2. Add a method to the iterator
3. Handle the step in StorageLayer

No changes to how queries are built or executed.

### The Trade-off

**Benefits**:
- ✅ Human-readable syntax (clear intent)
- ✅ Composable (build incrementally)
- ✅ Inspectable (see the plan)
- ✅ Extensible (add new operations easily)
- ✅ AI-friendly (clear structure)
- ✅ Supports advanced optimizations (could reorder steps, eliminate redundant filters, etc.)

**Costs**:
- ❌ More code to understand (QuerySpec, QueryStep, iterators)
- ❌ Slight overhead (building steps before execution)
- ❌ More complex for simple cases
- ❌ Could be confusing if someone expects immediate execution

### When You Might Do It Differently

- **Simple, SQL-only use case**: Direct SQL generation might be simpler
- **Eager execution preferred**: Execute on each method call (faster immediate feedback)
- **Small graphs**: Performance overhead negligible, but structure still helps

### Implementation Details

**Immutability Pattern**:
```python
...
# Each method returns a new iterator with updated QuerySpec
def filter(self, **properties) -> NodeIterator:
    new_spec = self.query_spec.copy()  # Copy, don't modify in place
    new_spec.steps.append(QueryStep(...))
    return NodeIterator(self.graph, new_spec)
...
```

This ensures queries are composable without surprise side effects.

---

## Proxy Objects Over Direct References

### The Decision

NodeProxy and EdgeProxy are lightweight handles, not full objects.

```python
## EXAMPLE
user = graph.add_node("User", name="Alice", age=30)
# 'user' is a NodeProxy: (graph_ref, node_id)
# Not a Python object with full state loaded

# Properties are queried on-demand
name = user.props["name"]  # Database query happens here
```

### Why This Design

**Memory Efficiency**:
```python
## EXAMPLE
# With full object loading
users = list(graph.nodes("User"))  # Loads all users into memory
# If you have 1M users with 10 properties each, that's a lot of RAM

# With proxies
users = graph.nodes("User")  # Returns iterator
for user in users:
    # Process one user at a time, don't keep all in memory
    process(user)
```

**Correctness**:
```python
## EXAMPLE
# With proxies, you always see current state
user = graph.add_node("User", name="Alice")
user.props["name"] = "Alice Smith"

# If someone else modifies in another connection:
# (not common in PropWeaver, but principle matters)
current_name = user.props["name"]  # Reads from DB
```

**Semantic Clarity**:
```python
## EXAMPLE
# It's obvious that modifications go to the database
user.props["active"] = False  # This is a database operation
# Not modifying an in-memory object that might not sync
```

### The Trade-off

**Benefits**:
- ✅ Memory efficient (don't load what you don't use)
- ✅ Always fresh (no stale data)
- ✅ Clear semantics (proxy ≠ object)
- ✅ No caching complexity

**Costs**:
- ❌ More database queries (one per property access)
- ❌ Slower than cached access (slight overhead)
- ❌ More complex than full object load
- ❌ Can't compare proxies easily (`user1 == user2` doesn't work as expected)

### When You Might Do It Differently

- **Frequently accessed properties**: Load and cache in memory
- **Large objects**: Loading entire state at once is expensive
- **Offline usage**: Load state, work offline, sync back

### Alternative Implementation

If you needed caching, you could add:
```python
...
class CachedNodeProxy(NodeProxy):
    def __init__(self, graph, node_id, node_type):
        super().__init__(graph, node_id, node_type)
        self._props_cache = None

    @property
    def props(self):
        if self._props_cache is None:
            self._props_cache = super().props
        return self._props_cache
...
```

This would be a separate class, keeping the simple proxy simple.

---

## Dict-Like Properties vs. Alternatives

### The Decision

Properties accessed as `node.props["key"]`, implementing the dict protocol.

```python
## EXAMPLE
user.props["name"] = "Alice"      # __setitem__
name = user.props["name"]         # __getitem__
"name" in user.props              # __contains__
del user.props["name"]            # __delitem__
for key in user.props:            # __iter__
    # ...
```

### Why This Design

**Pythonic**:
Dict-like access is familiar to any Python programmer:
```python
## EXAMPLE
# Consistent with how dicts work
d = {"name": "Alice"}
d["name"]  # Works the same

user.props["name"]  # Same interface
```

**Schema Flexibility**:
```python
## EXAMPLE
# Works with any property, no need to define them
user.props["custom_field"] = "value"
user.props["tags"] = ["a", "b", "c"]
```

**Consistency**:
```python
## EXAMPLE
# Same interface for everything
user.props["name"]      # Node properties
edge.props["strength"] # Edge properties
graph.props["version"] # Graph properties
```

**Comprehensive Error Handling**:
```python
## EXAMPLE
# PropertyNotFoundError gives helpful context
try:
    user.props["nonexistent"]
except PropertyNotFoundError as e:
    print(f"Property '{e.property_name}' not found on {e.entity_type} {e.entity_id}")
    print(f"Available: {e.available_properties}")
```

### The Trade-off

**Benefits**:
- ✅ Familiar to Python developers (standard interface)
- ✅ Flexible (any property name)
- ✅ Consistent across nodes/edges/graph
- ✅ Rich error messages
- ✅ Full dict protocol (`get`, `update`, `clear`, etc.)

**Costs**:
- ❌ No IDE autocomplete (dict keys aren't known statically)
- ❌ No type checking (`mypy` can't verify property names)
- ❌ Slightly slower than attribute access (dict lookup vs. attribute lookup)
- ❌ Different from attribute access (mental switch cost)

### Alternatives Considered

**Alternative 1: Attribute Access**
```python
## EXAMPLE
user.name = "Alice"
user.age = 30

# Pros: IDE autocomplete, type checking
# Cons: Dynamic attributes (fragile), can conflict with methods
```

**Alternative 2: Method Calls**
```python
## EXAMPLE
user.set_property("name", "Alice")
user.get_property("name")

# Pros: Explicit, clear it's a database operation
# Cons: Verbose, not idiomatic Python
```

**Alternative 3: TypedDict with Schema**
```python
## EXAMPLE
class User(TypedDict):
    name: str
    age: int

user.props["name"]  # Still type-safe with schema

# Pros: Type safety, IDE support
# Cons: Requires schema definition, less flexible
```

### When You Might Do It Differently

- **IDE support critical**: Attribute access or TypedDict with schema
- **Type safety paramount**: Explicit schema validation
- **Verbose intent preferred**: Method calls (`set_property`)

---

## SQLite Over Alternatives

### The Decision

SQLite as the storage backend (bundled with Python, zero external dependencies).

### Why This Design

**Zero Dependencies**:
```python
## EXAMPLE
# No external packages to install
import sqlite3  # Built in!

# This matters:
# - Easier to reason about code (no external library APIs)
# - Easier for AI tools to understand
# - No dependency hell (conflicting versions)
# - Easier to deploy
```

**ACID Compliance**:
```python
## EXAMPLE
# Automatic transaction safety
with graph._storage.transaction():
    graph.add_node("User", name="Alice")
    graph.add_node("User", name="Bob")
    graph.add_edge(alice, "FRIENDS", bob)
    # All succeed or all fail - no partial updates
```

**Good Performance for Typical Use**:
```python
## EXAMPLE
# Fast for single-process, working-set fits in RAM
# Suitable for:
# - Desktop applications
# - Single-machine servers
# - Embedded databases
# - Testing and development
```

**Inspectable**:
```bash
# Can open the database file directly
sqlite3 my_graph.db
sqlite> SELECT * FROM resource;
sqlite> SELECT * FROM resource_props;
# Inspect/debug without special tools
```

**Mature & Stable**:
- 20+ years of production use
- Extremely reliable
- Not going away

### The Trade-off

**Benefits**:
- ✅ Zero dependencies (simplicity, AI-friendly)
- ✅ Built-in (no installation needed)
- ✅ ACID transactions
- ✅ Good performance for typical use
- ✅ Inspectable (open the file directly)
- ✅ Portable (SQLite file works anywhere)

**Costs**:
- ❌ Not ideal for very large graphs (terabytes+)
- ❌ Limited concurrency (single writer)
- ❌ Not distributed (single machine)
- ❌ Not as performant as specialized databases
- ❌ In-memory graphs lose data on exit

### When You Might Do It Differently

- **Very large graphs** (>10GB): PostgreSQL, Neo4j
- **Distributed graphs**: Distributed databases
- **High concurrency**: PostgreSQL, MySQL
- **Cloud-first**: Managed databases (DynamoDB, etc.)
- **Specialized graph algorithms**: Neo4j (built-in algorithm support)

### How to Extend for Different Backends

The storage layer abstraction makes this possible:

```python
...
# Current: StorageLayer talks to SQLite
class StorageLayer:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def _add_node(self, ...):
        # SQLite-specific SQL

# Future: Could add PostgreSQL
class PostgreSQLStorageLayer(StorageLayer):
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)

    def _add_node(self, ...):
        # PostgreSQL-specific SQL
...
```

The Query and Core layers wouldn't change.

---

## Type Serialization

### The Decision

Complex types are serialized to JSON with type metadata.

```python
## EXAMPLE
# User writes
user.props["tags"] = ["python", "databases"]
user.props["metadata"] = {"role": "engineer", "level": 5}
user.props["created"] = datetime(2024, 1, 15)

# Storage (in database)
# tags: {"value": "[\"python\", \"databases\"]", "type": "list"}
# metadata: {"value": "{...}", "type": "dict"}
# created: {"value": "2024-01-15T00:00:00", "type": "datetime"}

# User gets back
tags = user.props["tags"]  # list, not string
metadata = user.props["metadata"]  # dict, not string
created = user.props["created"]  # datetime, not string
```

### Why This Design

**Type Fidelity**:
```python
## EXAMPLE
# What you put in is what you get out
value = user.props["count"]  # 42 (int)
assert isinstance(value, int)  # True, not "42" (string)
```

**Human Readable**:
```bash
# Can inspect the database file
sqlite3 graph.db
sqlite> SELECT * FROM resource_props;
# Sees {"value": "...", "type": "..."}
# Not binary pickle data
```

**Language Agnostic**:
```python
## EXAMPLE
# Could export to JSON and load from another language
# Impossible with Python pickle
export = json.dumps(user.to_json())
# Another system could import this
```

**Web Friendly**:
```python
## EXAMPLE
# Natural fit with JSON APIs
user_data = user.to_json()
response = jsonify(user_data)  # Works perfectly
```

**Queryable** (in database):
```sql
-- Could potentially query JSON fields
SELECT * FROM resource_props
WHERE json_extract(value, '$.tags[0]') = 'python'
```

### The Trade-off

**Benefits**:
- ✅ Full type preservation (round-trip fidelity)
- ✅ Human readable (JSON)
- ✅ Language agnostic
- ✅ Web friendly
- ✅ Potentially queryable

**Costs**:
- ❌ Extra storage (metadata overhead)
- ❌ Slower than native types (serialization time)
- ❌ Some types don't serialize (custom classes)
- ❌ Slightly more complex (need type mapping)

### When You Might Do It Differently

- **Performance critical**: Store native types (lose type info)
- **Custom types common**: Use pickle (Python-only, not inspectable)
- **Storage size critical**: Binary encoding (MessagePack, Protocol Buffers)

### Supported Types

Currently supported:
- Primitives: `int`, `float`, `str`, `bool`
- Collections: `list`, `dict`, `tuple`, `set`
- Temporal: `datetime`, `date`, `time`
- Absence: `None` (property doesn't exist)

### Extension Pattern

To add a new type:

```python
...
class TypeMapper:
    @staticmethod
    def to_sqlite(value):
        # ... existing code ...
        elif isinstance(value, MyCustomType):
            return {
                "value": serialize_my_type(value),
                "type": "mycustomtype"
            }

    @staticmethod
    def from_sqlite(data):
        # ... existing code ...
        elif data["type"] == "mycustomtype":
            return deserialize_my_type(data["value"])
...
```

---

## Zero Dependencies Philosophy

### The Decision

Use only Python standard library (sqlite3, json, datetime, logging, typing, etc.).

### Why This Design

**For AI Tools**:
```python
## EXAMPLE
# AI knows what sqlite3 does (it's built-in)
# AI doesn't have to learn:
# - pandas API
# - sqlalchemy API
# - custom library API

# Less hallucination risk
# Higher correctness of generated code
```

**For Deployment**:
```bash
# No pip install needed (beyond the library itself)
# No dependency hell (conflicting versions)
# No transitive dependencies (library A requires library B v1, C requires v2)
# Works in any Python environment

# Works offline
# Works in sandboxed environments
# Works in browsers (via Pyodide)
```

**For Maintainability**:
```python
## EXAMPLE
# When you read a function, you know what it does
import json
data = json.loads(text)  # Clear

# With external library, you have to know the library
import pandas
df = pandas.read_json(text)  # Need to know pandas API
```

**For Learning**:
```python
## EXAMPLE
# Students can understand the entire codebase
# No "magic" from external libraries
# Can trace through all code (libraries are black boxes)
```

**For Verification**:
```python
## EXAMPLE
# Can trace SQL generation completely (it's your code)
# Can understand type conversion (you wrote it)
# With ORMs, some behavior is hidden in the library
```

### The Trade-off

**Benefits**:
- ✅ Zero dependencies (simplicity, deployment)
- ✅ AI-friendly (clear code)
- ✅ Educational (transparent)
- ✅ Small package size
- ✅ No version conflicts
- ✅ Works anywhere Python works

**Costs**:
- ❌ Have to write more code ourselves
- ❌ Can't leverage mature libraries
- ❌ Some problems aren't worth solving (reinventing wheels)
- ❌ Might miss optimizations that libraries have
- ❌ Maintainability burden (we own all the code)

### When You Might Do It Differently

- **SQL generation complexity**: Use SQLAlchemy
- **Large graph algorithms**: Use graph-tool or networkx
- **Async operations**: Use libraries (not in standard library well)
- **Complex type handling**: Use attrs or dataclasses (though dataclasses are now in stdlib)

### What Standard Library Provides

It's more capable than people think:

```python
## EXAMPLE
# Query building: No need for SQLAlchemy
sql = "SELECT * FROM resource WHERE type = ?"
params = [user_type]

# Type handling: json, datetime, collections all available
# Logging: Built-in logging module
# Testing: unittest (plus pytest as dev dependency, not runtime)
# Data structures: dict, list, tuple, set, deque, defaultdict, etc.
```

---

## Comprehensive Test Coverage

### The Decision

Extensive test suite covering unit, integration, and edge cases.

**Test Organization**:
```
tests/
├── test_crud.py              # Create, read, update, delete
├── test_query.py             # Query building and filtering
├── test_bulk_operations.py   # Bulk deletes, transactions
├── test_integration.py       # End-to-end scenarios
├── test_types.py             # Type mapping and serialization
└── conftest.py               # Test fixtures and configuration
```

### Why This Design

**For AI Tools**:
```python
## EXAMPLE
# Tests are executable specification
# AI can read tests to understand expected behavior
def test_node_creation():
    graph = PropertyGraph()
    user = graph.add_node("User", name="Alice")
    assert user.props["name"] == "Alice"

# AI: "So add_node should create a node with properties"
```

**For Validation**:
```python
## EXAMPLE
# AI generates code → runs tests → passes → confidence
# Test failures provide precise feedback for the AI to fix
```

**For Regression Prevention**:
```python
## EXAMPLE
# When modifying code, run tests to ensure nothing breaks
# Especially important with AI-generated changes
```

**For Documentation**:
```python
## EXAMPLE
# Tests show how to use the code
# Test names are descriptive
def test_filter_multiple_properties_with_chaining():
    # This shows how to chain filters
```

**For Confidence**:
```python
## EXAMPLE
# Changes are safer if well-tested
# AI-generated code is safer if validated by tests
```

### Test Philosophy

**Coverage Focus**: Important paths, not 100% coverage obsession

```python
## EXAMPLE
# Worth testing
def test_add_node_with_multiple_properties():
    # How users actually use it

# Maybe not worth testing
def test_add_node_with_unicode_property_name():
    # Edge case that tests test framework, not our code
```

**Intent Over Implementation**:
```python
## EXAMPLE
# Test what it does (behavior), not how it does it (implementation)
# This allows refactoring without rewriting tests

# Good
def test_nodes_returns_all_nodes_of_type():
    user1 = graph.add_node("User", name="Alice")
    user2 = graph.add_node("User", name="Bob")
    project = graph.add_node("Project", name="App")

    users = list(graph.nodes("User"))
    assert len(users) == 2

# Bad (tests implementation, not behavior)
def test_nodes_calls_storage_query():
    graph.nodes("User")
    assert storage._query_nodes.called  # Tests HOW, not WHAT
```

### The Trade-off

**Benefits**:
- ✅ Confidence in changes
- ✅ Executable specification
- ✅ Regression prevention
- ✅ Easier AI collaboration
- ✅ Safe refactoring
- ✅ Documentation

**Costs**:
- ❌ Time to write tests
- ❌ Tests to maintain
- ❌ Tests can be fragile (implementation coupled)
- ❌ Test duplication
- ❌ Slower to run (many tests)

### Running Tests

```bash
# Brief output (useful in CI/with AI tools)
./bin/test.sh brief

# Detailed output
./bin/test.sh fast

# With coverage
./bin/test.sh coverage

# Comprehensive (all tests, all options)
./bin/test.sh comprehensive
```

### Test-Driven Development Pattern

Recommended workflow:

```python
## EXAMPLE
1. Write failing test
2. Implement feature to pass test
3. Refactor if needed (tests ensure correctness)
4. Run full test suite to check for regressions
```

This workflow is particularly good with AI tools:
- "Write a test for adding ordering to queries"
- AI writes test
- "Implement the feature to pass this test"
- AI implements
- Run tests to verify

---

## Module-Private APIs

### The Decision

Methods are marked private with underscore prefix (`_method_name`).

```python
## EXAMPLE
# Public API
graph.add_node("User", name="Alice")
graph.nodes("User")

# Private API (don't use directly)
storage = graph._storage
storage._add_node("User", {"name": "Alice"})
storage._execute_query(spec)
```

### Why This Design

**API Clarity**:
```python
## EXAMPLE
# Public: guaranteed stable interface
user = graph.add_node("User", ...)

# Private: subject to change, not part of API contract
user._internal_id = ...  # Don't rely on this
```

**Separation of Concerns**:
```python
## EXAMPLE
# Users use PropertyGraph methods
# Developers use StorageLayer methods
# Clear boundary between layers
```

**Refactoring Freedom**:
```python
## EXAMPLE
# Can refactor StorageLayer internals (private APIs)
# without breaking user code
# Can't change PropertyGraph methods (public API)
```

**AI Collaboration**:
```python
## EXAMPLE
# AI knows not to use private APIs
# Reduces hallucination (AI tends toward using public APIs)
# If AI uses private API, it's obvious (underscore prefix)
```

### Python Convention

This is a Python convention, not enforced by the language:

```python
## EXAMPLE
class Example:
    def public_method(self):
        # Safe to use
        pass

    def _private_method(self):
        # Intended for internal use
        # Subject to change
        pass

    def __very_private(self):
        # Name mangling (Python renames automatically)
        # For avoiding accidental overwrites in subclasses
        pass
```

PropWeaver uses single underscore for "private, but accessible if needed" (not name mangling).

### When Someone Uses Private APIs

If you find yourself using `graph._storage._add_node()`:

**Check**: Is there a public API that does what you need?
```python
## EXAMPLE
# Instead of:
graph._storage._add_node("User", {"name": "Alice"})

# Use:
graph.add_node("User", name="Alice")
```

**Reason**: The public API is stable; private APIs change.

### Trade-offs

**Benefits**:
- ✅ Clear API surface (not too large)
- ✅ Refactoring freedom (private methods can change)
- ✅ Less surface area to maintain
- ✅ Prevents misuse

**Costs**:
- ❌ Convention only (not enforced)
- ❌ Sometimes you need private APIs (acceptable, marked as such)
- ❌ Slight documentation burden (explain what's private)

---

## Summary: When to Follow vs. Break Patterns

Use these design decisions as guidelines, not absolute rules:

**Follow the pattern if**:
- Your changes are similar to existing code
- You're adding features within a layer
- The pattern has proven reliable

**Consider breaking the pattern if**:
- You have a specific performance need (measure first)
- The pattern doesn't fit your use case (document why)
- You're refactoring for good reason (run tests)

**Always**:
- Ask "why was this designed this way?"
- Understand the trade-offs
- Maintain the three-layer architecture (this is core)
- Keep tests in sync with code
- Document non-obvious decisions