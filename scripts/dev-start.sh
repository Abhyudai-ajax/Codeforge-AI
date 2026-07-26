#!/bin/bash
# Development startup script
# Starts PostgreSQL, Redis, and the backend service

set -e

echo "🚀 Starting CodeForge AI Development Environment..."

# Check if Docker is running
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not in PATH"
    exit 1
fi

# Start services
echo "📦 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
while ! docker exec codeforge-postgres pg_isready -U codeforge > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check Redis
echo "🔍 Checking Redis..."
while ! docker exec codeforge-redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 2
done
echo "✅ Redis is ready"

echo ""
echo "✨ Development environment ready!"
echo ""
echo "📝 Available commands:"
echo "  - Backend:  cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "  - Frontend: cd frontend && npm run dev"
echo "  - Docker:   docker-compose up"
