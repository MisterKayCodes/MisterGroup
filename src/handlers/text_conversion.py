# Made by Mister 💛

import re
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from src.utils.keyboards import (
    get_delay_range_keyboard, get_text_to_json_keyboard, get_main_menu_keyboard,
    get_schedule_type_keyboard, get_repeat_pattern_keyboard, get_add_more_batches_keyboard
)
from src.utils.text_to_json import parse_conversation_text, format_conversation_preview
from src.utils.database import Database
from src.models.conversation import ConversationData, ScheduledPeriod, Message as ConvMessage

router = Router()


class TextConversionStates(StatesGroup):
    waiting_for_delay_choice = State()
    waiting_for_schedule_type = State()
    waiting_for_time_input = State()
    waiting_for_batch_name = State()
    waiting_for_repeat_pattern = State()
    waiting_for_text = State()
    waiting_for_more_batches = State()


db: Database = None


def set_db(database: Database):
    """Set database instance"""
    global db
    db = database


async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    if not db:
        return False
    config = db.get_config()
    admin_id = config.get("admin_id")
    return admin_id == user_id if admin_id else False


def validate_time_format(time_str: str) -> bool:
    """Validate HH:MM time format"""
    try:
        parts = time_str.strip().split(':')
        if len(parts) != 2:
            return False
        hour, minute = int(parts[0]), int(parts[1])
        return 0 <= hour <= 23 and 0 <= minute <= 59
    except (ValueError, AttributeError):
        return False


def format_batches_preview(batches: list) -> str:
    """Format scheduled batches for preview"""
    if not batches:
        return "No batches scheduled yet."
    
    preview = "📋 <b>Scheduled Batches:</b>\n\n"
    for i, batch in enumerate(batches, 1):
        repeat_emoji = {
            "daily": "📅",
            "weekdays": "💼",
            "weekends": "🏖️",
            "once": "1️⃣"
        }.get(batch.get("repeat", "daily"), "📅")
        
        preview += f"{i}. <b>{batch.get('label', f'Batch {i}')}</b>\n"
        preview += f"   🕐 Time: {batch.get('time', 'Not set')} UTC\n"
        preview += f"   {repeat_emoji} Repeat: {batch.get('repeat', 'daily').title()}\n"
        preview += f"   💬 Messages: {batch.get('message_count', 0)}\n\n"
    
    return preview


@router.callback_query(F.data == "convert_text")
async def callback_convert_text(callback: CallbackQuery, state: FSMContext):
    """Start text conversion flow"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await state.clear()
    await state.set_state(TextConversionStates.waiting_for_delay_choice)
    
    await callback.message.answer(
        "📝 <b>Text-to-JSON Conversion</b>\n\n"
        "<b>Step 1/4:</b> Select message delay range\n\n"
        "🐇 <b>Fast (3-9s)</b> - Quick paced conversation\n"
        "🐢 <b>Normal (10-26s)</b> - Natural conversation flow\n"
        "🐌 <b>Slow (27-50s)</b> - Slow, thoughtful responses\n\n"
        "<i>This randomizes delays between messages</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_delay_range_keyboard()
    )


@router.callback_query(F.data.in_(["delay_fast", "delay_normal", "delay_slow"]))
async def callback_delay_choice(callback: CallbackQuery, state: FSMContext):
    """Handle delay range selection"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    speed = callback.data.replace("delay_", "")
    await state.update_data(delay_speed=speed, batches=[], is_scheduled=False)
    await state.set_state(TextConversionStates.waiting_for_schedule_type)
    
    speed_display = {"fast": "🐇 Fast", "normal": "🐢 Normal", "slow": "🐌 Slow"}
    
    await callback.message.answer(
        f"✅ Delay: {speed_display.get(speed, 'Normal')}\n\n"
        "<b>Step 2/4:</b> When should messages be sent?\n\n"
        "⚡ <b>Instant</b> - Run simulation immediately when you start it\n"
        "🕐 <b>Scheduled</b> - Set specific times (UTC) for automatic sending\n\n"
        "<i>Scheduled mode lets you create multiple time slots!</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_schedule_type_keyboard()
    )


