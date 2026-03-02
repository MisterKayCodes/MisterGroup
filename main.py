# Made by Mister 💛
import asyncio
import sys
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import get_config
from data.repositories.session_repo import SessionRepository
from data.repositories.config_repo import ConfigRepository
from data.repositories.media_repo import MediaRepository

from services.event_bus import EventBus
from services.telegram.client_manager import TelegramService
from services.telegram.message_sender import SenderService
from services.coordinator.simulation_coordinator import SimulationCoordinator
from services.coordinator.scheduler_service import BackgroundScheduler
from services.health_monitor import HealthMonitor

from bot.routers.base import router as base_router
from bot.routers.sessions import router as sessions_router
from bot.routers.settings import router as settings_router
from bot.routers.simulation import router as simulation_router
from bot.routers.status import router as status_router
from bot.routers.scheduler import router as scheduler_router
from bot.routers.media import router as media_router
from bot.routers.automation import router as automation_router
from bot.notification_handler import BotNotifier
from bot.middlewares.auth import AuthMiddleware
from services.coordinator.automation_worker import AutomationWorker

async def main():
    """The Skeleton: Connections and Nerves initialization."""
    # 0. Set up Logging (The Diary)
    import os
    import logging
    if not os.path.exists("logs"): os.makedirs("logs")
    
    # Intercept standard logging to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1
            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    logging.getLogger("aiogram").setLevel(logging.DEBUG)
    logger.add("logs/bot_{time}.log", rotation="10 MB", level="DEBUG")
    
    logger.info("Starting MisterGroup V2 (Living Organism Model)")
    
    # 1. Personality & Rules (Config)
    try:
        cfg = get_config()
    except Exception as e:
        logger.error(f"DNA Corruption: {e}")
        return

    # 2. Vault and Memory (Data Layer)
    session_repo = SessionRepository()
    config_repo = ConfigRepository()
    media_repo = MediaRepository()
    
    # 3. Connection & Nervous System (Services Layer)
    api_id = cfg.telethon.api_id
    api_hash = cfg.telethon.api_hash
    bot_token = cfg.bot.token
    admin_id = cfg.bot.admin_id
    
    event_bus = EventBus()
    telegram_service = TelegramService(session_repo, api_id, api_hash)
    if not telegram_service: return # Should not happen
    message_sender = SenderService()
    
    coordinator = SimulationCoordinator(telegram_service, message_sender, event_bus, media_repo)
    automation_worker = AutomationWorker(coordinator, config_repo)
    scheduler = BackgroundScheduler(coordinator, event_bus, config_repo, automation_worker)
    health_monitor = HealthMonitor()
    
    # 4. Interface (Bot Layer)
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    
    # Register Middleware
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    
    # Subscribing 'Voice Box' (Notifier)
    notifier = BotNotifier(bot, event_bus, admin_id)
    
    # Include 'Mouth' (Routers)
    dp.include_router(base_router)
    dp.include_router(sessions_router)
    dp.include_router(settings_router)
    dp.include_router(simulation_router)
    dp.include_router(status_router)
    dp.include_router(scheduler_router)
    dp.include_router(media_router)
    dp.include_router(automation_router)
    
    # Add repositories as dependencies for middleware (simplified here)
    dp["config_repo"] = config_repo
    dp["session_repo"] = session_repo
    dp["media_repo"] = media_repo
    dp["coordinator"] = coordinator
    dp["scheduler"] = scheduler
    dp["tg_service"] = telegram_service
    dp["health_monitor"] = health_monitor
    dp["automation_worker"] = automation_worker
    dp["bot"] = bot
    
    # 5. Birth & Execution
    logger.info("Organism is Alive! Waiting for input...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        # Auto-start scheduler if configured
        if config_repo.get_config().get("scheduler_running"):
            await scheduler.start()
            
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Organism died: {e}")
    finally:
        await telegram_service.disconnect_all()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Organism hibernating (Stopped by User)")
