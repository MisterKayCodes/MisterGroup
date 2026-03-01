# Made by Mister 💛
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
from bot.states.app_states import MediaStates
from data.repositories.media_repo import MediaRepository
from services.telegram.client_manager import TelegramService
from services.media.scan_service import MediaScanner
from core.calculators.media_parser import MediaParser

router = Router()

@router.message(F.text == "🎬 Media Setup")
async def cmd_media(message: Message, media_repo: MediaRepository):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📡 Add Source Channel", callback_data="media_add_channel"))
    builder.row(InlineKeyboardButton(text="📊 Manage Channels", callback_data="media_manage_channels"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="main_menu"))
    await message.answer("<b>🎬 Media Setup</b>\n\nChannels: <b>{}</b>".format(len(media_repo.get_all_channels())), reply_markup=builder.as_markup())

@router.callback_query(F.data == "media_add_channel")
async def start_add_channel(callback: CallbackQuery, state: FSMContext):
    await state.set_state(MediaStates.WAITING_FOR_CHANNEL)
    await callback.message.edit_text("📡 Send the <b>Channel @Username</b> or <b>Invite Link</b>:")
    await callback.answer()

@router.message(MediaStates.WAITING_FOR_CHANNEL)
async def process_channel_scan(message: Message, state: FSMContext, media_repo: MediaRepository, tg_service: TelegramService):
    ident = message.text.strip()
    if "t.me/" in ident: ident = "@" + ident.split("/")[-1]
    msg = await message.answer("🔄 Scanning channel... please wait.")
    try:
        sessions = tg_service.repo.get_all_sessions()
        active = [n for n, d in sessions.items() if d.get("status") == "active"]
        if not active: return await msg.edit_text("❌ No active sessions.")
        client = await tg_service.get_client(active[0])
        items = await MediaScanner.scan_channel(client, ident)
        media_repo.add_media_channel(ident, ident, items, invite_link=ident if "t.me/" in ident else None)
        await msg.edit_text(f"✅ <b>Channel Added!</b>\n📡 {ident}\n📊 Total items: {len(items)}")
        await state.clear()
    except Exception as e: await msg.edit_text(f"❌ Failed: {e}")

@router.callback_query(F.data == "media_manage_channels")
async def manage_channels(callback: CallbackQuery, media_repo: MediaRepository):
    channels = media_repo.get_all_channels()
    builder = InlineKeyboardBuilder()
    for ch in channels:
        builder.row(InlineKeyboardButton(text=f"📡 {ch['channel_username']}", callback_data=f"media_ch_view_{ch['id']}"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="media_main"))
    await callback.message.edit_text("📊 Registered Channels:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("media_ch_view_"))
async def view_channel(callback: CallbackQuery, media_repo: MediaRepository):
    ch_id = int(callback.data.split("_")[-1])
    cats = media_repo.get_all_categories(ch_id)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📁 Add Category Tag", callback_data=f"media_cat_add_{ch_id}"))
    for c in cats: builder.row(InlineKeyboardButton(text=f"🗑️ Delete {c['category_name']}", callback_data=f"media_cat_del_{c['id']}"))
    builder.row(InlineKeyboardButton(text="🛑 Delete Channel", callback_data=f"media_ch_del_{ch_id}"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="media_manage_channels"))
    await callback.message.edit_text(f"⚙️ Manage Channel #{ch_id}\nTags: <b>{len(cats)}</b>", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("media_cat_add_"))
async def start_add_cat(callback: CallbackQuery, state: FSMContext):
    ch_id = int(callback.data.split("_")[-1])
    await state.update_data(channel_id=ch_id)
    await state.set_state(MediaStates.WAITING_FOR_CATEGORIES)
    await callback.message.edit_text("✍️ Enter category: <code>TAG: START-END</code> (e.g. <code>BALANCE: 0-10</code>)")
    await callback.answer()

@router.message(MediaStates.WAITING_FOR_CATEGORIES)
async def save_cat(message: Message, state: FSMContext, media_repo: MediaRepository):
    ch_id = (await state.get_data())["channel_id"]
    cats = MediaParser.parse_category_ranges(message.text)
    if not cats: return await message.answer("❌ Invalid format.")
    for name, ranges in cats.items(): media_repo.add_category(name, ch_id, ranges)
    await message.answer(f"✅ {len(cats)} tags saved!")
    await state.clear()

@router.callback_query(F.data.startswith("media_cat_del_"))
async def del_cat(callback: CallbackQuery, media_repo: MediaRepository):
    cat_id = int(callback.data.split("_")[-1])
    # Find channel_id for redirection
    all_cats = media_repo.get_all_categories()
    ch_id = next((c["channel_id"] for c in all_cats if c["id"] == cat_id), None)
    media_repo.delete_category(cat_id)
    await callback.answer("✅ Category deleted.")
    if ch_id: 
        callback.data = f"media_ch_view_{ch_id}"
        await view_channel(callback, media_repo)
    else: await manage_channels(callback, media_repo)

@router.callback_query(F.data.startswith("media_ch_del_"))
async def del_ch(callback: CallbackQuery, media_repo: MediaRepository):
    media_repo.delete_channel(int(callback.data.split("_")[-1]))
    await callback.answer("✅ Channel deleted.")
    await manage_channels(callback, media_repo)

@router.callback_query(F.data == "media_main")
async def media_main_cb(callback: CallbackQuery, media_repo: MediaRepository):
    await cmd_media(callback.message, media_repo)
    await callback.answer()
