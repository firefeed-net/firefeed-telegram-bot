# FireFeed Telegram Bot - Monitoring Setup

This document provides comprehensive information on setting up monitoring and observability for the FireFeed Telegram Bot.

## 📋 Table of Contents

- [Monitoring Overview](#monitoring-overview)
- [Metrics Collection](#metrics-collection)
- [Logging Strategy](#logging-strategy)
- [Health Checks](#health-checks)
- [Alerting](#alerting)
- [Grafana Dashboards](#grafana-dashboards)
- [Troubleshooting](#troubleshooting)

## 📊 Monitoring Overview

The FireFeed Telegram Bot implements comprehensive monitoring and observability features:

- **Prometheus Metrics**: Application and system metrics
- **Structured Logging**: JSON logging with correlation IDs
- **Health Checks**: Service and dependency health monitoring
- **Alerting**: Proactive alerting for issues
- **Dashboards**: Visual monitoring through Grafana

### Monitoring Stack Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Grafana                              │
│                    (Dashboards & Alerts)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ HTTP
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      Prometheus                             │
│                   (Metrics Collection)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Service Discovery
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                FireFeed Telegram Bot                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Metrics Export  │  │ Health Checks   │  │ Structured   │ │
│  │                 │  │                 │  │ Logging      │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 📈 Metrics Collection

### Prometheus Integration

The application exposes Prometheus metrics on port 8080:

```bash
# Metrics endpoint
curl http://localhost:8080/metrics
```

### Custom Metrics

#### Application Metrics

```python
# Example metrics implementation
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('bot_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('bot_request_duration_seconds', 'Request duration')
ACTIVE_USERS = Gauge('bot_active_users', 'Number of active users')

# Notification metrics
NOTIFICATIONS_SENT = Counter('bot_notifications_sent_total', 'Total notifications sent', ['status'])
NOTIFICATION_DURATION = Histogram('bot_notification_duration_seconds', 'Notification duration')
QUEUE_SIZE = Gauge('bot_notification_queue_size', 'Notification queue size')
```

#### System Metrics

```python
# Cache metrics
CACHE_HITS = Counter('bot_cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('bot_cache_misses_total', 'Total cache misses')
CACHE_SIZE = Gauge('bot_cache_size', 'Current cache size')

# Database metrics
DB_CONNECTIONS = Gauge('bot_db_connections', 'Database connections')
DB_QUERY_DURATION = Histogram('bot_db_query_duration_seconds', 'Database query duration')

# Redis metrics
REDIS_CONNECTIONS = Gauge('bot_redis_connections', 'Redis connections')
REDIS_OPERATIONS = Counter('bot_redis_operations_total', 'Redis operations', ['operation', 'status'])
```

### Metrics Endpoints

#### Health Check Endpoint

```python
# GET /health
{
    "timestamp": "2025-12-22T12:00:00",
    "overall_status": "healthy",
    "services": {
        "redis": {
            "status": "healthy",
            "message": "Redis connection is working"
        },
        "firefeed_api": {
            "status": "healthy", 
            "message": "FireFeed API is accessible"
        },
        "telegram_bot": {
            "status": "healthy",
            "message": "Telegram Bot is accessible"
        }
    },
    "checks_passed": 3,
    "checks_total": 3
}
```

#### Detailed Health Endpoint

```python
# GET /health/detailed
{
    "timestamp": "2025-12-22T12:00:00",
    "services": { /* service health data */ },
    "system_info": {
        "platform": "Linux",
        "python_version": "3.11.5",
        "cpu_count": 4,
        "memory_total": 8589934592,
        "memory_available": 4294967296,
        "disk_usage": 45.2
    },
    "metrics": {
        "cache_stats": {
            "size": 100,
            "hits": 500,
            "misses": 50,
            "hit_rate": 0.909
        },
        "health_check_interval": 30,
        "last_check": "2025-12-22T12:00:00"
    }
}
```

### Prometheus Configuration

#### Service Monitor (Kubernetes)

```yaml
# k8s/prometheus-service-monitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: firefeed-telegram-bot
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: firefeed-telegram-bot
  endpoints:
  - port: metrics
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

#### Prometheus Rules

```yaml
# k8s/prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: firefeed-telegram-bot-rules
  namespace: monitoring
spec:
  groups:
  - name: firefeed-telegram-bot
    interval: 30s
    rules:
    # Uptime rule
    - record: firefeed_telegram_bot_up
      expr: up{job="firefeed-telegram-bot"}
    
    # Request rate
    - record: firefeed_telegram_bot_request_rate
      expr: rate(bot_requests_total[5m])
    
    # Error rate
    - record: firefeed_telegram_bot_error_rate
      expr: rate(bot_requests_total{status=~"5.."}[5m])
    
    # Notification rate
    - record: firefeed_telegram_bot_notification_rate
      expr: rate(bot_notifications_sent_total[5m])
    
    # Cache hit rate
    - record: firefeed_telegram_bot_cache_hit_rate
      expr: rate(bot_cache_hits_total[5m]) / (rate(bot_cache_hits_total[5m]) + rate(bot_cache_misses_total[5m]))
```

## 📝 Logging Strategy

### Structured Logging

The application uses structured JSON logging with correlation IDs:

```python
import logging
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Example log entry
logger.info(
    "User action",
    user_id=123456,
    action="subscribe",
    category_id=1,
    correlation_id="abc-123-def"
)
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General information about bot operations
- **WARNING**: Warning conditions that don't stop the bot
- **ERROR**: Error conditions that might stop the bot
- **CRITICAL**: Critical errors that will stop the bot

### Log Fields

#### Standard Fields

```json
{
    "@timestamp": "2025-12-22T12:00:00.000Z",
    "level": "info",
    "logger": "firefeed_telegram_bot.services.telegram_bot",
    "message": "User action",
    "user_id": 123456,
    "action": "subscribe",
    "category_id": 1,
    "correlation_id": "abc-123-def",
    "span_id": "span-123",
    "trace_id": "trace-456"
}
```

#### Error Logs

```json
{
    "@timestamp": "2025-12-22T12:00:00.000Z",
    "level": "error",
    "logger": "firefeed_telegram_bot.services.user_service",
    "message": "Failed to get user",
    "user_id": 123456,
    "error": "Database connection failed",
    "error_type": "DatabaseError",
    "correlation_id": "abc-123-def",
    "stacktrace": "Traceback (most recent call last)..."
}
```

### Log Aggregation

#### Docker Logging

```yaml
# docker-compose.yml
services:
  firefeed-telegram-bot:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### Kubernetes Logging

```yaml
# k8s/logging-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: firefeed-telegram-bot-logging
  namespace: firefeed-telegram-bot
data:
  logback-spring.xml: |
    <configuration>
      <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LoggingEventCompositeJsonEncoder">
          <providers>
            <timestamp/>
            <logLevel/>
            <loggerName/>
            <message/>
            <mdc/>
            <stackTrace/>
          </providers>
        </encoder>
      </appender>
      
      <root level="INFO">
        <appender-ref ref="STDOUT"/>
      </root>
    </configuration>
```

## 🏥 Health Checks

### Health Check Endpoints

#### Basic Health Check

```python
# GET /health
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
```

#### Detailed Health Check

```python
# GET /health/detailed
async def detailed_health_check():
    """Detailed health check with service status."""
    health_data = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "system_info": {},
        "metrics": {}
    }
    
    # Check Redis
    redis_health = await health_checker._check_redis()
    health_data["services"]["redis"] = redis_health
    
    # Check FireFeed API
    api_health = await health_checker._check_firefeed_api()
    health_data["services"]["firefeed_api"] = api_health
    
    # Check Telegram Bot
    bot_health = await health_checker._check_telegram_bot()
    health_data["services"]["telegram_bot"] = bot_health
    
    # Calculate overall status
    services = health_data["services"].values()
    if all(service["status"] == "healthy" for service in services):
        health_data["overall_status"] = "healthy"
    else:
        health_data["overall_status"] = "unhealthy"
    
    return health_data
```

### Kubernetes Health Checks

```yaml
# k8s/deployment.yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8081
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health
    port: 8081
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Health Check Monitoring

#### Prometheus Health Checks

```yaml
# k8s/health-check-monitoring.yaml
apiVersion: v1
kind: Service
metadata:
  name: firefeed-telegram-bot-health
  namespace: monitoring
spec:
  selector:
    app: firefeed-telegram-bot
  ports:
  - name: health
    port: 8081
    targetPort: 8081
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: firefeed-telegram-bot-health
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: firefeed-telegram-bot
  endpoints:
  - port: health
    path: /health
    interval: 30s
```

## 🚨 Alerting

### Alert Rules

#### Critical Alerts

```yaml
# k8s/alert-rules-critical.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: firefeed-telegram-bot-critical
  namespace: monitoring
spec:
  groups:
  - name: firefeed-telegram-bot-critical
    rules:
    - alert: BotDown
      expr: up{job="firefeed-telegram-bot"} == 0
      for: 1m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "FireFeed Telegram Bot is down"
        description: "The FireFeed Telegram Bot has been down for more than 1 minute"
        runbook_url: "https://docs.firefeed.net/runbooks/bot-down"
    
    - alert: HighErrorRate
      expr: rate(bot_requests_total{status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "High error rate detected"
        description: "Error rate is {{ $value }} errors per second"
        runbook_url: "https://docs.firefeed.net/runbooks/high-error-rate"
    
    - alert: NotificationFailureRateHigh
      expr: rate(bot_notifications_sent_total{status="failed"}[5m]) > 0.05
      for: 5m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "High notification failure rate"
        description: "Notification failure rate is {{ $value }} failures per second"
        runbook_url: "https://docs.firefeed.net/runbooks/notification-failures"
```

#### Warning Alerts

```yaml
# k8s/alert-rules-warning.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: firefeed-telegram-bot-warning
  namespace: monitoring
spec:
  groups:
  - name: firefeed-telegram-bot-warning
    rules:
    - alert: HighResponseTime
      expr: histogram_quantile(0.95, rate(bot_request_duration_seconds_bucket[5m])) > 1.0
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High response time detected"
        description: "95th percentile response time is {{ $value }} seconds"
    
    - alert: LowCacheHitRate
      expr: rate(bot_cache_hits_total[5m]) / (rate(bot_cache_hits_total[5m]) + rate(bot_cache_misses_total[5m])) < 0.8
      for: 10m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Low cache hit rate"
        description: "Cache hit rate is {{ $value | humanizePercentage }}"
    
    - alert: HighNotificationQueue
      expr: bot_notification_queue_size > 1000
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High notification queue size"
        description: "Notification queue has {{ $value }} items"
```

### Alert Manager Configuration

```yaml
# k8s/alertmanager-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      smtp_smarthost: 'localhost:587'
      smtp_from: 'mail@firefeed.net'
    
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 1h
      receiver: 'web.hook'
      routes:
      - match:
          severity: critical
        receiver: 'critical-alerts'
      - match:
          severity: warning
        receiver: 'warning-alerts'
    
    receivers:
    - name: 'web.hook'
      webhook_configs:
      - url: 'http://alertmanager-webhook:5001/'
    
    - name: 'critical-alerts'
      email_configs:
      - to: 'mail@firefeed.net'
        subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
      slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#alerts-critical'
        title: 'Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    
    - name: 'warning-alerts'
      email_configs:
      - to: 'mail@firefeed.net'
        subject: '[WARNING] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          Alert: {{ .Annotations.summary }}
          Description: {{ .Annotations.description }}
          {{ end }}
```

## 📊 Grafana Dashboards

### Dashboard Configuration

#### Bot Overview Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "FireFeed Telegram Bot - Overview",
    "tags": ["firefeed", "telegram", "bot"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Bot Status",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"firefeed-telegram-bot\"}",
            "legendFormat": "Bot Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {
                "options": {
                  "0": {"text": "DOWN", "color": "red"},
                  "1": {"text": "UP", "color": "green"}
                },
                "type": "value"
              }
            ]
          }
        }
      },
      {
        "id": 2,
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bot_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bot_requests_total{status=~\"5..\"}[5m])",
            "legendFormat": "Errors/sec"
          }
        ]
      },
      {
        "id": 4,
        "title": "Notification Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(bot_notifications_sent_total[5m])",
            "legendFormat": "Notifications/sec"
          }
        ]
      },
      {
        "id": 5,
        "title": "Cache Hit Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(bot_cache_hits_total[5m]) / (rate(bot_cache_hits_total[5m]) + rate(bot_cache_misses_total[5m]))",
            "legendFormat": "Hit Rate"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percentunit",
            "min": 0,
            "max": 1
          }
        }
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
```

#### Service Health Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "FireFeed Telegram Bot - Service Health",
    "tags": ["firefeed", "telegram", "health"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Service Status",
        "type": "table",
        "targets": [
          {
            "expr": "bot_service_status",
            "format": "table"
          }
        ]
      },
      {
        "id": 2,
        "title": "Redis Health",
        "type": "graph",
        "targets": [
          {
            "expr": "bot_redis_connections",
            "legendFormat": "Connections"
          },
          {
            "expr": "rate(bot_redis_operations_total{status=\"success\"}[5m])",
            "legendFormat": "Operations/sec"
          }
        ]
      },
      {
        "id": 3,
        "title": "Database Health",
        "type": "graph",
        "targets": [
          {
            "expr": "bot_db_connections",
            "legendFormat": "Connections"
          },
          {
            "expr": "histogram_quantile(0.95, rate(bot_db_query_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile query time"
          }
        ]
      }
    ]
  }
}
```

