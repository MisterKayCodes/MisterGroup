# Made by Mister 💛

import json
import os
import asyncio
import zipfile
import tempfile
import shutil
from datetime import datetime
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, FSInputFile
from aiogram.enums import ParseMode
from loguru import logger

from src.utils.database import Database
from src.services.session_manager import SessionManager
from src.services.simulation_engine import SimulationEngine
from src.models.conversation import ConversationData
from src.models.config import TypingSpeed
from src.utils.keyboards import (
    get_main_menu_keyboard, get_sessions_keyboard, get_schedule_keyboard,
    get_settings_keyboard, get_text_to_json_keyboard, get_simulation_control_keyboard
)

router = Router()

# Global instances (will be set in main.py)
db: Optional[Database] = None
session_manager: Optional[SessionManager] = None
simulation_engine: Optional[SimulationEngine] = None
admin_id: Optional[int] = None
_admin_lock = asyncio.Lock()  # Lock for admin assignment


def set_dependencies(database: Database,
                     sess_manager: Optional[SessionManager] = None,
                     sim_engine: Optional[SimulationEngine] = None,
                     admin_user_id: Optional[int] = None):
    """Set global dependencies for handlers"""
    global db, session_manager, simulation_engine, admin_id
    db = database
    session_manager = sess_manager
    simulation_engine = sim_engine
    admin_id = admin_user_id


