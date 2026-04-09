"""
Query system for PropWeaver - handles query building and execution.

This module contains the declarative query system including:
- QuerySpec and QueryStep for query representation
- NodeIterator and EdgeIterator for lazy evaluation
- XPath-style query chaining and execution
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Literal, Optional

from .logging_utils import get_logger, log_query_operation, log_error_with_context

if TYPE_CHECKING:
    from .core import EdgeProxy, NodeProxy

# Import here to avoid circular imports
from .exceptions import InvalidQueryError, QueryExecutionError


@dataclass(slots=True)
class QueryStep:
    """Single step in a query execution plan"""

    type: Literal["SOURCE", "FILTER", "TRAVERSE", "ORDER", "DELETE"]
    target: Optional[str] = None  # For SOURCE: "all_nodes", "all_edges"
    node_type: Optional[str] = None  # For FILTER: node type filter
    edge_type: Optional[str] = None  # For TRAVERSE/FILTER: edge type
    properties: Optional[dict] = None  # For FILTER: property filters
    direction: Literal["out", "in", "both"] = "both"  # For TRAVERSE: "out", "in", "both"
    field: Optional[str] = None  # For ORDER: field name
    order: Optional[Literal["asc", "desc"]] = None  # For ORDER: "asc", "desc"


@dataclass(slots=True)
class QuerySpec:
    """Declarative query specification"""

    steps: List[QueryStep] = field(default_factory=list)
    returning: Literal["nodes", "edges", "target_nodes", "source_nodes"] = (
        "nodes"  # What to return from the query
    )
    limit: Optional[int] = None

    # returning field documentation:
    # "nodes" - Return nodes from a node-based query (e.g., graph.nodes())
    # "edges" - Return edges from an edge-based query (e.g., graph.edges())
    # "target_nodes" - Return destination nodes after traversal (e.g., alice.outgoing("friends") returns Bob)
    # "source_nodes" - Return source nodes after reverse traversal (e.g., bob.incoming("friends") returns Alice)


class NodeIterator:
    """Lazy iterator for XPath-style graph traversal"""

    def __init__(
        self, query_spec: QuerySpec, executor: Callable, factory: Callable, deleter: Callable
    ):
        self.query_spec = query_spec
        self.executor = executor
        self.factory = factory
        self.deleter = deleter
        self._results = None

    def filter(self, type: Optional[str] = None, **properties):
        """Filter current result set - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.returning = self.query_spec.returning
        new_spec.limit = self.query_spec.limit

        new_spec.steps.append(
            QueryStep(type="FILTER", node_type=type, properties=properties if properties else None)
        )

        return NodeIterator(new_spec, self.executor, self.factory, self.deleter)

    def outgoing(self, edge_type: str):
        """Follow outgoing edges - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.steps.append(QueryStep(type="TRAVERSE", edge_type=edge_type, direction="out"))
        new_spec.returning = "target_nodes"
        new_spec.limit = self.query_spec.limit

        return NodeIterator(new_spec, self.executor, self.factory, self.deleter)

    def incoming(self, edge_type: str):
        """Follow incoming edges - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.steps.append(QueryStep(type="TRAVERSE", edge_type=edge_type, direction="in"))
        new_spec.returning = "source_nodes"
        new_spec.limit = self.query_spec.limit

        return NodeIterator(new_spec, self.executor, self.factory, self.deleter)

    def limit(self, count: int):
        """Limit results - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.returning = self.query_spec.returning
        new_spec.limit = count

        return NodeIterator(new_spec, self.executor, self.factory, self.deleter)

    def __iter__(self):
        """Execute query when iteration begins"""
        if self._results is None:
            self._results = self.executor(self.query_spec)

        for row in self._results:
            yield self.factory(row)

    def execute(self) -> int:
        """Execute modification operations and return count of affected items"""
        modification_steps = [step for step in self.query_spec.steps if step.type == "DELETE"]
        if not modification_steps:
            raise InvalidQueryError(
                "execute() can only be called on queries with modification operations",
                self.query_spec.steps,
            )

        logger = get_logger("query")
        start_time = time.time()

        affected_count = self.deleter(self.query_spec)

        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > 100:  # Log slow operations as warning
            logger.warning(f"⚠️ Slow bulk delete: {affected_count} nodes ({elapsed_ms:.0f}ms)")
        else:
            logger.summary(f"🔧 Bulk delete: {affected_count} nodes ({elapsed_ms:.0f}ms)")

        return affected_count

    def delete(self) -> "NodeIterator":
        """Add DELETE step to query - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.steps.append(QueryStep(type="DELETE"))
        new_spec.returning = self.query_spec.returning
        new_spec.limit = self.query_spec.limit

        return NodeIterator(new_spec, self.executor, self.factory, self.deleter)

    def __repr__(self):
        steps_str = " -> ".join(f"{step.type}" for step in self.query_spec.steps)
        return f"NodeIterator(steps: {steps_str}, returning: {self.query_spec.returning})"


class EdgeIterator:
    """Lazy iterator for edge operations"""

    def __init__(
        self, query_spec: QuerySpec, executor: Callable, factory: Callable, deleter: Callable
    ):
        self.query_spec = query_spec
        self.executor = executor
        self.factory = factory
        self.deleter = deleter
        self._results = None

    def filter(self, type: Optional[str] = None, **properties):
        """Filter current result set - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.returning = "edges"
        new_spec.limit = self.query_spec.limit

        new_spec.steps.append(
            QueryStep(type="FILTER", edge_type=type, properties=properties if properties else None)
        )

        return EdgeIterator(new_spec, self.executor, self.factory, self.deleter)

    def limit(self, count: int) -> "EdgeIterator":
        """Limit results - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.returning = "edges"
        new_spec.limit = count

        return EdgeIterator(new_spec, self.executor, self.factory, self.deleter)

    def __iter__(self):
        """Execute query and return edge iterator"""
        if self._results is None:
            self._results = self.executor(self.query_spec)

        for row in self._results:
            yield self.factory(row)

    def execute(self) -> int:
        """Execute modification operations and return count of affected edges"""
        modification_steps = [step for step in self.query_spec.steps if step.type == "DELETE"]
        if not modification_steps:
            raise InvalidQueryError(
                "execute() can only be called on queries with modification operations",
                self.query_spec.steps,
            )

        logger = get_logger("query")
        start_time = time.time()

        affected_count = self.deleter(self.query_spec)

        elapsed_ms = (time.time() - start_time) * 1000
        if elapsed_ms > 100:  # Log slow operations as warning
            logger.warning(f"⚠️ Slow bulk delete: {affected_count} edges ({elapsed_ms:.0f}ms)")
        else:
            logger.summary(f"🔧 Bulk delete: {affected_count} edges ({elapsed_ms:.0f}ms)")

        return affected_count

    def delete(self) -> "EdgeIterator":
        """Add DELETE step to query - returns new iterator"""
        new_spec = QuerySpec()
        new_spec.steps = self.query_spec.steps.copy()
        new_spec.steps.append(QueryStep(type="DELETE"))
        new_spec.returning = "edges"
        new_spec.limit = self.query_spec.limit

        return EdgeIterator(new_spec, self.executor, self.factory, self.deleter)

    def __repr__(self):
        steps_str = " -> ".join(f"{step.type}" for step in self.query_spec.steps)
        return f"EdgeIterator(steps: {steps_str}, returning: edges)"
