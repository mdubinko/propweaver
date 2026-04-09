"""
Security tests for path validation and directory traversal prevention
"""

import tempfile
from pathlib import Path

import pytest

from propweaver import PropertyGraph


class TestPathTraversalPrevention:
    """Test that path traversal attacks are prevented"""

    def test_simple_path_traversal_rejected(self):
        """Test that simple ../ paths are rejected"""
        with pytest.raises(ValueError, match="Path traversal detected"):
            PropertyGraph("../etc/passwd")

    def test_complex_path_traversal_rejected(self):
        """Test that complex traversal paths are rejected"""
        with pytest.raises(ValueError, match="Path traversal detected"):
            PropertyGraph("../../../../../../etc/passwd")

    def test_hidden_path_traversal_rejected(self):
        """Test that hidden traversal attempts are rejected"""
        with pytest.raises(ValueError, match="Path traversal detected"):
            PropertyGraph("./data/../../../etc/passwd")

    def test_relative_parent_path_rejected(self):
        """Test that any path with .. is rejected"""
        with pytest.raises(ValueError, match="Path traversal detected"):
            PropertyGraph("data/../database.db")

    def test_special_sqlite_paths_allowed(self):
        """Test that special SQLite paths are not affected"""
        # These should work without validation errors
        with PropertyGraph(":memory:") as graph:
            assert graph.node_count() == 0

        with PropertyGraph() as graph:  # None -> :memory:
            assert graph.node_count() == 0

        with PropertyGraph("") as graph:  # Empty string -> temp file
            assert graph.node_count() == 0

    def test_absolute_paths_allowed(self):
        """Test that absolute paths without traversal are allowed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            with PropertyGraph(db_path) as graph:
                graph.add_node("Test", value=1)
                assert graph.node_count() == 1

            # Verify file was created
            assert Path(db_path).exists()

    def test_simple_relative_paths_allowed(self):
        """Test that simple relative paths without .. are converted to absolute"""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)

                # Simple relative path (no ..)
                with PropertyGraph("test.db") as graph:
                    graph.add_node("Test", value=1)
                    # Should be converted to absolute path
                    assert Path(graph._storage.db_path).is_absolute()

            finally:
                os.chdir(old_cwd)


class TestAllowedBaseDirectory:
    """Test optional base directory restriction"""

    def test_path_within_allowed_directory(self):
        """Test that paths within allowed directory are accepted"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test.db")

            with PropertyGraph(db_path, allowed_base_dir=tmpdir) as graph:
                graph.add_node("Test", value=1)
                assert graph.node_count() == 1

    def test_path_outside_allowed_directory_rejected(self):
        """Test that paths outside allowed directory are rejected"""
        with tempfile.TemporaryDirectory() as allowed_dir:
            with tempfile.TemporaryDirectory() as other_dir:
                db_path = str(Path(other_dir) / "test.db")

                with pytest.raises(ValueError, match="must be within"):
                    PropertyGraph(db_path, allowed_base_dir=allowed_dir)

    def test_allowed_directory_prevents_traversal(self):
        """Test that allowed_base_dir prevents traversal outside directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Even if we try to use a path that traverses outside
            with pytest.raises(ValueError, match="Path traversal detected"):
                PropertyGraph(
                    str(Path(tmpdir) / "../etc/passwd"), allowed_base_dir=tmpdir
                )

    def test_subdirectories_within_base_allowed(self):
        """Test that subdirectories within base are allowed"""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = Path(tmpdir) / "databases" / "users"
            subdir.mkdir(parents=True)

            db_path = str(subdir / "user_123.db")

            with PropertyGraph(db_path, allowed_base_dir=tmpdir) as graph:
                graph.add_node("User", id=123)
                assert graph.node_count() == 1

    def test_special_paths_bypass_allowed_directory(self):
        """Test that special SQLite paths bypass allowed_base_dir restriction"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # :memory: should work even with allowed_base_dir
            with PropertyGraph(":memory:", allowed_base_dir=tmpdir) as graph:
                assert graph.node_count() == 0

            # Empty string (temp file) should also work
            with PropertyGraph("", allowed_base_dir=tmpdir) as graph:
                assert graph.node_count() == 0


class TestSecurePathExamples:
    """Test realistic secure usage patterns"""

    def test_user_database_isolation(self):
        """Test pattern for isolating user databases"""
        with tempfile.TemporaryDirectory() as base_dir:
            # Simulate multi-tenant application
            users = ["alice", "bob", "charlie"]

            for username in users:
                # Each user gets their own database
                db_path = str(Path(base_dir) / f"user_{username}.db")

                with PropertyGraph(db_path, allowed_base_dir=base_dir) as graph:
                    graph.add_node("User", name=username)
                    assert graph.node_count() == 1

            # Verify all databases were created
            assert len(list(Path(base_dir).glob("user_*.db"))) == 3

    def test_malicious_username_rejected(self):
        """Test that malicious usernames are rejected"""
        with tempfile.TemporaryDirectory() as base_dir:
            # Attacker tries to use ../ in username
            malicious_username = "../../../etc/passwd"

            with pytest.raises(ValueError, match="Path traversal detected"):
                db_path = str(Path(base_dir) / f"user_{malicious_username}.db")
                PropertyGraph(db_path, allowed_base_dir=base_dir)

    def test_path_normalization(self):
        """Test that paths are normalized to absolute paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create subdirectory
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()

            # Create with relative path components (contains . which should be normalized)
            db_path = str(data_dir / "." / "test.db")

            with PropertyGraph(db_path) as graph:
                # Path should be normalized to absolute
                assert Path(graph._storage.db_path).is_absolute()
                # Should not contain . or .. components in normalized form
                assert "/./" not in graph._storage.db_path
                # The path should end with test.db
                assert graph._storage.db_path.endswith("test.db")


class TestErrorMessages:
    """Test that error messages are informative"""

    def test_traversal_error_message(self):
        """Test that traversal attempts have clear error messages"""
        with pytest.raises(ValueError) as exc_info:
            PropertyGraph("../etc/passwd")

        assert "Path traversal detected" in str(exc_info.value)
        assert "Use absolute paths" in str(exc_info.value)

    def test_outside_base_error_message(self):
        """Test that outside-base errors have clear messages"""
        with tempfile.TemporaryDirectory() as allowed_dir:
            with tempfile.TemporaryDirectory() as other_dir:
                db_path = str(Path(other_dir) / "test.db")

                with pytest.raises(ValueError) as exc_info:
                    PropertyGraph(db_path, allowed_base_dir=allowed_dir)

                assert "must be within" in str(exc_info.value)
                assert allowed_dir in str(exc_info.value)