async def is_admin(user_id: int) -> bool:
    """Check if user is admin, set first user as admin if not configured"""
    global admin_id

    # Always check database first for the most current admin_id
    if db:
        config = db.get_config()
        db_admin_id = config.get("admin_id")

        # Database has an admin set
        if db_admin_id is not None:
            admin_id = db_admin_id  # Update global with DB value
            return user_id == db_admin_id

    # No admin set anywhere - make this user the admin (with lock to prevent race conditions)
    if admin_id is None:
        async with _admin_lock:
            # Double-check after acquiring lock (in case another request set it)
            if db:
                config = db.get_config()
                db_admin_id = config.get("admin_id")
                if db_admin_id is not None:
                    admin_id = db_admin_id
                    return user_id == db_admin_id

            # Still no admin - set this user as admin
            if admin_id is None:
                admin_id = user_id
                if db:
                    db.update_config({"admin_id": user_id})
                logger.info(f"Admin ID set to first user: {user_id}")
                return True

    # Fallback to global admin_id
    return user_id == admin_id


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    if not await is_admin(message.from_user.id):
        await message.answer(
            "❌ Sorry, this bot is restricted to authorized users only.")
        return

    welcome_text = """
🤖 <b>Telegram Conversation Simulator Bot</b>
Made by Mister 💛

Welcome, Admin! Here are the available commands:

📋 <b>General Management</b>
/start — Show this command list
/help — Show detailed help and instructions
/status — Show current bot status and statistics

👥 <b>Telethon Sessions Management</b>
/add_session — Add/register a new Telethon session
/import_sessions — Bulk import sessions from ZIP file
/list_sessions — List all active Telethon sessions
/remove_session &lt;name&gt; — Remove a specific session
/test_session &lt;name&gt; — Test if a session is valid

🌐 <b>Group Management</b>
/join_group &lt;link&gt; — Make all sessions join a group
/group_status — View all groups and simulation status

🗂️ <b>Conversation & Chat Simulation</b>
/upload_json — Upload conversation data (reply to JSON file)
/show_preview — Preview loaded conversation
/start_simulation — Begin message simulation (immediate mode)
/stop_simulation — Stop ongoing simulation
/pause_simulation — Pause simulation
/resume_simulation — Resume paused simulation

⏰ <b>Scheduling</b>
/schedule_status — View scheduled periods and their status
/start_scheduler — Start automatic scheduled simulation
/stop_scheduler — Stop the scheduler
/run_period &lt;label&gt; — Manually run a specific time period

📋 <b>Queue Management</b>
/queue_status — View queued conversations
/clear_queue — Clear all queued conversations
/process_queue — Manually process next queued item

⚙️ <b>Configuration & Settings</b>
/set_group &lt;group_id&gt; — Set target group
/set_typing_speed &lt;fast|normal|slow&gt; — Adjust typing speed
/pause_account &lt;name&gt; — Pause a session
/resume_account &lt;name&gt; — Resume a session
/pause_all — Pause all sessions
/resume_all — Resume all sessions

🛠️ <b>Maintenance & Debugging</b>
/get_logs — Retrieve recent log files
/restart — Restart the bot

Ready to simulate conversations! 🚀
    """
    await message.answer(welcome_text, parse_mode=ParseMode.HTML, reply_markup=get_main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    if not await is_admin(message.from_user.id):
        await message.answer(
            "❌ Access denied. Only authorized users can use this bot.")
        return

    help_text = """
🤖 <b>Bot Help & Command Guide</b>
Made by Mister 💛

<b>🔹 General Usage</b>
• Upload conversations in JSON format using /upload_json
• Preview your conversations with /show_preview
• Start and stop message simulations with /start_simulation and /stop_simulation
• Set the target Telegram group/channel with /set_group

<b>🔹 Session Management</b>
• Add a new Telethon session: /add_session
• Bulk import from ZIP: /import_sessions (reply to ZIP file)
• List all sessions: /list_sessions
• Remove a session: /remove_session &lt;name&gt;
• Test session connectivity: /test_session &lt;name&gt;
• Pause or resume accounts: /pause_account &lt;name&gt;, /resume_account &lt;name&gt;
• Pause or resume all sessions: /pause_all, /resume_all

<b>🔹 Group Management</b>
• Join all sessions to a group: /join_group &lt;link&gt;
• View all groups and their status: /group_status

<b>🔹 Scheduling (Time-Based Simulations)</b>
• View schedule status: /schedule_status
• Start automatic scheduler: /start_scheduler
• Stop scheduler: /stop_scheduler
• Run a specific period manually: /run_period &lt;label&gt;

<b>🔹 Typing Simulation</b>
• Configure typing speed: /set_typing_speed &lt;fast|normal|slow&gt;

<b>🔹 Bot Status & Logs</b>
• View bot status summary: /status
• Retrieve recent logs for debugging: /get_logs

<b>🔹 Bot Control</b>
• Restart the bot: /restart

For detailed command usage, just send the command to see how it works!

If you need further assistance, check the documentation or contact support.
    """
    await message.answer(help_text, parse_mode=ParseMode.HTML)


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Handle /status command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    # Get statistics
    stats = db.get_statistics()
    config = db.get_config()
    sessions = db.get_all_sessions()
    sim_state = db.get_simulation_state()

    # Count active/paused sessions
    active_count = sum(1 for s in sessions.values()
                       if s.get("status") == "active")
    paused_count = sum(1 for s in sessions.values()
                       if s.get("status") == "paused")

    status_text = f"""
📊 <b>Bot Status</b>
Made by Mister 💛

<b>Sessions:</b>
• Total: {len(sessions)}
• Active: {active_count}
• Paused: {paused_count}

<b>Configuration:</b>
• Typing Speed: {config.get('typing_speed', 'normal')}
• Target Group: {config.get('target_group', 'Not set')}

<b>Simulation:</b>
• Running: {'Yes' if sim_state.get('is_running') else 'No'}
• Paused: {'Yes' if sim_state.get('is_paused') else 'No'}
• Current Index: {sim_state.get('current_index', 0)}

<b>Statistics:</b>
• Messages Sent Today: {stats.get('messages_sent_today', 0)}
• Total Messages Sent: {stats.get('total_messages_sent', 0)}
• Last Reset: {stats.get('last_reset', 'Never')}
    """
    await message.answer(status_text, parse_mode=ParseMode.HTML)


@router.message(Command("add_session"))
async def cmd_add_session(message: Message, command: CommandObject):
    """Handle /add_session command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    await message.answer(
        "ℹ️ To add a Telethon session, you need to provide:\n\n"
        "1. Session name (unique identifier)\n"
        "2. Session string (from an authorized Telethon session)\n\n"
        "Usage: /add_session <name> <session_string>\n\n"
        "⚠️ Note: You need to generate session strings separately using Telethon. "
        "This bot cannot perform the full authorization flow interactively.")


@router.message(Command("import_sessions"))
async def cmd_import_sessions(message: Message):
    """Handle /import_sessions command - bulk import sessions from ZIP file"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not db:
        await message.answer("❌ Database not initialized.")
        return

    if message.reply_to_message and message.reply_to_message.document:
        doc = message.reply_to_message.document
        
        if not doc.file_name.lower().endswith('.zip'):
            await message.answer("❌ Please send a ZIP file containing session TXT files.")
            return
        
        await message.answer("📦 Processing ZIP file...")
        
        temp_dir = None
        try:
            file = await message.bot.get_file(doc.file_id)
            zip_path = f"/tmp/{doc.file_name}"
            await message.bot.download_file(file.file_path, zip_path)
            
            temp_dir = tempfile.mkdtemp()
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            txt_files = []
            for root, dirs, files in os.walk(temp_dir):
                for file_name in files:
                    if file_name.lower().endswith('.txt'):
                        txt_files.append(os.path.join(root, file_name))
            
            if not txt_files:
                await message.answer("❌ No .txt files found in the ZIP archive.")
                return
            
            new_sessions = 0
            updated_sessions = 0
            skipped = 0
            errors = []
            
            existing_sessions = db.get_all_sessions()
            
            for txt_path in txt_files:
                try:
                    file_name = os.path.basename(txt_path)
                    session_name = os.path.splitext(file_name)[0]
                    
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        session_string = f.read().strip()
                    
                    if not session_string:
                        errors.append(f"{session_name}: Empty file")
                        skipped += 1
                        continue
                    
                    if len(session_string) < 50:
                        errors.append(f"{session_name}: Session string too short")
                        skipped += 1
                        continue
                    
                    if not session_string[0].isalnum():
                        errors.append(f"{session_name}: Invalid session string format")
                        skipped += 1
                        continue
                    
                    if session_name in existing_sessions:
                        existing_data = existing_sessions[session_name]
                        session_data = {
                            "name": session_name,
                            "session_string": session_string,
                            "is_active": existing_data.get("is_active", True),
                            "status": existing_data.get("status", "active"),
                            "username": existing_data.get("username"),
                            "user_id": existing_data.get("user_id"),
                            "last_tested": existing_data.get("last_tested"),
                            "is_connected": existing_data.get("is_connected", False)
                        }
                        db.add_session(session_name, session_data)
                        updated_sessions += 1
                        logger.info(f"Updated session: {session_name}")
                    else:
                        session_data = {
                            "name": session_name,
                            "session_string": session_string,
                            "is_active": True
                        }
                        db.add_session(session_name, session_data)
                        new_sessions += 1
                        logger.info(f"Imported new session: {session_name}")
                    
                except Exception as e:
                    errors.append(f"{session_name}: {str(e)}")
                    skipped += 1
            
            result_text = f"✅ <b>Import Complete!</b>\n\n"
            result_text += f"🆕 New sessions: {new_sessions}\n"
            result_text += f"🔄 Updated sessions: {updated_sessions}\n"
            result_text += f"⏭️ Skipped: {skipped} files\n"
            
            if errors and len(errors) <= 5:
                result_text += f"\n<b>Errors:</b>\n"
                for err in errors:
                    result_text += f"• {err}\n"
            elif errors:
                result_text += f"\n⚠️ {len(errors)} files had errors"
            
            result_text += f"\nUse /list_sessions to view all sessions."
            
            await message.answer(result_text, parse_mode=ParseMode.HTML)
            
        except zipfile.BadZipFile:
            await message.answer("❌ Invalid ZIP file. Please send a valid ZIP archive.")
        except Exception as e:
            logger.error(f"Error importing sessions: {e}")
            await message.answer(f"❌ Error processing ZIP file: {str(e)}")
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    else:
        await message.answer(
            "ℹ️ <b>Import Sessions from ZIP</b>\n\n"
            "Send a ZIP file containing session TXT files, then reply to it with /import_sessions\n\n"
            "<b>Expected format:</b>\n"
            "• Each TXT file name = session name (e.g., AmberTerry.txt)\n"
            "• File content = session string\n\n"
            "The sessions will be saved with the same format as existing ones.",
            parse_mode=ParseMode.HTML
        )


@router.message(Command("list_sessions"))
async def cmd_list_sessions(message: Message):
    """Handle /list_sessions command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    sessions = session_manager.list_sessions()

    if not sessions:
        await message.answer(
            "📋 No sessions registered yet.\n\nUse /add_session to add one.")
        return

    session_list = "📋 <b>Registered Sessions:</b>\n\n"
    for session in sessions:
        status_emoji = "🟢" if session.get("status") == "active" else "🟡"
        session_list += f"{status_emoji} <b>{session.get('name')}</b>\n"
        session_list += f"  • Status: {session.get('status')}\n"
        session_list += f"  • Username: @{session.get('username', 'unknown')}\n"
        session_list += f"  • Connected: {'Yes' if session.get('is_connected') else 'No'}\n"
        last_tested = session.get('last_tested')
        if last_tested:
            session_list += f"  • Last Tested: {last_tested}\n"
        session_list += "\n"

    await message.answer(session_list, parse_mode=ParseMode.HTML)


@router.message(Command("remove_session"))
async def cmd_remove_session(message: Message, command: CommandObject):
    """Handle /remove_session command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    if not command.args:
        await message.answer(
            "❌ Please provide session name.\n\nUsage: /remove_session <name>")
        return

    name = command.args.strip()
    success = session_manager.remove_session(name)

    if success:
        await message.answer(
            f"✅ Session '{name}' has been removed successfully.")
    else:
        await message.answer(f"❌ Session '{name}' not found.")


@router.message(Command("test_session"))
async def cmd_test_session(message: Message, command: CommandObject):
    """Handle /test_session command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    if not command.args:
        await message.answer(
            "❌ Please provide session name.\n\nUsage: /test_session <name>")
        return

    name = command.args.strip()
    await message.answer(f"🔄 Testing session '{name}'...")

    result = await session_manager.test_session(name)

    if result["success"]:
        await message.answer(
            f"✅ {result['message']}\nUser: {result.get('user', 'Unknown')}")
    else:
        await message.answer(f"❌ {result['message']}")


@router.message(Command("upload_json"))
async def cmd_upload_json(message: Message):
    """Handle /upload_json command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    # Check if message is a reply to a document
    if message.reply_to_message and message.reply_to_message.document:
        doc = message.reply_to_message.document

        # Download file
        file = await message.bot.get_file(doc.file_id)
        file_path = f"/tmp/{doc.file_name}"
        await message.bot.download_file(file.file_path, file_path)

        try:
            # Read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_data = json.load(f)

            # Validate with Pydantic
            conversation = ConversationData(**conversation_data)

            # Save to database
            db.set_conversation(conversation.model_dump(mode='json'))

            # Determine mode and message count
            if conversation.is_scheduled():
                total_msgs = conversation.get_total_message_count()
                period_count = len(conversation.schedule)
                mode_info = f"Mode: Scheduled ({period_count} periods, {total_msgs} total messages)"
                next_step = "Use /schedule_status to view periods or /start_scheduler to begin."
            else:
                mode_info = f"Mode: Immediate ({len(conversation.messages)} messages)"
                next_step = "Use /show_preview to preview or /start_simulation to begin."
            
            # Check for media tags and validate categories
            media_tag_warning = ""
            try:
                from src.database.media_tables import MediaDatabase
                from src.utils.media_parser import validate_media_tags_in_messages, validate_scheduled_media_tags
                
                media_db = MediaDatabase()
                
                if conversation.is_scheduled():
                    schedule_dicts = [
                        {"messages": [msg.model_dump() for msg in period.messages]}
                        for period in conversation.schedule
                    ]
                    tag_validation = validate_scheduled_media_tags(schedule_dicts, media_db)
                else:
                    messages_dicts = [msg.model_dump() for msg in conversation.messages]
                    tag_validation = validate_media_tags_in_messages(messages_dicts, media_db)
                
                if tag_validation['warning_message']:
                    media_tag_warning = f"\n\n{tag_validation['warning_message']}"
            except Exception as e:
                logger.debug(f"Media tag validation skipped: {e}")
            
            await message.answer(
                f"✅ JSON data uploaded successfully!\n\n"
                f"Conversation: {conversation.name}\n"
                f"{mode_info}\n\n"
                f"{next_step}{media_tag_warning}",
                parse_mode=ParseMode.HTML)

        except Exception as e:
            await message.answer(
                f"❌ Error processing JSON: {str(e)}\n\nPlease check the file format."
            )

        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
    else:
        await message.answer(
            "ℹ️ Please reply to a JSON file with /upload_json command.\n\n"
            "Or send the JSON file and then reply to it with this command.")


@router.message(Command("show_preview"))
async def cmd_show_preview(message: Message):
    """Handle /show_preview command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    conversation_data = db.get_conversation()
    if not conversation_data:
        await message.answer(
            "❌ No conversation data loaded yet.\n\nUse /upload_json to upload data."
        )
        return

    conversation = ConversationData(**conversation_data)
    
    # Check if scheduled mode
    if conversation.is_scheduled():
        preview_text = f"📄 <b>Conversation Preview</b>\n"
        preview_text += f"Name: {conversation.name}\n"
        preview_text += f"Mode: <b>Scheduled</b>\n\n"
        
        for period in conversation.schedule:
            status = "✅" if period.enabled else "❌"
            participants = "All" if (isinstance(period.participants, str) and period.participants.lower() == "all") else f"{len(period.participants)} users"
            preview_text += f"{status} <b>{period.time}</b> — {period.label}\n"
            preview_text += f"   📧 {len(period.messages)} messages | {participants} | {period.repeat}\n"
            
            # Show first 2 messages from each period
            for msg in period.messages[:2]:
                content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
                preview_text += f"   • <i>{msg.sender_name}:</i> {content}\n"
            
            if len(period.messages) > 2:
                preview_text += f"   <i>...and {len(period.messages) - 2} more</i>\n"
            preview_text += "\n"
        
        total = conversation.get_total_message_count()
        preview_text += f"<b>Total: {len(conversation.schedule)} periods, {total} messages</b>\n\n"
        preview_text += "Use /schedule_status to view status\n"
        preview_text += "Use /start_scheduler to begin automatic execution\n"
        preview_text += "Use /run_period &lt;label&gt; to run a period manually"
    else:
        # Immediate mode
        preview_text = f"📄 <b>Conversation Preview</b>\n"
        preview_text += f"Name: {conversation.name}\n"
        preview_text += f"Mode: <b>Immediate</b>\n\n"

        # Show first 20 messages
        max_preview = min(20, len(conversation.messages))
        for i in range(max_preview):
            msg = conversation.messages[i]
            if msg.message_type == "text":
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                preview_text += f"<b>{msg.sender_name}:</b> {content}\n"
            else:
                preview_text += f"<b>{msg.sender_name}:</b> [{msg.message_type.upper()}]\n"

        if len(conversation.messages) > max_preview:
            preview_text += f"\n... and {len(conversation.messages) - max_preview} more messages\n"

        preview_text += f"\n<i>Total messages: {len(conversation.messages)}</i>"
        preview_text += "\n\nUse /start_simulation to run the conversation."

    await message.answer(preview_text, parse_mode=ParseMode.HTML)


@router.message(Command("start_simulation"))
async def cmd_start_simulation(message: Message):
    """Handle /start_simulation command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not simulation_engine:
        await message.answer(
            "❌ Simulation features unavailable. Telethon not configured.")
        return

    # Check for scheduler conflict
    conflict = simulation_engine.check_scheduler_conflict()
    if conflict.get("has_conflict"):
        reason = conflict.get("reason", "Scheduler is running")
        
        # Get conversation data to queue
        conversation_data = db.get_conversation()
        if conversation_data:
            try:
                from src.models.conversation import ConversationData
                conv = ConversationData(**conversation_data)
                
                # Only offer queuing for immediate mode conversations
                if not conv.is_scheduled():
                    queue_result = simulation_engine.queue_conversation(
                        conversation_data, 
                        reason=reason
                    )
                    
                    if queue_result.get("success"):
                        await message.answer(
                            f"⏳ <b>Scheduler Conflict Detected</b>\n\n"
                            f"Reason: {reason}\n\n"
                            f"✅ Your conversation has been queued (position {queue_result.get('queue_position')}).\n"
                            f"It will automatically run after scheduled posts complete.\n\n"
                            f"Use /queue_status to view queued conversations.\n"
                            f"Use /clear_queue to cancel all queued items.",
                            parse_mode=ParseMode.HTML
                        )
                        return
            except Exception as e:
                logger.debug(f"Queue check error: {e}")
        
        await message.answer(
            f"⚠️ <b>Scheduler Conflict</b>\n\n"
            f"{reason}\n\n"
            f"Stop the scheduler first with /stop_scheduler or wait for scheduled posts to complete.",
            parse_mode=ParseMode.HTML
        )
        return

    async def callback(msg: str):
        await message.answer(msg)

    result = await simulation_engine.start_simulation(admin_callback=callback)

    if not result["success"]:
        await message.answer(f"❌ {result['message']}")


@router.message(Command("stop_simulation"))
async def cmd_stop_simulation(message: Message):
    """Handle /stop_simulation command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not simulation_engine:
        await message.answer(
            "❌ Simulation features unavailable. Telethon not configured.")
        return

    result = simulation_engine.stop_simulation()
    await message.answer(
        f"{'✅' if result['success'] else '❌'} {result['message']}")


@router.message(Command("pause_simulation"))
async def cmd_pause_simulation(message: Message):
    """Handle /pause_simulation command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not simulation_engine:
        await message.answer(
            "❌ Simulation features unavailable. Telethon not configured.")
        return

    result = simulation_engine.pause_simulation()
    await message.answer(
        f"{'✅' if result['success'] else '❌'} {result['message']}")


@router.message(Command("resume_simulation"))
async def cmd_resume_simulation(message: Message):
    """Handle /resume_simulation command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not simulation_engine:
        await message.answer(
            "❌ Simulation features unavailable. Telethon not configured.")
        return

    result = simulation_engine.resume_simulation()
    await message.answer(
        f"{'✅' if result['success'] else '❌'} {result['message']}")


@router.message(Command("set_group"))
async def cmd_set_group(message: Message, command: CommandObject):
    """Handle /set_group command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not command.args:
        await message.answer(
            "❌ Please provide group ID.\n\nUsage: /set_group <group_id>")
        return

    try:
        group_id = int(command.args.strip())
        db.update_config({"target_group": group_id})
        await message.answer(f"✅ Target group set to: {group_id}")
    except ValueError:
        await message.answer("❌ Invalid group ID. Please provide a numeric ID."
                             )


@router.message(Command("set_typing_speed"))
async def cmd_set_typing_speed(message: Message, command: CommandObject):
    """Handle /set_typing_speed command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not command.args:
        await message.answer(
            "❌ Please provide speed.\n\nUsage: /set_typing_speed <fast|normal|slow>"
        )
        return

    speed = command.args.strip().lower()
    if speed not in ["fast", "normal", "slow"]:
        await message.answer("❌ Invalid speed. Choose: fast, normal, or slow")
        return

    db.update_config({"typing_speed": speed})
    await message.answer(f"✅ Typing speed set to: {speed}")


@router.message(Command("pause_account"))
async def cmd_pause_account(message: Message, command: CommandObject):
    """Handle /pause_account command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    if not command.args:
        await message.answer(
            "❌ Please provide account name.\n\nUsage: /pause_account <name>")
        return

    name = command.args.strip()
    success = session_manager.pause_session(name)

    if success:
        await message.answer(
            f"✅ Account '{name}' has been paused successfully.")
    else:
        await message.answer(f"❌ Account '{name}' not found.")


@router.message(Command("resume_account"))
async def cmd_resume_account(message: Message, command: CommandObject):
    """Handle /resume_account command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    if not command.args:
        await message.answer(
            "❌ Please provide account name.\n\nUsage: /resume_account <name>")
        return

    name = command.args.strip()
    success = session_manager.resume_session(name)

    if success:
        await message.answer(
            f"✅ Account '{name}' has been resumed successfully.")
    else:
        await message.answer(f"❌ Account '{name}' not found.")


@router.message(Command("pause_all"))
async def cmd_pause_all(message: Message):
    """Handle /pause_all command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    count = session_manager.pause_all_sessions()
    await message.answer(
        f"✅ All accounts have been paused ({count} sessions).\nNo messages will be sent until resumed."
    )


@router.message(Command("resume_all"))
async def cmd_resume_all(message: Message):
    """Handle /resume_all command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    count = session_manager.resume_all_sessions()
    await message.answer(
        f"✅ All accounts have been resumed ({count} sessions).\nMessage sending is now enabled."
    )


@router.message(Command("schedule_status"))
async def cmd_schedule_status(message: Message):
    """Handle /schedule_status command - view scheduled periods with countdown timers"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await message.answer("❌ Simulation engine not available.")
        return
    
    status = simulation_engine.get_schedule_status()
    
    if not status["has_schedule"]:
        await message.answer(
            "📅 <b>No Schedule Configured</b>\n\n"
            "The loaded conversation doesn't have scheduled periods.\n"
            "Upload a JSON file with a 'schedule' array to use time-based simulations.\n\n"
            "See /help for JSON format details.",
            parse_mode=ParseMode.HTML
        )
        return
    
    scheduler_status = "🟢 Running" if status["scheduler_running"] else "🔴 Stopped"
    
    text = f"📅 <b>Schedule Status</b>\n\n"
    text += f"<b>Scheduler:</b> {scheduler_status}\n"
    
    # Show next upcoming period with countdown
    next_period = status.get("next_period")
    if next_period and status["scheduler_running"]:
        text += f"<b>Next Post:</b> ⏱ {next_period['label']} in <b>{next_period['countdown']}</b>\n"
    
    text += "\n<b>Scheduled Periods:</b>\n"
    
    for period in status["periods"]:
        enabled_icon = "✅" if period["enabled"] else "❌"
        
        # Status indicator with countdown
        if period["executed_today"]:
            status_text = "✓ Done"
        elif period.get("countdown"):
            if period["countdown"] == "Passed":
                status_text = "⏰ Passed"
            else:
                status_text = f"⏱ in {period['countdown']}"
        else:
            status_text = "○ Pending"
        
        participants = period["participants"]
        if len(participants) > 25:
            participants = participants[:22] + "..."
        
        text += f"\n{enabled_icon} <b>{period['time']}</b> — {period['label']}\n"
        text += f"   {status_text} | {period['message_count']} msgs | {period['repeat']}\n"
        text += f"   👥 {participants}\n"
    
    # Show queued items if any
    queued_items = status.get("queued_items", 0)
    if queued_items > 0:
        text += f"\n📋 <b>Queue:</b> {queued_items} conversation(s) waiting\n"
        text += "   Will auto-process after scheduled posts complete.\n"
    
    text += "\n<b>Commands:</b>\n"
    if status["scheduler_running"]:
        text += "• /stop_scheduler — Stop automatic execution\n"
    else:
        text += "• /start_scheduler — Start automatic execution\n"
    text += "• /run_period &lt;label&gt; — Run a period manually"
    
    if queued_items > 0:
        text += "\n• /queue_status — View queued conversations"
    
    await message.answer(text, parse_mode=ParseMode.HTML)


@router.message(Command("start_scheduler"))
async def cmd_start_scheduler(message: Message):
    """Handle /start_scheduler command - start the automatic scheduler"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await message.answer("❌ Simulation engine not available.")
        return
    
    async def admin_notify(msg: str):
        try:
            await message.answer(msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
    
    result = await simulation_engine.start_scheduler(admin_callback=admin_notify)
    
    if result["success"]:
        await message.answer(
            f"✅ <b>Scheduler Started!</b>\n\n{result['message']}",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.answer(f"❌ {result['message']}")


@router.message(Command("stop_scheduler"))
async def cmd_stop_scheduler(message: Message):
    """Handle /stop_scheduler command - stop the automatic scheduler"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await message.answer("❌ Simulation engine not available.")
        return
    
    result = simulation_engine.stop_scheduler()
    
    if result["success"]:
        await message.answer(f"✅ {result['message']}")
    else:
        await message.answer(f"❌ {result['message']}")


@router.message(Command("run_period"))
async def cmd_run_period(message: Message, command: CommandObject):
    """Handle /run_period command - manually run a specific scheduled period"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    if not simulation_engine:
        await message.answer("❌ Simulation engine not available.")
        return
    
    if not command.args:
        # Show available periods
        status = simulation_engine.get_schedule_status()
        if not status["has_schedule"]:
            await message.answer(
                "❌ No scheduled periods available.\n"
                "Upload a JSON file with a 'schedule' array first."
            )
            return
        
        periods_list = "\n".join([f"• {p['label']} ({p['time']})" for p in status["periods"]])
        await message.answer(
            f"❌ Please specify which period to run.\n\n"
            f"Usage: /run_period &lt;label&gt;\n\n"
            f"<b>Available periods:</b>\n{periods_list}",
            parse_mode=ParseMode.HTML
        )
        return
    
    period_label = command.args.strip()
    
    async def admin_notify(msg: str):
        try:
            await message.answer(msg, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
    
    await message.answer(f"⏳ Running period: {period_label}...")
    
    result = await simulation_engine.run_specific_period(period_label, admin_callback=admin_notify)
    
    if result["success"]:
        await message.answer(f"✅ {result['message']}")
    else:
        await message.answer(f"❌ {result['message']}")


@router.message(Command("get_logs"))
async def cmd_get_logs(message: Message):
    """Handle /get_logs command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    # Get the most recent log file
    log_dir = "logs"
    if not os.path.exists(log_dir):
        await message.answer("❌ No log files found.")
        return

    log_files = [
        f for f in os.listdir(log_dir)
        if f.endswith('.log') and not f.endswith('.zip')
    ]
    if not log_files:
        await message.answer("❌ No log files found.")
        return

    # Get most recent file
    latest_log = max(log_files,
                     key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    log_path = os.path.join(log_dir, latest_log)

    # Send file
    try:
        file = FSInputFile(log_path, filename=latest_log)
        await message.answer_document(
            file, caption=f"📄 Latest log file: {latest_log}")
    except Exception as e:
        await message.answer(f"❌ Error sending log file: {str(e)}")


@router.message(Command("restart"))
async def cmd_restart(message: Message):
    """Handle /restart command"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    await message.answer(
        "🔄 Restarting bot...\n\nNote: Restart must be done manually from the server."
    )


@router.message(Command("join_group"))
async def cmd_join_group(message: Message, command: CommandObject):
    """Handle /join_group command - make all sessions join a group"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    if not command.args:
        await message.answer("❌ Please provide a group link.\n\n"
                             "Usage: /join_group <link>\n\n"
                             "Examples:\n"
                             "• /join_group https://t.me/groupname\n"
                             "• /join_group https://t.me/+invitehash\n"
                             "• /join_group @groupname")
        return

    group_link = command.args.strip()

    await message.answer(
        f"🔄 Starting to join all sessions to the group...\n\nLink: {group_link}"
    )

    async def progress_callback(msg: str):
        try:
            await message.answer(msg)
        except:
            pass

    result = await session_manager.join_all_to_group(
        group_link, callback=progress_callback)

    if result["success"]:
        summary = f"✅ <b>Join Group Complete!</b>\n\n"
        if result.get("group_info"):
            summary += f"<b>Group:</b> {result['group_info'].get('title', 'Unknown')}\n"
            summary += f"<b>ID:</b> {result['group_info'].get('id', 'Unknown')}\n\n"

        summary += f"<b>Results:</b>\n"
        summary += f"• ✅ Joined: {len([r for r in result['results'] if r['status'] == 'joined'])}\n"
        summary += f"• 👤 Already member: {len([r for r in result['results'] if r['status'] == 'already_member'])}\n"
        summary += f"• ❌ Failed: {len([r for r in result['results'] if r['status'] == 'failed'])}\n"
        summary += f"• ⏭️ Skipped: {len([r for r in result['results'] if r['status'] == 'skipped'])}\n"

        failed = [r for r in result["results"] if r["status"] == "failed"]
        if failed:
            summary += f"\n<b>Failed sessions:</b>\n"
            for f in failed[:5]:
                summary += f"• {f['name']}: {f['reason']}\n"
            if len(failed) > 5:
                summary += f"... and {len(failed) - 5} more\n"

        await message.answer(summary, parse_mode=ParseMode.HTML)
    else:
        await message.answer(f"❌ Failed to join group: {result['message']}")


@router.message(Command("group_status"))
async def cmd_group_status(message: Message):
    """Handle /group_status command - show all groups and their simulation status"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not session_manager:
        await message.answer(
            "❌ Telethon features unavailable. API_ID and API_HASH not configured."
        )
        return

    groups = await session_manager.get_groups_with_status()

    if not groups:
        await message.answer(
            "📋 <b>No groups tracked yet.</b>\n\n"
            "Use /join_group &lt;link&gt; to make all sessions join a group.",
            parse_mode=ParseMode.HTML)
        return

    status_text = "📋 <b>Group Status Overview</b>\n\n"

    for group in groups:
        if group["simulation_active"]:
            status_emoji = "🟢"
            status_label = "ACTIVE"
        elif group["is_target"]:
            status_emoji = "🟡"
            status_label = "TARGET (paused)"
        else:
            status_emoji = "⚪"
            status_label = "NOT ACTIVE"

        status_text += f"{status_emoji} <b>{group['title']}</b>\n"
        status_text += f"   • ID: <code>{group['id']}</code>\n"
        status_text += f"   • Type: {group['type']}\n"
        status_text += f"   • Members joined: {group['members_count']}\n"
        status_text += f"   • Simulation: {status_label}\n"
        if group.get("joined_at"):
            status_text += f"   • Joined: {group['joined_at'][:10]}\n"
        status_text += "\n"

    status_text += "<b>Legend:</b>\n"
    status_text += "🟢 Simulation running | 🟡 Target group (not running) | ⚪ Not active\n\n"
    status_text += "<i>Use /set_group <id> to set target, then /start_simulation to begin.</i>"

    await message.answer(status_text, parse_mode=ParseMode.HTML)


# Button text handlers (for reply keyboard)
@router.message(F.text == "📊 Status")
async def button_status(message: Message):
    """Handle Status button"""
    await cmd_status(message)


@router.message(F.text == "🗂️ Upload JSON")
async def button_upload_json(message: Message):
    """Handle Upload JSON button"""
    await message.answer(
        "📝 <b>Upload Conversation JSON</b>\n\n"
        "You can:\n"
        "1. Reply to a JSON file with /upload_json\n"
        "2. Convert text to JSON using the button below\n\n"
        "Text conversion allows you to paste conversation text and automatically convert it to JSON with randomized delays!",
        parse_mode=ParseMode.HTML,
        reply_markup=get_text_to_json_keyboard()
    )


@router.message(F.text == "📄 Upload TXT")
async def button_upload_txt(message: Message):
    """Handle Upload TXT button"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    await message.answer(
        "📄 <b>Upload TXT Batch File</b>\n\n"
        "Upload a .txt file with scheduled conversation batches.\n\n"
        "<b>Format:</b>\n"
        "<code>---BATCH: Morning Chat | 09:00 | daily---</code>\n"
        "<code>Alice: Good morning everyone!</code>\n"
        "<code>Bob: Hey, good morning!</code>\n\n"
        "<code>---BATCH: Lunch Break | 12:30 | weekdays---</code>\n"
        "<code>Alice: Lunch time!</code>\n\n"
        "<b>Batch header format:</b>\n"
        "<code>---BATCH: Label | HH:MM | repeat---</code>\n\n"
        "<b>Repeat options:</b> daily, weekdays, weekends, once\n\n"
        "📎 Send a .txt file, then reply to it with /upload_txt",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("upload_txt"))
async def cmd_upload_txt(message: Message):
    """Handle /upload_txt command - process TXT file with batch format"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    if not db:
        await message.answer("❌ Database not initialized.")
        return
    
    if message.reply_to_message and message.reply_to_message.document:
        doc = message.reply_to_message.document
        
        if not doc.file_name.lower().endswith('.txt'):
            await message.answer("❌ Please send a .txt file with batch format.")
            return
        
        await message.answer("📄 Processing TXT batch file...")
        
        try:
            file = await message.bot.get_file(doc.file_id)
            file_path = f"/tmp/{doc.file_name}"
            await message.bot.download_file(file.file_path, file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            from src.utils.text_to_json import parse_txt_batches, format_txt_batch_preview
            
            conversation_data = parse_txt_batches(text_content, delay_speed="normal")
            
            conversation = ConversationData(**conversation_data)
            
            db.set_conversation(conversation.model_dump(mode='json'))
            
            preview = format_txt_batch_preview(conversation_data)
            
            total_msgs = conversation.get_total_message_count()
            period_count = len(conversation.schedule)
            
            # Check for media tags and validate categories
            media_tag_warning = ""
            try:
                from src.database.media_tables import MediaDatabase
                from src.utils.media_parser import validate_scheduled_media_tags
                
                media_db = MediaDatabase()
                schedule_dicts = conversation_data.get('schedule', [])
                tag_validation = validate_scheduled_media_tags(schedule_dicts, media_db)
                
                if tag_validation['warning_message']:
                    media_tag_warning = f"\n\n{tag_validation['warning_message']}"
            except Exception as e:
                logger.debug(f"Media tag validation skipped: {e}")
            
            await message.answer(
                f"✅ <b>TXT Batch Upload Successful!</b>\n\n"
                f"{preview}\n"
                f"<b>Next Steps:</b>\n"
                f"• Use /schedule_status to view all periods\n"
                f"• Use /start_scheduler to begin automatic execution\n"
                f"• Use /run_period &lt;label&gt; to run a specific period manually{media_tag_warning}",
                parse_mode=ParseMode.HTML
            )
            
            if os.path.exists(file_path):
                os.remove(file_path)
                
        except ValueError as e:
            await message.answer(f"❌ Error parsing TXT file:\n{str(e)}", parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Error processing TXT upload: {e}")
            await message.answer(f"❌ Error processing file: {str(e)}")
    else:
        await message.answer(
            "ℹ️ <b>Upload TXT Batch File</b>\n\n"
            "Send a .txt file with batch format, then reply to it with /upload_txt\n\n"
            "<b>Example format:</b>\n"
            "<code>---BATCH: Morning Chat | 09:00 | daily---</code>\n"
            "<code>Alice: Good morning!</code>\n"
            "<code>Bob: Hey!</code>",
            parse_mode=ParseMode.HTML
        )


@router.message(F.text == "▶️ Start Sim")
async def button_start_sim(message: Message):
    """Handle Start Simulation button"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    sim_state = db.get_simulation_state()
    await message.answer(
        "▶️ <b>Simulation Control</b>\n\nSelect an action:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_simulation_control_keyboard(
            sim_state.get("is_running", False),
            sim_state.get("is_paused", False)
        )
    )


