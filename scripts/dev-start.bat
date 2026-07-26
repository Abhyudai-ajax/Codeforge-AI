@echo off
REM Windows Development startup script
REM Starts PostgreSQL, Redis, and the backend service

echo.
echo 🚀 Starting CodeForge AI Development Environment...
echo.

REM Check if Docker is running
docker ps > nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop.
    exit /b 1
)

REM Start services
echo 📦 Starting Docker services...
docker-compose up -d postgres redis

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 5

REM Check PostgreSQL
echo 🔍 Checking PostgreSQL...
:check_postgres
docker exec codeforge-postgres pg_isready -U codeforge > nul 2>&1
if errorlevel 1 (
    echo  Waiting for PostgreSQL...
    timeout /t 2 /nobreak
    goto check_postgres
)
echo ✅ PostgreSQL is ready

REM Check Redis
echo 🔍 Checking Redis...
:check_redis
docker exec codeforge-redis redis-cli ping > nul 2>&1
if errorlevel 1 (
    echo  Waiting for Redis...
    timeout /t 2 /nobreak
    goto check_redis
)
echo ✅ Redis is ready

echo.
echo ✨ Development environment ready!
echo.
echo 📝 Available commands:
echo   - Backend:  cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload
echo   - Frontend: cd frontend ^&^& npm run dev
echo   - Docker:   docker-compose up
echo.
