# FireFeed Telegram Bot - Deployment Guide

This document provides comprehensive deployment instructions for the FireFeed Telegram Bot in various environments.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Configuration](#configuration)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Scaling](#scaling)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## 🛠️ Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.11 or higher
- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher (for Docker Compose deployment)
- **Kubernetes**: 1.20 or higher (for Kubernetes deployment)

### External Dependencies

- **PostgreSQL**: 12 or higher (for user data)
- **Redis**: 6.0 or higher (for caching)
- **FireFeed API**: Running and accessible
- **Telegram Bot Token**: Valid Telegram bot token

### Network Requirements

- **Outbound Internet Access**: Required for Telegram API and external services
- **Firewall Rules**: Allow traffic on configured ports
- **DNS Resolution**: Proper DNS configuration for external API calls

## ⚙️ Environment Setup

### Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/firefeed/firefeed-telegram-bot.git
   cd firefeed-telegram-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -e .
   ```

3. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

4. **Configure environment variables** (see [Configuration](#configuration) section)

5. **Start dependencies**:
   ```bash
   docker-compose up -d postgres redis
   ```

6. **Run database migrations** (if applicable):
   ```bash
   # Database initialization would be handled by the application
   ```

7. **Start the application**:
   ```bash
   python -m firefeed_telegram_bot
   ```

### Production Environment

1. **Deploy dependencies**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

2. **Verify deployment**:
   ```bash
   docker-compose ps
   ```

3. **Check logs**:
   ```bash
   docker-compose logs -f firefeed-telegram-bot
   ```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure the following variables:

#### Essential Configuration

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_USE_WEBHOOK=false  # true for webhook, false for polling
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
TELEGRAM_WEBHOOK_PORT=8443
TELEGRAM_WEBHOOK_HOST=0.0.0.0

# FireFeed API Configuration
FIREFEED_API_BASE_URL=http://host.docker.internal:8001
FIREFEED_API_KEY=your_firefeed_api_key_here

# Database Configuration
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=firefeed_telegram_bot
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_database_password

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# Security Configuration
SECRET_KEY=your_secret_key_here
```

#### Optional Configuration

```bash
# Translation Configuration
TRANSLATION_ENABLED=true
TRANSLATION_DEFAULT_LANGUAGE=en
TRANSLATION_SUPPORTED_LANGUAGES=en,ru,de

# Cache Configuration
CACHE_ENABLED=true
CACHE_DEFAULT_TTL=300
CACHE_MAX_SIZE=1000

# Monitoring Configuration
MONITORING_ENABLED=true
METRICS_PORT=8080
HEALTH_CHECK_PORT=8081
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Configuration Files

#### Docker Compose Configuration

The `docker-compose.yml` file provides a complete development and production environment:

```yaml
version: '3.8'

services:
  firefeed-telegram-bot:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - FIREFEED_API_BASE_URL=${FIREFEED_API_BASE_URL}
      # ... other environment variables
    ports:
      - "8080:8080"  # Metrics
      - "8081:8081"  # Health checks
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
```

#### Production Overrides

Create `docker-compose.prod.yml` for production-specific configuration:

```yaml
version: '3.8'

services:
  firefeed-telegram-bot:
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - TELEGRAM_USE_WEBHOOK=true
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## 🐳 Docker Deployment

### Building the Image

```bash
# Build the image
docker build -t firefeed/telegram-bot:latest .

# Build with specific tag
docker build -t firefeed/telegram-bot:v1.0.0 .

# Build for different architectures
docker buildx build --platform linux/amd64,linux/arm64 -t firefeed/telegram-bot:latest .
```

### Running with Docker Compose

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d firefeed-telegram-bot

# View logs
docker-compose logs -f firefeed-telegram-bot

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Running with Docker Run

```bash
# Run the container
docker run -d \
  --name firefeed-telegram-bot \
  --env-file .env \
  -p 8080:8080 \
  -p 8081:8081 \
  --restart unless-stopped \
  firefeed/telegram-bot:latest

# Run with volume mounts
docker run -d \
  --name firefeed-telegram-bot \
  --env-file .env \
  -v ./logs:/app/logs \
  -v ./config:/app/config:ro \
  -p 8080:8080 \
  -p 8081:8081 \
  --restart unless-stopped \
  firefeed/telegram-bot:latest
```

### Multi-Stage Build Optimization

The Dockerfile uses multi-stage builds for optimization:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . .
USER appuser
ENTRYPOINT ["python", "-m", "firefeed_telegram_bot"]
```

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Container registry access

### Deployment Manifests

#### 1. Namespace and RBAC

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: firefeed-telegram-bot
---
# k8s/rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: firefeed-telegram-bot
  namespace: firefeed-telegram-bot
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: firefeed-telegram-bot
  name: firefeed-telegram-bot
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: firefeed-telegram-bot
  namespace: firefeed-telegram-bot
subjects:
- kind: ServiceAccount
  name: firefeed-telegram-bot
  namespace: firefeed-telegram-bot
roleRef:
  kind: Role
  name: firefeed-telegram-bot
  apiGroup: rbac.authorization.k8s.io
```

#### 2. ConfigMaps and Secrets

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: firefeed-telegram-bot-config
  namespace: firefeed-telegram-bot
data:
  environment: "production"
  debug: "false"
  log_level: "INFO"
  translation_enabled: "true"
  cache_enabled: "true"
---
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: firefeed-telegram-bot-secrets
  namespace: firefeed-telegram-bot
type: Opaque
stringData:
  telegram_bot_token: "your_telegram_bot_token"
  firefeed_api_key: "your_firefeed_api_key"
  database_password: "your_database_password"
  redis_password: "your_redis_password"
  secret_key: "your_secret_key"
```

#### 3. Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: firefeed-telegram-bot
  namespace: firefeed-telegram-bot
  labels:
    app: firefeed-telegram-bot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: firefeed-telegram-bot
  template:
    metadata:
      labels:
        app: firefeed-telegram-bot
    spec:
      serviceAccountName: firefeed-telegram-bot
      containers:
      - name: firefeed-telegram-bot
        image: firefeed/telegram-bot:latest
        ports:
        - containerPort: 8080
          name: metrics
        - containerPort: 8081
          name: health
        env:
        - name: ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: firefeed-telegram-bot-config
              key: environment
        - name: DEBUG
          valueFrom:
            configMapKeyRef:
              name: firefeed-telegram-bot-config
              key: debug
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: firefeed-telegram-bot-config
              key: log_level
        - name: TELEGRAM_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: firefeed-telegram-bot-secrets
              key: telegram_bot_token
        - name: FIREFEED_API_KEY
          valueFrom:
            secretKeyRef:
              name: firefeed-telegram-bot-secrets
              key: firefeed_api_key
        envFrom:
        - configMapRef:
            name: firefeed-telegram-bot-config
        - secretRef:
            name: firefeed-telegram-bot-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}
```

#### 4. Services

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: firefeed-telegram-bot
  namespace: firefeed-telegram-bot
  labels:
    app: firefeed-telegram-bot
spec:
  selector:
    app: firefeed-telegram-bot
  ports:
  - name: metrics
    port: 8080
    targetPort: 8080
  - name: health
    port: 8081
    targetPort: 8081
  type: ClusterIP
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: firefeed-telegram-bot
  namespace: firefeed-telegram-bot
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: firefeed-telegram-bot-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /health
        pathType: Prefix
        backend:
          service:
            name: firefeed-telegram-bot
            port:
              number: 8081
      - path: /metrics
        pathType: Prefix
        backend:
          service:
            name: firefeed-telegram-bot
            port:
              number: 8080
```

### Kubernetes Deployment Commands

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n firefeed-telegram-bot

# View logs
kubectl logs -f deployment/firefeed-telegram-bot -n firefeed-telegram-bot

# Scale deployment
kubectl scale deployment firefeed-telegram-bot --replicas=5 -n firefeed-telegram-bot

# Update deployment
kubectl rollout restart deployment/firefeed-telegram-bot -n firefeed-telegram-bot

# Check rollout status
kubectl rollout status deployment/firefeed-telegram-bot -n firefeed-telegram-bot
```

## 📈 Scaling

### Horizontal Scaling

#### Docker Compose

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  firefeed-telegram-bot:
    deploy:
      replicas: 3
```

```bash
# Scale services
docker-compose up -d --scale firefeed-telegram-bot=3
```

#### Kubernetes

```bash
# Manual scaling
kubectl scale deployment firefeed-telegram-bot --replicas=5 -n firefeed-telegram-bot

# Horizontal Pod Autoscaler
kubectl apply -f k8s/hpa.yaml
```

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: firefeed-telegram-bot-hpa
  namespace: firefeed-telegram-bot
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: firefeed-telegram-bot
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Vertical Scaling

#### Resource Limits

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

#### Database Scaling

- **Connection Pooling**: Adjust connection pool sizes
- **Read Replicas**: Use read replicas for read-heavy workloads
- **Sharding**: Consider sharding for very large datasets

#### Cache Scaling

- **Redis Clustering**: Use Redis Cluster for high availability
- **Memory Allocation**: Increase Redis memory limits
- **Persistence**: Configure appropriate persistence settings

## 📊 Monitoring

### Health Checks

The application provides health check endpoints:

```bash
# Application health
curl http://localhost:8081/health

# Metrics endpoint
curl http://localhost:8080/metrics
```

### Prometheus Integration

```yaml
# k8s/prometheus-service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: firefeed-telegram-bot
  namespace: firefeed-telegram-bot
spec:
  selector:
    matchLabels:
      app: firefeed-telegram-bot
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
```

### Grafana Dashboards

Import the provided Grafana dashboard configuration:

```json
{
  "dashboard": {
    "title": "FireFeed Telegram Bot",
    "panels": [
      {
        "title": "Bot Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"firefeed-telegram-bot\"}"
          }
        ]
      }
    ]
  }
}
```

### Alerting

Configure Prometheus alerting rules:

```yaml
# k8s/alerts.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: firefeed-telegram-bot-alerts
  namespace: firefeed-telegram-bot