@router.message(F.text == "⏹️ Stop Sim")
async def button_stop_sim(message: Message):
    """Handle Stop Simulation button"""
    await cmd_stop_simulation(message)


@router.message(F.text == "⏸️ Pause/Resume")
async def button_pause_resume(message: Message):
    """Handle Pause/Resume button"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    sim_state = db.get_simulation_state()
    if sim_state.get("is_paused"):
        await cmd_resume_simulation(message)
    else:
        await cmd_pause_simulation(message)


@router.message(F.text == "👥 Sessions")
async def button_sessions(message: Message):
    """Handle Sessions button"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    await message.answer(
        "👥 <b>Session Management</b>\n\nSelect an option:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_sessions_keyboard()
    )


@router.message(F.text == "⏰ Schedule")
async def button_schedule(message: Message):
    """Handle Schedule button"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    await message.answer(
        "⏰ <b>Schedule Management</b>\n\nSelect an option:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_schedule_keyboard()
    )


@router.message(F.text == "⚙️ Settings")
async def button_settings(message: Message):
    """Handle Settings button"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    config = db.get_config()
    settings_text = f"""
⚙️ <b>Settings</b>

<b>Current Configuration:</b>
• Typing Speed: {config.get('typing_speed', 'normal')}
• Target Group: {config.get('target_group', 'Not set')}

Select an option:
"""
    await message.answer(
        settings_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_settings_keyboard()
    )


