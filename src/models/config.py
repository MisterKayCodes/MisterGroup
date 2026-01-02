# Made by Mister 💛

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TypingSpeed(str, Enum):
    """Typing speed configuration"""
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"
    
    def get_multiplier(self) -> float:
        """Get the speed multiplier for typing simulation"""
        multipliers = {
            "fast": 0.5,
            "normal": 1.0,
            "slow": 2.0
        }
        return multipliers.get(self.value, 1.0)


class SimulationState(BaseModel):
    """Current state of message simulation"""
    is_running: bool = Field(default=False, description="Whether simulation is currently running")
    is_paused: bool = Field(default=False, description="Whether simulation is paused")
    current_index: int = Field(default=0, description="Current message index in conversation")
    target_group: Optional[int] = Field(None, description="Target group ID for simulation")


class BotConfig(BaseModel):
    """Bot configuration"""
    typing_speed: TypingSpeed = Field(default=TypingSpeed.NORMAL, description="Typing simulation speed")
    target_group: Optional[int] = Field(None, description="Default target group for simulations")
    admin_id: Optional[int] = Field(None, description="Admin Telegram user ID")
    
    class Config:
        use_enum_values = True
