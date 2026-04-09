# Database Migrations

This document explains how to handle database schema changes and migrations for the PropertyGraph database system.

## Overview

The PropertyGraph uses SQLite with a schema versioning system that tracks changes over time. Each database instance stores its schema version in the `graph_metadata_props` table with key `schema_version`.

## Current Architecture

### Schema Version Tracking

The PropertyGraph automatically stores a `schema_version` property (currently version 1) when creating new databases:

```python
## EXAMPLE
# Check current schema version
with PropertyGraph("my_database.db") as graph:
    current_version = graph.props["schema_version"]  # Returns int, e.g., 1
```

### Database Schema (Version 1)

Current tables:
- `resource` - Nodes with id, type, created_at
- `resource_props` - Node properties with typed values
- `rel` - Edges with src_id, dst_id, type, created_at  
- `rel_props` - Edge properties with typed values
- `graph_metadata` - Single-row graph metadata
- `graph_metadata_props` - Graph-level properties including schema_version

## Migration Strategies

### 1. SQL-Based Migrations (Recommended)

For structural changes to tables and indexes:

```python
## EXAMPLE
def migrate_database(graph: PropertyGraph, from_version: int, to_version: int):
    """Apply SQL migrations to upgrade database schema"""
    migrations = {
        1: {  # From version 1
            2: [  # To version 2
                "ALTER TABLE resource ADD COLUMN metadata TEXT",
                "CREATE INDEX IF NOT EXISTS idx_resource_metadata ON resource(metadata)",
                "ALTER TABLE rel ADD COLUMN weight REAL DEFAULT 1.0"
            ]
        },
        2: {  # From version 2  
            3: [  # To version 3
                "CREATE TABLE resource_tags (res_id INTEGER, tag TEXT, PRIMARY KEY(res_id, tag))",
                "ALTER TABLE graph_metadata_props ADD COLUMN updated_at REAL"
            ]
        }
    }
    
    # Apply migrations sequentially
    current_version = from_version
    while current_version < to_version:
        next_version = current_version + 1
        if current_version in migrations and next_version in migrations[current_version]:
            print(f"Migrating from version {current_version} to {next_version}")
            for sql in migrations[current_version][next_version]:
                graph.conn.execute(sql)
            graph.props["schema_version"] = next_version
            graph.commit()
            current_version = next_version
        else:
            raise ValueError(f"No migration path from version {current_version} to {next_version}")
```

### 2. Python-Based Migrations

For data transformations and complex logic:

```python
## EXAMPLE
def migrate_v1_to_v2_data(graph: PropertyGraph):
    """Migrate data from version 1 to version 2 format"""
    # Example: Convert old node type to new structure
    for node in graph.nodes("old_file_type"):
        # Extract and transform properties
        old_path = node.props["path"]
        new_properties = {
            "file_path": old_path,
            "normalized_path": normalize_path(old_path),
            "file_size": get_file_size(old_path)
        }
        
        # Create new node with transformed data
        new_node = graph.add_node("source_file", **new_properties)
        
        # Migrate relationships
        for edge in graph.iter_edges():
            if edge.src_id == node.node_id:
                graph.add_edge(new_node, edge.edge_type, edge.dst_id, **edge.props.copy())
            elif edge.dst_id == node.node_id:
                graph.add_edge(edge.src_id, edge.edge_type, new_node, **edge.props.copy())
        
        # Remove old node (this will cascade delete properties and edges)
        cursor = graph.conn.cursor()
        cursor.execute("DELETE FROM resource WHERE id = ?", (node.node_id,))

## EXAMPLE
def convert_properties(old_node):
    """Helper to convert old property format to new"""
    props = old_node.props.copy()
    # Apply transformations
    if "old_field" in props:
        props["new_field"] = transform_value(props.pop("old_field"))
    return props
```

### 3. Automatic Migration System

Integrate migrations into PropertyGraph initialization:

```python
...
class PropertyGraph:
    CURRENT_VERSION = 2  # Update when schema changes
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = ":memory:" if db_path is None else db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()
        self._create_indexes()
        self._migrate_if_needed()  # Add this line
    
    def _migrate_if_needed(self):
        """Check and apply migrations if database is outdated"""
        current = self.props.get("schema_version", 1)
        if current < self.CURRENT_VERSION:
            print(f"Migrating database from version {current} to {self.CURRENT_VERSION}")
            self._migrate(current, self.CURRENT_VERSION)
            print("Migration completed successfully")
    
    def _migrate(self, from_ver: int, to_ver: int):
        """Apply all migrations from from_ver to to_ver"""
        migrate_database(self, from_ver, to_ver)
...
```

## Forward Compatibility Guidelines

### Safe Changes (Post-Release)

These changes don't break existing databases:

- **Adding new tables** - Existing code ignores unknown tables
- **Adding new columns** - Use `ALTER TABLE ADD COLUMN` with DEFAULT values
- **Adding new node/edge types** - Property graphs are schema-flexible
- **Adding new properties** - Properties are stored as key-value pairs
- **Adding indexes** - Performance improvement, no data changes
- **Relaxing constraints** - Makes validation less strict

Example safe migration:
```sql
-- Safe: Add optional metadata column
ALTER TABLE resource ADD COLUMN file_hash TEXT DEFAULT NULL;

-- Safe: Add new index for performance
CREATE INDEX IF NOT EXISTS idx_resource_hash ON resource(file_hash);
```

