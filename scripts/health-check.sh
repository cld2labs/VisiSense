#!/bin/bash

echo "======================================"
echo "VisiSense - CatalogIQ Health Check"
echo "======================================"
echo ""

echo "Checking services..."
echo ""

echo "1. Backend Service"
if curl -f -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "   ✓ Backend is healthy (http://localhost:8001)"
else
    echo "   ✗ Backend is not responding"
    echo "     Check: docker compose logs backend"
fi
echo ""

echo "2. Frontend Service"
if curl -f -s http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✓ Frontend is accessible (http://localhost:5173)"
else
    echo "   ✗ Frontend is not responding"
    echo "     Check: docker compose logs frontend"
fi
echo ""

echo "3. Vision Provider"
PROVIDER_STATUS=$(curl -s http://localhost:8001/ | grep -o '"llm_provider":"[^"]*"' | cut -d'"' -f4)
if [ -n "$PROVIDER_STATUS" ]; then
    echo "   ✓ Provider configured: $PROVIDER_STATUS"
else
    echo "   ✗ Could not determine provider"
fi
echo ""

echo "======================================"
echo "Service URLs:"
echo "  - Frontend:  http://localhost:5173"
echo "  - Backend:   http://localhost:8001"
echo "  - API Docs:  http://localhost:8001/docs"
echo "======================================"