@router.callback_query(F.data == "schedule_instant")
async def callback_schedule_instant(callback: CallbackQuery, state: FSMContext):
    """User chose instant mode"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await state.update_data(is_scheduled=False)
    await state.set_state(TextConversionStates.waiting_for_text)
    
    data = await state.get_data()
    speed = data.get("delay_speed", "normal")
    
    await callback.message.answer(
        f"⚡ <b>Instant Mode Selected</b>\n\n"
        f"<b>Step 3/4:</b> Send your conversation text\n\n"
        f"Format each line as:\n"
        f"<code>Name: Message content</code>\n\n"
        f"<b>Example:</b>\n"
        f"<code>AmySaunders: Did you see Bitcoin jumped 11%?\n"
        f"KevinMccarthy: Yeah, it's crazy!\n"
        f"LenaCrowde: Not a good sign.</code>\n\n"
        f"<i>Delays will be randomized ({speed} speed)</i>",
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "schedule_custom")
async def callback_schedule_custom(callback: CallbackQuery, state: FSMContext):
    """User chose scheduled mode"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await state.update_data(is_scheduled=True)
    await state.set_state(TextConversionStates.waiting_for_batch_name)
    
    data = await state.get_data()
    batches = data.get("batches", [])
    batch_num = len(batches) + 1
    
    preview = ""
    if batches:
        preview = f"\n{format_batches_preview(batches)}\n"
    
    await callback.message.answer(
        f"🕐 <b>Scheduled Mode</b>\n\n"
        f"{preview}"
        f"<b>Creating Batch #{batch_num}</b>\n\n"
        f"First, give this batch a name (e.g., 'Morning Chat', 'Market Discussion'):\n\n"
        f"<i>Just type the name and send it</i>",
        parse_mode=ParseMode.HTML
    )


@router.message(TextConversionStates.waiting_for_batch_name)
async def handle_batch_name(message: Message, state: FSMContext):
    """Handle batch name input"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    batch_name = message.text.strip()
    if not batch_name or len(batch_name) > 50:
        await message.answer("❌ Please enter a valid name (1-50 characters).")
        return
    
    await state.update_data(current_batch_name=batch_name)
    await state.set_state(TextConversionStates.waiting_for_time_input)
    
    now_utc = datetime.now(timezone.utc)
    current_time = now_utc.strftime("%H:%M")
    
    await message.answer(
        f"✅ Batch Name: <b>{batch_name}</b>\n\n"
        f"<b>Enter the time (UTC) for this batch:</b>\n\n"
        f"Format: <code>HH:MM</code> (24-hour)\n"
        f"Examples: <code>08:00</code>, <code>14:30</code>, <code>20:00</code>\n\n"
        f"🕐 Current UTC time: <code>{current_time}</code>\n\n"
        f"<i>The scheduler will trigger messages at this time</i>",
        parse_mode=ParseMode.HTML
    )


@router.message(TextConversionStates.waiting_for_time_input)
async def handle_time_input(message: Message, state: FSMContext):
    """Handle time input"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    time_str = message.text.strip()
    
    if not validate_time_format(time_str):
        await message.answer(
            "❌ Invalid time format!\n\n"
            "Please use <code>HH:MM</code> format (24-hour).\n"
            "Examples: <code>08:00</code>, <code>14:30</code>, <code>20:00</code>",
            parse_mode=ParseMode.HTML
        )
        return
    
    await state.update_data(current_batch_time=time_str)
    await state.set_state(TextConversionStates.waiting_for_repeat_pattern)
    
    data = await state.get_data()
    batch_name = data.get("current_batch_name", "Unnamed")
    
    await message.answer(
        f"✅ Time: <b>{time_str} UTC</b>\n\n"
        f"<b>How often should '{batch_name}' run?</b>\n\n"
        f"📅 <b>Daily</b> - Every day at {time_str}\n"
        f"💼 <b>Weekdays</b> - Monday to Friday\n"
        f"🏖️ <b>Weekends</b> - Saturday and Sunday\n"
        f"1️⃣ <b>Once</b> - Only once, then disabled",
        parse_mode=ParseMode.HTML,
        reply_markup=get_repeat_pattern_keyboard()
    )


