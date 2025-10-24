from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import logging
from typing import Optional, Any, Dict

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings, logger, request_id as request_id_ctx
from app.logger import request_logger, get_request_id
from app.bot.handlers import router as bot_router
from app.bot.webhook import setup_webhook, remove_webhook

# Global variables to store bot instances
bot: Optional[Bot] = None
dp: Optional[Dispatcher] = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:  # noqa: ARG001
    """Lifespan manager for modern FastAPI startup/shutdown events.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        Control to the application
    """
    global bot, dp
    
    # Startup
    request_logger.info("Starting Telegram Bot Application...", extra={"request_id": "system"})
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    storage: MemoryStorage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(bot_router)
    
    # Setup webhook
    try:
        await setup_webhook(bot, settings)
        request_logger.info("Webhook setup completed successfully", extra={"request_id": "system"})
    except Exception as e:
        request_logger.error(f"Failed to setup webhook: {e}", extra={"request_id": "system"})
        raise
    
    yield
    
    # Shutdown
    request_logger.info("Shutting down Telegram Bot Application...", extra={"request_id": "system"})
    try:
        await remove_webhook(bot, settings)
        request_logger.info("Webhook removed successfully", extra={"request_id": "system"})
    except Exception as e:
        request_logger.error(f"Error during webhook removal: {e}", extra={"request_id": "system"})
    
    if bot:
        await bot.session.close()
    request_logger.info("Bot session closed", extra={"request_id": "system"})

# Create FastAPI app with lifespan
app: FastAPI = FastAPI(
    title="Telegram Bot API",
    description="A modern Telegram bot built with FastAPI and Aiogram",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware for request logging and ID handling
@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Any) -> Any:
    """Middleware to handle request ID and logging.
    
    Args:
        request: Incoming request
        call_next: Next middleware callable
        
    Returns:
        HTTP response
    """
    # Generate or get request ID
    request_id: str = await get_request_id(request)
    
    # Set request ID in context
    token = request_id_ctx.set(request_id)
    
    start_time: float = time.time()
    
    # Log incoming request with request ID
    request_logger.info(
        f"Incoming request: {request.method} {request.url}",
        extra={"request_id": request_id}
    )
    
    try:
        response = await call_next(request)
        
        # Calculate processing time
        process_time: float = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response with request ID
        request_logger.info(
            f"Request completed: {request.method} {request.url} "
            f"Status: {response.status_code} Duration: {process_time:.3f}s",
            extra={"request_id": request_id}
        )
        
        return response
        
    except Exception as exc:
        request_logger.error(
            f"Request failed: {request.method} {request.url} - {exc}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise
    finally:
        # Clean up context variable
        request_id_ctx.reset(token)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler.
    
    Args:
        request: Request that caused the exception
        exc: Exception that was raised
        
    Returns:
        JSON response with error details
    """
    current_request_id: str = request_id_ctx.get()
    request_logger.error(
        f"Global exception handler: {exc}",
        extra={"request_id": current_request_id},
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": current_request_id
        },
        headers={"X-Request-ID": current_request_id}
    )

@app.get("/")
async def root(request_id: str = Depends(get_request_id)) -> Dict[str, Any]:
    """Root endpoint.
    
    Args:
        request_id: Request ID from dependency
        
    Returns:
        Welcome message and status
    """
    request_logger.info("Root endpoint accessed", extra={"request_id": request_id})
    return {
        "message": "Telegram Bot is running!",
        "status": "active",
        "version": "1.0.0",
        "request_id": request_id
    }

@app.get("/health")
async def health_check(request_id: str = Depends(get_request_id)) -> Dict[str, Any]:
    """Comprehensive health check endpoint.
    
    Args:
        request_id: Request ID from dependency
        
    Returns:
        Health status information
    """
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": time.time(),
        "request_id": request_id,
        "services": {
            "api": "operational",
            "bot": "operational" if bot else "down",
            "webhook": "configured"
        }
    }
    request_logger.debug("Health check performed", extra={"request_id": request_id})
    return health_status

@app.get("/info")
async def bot_info(request_id: str = Depends(get_request_id)) -> Dict[str, Any]:
    """Get bot information.
    
    Args:
        request_id: Request ID from dependency
        
    Returns:
        Bot information
        
    Raises:
        HTTPException: If bot is not initialized or error occurs
    """
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        bot_user = await bot.get_me()
        webhook_info = await bot.get_webhook_info()
        
        request_logger.info("Bot info retrieved", extra={"request_id": request_id})
        
        return {
            "bot_username": bot_user.username,
            "bot_id": bot_user.id,
            "webhook_url": webhook_info.url,
            "webhook_pending_updates": webhook_info.pending_update_count,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "request_id": request_id
        }
    except Exception as e:
        request_logger.error(
            f"Error getting bot info: {e}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Error retrieving bot information",
            headers={"X-Request-ID": request_id}
        )

# Webhook endpoint with request ID
@app.post(settings.WEBHOOK_PATH)
async def bot_webhook(
    update: Dict[str, Any],
    request: Request,  # noqa: ARG001
    request_id: str = Depends(get_request_id),
) -> Dict[str, Any]:
    """Main webhook endpoint for Telegram updates.
    
    Args:
        update: Telegram update data
        request: FastAPI request object
        request_id: Request ID from dependency
        
    Returns:
        Processing status
        
    Raises:
        HTTPException: If service is unavailable or error occurs
    """
    if not bot or not dp:
        request_logger.error("Bot or dispatcher not initialized", extra={"request_id": request_id})
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    try:
        telegram_update = types.Update(**update)
        
        # Log incoming update with request ID
        update_type: str = "unknown"
        user_id: Optional[int] = None
        
        if telegram_update.message:
            update_type = "message"
            user_id = telegram_update.message.from_user.id
        elif telegram_update.callback_query:
            update_type = "callback_query"
            user_id = telegram_update.callback_query.from_user.id
        
        request_logger.info(
            f"Processing {update_type} update from user: {user_id}",
            extra={"request_id": request_id, "user_id": user_id, "update_type": update_type}
        )
        
        # Set request ID in context for bot handlers
        token = request_id_ctx.set(request_id)
        
        await dp.feed_update(bot=bot, update=telegram_update)
        
        # Reset context
        request_id_ctx.reset(token)
        
        request_logger.debug(
            f"Update processed successfully",
            extra={"request_id": request_id, "user_id": user_id}
        )
        
        return {
            "status": "ok",
            "request_id": request_id,
            "update_type": update_type
        }
        
    except Exception as e:
        request_logger.error(
            f"Error processing webhook update: {e}",
            extra={"request_id": request_id},
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Error processing update",
            headers={"X-Request-ID": request_id}
        )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT,
        reload=True,
        log_config=None,  # Use our custom logging
        access_log=False  # We handle access logging in middleware
    )