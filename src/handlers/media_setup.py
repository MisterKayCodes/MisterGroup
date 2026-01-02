# Made by Mister 💛

import asyncio
from typing import Optional
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from loguru import logger

from src.utils.database import Database
from src.database.media_tables import MediaDatabase
from src.utils.media_parser import (
    parse_category_ranges, format_ranges_display, 
    scan_channel_media_telethon
)
from src.services.session_manager import SessionManager

router = Router()

db: Optional[Database] = None
media_db: Optional[MediaDatabase] = None
session_manager: Optional[SessionManager] = None
admin_id: Optional[int] = None


class MediaSetupStates(StatesGroup):
    waiting_for_channel = State()
    waiting_for_categories = State()
    selecting_channel_for_categories = State()


def set_media_dependencies(
    database: Database,
    media_database: MediaDatabase,
    sess_manager: Optional[SessionManager] = None,
    admin_user_id: Optional[int] = None
):
    """Set global dependencies for media setup handlers"""
    global db, media_db, session_manager, admin_id
    db = database
    media_db = media_database
    session_manager = sess_manager
    admin_id = admin_user_id


async def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    global admin_id
    if db:
        config = db.get_config()
        db_admin_id = config.get("admin_id")
        if db_admin_id is not None:
            admin_id = db_admin_id
            return user_id == db_admin_id
    return admin_id is not None and user_id == admin_id


def get_media_setup_keyboard() -> InlineKeyboardMarkup:
    """Get main media setup menu keyboard"""
    buttons = [
        [InlineKeyboardButton(text="📡 Add New Media Channel", callback_data="media_add_channel")],
        [InlineKeyboardButton(text="📁 Manage Categories", callback_data="media_manage_categories")],
        [InlineKeyboardButton(text="📋 View Categories", callback_data="media_view_categories")],
        [InlineKeyboardButton(text="🗑️ Delete Category", callback_data="media_delete_category")],
        [InlineKeyboardButton(text="📊 View Channels", callback_data="media_view_channels")],
        [InlineKeyboardButton(text="❌ Exit", callback_data="media_exit")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_channel_selection_keyboard(channels: list, action: str) -> InlineKeyboardMarkup:
    """Get keyboard for selecting a channel"""
    buttons = []
    for ch in channels:
        name = ch['channel_username'] or ch['channel_id']
        count = len(ch['media_items'])
        buttons.append([InlineKeyboardButton(
            text=f"📡 {name} ({count} items)",
            callback_data=f"media_select_ch_{action}_{ch['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="media_setup_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_category_list_keyboard(categories: list, action: str) -> InlineKeyboardMarkup:
    """Get keyboard for category actions"""
    buttons = []
    for cat in categories:
        ranges_str = format_ranges_display(cat['index_ranges'])
        buttons.append([InlineKeyboardButton(
            text=f"📁 {cat['category_name']} ({ranges_str})",
            callback_data=f"media_cat_{action}_{cat['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="media_setup_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


QUICK_TEMPLATES = {
    "BALANCE": {"emoji": "💰", "desc": "Balance screenshots"},
    "DEPOSIT": {"emoji": "📥", "desc": "Deposit confirmations"},
    "PROFIT": {"emoji": "📈", "desc": "Profit/earnings proofs"},
    "LIFESTYLE": {"emoji": "🌴", "desc": "Lifestyle/luxury content"},
}


def get_quick_template_keyboard(channel_id: int, item_count: int) -> InlineKeyboardMarkup:
    """Get keyboard for quick category templates"""
    buttons = []
    
    for template_name, info in QUICK_TEMPLATES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{info['emoji']} {template_name} (auto-range)",
            callback_data=f"media_quick_{template_name}_{channel_id}"
        )])
    
    buttons.append([InlineKeyboardButton(
        text="🎯 Create All 4 Templates",
        callback_data=f"media_quick_ALL_{channel_id}"
    )])
    
    buttons.append([InlineKeyboardButton(
        text="✏️ Custom Categories",
        callback_data=f"media_custom_cat_{channel_id}"
    )])
    
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="media_manage_categories")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("media_setup"))
async def cmd_media_setup(message: Message, state: FSMContext):
    """Handle /media_setup command - main entry point"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied. Only admin can use this command.")
        return
    
    await state.clear()
    
    await message.answer(
        "🎬 <b>Media Setup Menu</b>\n\n"
        "Configure media channels and categories for simulation.\n\n"
        "Choose an option:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )


@router.callback_query(F.data == "media_setup_menu")
async def callback_media_setup_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main media setup menu"""
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        "🎬 <b>Media Setup Menu</b>\n\n"
        "Configure media channels and categories for simulation.\n\n"
        "Choose an option:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )


@router.callback_query(F.data == "media_exit")
async def callback_media_exit(callback: CallbackQuery, state: FSMContext):
    """Exit media setup"""
    await callback.answer("Exited media setup")
    await state.clear()
    await callback.message.edit_text("✅ Media setup closed.")


@router.callback_query(F.data == "media_add_channel")
async def callback_add_channel(callback: CallbackQuery, state: FSMContext):
    """Start add channel flow"""
    await callback.answer()
    
    if not session_manager:
        await callback.message.edit_text(
            "❌ Telethon not configured. API_ID and API_HASH required for channel scanning.\n\n"
            "Please configure these in your .env file.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Back", callback_data="media_setup_menu")]
            ])
        )
        return
    
    await state.set_state(MediaSetupStates.waiting_for_channel)
    
    await callback.message.edit_text(
        "📡 <b>Add Media Channel</b>\n\n"
        "Send the channel identifier:\n"
        "• Username: @channelname\n"
        "• Channel ID: -1001234567890\n"
        "• Invite link: https://t.me/channelname\n\n"
        "⚠️ The bot must be able to access this channel.\n\n"
        "<i>Send the channel identifier or /cancel to abort</i>",
        parse_mode=ParseMode.HTML
    )


