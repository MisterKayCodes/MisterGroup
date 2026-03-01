# Made by Mister 💛
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
from core.models.period import ScheduledPeriod

class SchedulerLogic:
    """Decision logic for the scheduler."""
    
    @staticmethod
    def should_run_period(
        period: ScheduledPeriod, 
        now_utc: datetime, 
        executed_today: List[str] # List of labels or IDs
    ) -> bool:
        """Check if a period should run based on current UTC time."""
        if not period.enabled:
            return False
            
        # Already executed today?
        today_key = f"{period.label}_{now_utc.date().isoformat()}"
        if today_key in executed_today:
            return False
            
        # Parse time (assumes 'HH:MM' in UTC)
        try:
            hour, minute = map(int, period.time.split(':'))
        except (ValueError, AttributeError):
            return False
            
        period_time = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Only run if we're AT or PAST the scheduled time (never before!)
        if now_utc < period_time:
            return False
        
        # Check grace window (5 min)
        time_since_scheduled = (now_utc - period_time).total_seconds()
        if time_since_scheduled > 300: # Missed (too far into the future)
            # Log something? No, logic just says NO.
            return False
            
        return SchedulerLogic.matches_repeat_pattern(period.repeat, now_utc)

    @staticmethod
    def matches_repeat_pattern(repeat: str, now: datetime) -> bool:
        """Determines if a repeat pattern matches the current day."""
        pattern = repeat.lower()
        weekday = now.weekday() # 0 = Monday, 6 = Sunday
        
        if pattern == "weekdays" and weekday >= 5:
            return False
        if pattern == "weekends" and weekday < 5:
            return False
        # Default: daily or once (already handled today check)
        return True

    @staticmethod
    def calculate_next_run(period: ScheduledPeriod, now_utc: datetime) -> Optional[datetime]:
        """Calculates the absolute datetime for the next run."""
        try:
            hour, minute = map(int, period.time.split(':'))
            period_dt = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If past today, calculate based on repeat
            if period_dt <= now_utc:
                repeat = period.repeat.lower()
                if repeat == "once":
                    return None
                
                # Default next-day calculation
                next_day = period_dt + timedelta(days=1)
                
                # Adjust for Weekdays/Weekends if necessary
                while not SchedulerLogic.matches_repeat_pattern(repeat, next_day):
                    next_day += timedelta(days=1)
                return next_day
                
            return period_dt
        except:
            return None
