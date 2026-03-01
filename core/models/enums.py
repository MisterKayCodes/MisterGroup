# Made by Mister 💛
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"
    VOICE = "voice"
    DOCUMENT = "document"
    STICKER = "sticker"

class TypingSpeed(str, Enum):
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"

    def get_multiplier(self) -> float:
        if self == TypingSpeed.FAST:
            return 0.5
        elif self == TypingSpeed.SLOW:
            return 2.0
        return 1.0
