import traceback
from typing import Any, Dict, Optional, Type
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.logger import request_logger

class ErrorHandler:
    """Handler for different types of built-in exceptions."""
    
    # Map exception types to HTTP status codes
    EXCEPTION_STATUS_MAP: Dict[Type[Exception], int] = {
        # Developer/programming errors - 500 Internal Server Error
        RuntimeError: 500,
        AssertionError: 500,
        SystemError: 500,
        NotImplementedError: 501,
        
        # Client errors - 400 Bad Request
        ValueError: 400,
        TypeError: 400,
        
        # Not found - 404
        LookupError: 404,
        KeyError: 404,
        IndexError: 404,
        
        # Authentication/Authorization - 401/403
        PermissionError: 403,
    }
    
    @classmethod
    async def handle_exception(cls, request: Request, exc: Exception) -> JSONResponse:
        """Handle exceptions and convert to appropriate HTTP responses.
        
        Args:
            request: The request that caused the exception
            exc: The exception that was raised
            
        Returns:
            JSON response with error details
        """
        # Get status code from map or default to 500
        status_code = cls.EXCEPTION_STATUS_MAP.get(type(exc), 500)
        
        # Check if this is a panic
        is_panic = isinstance(exc, RuntimeError) and "panic:" in str(exc)
        
        # Log the error appropriately
        if is_panic:
            request_logger.error(
                f"Panic recovered in HTTP layer: {exc}",
                extra={
                    "error_type": "RuntimeError(Panic)",
                    "status_code": status_code,
                    "is_panic": True
                },
                exc_info=True
            )
        elif status_code >= 500:
            # Server errors - log as error
            request_logger.error(
                f"Server error: {exc}",
                extra={
                    "error_type": type(exc).__name__,
                    "status_code": status_code
                },
                exc_info=True
            )
        else:
            # Client errors - log as warning
            request_logger.warning(
                f"Client error: {exc}",
                extra={
                    "error_type": type(exc).__name__,
                    "status_code": status_code
                }
            )
        
        # Prepare response
        error_detail = str(exc).replace("panic: ", "") if is_panic else str(exc)
        
        response_data = {
            "detail": error_detail,
            "error_type": type(exc).__name__,
        }
        
        # Add debug info in development
        if status_code >= 500:
            response_data["traceback"] = traceback.format_exc().split('\n')
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )

# Global exception handler
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for FastAPI.
    
    Args:
        request: The request that caused the exception
        exc: The exception that was raised
        
    Returns:
        JSON response with error details
    """
    return await ErrorHandler.handle_exception(request, exc)