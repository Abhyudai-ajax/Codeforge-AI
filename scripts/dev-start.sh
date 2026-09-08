#!/bin/bash
# Development startup script
# Starts PostgreSQL, Redis, and the backend service

set -e

echo "🚀 Starting CodeForge AI Development Environment..."

# Prefer the modern Docker Compose plugin, but allow the legacy standalone binary.
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo "❌ Docker Desktop is not installed or Docker is not in PATH"
    echo "Please install Docker Desktop and restart the terminal."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start services
echo "📦 Starting Docker services..."
"${COMPOSE_CMD[@]}" up -d postgres redis

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
while ! docker exec codeforge-postgres pg_isready -U codeforge >/dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo "✅ PostgreSQL is ready"

# Check Redis
echo "🔍 Checking Redis..."
while ! docker exec codeforge-redis redis-cli ping >/dev/null 2>&1; do
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
echo "  - Docker:   ${COMPOSE_CMD[*]} up"
