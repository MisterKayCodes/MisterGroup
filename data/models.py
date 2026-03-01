# Made by Mister 💛
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from core.models.enums import MessageType, TypingSpeed

class SessionModel(BaseModel):
    name: str
    phone: Optional[str] = None
    status: str = "active"
    session_string: Optional[str] = None
    last_tested: Optional[str] = None
    is_connected: bool = False
    user_id: Optional[int] = None
    username: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class ConfigModel(BaseModel):
    typing_speed: str = "normal"
    target_group: Optional[int] = None
    admin_id: Optional[int] = None
    scheduler_running: bool = False

class SimulationStateModel(BaseModel):
    is_running: bool = False
    is_paused: bool = False
    current_index: int = 0
    target_group: Optional[int] = None

class StatisticsModel(BaseModel):
    messages_sent_today: int = 0
    total_messages_sent: int = 0
    last_reset: Optional[str] = None

class GroupModel(BaseModel):
    id: str
    title: str = "Unknown"
    type: str = "unknown"
    link: Optional[str] = None
    joined_at: Optional[str] = None
    members_joined: List[str] = Field(default_factory=list)
    simulation_active: bool = False
