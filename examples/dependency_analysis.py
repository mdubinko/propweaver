#!/usr/bin/env python3
"""
Dependency Analysis Example for PropWeaver

Demonstrates how to model and analyze file dependencies, imports, and project structure.
"""

import sys
from pathlib import Path

# Add src to Python path for examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from propweaver import PropertyGraph


def main():
    """Dependency analysis example with files and imports"""
    print("=== Dependency Analysis Example ===\n")

    with PropertyGraph() as graph:  # Use in-memory for examples
        # Create source files
        print("Creating source files...")
        main_py = graph.add_node(
            "File", path="main.py", language="python", lines=120, type="application"
        )
        utils_py = graph.add_node(
            "File", path="utils.py", language="python", lines=85, type="utility"
        )
        models_py = graph.add_node(
            "File", path="models.py", language="python", lines=200, type="model"
        )
        api_py = graph.add_node(
            "File", path="api.py", language="python", lines=150, type="interface"
        )
        config_py = graph.add_node(
            "File", path="config.py", language="python", lines=45, type="configuration"
        )

        # Create some test files
        test_utils_py = graph.add_node(
            "File", path="test_utils.py", language="python", lines=60, type="test"
        )
        test_models_py = graph.add_node(
            "File", path="test_models.py", language="python", lines=95, type="test"
        )

        # Create some temporary files that we'll clean up later
        temp1 = graph.add_node(
            "File", path="/tmp/temp_data_1.py", language="python", lines=10, type="temp"
        )
        temp2 = graph.add_node(
            "File", path="/tmp/temp_processing.py", language="python", lines=15, type="temp"
        )

        print(f"✅ Created 9 files")

        # Create import relationships
        print("\nCreating import dependencies...")
        graph.add_edge(main_py, "IMPORTS", utils_py, line=3, type="direct")
        graph.add_edge(main_py, "IMPORTS", models_py, line=4, type="direct")
        graph.add_edge(main_py, "IMPORTS", api_py, line=5, type="direct")
        graph.add_edge(main_py, "IMPORTS", config_py, line=2, type="direct")

        graph.add_edge(api_py, "IMPORTS", models_py, line=8, type="direct")
        graph.add_edge(api_py, "IMPORTS", utils_py, line=9, type="direct")

        graph.add_edge(models_py, "IMPORTS", utils_py, line=12, type="direct")
        graph.add_edge(models_py, "IMPORTS", config_py, line=6, type="direct")

        # Test file dependencies
        graph.add_edge(test_utils_py, "IMPORTS", utils_py, line=1, type="test")
        graph.add_edge(test_models_py, "IMPORTS", models_py, line=1, type="test")
        graph.add_edge(test_models_py, "IMPORTS", utils_py, line=2, type="test")

        print(f"✅ Created import relationships")

        # Query examples
        print("\n=== Dependency Analysis ===")

        # Find all files by type
        app_files = list(graph.nodes("File", type="application"))
        util_files = list(graph.nodes("File", type="utility"))
        test_files = list(graph.nodes("File", type="test"))
        temp_files = list(graph.nodes("File", type="temp"))

        print(f"\nFile breakdown:")
        print(f"  - Application files: {len(app_files)}")
        print(f"  - Utility files: {len(util_files)}")
        print(f"  - Test files: {len(test_files)}")
        print(f"  - Temporary files: {len(temp_files)}")

        # Find dependencies for main.py
        main_imports = []
        for edge in graph.edges("IMPORTS"):
            if edge.src_id == main_py.node_id:
                # Find the imported file by ID
                for file_node in graph.nodes("File"):
                    if file_node.node_id == edge.dst_id:
                        main_imports.append(file_node.props["path"])
                        break

        print(f"\nmain.py directly imports {len(main_imports)} files:")
        for imp in main_imports:
            print(f"  - {imp}")

        # Find most imported file
        import_counts = {}
        for edge in graph.edges("IMPORTS"):
            # Find the imported file by ID
            for file_node in graph.nodes("File"):
                if file_node.node_id == edge.dst_id:
                    path = file_node.props["path"]
                    import_counts[path] = import_counts.get(path, 0) + 1
                    break

        if import_counts:
            most_imported = max(import_counts.items(), key=lambda x: x[1])
            print(f"\nMost imported file: {most_imported[0]} ({most_imported[1]} imports)")

        # Find total lines of code
        total_lines = sum(
            file.props["lines"] for file in graph.nodes("File") if file.props["type"] != "temp"
        )
        print(f"\nTotal lines of code (excluding temp files): {total_lines}")

        # Clean up temporary files
        print(f"\n=== Cleanup Operations ===")
        temp_files_before = len(list(graph.nodes("File", type="temp")))
        print(f"Temporary files before cleanup: {temp_files_before}")

        # Bulk delete temporary files
        deleted_count = graph.nodes("File", type="temp").delete().execute()
        print(f"✅ Deleted {deleted_count} temporary files")

        temp_files_after = len(list(graph.nodes("File", type="temp")))
        print(f"Temporary files after cleanup: {temp_files_after}")

        # Clean up files in /tmp/ directory using path filter
        temp_path_files = [f for f in graph.nodes("File") if f.props["path"].startswith("/tmp/")]
        print(f"Files in /tmp/ after type cleanup: {len(temp_path_files)}")

        # Set graph metadata
        graph.props.update(
            {
                "project_type": "python_application",
                "total_files": graph.node_count(),
                "total_imports": graph.edge_count(),
                "analysis_version": "2.0",
            }
        )

        # Show property management examples
        print(f"\n=== Property Management Examples ===")
        main_py.props["analyzed_at"] = "2023-12-01"
        print(f"Main.py has {len(main_py.props)} properties")

        # Clean up analysis metadata
        del main_py.props["analyzed_at"]
        print("Cleaned up temporary analysis metadata")

        print(f"\n✅ Dependency analysis completed!")
        print(
            f"Analyzed {graph.props['total_files']} files with {graph.props['total_imports']} import relationships"
        )


if __name__ == "__main__":
    main()
