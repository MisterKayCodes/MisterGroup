# Made by Mister 💛

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Callable
from loguru import logger
from telethon import TelegramClient
import pytz

from src.utils.database import Database
from src.services.session_manager import SessionManager
from src.models.conversation import ConversationData, Message, MessageType, ScheduledPeriod
from src.models.config import TypingSpeed


class SimulationEngine:
    """Engine for simulating conversations in Telegram groups"""
    
    def __init__(self, db: Database, session_manager: SessionManager):
        self.db = db
        self.session_manager = session_manager
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        
        # Media sender (lazy loaded)
        self._media_sender = None
        self._media_db = None
        
        # Scheduler state
        self.scheduler_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.admin_callback: Optional[Callable] = None
        self.executed_periods: Dict[str, datetime] = {}  # Track executed periods today
    
    def set_media_sender(self, media_db):
        """Set media database for media tag support"""
        self._media_db = media_db
        try:
            from src.utils.media_sender import MediaSender
            self._media_sender = MediaSender(media_db, self.session_manager)
            logger.info("Media sender initialized for simulation engine")
        except Exception as e:
            logger.warning(f"Could not initialize media sender: {e}")
        
    def _calculate_typing_duration(self, message: str, speed: TypingSpeed) -> float:
        """Calculate typing duration based on message length and speed"""
        words = len(message.split())
        base_duration = (words / 60) * 60  # Convert to seconds
        
        multiplier = speed.get_multiplier()
        duration = base_duration * multiplier
        
        return max(1.0, min(10.0, duration))
    
    async def send_typing_action(self, client: TelegramClient, chat_id: int, duration: float):
        """Send typing action for specified duration"""
        try:
            end_time = asyncio.get_event_loop().time() + duration
            while asyncio.get_event_loop().time() < end_time:
                await client.send_read_acknowledge(chat_id, max_id=0)
                await asyncio.sleep(min(4.0, duration))
        except Exception as e:
            logger.error(f"Error sending typing action: {e}")
    
    async def send_message(
        self,
        message: Message,
        client: TelegramClient,
        chat_id: int,
        typing_speed: TypingSpeed
    ) -> bool:
        """Send a single message"""
        try:
            typing_duration = message.typing_duration
            if typing_duration is None:
                typing_duration = self._calculate_typing_duration(message.content, typing_speed)
            
            logger.info(f"Simulating typing for {typing_duration:.1f}s for message from {message.sender_name}")
            await self.send_typing_action(client, chat_id, typing_duration)
            
            if message.message_type == MessageType.TEXT:
                if self._media_sender and self._media_sender.has_media_tags(message.content):
                    media_sent, cleaned_content = await self._media_sender.send_media_for_message(
                        client, chat_id, message.content
                    )
                    if media_sent:
                        logger.info(f"Sent media message from {message.sender_name}")
                    elif cleaned_content and cleaned_content.strip():
                        await client.send_message(chat_id, cleaned_content)
                        logger.info(f"Sent text message (media unavailable) from {message.sender_name}")
                    else:
                        logger.warning(f"Media unavailable and no text content for message from {message.sender_name}, skipping")
                else:
                    await client.send_message(chat_id, message.content)
                    logger.info(f"Sent text message from {message.sender_name}")
                
            elif message.message_type == MessageType.PHOTO:
                if message.media_url:
                    await client.send_file(
                        chat_id,
                        message.media_url,
                        caption=message.content if message.content else None
                    )
                    logger.info(f"Sent photo from {message.sender_name}")
                else:
                    logger.warning(f"Photo message from {message.sender_name} has no media_url")
                    return False
                    
            elif message.message_type == MessageType.VIDEO:
                if message.media_url:
                    await client.send_file(
                        chat_id,
                        message.media_url,
                        caption=message.content if message.content else None
                    )
                    logger.info(f"Sent video from {message.sender_name}")
                else:
                    logger.warning(f"Video message from {message.sender_name} has no media_url")
                    return False
                    
            elif message.message_type == MessageType.VOICE:
                if message.media_url:
                    await client.send_file(
                        chat_id,
                        message.media_url,
                        voice_note=True
                    )
                    logger.info(f"Sent voice note from {message.sender_name}")
                else:
                    logger.warning(f"Voice message from {message.sender_name} has no media_url")
                    return False
                    
            elif message.message_type == MessageType.DOCUMENT:
                if message.media_url:
                    await client.send_file(
                        chat_id,
                        message.media_url,
                        caption=message.content if message.content else None
                    )
                    logger.info(f"Sent document from {message.sender_name}")
                else:
                    logger.warning(f"Document message from {message.sender_name} has no media_url")
                    return False
            
            self.db.increment_messages_sent()
            return True
            
        except Exception as e:
            logger.error(f"Error sending message from {message.sender_name}: {e}")
            return False
    
    async def run_period_messages(
        self,
        period: ScheduledPeriod,
        target_group: int,
        typing_speed: TypingSpeed,
        admin_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Run messages for a specific scheduled period"""
        successful = 0
        failed = 0
        
        # Get available sessions
        all_sessions_dict = self.db.get_all_sessions()
        all_sessions = list(all_sessions_dict.keys())
        
        # Determine which participants to use
        if isinstance(period.participants, str) and period.participants.lower() == "all":
            active_participants = set(all_sessions)
        else:
            active_participants = set(period.participants) if isinstance(period.participants, list) else set()
        
        logger.info(f"Running period '{period.label}' with {len(period.messages)} messages")
        logger.info(f"Active participants: {active_participants}")
        
        if admin_callback:
            await admin_callback(f"🕐 Starting period: {period.label} ({period.time})\nParticipants: {', '.join(active_participants) if active_participants else 'all'}")
        
        for i, message in enumerate(period.messages):
            if self.should_stop:
                logger.info("Period execution stopped by user")
                break
            
            while self.is_paused and not self.should_stop:
                await asyncio.sleep(0.5)
            
            if self.should_stop:
                break
            
            # Check if sender is an active participant for this period
            if message.sender_name not in active_participants:
                logger.debug(f"Skipping message from {message.sender_name} - not active in this period")
                continue
            
            client = await self.session_manager.get_client(message.sender_name)
            if not client:
                logger.warning(f"No client available for {message.sender_name}, skipping message")
                failed += 1
                continue
            
            if message.delay_before > 0:
                await asyncio.sleep(message.delay_before)
            
            success = await self.send_message(message, client, target_group, typing_speed)
            if success:
                successful += 1
            else:
                failed += 1
        
        return {
            "successful": successful,
            "failed": failed,
            "period_label": period.label
        }
    
    async def start_simulation(self, admin_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Start the conversation simulation (immediate mode)"""
        try:
            if self.is_running:
                return {
                    "success": False,
                    "message": "Simulation is already running"
                }
            
            conversation_data = self.db.get_conversation()
            if not conversation_data:
                return {
                    "success": False,
                    "message": "No conversation data loaded. Use /upload_json first."
                }
            
            config = self.db.get_config()
            target_group = config.get("target_group")
            if not target_group:
                return {
                    "success": False,
                    "message": "No target group set. Use /set_group first."
                }
            
            typing_speed_str = config.get("typing_speed", "normal")
            typing_speed = TypingSpeed(typing_speed_str)
            
            conversation = ConversationData(**conversation_data)
            
            # Check if scheduled mode
            if conversation.is_scheduled():
                return {
                    "success": False,
                    "message": "This conversation uses scheduled mode. Use /start_scheduler to enable automatic scheduling, or /run_period <label> to run a specific period now."
                }
            
            sim_state = self.db.get_simulation_state()
            start_index = sim_state.get("current_index", 0)
            
            self.is_running = True
            self.is_paused = False
            self.should_stop = False
            self.db.update_simulation_state({
                "is_running": True,
                "is_paused": False,
                "target_group": target_group
            })
            
            logger.info(f"Starting simulation with {len(conversation.messages)} messages from index {start_index}")
            
            if admin_callback:
                await admin_callback(f"Starting conversation simulation in group {target_group}...")
            
            successful = 0
            failed = 0
            
            for i in range(start_index, len(conversation.messages)):
                if self.should_stop:
                    logger.info("Simulation stopped by user")
                    break
                
                while self.is_paused and not self.should_stop:
                    await asyncio.sleep(0.5)
                
                if self.should_stop:
                    break
                
                message = conversation.messages[i]
                
                client = await self.session_manager.get_client(message.sender_name)
                if not client:
                    logger.warning(f"No client available for {message.sender_name}, skipping message")
                    failed += 1
                    continue
                
                if message.delay_before > 0:
                    await asyncio.sleep(message.delay_before)
                
                success = await self.send_message(message, client, target_group, typing_speed)
                if success:
                    successful += 1
                else:
                    failed += 1
                
                self.db.update_simulation_state({"current_index": i + 1})
            
            self.is_running = False
            self.is_paused = False
            self.db.update_simulation_state({
                "is_running": False,
                "is_paused": False,
                "current_index": 0 if not self.should_stop else self.db.get_simulation_state().get("current_index", 0)
            })
            
            result_message = f"Simulation completed. Sent {successful} messages"
            if failed > 0:
                result_message += f", {failed} failed"
            
            logger.info(result_message)
            
            if admin_callback:
                await admin_callback(result_message)
            
            return {
                "success": True,
                "message": result_message,
                "successful": successful,
                "failed": failed
            }
            
        except Exception as e:
            self.is_running = False
            self.is_paused = False
            self.db.update_simulation_state({
                "is_running": False,
                "is_paused": False
            })
            logger.error(f"Error in simulation: {e}")
            return {
                "success": False,
                "message": f"Simulation error: {str(e)}"
            }
    
    async def run_specific_period(self, period_label: str, admin_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Run a specific scheduled period by label"""
        try:
            conversation_data = self.db.get_conversation()
            if not conversation_data:
                return {
                    "success": False,
                    "message": "No conversation data loaded. Use /upload_json first."
                }
            
            config = self.db.get_config()
            target_group = config.get("target_group")
            if not target_group:
                return {
                    "success": False,
                    "message": "No target group set. Use /set_group first."
                }
            
            conversation = ConversationData(**conversation_data)
            
            if not conversation.is_scheduled():
                return {
                    "success": False,
                    "message": "This conversation doesn't have scheduled periods. Use /start_simulation for immediate mode."
                }
            
            # Find the period by label
            target_period = None
            for period in conversation.schedule:
                if period.label.lower() == period_label.lower():
                    target_period = period
                    break
            
            if not target_period:
                available = ", ".join([p.label for p in conversation.schedule])
                return {
                    "success": False,
                    "message": f"Period '{period_label}' not found. Available periods: {available}"
                }
            
            typing_speed_str = config.get("typing_speed", "normal")
            typing_speed = TypingSpeed(typing_speed_str)
            
            self.is_running = True
            self.is_paused = False
            self.should_stop = False
            
            result = await self.run_period_messages(target_period, target_group, typing_speed, admin_callback)
            
            self.is_running = False
            
            message = f"Period '{target_period.label}' completed. Sent {result['successful']} messages"
            if result['failed'] > 0:
                message += f", {result['failed']} failed"
            
            if admin_callback:
                await admin_callback(message)
            
            return {
                "success": True,
                "message": message,
                **result
            }
            
        except Exception as e:
            self.is_running = False
            logger.error(f"Error running period: {e}")
            return {
                "success": False,
                "message": f"Error running period: {str(e)}"
            }
    
    def _should_run_period(self, period: ScheduledPeriod, now_utc: datetime) -> bool:
        """Check if a period should run based on current UTC time and repeat settings"""
        # Parse period time (assuming UTC)
        hour, minute = map(int, period.time.split(':'))
        period_time = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Only run if we're AT or PAST the scheduled time (never before!)
        if now_utc < period_time:
            return False  # Don't run before scheduled time
        
        # Check if we're within 5-minute grace window after scheduled time
        # This allows catching up if bot was briefly offline
        time_since_scheduled = (now_utc - period_time).total_seconds()
        if time_since_scheduled > 300:  # More than 5 min past scheduled time
            logger.warning(f"Scheduled period '{period.label}' at {period.time} was missed (now {now_utc.strftime('%H:%M')})")
            return False
        
        # Check repeat pattern
        weekday = now_utc.weekday()  # 0 = Monday, 6 = Sunday
        if period.repeat == "weekdays" and weekday >= 5:
            return False
        if period.repeat == "weekends" and weekday < 5:
            return False
        
        # Check if already executed today
        period_key = f"{period.label}_{now_utc.date().isoformat()}"
        if period_key in self.executed_periods:
            return False
        
        return period.enabled
    
    async def scheduler_loop(self, admin_callback: Optional[Callable] = None):
        """Background scheduler loop that runs periods at their scheduled times"""
        logger.info("Scheduler loop started")
        
        while self.scheduler_running:
            try:
                conversation_data = self.db.get_conversation()
                if not conversation_data:
                    await asyncio.sleep(30)
                    continue
                
                try:
                    conversation = ConversationData(**conversation_data)
                except Exception as e:
                    logger.error(f"Failed to parse conversation data: {e}")
                    await asyncio.sleep(30)
                    continue
                
                if not conversation.is_scheduled():
                    await asyncio.sleep(30)
                    continue
                
                config = self.db.get_config()
                target_group = config.get("target_group")
                if not target_group:
                    await asyncio.sleep(30)
                    continue
                
                # Use UTC time for scheduling (keep timezone aware)
                now_utc = datetime.now(timezone.utc)
                
                # Clear executed periods from previous days - keep only today's entries
                today_str = now_utc.date().isoformat()
                self.executed_periods = {k: v for k, v in self.executed_periods.items() if today_str in k}
                
                for period in conversation.schedule:
                    if self._should_run_period(period, now_utc):
                        period_key = f"{period.label}_{now_utc.date().isoformat()}"
                        self.executed_periods[period_key] = now_utc
                        
                        logger.info(f"Scheduler triggering period: {period.label}")
                        
                        typing_speed_str = config.get("typing_speed", "normal")
                        typing_speed = TypingSpeed(typing_speed_str)
                        
                        # Reset stop flags before starting new scheduled period
                        self.is_running = True
                        self.is_paused = False
                        self.should_stop = False
                        
                        result = await self.run_period_messages(period, target_group, typing_speed, admin_callback)
                        self.is_running = False
                        
                        logger.info(f"Scheduled period '{period.label}' completed: {result}")
                        
                        # Auto-disable 'once' periods after execution
                        if period.repeat.lower() == "once":
                            logger.info(f"Auto-disabling 'once' period: {period.label}")
                            
                            # Update both DB and in-memory conversation data
                            for p in conversation.schedule:
                                if p.label == period.label:
                                    p.enabled = False
                            
                            conversation_data['schedule'] = [
                                p.model_dump() for p in conversation.schedule
                            ]
                            self.db.set_conversation(conversation_data)
                            
                            if admin_callback:
                                await admin_callback(f"✅ Period '{period.label}' completed and auto-disabled (repeat: once)")
                            
                            # Only clean up if ALL periods are 'once' AND ALL are executed/disabled
                            # This prevents cleanup when there are mixed schedules
                            all_periods_once = all(p.repeat.lower() == "once" for p in conversation.schedule)
                            all_once_disabled = all(not p.enabled for p in conversation.schedule if p.repeat.lower() == "once")
                            
                            if all_periods_once and all_once_disabled:
                                logger.info("All 'once' periods completed and disabled. Cleaning up conversation data.")
                                self.db.set("conversation", None)
                                if admin_callback:
                                    await admin_callback("🧹 All scheduled periods completed. Conversation data cleaned up.")
                                
                                # Auto-process queued conversations after all scheduled posts complete
                                await self.auto_process_queue_after_schedule(admin_callback)
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(30)
        
        logger.info("Scheduler loop stopped")
    
    async def start_scheduler(self, admin_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Start the background scheduler"""
        if self.scheduler_running:
            return {
                "success": False,
                "message": "Scheduler is already running"
            }
        
        conversation_data = self.db.get_conversation()
        if not conversation_data:
            # Clear any stale flag
            self.db.update_config({"scheduler_running": False})
            return {
                "success": False,
                "message": "No conversation data loaded. Use /upload_json first."
            }
        
        conversation = ConversationData(**conversation_data)
        if not conversation.is_scheduled():
            # Clear any stale flag
            self.db.update_config({"scheduler_running": False})
            return {
                "success": False,
                "message": "The loaded conversation doesn't have scheduled periods. Upload a JSON with schedule array."
            }
        
        # Check if all 'once' periods are already disabled (nothing to run)
        all_periods_once = all(p.repeat.lower() == "once" for p in conversation.schedule)
        all_once_disabled = all(not p.enabled for p in conversation.schedule if p.repeat.lower() == "once")
        if all_periods_once and all_once_disabled:
            logger.info("All 'once' periods are already disabled. Nothing to schedule.")
            self.db.update_config({"scheduler_running": False})
            return {
                "success": False,
                "message": "All scheduled periods are already completed. Upload new conversation data."
            }
        
        # Save scheduler state to database BEFORE creating task for proper persistence
        self.db.update_config({"scheduler_running": True})
        
        try:
            # Reset stop flags when starting scheduler
            self.should_stop = False
            self.is_paused = False
            self.is_running = False
            
            self.scheduler_running = True
            self.admin_callback = admin_callback
            self.scheduler_task = asyncio.create_task(self.scheduler_loop(admin_callback))
        except Exception as e:
            # Revert flag if task creation fails
            self.scheduler_running = False
            self.db.update_config({"scheduler_running": False})
            logger.error(f"Failed to create scheduler task: {e}")
            return {
                "success": False,
                "message": f"Failed to start scheduler: {str(e)}"
            }
        
        periods_info = []
        for p in conversation.schedule:
            status = "✅" if p.enabled else "❌"
            periods_info.append(f"{status} {p.time} - {p.label}")
        
        return {
            "success": True,
            "message": f"Scheduler started! Monitoring {len(conversation.schedule)} scheduled periods:\n" + "\n".join(periods_info)
        }
    
    def stop_scheduler(self) -> Dict[str, Any]:
        """Stop the background scheduler"""
        if not self.scheduler_running:
            return {
                "success": False,
                "message": "Scheduler is not running"
            }
        
        self.scheduler_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
            self.scheduler_task = None
        
        # Save scheduler state to database for persistence
        self.db.update_config({"scheduler_running": False})
        
        return {
            "success": True,
            "message": "Scheduler stopped."
        }
    
    async def auto_resume_scheduler(self, admin_callback: Optional[Callable] = None) -> bool:
        """Auto-resume scheduler if it was running before bot restart"""
        # Prevent double-start if scheduler is already running in this process
        if self.scheduler_running:
            logger.info("Scheduler already running in this process, skipping auto-resume")
            return False
        
        # Also check if task exists and is not done
        if self.scheduler_task and not self.scheduler_task.done():
            logger.info("Scheduler task already exists and running, skipping auto-resume")
            return False
        
        config = self.db.get_config()
        was_running = config.get("scheduler_running", False)
        
        if not was_running:
            return False
        
        # Flag was true, but verify conversation data exists and is schedulable
        conversation_data = self.db.get_conversation()
        if not conversation_data:
            logger.warning("Scheduler flag was true but no conversation data found. Clearing flag.")
            self.db.update_config({"scheduler_running": False})
            return False
        
        try:
            conversation = ConversationData(**conversation_data)
            if not conversation.is_scheduled():
                logger.warning("Scheduler flag was true but conversation is not scheduled. Clearing flag.")
                self.db.update_config({"scheduler_running": False})
                return False
            
            logger.info("Auto-resuming scheduler after bot restart")
            result = await self.start_scheduler(admin_callback)
            return result.get("success", False)
        except Exception as e:
            logger.error(f"Failed to auto-resume scheduler: {e}")
            # Clear the flag if auto-resume failed
            self.db.update_config({"scheduler_running": False})
            return False
    
    def _get_next_run_datetime(self, period_time: str, repeat: str, now_utc: datetime) -> Optional[datetime]:
        """Calculate the next datetime when a period should run based on repeat pattern"""
        try:
            hour, minute = map(int, period_time.split(':'))
            period_datetime = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            repeat_lower = repeat.lower()
            weekday = now_utc.weekday()  # 0=Monday, 6=Sunday
            
            # Check if time has passed today
            time_passed_today = period_datetime <= now_utc
            
            if repeat_lower == "once":
                # Once periods only run on their scheduled time today
                if time_passed_today:
                    return None  # Already passed
                return period_datetime
            
            elif repeat_lower == "daily":
                # Daily runs every day
                if time_passed_today:
                    period_datetime += timedelta(days=1)
                return period_datetime
            
            elif repeat_lower == "weekdays":
                # Only Monday-Friday (weekday 0-4)
                if time_passed_today:
                    # Move to next day
                    period_datetime += timedelta(days=1)
                    weekday = period_datetime.weekday()
                
                # Skip weekends
                while weekday >= 5:  # Saturday or Sunday
                    period_datetime += timedelta(days=1)
                    weekday = period_datetime.weekday()
                
                return period_datetime
            
            elif repeat_lower == "weekends":
                # Only Saturday-Sunday (weekday 5-6)
                if time_passed_today:
                    period_datetime += timedelta(days=1)
                    weekday = period_datetime.weekday()
                
                # Skip weekdays
                while weekday < 5:  # Monday-Friday
                    period_datetime += timedelta(days=1)
                    weekday = period_datetime.weekday()
                
                return period_datetime
            
            else:
                # Default to daily for unknown patterns
                if time_passed_today:
                    period_datetime += timedelta(days=1)
                return period_datetime
                
        except Exception:
            return None
    
    def _normalize_participants(self, participants) -> str:
        """Safely normalize participants to a display string"""
        if isinstance(participants, str):
            if participants.lower() == "all":
                return "All sessions"
            return participants
        elif isinstance(participants, list):
            return ", ".join(str(p) for p in participants)
        else:
            return str(participants) if participants else "Unknown"
    
    def get_schedule_status(self) -> Dict[str, Any]:
        """Get current schedule status with countdown timers"""
        queue_count = self.db.get_queue_count()
        
        conversation_data = self.db.get_conversation()
        if not conversation_data:
            return {
                "has_schedule": False,
                "scheduler_running": self.scheduler_running,
                "periods": [],
                "next_period": None,
                "queued_items": queue_count
            }
        
        try:
            conversation = ConversationData(**conversation_data)
        except Exception:
            return {
                "has_schedule": False,
                "scheduler_running": self.scheduler_running,
                "periods": [],
                "next_period": None,
                "queued_items": queue_count
            }
        
        if not conversation.is_scheduled():
            return {
                "has_schedule": False,
                "scheduler_running": self.scheduler_running,
                "periods": [],
                "next_period": None,
                "queued_items": queue_count
            }
        
        periods = []
        now_utc = datetime.now(timezone.utc)
        today_str = now_utc.date().isoformat()
        
        next_period_info = None
        min_countdown_seconds = float('inf')
        
        for period in conversation.schedule:
            period_key = f"{period.label}_{today_str}"
            executed = period_key in self.executed_periods
            
            participants = self._normalize_participants(period.participants)
            
            # Calculate countdown timer
            countdown_seconds = None
            countdown_display = None
            next_run = None
            
            if period.enabled and not executed:
                next_run = self._get_next_run_datetime(period.time, period.repeat, now_utc)
                
                if next_run is None:
                    # Once period that has passed
                    countdown_display = "Passed"
                    countdown_seconds = -1
                else:
                    diff = next_run - now_utc
                    countdown_seconds = int(diff.total_seconds())
                    
                    # Format countdown display
                    if countdown_seconds >= 0:
                        hours = countdown_seconds // 3600
                        minutes = (countdown_seconds % 3600) // 60
                        if hours > 0:
                            countdown_display = f"{hours}h {minutes}m"
                        else:
                            countdown_display = f"{minutes}m"
            
            # Track next upcoming period - only enabled periods with valid future run times
            if (period.enabled and not executed and 
                next_run is not None and countdown_seconds is not None and 
                countdown_seconds >= 0 and countdown_seconds < min_countdown_seconds):
                min_countdown_seconds = countdown_seconds
                next_period_info = {
                    "label": period.label,
                    "time": period.time,
                    "countdown": countdown_display,
                    "countdown_seconds": countdown_seconds,
                    "message_count": len(period.messages)
                }
            
            periods.append({
                "time": period.time,
                "label": period.label,
                "participants": participants,
                "message_count": len(period.messages),
                "repeat": period.repeat,
                "enabled": period.enabled,
                "executed_today": executed,
                "countdown": countdown_display,
                "countdown_seconds": countdown_seconds
            })
        
        # Sort periods by time for better display
        periods.sort(key=lambda p: p["time"])
        
        return {
            "has_schedule": True,
            "scheduler_running": self.scheduler_running,
            "periods": periods,
            "next_period": next_period_info,
            "queued_items": queue_count
        }
    
    def pause_simulation(self) -> Dict[str, Any]:
        """Pause the ongoing simulation"""
        if not self.is_running:
            return {
                "success": False,
                "message": "No active simulation to pause"
            }
        
        self.is_paused = True
        self.db.update_simulation_state({"is_paused": True})
        logger.info("Simulation paused")
        
        return {
            "success": True,
            "message": "Simulation paused. Use /resume_simulation to continue."
        }
    
    def resume_simulation(self) -> Dict[str, Any]:
        """Resume a paused simulation"""
        if not self.is_running:
            return {
                "success": False,
                "message": "No simulation to resume. Use /start_simulation to start one."
            }
        
        if not self.is_paused:
            return {
                "success": False,
                "message": "Simulation is already running"
            }
        
        self.is_paused = False
        self.db.update_simulation_state({"is_paused": False})
        logger.info("Simulation resumed")
        
        return {
            "success": True,
            "message": "Simulation resumed."
        }
    
    def stop_simulation(self) -> Dict[str, Any]:
        """Stop the ongoing simulation"""
        if not self.is_running:
            return {
                "success": False,
                "message": "No active simulation to stop"
            }
        
        self.should_stop = True
        logger.info("Stopping simulation...")
        
        return {
            "success": True,
            "message": "Simulation stopped successfully."
        }
    
    # Queue management methods
    def check_scheduler_conflict(self) -> Dict[str, Any]:
        """Check if there's a scheduler conflict for running immediate simulation
        
        Returns conflict if scheduler is running, regardless of conversation type.
        This prevents immediate simulations from interrupting scheduled posts.
        """
        if not self.scheduler_running:
            return {"has_conflict": False, "reason": None}
        
        # Scheduler is running - there's a conflict
        # Try to get more specific info about upcoming periods
        conversation_data = self.db.get_conversation()
        if conversation_data:
            try:
                conversation = ConversationData(**conversation_data)
                if conversation.is_scheduled():
                    from datetime import timezone
                    now_utc = datetime.now(timezone.utc)
                    
                    for period in conversation.schedule:
                        if not period.enabled:
                            continue
                        
                        try:
                            hour, minute = map(int, period.time.split(':'))
                            period_time = now_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            
                            time_until = (period_time - now_utc).total_seconds()
                            
                            if time_until < 0:
                                period_time = period_time + timedelta(days=1)
                                time_until = (period_time - now_utc).total_seconds()
                            
                            if 0 <= time_until <= 1800:
                                minutes_until = int(time_until / 60)
                                return {
                                    "has_conflict": True,
                                    "reason": f"Scheduled period '{period.label}' starts in {minutes_until} minutes",
                                    "period_label": period.label,
                                    "minutes_until": minutes_until
                                }
                        except:
                            continue
            except Exception as e:
                logger.debug(f"Could not get period details: {e}")
        
        # Scheduler is running but couldn't get specific period info
        return {
            "has_conflict": True,
            "reason": "Scheduler is active with scheduled periods",
            "scheduler_active": True
        }
    
    def queue_conversation(self, conversation_data: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
        """Add an immediate conversation to the queue"""
        try:
            self.db.add_to_queue(conversation_data, reason)
            queue_count = self.db.get_queue_count()
            
            return {
                "success": True,
                "message": f"Conversation queued (position {queue_count}). Will auto-run after scheduled posts complete.",
                "queue_position": queue_count,
                "reason": reason
            }
        except Exception as e:
            logger.error(f"Error queuing conversation: {e}")
            return {
                "success": False,
                "message": f"Failed to queue conversation: {str(e)}"
            }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get the current queue status"""
        queue = self.db.get_queue()
        
        if not queue:
            return {
                "has_queued": False,
                "count": 0,
                "items": []
            }
        
        items = []
        for i, item in enumerate(queue):
            conv_data = item.get("conversation", {})
            items.append({
                "position": i + 1,
                "name": conv_data.get("name", "Unknown"),
                "queued_at": item.get("queued_at"),
                "reason": item.get("reason", "")
            })
        
        return {
            "has_queued": True,
            "count": len(queue),
            "items": items
        }
    
    async def process_queue(self, admin_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process the next item in the queue"""
        if self.scheduler_running:
            return {
                "success": False,
                "message": "Cannot process queue while scheduler is running"
            }
        
        if self.is_running:
            return {
                "success": False,
                "message": "A simulation is already running"
            }
        
        queued_conversation = self.db.pop_from_queue()
        if not queued_conversation:
            return {
                "success": False,
                "message": "No conversations in queue"
            }
        
        current_conversation = self.db.get_conversation()
        
        self.db.set_conversation(queued_conversation)
        
        if admin_callback:
            conv_name = queued_conversation.get("name", "Unknown")
            await admin_callback(f"📋 Processing queued conversation: {conv_name}")
        
        result = await self.start_simulation(admin_callback)
        
        if current_conversation:
            self.db.set_conversation(current_conversation)
        
        remaining = self.db.get_queue_count()
        if remaining > 0 and admin_callback:
            await admin_callback(f"📋 {remaining} conversation(s) still in queue")
        
        return result
    
    async def auto_process_queue_after_schedule(self, admin_callback: Optional[Callable] = None):
        """Called after scheduled periods complete to process queued conversations"""
        queue_count = self.db.get_queue_count()
        if queue_count == 0:
            return
        
        if admin_callback:
            await admin_callback(f"🔄 Processing {queue_count} queued conversation(s)...")
        
        while self.db.get_queue_count() > 0 and not self.scheduler_running:
            result = await self.process_queue(admin_callback)
            if not result.get("success"):
                logger.warning(f"Queue processing stopped: {result.get('message')}")
                break
            await asyncio.sleep(2)
