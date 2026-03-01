# Made by Mister 💛
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states.app_states import AuthStates
from bot.keyboards.main_menu import get_main_menu_keyboard
from data.repositories.config_repo import ConfigRepository

router = Router()

REQUIRED_PIN = "5135"

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, config_repo: ConfigRepository):
    """Entry point for the 'Mouth'. Greets the user and asks for PIN."""
    if config_repo.is_user_authenticated(message.from_user.id):
        await state.clear() # Clear any stuck states
        return await show_welcome(message, config_repo)
    
    await state.set_state(AuthStates.WAITING_FOR_PIN)
    await message.answer("🔐 <b>MisterGroup V2 Security Guard</b>\n\nPlease enter your <b>4-digit PIN</b> for access:")

@router.message(AuthStates.WAITING_FOR_PIN)
async def process_pin(message: Message, state: FSMContext, config_repo: ConfigRepository):
    """Verifies the 'Key' (PIN)."""
    text = message.text.strip() if message.text else ""
    
    # 1. Defensive Check: Ignore common menu buttons that might be in the user's old keyboard
    if any(btn_text in text for btn_text in ["LAZY", "START", "HELP", "STATUS", "MEDIA", "SESSIONS"]):
         return await message.answer("🔐 <b>Authentication Required</b>\n\nYour session is locked. Please enter your <b>4-digit PIN</b> (5135) to continue:")

    # 2. Validation: Ensure it's 4 digits
    if not text.isdigit() or len(text) != 4:
        return await message.answer("⚠️ Please enter precisely <b>4 digits</b> (e.g., 1234).")

    # 3. Verification
    if text == REQUIRED_PIN:
        config_repo.set_user_authenticated(message.from_user.id, True)
        await state.clear()
        await message.answer("✅ <b>Access Granted!</b> Welcome back, Mister.")
        await show_welcome(message, config_repo)
    else:
        await message.answer("❌ <b>Wrong PIN.</b> Access Denied.")

async def show_welcome(message: Message, config_repo: ConfigRepository):
    """Shows the 'Mouth' home base."""
    conf = config_repo.get_config()
    # Auto-set the admin ID on first successful login if not set.
    if not conf.get("admin_id"):
        config_repo.update_config({"admin_id": message.from_user.id})
    
    welcome_text = (
        "👋 <b>Welcome to MisterGroup V2!</b>\n\n"
        "This bot helps you simulate realistic conversations in Telegram groups.\n\n"
        "🚀 <b>Core Features:</b>\n"
        "• Multiple account management\n"
        "• News-driven AI automation\n"
        "• Realistic typing speed and delays\n"
        "• Media tag support from source channels\n\n"
        "Use the keyboard below to navigate!"
    )
    
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "main_menu")
async def callback_home(callback: CallbackQuery, state: FSMContext, config_repo: ConfigRepository):
    """Return to the 'Mouth' home base."""
    if not config_repo.is_user_authenticated(callback.from_user.id):
        return await cmd_start(callback.message, state, config_repo)
        
    await callback.message.edit_text("🏠 Main Menu", reply_markup=get_main_menu_keyboard()) # Using edit_text for cleaner UI
    await callback.answer()

@router.message(F.text == "❓ Help")
@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext, config_repo: ConfigRepository):
    """The 'Mouth' explains itself."""
    if not config_repo.is_user_authenticated(message.from_user.id):
        return await cmd_start(message, state, config_repo)
        
    help_text = (
        "<b>📖 Quick Guide:</b>\n\n"
        "1. <b>Sessions:</b> Add the bot accounts you want to use.\n"
        "2. <b>Media:</b> Link a channel to use media tags like [BALANCE].\n"
        "3. <b>Settings:</b> Set your target group ID and typing speed.\n"
        "4. <b>Run Now:</b> Upload a JSON or text to start simulation.\n"
        "5. <b>Schedule:</b> View or start the automated scheduler.\n\n"
        "<i>Tip: Use 🚀 Run Now for immediate simulations.</i>"
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())