### Dashboard Import

#### Via Grafana UI

1. Open Grafana in your browser
2. Navigate to **Dashboards** → **Import**
3. Paste the dashboard JSON configuration
4. Configure data source (Prometheus)
5. Import dashboard

#### Via API

```bash
# Import dashboard via API
curl -X POST \
  http://grafana:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d @dashboard-config.json \
  -u admin:password
```

#### Via ConfigMap (Kubernetes)

```yaml
# k8s/grafana-dashboard.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: firefeed-telegram-bot-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  firefeed-telegram-bot-overview.json: |
    {
      "dashboard": {
        "id": null,
        "title": "FireFeed Telegram Bot - Overview",
        "tags": ["firefeed", "telegram", "bot"],
        // ... dashboard configuration
      }
    }
```

## 🔍 Troubleshooting

### Common Monitoring Issues

#### 1. Metrics Not Appearing

**Symptoms**: No metrics in Prometheus or Grafana

**Solutions**:
```bash
# Check if metrics endpoint is accessible
curl http://localhost:8080/metrics

# Verify Prometheus configuration
kubectl get servicemonitor firefeed-telegram-bot -n monitoring

# Check Prometheus targets
# Navigate to Prometheus UI → Status → Targets

# Verify service discovery
kubectl get endpoints firefeed-telegram-bot -n firefeed-telegram-bot
```

