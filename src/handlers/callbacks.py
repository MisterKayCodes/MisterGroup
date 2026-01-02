# Made by Mister 💛

from typing import Optional
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode
from loguru import logger

from src.utils.keyboards import (
    get_main_menu_keyboard, get_sessions_keyboard, get_schedule_keyboard,
    get_settings_keyboard, get_typing_speed_keyboard, get_simulation_control_keyboard,
    get_text_to_json_keyboard
)
from src.utils.database import Database
from src.services.session_manager import SessionManager
from src.services.simulation_engine import SimulationEngine

router = Router()

# Global instances (will be set from main handler)
db: Optional[Database] = None
session_manager: Optional[SessionManager] = None
simulation_engine: Optional[SimulationEngine] = None
admin_id: Optional[int] = None


def set_dependencies(database: Database,
                     sess_manager: Optional[SessionManager] = None,
                     sim_engine: Optional[SimulationEngine] = None,
                     admin_user_id: Optional[int] = None):
    """Set global dependencies for callback handlers"""
    global db, session_manager, simulation_engine, admin_id
    db = database
    session_manager = sess_manager
    simulation_engine = sim_engine
    admin_id = admin_user_id


async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    if not db:
        return False
    config = db.get_config()
    db_admin_id = config.get("admin_id")
    return user_id == db_admin_id if db_admin_id else False


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery):
    """Show main menu"""
    await callback.answer()
    
    welcome_text = """
🤖 <b>Telegram Conversation Simulator Bot</b>
Made by Mister 💛

Use the buttons below to navigate:
"""
    
    await callback.message.edit_text(
        welcome_text,
        parse_mode=ParseMode.HTML,
        reply_markup=None
    )
    
    await callback.message.answer(
        "Select an option from the menu below:",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "sessions_menu")
async def callback_sessions_menu(callback: CallbackQuery):
    """Show sessions menu"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.edit_text(
        "👥 <b>Session Management</b>\n\nSelect an option:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_sessions_keyboard()
    )


@router.callback_query(F.data == "sessions_list")
async def callback_sessions_list(callback: CallbackQuery):
    """List all sessions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    if not session_manager:
        await callback.message.answer("❌ Session manager not available.")
        return
    
    sessions = session_manager.list_sessions()
    
    if not sessions:
        await callback.message.edit_text(
            "📋 No sessions registered yet.\n\nUse the buttons below to add sessions:",
            reply_markup=get_sessions_keyboard()
        )
        return
    
    session_list = "📋 <b>Registered Sessions:</b>\n\n"
    for session in sessions:
        status_emoji = "🟢" if session.get("status") == "active" else "🟡"
        session_list += f"{status_emoji} <b>{session.get('name')}</b>\n"
        session_list += f"  • Status: {session.get('status')}\n"
        if session.get('username'):
            session_list += f"  • Username: @{session.get('username')}\n"
        session_list += f"  • Connected: {'Yes' if session.get('is_connected') else 'No'}\n\n"
    
    await callback.message.edit_text(
        session_list,
        parse_mode=ParseMode.HTML,
        reply_markup=get_sessions_keyboard()
    )


@router.callback_query(F.data.in_(["sessions_pause_all", "sessions_resume_all"]))
async def callback_sessions_pause_resume_all(callback: CallbackQuery):
    """Pause or resume all sessions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    if not session_manager:
        await callback.message.answer("❌ Session manager not available.")
        return
    
    action = "resume" if "resume" in callback.data else "pause"
    
    sessions = db.get_all_sessions()
    if not sessions:
        await callback.message.answer("❌ No sessions to update.")
        return
    
    count = 0
    for name, data in sessions.items():
        new_status = "active" if action == "resume" else "paused"
        data["status"] = new_status
        db.add_session(name, data)
        count += 1
    
    emoji = "▶️" if action == "resume" else "⏸️"
    await callback.message.answer(
        f"{emoji} All sessions {action}d ({count} sessions updated).",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "schedule_menu")
async def callback_schedule_menu(callback: CallbackQuery):
    """Show schedule menu"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.edit_text(
        "⏰ <b>Schedule Management</b>\n\nSelect an option:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_schedule_keyboard()
    )


