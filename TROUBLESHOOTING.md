# Troubleshooting Guide

Common issues and their solutions.

## Frontend Issues

### "Cannot find module" errors

**Symptoms**: `Error: Cannot find module '@/...'`

**Solution**:
```bash
# Check tsconfig.json paths configuration
# Should include: "@/*": ["./*"]

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Port 3000 already in use

**Symptoms**: `Error: listen EADDRINUSE :::3000`

**Solution**:
```bash
# Option 1: Kill process using port
lsof -ti:3000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :3000   # Windows

# Option 2: Use different port
npm run dev -- -p 3001
```

### Dependencies not installing

**Symptoms**: `npm ERR!` or `npm WARN`

**Solution**:
```bash
# Clear npm cache
npm cache clean --force

# Delete lock file and reinstall
rm package-lock.json
npm install

# Or use npm ci for exact versions
npm ci
```

### TypeScript errors in IDE

**Symptoms**: Red squiggles in VSCode despite code working

**Solution**:
```bash
# Ensure tsconfig.json is correct
npm run type-check

# Restart TypeScript server (Cmd/Ctrl + Shift + P)
> TypeScript: Restart TS Server

# Or close and reopen VSCode
```

### Build fails in Docker

**Symptoms**: `docker-compose build` fails for frontend

**Solution**:
```bash
# Check Dockerfile.frontend for correct base image
# Ensure npm install is before build

# Build with verbose output
docker-compose build --verbose frontend

# Check Docker file permissions
chmod 755 docker/Dockerfile.frontend
```

---

## Backend Issues

### "ModuleNotFoundError" errors

**Symptoms**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Check PYTHONPATH
echo $PYTHONPATH

# Should include project root
export PYTHONPATH="${PYTHONPATH}:/path/to/backend"
```

### Database connection refused

**Symptoms**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# Verify PostgreSQL is running
docker-compose ps postgres
# or
psql --version

# Test connection
psql postgresql://codeforge:codeforge_password@localhost:5432/codeforge_ai

# If Docker, check network
docker network ls
docker network inspect codeforge-network
```

### Port 8000 already in use

**Symptoms**: `error: address already in use`

**Solution**:
```bash
# Kill process using port
lsof -ti:8000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :8000   # Windows

# Use different port
uvicorn app.main:app --port 8001
```

### Import errors after moving main.py

**Symptoms**: `ImportError: cannot import name 'app'`

**Solution**:
```bash
# Update PYTHONPATH or working directory
cd backend
python -m scripts.init_db

# Update docker-compose.yml
# command: uvicorn app.main:app --reload

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Redis connection errors

**Symptoms**: `ConnectionError: Error -2 connecting to redis`

**Solution**:
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# If Docker
docker-compose ps redis
docker-compose logs redis

# Start Redis if not running
docker-compose up -d redis
```

### Alembic migration issues

**Symptoms**: `alembic.util.exc.CommandError`

**Solution**:
```bash
# Verify alembic.ini exists
ls -la alembic/alembic.ini

# Check migration history
alembic current
alembic history

# Rollback and try again
alembic downgrade base
alembic upgrade head