#### 2. Alerts Not Firing

**Symptoms**: Alerts configured but not triggering

**Solutions**:
```bash
# Check AlertManager configuration
kubectl get configmap alertmanager-config -n monitoring -o yaml

# Verify alert rules
kubectl get prometheusrules firefeed-telegram-bot-critical -n monitoring -o yaml

# Check AlertManager status
# Navigate to AlertManager UI → Status

# Test alert rule
# Navigate to Prometheus UI → Alerts
```

#### 3. Grafana Dashboards Not Loading

**Symptoms**: Dashboards show no data or errors

**Solutions**:
```bash
# Check data source configuration
# Navigate to Grafana UI → Configuration → Data Sources

# Verify dashboard queries
# Navigate to Grafana UI → Dashboard → Edit → Panel → Query

# Check time range
# Ensure time range in Grafana matches data availability

# Verify permissions
kubectl auth can-i get pods -n monitoring
```

### Log Analysis

#### Finding Issues in Logs

```bash
# Search for errors
grep -i "error\|exception" /var/log/firefeed-telegram-bot/*.log

# Search for specific user issues
grep "user_id=123456" /var/log/firefeed-telegram-bot/*.log

# Search for notification failures
grep "notification.*failed" /var/log/firefeed-telegram-bot/*.log

# Search for API errors
grep "api.*error\|firefeed.*error" /var/log/firefeed-telegram-bot/*.log
```

