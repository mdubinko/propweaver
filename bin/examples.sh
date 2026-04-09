#!/usr/bin/env bash
# Example runner for PropWeaver development (uv-compatible)

set -e  # Exit on error

echo "=== PropWeaver Examples ==="

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Run different examples based on arguments
case "${1:-all}" in
    "all")
        echo "Running all examples..."
        echo "--- Social Network Example ---"
        uv run python3 examples/social_network.py
        echo
        echo "--- Knowledge Graph Example ---"
        uv run python3 examples/knowledge_graph.py
        echo
        echo "--- Dependency Analysis Example ---"
        uv run python3 examples/dependency_analysis.py
        echo
        echo "--- Schema Inspection Example ---"
        uv run python3 examples/schema_inspection.py
        echo
        echo "--- Resource Monitoring Example ---"
        uv run python3 examples/resource_monitoring.py
        ;;
    "social")
        echo "Running social network example..."
        uv run python3 examples/social_network.py
        ;;
    "knowledge")
        echo "Running knowledge graph example..."
        uv run python3 examples/knowledge_graph.py
        ;;
    "deps")
        echo "Running dependency analysis example..."
        uv run python3 examples/dependency_analysis.py
        ;;
    "schema")
        echo "Running schema inspection example..."
        uv run python3 examples/schema_inspection.py
        ;;
    "resources"|"resource")
        echo "Running resource monitoring example..."
        uv run python3 examples/resource_monitoring.py
        ;;
    "list")
        echo "Available examples:"
        find examples/ -name "*.py" | sed 's/examples\//  /' | sed 's/\.py//'
        ;;
    *)
        echo "Usage: $0 [all|social|knowledge|deps|schema|resources|list]"
        echo "  all       - Run all examples (default)"
        echo "  social    - Run social network example"
        echo "  knowledge - Run knowledge graph example"
        echo "  deps      - Run dependency analysis example"
        echo "  schema    - Run schema inspection example"
        echo "  resources - Run resource monitoring example"
        echo "  list      - List available examples"
        exit 1
        ;;
esac

echo "✅ Examples completed!"