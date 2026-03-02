# Made by Mister 💛
import asyncio
from datetime import datetime, timezone
from loguru import logger
from typing import Dict, List, Any, Optional

from core.simulation.scheduler_logic import SchedulerLogic
from core.models.conversation import ConversationData
from core.models.period import ScheduledPeriod
from core.models.message import Message
from core.models.enums import TypingSpeed
from core.events import CoreEvents, EventStatus
from services.event_bus import EventBus
from services.coordinator.simulation_coordinator import SimulationCoordinator
from data.repositories.config_repo import ConfigRepository
import dataclasses

class BackgroundScheduler:
    """The 'Rhythmic Nervous System'. Manages scheduled tasks using Brain logic."""
    
    def __init__(self, coordinator: SimulationCoordinator, eb: EventBus, repo: ConfigRepository, automation: Optional[Any] = None):
        self.coordinator = coordinator
        self.eb = eb
        self.repo = repo
        self.automation = automation
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.executed_today: List[str] = []

    async def start(self):
        if self.running: return
        self.running = True
        self.task = asyncio.create_task(self._scheduler_loop())
        await self.eb.emit(CoreEvents.SIMULATION_STARTED, EventStatus.STARTED, message="Scheduler task started")

    async def stop(self):
        self.running = False
        if self.task:
            self.task.cancel()
            self.task = None
        await self.eb.emit(CoreEvents.SIMULATION_STOPPED, EventStatus.STOPPED, message="Scheduler task stopped")

    def get_automation_status(self) -> Dict[str, Any]:
        """Calculates the time left until the next automation cycle."""
        conf = self.repo.get_config()
        if not conf.get("automation_enabled"):
            return {"enabled": False}
        
        import time
        now_ts = time.time()
        last_ts = self.repo.get_last_automation_timestamp()
        interval_hrs = self.repo.get_automation_interval()
        interval_sec = interval_hrs * 3600
        
        elapsed = now_ts - last_ts
        remaining_sec = max(0, interval_sec - elapsed)
        remaining_min = int(remaining_sec / 60)
        
        return {
            "enabled": True,
            "minutes_left": remaining_min,
            "pending_messages": 80 # AutomationWorker consistently generates 80
        }

    async def _scheduler_loop(self):
        logger.info("Scheduler loop started")
        while self.running:
            try:
                # 1. Fetch config and check Automation Cycle (Dynamic Interval)
                conf = self.repo.get_config()
                if self.automation and conf.get("automation_enabled"):
                    import time
                    now_ts = time.time()
                    last_ts = self.repo.get_last_automation_timestamp()
                    interval_hrs = self.repo.get_automation_interval()
                    interval_sec = interval_hrs * 3600
                    
                    if (now_ts - last_ts) >= interval_sec:
                        self.repo.set_last_automation_timestamp(now_ts)
                        logger.info(f"Triggering {interval_hrs}-hour News Cycle")
                        asyncio.create_task(self.automation.run_cycle())

                # 2. Fetch Manual Conversation from Vault
                conv_data = self.repo.get_conversation()
                if not conv_data or not conf.get("target_group"):
                    await asyncio.sleep(30); continue
                
                # 3. Decision Intelligence in Brain (core)
                # Reconstruct from Vault
                try:
                    conversation = ConversationData(
                        name=conv_data["name"],
                        mode=conv_data.get("mode", "immediate"),
                        schedule=[ScheduledPeriod(**p) if isinstance(p, dict) else p for p in conv_data.get("schedule", [])],
                        messages=[Message(**m) if isinstance(m, dict) else m for m in conv_data.get("messages", [])]
                    )
                    # Also reconstruct nested messages in schedule
                    for p in conversation.schedule:
                        p.messages = [Message(**m) if isinstance(m, dict) else m for m in p.messages]
                except Exception as e:
                    logger.error(f"Failed to reconstruct conversation: {e}")
                    await asyncio.sleep(30); continue
                
                if not conversation.is_scheduled():
                    await asyncio.sleep(30); continue
                
                now_utc = datetime.now(timezone.utc)
                # Cleanup old days
                today_date = now_utc.date().isoformat()
                self.executed_today = [e for e in self.executed_today if today_date in e]
                
                # 4. Decision & Execution for Scheduled Periods
                for period in conversation.schedule:
                    if SchedulerLogic.should_run_period(period, now_utc, self.executed_today):
                        self.executed_today.append(f"{period.label}_{today_date}")
                        
                        speed_str = conf.get("typing_speed", "normal")
                        speed = TypingSpeed(speed_str)
                        target_group = conf.get("target_group")
                        
                        logger.info(f"Triggering scheduled period: {period.label}")
                        await self.coordinator.run_period_messages(period, target_group, speed)
                        
                        # Once-only auto-disable logic
                        if period.repeat.lower() == "once":
                            period.enabled = False
                            self.repo.set_conversation(dataclasses.asdict(conversation))
                
                await asyncio.sleep(30)

                await asyncio.sleep(30)
            except asyncio.CancelledError: break
            except Exception as e:
                logger.error(f"Error in scheduler loop (service): {e}")
                await asyncio.sleep(30)
