# Made by Mister 💛
import random
from core.models.enums import TypingSpeed

class TypingCalculator:
    """Calculates typing and delay durations for realistic simulation."""
    
    @staticmethod
    def calculate_typing_duration(message: str, speed: TypingSpeed) -> float:
        """Calculate typing duration based on message length and speed."""
        words = len(message.split())
        base_duration = (words / 60) * 60  # Base logic: 60 WPM
        
        multiplier = speed.get_multiplier()
        duration = base_duration * multiplier
        
        # Clamp to realistic limits
        return max(1.0, min(10.0, duration))

    @staticmethod
    def get_random_delay(speed: TypingSpeed) -> float:
        """Get random delay between messages depending on speed."""
        ranges = {
            TypingSpeed.FAST: (3, 9),
            TypingSpeed.NORMAL: (10, 26),
            TypingSpeed.SLOW: (27, 50)
        }
        min_delay, max_delay = ranges.get(speed, ranges[TypingSpeed.NORMAL])
        return round(random.uniform(min_delay, max_delay), 2)

    @staticmethod
    def get_random_typing(speed: TypingSpeed) -> float:
        """Get random typing duration (different from wait delay)."""
        min_delay, max_delay = (5, 15)  # General spread
        if speed == TypingSpeed.FAST:
            min_delay, max_delay = (2, 6)
        elif speed == TypingSpeed.SLOW:
            min_delay, max_delay = (10, 30)

        # Usually shorter than total delay between messages
        return round(random.uniform(min_delay * 0.5, max_delay * 0.7), 2)