spec:
  groups:
  - name: firefeed-telegram-bot
    rules:
    - alert: BotDown
      expr: up{job="firefeed-telegram-bot"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "FireFeed Telegram Bot is down"
        description: "The FireFeed Telegram Bot has been down for more than 1 minute"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Bot Not Starting

**Symptoms**: Container exits immediately or shows startup errors

**Solutions**:
```bash
# Check logs
docker-compose logs firefeed-telegram-bot

# Verify environment variables
docker-compose exec firefeed-telegram-bot env | grep TELEGRAM

# Test database connection
docker-compose exec firefeed-telegram-bot python -c "
import asyncio
from services.user_service import UserService
async def test():
    service = UserService()
    result = await service.get_user(123456)
    print('Database connection successful')
asyncio.run(test())
"
```

#### 2. Telegram API Errors

**Symptoms**: Bot can't send messages or receives API errors

**Solutions**:
```bash
# Verify bot token
curl -s "https://api.telegram.org/botYOUR_TOKEN/getMe"

# Check Telegram API status
curl -s "https://api.telegram.org/botYOUR_TOKEN/getWebhookInfo"

# Test message sending
curl -X POST "https://api.telegram.org/botYOUR_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "YOUR_CHAT_ID", "text": "Test message"}'
```

#### 3. Database Connection Issues

**Symptoms**: Database connection errors or timeouts

**Solutions**:
```bash
# Test database connection
docker-compose exec postgres psql -U postgres -c "SELECT 1;"

# Check connection from bot container
docker-compose exec firefeed-telegram-bot python -c "
import asyncio
from services.user_service import UserService
async def test():
    service = UserService()
    result = await service.get_user(123456)
    print('Database connection successful')
asyncio.run(test())
"
```

#### 4. Redis Connection Issues

**Symptoms**: Cache operations failing or Redis connection errors

**Solutions**:
```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Check Redis from bot container
docker-compose exec firefeed-telegram-bot python -c "
import asyncio
from services.cache_service import CacheService
async def test():
    service = CacheService()
    await service.connect()
    result = await service.get('test')
    print('Redis connection successful')
asyncio.run(test())
"
```

### Debug Commands

#### Docker Compose

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f firefeed-telegram-bot

# Execute command in container
docker-compose exec firefeed-telegram-bot bash

# Restart service
docker-compose restart firefeed-telegram-bot

# Check service status
docker-compose ps
```

#### Kubernetes

```bash
# View pod status
kubectl get pods -n firefeed-telegram-bot

# View pod logs
kubectl logs -f pod-name -n firefeed-telegram-bot

# Execute command in pod
kubectl exec -it pod-name -n firefeed-telegram-bot -- bash

# Describe pod (for events and issues)
kubectl describe pod pod-name -n firefeed-telegram-bot

# Check service endpoints
kubectl get endpoints -n firefeed-telegram-bot
```

### Performance Issues

#### High Memory Usage

```bash
# Monitor memory usage
docker stats

# Check for memory leaks in logs
docker-compose logs firefeed-telegram-bot | grep -i "memory\|out of memory"

# Adjust memory limits
# Edit docker-compose.yml or Kubernetes deployment
```

#### High CPU Usage

```bash
# Monitor CPU usage
docker stats

# Check for infinite loops or heavy processing
docker-compose logs firefeed-telegram-bot | grep -i "error\|exception"

# Profile application (if needed)
docker-compose exec firefeed-telegram-bot python -m cProfile -o profile.stats app.py
```

#### Database Performance

```bash
# Check database connections
docker-compose exec postgres psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Check slow queries
docker-compose exec postgres psql -U postgres -c "SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Optimize database (if needed)
docker-compose exec postgres psql -U postgres -c "VACUUM ANALYZE;"
```

### Log Analysis

#### Structured Logging

The application uses structured logging with correlation IDs:

```bash
# Filter logs by user
docker-compose logs firefeed-telegram-bot | grep "user_id=123456"

# Filter logs by action
docker-compose logs firefeed-telegram-bot | grep "action=subscribe"

# Filter logs by correlation ID
docker-compose logs firefeed-telegram-bot | grep "correlation_id="
```

#### Error Patterns

Common error patterns to watch for:

```bash
# Telegram API errors
docker-compose logs firefeed-telegram-bot | grep -i "telegram.*error"

# Database errors
docker-compose logs firefeed-telegram-bot | grep -i "database.*error"

# Network errors
docker-compose logs firefeed-telegram-bot | grep -i "network.*error"

# Cache errors
docker-compose logs firefeed-telegram-bot | grep -i "cache.*error"
```

---

**Note**: This deployment guide is part of the FireFeed Telegram Bot project. For more information about the project, see the main [README](../README.md).