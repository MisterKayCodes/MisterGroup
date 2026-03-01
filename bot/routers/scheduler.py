# Made by Mister 💛
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import get_main_menu_keyboard
from data.repositories.config_repo import ConfigRepository
from services.coordinator.scheduler_service import BackgroundScheduler

router = Router()

@router.message(F.text == "⏰ Schedule")
@router.callback_query(F.data == "sch_main")
@router.callback_query(F.data == "sch_refresh")
async def cmd_schedule(event: Message | CallbackQuery, config_repo: ConfigRepository, scheduler: BackgroundScheduler):
    """The 'Mouth' shows the scheduler status from the Brain."""
    if isinstance(event, CallbackQuery):
        message = event.message
        is_callback = True
    else:
        message = event
        is_callback = False
        
    is_running = scheduler.running
    conv_data = config_repo.get_conversation()
    
    text = (
        "<b>⏰ Scheduler Control</b>\n\n"
        f"Status: <b>{'🟢 RUNNING' if is_running else '⚪ STOPPED'}</b>\n"
    )
    
    if conv_data and conv_data.get("schedule"):
        schedule = conv_data["schedule"]
        text += f"Total Periods: <b>{len(schedule)}</b>\n\n"
        for i, p in enumerate(schedule, 1):
            status = "✅" if p.get("enabled", True) else "❌"
            text += f"{i}. {status} <b>{p.get('time')}</b> - {p.get('label')} ({p.get('repeat')})\n"
    else:
        text += "⚠️ No schedule found in the Vault."
        
    text += "\nUse the buttons below to start or stop the automated scheduler."
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    if is_running:
        builder.row(InlineKeyboardButton(text="⏹️ Stop Scheduler", callback_data="sch_stop"))
    else:
        builder.row(InlineKeyboardButton(text="▶️ Start Scheduler", callback_data="sch_start"))
        
    builder.row(InlineKeyboardButton(text="🛋️ Lazy Setup (Daily 4x)", callback_data="sch_lazy_setup"))
    builder.row(InlineKeyboardButton(text="🗑️ Clear Schedule", callback_data="sch_clear"))
    builder.row(InlineKeyboardButton(text="🔄 Refresh", callback_data="sch_refresh"))
    builder.row(InlineKeyboardButton(text="🔙 Back to Main", callback_data="main_menu"))
    
    if is_callback:
        await message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "sch_lazy_setup")
async def sch_lazy_setup(callback: CallbackQuery, config_repo: ConfigRepository, scheduler: BackgroundScheduler):
    """The 'Brain' creates a lazy-man's schedule in 1 second."""
    from core.models.period import ScheduledPeriod
    import dataclasses
    
    # Create 4 balanced periods (UTC)
    lazy_schedule = [
        {"time": "06:00", "label": "Morning Wakeup", "repeat": "daily", "enabled": True, "messages": []},
        {"time": "12:00", "label": "Midday Hype", "repeat": "daily", "enabled": True, "messages": []},
        {"time": "18:00", "label": "Evening Update", "repeat": "daily", "enabled": True, "messages": []},
        {"time": "00:00", "label": "Night Shift", "repeat": "daily", "enabled": True, "messages": []}
    ]
    
    conv_data = config_repo.get_conversation() or {"name": "Default Conversation", "mode": "scheduled", "messages": []}
    conv_data["schedule"] = lazy_schedule
    config_repo.set_conversation(conv_data)
    
    await callback.answer("🛋️ Lazy setup complete! 4 daily periods added.")
    await cmd_schedule(callback, config_repo, scheduler) # scheduler instance should be in context

@router.callback_query(F.data == "sch_clear")
async def sch_clear(callback: CallbackQuery, config_repo: ConfigRepository, scheduler: BackgroundScheduler):
    conv_data = config_repo.get_conversation()
    if conv_data:
        conv_data["schedule"] = []
        config_repo.set_conversation(conv_data)
    await callback.answer("🗑️ Schedule cleared.")
    await cmd_schedule(callback, config_repo, scheduler)

@router.callback_query(F.data == "sch_start")
async def sch_start(callback: CallbackQuery, scheduler: BackgroundScheduler, config_repo: ConfigRepository):
    """The 'Mouth' triggers the rhythmic 'Nervous System' (Scheduler)."""
    await scheduler.start()
    config_repo.update_config({"scheduler_running": True})
    await callback.answer("✅ Automatic scheduler started!")
    await callback.message.edit_text("⏰ <b>Scheduler is now ACTIVE.</b> I will monitor the Brain's logic every 30s.", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "sch_stop")
async def sch_stop(callback: CallbackQuery, scheduler: BackgroundScheduler, config_repo: ConfigRepository):
    """The 'Mouth' stops the rhythmic 'Nervous System' (Scheduler)."""
    await scheduler.stop()
    config_repo.update_config({"scheduler_running": False})
    await callback.answer("⏹️ Scheduler stopped!")
    await callback.message.edit_text("⏰ <b>Scheduler is now STOPPED.</b>", reply_markup=get_main_menu_keyboard())
