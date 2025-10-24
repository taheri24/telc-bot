from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import time
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings, logger
from app.bot.handlers import router as bot_router
from app.bot.webhook import setup_webhook, remove_webhook

# Global variables to store bot instances
bot = None
dp = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for modern FastAPI startup/shutdown events"""
    global bot, dp
    
    # Startup
    logger.info("Starting Telegram Bot Application...")
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(bot_router)
    
    # Setup webhook
    try:
        await setup_webhook(bot, settings)
        logger.info("Webhook setup completed successfully")
    except Exception as e:
        logger.error(f"Failed to setup webhook: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Telegram Bot Application...")
    try:
        await remove_webhook(bot, settings)
        logger.info("Webhook removed successfully")
    except Exception as e:
        logger.error(f"Error during webhook removal: {e}")
    
    await bot.session.close()
    logger.info("Bot session closed")

# Create FastAPI app with lifespan
app = FastAPI(
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

# Custom middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    logger.info(
        f"Request completed: {request.method} {request.url} "
        f"Status: {response.status_code} Duration: {process_time:.3f}s"
    )
    
    return response

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Telegram Bot is running!",
        "status": "active",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "api": "operational",
            "bot": "operational" if bot else "down",
            "webhook": "configured"
        }
    }
    logger.debug("Health check performed")
    return health_status

@app.get("/info")
async def bot_info():
    """Get bot information"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    
    try:
        bot_user = await bot.get_me()
        webhook_info = await bot.get_webhook_info()
        
        return {
            "bot_username": bot_user.username,
            "bot_id": bot_user.id,
            "webhook_url": webhook_info.url,
            "webhook_pending_updates": webhook_info.pending_update_count,
            "has_custom_certificate": webhook_info.has_custom_certificate
        }
    except Exception as e:
        logger.error(f"Error getting bot info: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving bot information")

# Webhook endpoint
@app.post(settings.WEBHOOK_PATH)
async def bot_webhook(update: dict, request: Request):
    """Main webhook endpoint for Telegram updates"""
    if not bot or not dp:
        logger.error("Bot or dispatcher not initialized")
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    try:
        telegram_update = types.Update(**update)
        
        # Log incoming update
        update_type = "unknown"
        if telegram_update.message:
            update_type = "message"
        elif telegram_update.callback_query:
            update_type = "callback_query"
        
        logger.info(f"Processing {update_type} update from user: {getattr(telegram_update.message or telegram_update.callback_query, 'from_user', None)}")
        
        await dp.feed_update(bot=bot, update=telegram_update)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing update")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT,
        reload=True,
        log_config=None,  # Use our custom logging
        access_log=False  # We handle access logging in middleware
    )