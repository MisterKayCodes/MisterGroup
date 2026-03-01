# Made by Mister 💛
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class SimulationState:
    """The current state of a running simulation."""
    is_running: bool = False
    is_paused: bool = False
    should_stop: bool = False
    current_index: int = 0
    target_group: Optional[int] = None
    successful_count: int = 0
    failed_count: int = 0
    total_to_send: int = 0
    period_label: Optional[str] = None

    def reset_counts(self):
        self.successful_count = 0
        self.failed_count = 0
        self.current_index = 0
        self.should_stop = False
        self.is_paused = False
        self.is_running = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "current_index": self.current_index,
            "target_group": self.target_group,
            "successful_count": self.successful_count,
            "failed_count": self.failed_count,
            "total_to_send": self.total_to_send,
            "period_label": self.period_label
        }
