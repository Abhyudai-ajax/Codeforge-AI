# Getting Started - Full Stack Setup

## Prerequisites

- **Node.js** >= 18.17.0
- **npm** >= 9.0.0
- **Python** 3.12+
- **PostgreSQL** 16+ (or use Docker)
- **Redis** 7+ (or use Docker)
- **Docker** & **Docker Compose** (recommended)
- **Git**

## Quick Start (Recommended - Docker)

### 1. Clone and setup

```bash
cd codeforge-ai
cp .env.example .env
```

### 2. Start services

```bash
# Start backend services (PostgreSQL, Redis)
make docker-up

# Or manually:
docker-compose up -d postgres redis
```

### 3. Install dependencies

```bash
# Frontend
cd frontend
npm install

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start development servers

```bash
# Terminal 1: Frontend
cd frontend
npm run dev
# → http://localhost:3000

# Terminal 2: Backend
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# → http://localhost:8000
# → API docs: http://localhost:8000/api/docs
```

## Using Makefile Commands

```bash
# Install everything
make install

# Start all services
make dev

# Stop all services
make dev-stop

# Start frontend only
make dev-frontend

# Start backend only
make dev-backend

# Code quality
make lint
make format
make type-check

# Testing
make test
make test-backend-cov

# Database
make db-init
make db-migrate

# Clean up
make clean
```

## Full Docker Compose Setup

```bash
# Start everything in containers
docker-compose up --build

# Services:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
# Postgres: localhost:5432
# Redis: localhost:6379

# With Celery workers
docker-compose --profile workers up
```

## Frontend Setup (Detailed)

### 1. Navigate to frontend

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Environment setup

```bash
# Create .env.local (ignored by git)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 4. Run development server

```bash
npm run dev
# Open http://localhost:3000
```

### 5. Other useful commands

```bash
npm run build          # Build for production
npm run start          # Start production server
npm run lint           # Run ESLint
npm run format         # Format with Prettier
npm run type-check     # TypeScript check
npm test               # Run tests
```

## Backend Setup (Detailed)

### 1. Navigate to backend

```bash
cd backend
```

### 2. Create virtual environment

```bash
# macOS/Linux
python3.12 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment setup

Create `.env` file:

```bash
cp ../.env.example .env

# Edit .env with your local settings
# KEY settings:
# - DATABASE_URL (PostgreSQL)
# - REDIS_URL (Redis)
# - ENV=development
```

### 5. Database setup

```bash
# Option 1: Using Docker
docker-compose up -d postgres redis

# Option 2: Manual PostgreSQL setup
createdb codeforge_ai
```

### 6. Run development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access:
- API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/api/docs
- API ReDoc: http://localhost:8000/api/redoc

### 7. Other useful commands

```bash
# Database initialization
python -m scripts.init_db

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Code formatting
black app

# Import sorting
isort app

# Linting
flake8 app

# Type checking
mypy app
```

## Database Setup

### Using Docker (Recommended)

```bash
docker-compose up -d postgres

# Check connection
psql postgresql://codeforge:codeforge_password@localhost:5432/codeforge_ai
```

### Manual PostgreSQL Setup

```bash
# macOS with Homebrew
brew install postgresql
brew services start postgresql
createdb codeforge_ai

# Linux (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb codeforge_ai

# Windows
# Download and install from https://www.postgresql.org/download/windows/
createdb codeforge_ai
```

## Redis Setup

### Using Docker (Recommended)

```bash
docker-compose up -d redis

# Test connection
redis-cli ping
# → PONG
```

### Manual Redis Setup

```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis-server

# Windows
# Download from https://github.com/microsoftarchive/redis/releases
# Or use Docker
```

## Common Issues

### Issue: "Connection refused" to database

**Solution**: Make sure PostgreSQL is running
```bash
docker-compose up -d postgres
# or
psql --version  # to verify installation
```

### Issue: "Connection refused" to Redis

**Solution**: Make sure Redis is running
```bash
docker-compose up -d redis
# or
redis-cli ping
```

### Issue: Port already in use

**Solution**: Change port in configuration or stop conflicting service
```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8001  # Change port

# Backend
uvicorn app.main:app --port 8001
```

### Issue: Module not found (Python)

**Solution**: Activate virtual environment
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Issue: npm dependencies issues

**Solution**: Clear npm cache and reinstall
```bash
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## Next Steps

1. Read the [Architecture Guide](docs/architecture/ARCHITECTURE.md)
2. Check [API Documentation](docs/api/API_REFERENCE.md)
3. Review [Contributing Guidelines](CONTRIBUTING.md)
4. Start building features!

## Support

- Check existing GitHub issues
- Create a new issue with details
- Join our community discussions
