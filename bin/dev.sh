#!/usr/bin/env bash
# Development utilities for PropWeaver (uv-compatible)

set -e  # Exit on error

echo "=== PropWeaver Development Utilities ==="

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Run different development tasks based on arguments
case "${1:-help}" in
    "basic")
        echo "Testing basic functionality..."
        uv run python3 -c "
from propweaver import PropertyGraph
with PropertyGraph() as g:
    user = g.add_node('User', name='Alice')
    print(f'Created: {user}')
    print(f'Graph has {g.node_count()} nodes')
"
        ;;
    "bulk")
        echo "Testing bulk operations..."
        uv run python3 -c "
from propweaver import PropertyGraph
with PropertyGraph() as g:
    g.add_node('TempUser', name='temp1')
    g.add_node('TempUser', name='temp2') 
    deleted = g.nodes('TempUser').delete().execute()
    print(f'Deleted {deleted} temp users')
"
        ;;
    "setup")
        echo "Setting up development environment..."
        uv venv
        uv pip install pytest pytest-cov black isort mypy
        echo "Development environment ready!"
        ;;
    "lint")
        echo "Running code formatting and linting..."
        echo "Installing linting tools..."
        uv pip install black isort mypy
        echo "Running black..."
        uv run black src/ tests/ examples/
        echo "Running isort..."
        uv run isort src/ tests/ examples/
        echo "Running mypy..."
        uv run mypy src/ --ignore-missing-imports
        ;;
    "clean")
        echo "Cleaning up development artifacts..."
        find . -name "*.db" -type f -delete
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -type f -delete
        rm -rf .pytest_cache htmlcov .coverage build
        find dist -mindepth 1 ! -name ".gitignore" -delete 2>/dev/null || true
        echo "Cleanup completed!"
        ;;
    "install")
        echo "Installing PropWeaver in development mode..."
        uv pip install -e .
        echo "PropWeaver installed in development mode!"
        ;;
    "check")
        echo "Running full development checks..."
        echo "1. Code formatting..."
        uv run black --check src/ tests/ examples/
        echo "2. Import sorting..."
        uv run isort --check-only src/ tests/ examples/
        echo "3. Type checking..."
        uv run mypy src/ --ignore-missing-imports
        echo "4. Running tests..."
        uv run pytest tests/ -v
        echo "All checks passed!"
        ;;
    "help"|*)
        echo "Usage: $0 [command]"
        echo ""
        echo "Development Commands:"
        echo "  basic     - Test basic PropWeaver functionality"
        echo "  bulk      - Test bulk operations"
        echo "  setup     - Set up development environment"
        echo "  install   - Install PropWeaver in development mode"
        echo "  lint      - Format code and run linting"
        echo "  check     - Run all development checks"
        echo "  clean     - Clean up development artifacts"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 setup     # First time setup"
        echo "  $0 basic     # Quick functionality test"
        echo "  $0 check     # Full pre-commit checks"
        ;;
esac