@router.message(F.text == "📋 Help")
async def button_help(message: Message):
    """Handle Help button"""
    await cmd_help(message)


@router.message(F.text == "📄 Logs")
async def button_logs(message: Message):
    """Handle Logs button"""
    await cmd_get_logs(message)


@router.message(F.text == "🎬 Media Setup")
async def button_media_setup(message: Message):
    """Handle Media Setup button - redirect to media_setup handler"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    from src.handlers.media_setup import get_media_setup_keyboard
    
    await message.answer(
        "🎬 <b>Media Setup Menu</b>\n\n"
        "Configure media channels and categories for simulation.\n\n"
        "Choose an option:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )


@router.message(Command("queue_status"))
async def cmd_queue_status(message: Message):
    """Handle /queue_status command - show queued conversations"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not simulation_engine:
        await message.answer(
            "❌ Simulation features unavailable. Telethon not configured.")
        return

    queue_status = simulation_engine.get_queue_status()
    
    if not queue_status.get("has_queued"):
        await message.answer(
            "📋 <b>Queue Status</b>\n\n"
            "No conversations in queue.\n\n"
            "Conversations get queued when you try to run immediate simulations "
            "while the scheduler is active.",
            parse_mode=ParseMode.HTML
        )
        return
    
    status_text = f"📋 <b>Queue Status</b>\n\n"
    status_text += f"<b>Queued Conversations:</b> {queue_status.get('count')}\n\n"
    
    for item in queue_status.get("items", []):
        status_text += f"<b>#{item['position']}</b> — {item['name']}\n"
        if item.get('queued_at'):
            status_text += f"   ⏱️ Queued: {item['queued_at'][:16]}\n"
        if item.get('reason'):
            status_text += f"   📝 Reason: {item['reason']}\n"
        status_text += "\n"
    
    status_text += "These will auto-run after scheduled posts complete.\n"
    status_text += "Use /clear_queue to cancel all queued items."
    
    await message.answer(status_text, parse_mode=ParseMode.HTML)


