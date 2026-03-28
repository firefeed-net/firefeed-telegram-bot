# FireFeed Telegram Bot - API Documentation

This document provides comprehensive API documentation for the FireFeed Telegram Bot, including internal service APIs and external integrations.

## 📋 Table of Contents

- [Internal Service APIs](#internal-service-apis)
- [External API Integrations](#external-api-integrations)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Authentication](#authentication)

## 🔌 Internal Service APIs

### TelegramBotService

Main service for handling Telegram bot functionality.

#### Methods

##### `start_polling()`
Start the bot using long polling.

**Parameters**: None
**Returns**: None
**Raises**: `TelegramBotError` on failure

```python
await bot_service.start_polling()
```

##### `start_webhook()`
Start the bot using webhook.

**Parameters**: None
**Returns**: None
**Raises**: `TelegramBotError` on failure

```python
await bot_service.start_webhook()
```

##### `send_notification(user_id, articles, language)`
Send notification to user with articles.

**Parameters**:
- `user_id` (int): Telegram user ID
- `articles` (List[Dict]): List of article data
- `language` (str): Target language code

**Returns**: None
**Raises**: `TelegramBotError` on failure

```python
articles = [
    {
        "title": "Article Title",
        "link": "https://example.com/article",
        "summary": "Article summary",
        "category": "Technology"
    }
]
await bot_service.send_notification(123456, articles, "en")
```

### UserService

Service for managing user data and preferences.

#### Methods

##### `register_user(user_id, username)`
Register a new user.

**Parameters**:
- `user_id` (int): Telegram user ID
- `username` (str): Telegram username

**Returns**: bool - True if successful, False otherwise

```python
success = await user_service.register_user(123456, "username")
```

##### `get_user(user_id)`
Get user by ID.

**Parameters**:
- `user_id` (int): Telegram user ID

**Returns**: Optional[User] - User object or None

```python
user = await user_service.get_user(123456)
if user:
    print(f"User: {user.username}, Language: {user.language}")
```

##### `update_user_language(user_id, language)`
Update user's preferred language.

**Parameters**:
- `user_id` (int): Telegram user ID
- `language` (str): Language code (e.g., "en", "ru", "de")

**Returns**: bool - True if successful, False otherwise

```python
success = await user_service.update_user_language(123456, "ru")
```

##### `update_user_notifications(user_id, enabled)`
Enable or disable user notifications.

**Parameters**:
- `user_id` (int): Telegram user ID
- `enabled` (bool): Whether notifications should be enabled

**Returns**: bool - True if successful, False otherwise

```python
success = await user_service.update_user_notifications(123456, True)
```

##### `get_user_settings(user_id)`
Get user settings.

**Parameters**:
- `user_id` (int): Telegram user ID

**Returns**: Optional[UserSettings] - User settings or None

```python
settings = await user_service.get_user_settings(123456)
if settings:
    print(f"Language: {settings.language}")
    print(f"Notifications: {settings.notifications_enabled}")
```

### SubscriptionService

Service for managing user subscriptions to categories.

#### Methods

##### `get_available_categories()`
Get list of available categories.

**Parameters**: None
**Returns**: List[Dict] - List of category objects

```python
categories = await subscription_service.get_available_categories()
for category in categories:
    print(f"Category: {category['name']}")
```

##### `subscribe_to_category(user_id, category_id)`
Subscribe user to a category.

**Parameters**:
- `user_id` (int): Telegram user ID
- `category_id` (int): Category ID

**Returns**: bool - True if subscribed, False if already subscribed

```python
success = await subscription_service.subscribe_to_category(123456, 1)
```

##### `unsubscribe_from_category(user_id, category_id)`
Unsubscribe user from a category.

**Parameters**:
- `user_id` (int): Telegram user ID
- `category_id` (int): Category ID

**Returns**: bool - True if unsubscribed, False if not subscribed

```python
success = await subscription_service.unsubscribe_from_category(123456, 1)
```

##### `get_user_subscriptions(user_id)`
Get user's subscriptions.

**Parameters**:
- `user_id` (int): Telegram user ID

**Returns**: List[Subscription] - List of subscription objects

```python
subscriptions = await subscription_service.get_user_subscriptions(123456)
for sub in subscriptions:
    print(f"Subscribed to: {sub.category_name}")
```

### NotificationService

Service for managing notifications.

#### Methods

##### `schedule_notification(user_id, articles, language)`
Schedule notification for user.

**Parameters**:
- `user_id` (int): Telegram user ID
- `articles` (List[Dict]): List of article data
- `language` (str): Target language code

**Returns**: None

```python
await notification_service.schedule_notification(123456, articles, "en")
```

##### `schedule_batch_notifications(articles_by_category)`
Schedule notifications for multiple users based on categories.

**Parameters**:
- `articles_by_category` (Dict[int, List[Dict]]): Articles grouped by category ID

**Returns**: None

```python
articles_by_category = {
    1: [{"title": "Tech Article", "category": "Technology"}],
    2: [{"title": "Science Article", "category": "Science"}]
}
await notification_service.schedule_batch_notifications(articles_by_category)
```

##### `start_notification_worker()`
Start the notification worker.

**Parameters**: None
**Returns**: None

```python
await notification_service.start_notification_worker()
```

### TranslationService

Service for handling text translation.

#### Methods

##### `translate_text(text, target_language, source_language="auto")`
Translate text to target language.

**Parameters**:
- `text` (str): Text to translate
- `target_language` (str): Target language code
- `source_language` (str): Source language code (default: "auto")

**Returns**: Optional[str] - Translated text or original text on failure

```python
translated = await translation_service.translate_text(
    "Hello world", "ru", "en"
)
```

##### `translate_articles(articles, target_language)`
Translate list of articles.

**Parameters**:
- `articles` (List[Dict]): List of article objects
- `target_language` (str): Target language code

**Returns**: List[Dict] - List of translated articles

```python
translated_articles = await translation_service.translate_articles(
    articles, "ru"
)
```

##### `get_supported_languages()`
Get list of supported languages.

**Parameters**: None
**Returns**: List[str] - List of language codes

```python
languages = await translation_service.get_supported_languages()
print(f"Supported languages: {languages}")
```

### CacheService

Service for caching operations.

#### Methods

##### `get(key)`
Get value from cache.

**Parameters**:
- `key` (str): Cache key

**Returns**: Optional[Any] - Cached value or None

```python
value = await cache_service.get("translation:key")
```

##### `set(key, value, ttl=None)`
Set value in cache.

**Parameters**:
- `key` (str): Cache key
- `value` (Any): Value to cache
- `ttl` (int): Time to live in seconds (optional)

**Returns**: bool - True if successful, False otherwise

```python
await cache_service.set("translation:key", "translated_text", 3600)
```

##### `delete(key)`
Delete key from cache.

**Parameters**:
- `key` (str): Cache key

**Returns**: bool - True if deleted, False if not found

```python
await cache_service.delete("translation:key")
```

### HealthChecker

Service for health monitoring.

#### Methods

##### `perform_health_check()`
Perform comprehensive health check.

**Parameters**: None
**Returns**: None

```python
await health_checker.perform_health_check()
```

##### `get_health_status()`
Get current health status.

**Parameters**: None
**Returns**: Dict - Health status information

```python
status = health_checker.get_health_status()
print(f"Overall status: {status['overall_status']}")
```

## 🔗 External API Integrations

### FireFeed API Integration

The Telegram Bot integrates with the FireFeed API for user and subscription management.

#### Base Configuration

```python
BASE_URL = "http://localhost:8000"
API_KEY = "your_api_key"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}
```

#### User Management Endpoints

##### `POST /api/v1/users/telegram`
Register a new Telegram user.

**Request Body**:
```json
{
    "telegram_id": 123456,
    "username": "username",
    "language": "en",
    "timezone": "UTC",
    "notifications_enabled": true,
    "max_articles_per_notification": 5,
    "notification_interval": 60
}
```

**Response**:
```json
{
    "id": 123,
    "telegram_id": 123456,
    "username": "username",
    "language": "en",
    "timezone": "UTC",
    "notifications_enabled": true,
    "max_articles_per_notification": 5,
    "notification_interval": 60,
    "created_at": "2025-12-22T10:00:00",
    "last_activity": "2025-12-22T12:00:00",
    "is_blocked": false
}
```

##### `GET /api/v1/users/telegram/{user_id}`
Get user by Telegram ID.

**Response**:
```json
{
    "id": 123,
    "telegram_id": 123456,
    "username": "username",
    "language": "en",
    "timezone": "UTC",
    "notifications_enabled": true,
    "max_articles_per_notification": 5,
    "notification_interval": 60,
    "created_at": "2025-12-22T10:00:00",
    "last_activity": "2025-12-22T12:00:00",
    "is_blocked": false
}
```

##### `PATCH /api/v1/users/telegram/{user_id}/language`
Update user's language preference.

**Request Body**:
```json
{
    "language": "ru"
}
```

**Response**:
```json
{
    "message": "Language updated successfully"
}
```

#### Subscription Management Endpoints

##### `GET /api/v1/categories`
Get available categories.

**Response**:
```json
{
    "categories": [
        {
            "id": 1,
            "name": "Technology",
            "description": "Technology news and updates",
            "created_at": "2025-12-22T10:00:00"
        }
    ]
}
```

##### `POST /api/v1/subscriptions`
Create a new subscription.

**Request Body**:
```json
{
    "user_id": 123456,
    "category_id": 1
}
```

**Response**:
```json
{
    "message": "Subscription created successfully"
}
```

##### `DELETE /api/v1/subscriptions/{user_id}/{category_id}`
Delete a subscription.

**Response**:
```json
{
    "message": "Subscription deleted successfully"
}
```

#### Translation Endpoints

##### `POST /api/v1/translate`
Translate text.

**Request Body**:
```json
{
    "text": "Hello world",
    "target_language": "ru",
    "source_language": "en"
}
```

**Response**:
```json
{
    "translated_text": "Привет мир",
    "source_language": "en",
    "target_language": "ru",
    "confidence": 0.95
}
```

##### `GET /api/v1/translate/languages`
Get supported languages.

**Response**:
```json
{
    "languages": ["en", "ru", "de", "fr", "es"]
}
```

## 📊 Data Models

### User Model

```python
@dataclass
class User:
    id: int
    username: Optional[str]
    language: str
    timezone: str
    notifications_enabled: bool
    max_articles_per_notification: int
    notification_interval: int
    created_at: datetime
    last_activity: Optional[datetime]
    is_blocked: bool
```

### UserSettings Model

```python
@dataclass
class UserSettings:
    user_id: int
    language: str
    timezone: str
    notifications_enabled: bool
    max_articles_per_notification: int
    notification_interval: int
```

### Subscription Model

```python
@dataclass
class Subscription:
    user_id: int
    category_id: int
    category_name: str
    subscribed_at: datetime
```

### NotificationTask Model

```python
@dataclass
class NotificationTask:
    user_id: int
    articles: List[Dict[str, Any]]
    language: str
    scheduled_at: datetime
    retry_count: int = 0
```

## ⚠️ Error Handling

### Exception Hierarchy

```python
class TelegramBotError(Exception):
    """Base exception for Telegram bot errors."""
    
class UserError(TelegramBotError):
    """Exception for user-related errors."""
    
class SubscriptionError(TelegramBotError):
    """Exception for subscription-related errors."""
    
class NotificationError(TelegramBotError):
    """Exception for notification-related errors."""
    
class TranslationError(TelegramBotError):
    """Exception for translation-related errors."""
    
class CacheError(TelegramBotError):
    """Exception for cache-related errors."""
    
class HealthCheckError(TelegramBotError):
    """Exception for health check errors."""
```

### Error Handling Patterns

#### Service Method Error Handling

```python
async def get_user(self, user_id: int) -> Optional[User]:
    try:
        # Service logic here
        return user
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None
```

#### HTTP Request Error Handling

```python
try:
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"API error: {response.status}")
                return None
except Exception as e:
    logger.error(f"Network error: {e}")
    return None
```

#### Telegram API Error Handling

```python
try:
    await bot.send_message(chat_id=user_id, text=message)
except TelegramForbiddenError:
    logger.warning(f"User {user_id} blocked the bot")
    await self.user_service.block_user(user_id)
except TelegramBadRequest as e:
    logger.error(f"Telegram API error for user {user_id}: {e}")
except Exception as e:
    logger.error(f"Error sending notification to user {user_id}: {e}")
```

## 🔐 Authentication

### API Key Authentication

All requests to the FireFeed API require an API key:

```python
HEADERS = {
    "X-API-Key": self.config.firefeed_api.api_key,
    "Content-Type": "application/json"
}
```

### Telegram Bot Token

The Telegram bot uses a bot token for authentication:

```python
self.bot = Bot(token=self.config.telegram.token)
```

### Security Best Practices

1. **Environment Variables**: Store sensitive data in environment variables
2. **HTTPS**: Use HTTPS for all external API calls
3. **Input Validation**: Validate all user inputs
4. **Rate Limiting**: Implement rate limiting to prevent abuse
5. **Error Logging**: Log errors without exposing sensitive information

## 📈 API Usage Examples

### Complete User Registration Flow

```python
async def register_user_flow(user_id: int, username: str):
    user_service = UserService()
    
    # Register user
    success = await user_service.register_user(user_id, username)
    if not success:
        return "Registration failed"
    
    # Get user
    user = await user_service.get_user(user_id)
    if not user:
        return "User not found"
    
    # Update language
    await user_service.update_user_language(user_id, "en")
    
    return "User registered successfully"
```

### Complete Notification Flow

```python
async def send_notifications_flow(articles_by_category: Dict[int, List[Dict]]):
    notification_service = NotificationService()
    
    # Schedule notifications
    await notification_service.schedule_batch_notifications(articles_by_category)
    
    # Start worker
    await notification_service.start_notification_worker()
    
    return "Notifications scheduled"
```

### Complete Translation Flow

```python
async def translate_content_flow(text: str, target_language: str):
    translation_service = TranslationService()
    
    # Check cache first
    cache_key = f"translation:{text}:{target_language}"
    cached = await translation_service.cache_service.get(cache_key)
    if cached:
        return cached
    
    # Translate text
    translated = await translation_service.translate_text(text, target_language)
    
    # Cache result
    await translation_service.cache_service.set(cache_key, translated, ttl=3600)
    
    return translated
```

---

**Note**: This API documentation is part of the FireFeed Telegram Bot project. For more information about the project, see the main [README](../README.md).