#!/bin/bash

set -e

echo "======================================"
echo "VisiSense - CatalogIQ Setup Script"
echo "======================================"
echo ""

if [ ! -f .env.example ]; then
    echo "Error: .env.example not found"
    exit 1
fi

if [ ! -f backend/.env ]; then
    echo "Creating backend/.env from .env.example..."
    cp .env.example backend/.env
    echo "✓ Created backend/.env"
    echo ""
    echo "⚠️  IMPORTANT: Edit backend/.env and configure your LLM provider"
    echo ""
    echo "Options:"
    echo "  1. OpenAI (Production quality)"
    echo "  2. Groq (Fast & Free tier)"
    echo "  3. Ollama (Local/Private)"
    echo "  4. OpenRouter (Multiple models)"
    echo ""
else
    echo "backend/.env already exists, skipping..."
fi

echo "Checking dependencies..."
echo ""

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    echo "Install from: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✓ Docker installed"

if ! command -v docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi
echo "✓ Docker Compose installed"

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit backend/.env with your LLM provider credentials"
echo "  2. Run: docker compose up -d"
echo "  3. Access frontend at: http://localhost:5173"
echo ""
