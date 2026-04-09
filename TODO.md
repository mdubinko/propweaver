# PropWeaver TODO

This file tracks development tasks and improvements for the PropWeaver library.

## High Priority

### API Improvements

### Query System Enhancements
- [ ] Implement advanced filtering with lambda expressions or similar (e.g., `graph.edges("FRIENDS").filter(lambda e: e.prop("strength") >= 0.8)`)
- [ ] Add support for chained filtering on iterators
- [ ] Implement traversal operations (following edges to connected nodes)
- [ ] Add ordering/sorting capabilities to query results

### Database Features
- [ ] Investigate transaction isolation levels
- [ ] Add database integrity checks

### Security Features
- [ ] **Encryption at rest** - Add optional database encryption on create/load (SQLCipher integration)
- [ ] **Database-layer access control** - Optional row-level security and permissions system
- [x] **Path validation** - Validate db_path parameter to prevent directory traversal (COMPLETED)
- [ ] **Input validation** - Add validation for node_type, edge_type (max length, character restrictions)
- [ ] **Resource limits** - Configurable limits for nodes, edges, property sizes
- [ ] **Security logging** - Audit trail for data modifications and access patterns

## Medium Priority

### Performance & Optimization
- [ ] Optimize bulk operations for large datasets example https://ldbcouncil.org/data-sets-surf-repository/
- [ ] Add query plan caching
- [ ] Implement lazy loading for properties
- [ ] Add connection pooling for concurrent access

### Developer Experience (DX)
- [ ] Add comprehensive type hints throughout codebase
- [x] Improve error messages and exception handling
- [ ] Add query debugging/logging capabilities
- [ ] Create development utilities (schema inspection, etc.)
- [ ] Investigate self-logging exceptions (similar to structured logging patterns)
- [ ] **Check logging setup for PropWeaver development** - Verify that `configure_for_tests()` is called in conftest.py or test setup so developers see PropWeaver logs during testing. Without application logging config, PropWeaver logs may not be visible during standalone development.

### Testing & Quality
- [ ] Add performance benchmarks
- [ ] Create integration tests with real-world sized datasets
- [ ] Add property-based testing (hypothesis)
- [ ] Test edge cases with large graphs (>10k nodes/edges)

## Low Priority

### Documentation
- [ ] Create API reference documentation
- [ ] Add more usage examples to README
- [ ] Document best practices for large graphs
- [ ] Create migration guide from other graph databases

### Advanced Features
- [ ] Add graph algorithms (shortest path, centrality measures, etc.)
- [ ] Implement graph visualization export (GraphViz, etc.)
- [ ] Add import/export functionality (JSON, CSV, GraphML)
- [ ] Support for graph schemas/validation

### Packaging & Distribution
- [ ] Prepare for PyPI publication
- [ ] Add GitHub Actions CI/CD
- [ ] Create conda package
- [ ] Add Docker examples

## Code Quality Tasks

### Refactoring
- [ ] Extract common patterns in storage layer
- [ ] Simplify query execution engine
- [ ] Reduce code duplication in test fixtures
- [ ] Improve separation of concerns between modules

### Code Comments & Documentation
- [ ] Add docstrings to all public methods
- [ ] Document complex algorithms in storage layer
- [ ] Add inline comments for tricky SQL queries
- [ ] Document thread safety considerations

## Issues Discovered During Testing

### Examples
- [ ] Simplify filtering syntax in all examples
- [ ] Add error handling to examples
- [ ] Test all examples work with current API

### API Inconsistencies
- [ ] Standardize return types across similar methods
- [ ] Ensure consistent parameter naming
- [ ] Review method signatures for usability
- [ ] Add missing convenience methods

## Future Considerations

### Architecture
- [ ] Consider supporting multiple storage backends (not just SQLite)
- [ ] Evaluate async/await support for I/O operations
- [ ] Research memory-mapped file support for large graphs
- [ ] Consider distributed graph storage options

### Compatibility
- [ ] Test with different Python versions (3.10, 3.11, 3.12+)
- [ ] Ensure compatibility with different SQLite versions
- [ ] Test on different operating systems
- [ ] Verify thread safety in multi-threaded applications

---

## Contributing

When working on items from this TODO:

1. Move items from TODO to "In Progress" when starting work
2. Reference this file in commit messages (e.g., "Implements TODO: Add default value support to prop()")
3. Update this file as new issues/improvements are discovered
4. Consider breaking large tasks into smaller, actionable items

## Completed Items

### Recently Completed
- [x] Create examples/ directory with real-world scenarios
- [x] Convert test suite to use pytest framework
- [x] Set up proper virtual environment with dependencies
- [x] Fix test failures to match actual API behavior
- [x] Organize tests into logical modules (query, CRUD, bulk operations, integration)
- [x] Add comprehensive test fixtures and utilities
- [x] Add single underscore prefix to all StorageLayer methods (proper private API naming)
- [x] Fix examples to use public PropertyGraph API instead of direct storage access
- [x] Create development scripts in bin/ directory (test.sh, examples.sh, dev.sh)
- [x] Update README.md and CLAUDE.md with simplified development workflows
- [x] Implement SQLAlchemy-style exception hierarchy with rich context
- [x] Add comprehensive exception tests with backward compatibility
- [x] Export new exception types in main __init__.py module