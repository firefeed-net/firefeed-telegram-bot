# Firefeed Telegram Bot

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-Passing-green.svg)](https://github.com/yuremweiland/firefeed/actions)

This module contains a Telegram bot for Firefeed that allows users to receive RSS news in Telegram.

## Description

The Telegram bot serves as the main interface for user interaction with the FireFeed system. It provides personalized news delivery, subscription management, and multilingual support.

### Key Features

- **Personalized news delivery**: Users receive news based on category subscriptions in their preferred language
- **Multilingual interface**: Full localization to English, Russian, German, and French languages
- **Subscription management**: Easy subscription setup for categories via inline keyboards
- **Automatic publishing**: News is automatically published to configured Telegram channels

### Publication Rate Limits

To prevent spam and ensure fair usage, the bot implements sophisticated rate limits for news publications:

#### Feed-level Limits
Each RSS feed has configurable limits:
- `cooldown_minutes`: Minimum time between publications from this feed (default: 60 minutes)
- `max_news_per_hour`: Maximum number of news items per hour from this feed (default: 10)

#### Telegram Publication Checks
Before publishing any news to Telegram channels, the system performs two checks:

1. **Quantity limit**:
   - Counts publications from the same feed in the last 60 minutes
   - If count >= `max_news_per_hour`, skips publication
   - Uses data from the `rss_items_telegram_bot_published` table

2. **Time limit**:
   - Checks time since last publication from the same feed
   - If elapsed time < `cooldown_minutes`, skips publication

##### How it works
```python
# Example: feed with cooldown_minutes=120, max_news_per_hour=1
# - Maximum 1 publication per 120 minutes
# - Minimum 120 minutes between publications

# Before each publication attempt:
recent_count = get_recent_telegram_publications_count(feed_id, 60)
if recent_count >= 1:
    skip_publication()

last_time = get_last_telegram_publication_time(feed_id)
if last_time:
    elapsed = now - last_time
    if elapsed < timedelta(minutes=120):
        skip_publication()
```

This ensures that even if multiple news items from the same feed are processed simultaneously, only the allowed number will be published to Telegram, preventing limit violations and maintaining user experience quality.

## Installation and Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in the variables:
   ```bash
   cp .env.example .env
   ```

3. Configure environment variables in `.env`:
   - `BOT_TOKEN`: Bot token from @BotFather
   - `WEBHOOK_URL`: Public URL for webhook
   - `API_BASE_URL`: API server URL
   - `BOT_API_KEY`: Key for API authentication
   - Database and Redis settings

## Running

Run the bot:
```bash
python -m telegram_bot
```

Or use the script:
```bash
./run_bot.sh
```

## Structure

- `core/`: Common dependencies (config, repositories, services)
- `handlers/`: Command and callback handlers
- `services/`: Bot services (API, DB, Telegram)
- `models/`: Data models
- `utils/`: Utilities for formatting and validation
- `translations.py`: Localization

## Functionality

- Receiving RSS news
- Subscription management
- Multilingual support
- Sending to channels and private messages

## Webhook Setup

For webhook mode, configure Nginx:

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location /webhook {
        proxy_pass http://127.0.0.1:5000/webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Systemd Service

For production, use a systemd service:

```ini
[Unit]
Description=FireFeed Telegram Bot Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/firefeed/apps/telegram_bot
Environment=HOME=/path/to/data
ExecStart=/path/to/firefeed/apps/telegram_bot/run_bot.sh
Restart=on-failure
RestartSec=10
TimeoutStopSec=30
KillMode=mixed
KillSignal=SIGTERM
SendSIGKILL=yes
NoNewPrivileges=no

[Install]
WantedBy=default.target
```