# Contributing to CodeForge AI

Thank you for considering contributing to CodeForge AI! This document provides guidelines and instructions.

## Code of Conduct

- Be respectful and inclusive
- Welcome all experience levels
- Give and receive constructive feedback
- Focus on the code, not the person

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/codeforge-ai.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Follow the development setup in [GETTING_STARTED.md](GETTING_STARTED.md)

## Development Workflow

### 1. Code Quality

Before committing, ensure code quality:

```bash
# Frontend
cd frontend
npm run lint
npm run format
npm run type-check

# Backend
cd backend
source venv/bin/activate
black app
isort app
flake8 app
mypy app
```

### 2. Testing

Write and run tests:

```bash
# Frontend
cd frontend
npm test

# Backend
cd backend
source venv/bin/activate
pytest
pytest --cov=app  # with coverage
```

### 3. Commit Messages

Follow conventional commits:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(auth): add JWT token validation
fix(api): handle null response from database
docs: update setup instructions
```

### 4. Pull Requests

1. Push your feature branch
2. Create a Pull Request with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots for UI changes
3. Respond to review feedback
4. Ensure CI/CD passes

## Git Hooks

Husky and lint-staged are configured to automatically:
- Lint staged files
- Format code
- Type check

These run before each commit. If they fail, fix the issues and try again.

## Project Structure

Follow the established architecture:

### Frontend

```
components/
├── ui/          # Generic UI components
├── layout/      # Layout components
├── common/      # Shared components
└── editor/      # Feature-specific components

hooks/           # Custom React hooks
services/        # API service layer
store/           # Zustand stores
types/           # TypeScript types
utils/           # Utility functions
```

### Backend

```
app/
├── api/         # Route handlers
├── core/        # Configuration
├── services/    # Business logic
├── models/      # Database models
├── schemas/     # Pydantic schemas
└── utils/       # Utilities
```

## Branch Naming

```
feature/description         # New feature
fix/description            # Bug fix
docs/description           # Documentation
refactor/description       # Code refactoring
```

## Commit Frequency

- Commit frequently (don't accumulate changes)
- Each commit should be a logical unit
- Keep commits small and focused

## Documentation

- Document complex logic
- Add docstrings to functions
- Update README for new features
- Add comments for "why", not "what"

## Performance

- Write efficient code
- Consider database performance
- Minimize API requests
- Use proper caching strategies

## Security

- Never commit secrets to version control
- Use environment variables for sensitive data
- Follow OWASP guidelines
- Validate all user input
- Use parameterized queries

## Testing Requirements

### Frontend
- Component tests
- Integration tests
- E2E tests for critical paths

### Backend
- Unit tests for services
- Integration tests for API endpoints
- Database tests with transactions

## Submitting Changes

1. Fork and create feature branch
2. Make changes following guidelines
3. Ensure tests pass: `make test`
4. Ensure code quality: `make lint`
5. Create descriptive commit messages
6. Push to your fork
7. Submit Pull Request

## Areas to Contribute

### Priority Areas
- [ ] Frontend components
- [ ] API endpoints
- [ ] Database models
- [ ] Tests and documentation
- [ ] Bug fixes

### Good First Issues
- Look for `good-first-issue` label
- Start with smaller contributions
- Ask for help if needed

## Code Review Process

### For Authors
- Respond to feedback promptly
- Ask questions if feedback is unclear
- Don't take feedback personally

### For Reviewers
- Be constructive and respectful
- Ask questions instead of demanding
- Acknowledge good work
- Suggest improvements, not demands

## Questions?

- Open a GitHub discussion
- Check existing issues
- Create a new issue with [QUESTION] prefix

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Additional Resources

- [Architecture Guide](docs/architecture/ARCHITECTURE.md)
- [API Documentation](docs/api/API_REFERENCE.md)
- [Database Guide](docs/database/DATABASE.md)

Thank you for contributing to CodeForge AI! 🎉
