# Made by Mister 💛

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Get main menu reply keyboard"""
    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(text="📊 Status"),
        KeyboardButton(text="🗂️ Upload JSON"),
        KeyboardButton(text="📄 Upload TXT")
    )
    builder.row(
        KeyboardButton(text="▶️ Start Sim"),
        KeyboardButton(text="⏹️ Stop Sim"),
        KeyboardButton(text="⏸️ Pause/Resume")
    )
    builder.row(
        KeyboardButton(text="👥 Sessions"),
        KeyboardButton(text="⏰ Schedule"),
        KeyboardButton(text="⚙️ Settings")
    )
    builder.row(
        KeyboardButton(text="🎬 Media Setup"),
        KeyboardButton(text="📋 Help"),
        KeyboardButton(text="📄 Logs")
    )
    
    return builder.as_markup(resize_keyboard=True)


def get_sessions_keyboard() -> InlineKeyboardMarkup:
    """Get sessions management inline keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📋 List Sessions", callback_data="sessions_list"),
        InlineKeyboardButton(text="➕ Add Session", callback_data="sessions_add")
    )
    builder.row(
        InlineKeyboardButton(text="📦 Import ZIP", callback_data="sessions_import"),
        InlineKeyboardButton(text="🧪 Test Session", callback_data="sessions_test")
    )
    builder.row(
        InlineKeyboardButton(text="❌ Remove Session", callback_data="sessions_remove")
    )
    builder.row(
        InlineKeyboardButton(text="⏸️ Pause All", callback_data="sessions_pause_all"),
        InlineKeyboardButton(text="▶️ Resume All", callback_data="sessions_resume_all")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_schedule_keyboard() -> InlineKeyboardMarkup:
    """Get schedule management inline keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📊 Schedule Status", callback_data="schedule_status"),
        InlineKeyboardButton(text="▶️ Start Scheduler", callback_data="schedule_start")
    )
    builder.row(
        InlineKeyboardButton(text="⏹️ Stop Scheduler", callback_data="schedule_stop"),
        InlineKeyboardButton(text="▶️ Run Period", callback_data="schedule_run_period")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Get settings inline keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🎯 Set Target Group", callback_data="settings_set_group"),
        InlineKeyboardButton(text="⏱️ Typing Speed", callback_data="settings_typing_speed")
    )
    builder.row(
        InlineKeyboardButton(text="🌐 Join Group", callback_data="settings_join_group"),
        InlineKeyboardButton(text="📊 Group Status", callback_data="settings_group_status")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_typing_speed_keyboard() -> InlineKeyboardMarkup:
    """Get typing speed selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🐇 Fast (3-9s)", callback_data="speed_fast"),
        InlineKeyboardButton(text="🐢 Normal (10-26s)", callback_data="speed_normal"),
        InlineKeyboardButton(text="🐌 Slow (27-50s)", callback_data="speed_slow")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="settings_menu")
    )
    
    return builder.as_markup()


def get_simulation_control_keyboard(is_running: bool, is_paused: bool) -> InlineKeyboardMarkup:
    """Get simulation control keyboard based on state"""
    builder = InlineKeyboardBuilder()
    
    if not is_running:
        builder.row(
            InlineKeyboardButton(text="▶️ Start Simulation", callback_data="sim_start")
        )
    else:
        if is_paused:
            builder.row(
                InlineKeyboardButton(text="▶️ Resume", callback_data="sim_resume"),
                InlineKeyboardButton(text="⏹️ Stop", callback_data="sim_stop")
            )
        else:
            builder.row(
                InlineKeyboardButton(text="⏸️ Pause", callback_data="sim_pause"),
                InlineKeyboardButton(text="⏹️ Stop", callback_data="sim_stop")
            )
    
    builder.row(
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_text_to_json_keyboard() -> InlineKeyboardMarkup:
    """Get text-to-JSON conversion keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📝 Convert Text to JSON", callback_data="convert_text")
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ How to Use", callback_data="convert_help")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")
    )
    
    return builder.as_markup()


def get_delay_range_keyboard() -> InlineKeyboardMarkup:
    """Get delay range selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="🐇 Fast (3-9s)", callback_data="delay_fast"),
        InlineKeyboardButton(text="🐢 Normal (10-26s)", callback_data="delay_normal"),
        InlineKeyboardButton(text="🐌 Slow (27-50s)", callback_data="delay_slow")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Cancel", callback_data="convert_cancel")
    )
    
    return builder.as_markup()


def get_schedule_type_keyboard() -> InlineKeyboardMarkup:
    """Get schedule type selection keyboard (instant vs scheduled)"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="⚡ Instant (Run Now)", callback_data="schedule_instant"),
        InlineKeyboardButton(text="🕐 Scheduled (Set Time)", callback_data="schedule_custom")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Cancel", callback_data="convert_cancel")
    )
    
    return builder.as_markup()


def get_repeat_pattern_keyboard() -> InlineKeyboardMarkup:
    """Get repeat pattern selection keyboard"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="📅 Daily", callback_data="repeat_daily"),
        InlineKeyboardButton(text="💼 Weekdays", callback_data="repeat_weekdays")
    )
    builder.row(
        InlineKeyboardButton(text="🏖️ Weekends", callback_data="repeat_weekends"),
        InlineKeyboardButton(text="1️⃣ Once Only", callback_data="repeat_once")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Back", callback_data="schedule_custom")
    )
    
    return builder.as_markup()


def get_add_more_batches_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard to add more time slots or finish"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(text="➕ Add Another Time Slot", callback_data="add_more_batch"),
        InlineKeyboardButton(text="✅ Done - Save All", callback_data="save_batches")
    )
    builder.row(
        InlineKeyboardButton(text="🔙 Cancel", callback_data="convert_cancel")
    )
    
    return builder.as_markup()
