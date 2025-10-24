import logging
from contextvars import ContextVar
from typing import Any
from pydantic_settings import BaseSettings
import sys

# Context variable for request ID
request_id: ContextVar[str] = ContextVar('request_id', default='default')

class Settings(BaseSettings):
    """Application settings configuration."""
    
    BOT_TOKEN: str
    WEBHOOK_URL: str
    WEBHOOK_PATH: str = "/webhook"
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8000
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False

class RequestIDFilter(logging.Filter):
    """Custom filter to inject request ID into log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to log record."""
        record.request_id = request_id.get()
        return True

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup comprehensive logging configuration with request ID.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured logger instance
    """
    log_level: int = getattr(logging, level.upper(), logging.INFO)
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create formatter with request ID
    formatter: logging.Formatter = logging.Formatter(Settings().LOG_FORMAT)
    
    # Create handlers
    console_handler: logging.StreamHandler[Any] = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIDFilter())
    
    file_handler: logging.FileHandler[Any] = logging.FileHandler("bot.log", encoding='utf-8') # type: ignore
    file_handler.setFormatter(formatter)
    file_handler.addFilter(RequestIDFilter())
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=[console_handler, file_handler]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger: logging.Logger = logging.getLogger(__name__)
    logger.info("Logging configured with request ID support", extra={"request_id": "system"})
    
    return logger

# Initialize settings and logging
settings: Settings = Settings()
logger: logging.Logger = setup_logging(settings.LOG_LEVEL)