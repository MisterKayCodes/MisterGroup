# Made by Mister 💛
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from data.repositories.config_repo import ConfigRepository
from services.coordinator.automation_worker import AutomationWorker

router = Router()

@router.message(F.text == "🚀 LAZY START")
async def cmd_automation(message: Message, config_repo: ConfigRepository):
    """The 'Mouth' shows the Automation Dashboard."""
    conf = config_repo.get_config()
    enabled = conf.get("automation_enabled", False)
    
    status = "🟢 ACTIVE" if enabled else "⚪ DISABLED"
    text = (
        "<b>🚀 Lazy Start: News Automation</b>\n\n"
        f"Status: <b>{status}</b>\n"
        "Cycles: <b>Every 4 Hours</b>\n\n"
        "When active, I fetch news, generate real 80-msg conversations, and run them automatically."
    )
    
    builder = InlineKeyboardBuilder()
    if enabled:
        builder.row(InlineKeyboardButton(text="🛑 Deactivate Automation", callback_data="auto_stop"))
    else:
        builder.row(InlineKeyboardButton(text="🚀 Activate AI Automation", callback_data="auto_start"))
        
    # Manual Trigger for testing
    builder.row(InlineKeyboardButton(text="⚡ Run Test Cycle Now", callback_data="auto_test_run"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="main_menu"))
    
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "auto_start")
async def auto_start(callback: CallbackQuery, config_repo: ConfigRepository):
    config_repo.update_config({"automation_enabled": True})
    await callback.answer("🚀 Automation Activated!")
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
