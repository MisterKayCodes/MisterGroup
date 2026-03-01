# Made by Mister 💛
from dataclasses import dataclass, field
from typing import List, Union, Optional
from core.models.message import Message

@dataclass
class ScheduledPeriod:
    time: str
    label: str
    participants: Union[List[str], str] # List of names or "all"
    messages: List[Message] = field(default_factory=list)
    repeat: str = "daily"
    enabled: bool = True
