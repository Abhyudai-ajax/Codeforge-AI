# CodeForge AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://github.com/your-org/codeforge-ai/workflows/CI%2FCD/badge.svg)](https://github.com/your-org/codeforge-ai/actions)

AI-powered collaborative coding platform combining the best features of LeetCode, GitHub Copilot, Replit, and CodeSandbox.

**[Documentation](#-documentation)** • **[Quick Start](#-quick-start)** • **[Architecture](#-architecture)** • **[Contributing](#-contributing)**

---

## 🎯 Overview

CodeForge AI is a production-grade SaaS platform designed to revolutionize how developers learn, practice, and collaborate on coding challenges. It integrates:

- **Problem Solving**: LeetCode-style coding challenges with multiple difficulty levels
- **AI Assistance**: GitHub Copilot-like code completion and smart suggestions
- **Real-time Collaboration**: Replit-style multiplayer coding sessions
- **Instant Execution**: CodeSandbox-like environment for immediate code testing

### Key Features

- 📚 **50 curated DSA problems** across 19 topics and all three difficulty levels
- 💻 **Five languages** — Python, **C**, **C++**, JavaScript and Java — with
  per-problem starter code for each
- 🚀 Sandboxed multi-language execution with per-problem time and memory limits
- 🤖 AI hints, explanations and code review, grounded in the problem statement
- 🏆 Contests, leaderboards, roadmaps and per-user progress tracking
- 👥 Real-time collaborative rooms over WebSockets
- 🔐 JWT authentication, profiles and role-based admin
- 🔗 GitHub integration with AI-assisted PR review

> The backend is feature-complete and tested. Frontend integration is in progress.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript 5.3
- **Styling**: Tailwind CSS 3.3
- **UI Ready**: shadcn/ui compatible components
- **State**: Zustand 4.4
- **Data Fetching**: TanStack Query 5.28
- **HTTP**: Axios 1.6
- **Real-time**: Socket.io Client 4.7
- **Code Quality**: ESLint, Prettier, Husky

### Backend
- **Framework**: FastAPI 0.104
- **Language**: Python 3.12
- **ORM**: SQLAlchemy 2.0 with async
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Migrations**: Alembic 1.12
- **Background Jobs**: Celery 5.3
- **Server**: Uvicorn 0.24
- **Validation**: Pydantic v2
- **Code Execution**: Isolated sandbox runners for Python, C, C++, JavaScript, Java (optional, off by default)
- **AI**: Pluggable providers (OpenAI, Ollama) with graceful fallbacks
- **Code Quality**: Black, isort, Flake8, mypy

### DevOps
- **CI/CD**: GitHub Actions
- **Monitoring**: Logging & Health checks ready

---

## 📁 Project Structure

```
codeforge-ai/
├── 📱 frontend/                    # Next.js application
│   ├── app/                        # App Router pages
│   ├── components/                 # React components (ui, layout, common, editor)
│   ├── hooks/                      # Custom React hooks
│   ├── lib/                        # Utilities & libraries
│   ├── services/                   # API service layer
│   ├── store/                      # Zustand state management
│   ├── providers/                  # React providers
│   ├── types/                      # TypeScript definitions
│   └── package.json
│
├── 🔙 backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py                 # Application entry point
│   │   ├── api/v1/                 # API routes
│   │   ├── core/                   # Configuration & setup
│   │   ├── db/                     # Database layer
│   │   ├── models/                 # Database models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # Business logic
│   │   ├── middleware/             # Custom middleware
│   │   ├── websocket/              # WebSocket handlers
│   │   ├── ai/                     # AI services
│   │   ├── workers/                # Celery tasks
│   │   └── utils/                  # Utilities
│   ├── alembic/                    # Database migrations
│   ├── tests/                      # Test suite
│   ├── scripts/                    # Utility scripts
│   ├── requirements.txt
│   └── pyproject.toml
│
├── 📚 docs/                        # Documentation
│   ├── architecture/               # Architecture docs
│   ├── api/                        # API reference
│   └── database/                   # Database schema
│
├── 📋 scripts/                     # Helper scripts
│   ├── init_db.py
│   ├── dev-start.sh
│   └── dev-start.bat
│
├── 🚀 .github/workflows/           # CI/CD workflows
├── ⚙️ .vscode/                     # VSCode configuration
├── 📖 Makefile                     # Development commands
├── 📄 README.md                    # This file
├── 📖 GETTING_STARTED.md           # Setup guide
├── 🤝 CONTRIBUTING.md              # Contribution guide
├── 🚀 DEPLOYMENT.md                # Deployment guide
├── .env.example
├── .gitignore
└── LICENSE
```

---

## 🚀 Quick Start

### 1. **Clone Repository**
```bash
git clone https://github.com/your-org/codeforge-ai.git
cd codeforge-ai
```

### 2. **Setup Environment**
```bash
cp .env.example .env
```

By default this runs against a local **SQLite** file — no PostgreSQL or Redis
install required. For production parity, edit `.env` and point `DATABASE_URL`
at a real PostgreSQL instance and `REDIS_URL` at a real Redis instance instead
(see [GETTING_STARTED.md](GETTING_STARTED.md)).

### 3. **Backend**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .[dev]

# Create the schema. Using SQLite (the default): the Alembic migration chain
# has some PostgreSQL-only DDL, so create tables straight from the ORM models
# instead:
python -c "import asyncio; from app.core.database import init_db; asyncio.run(init_db())"
# Using a real PostgreSQL database instead, run migrations normally:
#   alembic -c alembic/alembic.ini upgrade head

# Seed the 50-problem catalog + a demo user (demo@codeforge.ai / password123):
python -m app.db.seed_data

uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000  (docs at /api/docs)
```

`--reload` can hit a Windows-specific bug in uvicorn's file-watcher IPC socket
(`WinError 10013`); if you see that, drop `--reload` and restart manually
after backend changes.

**Code execution**: submissions run through a Docker-isolated sandbox when
Docker is available. Without Docker, `app/workers/sandbox.py` falls back to
running submitted code directly on your machine using your local `python`,
`node`, `gcc`, `g++` and `javac`/`java` — convenient for local dev, but
**not sandboxed** (no network/filesystem/memory isolation). Never expose that
fallback to untrusted, multi-user submissions. Submission judging also runs
synchronously in-process when `CELERY_TASK_ALWAYS_EAGER=true` (the `.env`
default), so no Redis broker or separate Celery worker is needed locally —
turn it off once you have a real broker running.

### 4. **Frontend**
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 5. **Verify Installation**
```bash
# Check frontend
curl http://localhost:3000

# Check backend
curl http://localhost:8000/api/health

# API docs
open http://localhost:8000/api/docs
```

---

## 💻 Development Workflow

### Using Makefile (Recommended)
```bash
make install        # Install all dependencies
make dev           # Start all services
make lint          # Run linters
make format        # Format code
make type-check    # Type checking
make test          # Run tests
make clean         # Clean caches
```

### Frontend Development
```bash
cd frontend
npm run dev         # Start dev server
npm run build       # Production build
npm run lint        # ESLint
npm run format      # Prettier
npm run type-check  # TypeScript
npm test            # Jest tests
```

### Backend Development
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload              # Dev server
pytest                                      # Tests
black app && isort app                      # Format
flake8 app && mypy app                      # Lint & type-check
python -m scripts.init_db                   # Initialize database
```

### Code Quality

All code must pass:
- ✅ Linting (ESLint, Flake8)
- ✅ Formatting (Prettier, Black)
- ✅ Type checking (TypeScript, mypy)
- ✅ Tests (minimum 80% coverage)

Git hooks (Husky) automatically enforce these on commit.

---

## 🗂️ Architecture

### Clean Architecture Layers

```
API Layer (FastAPI routers)
    ↓
Services Layer (Business logic)
    ↓
Data Access Layer (CRUD repositories / Cache)
    ↓
PostgreSQL / Redis / sandbox runner
```

Routers only wire dependencies to services; business rules live in
`app/services/` and all database access goes through `app/crud/`.

### Data Flow

```
Frontend (Next.js)
    ↓
State Management (Zustand)
    ↓
API Services (Axios)
    ↓
Backend API (FastAPI)
    ↓
Services & Database (SQLAlchemy)
    ↓
PostgreSQL / Redis
```

For detailed architecture, see [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)

---

## 📚 Documentation

- **[Getting Started](GETTING_STARTED.md)** - Complete setup guide
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System design and patterns
- **[API Reference](docs/api/API_REFERENCE.md)** - API endpoints (when implemented)
- **[Database](docs/database/DATABASE.md)** - Database schema and migration guide
- **[Contributing](CONTRIBUTING.md)** - Contribution guidelines
- **[Deployment](DEPLOYMENT.md)** - Production deployment guide

---

## ⚙️ Services

- **frontend**: Next.js dev server (port 3000)
- **backend**: FastAPI (port 8000) — run Alembic migrations and the seeder manually (see Quick Start)
- **postgres**: PostgreSQL (port 5432) — install and run locally
- **redis**: Redis (port 6379) — install and run locally
- **celery**: Optional execution/judge worker (`python -m celery -A app.workers:app worker --loglevel=info` from `backend/`)

### Code execution

Submissions are graded by the Celery worker inside an isolated sandbox runner
(`CODE_EXECUTION_ENABLED`, off by default). Without a runner configured and the
worker running, the API still serves problems, but submissions stay `queued`.
See [EXECUTION_ENGINE.md](docs/backend/EXECUTION_ENGINE.md) for the sandbox's
isolation model.

---

## 🔍 API Documentation

When backend is running:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

(Only available in development mode)

---

## 🧪 Testing

```bash
# Frontend tests
cd frontend && npm test

# Backend tests
cd backend && source venv/bin/activate && pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test
pytest tests/test_api.py::test_health_check
```

---

## 📦 Dependencies

### Frontend
- See [frontend/package.json](frontend/package.json)

### Backend
- See [backend/requirements.txt](backend/requirements.txt)

---

## 🔒 Security

- Environment variables for all secrets
- Input validation (Pydantic)
- CORS properly configured
- SQL injection protection (SQLAlchemy)
- HTTPS ready
- Rate limiting ready
- JWT authentication ready (placeholder)

---

## 🚀 Roadmap

### Phase 1 (MVP)
- [x] User authentication & authorization
- [x] Problem management system (50-problem catalog)
- [x] Real-time collaboration (WebSockets)
- [x] Multi-language code execution (Python, C, C++, JavaScript, Java)
- [ ] Editor UI wiring (backend metadata ready via `/api/v1/languages`)

### Phase 2
- [x] AI code assistance (hint, explain, review, debug, tests, docs)
- [x] Leaderboards & contests
- [x] Problem categories & difficulty filters
- [x] Roadmaps & progress tracking
- [ ] User portfolios

### Phase 3
- [x] GitHub integration with AI PR review
- [x] Custom problem creation (admin API)
- [ ] Advanced ML features
- [ ] Enterprise features

---

## 🤝 Contributing

We welcome contributions! Please:

1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Fork the repository
3. Create a feature branch
4. Follow code quality standards
5. Submit a pull request

### Development Setup
```bash
# Clone your fork
git clone https://github.com/your-username/codeforge-ai.git

# Create feature branch
git checkout -b feature/your-feature

# Follow CONTRIBUTING.md guidelines
```

---

## 📋 Pre-Development Checklist

Before starting development:

- [ ] ✅ Read [GETTING_STARTED.md](GETTING_STARTED.md)
- [ ] ✅ Read [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
- [ ] ✅ Set up local development environment
- [ ] ✅ Run all tests successfully
- [ ] ✅ Code quality checks passing
- [ ] ✅ Database migrations working
- [ ] ✅ API documentation accessible

---

## 📝 Common Issues & Solutions

### Port Already in Use
```bash
# Change port in .env
NEXT_PUBLIC_API_URL=http://localhost:8001
# Or kill process using port
lsof -ti:8000 | xargs kill -9
```

### Database Connection Error
```bash
# Make sure your local PostgreSQL service is running
# Then check the connection string in .env
```

### Module Not Found (Python)
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

For more troubleshooting, see [GETTING_STARTED.md#common-issues](GETTING_STARTED.md#common-issues)

---

## 📞 Support

- 📖 Check [documentation](docs/)
- 🐛 [Open an issue](https://github.com/your-org/codeforge-ai/issues)
- 💬 [Start a discussion](https://github.com/your-org/codeforge-ai/discussions)
- 📧 Email: team@codeforge.ai

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 👥 Authors & Contributors

**CodeForge AI Team** - *Initial scaffold and architecture*

See [CONTRIBUTING.md](CONTRIBUTING.md) for a list of contributors.

---

## 🙏 Acknowledgments

Built with:
- ❤️ Next.js & FastAPI communities
- 🚀 Modern web development best practices
- 📚 Clean architecture principles
- 🔄 CI/CD and DevOps automation

---

**Built by developers, for developers.** ✨

*Last updated: 2026-09-06*
