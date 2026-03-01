# Made by Mister 💛
from dataclasses import dataclass, field
from typing import List, Optional
from core.models.message import Message
from core.models.period import ScheduledPeriod

@dataclass
class ConversationData:
    name: str
    description: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    schedule: List[ScheduledPeriod] = field(default_factory=list)
    mode: str = "immediate"  # 'immediate' or 'scheduled'

    def is_scheduled(self) -> bool:
        return len(self.schedule) > 0 or self.mode == "scheduled"

    def get_all_messages(self) -> List[Message]:
        if self.schedule:
            all_msgs = []
            for period in self.schedule:
                all_msgs.extend(period.messages)
            return all_msgs
        return self.messages

    def get_total_message_count(self) -> int:
        if self.schedule:
            return sum(len(p.messages) for p in self.schedule)
        return len(self.messages)

    def get_participants(self) -> set:
        participants = set()
        for msg in self.get_all_messages():
            participants.add(msg.sender_name)
        return participants