@router.callback_query(F.data.in_(["repeat_daily", "repeat_weekdays", "repeat_weekends", "repeat_once"]))
async def callback_repeat_pattern(callback: CallbackQuery, state: FSMContext):
    """Handle repeat pattern selection"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    repeat = callback.data.replace("repeat_", "")
    await state.update_data(current_batch_repeat=repeat)
    await state.set_state(TextConversionStates.waiting_for_text)
    
    data = await state.get_data()
    batch_name = data.get("current_batch_name", "Unnamed")
    batch_time = data.get("current_batch_time", "00:00")
    speed = data.get("delay_speed", "normal")
    
    repeat_display = {
        "daily": "📅 Daily",
        "weekdays": "💼 Weekdays",
        "weekends": "🏖️ Weekends",
        "once": "1️⃣ Once"
    }
    
    await callback.message.answer(
        f"✅ <b>Batch Configuration Complete!</b>\n\n"
        f"📌 Name: {batch_name}\n"
        f"🕐 Time: {batch_time} UTC\n"
        f"{repeat_display.get(repeat, 'Daily')}\n\n"
        f"<b>Now send the conversation text for this batch:</b>\n\n"
        f"<code>AmySaunders: Did you see Bitcoin jumped 11%?\n"
        f"KevinMccarthy: Yeah, it's crazy!\n"
        f"LenaCrowde: Not a good sign.</code>\n\n"
        f"<i>Delays will be randomized ({speed} speed)</i>",
        parse_mode=ParseMode.HTML
    )


@router.message(TextConversionStates.waiting_for_text)
async def handle_conversion_text(message: Message, state: FSMContext):
    """Handle text input for conversion"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied.")
        return
    
    text = message.text.strip()
    if not text:
        await message.answer("❌ Please send the conversation text.")
        return
    
    data = await state.get_data()
    delay_speed = data.get("delay_speed", "normal")
    is_scheduled = data.get("is_scheduled", False)
    
    try:
        conversation = parse_conversation_text(text, delay_speed)
        messages = conversation.get("messages", [])
        
        if not messages:
            await message.answer(
                "❌ No valid messages found!\n\n"
                "Make sure each line follows: <code>Name: Message</code>",
                parse_mode=ParseMode.HTML
            )
            return
        
        participants = set(msg["sender_name"] for msg in messages)
        
        if is_scheduled:
            batch_name = data.get("current_batch_name", "Unnamed Batch")
            batch_time = data.get("current_batch_time", "12:00")
            batch_repeat = data.get("current_batch_repeat", "daily")
            
            batches = data.get("batches", [])
            batches.append({
                "label": batch_name,
                "time": batch_time,
                "repeat": batch_repeat,
                "messages": messages,
                "message_count": len(messages),
                "participants": list(participants)
            })
            
            await state.update_data(batches=batches)
            await state.set_state(TextConversionStates.waiting_for_more_batches)
            
            preview = format_batches_preview(batches)
            
            await message.answer(
                f"✅ <b>Batch Added!</b>\n\n"
                f"{preview}\n"
                f"Would you like to add another time slot or save now?",
                parse_mode=ParseMode.HTML,
                reply_markup=get_add_more_batches_keyboard()
            )
        else:
            try:
                conversation_obj = ConversationData(**conversation)
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                await message.answer(f"❌ Validation error: {str(e)}", parse_mode=ParseMode.HTML)
                await state.clear()
                return
            
            all_sessions = db.get_all_sessions()
            session_names = set(all_sessions.keys())
            missing = participants - session_names
            
            warning = ""
            if missing:
                warning = f"\n\n⚠️ Missing sessions: {', '.join(list(missing)[:5])}"
            
            # Check for media tags and validate categories
            media_tag_warning = ""
            try:
                from src.database.media_tables import MediaDatabase
                from src.utils.media_parser import validate_media_tags_in_messages
                
                media_db = MediaDatabase()
                tag_validation = validate_media_tags_in_messages(messages, media_db)
                
                if tag_validation['warning_message']:
                    media_tag_warning = f"\n\n{tag_validation['warning_message']}"
            except Exception as e:
                logger.debug(f"Media tag validation skipped: {e}")
            
            db.set_conversation(conversation_obj.model_dump(mode='json'))
            
            await message.answer(
                f"✅ <b>Conversation Saved (Instant Mode)</b>\n\n"
                f"📊 Messages: {len(messages)}\n"
                f"👥 Participants: {len(participants)}\n"
                f"⏱️ Delay: {delay_speed.title()}{warning}{media_tag_warning}\n\n"
                f"Use <b>/start_simulation</b> to run now!",
                parse_mode=ParseMode.HTML,
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            
    except ValueError as e:
        logger.error(f"Parse error: {e}")
        await message.answer(
            f"❌ Error: {str(e)}\n\nCheck format: <code>Name: Message</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        await message.answer(f"❌ Unexpected error: {str(e)}")
        await state.clear()


@router.callback_query(F.data == "add_more_batch")
async def callback_add_more_batch(callback: CallbackQuery, state: FSMContext):
    """Add another time slot"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    await state.set_state(TextConversionStates.waiting_for_batch_name)
    
    data = await state.get_data()
    batches = data.get("batches", [])
    batch_num = len(batches) + 1
    
    preview = format_batches_preview(batches)
    
    await callback.message.answer(
        f"{preview}\n"
        f"<b>Adding Batch #{batch_num}</b>\n\n"
        f"Enter a name for this batch:",
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data == "save_batches")
async def callback_save_batches(callback: CallbackQuery, state: FSMContext):
    """Save all scheduled batches"""
    await callback.answer()
    
    if not await is_admin(callback.from_user.id):
        await callback.message.answer("❌ Access denied.")
        return
    
    data = await state.get_data()
    batches = data.get("batches", [])
    
    if not batches:
        await callback.message.answer("❌ No batches to save!")
        await state.clear()
        return
    
    try:
        schedule = []
        all_participants = set()
        
        for batch in batches:
            period = ScheduledPeriod(
                time=batch["time"],
                label=batch["label"],
                participants=batch.get("participants", "all"),
                messages=[ConvMessage(**msg) for msg in batch["messages"]],
                repeat=batch["repeat"],
                enabled=True
            )
            schedule.append(period)
            all_participants.update(batch.get("participants", []))
        
        conversation = ConversationData(
            name="Scheduled Conversation",
            description=f"Auto-generated with {len(batches)} scheduled batches",
            mode="scheduled",
            messages=[],
            schedule=schedule
        )
        
        db.set_conversation(conversation.model_dump(mode='json'))
        
        all_sessions = db.get_all_sessions()
        session_names = set(all_sessions.keys())
        missing = all_participants - session_names
        
        warning = ""
        if missing:
            warning = f"\n\n⚠️ Missing sessions: {', '.join(list(missing)[:5])}"
        
        # Check for media tags and validate categories
        media_tag_warning = ""
        try:
            from src.database.media_tables import MediaDatabase
            from src.utils.media_parser import validate_scheduled_media_tags
            
            media_db = MediaDatabase()
            tag_validation = validate_scheduled_media_tags(batches, media_db)
            
            if tag_validation['warning_message']:
                media_tag_warning = f"\n\n{tag_validation['warning_message']}"
        except Exception as e:
            logger.debug(f"Media tag validation skipped: {e}")
        
        total_messages = sum(b["message_count"] for b in batches)
        
        await callback.message.answer(
            f"✅ <b>Scheduled Conversation Saved!</b>\n\n"
            f"📊 Total Batches: {len(batches)}\n"
            f"💬 Total Messages: {total_messages}\n"
            f"👥 Participants: {len(all_participants)}{warning}{media_tag_warning}\n\n"
            f"<b>Scheduled Times:</b>\n" +
            "\n".join([f"• {b['time']} UTC - {b['label']}" for b in batches]) +
            f"\n\n🚀 Use <b>/start_scheduler</b> to activate!\n"
            f"📋 Use <b>/schedule_status</b> to view all batches.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_main_menu_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error saving batches: {e}", exc_info=True)
        await callback.message.answer(f"❌ Error saving: {str(e)}")
        await state.clear()


@router.callback_query(F.data == "convert_help")
async def callback_convert_help(callback: CallbackQuery):
    """Show conversion help"""
    await callback.answer()
    
    help_text = """
📘 <b>Text-to-JSON Conversion Guide</b>

<b>Two Modes Available:</b>

⚡ <b>Instant Mode</b>
Run the conversation immediately when you start simulation.

🕐 <b>Scheduled Mode</b>
Set specific times for automatic sending. You can:
• Create multiple time slots (batches)
• Name each batch (e.g., "Morning Chat")
• Set repeat patterns (daily, weekdays, etc.)
• All times are in UTC

<b>Text Format:</b>
<code>Name: Message content</code>

<b>Example:</b>
<code>AmySaunders: Bitcoin jumped 11%!
KevinMccarthy: That's crazy!
LenaCrowde: Not a good sign.</code>

<b>Delay Ranges:</b>
🐇 Fast: 3-9 seconds
🐢 Normal: 10-26 seconds
🐌 Slow: 27-50 seconds

<b>Repeat Patterns:</b>
📅 Daily - Every day
💼 Weekdays - Mon-Fri
🏖️ Weekends - Sat-Sun
1️⃣ Once - Single execution
"""
    
    await callback.message.answer(
        help_text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_text_to_json_keyboard()
    )


@router.callback_query(F.data == "convert_cancel")
async def callback_convert_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel conversion"""
    await callback.answer("Cancelled")
    await state.clear()
    
    await callback.message.answer(
        "❌ Conversion cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
