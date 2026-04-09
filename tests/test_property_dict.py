"""
Tests for dict-like property interface functionality.
"""

import warnings

import pytest


class TestPropertyDictInterface:
    """Tests for the new dict-like property access"""

    def test_graph_property_dict_access(self, graph):
        """Test dict-like access to graph properties"""
        # Set properties using dict interface
        graph.props["project_name"] = "PropWeaver"
        graph.props["version"] = "0.2.0"
        graph.props["active"] = True

        # Get properties using dict interface
        assert graph.props["project_name"] == "PropWeaver"
        assert graph.props["version"] == "0.2.0"
        assert graph.props["active"] == True

    def test_node_property_dict_access(self, graph):
        """Test dict-like access to node properties"""
        user = graph.add_node("User", name="Alice", age=30)

        # Update properties using dict interface
        user.props["age"] = 31
        user.props["verified"] = True

        # Verify updates
        assert user.props["age"] == 31
        assert user.props["verified"] == True
        assert user.props["name"] == "Alice"  # Original property preserved

    def test_edge_property_dict_access(self, graph):
        """Test dict-like access to edge properties"""
        alice = graph.add_node("User", name="Alice")
        project = graph.add_node("Project", name="Web App")
        edge = graph.add_edge(alice, "WORKS_ON", project, role="Lead")

        # Update properties using dict interface
        edge.props["since"] = "2023-01-01"
        edge.props["active"] = True

        # Verify updates
        assert edge.props["role"] == "Lead"
        assert edge.props["since"] == "2023-01-01"
        assert edge.props["active"] == True


class TestPropertyDictDeletion:
    """Tests for property deletion via dict interface"""

    def test_delete_node_property(self, graph):
        """Test deleting node properties with del"""
        user = graph.add_node("User", name="Alice", temp_token="abc123", age=30)

        # Verify property exists
        assert "temp_token" in user.props
        assert user.props["temp_token"] == "abc123"

        # Delete property
        del user.props["temp_token"]

        # Verify property is gone
        assert "temp_token" not in user.props
        assert user.props.get("temp_token") is None

        # Other properties should remain
        assert user.props["name"] == "Alice"
        assert user.props["age"] == 30

    def test_delete_edge_property(self, graph):
        """Test deleting edge properties with del"""
        alice = graph.add_node("User", name="Alice")
        project = graph.add_node("Project", name="Web App")
        edge = graph.add_edge(alice, "WORKS_ON", project, role="Lead", temp_field="temporary")

        # Delete property
        del edge.props["temp_field"]

        # Verify deletion
        assert "temp_field" not in edge.props
        assert edge.props["role"] == "Lead"  # Other properties remain

    def test_delete_graph_property(self, graph):
        """Test deleting graph properties with del"""
        graph.props["temp_config"] = "test"
        graph.props["project_name"] = "PropWeaver"

        # Delete property
        del graph.props["temp_config"]

        # Verify deletion
        assert "temp_config" not in graph.props
        assert graph.props["project_name"] == "PropWeaver"

    def test_delete_nonexistent_property_raises_keyerror(self, graph):
        """Test that deleting non-existent property raises KeyError"""
        user = graph.add_node("User", name="Alice")

        with pytest.raises(KeyError):
            del user.props["nonexistent"]


