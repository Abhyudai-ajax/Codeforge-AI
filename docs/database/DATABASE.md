# Database Schema Guide

## Database Design

CodeForge AI uses PostgreSQL as the primary database with SQLAlchemy ORM for database abstraction.

## Tables (Future Implementation)

The following tables will be implemented when features are developed:

### Users
- Stores user account information
- Fields: id, email, password_hash, name, avatar_url, created_at, updated_at
- Relationships: Problems, Submissions, Sessions

### Problems
- Coding challenge problems
- Fields: id, title, description, difficulty, examples, constraints, created_at, updated_at
- Relationships: Tags, Submissions, TestCases

### Submissions
- User code submissions
- Fields: id, user_id, problem_id, code, language, status, runtime, memory, created_at
- Relationships: User, Problem, TestResults

### Sessions
- Collaborative coding sessions
- Fields: id, user_id, problem_id, code_snapshot, active_participants, created_at, updated_at
- Relationships: User, Problem

### Alembic Migrations

Database migrations are managed through Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1
```

## Connection Management

### Development
- Single PostgreSQL instance
- 20 connections in pool
- Echo SQL queries for debugging

### Production
- Connection pooling with pgBouncer
- 50+ connections in pool
- Read replicas for scaling

## Performance Considerations

### Indexing
- Primary keys indexed automatically
- Foreign key indexes
- Query optimization indexes (TBD)

### Optimization
- Connection pooling
- Query result caching with Redis
- Lazy loading of relationships
- Bulk operations where possible

## Backup & Recovery

- Daily automated backups
- Point-in-time recovery capability
- Replication setup for HA

## Migration Workflow

1. Create migration: `make db-migrate`
2. Review generated migration
3. Apply migration: `make db-upgrade`
4. Test thoroughly
5. Commit to version control

For detailed migration instructions, see the backend README.
