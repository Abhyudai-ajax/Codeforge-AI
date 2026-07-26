# API Documentation

## Overview

CodeForge AI API is built with FastAPI and provides RESTful endpoints for the frontend application.

## API Versions

### V1 (`/api/v1`)

The current API version. All endpoints are versioned to support future API evolution.

## Authentication (Future)

```
Authorization: Bearer <token>
```

## Response Format

### Success Response

```json
{
  "status": 200,
  "data": { /* response data */ },
  "message": "Success"
}
```

### Error Response

```json
{
  "status": 400,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request",
    "details": { /* error details */ }
  }
}
```

## Common Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created
- `204 No Content` - Successful, no content
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

Rate limiting will be implemented on all endpoints:
- 1000 requests per hour per API key
- 100 requests per minute per endpoint

## Pagination

Endpoints that return lists support pagination:

```
GET /api/v1/resources?page=1&limit=20
```

Response includes:
- `items`: Array of results
- `total`: Total number of items
- `page`: Current page
- `limit`: Items per page
- `pages`: Total number of pages

## Available Endpoints

### Health Check

```
GET /api/health
```

Returns application health status.

### Root

```
GET /
```

Returns API information and version.

## Documentation

- **Swagger UI**: Available at `/api/docs`
- **ReDoc**: Available at `/api/redoc`
- **OpenAPI JSON**: Available at `/api/openapi.json`

(Only in development mode)

## Future Endpoints

Planned endpoints for implementation:

### Users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user
- `GET /api/v1/users/me` - Get current user

### Problems
- `GET /api/v1/problems` - List problems
- `POST /api/v1/problems` - Create problem (admin)
- `GET /api/v1/problems/{id}` - Get problem
- `PUT /api/v1/problems/{id}` - Update problem (admin)

### Submissions
- `POST /api/v1/submissions` - Submit solution
- `GET /api/v1/submissions/{id}` - Get submission
- `GET /api/v1/submissions` - List user submissions

### WebSocket
- `WS /ws/sessions/{session_id}` - Join collaborative session

## Error Handling

All errors follow a consistent format with error codes for client-side handling.

Error codes include:
- `VALIDATION_ERROR`
- `AUTHENTICATION_ERROR`
- `AUTHORIZATION_ERROR`
- `NOT_FOUND_ERROR`
- `CONFLICT_ERROR`
- `INTERNAL_ERROR`

## Best Practices

1. Always include proper error handling
2. Use appropriate HTTP methods
3. Include pagination for list endpoints
4. Validate all input data
5. Return meaningful error messages
6. Use consistent response format

## Version History

### V1.0.0 (2024-Q1)
- Initial API scaffold
- Basic endpoints structure
- Documentation endpoints
