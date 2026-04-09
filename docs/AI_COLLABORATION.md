# Working with AI Tools on PropWeaver

This guide explains how to effectively collaborate with AI-assisted development tools (like Claude Code) on the PropWeaver codebase. It covers prompting strategies, review practices, and workflows that work well with the codebase's architecture.

## Table of Contents

1. [Why PropWeaver Works Well with AI Tools](#why-propweaver-works-well-with-ai-tools)
2. [Getting AI Oriented to the Codebase](#getting-ai-oriented-to-the-codebase)
3. [Effective Prompting Patterns](#effective-prompting-patterns)
4. [How the Architecture Helps (and Constrains) AI](#how-the-architecture-helps-and-constrains-ai)
5. [Code Review for AI-Generated Changes](#code-review-for-ai-generated-changes)
6. [Iterative Development Workflows](#iterative-development-workflows)
7. [Common Pitfalls and How to Avoid Them](#common-pitfalls-and-how-to-avoid-them)
8. [Using CLAUDE.md and TODO.md](#using-claudemd-and-todomd)

---

## Why PropWeaver Works Well with AI Tools

PropWeaver was deliberately designed with AI collaboration in mind. Understanding why helps you work more effectively with AI tools.

### 1. Zero Dependencies = Reduced Hallucination

**The Benefit**:
AI tools hallucinate less when they don't have to reason about external library APIs.

```python
## EXAMPLE
# PropWeaver (AI can understand this)
import json
data = json.loads(stored_value)

# vs. System with many dependencies (AI might guess)
import pandas
df = pandas.read_json(stored_value)  # Is this the right function? Signature?
```

**For You**: When asking AI to modify code, mention this is a dependency-free project.

### 2. Clear Layer Boundaries = Contained Changes

**The Benefit**:
The three-layer architecture keeps AI changes focused and testable.

```
Core API (core.py)  ←→ Query Layer (query.py) ←→ Storage (storage.py)
Clear contracts between layers
```

**For You**: When asking AI to add a feature, specify which layer(s) it touches. AI is much more likely to stay focused.

### 3. Declarative Query System = Understandable Structures

**The Benefit**:
AI can reason about QuerySpec and QueryStep clearly.

```python
## EXAMPLE
# AI understands this structure
QueryStep(type="FILTER", properties={"active": True})

# AI might misunderstand this
# "SELECT * FROM resource WHERE active = 1"  (could be wrong SQL)
```

**For You**: The query system makes it easy to ask AI to add new operations without worrying about SQL generation bugs.

### 4. Comprehensive Tests = Validation & Feedback

**The Benefit**:
Tests provide immediate, precise feedback to AI about whether code is correct.

```bash
# AI generates code
./bin/test.sh brief
# Test output tells AI exactly what's wrong
```

**For You**: Always ask AI to write tests first, then implementation.

### 5. Explicit Development Instructions (CLAUDE.md)

**The Benefit**:
Clear standards mean AI-generated code matches project style.

CLAUDE.md includes:
- Emoji style guide (token efficiency)
- Testing philosophy
- Code quality standards
- Integration instructions

**For You**: Reference CLAUDE.md when setting expectations for AI collaboration.

---

## Getting AI Oriented to the Codebase

Before asking AI to make changes, provide context. Here's an effective orientation sequence:

### Step 1: Provide the Architecture Overview

**What to share**:
```
"This codebase has three layers:
1. Core API (core.py) - user-facing interface
2. Query Layer (query.py) - builds QuerySpec objects
3. Storage Layer (storage.py) - executes SQL

For this change, I want to modify [which layer(s)]."
```

Or just reference the document:
```
"Read docs/ARCHITECTURE.md to understand the three-layer system,
then let me know what you think about how to implement [feature]."
```

### Step 2: Show Relevant Code Examples

When asking AI to modify something, provide a working example:

```
"Here's how nodes() works (in core.py):
```python
...
def nodes(self, node_type: str | None = None, **properties):
    return NodeIterator(self, QuerySpec(steps=[...]))
...
```

I want to add an order_by() method that works similarly.
Show me:
1. What test would verify this works?
2. The change to query.py?
3. The change to storage.py?"
```

### Step 3: Set Expectations About Tests

Be explicit:
```
"Before writing implementation code, write a test that shows
what order_by() should do. Show me the test first."
```

### Step 4: Reference Patterns

Point to similar code:
```
"Look at how filter() works in query.py for reference.
I want order_by() to work the same way (immutable, returns new iterator)."
```

---

## Effective Prompting Patterns

### Pattern 1: Ask for Test First

**Good Prompt**:
```
I want to add support for ordering results by a property.

First, write a test that shows how this should work:
- Create some users with a name property
- Call order_by("name") on a node iterator
- Verify the results are sorted alphabetically

Just show me the test, don't implement yet.
```

**Why This Works**:
- Test clarifies intent before implementation
- AI sees what should happen before writing code
- You can review expected behavior before implementation

### Pattern 2: Specify Which Layer(s)

**Good Prompt**:
```
I'd like to add support for ordering results.

This will require changes to:
1. query.py - add order_by() method to NodeIterator
2. storage.py - handle ORDER step type in execution

Please modify these two files to add ordering.
Show me the changes to each layer.
```

**Why This Works**:
- Prevents AI from changing unrelated files
- Makes review easier (know what to expect)
- Aligns with architecture

### Pattern 3: Show Before/After Behavior

**Good Prompt**:
```
Before: graph.nodes("User").filter(active=True)
After: graph.nodes("User").filter(active=True).order_by("name")

The order_by() method should:
- Accept a field name (string)
- Return a new NodeIterator (immutable pattern)
- Add an ORDER QueryStep to the QuerySpec

Implement this in query.py and storage.py.
```

**Why This Works**:
- Clear input/output
- Shows expected API
- Demonstrates composability

### Pattern 4: Ask for Explanation First

**Good Prompt**:
```
Here's the codebase structure [share ARCHITECTURE.md excerpt].

Before implementing [feature], explain:
1. Which layer(s) will you modify?
2. How will you modify them?
3. What tests would verify it works?

Then, implement it.
```

**Why This Works**:
- AI explains reasoning before coding
- You can catch issues early
- Shows the thought process

### Pattern 5: Reference Existing Code

**Good Prompt**:
```
In query.py, I see that filter() works like this:
[paste filter() implementation]

I want to add order_by() that works the same way.
Show me the code for order_by() in query.py.
Then show how storage.py should handle ORDER steps.
```

**Why This Works**:
- AI learns from existing patterns
- Consistency is automatic
- Less room for deviation

### Pattern 6: Bound the Change

**Good Prompt**:
```
Add order_by() to query.py and storage.py only.
Don't modify:
- core.py
- Any test files yet

Just the implementation in those two files.
```

**Why This Works**:
- Prevents scope creep
- Easier to review
- Clear boundaries

---

## How the Architecture Helps (and Constrains) AI

Understanding the architecture helps you work with its constraints.

### Constraint 1: Module Boundaries

**The Constraint**:
Changes should respect layer boundaries. A feature shouldn't span all three layers unnecessarily.

**Example - Good**:
```
Feature: Add ordering
Changes:
- query.py: Add order_by() method
- storage.py: Handle ORDER step
Result: Two focused, testable changes
```

**Example - Bad**:
```
Feature: Add ordering
Changes:
- core.py: Add parameter to nodes()
- query.py: Build QueryStep
- storage.py: Handle step
Result: Three changes to implement one feature
```

**For You**: If AI proposes changes across all three layers for a simple feature, ask: "Can this be done in fewer layers?"

### Constraint 2: QueryStep Types Are Finite

**The Constraint**:
New QueryStep types must be explicitly defined in query.py.

```python
...
# In query.py, the union of allowed types:
type: Literal["SOURCE", "FILTER", "TRAVERSE", "ORDER", "DELETE", ...]
...
```

**For You**: When asking AI to add a new query operation, remind it:
```
"Add ORDER to the QueryStep type union in query.py,
then implement order_by() in NodeIterator,
then handle it in StorageLayer._execute_query()"
```

### Constraint 3: Private API Boundary

**The Constraint**:
All storage operations go through StorageLayer methods (prefixed with `_`).

```python
...
# Good
storage._add_node(...)
storage._set_property(...)

# Bad (reaches into internals)
cursor.execute("INSERT INTO resource ...")
...
```

**For You**: If AI generates code that bypasses StorageLayer, ask it to use the StorageLayer methods instead.

### How Constraints Help

These constraints actually make AI better:

1. **Fewer hallucinations** - "What code could go here?" is bounded
2. **Easier review** - "This looks like a typical QueryStep handler"
3. **Safer changes** - Limited scope means lower risk

---

## Code Review for AI-Generated Changes

When reviewing AI-generated changes, focus on what matters.

### Checklist for AI-Generated Code

#### ✅ Architecture

- [ ] Change respects layer boundaries (doesn't unnecessarily span layers)
- [ ] Change is isolated to appropriate module(s)
- [ ] Uses existing patterns (doesn't introduce new patterns)

#### ✅ Tests

- [ ] Tests are written
- [ ] Tests verify behavior (not implementation)
- [ ] Tests pass
- [ ] Tests are readable and clear

#### ✅ Code Quality

- [ ] Follows existing style (emojis in logging, naming patterns, etc.)
- [ ] Has clear comments where non-obvious
- [ ] No new dependencies introduced
- [ ] No private APIs used inappropriately

#### ✅ Completeness

- [ ] Implementation matches the proposal
- [ ] Docstrings updated if needed
- [ ] Related tests updated (e.g., integration tests)

#### ✅ Safety

- [ ] No SQL injection risks
- [ ] Handles edge cases (empty results, None values, etc.)
- [ ] Transactions used where needed
- [ ] Doesn't break existing functionality

### Red Flags in AI-Generated Code

**🚩 Adds External Dependency**
```python
## EXAMPLE
import pandas  # Should ask: why?
```

**🚩 Bypasses StorageLayer**
```python
## EXAMPLE
cursor.execute("...")  # Should use storage methods
```

**🚩 Implements Public API in Wrong Layer**
```python
...
# In storage.py
class StorageLayer:
    def order_by(self, field):  # Should be in query.py
...
```

**🚩 Changes Multiple Unrelated Things**
```
# Commit includes:
- Add ordering (requested)
- Refactor type handling (not requested)
- Rename variables (not requested)

# Scope creep! Ask AI to focus.
```

**🚩 Ignores Existing Patterns**
```python
...
# Current pattern: immutable (returns new iterator)
def filter(self):
    new_spec = self.query_spec.copy()
    new_spec.steps.append(...)
    return NodeIterator(...)

# AI does:
def order_by(self):
    self.query_spec.steps.append(...)  # Mutating!
    return self
...
```

**🚩 Missing Tests**
```
"Here's the implementation of feature X"
# But no tests shown
# Ask: "What test validates this works?"
```

### When to Push Back

Be willing to reject or ask for revision:

```
"I see you implemented order_by() in storage.py,
but similar methods like filter() are in query.py.
Let's keep related methods together - can you move it?"
```

```
"The code works, but I don't see a test for the edge case
where there are no results to order. Can you add that?"
```

```
"You added a new dependency (requests). We want zero dependencies.
Can you implement this another way?"
```

---

## Iterative Development Workflows

Here's how to structure multi-step projects with AI tools.

### Workflow A: Small Feature (1-2 Steps)

```
1. Propose feature to AI
2. Ask AI to sketch approach (which files? which methods?)
3. Review approach with AI
4. Ask AI to write test
5. Review test
6. Ask AI to implement
7. Run tests
8. Review code
9. Ask for any needed fixes
10. Commit
```

### Workflow B: Medium Feature (3+ Steps)

Use TODO.md:

```markdown
## In Progress: Add ordering capability

- [ ] Write test for order_by()
- [ ] Add ORDER to QueryStep type in query.py
- [ ] Add order_by() method to NodeIterator
- [ ] Handle ORDER step in StorageLayer
- [ ] Add integration test
- [ ] Update README with example
```

Then work through items:

```
AI: "I'm ready to start. What's first?"
You: "Start with the test from task 1.
Show me a test that verifies order_by('name') returns results sorted."
AI: [writes test]
You: "Good, I'll move to task 2. Add ORDER to the QueryStep type."
AI: [modifies query.py]
You: [review] "Good. Now task 3: implement order_by()."
AI: [implements]
You: ./bin/test.sh brief
# ✅ All tests pass
You: [review code, then] "Great! Move to task 4: storage layer."
AI: [implements storage handling]
You: ./bin/test.sh brief
# ✅ Integration tests pass
You: "Perfect. Merge this change."
```

### Workflow C: Complex Refactoring

```
1. Explain what you want to refactor and why
2. Ask AI to propose approach (don't just do it)
3. Review proposal
4. Ask AI to make changes incrementally
5. After each change, run tests
6. Review for regressions
7. Commit when all tests pass
```

### Workflow D: Bug Fix

```
1. Ask AI to write a test that reproduces the bug
2. Verify test fails (proves bug exists)
3. Ask AI to find the bug (trace through code)
4. Review proposed fix
5. Ask AI to implement fix
6. Verify test passes
7. Run full test suite (verify no regressions)
8. Review fix
9. Commit
```

---

## Common Pitfalls and How to Avoid Them

### Pitfall 1: "Do Everything"

**The Problem**:
```
You: "Add ordering to the query system"
AI: [modifies core.py, query.py, storage.py, adds examples, updates README, ...]
Result: Hard to review, changes everywhere
```

**The Fix**:
Be specific about scope:
```
"Add ordering to the query system.

Start with:
1. The test in tests/test_query.py
2. Modifications to query.py only

Don't modify: core.py, storage.py, examples, README (yet)."
```

### Pitfall 2: "No Tests"

**The Problem**:
```
AI: [writes implementation]
You: [no way to verify it works]
```

**The Fix**:
Always ask for tests first:
```
"First, write a test that shows order_by() working.
Then implement to pass the test."
```

### Pitfall 3: "Lost in Complexity"

**The Problem**:
```
Feature requires 10 steps. You ask AI to do all at once.
AI gets confused, produces poor code.
```

**The Fix**:
Break into pieces, use TODO.md:
```markdown
- [ ] Step 1: Write test
- [ ] Step 2: Add type to union
- [ ] Step 3: Add method
- [ ] Step 4: Handle in storage
- [ ] Step 5: Test integration
```

Work through one at a time.

### Pitfall 4: "Scope Creep"

**The Problem**:
```
You ask for ordering. AI refactors type handling, renames variables, ...
```

**The Fix**:
Be explicit about what not to change:
```
"Add ordering. Don't:
- Refactor existing code
- Rename variables
- Change anything except what's needed for ordering"
```

### Pitfall 5: "No Context"

**The Problem**:
```
You: "Add a new feature"
AI: [makes changes that don't fit architecture]
```

**The Fix**:
Provide context:
```
"Here's the architecture: [excerpt from ARCHITECTURE.md]
The pattern for similar features is: [show example code]
Please follow this pattern."
```

### Pitfall 6: "Ignoring Existing Patterns"

**The Problem**:
```
filter() uses immutable pattern (returns new iterator)
AI implements order_by() with mutable pattern (modifies self)
```

**The Fix**:
Point to patterns:
```
"Look at filter() in query.py - it returns a new iterator.
order_by() should use the same pattern."
```

---

## Using CLAUDE.md and TODO.md

PropWeaver has two special files for AI collaboration:

### CLAUDE.md

This file contains guidance for Claude Code specifically. It includes:
- Approach: "Clean, maintainable, readable code"
- Emoji style guide (token efficiency)
- Development commands
- API reference
- Best practices

**For You**:
- Reference it when setting expectations
- Update it as you establish new patterns
- Use the emoji guide for your own code

**When to Extend**:
Add new guidance if you discover:
- A pattern that works well with AI tools
- A common mistake that AI makes
- A better way to structure something

### TODO.md

This file tracks work across sessions.

**Use it when**:
- Working on multi-step features
- Want continuity across sessions
- Need to hand off to someone else
- Planning future work

**Pattern**:
```markdown
## In Progress: Feature X

- [ ] Implement test
- [ ] Modify query.py
- [ ] Modify storage.py
- [ ] Integration testing

## Blocked: Feature Y

- [ ] Waiting on decision about API

## Completed

- [x] Completed feature
```

**For AI Collaboration**:
Tell AI to reference TODO.md:
```
"Check TODO.md for what we're working on.
Next item is: [item]. Here's what needs to happen..."
```

---

## Quick Reference: Prompting Template

Here's a template for effective prompts:

```
Context:
[Explain what you're trying to do and why]

Architecture:
[Reference ARCHITECTURE.md or explain which layer(s) you're modifying]

Current Code:
[Show relevant existing code]

Desired Behavior:
[Before/after or explicit expected behavior]

Steps:
1. [First thing - usually write a test]
2. [Second thing - usually modify query.py or core.py]
3. [Third thing - usually modify storage.py if needed]

Constraints:
- Don't modify [files you don't want changed]
- Follow existing patterns (reference specific pattern)
- Include tests

First, [ask for what you want first]:
"Show me the test for this feature"
```

---

## Example: Adding a Real Feature

Here's a real example of working with AI on PropWeaver.

### Scenario: Add `limit()` to Queries

**Step 1: Propose to AI with Context**

```
I'd like to add a limit() method to queries.

Current: graph.nodes("User").filter(active=True)
Desired: graph.nodes("User").filter(active=True).limit(10)

The method should:
- Accept an integer count
- Return the same number of results
- Work with filters/ordering

Here's the architecture: [excerpt from ARCHITECTURE.md]

Before you implement, write a test in tests/test_query.py
that shows how limit() should work.
```

**Step 2: Review Test**

AI provides:
```python
## EXAMPLE
def test_limit_returns_specified_count(graph):
    # Create 20 users
    for i in range(20):
        graph.add_node("User", name=f"User{i}")

    # Limit to 5
    limited = list(graph.nodes("User").limit(5))
    assert len(limited) == 5

def test_limit_with_filter(graph):
    # Create 10 active users, 10 inactive
    for i in range(10):
        graph.add_node("User", name=f"Active{i}", active=True)
    for i in range(10):
        graph.add_node("User", name=f"Inactive{i}", active=False)

    # Filter then limit
    limited = list(graph.nodes("User")
                  .filter(active=True)
                  .limit(5))
    assert len(limited) == 5
```

**You**: "Perfect, these tests are clear. Now implement it."

**Step 3: Implement**

You ask:
```
Now implement limit() following the pattern of filter().

Modify:
1. query.py - add LIMIT to QueryStep type, add limit() method
2. storage.py - handle LIMIT step in _execute_query()

Show me both changes.
```

AI provides changes to both files.

**Step 4: Review**

```python
...
# query.py looks good - follows filter() pattern
def limit(self, count: int) -> NodeIterator:
    new_spec = self.query_spec.copy()
    new_spec.steps.append(QueryStep(type="LIMIT", count=count))
    return NodeIterator(self.graph, new_spec)

# storage.py looks good - adds LIMIT to SQL
elif step.type == "LIMIT":
    query_sql += f" LIMIT {step['count']}"
...
```

**You**: "Looks good. Run the tests."

**Step 5: Verify**

```bash
./bin/test.sh brief
```

All tests pass!

**Step 6: Merge**

```bash
git add .
git commit -m "Add limit() method to query iterators"
```

---

## Summary: Working Well with AI on PropWeaver

**Key Principles**:

1. **Provide context** - Reference the architecture, show examples
2. **Ask for tests first** - Before implementation
3. **Specify boundaries** - Tell AI what not to change
4. **Review carefully** - Check for patterns, not just correctness
5. **Iterate incrementally** - One step at a time
6. **Reference existing patterns** - Show similar code
7. **Use TODO.md** - Track multi-step work
8. **Leverage the architecture** - Module boundaries contain changes

PropWeaver's design makes it excellent for AI collaboration. Use that to your advantage!
