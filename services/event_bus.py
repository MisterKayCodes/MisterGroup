# Made by Mister 💛
import asyncio
from typing import Callable, List, Dict, Any, Optional
from loguru import logger
from core.events import SimulationEvent

class EventBus:
    """The 'Spinal Cord' of the organism. Carries messages across folders."""
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Register a 'Voice Box' (handler) for an event shout."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    async def emit_event(self, event: SimulationEvent):
        """Shouts an event to all subscribers (Handlers)."""
        logger.debug(f"EventBus emit: {event.event_type} - {event.status}")
        
        callbacks = self._listeners.get(event.event_type, [])
        # Also broadcast to "all" listeners if needed
        all_callbacks = self._listeners.get("*", [])
        
        tasks = []
        for cb in callbacks + all_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    tasks.append(cb(event))
                else:
                    cb(event)
            except Exception as e:
                logger.error(f"Error in EventBus listener: {e}")
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def emit(self, event_type: str, status: str, data: Optional[Any] = None, message: Optional[str] = None):
        """Shortcut to emit a simulation event."""
        event = SimulationEvent(event_type=event_type, status=status, data=data, message=message)
        await self.emit_event(event)
