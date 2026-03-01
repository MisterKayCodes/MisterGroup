# Made by Mister 💛
from aiogram.types import Message, CallbackQuery
from typing import Optional, Any
from core.events import SimulationEvent, CoreEvents, EventStatus
from services.event_bus import EventBus
from bot.keyboards.main_menu import get_main_menu_keyboard

class BotNotifier:
    """The 'Voice Box'. Listens for 'Spinal Cord' (EventBus) shouts and screams to the User."""
    
    def __init__(self, bot, event_bus: EventBus, admin_id: Optional[int] = None):
        self.bot = bot
        self.eb = event_bus
        self.admin_id = admin_id
        
        # Subscribe to all events by default
        self.eb.subscribe("*", self.handle_notification)

    async def handle_notification(self, event: SimulationEvent):
        """As the 'Voice Box', translate internal 'Spinal Cord' signals into User-friendly messages."""
        if not self.admin_id: return

        # Translator logic:
        # MAP: event_type + status -> Message Text
        text = self._translate_event_to_text(event)
        if not text: return

        try:
            await self.bot.send_message(self.admin_id, text, parse_mode="HTML")
        except Exception as e:
            # Avoid infinite loop if logging fails here
            import sys
            print(f"FAILED TO SCREAM TO USER: {e}", file=sys.stderr)

    def _translate_event_to_text(self, event: SimulationEvent) -> Optional[str]:
        """Translates Brain signals (SimulationEvent) into human words."""
        et = event.event_type
        es = event.status
        
        if et == CoreEvents.SIMULATION_STARTED:
            return f"🚀 <b>Simulation Started!</b>\n{event.message or ''}"
        
        if et == CoreEvents.SIMULATION_STOPPED:
            status_msg = "Completed ✅" if es == EventStatus.COMPLETED else "Stopped ⏹️"
            return f"🏁 <b>Simulation {status_msg}</b>\n{event.message or ''}"
        
        if et == CoreEvents.PERIOD_STARTED:
            return f"🕐 <b>Starting Period:</b> {event.data}"
            
        if et == CoreEvents.PERIOD_COMPLETED:
            return f"✅ <b>Period Completed:</b> {event.data}"
            
        if et == CoreEvents.ERROR:
            return f"❌ <b>Error:</b> {event.message}"
            
        return None  # Ignore silent events
