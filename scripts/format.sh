#!/bin/bash
# Quick formatting script

echo "📐 Formatting code..."
uv run black .
uv run isort .
echo "✅ Code formatted!"