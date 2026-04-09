# PropWeaver Security Audit Report

**Date:** 2025-12-13
**Auditor:** Claude Code Security Analysis
**Scope:** PropWeaver v0.2.1 codebase

## Executive Summary

This security audit examines the PropWeaver library against the OWASP Top 10 2025 and SQLite security best practices. PropWeaver is a graph database library built on SQLite with zero external dependencies.

**Overall Security Posture:** GOOD ✅

The codebase demonstrates solid security practices, particularly in SQL injection prevention through consistent use of parameterized queries. However, several areas require attention for production use in security-sensitive environments.

## OWASP Resources Referenced

This audit follows guidance from:
- [OWASP Top 10 2025](https://owasp.org/Top10/2025/) - A05:2025 Injection
- [OWASP SQL Injection Prevention](https://owasp.org/www-community/attacks/SQL_Injection)
- [Python SQLite Security Best Practices](https://dev.to/stephenc222/basic-security-practices-for-sqlite-safeguarding-your-data-23lh)

## Findings by OWASP Category

### 🟢 A05:2025 - Injection (SQL Injection)

**Status:** SECURE ✅

**Analysis:**
- All database operations use parameterized queries via the `__execute()` method (storage.py:126-138)
- Query values are consistently passed as tuple parameters, never concatenated into SQL strings
- Dynamic SQL construction for table/column names uses f-strings BUT only with hardcoded values

**Evidence:**
```python
# GOOD: Parameterized query (storage.py:267-268)
cursor = self.__execute(
    "INSERT INTO resource (type, created_at) VALUES (?, ?)", (node_type, created_at)
)

# SAFE: f-string with hardcoded table names (storage.py:308-309)
sql = f"SELECT k, v, datatype FROM {table_name} WHERE {owner_id_col} = ?"
cursor = self.__execute(sql, (owner_id,))
# Called only with: table_name="resource_props", owner_id_col="res_id"
```

**Verification:**
- Lines 263-280: Node insertion - ✅ Parameterized
- Lines 282-300: Edge insertion - ✅ Parameterized
- Lines 629-666: Dynamic node queries - ✅ All user inputs parameterized
- Lines 668-705: Dynamic edge queries - ✅ All user inputs parameterized

**Property Key Safety:**
Property keys come from Python `**kwargs`, which enforces valid Python identifiers. This prevents injection attempts via special characters.

**Recommendation:**
Consider adding explicit validation that `table_name` and `owner_id_col` parameters match an allowlist, even though they're currently only called with hardcoded values. This defense-in-depth approach would prevent future refactoring mistakes.

---

### 🟡 A08:2025 - Software and Data Integrity Failures (Deserialization)

**Status:** LOW RISK ⚠️

**Analysis:**
The library uses `json.loads()` for deserializing JSON data (storage.py:94), which is significantly safer than pickle/yaml/eval approaches.

**Evidence:**
```python
# storage.py:72-75, 93-94
case list() | dict():
    return (json.dumps(value), "json")
...
case "json":
    return json.loads(str_value)
```

**Security Notes:**
- `json.loads()` only deserializes to basic Python types (dict, list, str, int, float, bool, None)
- No code execution risk like pickle.loads()
- No YAML anchors/references risk
- Safe against deserialization attacks

**Potential Issues:**
1. **No size limits** on JSON data - could cause memory exhaustion with very large JSON blobs
2. **No depth limits** - deeply nested JSON could cause stack overflow
3. **No schema validation** - malformed but valid JSON is accepted

**Recommendations:**
```python
import json

# Add limits for production use
def safe_json_loads(str_value: str, max_size: int = 1_000_000) -> Any:
    """Safely deserialize JSON with size limits"""
    if len(str_value) > max_size:
        raise ValueError(f"JSON data exceeds maximum size of {max_size} bytes")

    # Python's json.loads is already safe, but add explicit limits
    return json.loads(str_value)
```

---

### 🟢 A03:2025 - Injection (Path Traversal)

**Status:** FIXED ✅ (as of 2025-12-13)

**Analysis:**
Path validation has been implemented to prevent directory traversal attacks. Database paths are now validated before use.

**Implementation (storage.py:127-180):**
```python
def _validate_db_path(self, db_path: str, allowed_base_dir: Optional[str] = None) -> str:
    """Validate database path to prevent directory traversal attacks"""
    # Special SQLite paths are allowed unchanged
    if db_path in [":memory:", ""]:
        return db_path

    # Convert to absolute path (normalizes and resolves symlinks)
    path_obj = Path(db_path).resolve()

    # Check for path traversal attempts
    if ".." in db_path:
        raise ValueError(f"Path traversal detected in database path: {db_path}")

    # Optional: Restrict to base directory
    if allowed_base_dir is not None:
        base_path = Path(allowed_base_dir).resolve()
        path_obj.relative_to(base_path)  # Raises ValueError if outside

    return str(path_obj)
```

**Protection Mechanisms:**
1. ✅ Paths with ".." sequences are rejected
2. ✅ Paths are resolved to absolute paths
3. ✅ Optional base directory restriction via `allowed_base_dir` parameter
4. ✅ Special SQLite paths (":memory:", "") bypass validation
5. ✅ Comprehensive test coverage (17 tests)

**Secure Usage:**
```python
# Basic usage (rejects path traversal)
try:
    graph = PropertyGraph("../../../etc/passwd")
except ValueError:
    print("Path traversal blocked!")  # ✅ Protected

# Maximum security (restrict to directory)
graph = PropertyGraph(
    "user_123.db",
    allowed_base_dir="/var/lib/myapp"
)  # ✅ Only allows paths within /var/lib/myapp
```

**Test Coverage:** 17 tests in test_path_security.py verify:
- Path traversal attempts are blocked
- Absolute paths work correctly
- Base directory restriction works
- Error messages are informative
- Special SQLite paths still work

---

### 🟢 A01:2025 - Broken Access Control

**Status:** NOT APPLICABLE

**Analysis:**
PropWeaver is a library, not a service. Access control is the responsibility of the consuming application. The library provides no authentication or authorization mechanisms, which is appropriate for a database library.

**Note:** Applications using PropWeaver must implement their own access control.

---

### 🟡 A02:2025 - Cryptographic Failures

**Status:** MEDIUM RISK ⚠️

**Analysis:**
No encryption at rest or in transit. SQLite databases are stored as plaintext files.

**Issues:**
1. **No encryption at rest** - Database files contain plaintext data
2. **No encryption in transit** - Not applicable (local library)
3. **No password protection** - SQLite files are unprotected
4. **Sensitive data exposure** - to_json() methods expose all data

**Impact:**
- Anyone with filesystem access can read all data
- Database files could be stolen/copied
- Passwords, API keys, PII stored as plaintext

**Recommendations:**

1. **Document encryption options:**
```markdown
## Data Security

PropWeaver stores data in plaintext SQLite files. For sensitive data:

1. Use filesystem encryption (LUKS, BitLocker, FileVault)
2. Use SQLCipher for database encryption
3. Encrypt sensitive fields before storing
4. Control filesystem permissions (chmod 600)
```

2. **Consider SQLCipher integration** (optional):
```python
# Using pysqlcipher3
import sqlite3
from pysqlcipher3 import dbapi2 as sqlcipher

class EncryptedStorageLayer(StorageLayer):
    def __init__(self, db_path: str, password: str):
        self.db_path = db_path
        self.conn = sqlcipher.connect(db_path)
        self.conn.execute(f"PRAGMA key = '{password}'")
        # ... rest of initialization
```

---

### 🟡 A04:2025 - Insecure Design

**Status:** LOW RISK ⚠️

**Issue: Unlimited Resource Consumption**

**Analysis:**
No limits on:
- Number of nodes/edges
- Property sizes
- Query result sizes
- JSON depth/complexity
- Database file size

**DoS Scenarios:**
```python
# Memory exhaustion
for i in range(10_000_000):
    graph.add_node("Spam", data="x" * 1_000_000)

# CPU exhaustion
huge_json = {"a": {"b": {"c": {...}}}}  # Deeply nested
node.props["evil"] = huge_json
```

**Recommendations:**

1. **Add configurable limits:**
```python
class PropertyGraph:
    def __init__(
        self,
        db_path: Optional[str] = None,
        max_nodes: int = 10_000_000,
        max_property_size: int = 1_000_000,
        max_json_depth: int = 20
    ):
        self.max_nodes = max_nodes
        self.max_property_size = max_property_size
        # ...
```

2. **Add resource monitoring:**
```python
def add_node(self, node_type: str, **properties) -> NodeProxy:
    if self.node_count() >= self.max_nodes:
        raise ResourceLimitError(f"Maximum nodes ({self.max_nodes}) exceeded")
    # ...
```

---

### 🟢 A06:2025 - Vulnerable and Outdated Components

**Status:** EXCELLENT ✅

**Analysis:**
- **Zero external dependencies** - No third-party packages to audit
- Uses only Python standard library (sqlite3, json, time, etc.)
- No npm/pip dependencies to track for CVEs

**Note:** This is a significant security advantage. The attack surface is minimal.

---

### 🟡 A09:2025 - Security Logging and Monitoring Failures

**Status:** LOW RISK ⚠️

**Current State:**
- Logging exists but focuses on performance, not security
- No audit trail of data modifications
- No logging of failed operations
- No rate limiting or abuse detection

**Evidence:**
```python
# logging_utils.py - Performance focused
self.logger.summary(f"🔧 Bulk delete: {affected_count} nodes ({elapsed_ms:.0f}ms)")
```

**Recommendations:**

1. **Add security logging:**
```python
# Log security-relevant events
def _insert_node(self, node_type: str, properties: dict) -> int:
    self.logger.security(f"Node created: type={node_type}, props_count={len(properties)}")
    # ...

def _delete_node(self, node_id: int):
    self.logger.security(f"Node deleted: id={node_id}")
    # ...
```

2. **Add audit trail:**
```python
# Optional audit table
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    timestamp REAL NOT NULL,
    operation TEXT NOT NULL,  -- INSERT, UPDATE, DELETE
    entity_type TEXT NOT NULL, -- node, edge, property
    entity_id INTEGER,
    details TEXT  -- JSON
)
```

---

### 🟡 A10:2025 - Server-Side Request Forgery (SSRF)

**Status:** NOT APPLICABLE

**Analysis:** PropWeaver does not make any network requests or load external resources.

---

## Additional Security Considerations

### 🟡 Input Validation

**Issue:** Limited validation on user inputs

**Current State:**
- No validation on `node_type` or `edge_type` strings
- No validation on property keys (except Python identifier restrictions)
- No length limits on strings
- Type validation only checks for allowed Python types

**Recommendations:**

1. **Add type/key validation:**
```python
def validate_type_name(type_name: str, max_length: int = 255) -> None:
    """Validate node/edge type names"""
    if not type_name:
        raise ValueError("Type name cannot be empty")
    if len(type_name) > max_length:
        raise ValueError(f"Type name exceeds {max_length} characters")
    if not type_name[0].isalpha():
        raise ValueError("Type name must start with a letter")
    if not all(c.isalnum() or c in "_-" for c in type_name):
        raise ValueError("Type name contains invalid characters")

def add_node(self, node_type: str, **properties) -> NodeProxy:
    validate_type_name(node_type)
    # ...
```

2. **Add property size limits:**
```python
def _set_property(self, key: str, value: Any) -> None:
    if isinstance(value, str) and len(value) > self.max_string_length:
        raise ValueError(f"String property exceeds maximum length")
    # ...
```

### 🟢 Transaction Safety

**Status:** GOOD ✅

**Analysis:**
- Proper transaction management with context managers (storage.py:572-590)
- Automatic rollback on errors
- ACID compliance through SQLite
- Foreign key constraints enabled

**Evidence:**
```python
@contextmanager
def transaction(self):
    try:
        yield
        self.conn.commit()
    except Exception:
        self.conn.rollback()
        raise
```

### 🟡 Error Handling Information Disclosure

**Issue:** Exception messages may leak sensitive information

**Example:**
```python
# Could reveal database structure
raise PropertyNotFoundError(key, entity_type, entity_id, available_props)
# Message: "Property 'password' not found on Node(123). Available: ['username', 'email', 'api_key']"
```

**Recommendation:**
- Sanitize error messages in production
- Don't expose full stack traces to untrusted clients
- Consider different error detail levels for dev vs. prod

## Priority Recommendations

### ✅ COMPLETED

1. ✅ **Path validation** for `db_path` parameter (Path Traversal - A03) - FIXED
2. ✅ **Resource monitoring** via `resource_stats()` method - IMPLEMENTED
3. ✅ **Security documentation** in README - ADDED

### 🔴 HIGH Priority (Remaining)

1. **Add input validation** for type names and property keys
2. **Add resource limits** (DoS protection - A04)

### 🟡 MEDIUM Priority

3. **Document encryption options** (Cryptographic Failures - A02)
4. **Add size limits** for JSON deserialization
5. **Improve security logging** for audit trails

### 🟢 LOW Priority

6. Consider SQLCipher integration for encryption at rest
7. Implement rate limiting for bulk operations
8. Add additional security-focused test cases

## Testing Recommendations

Security test coverage:

### ✅ Implemented Tests

**Path Traversal Prevention** (test_path_security.py - 17 tests):
```python
def test_simple_path_traversal_rejected():
    """Path traversal attempts are blocked"""
    with pytest.raises(ValueError, match="Path traversal detected"):
        PropertyGraph("../etc/passwd")

def test_allowed_base_directory():
    """Base directory restriction works"""
    with PropertyGraph("user.db", allowed_base_dir="/var/lib/app"):
        pass  # Only allows paths within /var/lib/app
```

**Resource Monitoring** (test_resource_stats.py - 5 tests):
```python
def test_resource_stats():
    """Monitor database size and entity counts"""
    stats = graph.resource_stats()
    assert stats['node_count'] <= MAX_NODES
    assert stats['db_size_mb'] < MAX_DB_SIZE_MB
```

### 🔧 TODO: Add These Security Tests

**SQL Injection Verification:**
```python
def test_sql_injection_attempts():
    """Ensure SQL injection attempts are safely handled"""
    graph = PropertyGraph()

    # Try SQL injection in node type
    malicious_type = "User'; DROP TABLE resource; --"
    node = graph.add_node(malicious_type, name="test")
    assert node.node_type == malicious_type  # Stored safely

    # Try SQL injection in property value
    node.props["name"] = "'; DELETE FROM resource_props; --"
    assert node.props["name"] == "'; DELETE FROM resource_props; --"
```

**Resource Limits:**
```python
def test_resource_limits():
    """Ensure resource limits prevent DoS"""
    # TODO: Implement configurable limits
    graph = PropertyGraph(max_nodes=10)
    for i in range(10):
        graph.add_node("Test", index=i)

    with pytest.raises(ResourceLimitError):
        graph.add_node("Test", index=11)
```

## Conclusion

PropWeaver demonstrates **excellent security practices** with:
- ✅ Excellent SQL injection prevention (parameterized queries throughout)
- ✅ Safe deserialization practices (json.loads only)
- ✅ Zero external dependencies (minimal attack surface)
- ✅ Proper transaction handling (ACID compliance)
- ✅ **Path traversal protection** (validated paths, optional base directory restriction)
- ✅ **Resource monitoring** (resource_stats() for tracking usage)
- ✅ **Security documentation** (clear warnings and best practices)

**Remaining considerations for production use:**
- ⚠️ No encryption at rest (document encryption options)
- ⚠️ Limited input validation (type names, property sizes)
- ⚠️ No built-in resource limits (monitoring available, enforcement needed)

**Security Posture Update (2025-12-13):**
With the addition of path validation and resource monitoring, PropWeaver has **significantly improved security**. The most critical vulnerability (path traversal) has been fixed with comprehensive test coverage.

**Recommendation:** PropWeaver is now **suitable for production use in controlled environments**. For maximum security with untrusted input:
1. Use `allowed_base_dir` parameter to restrict database locations
2. Monitor resources with `resource_stats()`
3. Implement application-level input validation
4. Use filesystem encryption for sensitive data

---

## References

### OWASP Resources
- [OWASP Top 10 2025](https://owasp.org/Top10/2025/)
- [A05:2025 - Injection](https://owasp.org/Top10/2025/A05_2025-Injection/)
- [SQL Injection Prevention Cheat Sheet](https://owasp.org/www-community/attacks/SQL_Injection)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

### SQLite Security
- [SQLite Security Best Practices](https://dev.to/stephenc222/basic-security-practices-for-sqlite-safeguarding-your-data-23lh)
- [Python SQLite3 Security](https://en.ittrip.xyz/python/sqlite-security-python)
- [Parameterized Queries Guide](https://labex.io/tutorials/python-how-to-use-parameterized-queries-safely-437628)

### Python Security
- [Python SQL Injection Prevention](https://brightsec.com/blog/sql-injection-python/)
- [OWASP Python Security](https://devm.io/python/python-owasp-app-security/)

---

**Audit Completed:** 2025-12-13
**Next Review:** Recommended after any major changes to query system or storage layer
