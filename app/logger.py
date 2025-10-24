import logging
import uuid
from fastapi import Request, Header
from typing import Optional, Any, Dict

from app.config import request_id as request_id_ctx

# Get the standard logger
logger: logging.Logger = logging.getLogger(__name__)

class RequestIDLogger:
    """Logger wrapper that automatically includes request ID."""
    
    def __init__(self, base_logger: logging.Logger) -> None:
        """Initialize the request ID logger.
        
        Args:
            base_logger: Base logger instance to wrap
        """
        self.logger: logging.Logger = base_logger
    
    def _get_extra(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get extra context with request ID.
        
        Args:
            extra: Additional extra context
            
        Returns:
            Dictionary with request ID and any additional context
        """
        current_request_id: str = request_id_ctx.get()
        extra_dict: Dict[str, Any] = extra or {}
        extra_dict['request_id'] = current_request_id
        return extra_dict
    
    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Log debug message with request ID."""
        self.logger.debug(msg, extra=self._get_extra(extra), **kwargs)
    
    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Log info message with request ID."""
        self.logger.info(msg, extra=self._get_extra(extra), **kwargs)
    
    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Log warning message with request ID."""
        self.logger.warning(msg, extra=self._get_extra(extra), **kwargs)
    
    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Log error message with request ID."""
        self.logger.error(msg, extra=self._get_extra(extra), **kwargs)
    
    def exception(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Log exception with request ID."""
        self.logger.exception(msg, extra=self._get_extra(extra), **kwargs)
    
    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None, **kwargs: Any) -> None:
        """Log critical message with request ID."""
        self.logger.critical(msg, extra=self._get_extra(extra), **kwargs)

# Create the enhanced logger
request_logger: RequestIDLogger = RequestIDLogger(logger)

async def get_request_id(
    request: Request,  # noqa: ARG001
    x_request_id: Optional[str] = Header(None, alias="X-Request-ID"),
) -> str:
    """Dependency to get or generate request ID.
    
    Args:
        request: FastAPI request object
        x_request_id: X-Request-ID header value
        
    Returns:
        Request ID string
    """
    if x_request_id:
        return x_request_id
    return str(uuid.uuid4())

async def setup_request_context(request_id: str) -> str:
    """Setup request context for logging.
    
    Args:
        request_id: Request ID to set in context
        
    Returns:
        The request ID
    """
    request_id_ctx.set(request_id)
    return request_id