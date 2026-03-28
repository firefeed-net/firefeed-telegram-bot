# Multi-stage build for FireFeed Telegram Bot
FROM python:3.13-slim AS builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add labels
LABEL maintainer="FireFeed Team <mail@firefeed.net>"
LABEL description="FireFeed Telegram Bot - RSS notifications bot"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="FireFeed Telegram Bot"
LABEL org.label-schema.description="Telegram bot for RSS notifications"
LABEL org.label-schema.url="https://github.com/firefeed-net/firefeed-telegram-bot"
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.vcs-url="https://github.com/firefeed-net/firefeed-telegram-bot"
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.schema-version="1.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy requirements
COPY firefeed-telegram-bot/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.13-slim AS production

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Add labels
LABEL maintainer="FireFeed Team <mail@firefeed.net>"
LABEL description="FireFeed Telegram Bot - RSS notifications bot"
LABEL org.label-schema.build-date=$BUILD_DATE
LABEL org.label-schema.name="FireFeed Telegram Bot"
LABEL org.label-schema.description="Telegram bot for RSS notifications"
LABEL org.label-schema.url="https://github.com/firefeed-net/firefeed-telegram-bot"
LABEL org.label-schema.vcs-ref=$VCS_REF
LABEL org.label-schema.vcs-url="https://github.com/firefeed-net/firefeed-telegram-bot"
LABEL org.label-schema.version=$VERSION
LABEL org.label-schema.schema-version="1.0"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser firefeed-telegram-bot/ .

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Expose ports
EXPOSE 8080 8081

# Set entrypoint
ENTRYPOINT ["python", "main.py"]