# Made by Mister 💛
import json
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from loguru import logger

from bot.states.app_states import SimulationStates
from bot.keyboards.main_menu import get_main_menu_keyboard
from data.repositories.config_repo import ConfigRepository
from services.coordinator.simulation_coordinator import SimulationCoordinator
from core.models.enums import TypingSpeed
from core.calculators.text_parser import TextParser

router = Router()

@router.message(F.text == "🚀 Run Now")
async def cmd_simulation(message: Message, config_repo: ConfigRepository, coordinator: SimulationCoordinator):
    """The 'Mouth' shows current simulation status from the Vault."""
    is_running = coordinator.state.is_running
    status_emoji = "🟢 RUNNING" if is_running else "⚪ IDLE"
    
    conv_data = config_repo.get_conversation()
    name = conv_data.get("name", "<i>None</i>") if conv_data else "<i>None</i>"
    
    text = (
        f"<b>🚀 Simulation Control</b>\n\n"
        f"Status: <b>{status_emoji}</b>\n"
        f"Active Conversation: <b>{name}</b>\n\n"
        "Please select an action below to manage your simulation."
    )
    
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    
    builder = InlineKeyboardBuilder()
    if is_running:
        builder.row(InlineKeyboardButton(text="⏹️ Stop", callback_data="sim_stop"))
        builder.row(
            InlineKeyboardButton(text="⏸️ Pause", callback_data="sim_pause") if not coordinator.state.is_paused 
            else InlineKeyboardButton(text="▶️ Resume", callback_data="sim_resume")
        )
    else:
        builder.row(InlineKeyboardButton(text="📥 Upload JSON", callback_data="sim_upload"))
        builder.row(InlineKeyboardButton(text="📄 Upload TXT", callback_data="sim_upload_txt"))
        builder.row(InlineKeyboardButton(text="✍️ Convert Text", callback_data="sim_convert"))
        if conv_data:
            builder.row(InlineKeyboardButton(text="▶️ Start Simulation", callback_data="sim_start"))
            
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data == "sim_upload")
async def upload_json(callback: CallbackQuery, state: FSMContext):
    """Wait for the user's 'Mouth' to send a JSON document."""
    await state.set_state(SimulationStates.WAITING_FOR_JSON_UPLOAD)
    await callback.message.answer("📥 Please upload your <b>Conversation JSON</b> file.")
    await callback.answer()

@router.message(SimulationStates.WAITING_FOR_JSON_UPLOAD, F.document)
async def process_json_upload(message: Message, state: FSMContext, bot, config_repo: ConfigRepository):
    """Librarian (Vault) receives a new blueprint (JSON)."""
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    import io
    content = await bot.download_file(file_path)
    try:
        data = json.loads(content.read().decode('utf-8'))
        config_repo.set_conversation(data)
        await message.answer("✅ JSON loaded into the Vault successfully!", reply_markup=get_main_menu_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer(f"❌ Failed to parse JSON: {e}")

@router.callback_query(F.data == "sim_upload_txt")
async def upload_txt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SimulationStates.WAITING_FOR_TXT_UPLOAD)
    await callback.message.answer("📄 Please upload your <b>Conversation TXT</b> (batches) file.")
    await callback.answer()

@router.message(SimulationStates.WAITING_FOR_TXT_UPLOAD, F.document)
async def process_txt_upload(message: Message, state: FSMContext, bot, config_repo: ConfigRepository):
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    content = await bot.download_file(file.file_path)
    text = content.read().decode('utf-8')
    try:
        data = TextParser.parse_txt_batches(text) if "---BATCH:" in text else TextParser.parse_conversation_text(text)
        config_repo.set_conversation(data)
        await message.answer("✅ TXT loaded successfully!", reply_markup=get_main_menu_keyboard())
        await state.clear()
    except Exception as e: await message.answer(f"❌ Failed: {e}")

@router.callback_query(F.data == "sim_convert")
async def start_conversion(callback: CallbackQuery, state: FSMContext):
    """Wait for the user's 'Mouth' to speak text for conversion."""
    await state.set_state(SimulationStates.WAITING_FOR_TEXT_CONVERSION)
    await callback.message.answer("✍️ Paste your conversation text (Format: <code>Name: Message</code>) or a TXT batch file.")
    await callback.answer()

@router.message(SimulationStates.WAITING_FOR_TEXT_CONVERSION)
async def process_conversion(message: Message, state: FSMContext, config_repo: ConfigRepository):
    """The 'Brain' (TextParser) translates raw text into simulation logic."""
    text = message.text
    try:
        # Check if it's a batch or normal text
        if "---BATCH:" in text:
            data = TextParser.parse_txt_batches(text)
        else:
            data = TextParser.parse_conversation_text(text)
            
        config_repo.set_conversation(data)
        await message.answer("✅ Conversion complete! Brain has updated the Vault.", reply_markup=get_main_menu_keyboard())
        await state.clear()
    except ValueError as e:
        await message.answer(f"❌ Conversion failed: {e}")

@router.callback_query(F.data == "sim_start")
async def start_sim(callback: CallbackQuery, config_repo: ConfigRepository, coordinator: SimulationCoordinator):
    """Tell the 'Spinal Cord' (Coordinator) to start the simulation."""
    import time
    start_time = time.perf_counter()
    
    conv_data = config_repo.get_conversation()
    conf = config_repo.get_config()
    
    if not conv_data:
        await callback.answer("❌ No conversation found. Upload/Convert one first.", show_alert=True)
        return
        
    target_group = conf.get("target_group")
    if not target_group:
        await callback.answer("❌ Target Group ID not set in Settings.", show_alert=True)
        return
        
    speed_str = conf.get("typing_speed", "normal")
    speed = TypingSpeed(speed_str)
    
    from core.models.conversation import ConversationData
    import asyncio
    
    # Non-blocking task
    asyncio.create_task(coordinator.start_simulation(ConversationData(**conv_data), int(target_group), speed))
    
    latency = (time.perf_counter() - start_time) * 1000
    logger.info(f"🚀 Simulation start latency: {latency:.2f}ms")
    
    await callback.answer(f"✅ Simulation started! (Lat: {latency:.1f}ms)")
    await callback.message.edit_text("🚀 <b>Simulation is now active.</b> Monitor the progress in Status.")

@router.callback_query(F.data == "sim_stop")
async def sim_stop(callback: CallbackQuery, coordinator: SimulationCoordinator):
    """The 'Spinal Cord' gets a stop signal."""
    coordinator.stop_simulation()
    await callback.answer("⏹️ Stopping simulation...")

@router.callback_query(F.data == "sim_pause")
async def sim_pause(callback: CallbackQuery, coordinator: SimulationCoordinator):
    """The 'Spinal Cord' gets a pause signal."""
    coordinator.pause_simulation()
    await callback.answer("⏸️ Paused.")

@router.callback_query(F.data == "sim_resume")
async def sim_resume(callback: CallbackQuery, coordinator: SimulationCoordinator):
    """The 'Spinal Cord' gets a resume signal."""
    coordinator.resume_simulation()
    await callback.answer("▶️ Resumed.")
