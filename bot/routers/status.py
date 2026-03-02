# Made by Mister 💛
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from data.repositories.session_repo import SessionRepository
from data.repositories.config_repo import ConfigRepository
from services.coordinator.simulation_coordinator import SimulationCoordinator
from services.coordinator.scheduler_service import BackgroundScheduler
from services.health_monitor import HealthMonitor

router = Router()

@router.message(F.text == "📊 Status")
async def cmd_status(message: Message, session_repo: SessionRepository, config_repo: ConfigRepository, coordinator: SimulationCoordinator, health_monitor: HealthMonitor, scheduler: BackgroundScheduler):
    """The 'Mouth' status report. Gathers info from Brain, Nervous System, and Health Probe."""
    sessions = session_repo.get_all_sessions()
    conf = config_repo.get_config()
    is_running = coordinator.state.is_running
    health = health_monitor.get_health_status()
    await health_monitor.check_network_latency() # Refresh sample
    
    active_count = sum(1 for s in sessions.values() if s.get("status") == "active")
    connected_count = sum(1 for s in sessions.values() if s.get("is_connected"))
    
    target_group = conf.get("target_group", "<i>Not set</i>")
    speed = conf.get("typing_speed", "normal").upper()
    
    status_text = (
        "<b>📊 Organism Status Report</b>\n\n"
        f"🧠 <b>Simulation:</b> {'🟢 Running' if is_running else '⚪ Idle'}\n"
        f"🏥 <b>Health:</b> {health['status']} ({health['avg_latency']}ms)\n"
        f"🧬 <b>Sessions:</b> {active_count} active / {len(sessions)} total\n"
        f"🤝 <b>Connected:</b> {connected_count} accounts\n\n"
        f"🎯 <b>Target Group:</b> <code>{target_group}</code>\n"
        f"⚡ <b>Typing Speed:</b> {speed}\n"
    )
    
    auto_status = scheduler.get_automation_status()
    if auto_status["enabled"]:
        mins = auto_status["minutes_left"]
        msgs = auto_status["pending_messages"]
        status_text += f"🚀 <b>AI Automation:</b> {mins}m until next batch ({msgs} msgs)\n"
    else:
        status_text += "🚀 <b>AI Automation:</b> ⚪ Disabled\n"
    
    if is_running:
        status_text += (
            f"\n📈 <b>Current Progress:</b>\n"
            f"• Processed: {coordinator.state.current_index}/{coordinator.state.total_to_send}\n"
            f"• Success: {coordinator.state.successful_count} | Failed: {coordinator.state.failed_count}"
        )
        
    await message.answer(status_text)
