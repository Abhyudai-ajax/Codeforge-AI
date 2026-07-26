# Architecture Guide

## Overview

CodeForge AI follows a modern, scalable architecture combining:
- **Clean Architecture**: Clear separation of concerns
- **Async-First**: Non-blocking operations throughout
- **Microservices Ready**: Designed for future horizontal scaling

## Frontend Architecture

### Layer Structure

```
Frontend (Next.js)
├── UI Layer (Pages & Components)
├── Hooks Layer (React Hooks)
├── Services Layer (API calls)
├── State Layer (Zustand stores)
└── Utilities Layer (Helpers)
```

### Key Technologies

- **Next.js 15**: React framework with SSR/SSG
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Zustand**: Lightweight state management
- **TanStack Query**: Server state management
- **Axios**: HTTP client with interceptors

### Component Organization

```
components/
├── ui/          # Reusable UI components
├── layout/      # Layout components
├── common/      # Common/shared components
└── editor/      # Code editor specific components
```

## Backend Architecture

### Layer Structure

```
Backend (FastAPI)
├── API Layer (Routes/Endpoints)
├── Services Layer (Business Logic)
├── Database Layer (ORM/Models)
├── Core Layer (Configuration)
└── Utils Layer (Helpers)
```

### Key Technologies

- **FastAPI**: Modern async Python framework
- **SQLAlchemy 2.0**: ORM with async support
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker
- **Celery**: Background job processing
- **Pydantic v2**: Data validation

### Directory Structure

```
app/
├── api/         # Route handlers
├── core/        # Configuration
├── db/          # Database layer
├── models/      # SQLAlchemy models
├── schemas/     # Pydantic schemas
├── services/    # Business logic
├── middleware/  # Custom middleware
├── websocket/   # WebSocket handlers
├── ai/          # AI services
├── workers/     # Celery tasks
└── utils/       # Utility functions
```

## Data Flow

### Request/Response Flow

```
Frontend
  ↓
Next.js Page/Component
  ↓
useQuery/useMutation (TanStack Query)
  ↓
Zustand Store (optional)
  ↓
Axios Client
  ↓ (HTTP)
Backend API
  ↓
FastAPI Route Handler
  ↓
Service Layer (Business Logic)
  ↓
Database Layer (SQLAlchemy)
  ↓
PostgreSQL/Redis
```

### Real-time Data Flow

```
WebSocket Client → Socket.io Client
  ↓
Socket.io Server
  ↓
WebSocket Handler
  ↓
Service Layer
  ↓
Cache/Database
  ↓
Broadcast Back to Clients
```

### Background Task Flow

```
API Endpoint
  ↓
Create Celery Task
  ↓
Redis (Message Broker)
  ↓
Celery Worker
  ↓
Service Logic
  ↓
Database/External Services
```

## Deployment Architecture

### Development

```
Frontend (npm run dev)
Backend (uvicorn --reload)
PostgreSQL (Docker)
Redis (Docker)
```

### Production

```
CDN → Frontend (Next.js optimized)
Load Balancer
  ↓
Backend Cluster (Multiple Uvicorn workers)
  ↓
Connection Pool → PostgreSQL
  ↓
Redis Cluster
  ↓
Celery Workers
```

### Docker Compose Setup

```
Frontend Container → Backend Container
                  ↓
              PostgreSQL Container
              Redis Container
              Celery Container (optional)
```

## Error Handling

### Frontend

```typescript
// Global error handler
axios.interceptors.response.use(
  response => response,
  error => {
    // Handle 401 → Redirect to login
    // Handle 500 → Show error notification
    // Retry logic
  }
)
```

### Backend

```python
# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )
```

## Security Considerations

### Frontend
- HTTPS only in production
- Secure cookie flags
- CSRF protection
- XSS prevention

### Backend
- Input validation (Pydantic)
- Rate limiting
- CORS configuration
- JWT token management
- Parameterized queries (SQLAlchemy)

## Scalability

### Horizontal Scaling

1. **Frontend**: Deploy multiple instances behind CDN
2. **Backend**: Multiple Uvicorn workers, load balancer
3. **Database**: Connection pooling, read replicas
4. **Cache**: Redis cluster
5. **Jobs**: Multiple Celery workers

### Performance Optimization

- Database query optimization
- Caching strategies (Redis)
- API response compression (GZIP)
- Connection pooling
- Async/await for I/O operations

## Monitoring & Observability

### Logging

- Structured JSON logging
- Different levels (DEBUG, INFO, WARNING, ERROR)
- Centralized log aggregation ready

### Metrics

- Application metrics (requests, response time)
- Database metrics (query performance)
- Cache hit rates
- Worker metrics (Celery tasks)

## Future Enhancements

- WebSocket scaling (Redis pub/sub)
- Service mesh (Istio)
- API Gateway
- Message queue optimization
- Distributed tracing (OpenTelemetry)
