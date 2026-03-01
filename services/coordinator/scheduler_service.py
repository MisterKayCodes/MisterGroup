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

    async def _scheduler_loop(self):
        logger.info("Scheduler loop started")
        while self.running:
            try:
                # 1. Fetch from Vault via Repository
                conv_data = self.repo.get_conversation()
                conf = self.repo.get_config()
                if not conv_data or not conf.get("target_group"):
                    await asyncio.sleep(30); continue
                
                # 2. Check Decision Intelligence in Brain (core)
                # 2. Deep Reconstruction from Vault
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
                
                # 3. Decision & Execution
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
                
                # 4. Automation Cycle (Every 4 Hours: 00, 04, 08, 12, 16, 20)
                if self.automation and conf.get("automation_enabled"):
                    h = datetime.now().hour
                    last_h = self.repo.get_last_automation_hour()
                    
                    if h % 4 == 0 and h != last_h:
                        self.repo.set_last_automation_hour(h)
                        logger.info(f"Triggering 4-hour News Cycle for hour {h}")
                        asyncio.create_task(self.automation.run_cycle())

                await asyncio.sleep(30)
            except asyncio.CancelledError: break
            except Exception as e:
                logger.error(f"Error in scheduler loop (service): {e}")
                await asyncio.sleep(30)
