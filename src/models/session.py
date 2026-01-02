# Made by Mister 💛

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    """Status of a Telethon session"""
    ACTIVE = "active"
    PAUSED = "paused"
    INACTIVE = "inactive"


class TelethonSession(BaseModel):
    """Model for a Telethon session"""
    name: str = Field(..., description="Unique name for the session")
    phone: Optional[str] = Field(None, description="Phone number associated with session")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Current status of the session")
    session_string: Optional[str] = Field(None, description="Telethon session string")
    last_tested: Optional[datetime] = Field(None, description="Last time session was tested")
    is_connected: bool = Field(default=False, description="Whether session is currently connected")
    user_id: Optional[int] = Field(None, description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    created_at: datetime = Field(default_factory=datetime.now, description="When session was created")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