@router.message(Command("clear_queue"))
async def cmd_clear_queue(message: Message):
    """Handle /clear_queue command - clear all queued conversations"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not db:
        await message.answer("❌ Database not initialized.")
        return

    queue_count = db.get_queue_count()
    
    if queue_count == 0:
        await message.answer(
            "📋 Queue is already empty. Nothing to clear.",
            parse_mode=ParseMode.HTML
        )
        return
    
    db.clear_queue()
    await message.answer(
        f"✅ <b>Queue Cleared</b>\n\n"
        f"Removed {queue_count} conversation(s) from the queue.",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("process_queue"))
async def cmd_process_queue(message: Message):
    """Handle /process_queue command - manually process next queued conversation"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return

    if not simulation_engine:
        await message.answer(
            "❌ Simulation features unavailable. Telethon not configured.")
        return

    queue_count = db.get_queue_count()
    if queue_count == 0:
        await message.answer("📋 No conversations in queue to process.")
        return

    # Check if scheduler is running
    if simulation_engine.scheduler_running:
        await message.answer(
            "⚠️ Cannot process queue while scheduler is running.\n"
            "Wait for scheduled posts to complete or use /stop_scheduler first."
        )
        return

    async def callback(msg: str):
        await message.answer(msg)

    await message.answer(f"🔄 Processing next queued conversation...")
    result = await simulation_engine.process_queue(admin_callback=callback)
    
    if not result.get("success"):
        await message.answer(f"❌ {result.get('message')}")
