# Use official Python 3.13 slim image to reduce size
FROM python:3.13-slim

# Install system dependencies (if needed for heavy libraries like torch)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code
COPY . .

# Create directory for data (if needed for images, but better to mount volume)
RUN mkdir -p /app/data

# Expose port for Telegram bot webhook (default 5000)
EXPOSE 5000

# By default, start Telegram bot
CMD ["python", "__main__.py"]