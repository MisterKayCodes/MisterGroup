# Made by Mister 💛
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.keyboards.sessions_menu import get_session_menu_inline
from bot.states.app_states import SessionStates
from data.repositories.session_repo import SessionRepository
from services.telegram.client_manager import TelegramService

router = Router()

@router.message(F.text == "👤 Sessions")
@router.callback_query(F.data == "sessions_main")
async def cmd_sessions(event: Message | CallbackQuery, session_repo: SessionRepository):
    """The 'Mouth' shows the sessions menu."""
    if isinstance(event, CallbackQuery):
        message = event.message
        is_callback = True
    else:
        message = event
        is_callback = False
        
    sessions = session_repo.get_all_sessions()
    text = (
        f"<b>👤 Sessions Management</b>\n\n"
        f"Total accounts registered: <b>{len(sessions)}</b>\n\n"
        f"You can add new accounts, test existing ones, or manage all sessions simultaneously."
    )
    if is_callback:
        await message.edit_text(text, reply_markup=get_session_menu_inline())
    else:
        await message.answer(text, reply_markup=get_session_menu_inline())

@router.callback_query(F.data == "sessions_list")
async def callback_sessions_list(callback: CallbackQuery, session_repo: SessionRepository):
    """List all accounts from the Vault."""
    sessions = session_repo.get_all_sessions()
    if not sessions:
        await callback.answer("No sessions found.", show_alert=True)
        return
        
    text = "<b>📋 Registered Sessions:</b>\n\n"
    for name, data in sessions.items():
        status = "🟢" if data.get("status") == "active" else "🔴"
        conn = "✅" if data.get("is_connected") else "❌"
        text += f"{status} <b>{name}</b> (Conn: {conn})\n"
        
    await callback.message.edit_text(text, reply_markup=get_session_menu_inline())
    await callback.answer()

@router.callback_query(F.data == "sessions_test_all")
async def callback_test_all(callback: CallbackQuery, session_repo: SessionRepository, tg_service: TelegramService):
    """Asks the 'Eyes' to verify all connections."""
    sessions = session_repo.get_all_sessions()
    if not sessions:
        await callback.answer("❌ No sessions to test.", show_alert=True)
        return
        
    await callback.message.edit_text("🧪 <b>Bulk Testing In Progress...</b>")
    
    results = []
    for name in sessions.keys():
        res = await tg_service.test_session(name)
        is_connected = res.get("success", False)
        data = sessions[name]
        data["is_connected"] = is_connected
        session_repo.add_session(name, data)
        results.append(f"{'✅' if is_connected else '❌'} <b>{name}</b>")
        
    await callback.message.answer("🏁 <b>Test Results:</b>\n\n" + "\n".join(results), reply_markup=get_session_menu_inline())
    await callback.answer()

@router.callback_query(F.data == "sessions_toggle_all")
async def toggle_all(callback: CallbackQuery, session_repo: SessionRepository):
    """Pause or Resume all sessions in the Vault."""
    sessions = session_repo.get_all_sessions()
    if not sessions: return await callback.answer("No sessions.", show_alert=True)
    
    # Check current status of first session
    first_name = list(sessions.keys())[0]
    is_paused = sessions[first_name].get("status") == "paused"
    new_status = "active" if is_paused else "paused"
    
    for name, data in sessions.items():
        data["status"] = new_status
        session_repo.add_session(name, data)
        
    await callback.answer(f"✅ All sessions are now {new_status.upper()}")
    await callback_sessions_list(callback, session_repo)

@router.callback_query(F.data == "sessions_add")
async def sessions_add(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SessionStates.WAITING_FOR_NAME)
    await callback.message.answer("👤 Enter a unique <b>Name</b> for this session:")
    await callback.answer()

@router.message(SessionStates.WAITING_FOR_NAME)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(SessionStates.WAITING_FOR_SESSION_STRING)
    await message.answer("📦 Now paste the Telethon <b>String Session</b>:")

@router.message(SessionStates.WAITING_FOR_SESSION_STRING)
async def process_string(message: Message, state: FSMContext, session_repo: SessionRepository):
    data = await state.get_data()
    session_repo.add_session(data["name"], {
        "name": data["name"], "session_string": message.text.strip(),
        "status": "active", "is_connected": False, "created_at": datetime.now().isoformat()
    })
    await message.answer(f"✅ <b>{data['name']}</b> added!", reply_markup=get_session_menu_inline())
    await state.clear()

@router.callback_query(F.data == "sessions_import")
async def sessions_import(callback: CallbackQuery):
    """The 'Mouth' shows instructions for the 'Lungs' (Sessions)."""
    text = (
        "📂 <b>Bulk Import Sessions</b>\n\n"
        "To import multiple sessions at once, place your <code>.session</code> files "
        "or a <code>sessions.txt</code> (with names and strings) into the <code>/sessions</code> directory "
        "and click 'Refresh List'.\n\n"
        "<i>Feature enhancement coming soon!</i>"
    )
    await callback.message.edit_text(text, reply_markup=get_session_menu_inline())
    await callback.answer()


@router.callback_query(F.data.startswith("sessions_delete_"))
async def process_delete(callback: CallbackQuery, session_repo: SessionRepository):
    # This might be sessions_delete_confirm_{name}
    parts = callback.data.split("_")
    if len(parts) < 3: return
    
    if parts[2] == "confirm":
        name = parts[3]
        session_repo.remove_session(name)
        await callback.answer(f"🗑️ Session {name} deleted!")
        await callback_sessions_list(callback, session_repo)
    else:
        # User clicked delete on a specific session list (if we had one)
        pass
