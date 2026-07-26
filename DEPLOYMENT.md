# Deployment Guide

## Deployment Strategies

CodeForge AI can be deployed to various platforms using Docker.

## Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Code reviewed and merged to main
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] SSL certificates ready
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Load balancer configured (if needed)

## Environment Setup

### Production Environment Variables

```env
ENV=production
DEBUG=false

# Frontend
NEXT_PUBLIC_API_URL=https://api.codeforge.ai
NEXT_PUBLIC_WS_URL=wss://api.codeforge.ai

# Backend
DATABASE_URL=postgresql://user:strong_password@db.host:5432/codeforge_ai
REDIS_URL=redis://cache.host:6379
SECRET_KEY=generate-secure-key-with-openssl-rand-hex-32
```

## Docker Deployment

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build frontend
docker-compose build backend
```

### Running Containers

```bash
# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With Celery workers
docker-compose --profile workers up -d
```

## Cloud Deployment

### AWS ECS/EKS

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com

docker tag codeforge-ai:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/codeforge-ai:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/codeforge-ai:latest
```

### Kubernetes

```bash
# Deploy using Helm (example)
helm install codeforge-ai ./helm-chart \
  --values helm-values.prod.yaml \
  --namespace codeforge-ai
```

## Database Migrations

Before deploying, run migrations:

```bash
# In container
docker exec codeforge-backend alembic upgrade head

# Or manually
cd backend
alembic upgrade head
```

## Monitoring

### Application Monitoring

- Set up log aggregation (ELK, CloudWatch)
- Monitor error rates and performance
- Set up alerting for critical issues

### Database Monitoring

- Query performance monitoring
- Connection pool monitoring
- Backup verification

## SSL/TLS

### Self-Signed (Development)

```bash
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

### Let's Encrypt (Production)

```bash
# Using Certbot
certbot certonly --standalone -d codeforge.ai -d api.codeforge.ai
```

## Performance Optimization

### Backend

- Enable gzip compression (enabled by default)
- Use connection pooling
- Cache frequently accessed data
- Optimize database queries

### Frontend

- Build for production: `npm run build`
- Enable CDN caching
- Minimize bundle size
- Use image optimization

## Scaling

### Horizontal Scaling

```bash
# Scale backend services
docker-compose up -d --scale backend=3
```

### Load Balancing

Use Nginx, HAProxy, or cloud load balancer:

```nginx
upstream backend {
    server backend:8000;
    server backend:8001;
    server backend:8002;
}

server {
    listen 443 ssl;
    server_name api.codeforge.ai;
    
    location / {
        proxy_pass http://backend;
    }
}
```

## Backup Strategy

### Database Backups

```bash
# Manual backup
docker exec codeforge-postgres pg_dump -U codeforge codeforge_ai > backup.sql

# Automated (cron job)
0 2 * * * docker exec codeforge-postgres pg_dump -U codeforge codeforge_ai | gzip > /backups/backup-$(date +\%Y\%m\%d-\%H\%M\%S).sql.gz
```

### Restore from Backup

```bash
# Restore database
psql -U codeforge codeforge_ai < backup.sql
```

## Rollback Procedure

### If deployment fails:

```bash
# Revert to previous image version
docker pull codeforge-ai:v1.0.0
docker-compose down
docker-compose up -d
```

### If database migration fails:

```bash
# Rollback migration
alembic downgrade -1

# Or to specific revision
alembic downgrade abc123def
```

## Health Checks

### Endpoint Monitoring

```bash
# Frontend health
curl http://localhost:3000

# Backend health
curl http://localhost:8000/api/health

# Database health
curl http://localhost:8000/api/health/db
```

## Post-Deployment

- [ ] Verify all services are running
- [ ] Test critical user flows
- [ ] Monitor error rates and performance
- [ ] Check database integrity
- [ ] Verify backups are working
- [ ] Test rollback procedure

## Emergency Procedures

### Application Down

1. Check service status: `docker-compose ps`
2. Check logs: `docker-compose logs backend`
3. Restart service: `docker-compose restart backend`
4. If still failing, rollback to previous version

### Database Issues

1. Check connection: `psql postgresql://...`
2. Check disk space: `df -h`
3. Restore from backup if corrupted
4. Run consistency check: `VACUUM ANALYZE`

### High Load

1. Check resource usage: `docker stats`
2. Scale services if needed
3. Check database query performance
4. Implement caching if needed

## Support & Monitoring

- Set up error tracking (Sentry)
- Configure performance monitoring (New Relic, DataDog)
- Set up log aggregation
- Configure alerting for critical metrics
