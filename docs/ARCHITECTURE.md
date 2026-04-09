# PropWeaver Architecture & AI-Assisted Development

A comprehensive guide to understanding PropWeaver's design, its core architectural decisions, and how to work effectively with AI tools to maintain and extend this codebase.

## Table of Contents

1. [Foundation](#foundation)
2. [The Three-Layer Architecture](#the-three-layer-architecture)
3. [Core Design Patterns](#core-design-patterns)
4. [Architecture by Layer](#architecture-by-layer)
5. [Design for AI Collaboration](#design-for-ai-collaboration)
6. [Thinking Like a Maintainer](#thinking-like-a-maintainer)
7. [Key Design Decisions & Trade-offs](#key-design-decisions--trade-offs)

---

## Foundation

### What Is PropWeaver?

PropWeaver is a **property graph database library** — a lightweight, dependency-free implementation of graph database fundamentals built on SQLite. Unlike traditional ORM systems or document databases, property graphs explicitly model:

- **Nodes**: Entities (users, products, concepts) with properties
- **Edges**: Relationships between entities with their own properties
- **Properties**: Arbitrary typed values on both nodes and edges

This makes property graphs ideal for:
- Social networks (users → friends → interests)
- Knowledge graphs (concepts → related_to → concepts)
- Dependency analysis (components → depends_on → components)
- Any domain where relationships and their attributes matter

### Why PropWeaver Exists

PropWeaver was built with specific constraints and goals:

1. **No external dependencies** - The entire system uses only Python's standard library
2. **Clear architecture** - Separated concerns make it easy to understand and modify
3. **AI-friendly design** - Structured for effective collaboration with AI-assisted development tools
4. **Educational value** - Serves as a reference implementation of graph database design
5. **Composable queries** - Declarative query building enables both human understanding and AI generation

### The Property Graph Data Model

A property graph extends basic graphs with properties:

```
Graph:
├── Nodes (resources)
│   ├── id: unique identifier
│   ├── type: string category
│   ├── created_at: timestamp
│   └── properties: key-value pairs
│
└── Edges (relationships)
    ├── src_id: source node
    ├── dst_id: target node
    ├── type: string category
    ├── created_at: timestamp
    └── properties: key-value pairs
```

Example:
```
Node: id=1, type="User", name="Alice", active=true
Node: id=2, type="Project", name="Web App", status="active"
Edge: src=1, dst=2, type="WORKS_ON", role="Lead", since="2023-01-01"
```

---

## The Three-Layer Architecture

PropWeaver uses a **layered architecture** that separates concerns into three distinct levels:

```
┌─────────────────────────────────────────────┐
│  Core API Layer (core.py)                   │
│  PropertyGraph, NodeProxy, EdgeProxy        │
│  User-facing interface                      │
└──────────────┬──────────────────────────────┘
               │
┌──────────────┴──────────────────────────────┐
│  Query Layer (query.py)                     │
│  QuerySpec, QueryStep, NodeIterator,        │
│  EdgeIterator                               │
│  Declarative query building & lazy eval     │
└──────────────┬──────────────────────────────┘
               │
┌──────────────┴──────────────────────────────┐
│  Storage Layer (storage.py)                 │
│  StorageLayer, TypeMapper                   │
│  SQLite operations & type conversion        │
└─────────────────────────────────────────────┘
```

### Why This Separation?

1. **Clarity** - Each layer has a single responsibility
2. **Testability** - Layers can be tested independently
3. **Maintainability** - Changes to SQL logic don't affect the API
4. **AI Collaboration** - Clear boundaries make it easier for AI tools to understand and modify specific components
5. **Extensibility** - New features often involve adding logic to one layer

### Data Flow: A Node Query Example

To understand how layers work together, let's trace a query operation on the example data above:

```python
## EXAMPLE
# Query active users (matches the data from above)
active_users = graph.nodes("User", active=True)
for user in active_users:
    print(user.prop("name"))  # Prints: Alice
```

**Step 1: Core API** receives the request:
- `PropertyGraph.nodes("User", active=True)` creates a `NodeIterator` with a new `QuerySpec`
- The spec starts with a SOURCE step

**Step 2: Query Layer** builds the plan (no database hit yet):
- The filtering is captured in a FILTER step within the QuerySpec:
  ```
  QuerySpec.steps = [
    QueryStep(type="SOURCE", source_type="User"),
    QueryStep(type="FILTER", properties={"active": True})
  ]
  ```
- Still declarative—the query plan is just a list of steps

**Step 3: Storage Layer** executes only when iteration starts:
- When you call `for user in active_users`, the iterator triggers `StorageLayer._execute_query()`
- The storage layer converts the QuerySpec steps into SQL:
  ```sql
  SELECT * FROM resource
  WHERE type='User' AND active=1
  ```
- Executes the query and yields results
- Returns rows one at a time (lazy evaluation)

**Step 4: Core API** wraps results:
- Each row is wrapped in a `NodeProxy` handle
- When you access `user.prop("name")`, the NodeProxy queries the database for that specific property

This flow demonstrates **lazy evaluation** and **declarative queries**: the query is specified step-by-step, but only executed when needed.

---

### Data Flow: A Node Creation Example

Now let's trace how creation works:

```python
## EXAMPLE
user = graph.add_node("User", name="Alice", active=True)
```

**Step 1: Core API** receives the request:
- `PropertyGraph.add_node()` validates input
- Delegates to the storage layer

**Step 2: Storage Layer** executes immediately (creation can't be lazy):
- Runs INSERT on `resource` table: `(id, type, created_at)`
- Runs INSERT on `resource_props` table: one row per property
  - `(resource_id, key="name", value="Alice", type="str")`
  - `(resource_id, key="active", value=1, type="bool")`
- Returns the created node ID

**Step 3: Core API** wraps it:
- Returns a `NodeProxy` handle to the user
- NodeProxy remembers: graph reference, node_id, and node_type

This demonstrates **eager execution** for mutations: creations can't be deferred.

---

### Data Flow: A Bulk Deletion Example

Finally, let's trace bulk operations using the query system:

```python
## EXAMPLE
# Query then delete nodes matching a condition
# Note: In the example data, there are no inactive users, so this is a no-op
deleted_count = graph.nodes("User", active=False).delete().execute()
print(f"Deleted {deleted_count} inactive users")  # Prints: Deleted 0 inactive users
```

**Step 1: Core API & Query Layer** build the plan:
- `graph.nodes("User", active=False)` creates a NodeIterator with SOURCE and FILTER steps
- `.delete()` adds a DELETE step and returns a DeleteAction object
- **Still no database execution** — just a plan

**Step 2: DeleteAction** holds the plan:
- The delete operation is wrapped in an action object
- Provides `.execute()` method to trigger execution

**Step 3: Storage Layer** executes on `.execute()`:
- `StorageLayer._execute_query()` processes the QuerySpec
- Converts to SQL: `DELETE FROM resource WHERE type='User' AND active=0`
- Cascading deletes (via foreign keys) also remove associated properties and edges
- Returns count of deleted rows (0 in this example, since all users are active)

**Step 4: Transaction safety**:
- All deletes happen in a single transaction
- If anything fails, entire operation rolls back
- If successful, returns count to user
- No-op deletions (0 rows affected) are safe and common

This demonstrates **queryable bulk operations**: you build a query, then execute deletion, with full transaction safety.

---

## Core Design Patterns

Before diving into each layer, understanding these patterns is essential:

### Pattern 1: Proxy Objects (NodeProxy, EdgeProxy)

Instead of loading entire graph structures into memory, PropWeaver uses lightweight **proxy objects**:

```python
## EXAMPLE
user = graph.add_node("User", name="Alice")
# 'user' is a NodeProxy, not a full User object
# It's a lightweight handle: (graph_ref, node_id, node_type)

# When you access properties, it queries the database
name = user.props["name"]  # Database query happens here
```

**Why?**
- Memory efficient for large graphs (don't load what you don't use)
- Always reflects current database state (no stale data)
- Consistent with lazy evaluation philosophy

### Pattern 2: Declarative Query System (QuerySpec + QueryStep)

Instead of generating SQL imperatively, queries are **declaratively specified** as a series of steps:

```python
## EXAMPLE
# User code
senior_engineers = (graph.nodes("User")
                   .filter(department="Engineering")
                   .filter(level="Senior"))

# Behind the scenes: a QuerySpec is built
# QuerySpec has steps like:
# - QueryStep(type="SOURCE", source_type="User")
# - QueryStep(type="FILTER", properties={"department": "Engineering"})
# - QueryStep(type="FILTER", properties={"level": "Senior"})

# Only when iterating does StorageLayer.execute() convert steps → SQL
for engineer in senior_engineers:
    print(engineer.props["name"])
```

**Why?**
- **Human readable** - the code reads like the intent
- **AI friendly** - clear step structure is easier for models to reason about
- **Composable** - build complex queries from simple steps
- **Inspectable** - you can see the query plan before execution
- **Optimizable** - could add query optimization between building and execution

### Pattern 3: Type Mapping (TypeMapper)

Python has rich data types; SQLite doesn't. **TypeMapper** bridges this:

```python
## EXAMPLE
# User code
user.props["tags"] = ["python", "databases", "ai"]  # Python list
user.props["metadata"] = {"role": "engineer"}        # Python dict
user.props["created"] = datetime.now()               # datetime object

# TypeMapper converts to SQLite:
# tags → json | {"value": "[\"python\", \"databases\", \"ai\"]", "type": "list"}
# metadata → json | {"value": "{...}", "type": "dict"}
# created → text | {"value": "2024-01-15T10:30:00", "type": "datetime"}
```

**Why?**
- PropWeaver appears to store any Python type (great UX)
- SQLite stores it efficiently (as JSON for complex types)
- Full type fidelity on retrieval (get back exactly what you put in)

### Pattern 4: Lazy Evaluation with Context Managers

Operations are bundled in transactions naturally:

```python
## EXAMPLE
# Manual transaction
with graph._storage.transaction():
    user1 = graph.add_node("User", name="Alice")
    user2 = graph.add_node("User", name="Bob")
    graph.add_edge(user1, "FRIENDS", user2)
    # Automatically committed here, or all rolled back on error
```

**Why?**
- ACID compliance by default
- Natural to write (matches `with` statement semantics)
- Prevents partial updates on error

---

## Architecture by Layer

Now let's examine each layer in detail.

### Layer 1: Storage Layer (storage.py)

**Responsibility**: All database operations and type conversions

**Key Classes**:

#### TypeMapper
Converts between Python types and SQLite representations:

```
Python Type → SQL Representation
─────────────────────────────────
int         → INTEGER
float       → REAL
str         → TEXT
bool        → INTEGER (0/1)
list        → TEXT (JSON encoded)
dict        → TEXT (JSON encoded)
datetime    → TEXT (ISO format)
None        → NOT STORED (field absence indicates None)
```

The key insight: **complex types become JSON**, which is queryable in SQLite.

#### StorageLayer
All SQL operations flow through here:

```
_add_node()         → INSERT into resource, resource_props
_add_edge()         → INSERT into rel, rel_props
_query_nodes()      → SELECT from resource JOIN resource_props
_query_edges()      → SELECT from rel JOIN rel_props
_delete_nodes()     → DELETE from resource (cascading)
_delete_edges()     → DELETE from rel (cascading)
_set_property()     → INSERT/UPDATE/DELETE on *_props tables
transaction()       → context manager for ACID operations
```

**Design Note**: All methods use single underscore prefix (`_method_name()`) indicating they're internal APIs. Never call these directly; use the public API via PropertyGraph and iterators.

**Why This Design?**
- Centralized SQL knowledge (easier to optimize or migrate)
- All type conversion in one place (consistency)
- Transaction boundaries clear (one method owns transaction logic)
- AI tools can reason about "what executes SQL" by looking at this module

### Layer 2: Query Layer (query.py)

**Responsibility**: Declarative query specification and lazy evaluation

**Key Classes**:

#### QuerySpec and QueryStep
A query is a sequence of steps:

```python
...
class QueryStep(TypedDict):
    type: Literal["SOURCE", "FILTER", "TRAVERSE", "DELETE", ...]
    # Other fields depend on type, e.g.:
    # FILTER: properties: dict
    # DELETE: none (just remove matching items)

class QuerySpec:
    steps: list[QueryStep]  # The execution plan
...
```

#### NodeIterator and EdgeIterator
Lazy evaluation with method chaining:

```python
...
# Each method returns a new iterator with an updated QuerySpec
class NodeIterator:
    def filter(self, **properties) -> NodeIterator:
        new_spec = self.query_spec.copy()
        new_spec.steps.append(QueryStep(type="FILTER", properties=properties))
        return NodeIterator(self.graph, new_spec)

    def delete(self) -> DeleteAction:
        # Returns an action object, doesn't execute yet
        return DeleteAction(self)

    def __iter__(self):
        # Executes the query plan when iteration starts
        return self.graph._storage._execute_query(self.query_spec)
...
```

**Why This Design?**
- **Composability**: `graph.nodes("User").filter(active=True).filter(role="Senior")` builds a query step-by-step
- **Laziness**: No database hit until you iterate or call `.execute()`
- **Inspectability**: You could print the QuerySpec to see what will be executed
- **AI friendly**: Clear steps make it easier for models to suggest/understand queries

**Extending the Query System**:

To add a new query capability (e.g., ordering):

1. Add to the QueryStep type union in query.py:
   ```python
...
   type: Literal["SOURCE", "FILTER", "TRAVERSE", "ORDER", "DELETE", "MY_NEW_TYPE"]
...
   ```

2. Add method to iterator:
   ```python
...
   def order_by(self, field: str) -> NodeIterator:
       new_spec = self.query_spec.copy()
       new_spec.steps.append(QueryStep(type="ORDER", field=field))
       return NodeIterator(self.graph, new_spec)
...
   ```

3. Handle in StorageLayer execution:
   ```python
...
   elif step.type == "ORDER":
       # Build SQL ORDER BY clause
       query_sql += f" ORDER BY {step['field']}"
...
   ```

### Layer 3: Core API Layer (core.py)

**Responsibility**: User-facing interface and entity proxies

**Key Classes**:

#### PropertyGraph
The main entry point:

```python
## EXAMPLE
with PropertyGraph("my_graph.db") as graph:
    # graph.add_node() - delegates to StorageLayer
    # graph.add_edge() - delegates to StorageLayer
    # graph.nodes() - returns NodeIterator
    # graph.edges() - returns EdgeIterator
    # graph.set_prop() - delegates to StorageLayer
    # graph.props - dict-like interface
```

#### NodeProxy and EdgeProxy
Lightweight handles to entities:

```python
## EXAMPLE
user = graph.add_node("User", name="Alice")
# user is a NodeProxy with:
# - user.node_id (the ID in the database)
# - user.props (PropertyDict for properties)
# - user.to_json() (export as dict)
# - user.timestamp() (creation time)
```

#### PropertyDict
Dict-like interface hiding database operations:

```python
## EXAMPLE
# These all trigger database operations:
name = user.props["name"]          # SELECT
user.props["name"] = "Alice2"      # UPDATE
del user.props["name"]             # DELETE
"name" in user.props               # SELECT (check existence)
```

**Why This Design?**
- **Pythonic**: Using standard Python interfaces (`with`, `[]`, `in`, iteration)
- **User-friendly**: No awareness of layers below
- **Testable**: Can mock StorageLayer for unit tests
- **AI-friendly**: Familiar patterns that models understand

---

## Design for AI Collaboration

PropWeaver was designed with AI-assisted development specifically in mind. This section explains those choices.

### 1. Zero External Dependencies

**The Choice**: Use only Python standard library (sqlite3, json, datetime, etc.)

**Why This Matters for AI**:
- When an AI tool reads the code, it sees only standard library functions
- No need for the AI to understand third-party library APIs
- Reduced context needed to understand any function
- Makes generated code more likely to be correct (less hallucination risk)
- Easier to reason about what code does without external documentation

**Example of the benefit**:
```python
## EXAMPLE
# AI sees this and knows exactly what it does
import json
data = json.loads(stored_json)

# AI has to guess at this (if using external library)
import pandas
df = pandas.read_json(data)
```

### 2. Declarative Query System (The Hidden AI Superpower)

**The Choice**: QuerySpec with steps instead of imperative SQL generation

**Why This Matters for AI**:

This design choice is **critical for AI collaboration** for several reasons:

#### A. Fluent, Human-Readable Syntax

```python
## EXAMPLE
# This reads like natural thought, not like a query language
senior_engineers = (graph.nodes("User")
                   .filter(department="Engineering")
                   .filter(level="Senior")
                   .order_by("name"))

# Even downstream projects using AI tools benefit from this
# AI can suggest: "use graph.nodes('X').filter(...)"
# instead of having to understand SQL generation patterns
```

This fluent interface **plays extremely well** with downstream projects that also use AI tools. A student's AI assistant can suggest PropWeaver code using patterns it understands (method chaining, filter operations) rather than having to understand internal query generation.

#### B. Module Boundary "Fencing" for AI Assistants

The declarative QuerySpec design creates **strong boundary contracts** that keep AI code generation in tight bounds:

```
Core API Layer (core.py)
    ↓ clearly defined interface: returns NodeIterator
Query Layer (query.py)
    ↓ QueryStep is the contract: all modifications add steps
Storage Layer (storage.py)
    ↓ executes steps, only step types it knows about
```

When you ask an AI to "add ordering capability":
- **Without this design**: AI might modify SQL strings everywhere, touch query building, modify the API simultaneously. Changes scattered, hard to test, easy to break things.
- **With this design**: AI *must* follow a clear path:
  1. Add "ORDER" to the QueryStep type
  2. Add method to NodeIterator
  3. Handle in StorageLayer

Each step is:
- ✅ Obviously testable (one test per step)
- ✅ Isolated from other code (won't break unrelated features)
- ✅ Obvious what changed (clear PR diff)
- ✅ Easy to review (small, focused changes)

**This is crucial**: High cohesion and low coupling prevent AI from accidentally changing too much. Strong boundary contracts mean that when something *needs* to change, it's an obvious, testable, step-wise change.

#### C. Structured Representation for Reasoning

```python
## EXAMPLE
# The AI can reason about this structure
QuerySpec(steps=[
    QueryStep(type="SOURCE", source_type="User"),
    QueryStep(type="FILTER", properties={"active": True}),
    QueryStep(type="ORDER", field="name")
])

# Rather than having to understand and reason about SQL strings
"SELECT * FROM resource WHERE type='User' AND ... ORDER BY ..."
```

#### D. Composability

```python
## EXAMPLE
# An AI can reason about building queries incrementally
base_query = graph.nodes("User")
filtered = base_query.filter(active=True)
ordered = filtered.order_by("name")

# Each step adds one QueryStep. Predictable. Testable. Clean.
```

**Why This Matters**:
- **Human readable intent**: `nodes("User").filter(active=True)` is clearer than SQL
- **Structured representation**: QueryStep is a dict/dataclass, easier for AI to reason about
- **Composable**: Building queries from steps is a clear pattern
- **Inspectable**: You can examine the query plan before execution
- **Generatable**: AI can generate QueryStep structures without knowing SQL
- **Fluent for downstream**: Other projects (especially AI-assisted ones) see clean, readable code patterns to follow
- **Fenced for AI extensions**: AI modifications follow clear, testable boundaries

### 3. Clear Module Boundaries

**The Choice**: Three distinct, well-separated modules (storage.py, query.py, core.py)

**Why This Matters for AI**:
- When modifying one module, the AI understands what it shouldn't change
- Storage layer changes don't affect query layer
- API changes can be made without touching SQL
- AI can focus on the relevant module for a change

**Example workflow**:
```
User: "I want to add query result ordering"
AI: "I'll modify query.py to add an OrderStep, then update storage.py to handle it"
    Rather than: "I'll search the entire codebase for where queries happen"
```

### 4. Comprehensive Testing

**The Choice**: Extensive test coverage with clear test organization

**Why This Matters for AI**:
- Tests serve as executable specification (what should happen?)
- AI can read tests to understand expected behavior
- When AI generates code, it can run tests for validation
- Test failures provide precise feedback

**Test organization** (`tests/`):
```
test_query.py          - Query building and lazy evaluation
test_crud.py           - Node/edge creation, reading, updating
test_bulk_operations.py - Deletions, batch operations
test_integration.py    - End-to-end scenarios
```

### 5. CLAUDE.md and Development Instructions

**The Choice**: Explicit guidance file for AI tool collaboration (Claude Code specific, might need adaptation for other systems)

**Key Points from CLAUDE.md**:
- Emoji style guide for concise, token-efficient logging
- Preference for brief test output (`./bin/test.sh brief`)
- Clear approach: "clean, maintainable, readable code that sets the standard"
- Emphasis on keeping tests in sync with implementation
- Use TODO.md to track work across sessions

**Why This Matters**:
- AI tools have token budgets; emojis are dense communication
- Brief test output means faster feedback loops
- Explicit standards help AI generate code that matches the project's philosophy
- TODO.md is a continuation mechanism across sessions

### 6. Logging with Token Efficiency

**The Choice**: Custom SUMMARY log level with emoji messages

**Why This Matters for AI**:
- `✅ INSERT (2.1ms)` communicates status in 3 tokens
- Same information as "Successfully inserted node in 2.1 milliseconds" (9 tokens)
- In AI workflows with token limits, every word matters
- Consistent emoji use helps parsing tool output

### 7. Proxy Pattern for Memory Efficiency

**The Choice**: NodeProxy/EdgeProxy as lightweight handles, not full object copies

**Why This Matters for AI**:
- When an AI tool reasons about "what happens when I modify a node," it's clear that changes go to database
- No confusion about stale copies in memory
- Simpler mental model for the AI (and humans): proxies are handles, not objects

---

## Thinking Like a Maintainer

As a maintainer of PropWeaver (or a student working on it), here's how to approach problems.

### The Mental Model

Think of PropWeaver as three separate concerns:

1. **What should happen?** (Core API / user perspective)
2. **How should we build it?** (Query system / specification)
3. **How do we execute it?** (Storage / SQL)

When a feature request or bug comes in, ask:
- Is this about the API? → Modify core.py and update tests
- Is this about how queries work? → Modify query.py and update tests
- Is this about SQL execution? → Modify storage.py and update tests

### Common Modification Patterns

#### Pattern A: Adding a New Query Operation

Example: Add ordering/sorting to queries

**Steps**:
1. Update the QueryStep type in query.py:
   ```python
...
   type: Literal["SOURCE", "FILTER", "TRAVERSE", "ORDER", "DELETE"]
...
   ```

2. Add method to NodeIterator/EdgeIterator:
   ```python
...
   def order_by(self, field: str) -> NodeIterator:
       new_spec = self.query_spec.copy()
       new_spec.steps.append(QueryStep(type="ORDER", field=field))
       return NodeIterator(self.graph, new_spec)
...
   ```

3. Handle in StorageLayer._execute_query():
   ```python
...
   elif step.type == "ORDER":
       query_sql += f" ORDER BY {step['field']}"
...
   ```

4. Add tests:
   ```python
## EXAMPLE
   def test_order_by_ascending(graph):
       results = list(graph.nodes("User").order_by("name"))
       # assertions...
   ```

#### Pattern B: Adding a New Property Type

Example: Support datetime objects natively

**Steps**:
1. Extend TypeMapper.to_sqlite() in storage.py
2. Extend TypeMapper.from_sqlite() in storage.py
3. Add tests in test_types.py
4. Document in README.md

#### Pattern C: Fixing a Bug

**Process**:
1. Write a test that reproduces the bug (should fail)
2. Trace the bug through the three layers
3. Fix in the appropriate layer
4. Run tests to verify

### Reading the Code with Purpose

When you need to understand a feature:

1. **Start at the API** (core.py): How does the user interact with it?
2. **Follow to Query** (query.py): How is the intent specified?
3. **Trace to Storage** (storage.py): How is it executed?

This top-down approach is faster than bottom-up.

### Working with AI Tools on This Codebase

PropWeaver is designed to work well with AI-assisted development. Here's how:

**When asking AI to modify code**:
- Specify which layer(s) need changes (storage, query, or core)
- Explain the before/after behavior (not just "add feature X")
- Ask AI to show the test it would write first
- Request that tests be updated alongside implementation

**Example prompt**:
```
In the query layer, I'd like to add an order_by() method that
orders results by a property. Show me:
1. The test that verifies this works
2. The change to query.py
3. The change to storage.py to handle ORDER steps

Before implementing, show me the test you'd write.
```

**When reviewing AI-generated changes**:
- Verify tests were updated
- Check that the change is isolated to one layer (or clearly spans necessary layers)
- Ensure no new dependencies were added
- Run the test suite (including new tests)

### The Development Workflow

Typical workflow for a change:

```
1. Understand the feature (read ARCHITECTURE.md, relevant code)
2. Write the failing test (tests/)
3. Implement the feature (the three layers, as needed)
4. Run tests: ./bin/test.sh brief
5. Update TODO.md if discovering new work
6. Commit with reference to what was implemented
```

---

## Key Design Decisions & Trade-offs

Understanding *why* certain choices were made helps you recognize when to follow patterns and when to break them.

### Decision 1: Properties in Separate Tables vs. JSON

**Choice**: Store properties in separate `*_props` tables

**Alternatives Considered**:
- Store as JSON column: `resource.props = '{"name": "Alice", "age": 30}'`
- Store as individual columns per type: `resource.name`, `resource.age`

**Why separate tables**:
- ✅ Properties are queryable (`WHERE property_value > 30`)
- ✅ Type information is preserved
- ✅ No need to know property names in advance (schema-flexible)
- ✅ Easy to add/remove properties without migrations
- ❌ More queries needed (join on properties)
- ❌ More database tables
- ❌ Slightly slower for "get all properties" operations

**Trade-off**: Flexibility and query power over raw performance

### Decision 2: Lazy Evaluation with QuerySpec

**Choice**: Build query plans declaratively, execute on iteration

**Alternatives Considered**:
- Eager execution: Execute queries immediately when methods called
- SQL builder: Generate SQL directly, no intermediate representation

**Why lazy + QuerySpec**:
- ✅ Composable: can build queries step-by-step
- ✅ Inspectable: can see the plan before execution
- ✅ Extensible: easy to add new steps
- ✅ AI-friendly: clear structure for reasoning
- ✅ **Fluent syntax**: reads naturally, plays well with downstream AI-assisted projects
- ✅ **High cohesion, low coupling**: Module boundaries keep AI code generation contained and testable
- ❌ Slightly harder to understand for beginners
- ❌ Additional abstraction layer

**Trade-off**: Flexibility and clarity over simplicity

### Decision 3: Proxy Objects Instead of Full Loads

**Choice**: NodeProxy/EdgeProxy as lightweight handles

**Alternatives Considered**:
- Load entire node with properties into memory
- Load on-demand from proxies (current approach)

**Why proxies**:
- ✅ Memory efficient for large graphs
- ✅ Always reflects current DB state
- ✅ Clear semantics (proxy = handle to entity)
- ❌ Must query DB for each property access
- ❌ Slightly more complex caching model

**Trade-off**: Memory and correctness over access performance

### Decision 4: Dict-like Property Interface

**Choice**: `node.props["name"]` instead of `node.name` or `node.get_property("name")`

**Alternatives Considered**:
- Attribute access: `node.name` (dynamic attributes)
- Method calls: `node.get_property("name")`
- TypedDict: specific properties per type

**Why dict-like**:
- ✅ Pythonic (matches dict interface)
- ✅ Works for any property (schema-flexible)
- ✅ Consistent with PropertyGraph.props
- ✅ All edge cases handled (None values, missing keys, etc.)
- ❌ No IDE autocomplete for property names
- ❌ No compile-time type checking

**Trade-off**: Flexibility and ease-of-use over IDE support

### Decision 5: SQLite as the Storage Backend

**Choice**: SQLite over in-memory, file-based alternatives

**Alternatives Considered**:
- In-memory dict-based graph
- Other SQL databases (PostgreSQL, MySQL)
- NoSQL databases (MongoDB, etc.)

**Why SQLite**:
- ✅ Zero external dependencies (bundled with Python)
- ✅ ACID transactions
- ✅ Good performance for single-process use
- ✅ Easy to inspect (`.db` file can be opened directly)
- ❌ No multi-process access (WAL mode helps but limited)
- ❌ Not ideal for very large graphs (terabytes+)

**Trade-off**: Simplicity and zero-dependency design over scalability

### Decision 6: Type Serialization Strategy

**Choice**: Complex types as JSON, with type metadata

**Alternatives Considered**:
- Pickle (Python-specific serialization)
- Protocol Buffers (more complex)
- Plain JSON (loss of type information)

**Why JSON + type metadata**:
- ✅ Human readable (can inspect `.db` file)
- ✅ Language-agnostic (could access from other languages)
- ✅ Type fidelity preserved (get back what you put in)
- ✅ Web-friendly (JSON is standard)
- ❌ Slightly more storage (metadata overhead)
- ❌ Some types don't serialize well (custom objects)

**Trade-off**: Clarity and compatibility over conciseness

---

## Summary: The PropWeaver Philosophy

PropWeaver's architecture embodies these principles:

1. **Clarity Over Cleverness** - Three clear layers, not magic
2. **Pythonic Design** - Uses familiar Python patterns (`with`, iteration, dicts)
3. **AI Collaboration** - Zero dependencies, clear structure, comprehensive tests
4. **Flexibility** - Schema-free properties, composable queries
5. **Transparency** - You understand what's happening at each layer
6. **Testing** - Extensive tests as both validation and documentation

When extending or maintaining PropWeaver, ask yourself:
- Does this follow existing patterns?
- Is the change isolated to one layer?
- Are tests updated alongside code?
- Would an AI tool understand this code?
- Is there a simpler approach?

These questions will keep the codebase healthy and maintainable.

---

## Next Steps for Learning

1. **Read the code in order**: core.py → query.py → storage.py
2. **Run the examples**: `./bin/examples.sh` to see real usage
3. **Examine the tests**: Start with `tests/test_crud.py`
4. **Extend a feature**: Add a new query operation using the patterns shown here
5. **Refer to DESIGN_DECISIONS.md**: For deeper dives into specific choices
6. **Check AI_COLLABORATION.md**: For working effectively with AI tools on this codebase
