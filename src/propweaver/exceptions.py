"""
PropWeaver exception hierarchy following SQLAlchemy patterns.

Provides structured exceptions with rich context for debugging and error handling.
Follows established Python database library conventions for consistency.
"""

from typing import Any, Dict, List, Optional, Union


class PropWeaverError(Exception):
    """
    Base exception for all PropWeaver operations.

    Similar to SQLAlchemy's SQLAlchemyError - provides the root of the exception
    hierarchy and basic context storage.
    """

    def __init__(self, message: str, **context):
        super().__init__(message)
        # Store context as instance attributes for programmatic access
        for key, value in context.items():
            setattr(self, key, value)


class StatementError(PropWeaverError):
    """
    Error executing a graph operation or query.

    Similar to SQLAlchemy's StatementError - provides context about the
    operation that failed, including operation type and parameters.
    """

    def __init__(
        self,
        message: str,
        operation: str,
        params: Optional[Dict[str, Any]] = None,
        orig: Optional[Exception] = None,
    ):
        self.operation = operation
        self.params = params or {}
        self.orig = orig  # Original exception that caused this error

        super().__init__(message, operation=operation, params=params, orig=orig)


class EntityError(PropWeaverError):
    """
    Base class for entity-related errors (nodes and edges).

    Provides common context for operations on graph entities.
    """

    def __init__(
        self, message: str, entity_type: str, entity_id: Optional[Union[int, str]] = None, **context
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id

        super().__init__(message, entity_type=entity_type, entity_id=entity_id, **context)


class EntityNotFoundError(EntityError):
    """
    Entity (node or edge) does not exist in the database.

    Similar to Django's DoesNotExist - indicates the requested entity
    cannot be found. Includes entity type and ID for debugging.
    """

    def __init__(self, entity_type: str, entity_id: Union[int, str]):
        message = f"{entity_type} with ID {entity_id} does not exist"
        super().__init__(message, entity_type, entity_id)


class PropertyError(EntityError):
    """
    Base class for property-related operations.

    Provides context about which property caused the error.
    """

    def __init__(
        self,
        message: str,
        property_key: str,
        entity_type: str,
        entity_id: Optional[Union[int, str]] = None,
        **context,
    ):
        self.property_key = property_key

        super().__init__(message, entity_type, entity_id, property_key=property_key, **context)


class PropertyNotFoundError(PropertyError, KeyError):
    """
    Property does not exist on the specified entity.

    Includes available properties to help with debugging typos and
    understanding the entity's structure.

    Inherits from KeyError for backward compatibility.
    """

    def __init__(
        self,
        property_key: str,
        entity_type: str,
        entity_id: Union[int, str],
        available_properties: Optional[List[str]] = None,
    ):
        self.available_properties = available_properties or []

        # Build helpful error message
        available_str = ", ".join(self.available_properties[:5])
        if len(self.available_properties) > 5:
            available_str += f" (and {len(self.available_properties) - 5} more)"

        if self.available_properties:
            message = f"Property '{property_key}' not found on {entity_type}#{entity_id}. Available: {available_str}"
        else:
            message = f"Property '{property_key}' not found on {entity_type}#{entity_id}. No properties set"

        super().__init__(
            message,
            property_key,
            entity_type,
            entity_id,
            available_properties=self.available_properties,
            available_count=len(self.available_properties),
        )


class PropertyValueError(PropertyError, ValueError):
    """
    Property value is invalid or cannot be stored.

    Includes information about the attempted value and why it's invalid.

    Inherits from ValueError for backward compatibility.
    """

    def __init__(
        self,
        property_key: str,
        value: Any,
        reason: str,
        entity_type: str = "Entity",
        entity_id: Optional[Union[int, str]] = None,
    ):
        self.value = value
        self.reason = reason
        self.value_type = type(value).__name__

        message = f"Invalid value for property '{property_key}': {reason}"

        super().__init__(
            message,
            property_key,
            entity_type,
            entity_id,
            value=str(value)[:100] + "..." if len(str(value)) > 100 else str(value),
            value_type=self.value_type,
            reason=reason,
        )


class QueryError(PropWeaverError):
    """
    Base class for query construction and execution errors.

    Provides context about the query that failed.
    """

    def __init__(self, message: str, query_steps: Optional[List] = None, **context):
        self.query_steps = query_steps or []

        super().__init__(
            message, query_steps=query_steps, step_count=len(self.query_steps), **context
        )


class InvalidQueryError(QueryError):
    """
    Query is malformed or uses invalid operations.

    Indicates a programming error in query construction.
    """

    def __init__(self, message: str, query_steps: Optional[List] = None):
        super().__init__(message, query_steps)


class QueryExecutionError(QueryError):
    """
    Query failed during execution.

    Similar to SQLAlchemy's StatementError but for graph queries.
    Includes the original exception that caused the failure.
    """

    def __init__(
        self, message: str, query_steps: Optional[List] = None, orig: Optional[Exception] = None
    ):
        self.orig = orig

        # Add query context to message
        if query_steps:
            steps_str = " → ".join(
                str(step.type) if hasattr(step, "type") else str(step) for step in query_steps
            )
            full_message = f"{message} (Query: {steps_str})"
        else:
            full_message = message

        super().__init__(full_message, query_steps, orig=orig)


class DatabaseError(StatementError):
    """
    Low-level database operation failed.

    Similar to SQLAlchemy's DBAPIError - wraps underlying database
    errors while preserving the original exception and SQL context.
    """

    def __init__(
        self,
        message: str,
        sql_query: Optional[str] = None,
        sql_params: Optional[List] = None,
        orig: Optional[Exception] = None,
    ):
        self.sql_query = sql_query
        self.sql_params = sql_params

        super().__init__(
            message,
            "database_operation",
            params={"sql_query": sql_query, "sql_params": sql_params},
            orig=orig,
        )


class IntegrityError(DatabaseError):
    """
    Database constraint violation.

    Similar to SQLAlchemy's IntegrityError - indicates a constraint
    violation like foreign key, unique constraint, or check constraint.
    """

    pass


class TransactionError(PropWeaverError):
    """
    Transaction management error.

    Indicates problems with transaction state, rollback, or commit operations.
    """

    def __init__(self, message: str, transaction_state: Optional[str] = None):
        self.transaction_state = transaction_state

        super().__init__(message, transaction_state=transaction_state)


class ValidationError(PropWeaverError):
    """
    Data validation failed.

    Indicates that data doesn't meet expected constraints or formats.
    Can include multiple validation failures.
    """

    def __init__(self, message: str, validation_failures: Optional[List[str]] = None):
        self.validation_failures = validation_failures or []

        super().__init__(
            message,
            validation_failures=self.validation_failures,
            failure_count=len(self.validation_failures),
        )


# Convenience exception for the most common case - similar to Django's get_object_or_404
class DoesNotExist(EntityNotFoundError):
    """
    Convenience exception similar to Django's DoesNotExist.

    Can be used when the specific entity type doesn't matter,
    or for generic "not found" scenarios.
    """

    pass
