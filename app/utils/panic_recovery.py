import functools
import logging
import traceback
from typing import Any, Callable, TypeVar, Optional, cast
from contextlib import contextmanager

from app.logger import request_logger

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

def panic(value: Any) -> None:
    """Go-style panic function using RuntimeError.
    
    Args:
        value: The panic value (can be any type)
        
    Raises:
        RuntimeError: For unrecoverable errors (nearest to Go panic)
    """
    # RuntimeError is the closest built-in for programming errors
    raise RuntimeError(f"panic: {value}")

def recover(default: Optional[T] = None) -> Callable[[F], F]:
    """Go-style recover decorator using built-in exceptions.
    
    Args:
        default: Default value to return if panic occurs
        
    Returns:
        Decorated function that catches panics
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except (RuntimeError, SystemExit, KeyboardInterrupt) as e:
                # RuntimeError - programming errors, assertion failures
                # SystemExit - sys.exit() calls  
                # KeyboardInterrupt - Ctrl+C
                if "panic:" in str(e):
                    request_logger.error(
                        f"Recovered from panic: {e}",
                        extra={
                            "panic_value": str(e).replace("panic: ", ""),
                            "traceback": traceback.format_exc()
                        }
                    )
                    return default
                else:
                    # Re-raise non-panic RuntimeErrors
                    raise e
        return cast(F, wrapper)
    return decorator

@contextmanager
def recovery_context(default: Optional[T] = None):
    """Context manager for panic recovery.
    
    Args:
        default: Default value to return if panic occurs
        
    Yields:
        Recovery context
    """
    try:
        yield
    except (RuntimeError, SystemExit, KeyboardInterrupt) as e:
        if "panic:" in str(e):
            request_logger.error(
                f"Recovered from panic in context: {e}",
                extra={
                    "panic_value": str(e).replace("panic: ", ""),
                    "traceback": traceback.format_exc()
                }
            )
            return default
        else:
            raise e

def must(condition: bool, message: str = "") -> None:
    """Assert-like function that panics if condition is false.
    
    Args:
        condition: Condition to check
        message: Panic message if condition fails
        
    Raises:
        RuntimeError: If condition is false
    """
    if not condition:
        panic(message or "assertion failed")

def must_not_none(value: Optional[T], message: str = "") -> T:
    """Panic if value is None, otherwise return value.
    
    Args:
        value: Value to check
        message: Panic message if value is None
        
    Returns:
        The non-None value
        
    Raises:
        RuntimeError: If value is None
    """
    if value is None:
        panic(message or "unexpected None value")
    return value