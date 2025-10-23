from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
import uvicorn

from app.config import settings
from app.bot.handlers import router as bot_router
from app.bot.webhook import setup_webhook

app = FastAPI(title="Telegram Bot Webhook")

# Initialize bot and dispatcher
bot = Bot(token=settings.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Include bot router
dp.include_router(bot_router)

@app.on_event("startup")
async def on_startup():
    await setup_webhook(bot, settings)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.session.close()

@app.get("/")
async def root():
    return {"message": "Telegram Bot is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Webhook endpoint
@app.post(settings.WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.WEBAPP_HOST,
        port=settings.WEBAPP_PORT,
        reload=True
    )