### Breaking Changes (Require Migration)

These changes need careful migration planning:

- **Renaming/removing tables or columns**
- **Changing data types** (e.g., TEXT to INTEGER)
- **Adding NOT NULL constraints** to existing columns
- **Changing relationship semantics** (e.g., changing what edge types mean)
- **Removing node/edge types** that existing code expects

Example breaking change migration:
```python
## EXAMPLE
def migrate_v2_to_v3_breaking(graph: PropertyGraph):
    """Example: Rename 'path' property to 'file_path' for all nodes"""
    cursor = graph.conn.cursor()
    
    # Update all nodes with 'path' property
    cursor.execute("""
        UPDATE resource_props 
        SET k = 'file_path' 
        WHERE k = 'path'
    """)
    
    # Update schema version
    graph.props["schema_version"] = 3
    graph.commit()
```

## Best Practices

### 1. Version Bump Strategy

- **Patch versions (1.0.1)**: Bug fixes, no schema changes
- **Minor versions (1.1.0)**: Safe additive changes
- **Major versions (2.0.0)**: Breaking changes requiring migration

### 2. Testing Migrations

```python
## EXAMPLE
def test_migration():
    """Test migration with sample data"""
    # Create v1 database with test data
    with PropertyGraph(":memory:") as graph_v1:
        graph_v1.props["schema_version"] = 1
        test_node = graph_v1.add_node("file", path="/test.py")
        
        # Apply migration
        migrate_database(graph_v1, 1, 2)
        
        # Verify migration worked
        assert graph_v1.props["schema_version"] == 2
        migrated_node = list(graph_v1.nodes("source_file"))[0]
        assert migrated_node.props["file_path"] == "/test.py"
```

### 3. Backup Strategy

```python
## EXAMPLE
def safe_migrate(db_path: str):
    """Migrate with automatic backup"""
    import shutil
    from datetime import datetime
    
    # Create backup
    backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    try:
        # Perform migration
        with PropertyGraph(db_path) as graph:
            # Migration happens automatically in __init__
            pass
        print("Migration successful")
    except Exception as e:
        # Restore backup on failure
        shutil.copy2(backup_path, db_path)
        print(f"Migration failed, restored backup: {e}")
        raise
```

## Migration Checklist

When planning a schema change:

1. **Determine impact**: Safe additive vs. breaking change
2. **Write migration code**: SQL and/or Python transformations  
3. **Update CURRENT_VERSION**: Increment version number
4. **Test migration**: Use test data to verify correctness
5. **Document changes**: Update this file and CLAUDE.md
6. **Plan rollback**: Consider how to reverse if needed

## Using Bulk Operations in Migrations

For migrations that need to delete or modify many nodes/edges, use the new bulk operations for better performance and atomicity:

### Bulk Deletion in Migrations

```python
## EXAMPLE
def migrate_v2_to_v3_cleanup(graph: PropertyGraph):
    """Example migration that removes deprecated data using bulk operations"""
    
    # Remove deprecated node types
    deleted_temp = graph.nodes("temp_node").delete().execute()
    print(f"Removed {deleted_temp} temporary nodes")
    
    # Remove inactive relationships
    deleted_edges = graph.edges("legacy_relation", active=False).delete().execute()
    print(f"Removed {deleted_edges} inactive legacy relationships")
    
    # Remove nodes matching complex criteria
    deleted_old = graph.nodes("user").filter(status="deprecated").delete().execute()
    print(f"Removed {deleted_old} deprecated users")
```

### Transactional Migrations

Use transactions to ensure migrations are atomic - either fully succeed or fully roll back:

```python
## EXAMPLE
def migrate_v3_to_v4_atomic(graph: PropertyGraph):
    """Migration that uses transactions for safety"""
    
    with graph._storage.transaction():
        # Step 1: Create new nodes
        for old_node in graph.nodes("legacy_type"):
            new_node = graph.add_node("modern_type", 
                                    name=old_node.props["name"],
                                    migrated_from=old_node.node_id)
        
        # Step 2: Update relationships
        for edge in graph.edges("old_relation"):
            # Create equivalent new relationship
            graph.add_edge(edge.src_id, "new_relation", edge.dst_id,
                         strength=edge.props.get("weight", 1.0))
        
        # Step 3: Clean up old data (bulk operations)
        graph.edges("old_relation").delete().execute()
        graph.nodes("legacy_type").delete().execute()
        
        # All operations committed together, or all rolled back on error
```

### Modern Migration Patterns

Replace old manual SQL patterns with the new API:

```python
## EXAMPLE
# Old pattern (avoid):
cursor = graph.conn.cursor()
cursor.execute("DELETE FROM resource WHERE id = ?", (node.node_id,))

# New pattern (preferred):
graph.nodes().filter(node_id=node.node_id).delete().execute()

# Even better for bulk operations:
graph.nodes("deprecated_type").delete().execute()
```

### Performance Benefits

Bulk operations provide better performance for large migrations:

```python
## EXAMPLE
def performance_comparison():
    # Slow: Individual deletions
    for node in graph.nodes("temp_data"):
        graph._storage._delete_node(node.node_id)  # Don't do this
    
    # Fast: Single bulk operation
    deleted_count = graph.nodes("temp_data").delete().execute()
    print(f"Deleted {deleted_count} nodes in one transaction")
```

## Example Migration Implementation

See `src/propweaver/core.py` for the base PropertyGraph class that supports this migration system.
