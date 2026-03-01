# Made by Mister 💛
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_session_menu_inline() -> InlineKeyboardMarkup:
    """Inline 'Mouth' buttons for session management."""
    builder = InlineKeyboardBuilder()
    
    # List and Add on first row
    builder.row(
        InlineKeyboardButton(text="📋 List All", callback_data="sessions_list"),
        InlineKeyboardButton(text="➕ Add New", callback_data="sessions_add")
    )
    
    # Test and Bulk Import on second row
    builder.row(
        InlineKeyboardButton(text="🧪 Test All", callback_data="sessions_test_all"),
        InlineKeyboardButton(text="📂 Bulk Import", callback_data="sessions_import")
    )
    
    # Pause/Resume All on third row
    builder.row(
        InlineKeyboardButton(text="⏯️ Pause/Resume All", callback_data="sessions_toggle_all")
    )
    
    # Back to Main on fourth row
    builder.row(
        InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="main_menu")
    )
    
    return builder.as_markup()

def get_confirm_delete_keyboard(session_name: str) -> InlineKeyboardMarkup:
    """Inline confirmation for risky 'Mouth' actions."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⚠️ Yes, Delete", callback_data=f"sessions_delete_confirm_{session_name}"),
        InlineKeyboardButton(text="❌ Cancel", callback_data="sessions_list")
    )
    return builder.as_markup()
