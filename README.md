# FireFeed Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://docker.com)
[![CI/CD](https://img.shields.io/badge/CI/CD-Configured-orange.svg)](https://github.com/firefeed-net/firefeed-telegram-bot/actions)

Telegram bot for FireFeed RSS notifications. This microservice provides a complete Telegram bot implementation for receiving RSS feed notifications with translation support, user management, and comprehensive monitoring.

> **Note**: This service is part of the [FireFeed platform](https://github.com/firefeed-net/firefeed) microservices architecture. It can be run standalone or as part of the complete FireFeed ecosystem with [API](https://github.com/firefeed-net/firefeed-api) and [RSS Parser](https://github.com/firefeed-net/firefeed-rss-parser).

## 🚀 Features

### Core Functionality
- **RSS Notifications**: Receive notifications for new RSS feed articles
- **Telegram Integration**: Full Telegram bot with command support
- **User Management**: Complete user registration and management system
- **Subscription System**: Category-based subscription management
- **Translation Support**: Multi-language support with automatic translation

### Advanced Features
- **Rate Limiting**: Smart rate limiting to prevent spam
- **Caching**: Redis-based caching for performance
- **Health Monitoring**: Comprehensive health checks and monitoring
- **Error Handling**: Robust error handling and logging
- **Security**: Production-ready security measures

### Technical Features
- **Modern Python**: Python 3.11+ with async/await patterns
- **Type Safety**: Full type hints and dataclasses
- **Dependency Injection**: Clean service architecture
- **Configuration Management**: Environment-based configuration
- **Container Native**: Docker containerization ready

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Monitoring](#monitoring)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Redis (for caching)
- PostgreSQL (for user data)

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/firefeed-net/firefeed-telegram-bot.git
   cd firefeed-telegram-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

5. **Access the bot:**
   - Bot will be available at the configured webhook URL
   - Health check: `http://localhost:8081/health`
   - Metrics: `http://localhost:8080/metrics`

## ⚙️ Configuration

### Environment Variables

The bot uses environment variables for configuration. Copy `.env.example` to `.env` and customize:

```bash
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_USE_WEBHOOK=false  # true for webhook, false for polling

# FireFeed API Integration
API_BASE_URL=http://localhost:8000
FIREFEED_API_SERVICE_TOKEN=your_api_key

# Database Configuration
DATABASE_HOST=localhost
DATABASE_NAME=firefeed_telegram_bot
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Translation Configuration
TRANSLATION_ENABLED=true
TRANSLATION_DEFAULT_LANGUAGE=en

# Monitoring
LOG_LEVEL=INFO
PROMETHEUS_ENABLED=true
```

### Configuration Files

- `config/services_config.py` - Service configuration classes
- `config/logging_config.py` - Logging configuration
- `docker-compose.yml` - Docker orchestration
- `Dockerfile` - Container build configuration

## 🤖 Usage

### Telegram Bot Commands

The bot supports the following commands:

- `/start` - Start the bot and register user
- `/help` - Show help and available commands
- `/subscribe` - Subscribe to categories
- `/unsubscribe` - Unsubscribe from categories
- `/subscriptions` - View current subscriptions
- `/language` - Change notification language
- `/settings` - Configure notification settings
- `/stats` - View usage statistics

### User Management

Users are automatically registered when they start the bot. The system provides:

- User registration and profile management
- Language preferences
- Notification settings
- Subscription management
- Activity tracking

### Subscription Management

Users can subscribe to RSS feed categories:

1. Use `/subscribe` to see available categories
2. Select categories via inline keyboard
3. Use `/subscriptions` to view current subscriptions
4. Use `/unsubscribe` to remove subscriptions

## 📚 API Reference

### Services

#### TelegramBotService
Main bot service handling all Telegram interactions.

```python
from services.telegram_bot import TelegramBotService

bot_service = TelegramBotService()
await bot_service.start_polling()  # Start polling
# or
await bot_service.start_webhook()  # Start webhook
```

#### UserService
User management and authentication.

```python
from services.user_service import UserService

user_service = UserService()
await user_service.register_user(user_id, username)
user = await user_service.get_user(user_id)
```

#### SubscriptionService
Category subscription management.

```python
from services.subscription_service import SubscriptionService

subscription_service = SubscriptionService()
await subscription_service.subscribe_to_category(user_id, category_id)
subscriptions = await subscription_service.get_user_subscriptions(user_id)
```

#### NotificationService
Notification sending and management.

```python
from services.notification_service import NotificationService

notification_service = NotificationService()
await notification_service.schedule_notification(user_id, articles, language)
await notification_service.start_notification_worker()
```

#### TranslationService
Text translation and language support.

```python
from services.translation_service import TranslationService

translation_service = TranslationService()
translated_text = await translation_service.translate_text(text, target_language)
translated_articles = await translation_service.translate_articles(articles, language)
```

### Configuration

#### Environment Configuration

```python
from config import get_config

config = get_config()
print(f"Environment: {config.environment}")
print(f"Telegram Token: {config.telegram.token}")
print(f"Database Host: {config.database.host}")
```

#### Service Configuration

```python
from config.services_config import Config, Environment

# Set environment
from config import set_environment
set_environment(Environment.PRODUCTION)

# Get configuration
from config import get_config
config = get_config()
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_telegram_bot.py

# Run with coverage
pytest --cov=firefeed_telegram_bot tests/

# Run integration tests
pytest tests/test_integration.py
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py          # Test configuration and fixtures
├── test_telegram_bot.py # Bot functionality tests
├── test_user_service.py # User service tests
├── test_subscription_service.py # Subscription tests
├── test_notification_service.py # Notification tests
├── test_translation_service.py # Translation tests
├── test_cache_service.py # Cache tests
├── test_health_checker.py # Health check tests
├── test_main.py         # Main module tests
├── test_integration.py  # Integration tests
└── README.md           # Test documentation
```

### Test Configuration

Test configuration is managed in `tests/conftest.py`:

```python
import pytest
from config import set_environment

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment."""
    set_environment(Environment.TESTING)
    # Additional test setup
```

## 🚢 Deployment

### Docker Deployment

#### Development Environment

```bash
# Start development environment
docker-compose up -d

# View logs
docker-compose logs -f firefeed-telegram-bot

# Stop services
docker-compose down
```

#### Production Environment

```bash
# Build production image
docker build -t firefeed/telegram-bot:latest .

# Deploy with production compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Monitor services
docker-compose ps
```

### Kubernetes Deployment

Kubernetes manifests are available in the `k8s/` directory:

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=firefeed-telegram-bot

# View logs
kubectl logs -f deployment/firefeed-telegram-bot
```

### Environment-Specific Configuration

#### Development
```bash
ENVIRONMENT=development
DEBUG=true
TELEGRAM_USE_WEBHOOK=false
```

#### Production
```bash
ENVIRONMENT=production
DEBUG=false
TELEGRAM_USE_WEBHOOK=true
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
```

## 📊 Monitoring

### Health Checks

The bot provides comprehensive health checks:

- **Health Endpoint**: `GET /health`
- **Metrics Endpoint**: `GET /metrics` (Prometheus format)
- **Service Status**: Individual service health checks

### Monitoring Stack

#### Prometheus Metrics

```bash
# Access metrics
curl http://localhost:8080/metrics
```

#### Grafana Dashboards

Grafana dashboards are configured in `monitoring/grafana/`:

- Bot performance metrics
- User activity statistics
- Service health monitoring
- Error rate tracking

#### Alerting

Alerting rules are configured in `monitoring/prometheus/alerts.yml`:

- Service downtime alerts
- High error rate notifications
- Performance degradation warnings

### Log Monitoring

Structured logging with correlation IDs:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("User action", extra={
    "user_id": user_id,
    "action": "subscribe",
    "category_id": category_id
})
```

## 🔄 Integration

### With FireFeed API
The Telegram Bot integrates with FireFeed API for:
- **User management** - Registration, authentication, preferences
- **RSS items** - Fetching news for notifications
- **Categories** - Managing user subscriptions
- **Translations** - Multi-language support

### With Other Services
- **[FireFeed API](https://github.com/firefeed-net/firefeed-api)** - Main API service
- **[FireFeed RSS Parser](https://github.com/firefeed-net/firefeed-rss-parser)** - RSS feed parsing service

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. **Fork the repository**
2. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/firefeed-telegram-bot.git
   cd firefeed-telegram-bot
   ```
3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```
5. **Run tests:**
   ```bash
   pytest
   ```
6. **Submit a pull request**

### Code Style

This project follows PEP 8 and uses Black for code formatting:

```bash
# Format code
black .

# Check code style
flake8

# Type checking
mypy firefeed_telegram_bot/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram bot framework
- [Redis](https://redis.io/) - Caching and session storage
- [PostgreSQL](https://www.postgresql.org/) - Database management
- [Prometheus](https://prometheus.io/) - Monitoring and alerting

## 📞 Support

For support and questions:

- **GitHub Issues**: [Create an issue](https://github.com/firefeed-net/firefeed-telegram-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/firefeed-net/firefeed-telegram-bot/discussions)
- **Documentation**: [Read the docs](https://github.com/firefeed-net/firefeed)
- **Community**: [Join our community](https://t.me/firefeed_community)
- **Email**: mail@firefeed.net

## 🔗 Related Projects

- [FireFeed Platform](https://github.com/firefeed-net/firefeed) - Main platform documentation
- [FireFeed API](https://github.com/firefeed-net/firefeed-api) - Main API service
- [FireFeed RSS Parser](https://github.com/firefeed-net/firefeed-rss-parser) - RSS parsing service

---

**Made with ❤️ by the FireFeed Team**

[![GitHub stars](https://img.shields.io/github/stars/firefeed-net/firefeed-telegram-bot.svg?style=social&label=Star)](https://github.com/firefeed-net/firefeed-telegram-bot)
[![Twitter Follow](https://img.shields.io/twitter/follow/firefeed?style=social)](https://twitter.com/firefeed)