@router.message(MediaSetupStates.waiting_for_channel)
async def handle_channel_input(message: Message, state: FSMContext):
    """Handle channel identifier input"""
    if not await is_admin(message.from_user.id):
        return
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Cancelled.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    channel_input = message.text.strip()
    
    if channel_input.startswith("https://t.me/"):
        channel_input = "@" + channel_input.split("/")[-1]
    
    await message.answer("🔄 Scanning channel for media... This may take a moment.")
    
    try:
        sessions = session_manager.list_sessions()
        if not sessions:
            await message.answer(
                "❌ No Telethon sessions available. Please add sessions first with /add_session",
                reply_markup=get_media_setup_keyboard()
            )
            await state.clear()
            return
        
        client = None
        for sess in sessions:
            if sess.get('status') == 'active':
                client = await session_manager.get_client(sess['name'])
                if client:
                    break
        
        if not client:
            await message.answer(
                "❌ No active Telethon sessions. Please test your sessions with /test_session",
                reply_markup=get_media_setup_keyboard()
            )
            await state.clear()
            return
        
        try:
            if channel_input.startswith('@'):
                entity = await client.get_entity(channel_input)
            else:
                entity = await client.get_entity(int(channel_input))
            
            channel_username = getattr(entity, 'username', None)
            channel_title = getattr(entity, 'title', str(entity.id))
            channel_id = str(entity.id)
            
        except Exception as e:
            await message.answer(
                f"❌ Cannot access channel: {e}\n\n"
                "Make sure the session account can access this channel.",
                reply_markup=get_media_setup_keyboard()
            )
            await state.clear()
            return
        
        await message.answer(f"📡 Found: {channel_title}\n🔄 Scanning media...")
        
        media_items = await scan_channel_media_telethon(client, channel_input, limit=500)
        
        if not media_items:
            await message.answer(
                "❌ No media found in this channel.\n\n"
                "The channel may be empty or contain only text messages.",
                reply_markup=get_media_setup_keyboard()
            )
            await state.clear()
            return
        
        channel_db_id = media_db.add_media_channel(
            channel_id=channel_id,
            channel_username=channel_username or channel_title,
            media_items=media_items
        )
        
        photo_count = sum(1 for m in media_items if m.get('media_type') == 'photo')
        video_count = sum(1 for m in media_items if m.get('media_type') == 'video')
        album_count = len(set(m.get('media_group') for m in media_items if m.get('media_group')))
        
        await message.answer(
            f"✅ <b>Channel Added Successfully!</b>\n\n"
            f"📡 Channel: {channel_title}\n"
            f"🆔 ID: {channel_id}\n\n"
            f"<b>Media Found:</b>\n"
            f"📷 Photos: {photo_count}\n"
            f"🎬 Videos: {video_count}\n"
            f"📦 Albums: {album_count}\n"
            f"📊 Total Items: {len(media_items)}\n\n"
            f"You can now create categories with /media_setup → Manage Categories",
            parse_mode=ParseMode.HTML,
            reply_markup=get_media_setup_keyboard()
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error scanning channel: {e}", exc_info=True)
        await message.answer(
            f"❌ Error scanning channel: {str(e)}",
            reply_markup=get_media_setup_keyboard()
        )
        await state.clear()


@router.callback_query(F.data == "media_view_channels")
async def callback_view_channels(callback: CallbackQuery):
    """View all registered channels"""
    await callback.answer()
    
    channels = media_db.get_all_media_channels()
    
    if not channels:
        await callback.message.edit_text(
            "📡 <b>No Media Channels</b>\n\n"
            "No channels have been added yet.\n"
            "Use 'Add New Media Channel' to get started.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    text = "📡 <b>Registered Media Channels</b>\n\n"
    
    for ch in channels:
        name = ch['channel_username'] or ch['channel_id']
        items = ch['media_items']
        photo_count = sum(1 for m in items if m.get('media_type') == 'photo')
        video_count = sum(1 for m in items if m.get('media_type') == 'video')
        
        text += f"<b>{name}</b>\n"
        text += f"  📷 {photo_count} photos, 🎬 {video_count} videos\n"
        text += f"  📊 Total: {len(items)} items\n"
        text += f"  📅 Scanned: {ch['scanned_at'][:10]}\n\n"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )


@router.callback_query(F.data == "media_manage_categories")
async def callback_manage_categories(callback: CallbackQuery, state: FSMContext):
    """Start category management flow"""
    await callback.answer()
    
    channels = media_db.get_all_media_channels()
    
    if not channels:
        await callback.message.edit_text(
            "❌ No channels available.\n\n"
            "Add a media channel first before creating categories.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "📁 <b>Manage Categories</b>\n\n"
        "Select a channel to create categories for:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_channel_selection_keyboard(channels, "create")
    )


@router.callback_query(F.data.startswith("media_select_ch_create_"))
async def callback_select_channel_for_categories(callback: CallbackQuery, state: FSMContext):
    """Handle channel selection for category creation - show quick templates"""
    await callback.answer()
    
    channel_id = int(callback.data.split("_")[-1])
    channel = media_db.get_media_channel(channel_id)
    
    if not channel:
        await callback.message.edit_text(
            "❌ Channel not found.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    await state.update_data(selected_channel_id=channel_id)
    item_count = len(channel['media_items'])
    
    await callback.message.edit_text(
        f"📁 <b>Create Categories</b>\n\n"
        f"📡 Channel: {channel['channel_username'] or channel['channel_id']}\n"
        f"📊 Media items: {item_count}\n\n"
        f"<b>Quick Templates:</b>\n"
        f"One-tap buttons auto-assign ranges based on your media count.\n\n"
        f"💰 BALANCE - Balance screenshots\n"
        f"📥 DEPOSIT - Deposit confirmations\n"
        f"📈 PROFIT - Profit/earnings proofs\n"
        f"🌴 LIFESTYLE - Lifestyle/luxury content\n\n"
        f"<i>Select a template or use custom for manual setup:</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=get_quick_template_keyboard(channel_id, item_count)
    )


@router.message(MediaSetupStates.waiting_for_categories)
async def handle_categories_input(message: Message, state: FSMContext):
    """Handle category definitions input"""
    if not await is_admin(message.from_user.id):
        return
    
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Cancelled.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    data = await state.get_data()
    channel_id = data.get('selected_channel_id')
    
    if not channel_id:
        await state.clear()
        await message.answer(
            "❌ Session expired. Please start over.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    channel = media_db.get_media_channel(channel_id)
    if not channel:
        await state.clear()
        await message.answer(
            "❌ Channel not found.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    categories = parse_category_ranges(message.text)
    
    if not categories:
        await message.answer(
            "❌ No valid categories found.\n\n"
            "Please use format: CATEGORY_NAME: start-end\n"
            "Example: BALANCE: 0-20"
        )
        return
    
    max_index = len(channel['media_items']) - 1
    valid_categories = []
    warnings = []
    
    for name, ranges in categories.items():
        adjusted_ranges = []
        for start, end in ranges:
            if start > max_index:
                warnings.append(f"{name}: Range {start}-{end} exceeds max index {max_index}")
                continue
            if end > max_index:
                end = max_index
                warnings.append(f"{name}: Adjusted end to {max_index}")
            adjusted_ranges.append([start, end])
        
        if adjusted_ranges:
            media_db.add_category(name, channel_id, adjusted_ranges)
            valid_categories.append((name, adjusted_ranges))
    
    if not valid_categories:
        await message.answer(
            "❌ No valid categories could be created.\n"
            "All ranges were out of bounds."
        )
        return
    
    result = "✅ <b>Categories Saved!</b>\n\n"
    for name, ranges in valid_categories:
        ranges_str = format_ranges_display(ranges)
        result += f"📁 {name} ({ranges_str})\n"
    
    if warnings:
        result += f"\n⚠️ Warnings:\n"
        for w in warnings[:5]:
            result += f"• {w}\n"
    
    result += f"\n<i>Categories are ready for use in simulations!</i>"
    
    await message.answer(
        result,
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data == "media_view_categories")
async def callback_view_categories(callback: CallbackQuery):
    """View all categories"""
    await callback.answer()
    
    categories = media_db.get_all_categories()
    
    if not categories:
        await callback.message.edit_text(
            "📁 <b>No Categories</b>\n\n"
            "No categories have been created yet.\n"
            "Use 'Manage Categories' to create some.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    text = "📁 <b>Media Categories</b>\n\n"
    
    for cat in categories:
        ranges_str = format_ranges_display(cat['index_ranges'])
        stats = media_db.get_category_stats(cat['id'])
        
        text += f"<b>[{cat['category_name']}]</b>\n"
        text += f"  📡 Channel: {cat.get('channel_username', 'Unknown')}\n"
        text += f"  📊 Indices: {ranges_str}\n"
        text += f"  🔄 Pointer: {cat['current_pointer']}\n"
        text += f"  ✅ Sent: {stats['successful']} | ❌ Failed: {stats['failed']}\n\n"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )


@router.callback_query(F.data == "media_delete_category")
async def callback_delete_category_menu(callback: CallbackQuery):
    """Show categories for deletion"""
    await callback.answer()
    
    categories = media_db.get_all_categories()
    
    if not categories:
        await callback.message.edit_text(
            "📁 <b>No Categories</b>\n\n"
            "No categories to delete.",
            parse_mode=ParseMode.HTML,
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    await callback.message.edit_text(
        "🗑️ <b>Delete Category</b>\n\n"
        "Select a category to delete:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_category_list_keyboard(categories, "delete")
    )


@router.callback_query(F.data.startswith("media_cat_delete_"))
async def callback_confirm_delete_category(callback: CallbackQuery):
    """Delete a category"""
    await callback.answer()
    
    category_id = int(callback.data.split("_")[-1])
    category = media_db.get_category_by_id(category_id)
    
    if not category:
        await callback.message.edit_text(
            "❌ Category not found.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    media_db.delete_category(category_id)
    
    await callback.message.edit_text(
        f"✅ Category <b>{category['category_name']}</b> deleted.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )


@router.callback_query(F.data.startswith("media_cat_reset_"))
async def callback_reset_category_pointer(callback: CallbackQuery):
    """Reset a category pointer"""
    await callback.answer()
    
    category_id = int(callback.data.split("_")[-1])
    category = media_db.get_category_by_id(category_id)
    
    if not category:
        await callback.message.edit_text(
            "❌ Category not found.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    media_db.reset_category_pointer(category_id)
    
    await callback.message.edit_text(
        f"✅ Category <b>{category['category_name']}</b> pointer reset to 0.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_media_setup_keyboard()
    )


def find_contiguous_segments(available_indices: list) -> list:
    """Find contiguous segments from a list of indices"""
    if not available_indices:
        return []
    
    segments = []
    start = available_indices[0]
    prev = start
    
    for idx in available_indices[1:]:
        if idx != prev + 1:
            segments.append((start, prev))
            start = idx
        prev = idx
    
    segments.append((start, prev))
    return segments


@router.callback_query(F.data.startswith("media_quick_"))
async def callback_quick_template(callback: CallbackQuery, state: FSMContext):
    """Handle quick template category creation"""
    await callback.answer()
    
    parts = callback.data.split("_")
    template_name = parts[2]
    channel_id = int(parts[3])
    
    channel = media_db.get_media_channel(channel_id)
    if not channel:
        await callback.message.edit_text(
            "❌ Channel not found.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    item_count = len(channel['media_items'])
    
    if item_count < 4:
        await callback.message.edit_text(
            f"❌ Not enough media items ({item_count}).\n\n"
            f"Need at least 4 items for quick templates.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    if template_name == "ALL":
        existing_cats = media_db.get_all_categories(channel_id)
        
        if existing_cats:
            existing_names = [c['category_name'] for c in existing_cats]
            await callback.message.edit_text(
                f"⚠️ <b>Existing categories found:</b>\n"
                f"{', '.join(existing_names)}\n\n"
                f"Please delete existing categories first before using 'Create All'.\n"
                f"This prevents accidental data loss.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_media_setup_keyboard()
            )
            return
        
        template_count = len(QUICK_TEMPLATES)
        items_per_category = item_count // template_count
        created = []
        
        for i, (name, info) in enumerate(QUICK_TEMPLATES.items()):
            start = i * items_per_category
            end = (i + 1) * items_per_category - 1 if i < template_count - 1 else item_count - 1
            
            if start <= end:
                media_db.add_category(name, channel_id, [[start, end]])
                created.append(f"{info['emoji']} {name}: {start}-{end}")
        
        if not created:
            await callback.message.edit_text(
                "❌ Could not create any categories.",
                reply_markup=get_media_setup_keyboard()
            )
            return
        
        result = "✅ <b>All Templates Created!</b>\n\n"
        for cat_info in created:
            result += f"{cat_info}\n"
        result += f"\n📊 Total items: {item_count}\n"
        result += f"\n<i>Categories are ready for use in simulations!</i>"
        
        await state.clear()
        
        await callback.message.edit_text(
            result,
            parse_mode=ParseMode.HTML,
            reply_markup=get_media_setup_keyboard()
        )
    else:
        if template_name not in QUICK_TEMPLATES:
            await callback.message.edit_text(
                "❌ Unknown template.",
                reply_markup=get_media_setup_keyboard()
            )
            return
        
        info = QUICK_TEMPLATES[template_name]
        existing_cats = media_db.get_all_categories(channel_id)
        existing_names = [c['category_name'] for c in existing_cats]
        
        if template_name in existing_names:
            await callback.message.edit_text(
                f"⚠️ Category <b>{template_name}</b> already exists for this channel.\n\n"
                f"Delete it first if you want to recreate it.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_media_setup_keyboard()
            )
            return
        
        used_indices = set()
        for cat in existing_cats:
            for start, end in cat['index_ranges']:
                used_indices.update(range(start, end + 1))
        
        available_indices = sorted([i for i in range(item_count) if i not in used_indices])
        
        if not available_indices:
            await callback.message.edit_text(
                f"❌ No available indices left for new categories.\n\n"
                f"All {item_count} items are already assigned to categories.",
                reply_markup=get_media_setup_keyboard()
            )
            return
        
        segments = find_contiguous_segments(available_indices)
        
        if not segments:
            await callback.message.edit_text(
                "❌ No contiguous range available for new category.",
                reply_markup=get_media_setup_keyboard()
            )
            return
        
        largest_segment = max(segments, key=lambda s: s[1] - s[0] + 1)
        segment_start, segment_end = largest_segment
        segment_size = segment_end - segment_start + 1
        
        items_to_assign = min(segment_size, max(1, item_count // 4))
        
        start = segment_start
        end = segment_start + items_to_assign - 1
        
        media_db.add_category(template_name, channel_id, [[start, end]])
        
        await state.clear()
        
        await callback.message.edit_text(
            f"✅ <b>Category Created!</b>\n\n"
            f"{info['emoji']} <b>{template_name}</b>\n"
            f"📊 Range: {start}-{end}\n"
            f"📁 Items: {end - start + 1}\n\n"
            f"<i>Category is ready for use in simulations!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=get_media_setup_keyboard()
        )


@router.callback_query(F.data.startswith("media_custom_cat_"))
async def callback_custom_categories(callback: CallbackQuery, state: FSMContext):
    """Handle custom category creation - manual input flow"""
    await callback.answer()
    
    channel_id = int(callback.data.split("_")[-1])
    channel = media_db.get_media_channel(channel_id)
    
    if not channel:
        await callback.message.edit_text(
            "❌ Channel not found.",
            reply_markup=get_media_setup_keyboard()
        )
        return
    
    await state.update_data(selected_channel_id=channel_id)
    await state.set_state(MediaSetupStates.waiting_for_categories)
    
    item_count = len(channel['media_items'])
    
    await callback.message.edit_text(
        f"📁 <b>Custom Categories</b>\n\n"
        f"Channel: {channel['channel_username'] or channel['channel_id']}\n"
        f"Available indices: 0 to {item_count - 1}\n\n"
        f"<b>Enter categories in this format:</b>\n"
        f"<code>BALANCE: 0-20\n"
        f"DEPOSIT: 21-40\n"
        f"WITHDRAW: 41-60</code>\n\n"
        f"Each line: CATEGORY_NAME: start-end\n"
        f"You can also use comma-separated ranges:\n"
        f"<code>MIXED: 0-10, 50-60</code>\n\n"
        f"<i>Send your category definitions or /cancel</i>",
        parse_mode=ParseMode.HTML
    )


@router.message(Command("media_help"))
async def cmd_media_help(message: Message):
    """Handle /media_help command - show visual guide and current status"""
    if not await is_admin(message.from_user.id):
        await message.answer("❌ Access denied. Only admin can use this command.")
        return
    
    categories = media_db.get_all_categories() if media_db else []
    channels = media_db.get_all_media_channels() if media_db else []
    
    step1_status = "✅" if channels else "⬜"
    step2_status = "✅" if categories else "⬜"
    step3_status = "✅" if (channels and categories) else "⬜"
    
    status_section = ""
    if categories:
        status_section = "\n\n📊 <b>Current Categories:</b>\n"
        for cat in categories:
            ranges_str = format_ranges_display(cat['index_ranges'])
            stats = media_db.get_category_stats(cat['id'])
            status_section += f"  [{cat['category_name']}] → {ranges_str} (used: {stats['successful']}x)\n"
    else:
        status_section = "\n\n⚠️ <b>No categories configured yet</b>\n"
    
    if channels:
        status_section += "\n📡 <b>Media Channels:</b>\n"
        for ch in channels:
            name = ch['channel_username'] or ch['channel_id']
            count = len(ch['media_items'])
            status_section += f"  • {name} ({count} items)\n"
    
    help_text = f"""
📖 <b>Media System Guide</b>

The media system lets you attach images/videos from channels to your simulated messages using [TAGS].

━━━━━━━━━━━━━━━━━━━━━━━━

<b>🔧 SETUP STEPS</b>

{step1_status} <b>Step 1: Add Media Channel</b>
   Run /media_setup → Add New Media Channel
   Enter your channel @username or ID
   The bot scans and stores all media

{step2_status} <b>Step 2: Create Categories</b>
   Run /media_setup → Manage Categories
   Select your channel
   Use Quick Templates or Custom ranges
   Example: BALANCE: 0-20 (uses items 0-20)

{step3_status} <b>Step 3: Use Tags in Messages</b>
   Add [CATEGORYNAME] in your conversation text:
   <code>AmySaunders: Check my gains! [PROFIT]</code>
   <code>KevinMccarthy: Just deposited [DEPOSIT]</code>

━━━━━━━━━━━━━━━━━━━━━━━━

<b>📝 EXAMPLE WORKFLOW</b>

1️⃣ You have a channel with 100 screenshots
2️⃣ Create categories:
   • BALANCE: 0-30 (balance screenshots)
   • PROFIT: 31-60 (profit images)
   • LIFESTYLE: 61-99 (lifestyle pics)

3️⃣ In your conversation:
   <code>Amy: My account balance [BALANCE]</code>
   → Bot picks next image from items 0-30

4️⃣ Categories cycle through media:
   First use → item 0
   Second use → item 1
   ...and so on (loops back to start)

━━━━━━━━━━━━━━━━━━━━━━━━

<b>🎯 QUICK TEMPLATES</b>

One-tap buttons auto-divide your media:
💰 BALANCE - Balance screenshots
📥 DEPOSIT - Deposit confirmations  
📈 PROFIT - Profit/earnings proofs
🌴 LIFESTYLE - Lifestyle content
{status_section}
━━━━━━━━━━━━━━━━━━━━━━━━

<b>🔗 COMMANDS</b>

/media_setup - Configure channels & categories
/media_help - This guide

<i>💡 Tip: Run /media_setup to get started!</i>
"""
    
    await message.answer(
        help_text,
        parse_mode=ParseMode.HTML
    )
