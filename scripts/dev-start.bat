@echo off
REM Windows Development startup script
REM Starts PostgreSQL, Redis, and the backend service

setlocal
echo.
echo 🚀 Starting CodeForge AI Development Environment...
echo.

REM Detect Docker Compose command (supports both modern 'docker compose' and legacy 'docker-compose')
docker compose version > nul 2>&1
if not errorlevel 1 (
    set "COMPOSE_CMD=docker compose"
) else (
    docker-compose version > nul 2>&1
    if not errorlevel 1 (
        set "COMPOSE_CMD=docker-compose"
    ) else (
        echo ❌ Docker Desktop is not installed or Docker is not in PATH.
        echo Please install Docker Desktop and restart the terminal.
        exit /b 1
    )
)

REM Check if Docker daemon is running
docker info > nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop.
    exit /b 1
)

REM Start services
echo 📦 Starting Docker services...
call %COMPOSE_CMD% up -d postgres redis

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
echo   - Docker:   %COMPOSE_CMD% up
echo.