@router.callback_query(F.data == "schedule_status")
async def callback_schedule_status(callback: CallbackQuery):
    """Show schedule status with countdown timers"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await callback.message.answer("❌ Simulation engine not available.")
        return
    
    status = simulation_engine.get_schedule_status()
    
    if not status["has_schedule"]:
        await callback.message.edit_text(
            "❌ No scheduled conversation loaded.\n\n"
            "Upload a JSON file with 'schedule' array first.",
            reply_markup=get_schedule_keyboard()
        )
        return
    
    status_text = "📊 <b>Schedule Status</b>\n\n"
    status_text += f"Scheduler: {'🟢 Running' if status['scheduler_running'] else '⚪ Stopped'}\n"
    
    # Show next upcoming period with countdown
    next_period = status.get("next_period")
    if next_period and status["scheduler_running"]:
        status_text += f"Next: ⏱ <b>{next_period['label']}</b> in {next_period['countdown']}\n"
    
    status_text += "\n<b>Scheduled Periods:</b>\n\n"
    
    for p in status["periods"]:
        status_emoji = "✅" if p["enabled"] else "❌"
        
        # Status with countdown
        if p["executed_today"]:
            time_status = "✓ Done"
        elif p.get("countdown"):
            if p["countdown"] == "Passed":
                time_status = "⏰ Passed"
            else:
                time_status = f"⏱ in {p['countdown']}"
        else:
            time_status = "○ Pending"
        
        status_text += f"{status_emoji} <b>{p['label']}</b> — {p['time']} UTC\n"
        status_text += f"   {time_status} | {p['message_count']} msgs | {p['repeat']}\n\n"
    
    # Show queued items if any
    queued_items = status.get("queued_items", 0)
    if queued_items > 0:
        status_text += f"📋 Queue: {queued_items} conversation(s) waiting\n"
    
    status_text += "\n<i>Times are in UTC timezone</i>"
    
    await callback.message.edit_text(
        status_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_schedule_keyboard()
    )


@router.callback_query(F.data.in_(["schedule_start", "schedule_stop"]))
async def callback_schedule_start_stop(callback: CallbackQuery):
    """Start or stop scheduler"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await callback.message.answer("❌ Simulation engine not available.")
        return
    
    if "start" in callback.data:
        async def admin_notify(msg: str):
            try:
                await callback.message.answer(msg, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
        
        result = await simulation_engine.start_scheduler(admin_callback=admin_notify)
    else:
        result = simulation_engine.stop_scheduler()
    
    if result["success"]:
        await callback.message.answer(
            f"✅ {result['message']}",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.answer(f"❌ {result['message']}")


@router.callback_query(F.data == "settings_menu")
async def callback_settings_menu(callback: CallbackQuery):
    """Show settings menu"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    config = db.get_config()
    
    settings_text = f"""
⚙️ <b>Settings</b>

<b>Current Configuration:</b>
• Typing Speed: {config.get('typing_speed', 'normal')}
• Target Group: {config.get('target_group', 'Not set')}

Select an option:
"""
    
    await callback.message.edit_text(
        settings_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard()
    )


@router.callback_query(F.data == "settings_typing_speed")
async def callback_typing_speed(callback: CallbackQuery):
    """Show typing speed options"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.edit_text(
        "⏱️ <b>Select Typing Speed</b>\n\n"
        "This controls the delay range for text-to-JSON conversion:\n\n"
        "🐇 Fast: 3-9 seconds\n"
        "🐢 Normal: 10-26 seconds\n"
        "🐌 Slow: 27-50 seconds",
        parse_mode=ParseMode.HTML,
        reply_markup=get_typing_speed_keyboard()
    )


@router.callback_query(F.data.in_(["speed_fast", "speed_normal", "speed_slow"]))
async def callback_set_speed(callback: CallbackQuery):
    """Set typing speed"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    speed = callback.data.replace("speed_", "")
    db.update_config({"typing_speed": speed})
    
    await callback.message.answer(
        f"✅ Typing speed set to: {speed}\n\n"
        f"This will affect future text-to-JSON conversions.",
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data.in_(["sim_start", "sim_stop", "sim_pause", "sim_resume"]))
async def callback_simulation_control(callback: CallbackQuery):
    """Control simulation"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await callback.message.answer("❌ Simulation engine not available.")
        return
    
    action = callback.data.replace("sim_", "")
    
    if action == "start":
        async def admin_notify(msg: str):
            try:
                await callback.message.answer(msg, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
        
        result = await simulation_engine.start_simulation(admin_callback=admin_notify)
    elif action == "stop":
        result = simulation_engine.stop_simulation()
    elif action == "pause":
        result = simulation_engine.pause_simulation()
    elif action == "resume":
        result = simulation_engine.resume_simulation()
    else:
        await callback.message.answer("❌ Unknown action")
        return
    
    if result["success"]:
        await callback.message.answer(
            f"✅ {result['message']}",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.message.answer(f"❌ {result['message']}")


# Missing callback handlers (redirects to commands with instructions)
@router.callback_query(F.data == "sessions_add")
async def callback_sessions_add(callback: CallbackQuery):
    """Add session - show instructions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.answer(
        "➕ <b>Add Session</b>\n\n"
        "To add a Telethon session, use:\n"
        "<code>/add_session &lt;name&gt; &lt;session_string&gt;</code>\n\n"
        "⚠️ Note: You need to generate session strings separately using Telethon.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_sessions_keyboard()
    )


@router.callback_query(F.data == "sessions_import")
async def callback_sessions_import(callback: CallbackQuery):
    """Import sessions - show instructions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.answer(
        "📦 <b>Import Sessions from ZIP</b>\n\n"
        "1. Send a ZIP file containing session TXT files\n"
        "2. Reply to it with /import_sessions\n\n"
        "Each TXT file should contain a session string.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_sessions_keyboard()
    )


@router.callback_query(F.data == "sessions_test")
async def callback_sessions_test(callback: CallbackQuery):
    """Test session - show instructions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.answer(
        "🧪 <b>Test Session</b>\n\n"
        "To test a session, use:\n"
        "<code>/test_session &lt;session_name&gt;</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_sessions_keyboard()
    )


@router.callback_query(F.data == "sessions_remove")
async def callback_sessions_remove(callback: CallbackQuery):
    """Remove session - show instructions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.answer(
        "❌ <b>Remove Session</b>\n\n"
        "To remove a session, use:\n"
        "<code>/remove_session &lt;session_name&gt;</code>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_sessions_keyboard()
    )


@router.callback_query(F.data == "schedule_run_period")
async def callback_schedule_run_period(callback: CallbackQuery):
    """Run period - show available periods"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await callback.message.answer("❌ Simulation engine not available.")
        return
    
    status = simulation_engine.get_schedule_status()
    if not status["has_schedule"]:
        await callback.message.answer(
            "❌ No scheduled periods available.\n"
            "Upload a JSON file with a 'schedule' array first.",
            reply_markup=get_schedule_keyboard()
        )
        return
    
    periods_list = "\n".join([f"• {p['label']} ({p['time']} UTC)" for p in status["periods"]])
    await callback.message.answer(
        f"▶️ <b>Run Period Manually</b>\n\n"
        f"To run a specific period, use:\n"
        f"<code>/run_period &lt;label&gt;</code>\n\n"
        f"<b>Available periods:</b>\n{periods_list}",
        parse_mode=ParseMode.HTML,
        reply_markup=get_schedule_keyboard()
    )


@router.callback_query(F.data == "settings_set_group")
async def callback_settings_set_group(callback: CallbackQuery):
    """Set target group - show instructions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.answer(
        "🎯 <b>Set Target Group</b>\n\n"
        "To set the target group for simulations, use:\n"
        "<code>/set_group &lt;group_id&gt;</code>\n\n"
        "You can get the group ID from /group_status",
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard()
    )


@router.callback_query(F.data == "settings_join_group")
async def callback_settings_join_group(callback: CallbackQuery):
    """Join group - show instructions"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await callback.message.answer(
        "🌐 <b>Join Group</b>\n\n"
        "To make all sessions join a group, use:\n"
        "<code>/join_group &lt;link&gt;</code>\n\n"
        "Examples:\n"
        "• /join_group https://t.me/groupname\n"
        "• /join_group @groupname",
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard()
    )


@router.callback_query(F.data == "settings_group_status")
async def callback_settings_group_status(callback: CallbackQuery):
    """Show group status"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    if not session_manager:
        await callback.message.answer("❌ Session manager not available.")
        return
    
    groups = await session_manager.get_groups_with_status()
    
    if not groups:
        await callback.message.answer(
            "📋 <b>No groups tracked yet.</b>\n\n"
            "Use /join_group &lt;link&gt; to make all sessions join a group.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_settings_keyboard()
        )
        return
    
    status_text = "📋 <b>Group Status Overview</b>\n\n"
    
    for group in groups:
        if group["simulation_active"]:
            status_emoji = "🟢"
            status_label = "ACTIVE"
        elif group["is_target"]:
            status_emoji = "🟡"
            status_label = "TARGET"
        else:
            status_emoji = "⚪"
            status_label = "NOT ACTIVE"
        
        status_text += f"{status_emoji} <b>{group['title']}</b>\n"
        status_text += f"   • ID: <code>{group['id']}</code>\n"
        status_text += f"   • Members: {group['members_count']}\n"
        status_text += f"   • Status: {status_label}\n\n"
    
    await callback.message.answer(
        status_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard()
    )
