"""
Tests for PropWeaver exception hierarchy and error handling.

Tests the new SQLAlchemy-style exceptions with rich context for debugging.
"""

import pytest

from propweaver import PropertyGraph
from propweaver.exceptions import (
    EntityNotFoundError,
    InvalidQueryError,
    PropertyNotFoundError,
    PropertyValueError,
    PropWeaverError,
)


class TestPropertyExceptions:
    """Test property-related exceptions"""

    def test_property_not_found_error_node(self, graph):
        """Test PropertyNotFoundError provides helpful context for nodes"""
        user = graph.add_node("User", name="Alice", email="alice@example.com")

        with pytest.raises(PropertyNotFoundError) as exc_info:
            _ = user.props["age"]  # Property doesn't exist

        error = exc_info.value
        assert error.property_key == "age"
        assert error.entity_type == "Node"
        assert error.entity_id == user.node_id
        assert "name" in error.available_properties
        assert "email" in error.available_properties
        assert len(error.available_properties) == 2
        assert "Available: email, name" in str(error)

    def test_property_not_found_error_edge(self, graph):
        """Test PropertyNotFoundError provides helpful context for edges"""
        user1 = graph.add_node("User", name="Alice")
        user2 = graph.add_node("User", name="Bob")
        friendship = graph.add_edge(user1, "FRIENDS", user2, since="2023-01-01")

        with pytest.raises(PropertyNotFoundError) as exc_info:
            _ = friendship.props["strength"]  # Property doesn't exist

        error = exc_info.value
        assert error.property_key == "strength"
        assert error.entity_type == "Edge"
        assert error.entity_id == friendship.edge_id
        assert "since" in error.available_properties
        assert "Available: since" in str(error)

    def test_property_not_found_no_properties(self, graph):
        """Test PropertyNotFoundError when entity has no properties"""
        user = graph.add_node("User")  # No properties

        with pytest.raises(PropertyNotFoundError) as exc_info:
            _ = user.props["name"]

        error = exc_info.value
        assert error.available_properties == []
        assert "No properties set" in str(error)

    def test_property_value_error_none_value(self, graph):
        """Test PropertyValueError for None values"""
        user = graph.add_node("User", name="Bob")

        with pytest.raises(PropertyValueError) as exc_info:
            user.props["active"] = None  # None not allowed

        error = exc_info.value
        assert error.property_key == "active"
        assert error.value == "None"
        assert error.value_type == "NoneType"
        assert "None values are not allowed" in error.reason
        assert error.entity_type == "Node"
        assert error.entity_id == user.node_id

    def test_property_value_error_edge(self, graph):
        """Test PropertyValueError on edges"""
        user1 = graph.add_node("User", name="Alice")
        user2 = graph.add_node("User", name="Bob")
        friendship = graph.add_edge(user1, "FRIENDS", user2)

        with pytest.raises(PropertyValueError) as exc_info:
            friendship.props["weight"] = None

        error = exc_info.value
        assert error.entity_type == "Edge"
        assert error.entity_id == friendship.edge_id


class TestQueryExceptions:
    """Test query-related exceptions"""

    def test_invalid_query_error_no_operations(self, graph):
        """Test InvalidQueryError when execute() called without DELETE operations"""
        user = graph.add_node("User", name="Charlie")

        with pytest.raises(InvalidQueryError) as exc_info:
            # Try to execute a query without DELETE operations
            graph.nodes("User").execute()

        error = exc_info.value
        assert "modification operations" in str(error)
        assert len(error.query_steps) == 2  # SOURCE + FILTER
        assert error.step_count == 2

    def test_invalid_query_error_empty_query(self, graph):
        """Test InvalidQueryError with empty query"""
        from propweaver.query import NodeIterator, QuerySpec

        # Create an iterator with no steps
        empty_spec = QuerySpec()
        iterator = NodeIterator(empty_spec, lambda x: [], lambda x: x, lambda x: 0)

        with pytest.raises(InvalidQueryError) as exc_info:
            iterator.execute()

        error = exc_info.value
        assert error.query_steps == []
        assert error.step_count == 0


class TestExceptionHierarchy:
    """Test exception inheritance and attributes"""

    def test_propweaver_error_base_class(self):
        """Test PropWeaverError base class functionality"""
        error = PropWeaverError("Test message", test_attr="test_value", number=42)

        assert str(error) == "Test message"
        assert error.test_attr == "test_value"
        assert error.number == 42

    def test_exception_inheritance(self):
        """Test that all exceptions inherit from PropWeaverError"""
        assert issubclass(PropertyNotFoundError, PropWeaverError)
        assert issubclass(PropertyValueError, PropWeaverError)
        assert issubclass(InvalidQueryError, PropWeaverError)
        assert issubclass(EntityNotFoundError, PropWeaverError)

    def test_property_error_attributes(self, graph):
        """Test that PropertyError subclasses have expected attributes"""
        user = graph.add_node("User", name="Alice")

        with pytest.raises(PropertyNotFoundError) as exc_info:
            _ = user.props["missing"]

        error = exc_info.value
        # Check all expected attributes are present
        assert hasattr(error, "property_key")
        assert hasattr(error, "entity_type")
        assert hasattr(error, "entity_id")
        assert hasattr(error, "available_properties")
        assert hasattr(error, "available_count")


class TestExceptionContext:
    """Test exception context and chaining"""

    def test_exception_chaining(self, graph):
        """Test that exceptions properly chain original causes"""
        user = graph.add_node("User", name="Test")

        with pytest.raises(PropertyValueError) as exc_info:
            user.props["invalid"] = None

        error = exc_info.value
        # Should have the original ValueError as the cause
        assert error.__cause__ is not None
        assert isinstance(error.__cause__, ValueError)

    def test_structured_exception_data(self, graph):
        """Test that exceptions can be converted to structured data"""
        user = graph.add_node("User", name="Alice", email="alice@example.com")

        with pytest.raises(PropertyNotFoundError) as exc_info:
            _ = user.props["missing"]

        error = exc_info.value

        # Test that all key attributes are accessible
        assert error.property_key == "missing"
        assert error.entity_type == "Node"
        assert isinstance(error.available_properties, list)
        assert len(error.available_properties) == 2


class TestBackwardCompatibility:
    """Test that new exceptions don't break existing patterns"""

    def test_keyerror_compatibility(self, graph):
        """Test that PropertyNotFoundError can be caught as KeyError"""
        user = graph.add_node("User", name="Alice")

        # Should be catchable as KeyError for backward compatibility
        with pytest.raises(KeyError):
            _ = user.props["missing"]

    def test_valueerror_compatibility(self, graph):
        """Test that PropertyValueError can be caught as ValueError"""
        user = graph.add_node("User", name="Alice")

        # Should be catchable as ValueError for backward compatibility
        with pytest.raises(ValueError):
            user.props["test"] = None
