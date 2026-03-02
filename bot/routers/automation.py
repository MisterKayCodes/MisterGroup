# Made by Mister 💛
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.repositories.config_repo import ConfigRepository
from loguru import logger
from services.coordinator.automation_worker import AutomationWorker
from services.coordinator.scheduler_service import BackgroundScheduler

router = Router()

@router.message(F.text == "🚀 LAZY START")
async def cmd_automation(message: Message, config_repo: ConfigRepository):
    """The 'Mouth' shows the Automation Dashboard."""
    print(f"DEBUG: cmd_automation hit by {message.from_user.id}")
    logger.debug(f"Handling LAZY START message from {message.from_user.id}")
    conf = config_repo.get_config()
    enabled = conf.get("automation_enabled", False)
    interval = conf.get("automation_interval_hours", 4)
    
    status = "🟢 ACTIVE" if enabled else "⚪ DISABLED"
    text = (
        "<b>🚀 Lazy Start: News Automation</b>\n\n"
        f"Status: <b>{status}</b>\n"
        f"Check Interval: <b>Every {interval} Hours</b>\n\n"
        "When active, I fetch news, generate real 80-msg conversations, and run them automatically."
    )
    
    builder = InlineKeyboardBuilder()
    if enabled:
        builder.row(InlineKeyboardButton(text="🛑 Deactivate Automation", callback_data="auto_stop"))
    else:
        builder.row(InlineKeyboardButton(text="🚀 Activate AI Automation", callback_data="auto_start"))
        
    # Interval Settings
    builder.row(
        InlineKeyboardButton(text="⏱️ 5 min (testing)", callback_data="auto_int_5"),
        InlineKeyboardButton(text="⏱️ 2h", callback_data="auto_int_2"),
        InlineKeyboardButton(text="⏱️ 4h", callback_data="auto_int_4"),
        InlineKeyboardButton(text="⏱️ 8h", callback_data="auto_int_8"),
        InlineKeyboardButton(text="⏱️ 12h", callback_data="auto_int_12")
    )
    
    # Manual Trigger for testing
    builder.row(InlineKeyboardButton(text="⚡ Run Test Cycle Now", callback_data="auto_test_run"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="main_menu"))
    
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("auto_int_"))
async def set_interval(callback: CallbackQuery, config_repo: ConfigRepository):
    raw_value = int(callback.data.split("_")[-1])
    if raw_value == 5:
        # 5 minutes expressed in hours
        interval = 5 / 60
        config_repo.update_config({"automation_interval_hours": interval})
        await callback.answer("⏱️ Interval set to 5 min (testing)!")
    else:
        interval = raw_value
        config_repo.update_config({"automation_interval_hours": interval})
        await callback.answer(f"⏱️ Interval set to {interval} hours!")
    await cmd_automation(callback.message, config_repo)

@router.callback_query(F.data == "auto_start")
async def auto_start(callback: CallbackQuery, config_repo: ConfigRepository, scheduler: BackgroundScheduler):
    conf = config_repo.get_config()
    if not conf.get("target_group"):
        await callback.answer("❌ Cannot start: Target Group ID is not set in Settings!", show_alert=True)
        return

    config_repo.update_config({"automation_enabled": True, "scheduler_running": True})
    await scheduler.start()
    await callback.answer("🚀 Automation & Scheduler Activated!")
    await cmd_automation(callback.message, config_repo)

@router.callback_query(F.data == "auto_stop")
async def auto_stop(callback: CallbackQuery, config_repo: ConfigRepository):
    config_repo.update_config({"automation_enabled": False})
    await callback.answer("🛑 Automation Disabled.")
    await cmd_automation(callback.message, config_repo)

@router.callback_query(F.data == "auto_test_run")
async def auto_test_run(callback: CallbackQuery, automation_worker: AutomationWorker):
    success = await automation_worker.run_cycle()
    if success:
        await callback.answer("✅ Test Cycle Started!", show_alert=True)
    else:
        await callback.answer("❌ Failed: Check news or output group settings.", show_alert=True)