# Check for syntax errors in migration
cat alembic/versions/*.py
```

### Tests failing

**Symptoms**: `FAILED tests/test_*.py`

**Solution**:
```bash
# Run single test with verbose output
pytest tests/test_api.py::test_health_check -v

# Check test fixtures
pytest --fixtures

# Run with logging
pytest -v --log-cli-level=DEBUG

# Check test database is clean
pytest --cov=app --cov-report=term
```

---

## Docker Issues

### "docker: command not found"

**Solution**:
```bash
# Install Docker
# macOS: brew install docker
# Linux: sudo apt-get install docker.io
# Windows: Download Docker Desktop

# Verify installation
docker --version
docker run hello-world
```

### "Cannot connect to Docker daemon"

**Solution**:
```bash
# macOS/Windows: Start Docker Desktop
# Linux: Start docker service
sudo systemctl start docker

# Check status
docker ps
```

### Container exits immediately

**Symptoms**: `docker-compose up` then container stops

**Solution**:
```bash
# Check logs
docker-compose logs backend

# Check Dockerfile for errors
docker-compose build --verbose

# Try running container directly
docker run -it codeforge-ai-backend /bin/bash

# Check entrypoint
cat docker/Dockerfile.backend | grep CMD
```

### Volume mount issues

**Symptoms**: Files not updating in container

**Solution**:
```bash
# Check docker-compose.yml volumes
cat docker-compose.yml | grep volumes

# Verify volume permissions
docker exec codeforge-backend ls -la /app

# Rebuild without cache
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Network issues between containers

**Symptoms**: `Connection refused` from one container to another

**Solution**:
```bash
# Check network exists
docker network ls | grep codeforge

# Inspect network
docker network inspect codeforge-network

# Services should be able to reach each other using container name
# e.g., from backend: postgresql://postgres:5432/...
```

---

## Environment & Configuration Issues

### Wrong environment variables loaded

**Symptoms**: Features not working as expected

**Solution**:
```bash
# Check current .env
cat .env

# Verify .env is in .gitignore
grep .env .gitignore

# Reload environment
source .env
# or in Python
from dotenv import load_dotenv
load_dotenv(verbose=True)
```

### "SECRET_KEY not set"

**Solution**:
```bash
# Generate secure key
openssl rand -hex 32

# Add to .env
SECRET_KEY=<generated-key>

# Never commit .env to version control
```

### CORS errors in frontend

**Symptoms**: "Access to XMLHttpRequest blocked by CORS"

**Solution**:
```bash
# Check CORS configuration in backend
# See app/core/config.py CORS_ORIGINS

# Update .env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Restart backend after changing
```

---

## Performance Issues

### Slow database queries

**Solution**:
```bash
# Check query logs
# In SQLAlchemy, set DATABASE_ECHO=true

# Analyze slow queries
EXPLAIN ANALYZE SELECT * FROM table;

# Add indexes if needed
# See docs/database/DATABASE.md
```

### High memory usage

**Solution**:
```bash
# Check what's consuming memory
docker stats

# In backend:
# Check connection pool size
# Reduce DATABASE_POOL_SIZE in .env

# Check for memory leaks in code
python -m memory_profiler script.py
```

### Slow API responses

**Solution**:
```bash
# Check response time
curl -w "@curl-format.txt" http://localhost:8000/api/health

# Enable API profiling
# Add middleware to log response times

# Check database performance
# Run EXPLAIN on slow queries
```

---

## Git & Version Control Issues

### "fatal: not a git repository"

**Solution**:
```bash
# Initialize git
git init

# Or clone the repository
git clone https://github.com/your-org/codeforge-ai.git
```

### Large files in git history

**Solution**:
```bash
# Check for large files
git rev-list --all --objects | sort -k 2 | tail -10

# Use .gitignore to prevent new large files
echo "*.log" >> .gitignore
```

### Cannot push due to pre-commit hooks

**Solution**:
```bash
# Fix the code quality issues
npm run lint:fix
npm run format

# Or temporarily skip hooks (not recommended)
git commit --no-verify
```

---

## IDE & Editor Issues

### VSCode not recognizing Python environment

**Solution**:
```bash
# Select interpreter (Cmd/Ctrl + Shift + P)
> Python: Select Interpreter

# Choose venv from list

# If not visible, restart VSCode
# Or manually set in .vscode/settings.json
"python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/bin/python"
```

### ESLint not working in VSCode

**Solution**:
```bash
# Install ESLint extension
code --install-extension dbaeumer.vscode-eslint

# Verify package.json has eslint
cat frontend/package.json | grep eslint

# Reload VSCode
```

### Prettier formatting not working

**Solution**:
```bash
# Install Prettier extension
code --install-extension esbenp.prettier-vscode

# Set as default formatter (Cmd/Ctrl + ,)
> default formatter = Prettier

# Or use keyboard shortcut
# Shift + Alt + F (Windows/Linux)
# Shift + Option + F (macOS)
```

---

## Getting Help

1. **Check Documentation**: Read [GETTING_STARTED.md](GETTING_STARTED.md)
2. **Search Issues**: Look for similar problems on GitHub
3. **Check Logs**: 
   ```bash
   docker-compose logs -f
   npm run dev 2>&1 | head -100
   ```
4. **Search Online**: Stack Overflow, GitHub discussions
5. **Create Issue**: Provide:
   - Error message (full)
   - Steps to reproduce
   - Environment info (OS, versions)
   - What you've tried

---

## Still Stuck?

Create a GitHub issue with:

```markdown
## Problem
[Describe what's happening]

## Expected behavior
[What should happen]

## Steps to reproduce
1. [First step]
2. [Second step]

## Environment
- OS: [Your OS]
- Node: [node --version]
- Python: [python --version]
- Docker: [docker --version]

## Error logs
[Paste full error messages]

## What I've tried
[What troubleshooting steps you've taken]
```

---

**Last updated: 2024-07-23**