#### Log Aggregation Queries

```bash
# Using Loki (if configured)
# Search for errors in last hour
{job="firefeed-telegram-bot"} |= "ERROR" | json | level="ERROR"

# Count errors by type
{job="firefeed-telegram-bot"} |= "ERROR" | json | level="ERROR" | line_format "{{.error_type}}" | count by (error_type)

# Search for specific correlation ID
{job="firefeed-telegram-bot"} | json | correlation_id="abc-123-def"
```

### Performance Monitoring

#### Identifying Performance Issues

```bash
# Check response times
# Prometheus query: histogram_quantile(0.95, rate(bot_request_duration_seconds_bucket[5m]))

# Check memory usage
# Prometheus query: container_memory_usage_bytes{pod=~"firefeed-telegram-bot.*"}

# Check CPU usage
# Prometheus query: rate(container_cpu_usage_seconds_total{pod=~"firefeed-telegram-bot.*"}[5m])

# Check notification queue size
# Prometheus query: bot_notification_queue_size
```

#### Performance Optimization

```bash
# Database optimization
# Check slow queries
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# Cache optimization
# Check cache hit rate
# Prometheus query: rate(bot_cache_hits_total[5m]) / (rate(bot_cache_hits_total[5m]) + rate(bot_cache_misses_total[5m]))

# Memory optimization
# Check memory usage patterns
# Prometheus query: container_memory_usage_bytes{pod=~"firefeed-telegram-bot.*"}
```

### Health Check Debugging

#### Manual Health Check Testing

```bash
# Test basic health check
curl -f http://localhost:8081/health

# Test detailed health check
curl -f http://localhost:8081/health/detailed

# Test individual service health
# These would be internal endpoints or methods
```

#### Health Check Troubleshooting

```bash
# Check Redis connection
redis-cli -h redis ping

# Check database connection
psql -h postgres -U postgres -c "SELECT 1;"

# Check FireFeed API
curl -H "X-API-Key: your_key" http://firefeed-api:8000/api/v1/health

# Check Telegram Bot
curl -s "https://api.telegram.org/botYOUR_TOKEN/getMe"
```

---

**Note**: This monitoring setup guide is part of the FireFeed Telegram Bot project. For more information about the project, see the main [README](../README.md).