class TestPropertyDictMethods:
    """Tests for dict methods on property interface"""

    def test_property_keys(self, graph):
        """Test getting property keys"""
        user = graph.add_node("User", name="Alice", age=30, active=True)

        keys = list(user.props.keys())
        assert "name" in keys
        assert "age" in keys
        assert "active" in keys
        assert len(keys) == 3

    def test_property_values(self, graph):
        """Test getting property values"""
        user = graph.add_node("User", name="Alice", age=30)

        values = list(user.props.values())
        assert "Alice" in values
        assert 30 in values
        assert len(values) == 2

    def test_property_items(self, graph):
        """Test getting property items"""
        user = graph.add_node("User", name="Alice", age=30)

        items = list(user.props.items())
        assert ("name", "Alice") in items
        assert ("age", 30) in items
        assert len(items) == 2

    def test_property_len(self, graph):
        """Test getting property count with len()"""
        user = graph.add_node("User", name="Alice", age=30, active=True)
        assert len(user.props) == 3

        # Add property
        user.props["verified"] = True
        assert len(user.props) == 4

        # Delete property
        del user.props["active"]
        assert len(user.props) == 3

    def test_property_contains(self, graph):
        """Test property existence with 'in' operator"""
        user = graph.add_node("User", name="Alice", age=30)

        assert "name" in user.props
        assert "age" in user.props
        assert "nonexistent" not in user.props

    def test_property_get_with_default(self, graph):
        """Test get() method with default values"""
        user = graph.add_node("User", name="Alice")

        assert user.props.get("name") == "Alice"
        assert user.props.get("age", 0) == 0
        assert user.props.get("nonexistent") is None
        assert user.props.get("nonexistent", "default") == "default"

    def test_property_iteration(self, graph):
        """Test iterating over properties"""
        user = graph.add_node("User", name="Alice", age=30, active=True)

        # Iteration should yield keys
        keys = list(user.props)
        assert "name" in keys
        assert "age" in keys
        assert "active" in keys
        assert len(keys) == 3

    def test_property_update(self, graph):
        """Test bulk property update"""
        user = graph.add_node("User", name="Alice", age=30)

        # Bulk update
        user.props.update({"age": 31, "verified": True, "last_login": "2023-12-01"})

        assert user.props["age"] == 31
        assert user.props["verified"] == True
        assert user.props["last_login"] == "2023-12-01"
        assert user.props["name"] == "Alice"  # Original preserved

    def test_property_clear(self, graph):
        """Test clearing all properties"""
        user = graph.add_node("User", name="Alice", age=30, active=True)
        assert len(user.props) == 3

        # Clear all properties
        user.props.clear()
        assert len(user.props) == 0
        assert "name" not in user.props
        assert "age" not in user.props

    def test_property_copy(self, graph):
        """Test copying properties to regular dict"""
        user = graph.add_node("User", name="Alice", age=30, active=True)

        props_copy = user.props.copy()
        assert isinstance(props_copy, dict)
        assert props_copy["name"] == "Alice"
        assert props_copy["age"] == 30
        assert props_copy["active"] == True

        # Should be independent copy
        user.props["age"] = 31
        assert props_copy["age"] == 30  # Original copy unchanged


class TestPropertyDictErrorHandling:
    """Tests for error conditions in property dict interface"""

    def test_getitem_missing_key_raises_keyerror(self, graph):
        """Test that accessing missing property raises KeyError"""
        user = graph.add_node("User", name="Alice")

        with pytest.raises(KeyError):
            _ = user.props["nonexistent"]

    def test_property_type_preservation(self, graph):
        """Test that property types are preserved correctly"""
        user = graph.add_node("User", name="Alice")

        # Test different types
        user.props["age"] = 30
        user.props["height"] = 5.8
        user.props["active"] = True
        user.props["tags"] = ["admin", "user"]
        user.props["metadata"] = {"role": "admin"}

        assert isinstance(user.props["age"], int)
        assert isinstance(user.props["height"], float)
        assert isinstance(user.props["active"], bool)
        assert isinstance(user.props["tags"], list)
        assert isinstance(user.props["metadata"], dict)

    def test_property_none_values_rejected(self, graph):
        """Test that None property values are properly rejected"""
        user = graph.add_node("User", name="Alice")

        # None values should be rejected with helpful error message
        with pytest.raises(ValueError, match="None values are not allowed"):
            user.props["optional_field"] = None

        # Missing keys should return None via get()
        assert user.props.get("missing_field") is None
        assert user.props.get("missing_field", "default") == "default"
