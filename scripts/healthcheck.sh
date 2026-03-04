#!/bin/bash

echo "Checking VisiSense - CatalogIQ services..."

echo ""
echo "Frontend (port 3000):"
curl -s http://localhost:3000 > /dev/null && echo "✓ Running" || echo "✗ Not running"

echo ""
echo "Backend (port 8000):"
curl -s http://localhost:8000/api/v1/health > /dev/null && echo "✓ Running" || echo "✗ Not running"

echo ""
echo "Ollama (port 11434):"
curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Running" || echo "✗ Not running"

echo ""
echo "Health check complete!"
