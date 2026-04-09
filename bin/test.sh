#!/usr/bin/env bash
# Test runner for PropWeaver development (uv-compatible)

set -e  # Exit on error

echo "=== PropWeaver Test Suite ==="

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "🔧 Creating virtual environment..."
    uv venv
fi

# Ensure test dependencies are installed
echo "🔧 Ensuring test dependencies..."
uv pip install pytest pytest-cov

# Run different test suites based on arguments
case "${1:-all}" in
    "all")
        echo "Running all tests..."
        uv run pytest tests/ -v
        ;;
    "fast")
        echo "Running fast tests (excluding integration)..."
        uv run pytest tests/ -v -m "not integration"
        ;;
    "integration")
        echo "Running integration tests..."
        uv run pytest tests/test_integration.py -v
        ;;
    "coverage")
        echo "Running tests with coverage..."
        uv run pytest tests/ --cov=src/propweaver --cov-report=html --cov-report=term
        ;;
    "comprehensive")
        echo "Running comprehensive test suite..."
        uv run python3 tests/test_propweaver.py
        ;;
    "brief")
        echo "Running comprehensive test suite (brief output)..."
        uv run python3 tests/test_propweaver.py --brief
        ;;
    *)
        echo "Usage: $0 [all|fast|integration|coverage|comprehensive|brief]"
        echo "  all           - Run all pytest tests (default)"
        echo "  fast          - Run tests excluding integration"
        echo "  integration   - Run only integration tests"
        echo "  coverage      - Run tests with coverage report"
        echo "  comprehensive - Run comprehensive test suite"
        echo "  brief         - Run comprehensive test suite (token-efficient output)"
        exit 1
        ;;
esac

echo "✅ Tests completed!"