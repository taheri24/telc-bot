from aiogram import Bot
from app.config import Settings

async def setup_webhook(bot: Bot, settings: Settings):
    webhook_url = f"{settings.WEBHOOK_URL}{settings.WEBHOOK_PATH}"
    
    # Set webhook
    await bot.set_webhook(
        url=webhook_url,
        drop_pending_updates=True
    )
    
    print(f"Webhook set to: {webhook_url}")
