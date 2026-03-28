"""Validation utilities for FireFeed Telegram Bot."""

import re
import logging
from typing import Optional


logger = logging.getLogger(__name__)


def validate_telegram_token(token: str) -> bool:
    """
    Validate Telegram bot token format.
    
    Args:
        token: Telegram bot token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    if not token:
        return False
    
    # Telegram bot token format: 123456789:ABCdefGHIjklMNOpqrsTUVwxYZ123_abc
    pattern = r'^\d{8,10}:[A-Za-z0-9_-]{35}$'
    
    if re.match(pattern, token):
        return True
    else:
        logger.warning(f"Invalid Telegram token format: {token[:10]}...")
        return False


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid, False otherwise
    """
    if not url:
        return False
    
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:[-\w.]|(?:%[\da-fA-F]{2}))+'  # domain name
        r'(?::\d+)?'  # optional port
        r'(?:[/?:].*)?$',  # path, query, fragment
        re.IGNORECASE
    )
    
    if url_pattern.match(url):
        return True
    else:
        logger.warning(f"Invalid URL format: {url}")
        return False


def validate_language_code(language_code: str) -> bool:
    """
    Validate language code format.
    
    Args:
        language_code: Language code to validate
        
    Returns:
        True if language code is valid, False otherwise
    """
    if not language_code:
        return False
    
    # ISO 639-1 language code format (2 letters)
    pattern = r'^[a-z]{2}$'
    
    if re.match(pattern, language_code.lower()):
        return True
    else:
        logger.warning(f"Invalid language code format: {language_code}")
        return False


def validate_integer(value: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> bool:
    """
    Validate integer value with optional range constraints.
    
    Args:
        value: String value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        True if value is valid integer within range, False otherwise
    """
    try:
        int_value = int(value)
        
        if min_value is not None and int_value < min_value:
            logger.warning(f"Value {int_value} is below minimum {min_value}")
            return False
        
        if max_value is not None and int_value > max_value:
            logger.warning(f"Value {int_value} is above maximum {max_value}")
            return False
        
        return True
        
    except ValueError:
        logger.warning(f"Invalid integer value: {value}")
        return False


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    if not email:
        return False
    
    # Basic email validation
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    if email_pattern.match(email):
        return True
    else:
        logger.warning(f"Invalid email format: {email}")
        return False


def validate_username(username: str) -> bool:
    """
    Validate Telegram username format.
    
    Args:
        username: Username to validate
        
    Returns:
        True if username is valid, False otherwise
    """
    if not username:
        return False
    
    # Telegram username format: 5-32 characters, letters, numbers, underscores
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    
    if re.match(pattern, username):
        return True
    else:
        logger.warning(f"Invalid username format: {username}")
        return False


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize text input by removing potentially harmful characters.
    
    Args:
        text: Text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = re.sub(r'[<>]', '', text)
    
    # Truncate if max_length is specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_message_length(message: str, max_length: int = 4096) -> bool:
    """
    Validate message length for Telegram.
    
    Args:
        message: Message to validate
        max_length: Maximum allowed length (default: 4096 for Telegram)
        
    Returns:
        True if message length is valid, False otherwise
    """
    if not message:
        return False
    
    if len(message) > max_length:
        logger.warning(f"Message length {len(message)} exceeds maximum {max_length}")
        return False
    
    return True


def validate_callback_data(data: str, max_length: int = 64) -> bool:
    """
    Validate callback data length for Telegram.
    
    Args:
        data: Callback data to validate
        max_length: Maximum allowed length (default: 64 for Telegram)
        
    Returns:
        True if callback data length is valid, False otherwise
    """
    if not data:
        return False
    
    if len(data) > max_length:
        logger.warning(f"Callback data length {len(data)} exceeds maximum {max_length}")
        return False
    
    return True