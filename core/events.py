# Made by Mister 💛
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional

class EventStatus(str, Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    RESUMED = "resumed"
    STOPPED = "stopped"
    PROGRESS = "progress"

@dataclass
class SimulationEvent:
    """An event produced by the simulation engine logic."""
    event_type: str        # e.g., "message_sent", "period_started"
    status: EventStatus
    data: Optional[Any] = None
    message: Optional[str] = None

class CoreEvents:
    # Event constant names
    MESSAGE_SENT = "message_sent"
    PERIOD_STARTED = "period_started"
    PERIOD_COMPLETED = "period_completed"
    SIMULATION_STARTED = "simulation_started"
    SIMULATION_STOPPED = "simulation_stopped"
    SIMULATION_PAUSED = "simulation_paused"
    SIMULATION_RESUMED = "simulation_resumed"
    QUEUE_PROCESSED = "queue_processed"
    ERROR = "error"
