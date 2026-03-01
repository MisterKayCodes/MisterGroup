# Made by Mister 💛
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.states.app_states import SettingsStates
from bot.keyboards.main_menu import get_main_menu_keyboard
from data.repositories.config_repo import ConfigRepository
from data.repositories.session_repo import SessionRepository
from services.coordinator.simulation_coordinator import SimulationCoordinator

router = Router()

@router.message(F.text == "⚙️ Settings")
@router.callback_query(F.data == "settings_main")
async def cmd_settings(event: Message | CallbackQuery, config_repo: ConfigRepository):
    """The 'Mouth' shows current settings from the Vault."""
    if isinstance(event, CallbackQuery):
        message = event.message
        is_callback = True
    else:
        message = event
        is_callback = False
        
    conf = config_repo.get_config()
    
    group = conf.get("target_group", "<i>Not set</i>")
    speed = conf.get("typing_speed", "normal").upper()
    
    text = (
        "<b>⚙️ Bot Settings</b>\n\n"
        f"🎯 <b>Target Group:</b> <code>{group}</code>\n"
        f"⚡ <b>Typing Speed:</b> {speed}\n\n"
        "To update these, click a button below."
    )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎯 Set Group ID", callback_data="settings_set_group"))
    builder.row(InlineKeyboardButton(text="⚡ Typing Speed", callback_data="settings_set_speed"))
    builder.row(InlineKeyboardButton(text="🤝 Join All to Group", callback_data="settings_join_group"))
    builder.row(InlineKeyboardButton(text="🔙 Back to Main", callback_data="main_menu"))
    
    if is_callback:
        await message.edit_text(text, reply_markup=builder.as_markup())
    else:
        await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "settings_set_speed")
async def start_set_speed(callback: CallbackQuery, state: FSMContext):
    """The 'Mouth' starts the typing speed selection."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🐢 SLOW", callback_data="speed_slow"))
    builder.row(InlineKeyboardButton(text="⚡ NORMAL", callback_data="speed_normal"))
    builder.row(InlineKeyboardButton(text="🚀 FAST", callback_data="speed_fast"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="settings_back"))
    
    await callback.message.edit_text("⚡ <b>Select Typing Speed:</b>\n\n- <b>SLOW:</b> 10-25 chars/s (More human-like)\n- <b>NORMAL:</b> 25-50 chars/s (Balanced)\n- <b>FAST:</b> 50-100 chars/s (Efficient)", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("speed_"))
async def process_speed_choice(callback: CallbackQuery, config_repo: ConfigRepository):
    """The 'Brain' saves the choice."""
    new_speed = callback.data.split("_")[1]
    config_repo.update_config({"typing_speed": new_speed})
    await callback.answer(f"✅ Typing speed set to {new_speed.upper()}")
    # Re-show settings menu by editing
    await cmd_settings(callback, config_repo)

@router.callback_query(F.data == "settings_back")
async def settings_back(callback: CallbackQuery, config_repo: ConfigRepository):
    await cmd_settings(callback, config_repo)
    await callback.answer()

@router.callback_query(F.data == "settings_set_group")
async def start_set_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsStates.WAITING_FOR_TARGET_GROUP)
    await callback.message.answer("🎯 Enter your <b>Target Group ID</b> (e.g., -1001234567890):")
    await callback.answer()

@router.message(SettingsStates.WAITING_FOR_TARGET_GROUP)
async def process_target_group(message: Message, state: FSMContext, config_repo: ConfigRepository):
    line = message.text.strip()
    try:
        group_id = int(line)
        config_repo.update_config({"target_group": group_id})
        await message.answer(f"✅ Target group updated to: <b>{group_id}</b>", reply_markup=get_main_menu_keyboard())
        await state.clear()
    except ValueError:
        await message.answer("❌ Invalid Group ID. Numbers Only.")

@router.callback_query(F.data == "settings_join_group")
async def start_join_group(callback: CallbackQuery, state: FSMContext):
    """Wait for the user's 'Mouth' to speak the invitation link."""
    await state.set_state(SettingsStates.WAITING_FOR_JOIN_LINK)
    await callback.message.answer("🤝 Send the <b>Group Link</b> or <b>Username</b> (e.g., @groupname) for all accounts to join:")
    await callback.answer()

@router.message(SettingsStates.WAITING_FOR_JOIN_LINK)
async def process_join_group(message: Message, state: FSMContext, coordinator: SimulationCoordinator, session_repo: SessionRepository):
    """Orchestrate the join process through the 'Spinal Cord' (Coordinator)."""
    link = message.text.strip()
    await message.answer("🧪 <b>Joining Group...</b>\nPlease wait while your accounts are being introduced to the group.")
    
    sessions = session_repo.get_all_sessions()
    names = list(sessions.keys())
    
    res = await coordinator.join_group(link, names)
    
    text = (
        f"🏁 <b>Join Process Finished</b>\n\n"
        f"✅ Success: <b>{len(res['success'])}</b>\n"
        f"❌ Failed: <b>{len(res['failed'])}</b>\n\n"
    )
    if res["failed"]:
        text += "<b>Errors:</b>\n" + "\n".join(res["failed"][:5])
        
    await message.answer(text, reply_markup=get_main_menu_keyboard())
    await state.clear()
