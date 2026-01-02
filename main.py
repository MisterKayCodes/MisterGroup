# Made by Mister 💛

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from loguru import logger

from config import get_config, ConfigError
from src.utils.logger import setup_logger
from src.utils.database import Database
from src.database.media_tables import MediaDatabase
from src.services.session_manager import SessionManager
from src.services.simulation_engine import SimulationEngine
from src.handlers.admin_commands import router as admin_router, set_dependencies as set_admin_deps
from src.handlers.callbacks import router as callback_router, set_dependencies as set_callback_deps
from src.handlers.text_conversion import router as text_conv_router, set_db
from src.handlers.media_setup import router as media_router, set_media_dependencies


async def main():
    """Main function to start the bot"""
    try:
        cfg = get_config()
    except ConfigError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("Please create a .env file with your configuration.")
        print("See .env.example for template.\n")
        return
    
    setup_logger(cfg.log_level)
    
    logger.info("Starting Telegram Conversation Simulator Bot")
    logger.info("Made by Mister 💛")
    
    admin_id = cfg.bot.admin_id
    if admin_id is None:
        logger.warning("ADMIN_ID not set in environment. Bot will accept first user as admin.")
    else:
        logger.info(f"Admin ID set to: {admin_id}")
    
    if not cfg.telethon.is_configured:
        logger.warning("API_ID or API_HASH not set. Telethon features will be limited.")
        logger.warning("Get your API credentials from https://my.telegram.org")
    
    db = Database()
    logger.info("Database initialized")
    
    media_db = MediaDatabase()
    logger.info("Media database initialized")
    
    if admin_id is None:
        config_data = db.get_config()
        stored_admin_id = config_data.get("admin_id")
        if stored_admin_id is not None:
            admin_id = stored_admin_id
            logger.info(f"Loaded admin ID from database: {admin_id}")
    else:
        db.update_config({"admin_id": admin_id})
        logger.info(f"Admin ID set from environment: {admin_id}")
    
    if cfg.telethon.is_configured:
        session_manager = SessionManager(db, cfg.telethon.api_id, cfg.telethon.api_hash)
        logger.info("Session manager initialized")
    else:
        session_manager = None
        logger.warning("Session manager not initialized (missing API credentials)")
    
    simulation_engine = SimulationEngine(db, session_manager) if session_manager else None
    if simulation_engine:
        logger.info("Simulation engine initialized")
        simulation_engine.set_media_sender(media_db)
    
    bot = Bot(
        token=cfg.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    if simulation_engine:
        asyncio.create_task(simulation_engine.auto_resume_scheduler())
    
    set_admin_deps(db, session_manager, simulation_engine, admin_id)
    set_callback_deps(db, session_manager, simulation_engine, admin_id)
    set_db(db)
    set_media_dependencies(db, media_db, session_manager, admin_id)
    
    dp.include_router(admin_router)
    dp.include_router(callback_router)
    dp.include_router(text_conv_router)
    dp.include_router(media_router)
    logger.info("Command handlers registered")
    
    logger.info("Bot starting... Press Ctrl+C to stop")
    logger.info("="*50)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error running bot: {e}")
    finally:
        if session_manager:
            await session_manager.disconnect_all()
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
