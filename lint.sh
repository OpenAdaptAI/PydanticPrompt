#!/bin/bash
set -e

# Format code
echo "Formatting code with ruff..."
ruff format .

# Fix auto-fixable issues (including unsafe fixes for typing upgrades)
echo "Fixing issues with ruff..."
ruff check --fix --unsafe-fixes .

# Run the linter to show any remaining issues
echo "Running final check..."
ruff check .

# Type checking
echo "Type-checking with mypy..."
mypy pydantic_prompt

echo "All checks completed!"