import logging
from typing import Any, Optional

from app.logger import request_logger

def assert_developer(condition: bool, message: str = "") -> None:
    """Use AssertionError for developer mistakes and programming errors.
    
    Args:
        condition: Condition that should always be true
        message: Error message if condition fails
        
    Raises:
        AssertionError: For developer programming errors
    """
    if not condition:
        request_logger.error(
            f"Developer assertion failed: {message}",
            extra={"error_type": "AssertionError"}
        )
        raise AssertionError(message or "Developer assertion failed")

def check_state(condition: bool, message: str = "") -> None:
    """Use RuntimeError for invalid program state.
    
    Args:
        condition: State condition that should be true
        message: Error message if state is invalid
        
    Raises:
        RuntimeError: For invalid program state
    """
    if not condition:
        request_logger.error(
            f"Invalid program state: {message}",
            extra={"error_type": "RuntimeError"}
        )
        raise RuntimeError(message or "Invalid program state")

def check_argument(condition: bool, message: str = "") -> None:
    """Use ValueError for invalid arguments.
    
    Args:
        condition: Argument condition that should be true
        message: Error message if argument is invalid
        
    Raises:
        ValueError: For invalid arguments
    """
    if not condition:
        request_logger.error(
            f"Invalid argument: {message}",
            extra={"error_type": "ValueError"}
        )
        raise ValueError(message or "Invalid argument")

def check_not_none(value: Optional[Any], message: str = "") -> Any:
    """Use ValueError for None values where they're not allowed.
    
    Args:
        value: Value to check
        message: Error message if value is None
        
    Returns:
        The non-None value
        
    Raises:
        ValueError: If value is None
    """
    if value is None:
        request_logger.error(
            f"Unexpected None value: {message}",
            extra={"error_type": "ValueError"}
        )
        raise ValueError(message or "Unexpected None value")
    return value

def unsupported_operation(message: str = "") -> None:
    """Use NotImplementedError for unsupported operations.
    
    Args:
        message: Error message describing the unsupported operation
        
    Raises:
        NotImplementedError: For operations that aren't implemented
    """
    request_logger.error(
        f"Unsupported operation: {message}",
        extra={"error_type": "NotImplementedError"}
    )
    raise NotImplementedError(message or "Unsupported operation")

def illegal_state(message: str = "") -> None:
    """Use SystemError for illegal internal state (JVM-like IllegalStateException).
    
    Args:
        message: Error message describing the illegal state
        
    Raises:
        SystemError: For illegal internal state
    """
    request_logger.critical(
        f"Illegal internal state: {message}",
        extra={"error_type": "SystemError"}
    )
    raise SystemError(message or "Illegal internal state")