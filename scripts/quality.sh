#!/bin/bash
# Code quality check script

set -e

echo "🔍 Running code quality checks..."
echo

# Format code with black
echo "📐 Formatting code with Black..."
uv run black .

# Sort imports with isort
echo "🔄 Sorting imports with isort..."
uv run isort .

# Run flake8 for linting
echo "🧹 Running flake8 linter..."
uv run flake8 .

# Run mypy for type checking
echo "🔍 Running mypy type checker..."
uv run mypy backend/ --ignore-missing-imports --disable-error-code=import-untyped

echo
echo "✅ All code quality checks passed!"