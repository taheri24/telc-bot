from app.config import Settings, logger
from aiogram import Bot

async def setup_webhook(bot:Bot, settings:Settings):
    """Setup webhook with comprehensive logging"""
    webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
    
    logger.info(f"Setting up webhook to: {webhook_url}")
    
    try:
        # Get current webhook info
        current_webhook = await bot.get_webhook_info()
        logger.info(f"Current webhook URL: {current_webhook.url}")
        logger.info(f"Pending updates: {current_webhook.pending_update_count}")
        
        # Set new webhook
        result = await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
        if result:
            logger.info("Webhook set successfully")
            
            # Verify webhook setup
            new_webhook = await bot.get_webhook_info()
            logger.info(f"New webhook URL: {new_webhook.url}")
            logger.info(f"Pending updates after reset: {new_webhook.pending_update_count}")
        else:
            logger.error("Failed to set webhook")
            
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        raise

async def remove_webhook(bot:Bot, settings:Settings):
    """Remove webhook with logging"""
    logger.info("Removing webhook...")
    
    try:
        result = await bot.delete_webhook(drop_pending_updates=False)
        if result:
            logger.info("Webhook removed successfully")
        else:
            logger.warning("Failed to remove webhook")
    except Exception as e:
        logger.error(f"Error removing webhook: {e}")
        raise