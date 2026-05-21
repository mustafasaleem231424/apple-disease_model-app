#!/bin/bash
set -e

echo "🍎 Apple Disease Detector - Deployment Script"
echo "=============================================="

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required"; exit 1; }

# Load environment
if [ -f .env ]; then
    echo "✅ Loading .env configuration"
    export $(cat .env | grep -v '#' | xargs)
else
    echo "⚠️  No .env file found, using defaults"
    cp backend/.env.example .env
fi

# Build and start
echo "🔨 Building services..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

# Health check
echo "⏳ Waiting for services to start..."
sleep 10

echo "🔍 Checking health..."
if curl -f http://localhost:8000/ping >/dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    docker-compose logs backend
    exit 1
fi

if curl -f http://localhost/ >/dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    docker-compose logs frontend
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "📱 Frontend: http://localhost"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
