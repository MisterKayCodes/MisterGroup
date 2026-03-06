# Made by Mister 💛
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from loguru import logger
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from core.models.message import Message
from core.models.conversation import ConversationData
from core.models.period import ScheduledPeriod
from core.models.enums import TypingSpeed, MessageType
from core.simulation.status import SimulationState
from core.events import CoreEvents, EventStatus
from services.event_bus import EventBus
from services.telegram.client_manager import TelegramService
from services.telegram.message_sender import SenderService
from data.repositories.media_repo import MediaRepository
from core.calculators.media_parser import MediaParser
import json

class SimulationCoordinator:
    """The 'Nervous System' core. Coordinates the Brain (models) and Nerves (services)."""
    
    def __init__(self, telegram_service: TelegramService, sender: SenderService, event_bus: EventBus, media_repo: MediaRepository):
        self.tg = telegram_service
        self.sender = sender
        self.eb = event_bus
        self.media_repo = media_repo
        self.state = SimulationState()
        self.last_latency = 0

    def stop_simulation(self):
        self.state.should_stop = True
        logger.info("Simulation stop internal signal sent")

    def pause_simulation(self):
        self.state.is_paused = True
        logger.info("Simulation pause internal signal sent")

    def resume_simulation(self):
        self.state.is_paused = False
        logger.info("Simulation resume internal signal sent")

    async def join_group(self, group_link: str, session_names: List[str]) -> Dict[str, Any]:
        """Orchestrate multiple 'Hands' (Clients) to join a specific group link."""
        results = {"success": [], "failed": []}
        
        # Parse link
        is_invite = "/joinchat/" in group_link or "+" in group_link
        entity = group_link.split('/')[-1].replace('+', '') if is_invite else group_link.replace('@', '')

        for name in session_names:
            client = await self.tg.get_client(name)
            if not client:
                results["failed"].append(f"{name}: Connection error")
                continue
                
            try:
                if is_invite:
                    await client(ImportChatInviteRequest(entity))
                else:
                    await client(JoinChannelRequest(entity))
                results["success"].append(name)
                logger.info(f"Session {name} joined {group_link}")
            except Exception as e:
                # Check for "already in" error
                if "already" in str(e).lower():
                    results["success"].append(name)
                else:
                    results["failed"].append(f"{name}: {str(e)}")
            
            # Anti-flood delay
            await asyncio.sleep(2)
            
        return results

    async def _resolve_media_tags(self, message: Message):
        """Brain: Resolve Media Tags [TAG] with Guard and clean content."""
        try:
            tags = MediaParser.extract_tags(message.content)
            if not tags:
                return

            tag = tags[0]
            # Clean tags from text immediately to satisfy "even if media doesn't exist"
            message.content = MediaParser.remove_tags(message.content)

            # Look for category matching the tag
            cat = self.media_repo.get_category_by_tag(tag)
            if cat:
                ranges = cat["index_ranges"]
                indices = []
                for r in ranges: indices.extend(range(r[0], r[1] + 1))
                
                ptr = cat["current_pointer"]
                if ptr >= len(indices): ptr = 0
                
                target_idx = indices[ptr]
                media_items = cat["media_items"]
                if target_idx < len(media_items):
                    item = media_items[target_idx]
                    item["source_channel_id"] = cat["source_channel_id"]
                    message.media_file_id = item["file_id"]
                    message.media_meta = item
                    message.media_type = MessageType(item["media_type"])
                    self.media_repo.update_pointer(cat["id"], ptr + 1)
                    logger.info(f"Resolved tag [{tag}] to media item {target_idx}")
                else:
                    logger.warning(f"Media item at index {target_idx} not found for tag {tag}")
            else:
                logger.debug(f"No media category found for tag {tag}. Tag removed from text.")
        except Exception as e:
            logger.error(f"Media Tag Resolution Error: {e}")

    async def run_period_messages(
        self,
        period: ScheduledPeriod,
        target_group: int,
        speed: TypingSpeed
    ) -> Dict[str, Any]:
        """Process messages for a specified Brain-calculated 'period'."""
        if isinstance(speed, str): speed = TypingSpeed(speed)
        successful = 0
        failed = 0
        
        await self.eb.emit(CoreEvents.PERIOD_STARTED, EventStatus.STARTED, data=period.label)
        
        # Ensure messages are objects
        messages = []
        for m in period.messages:
            if isinstance(m, dict): messages.append(Message(**m))
            else: messages.append(m)
        
        for i, message in enumerate(messages):
            if self.state.should_stop: break
            while self.state.is_paused and not self.state.should_stop:
                await asyncio.sleep(0.5)
            
            # Resolve tags before sending
            await self._resolve_media_tags(message)

            client = await self.tg.get_client(message.sender_name)
            if not client:
                failed += 1
                continue
            
            if message.delay_before > 0:
                await asyncio.sleep(message.delay_before)
            
            success = await self.sender.send_message(message, client, target_group, speed)
            if success: successful += 1
            else: failed += 1
            self.state.current_index += 1
        
        await self.eb.emit(CoreEvents.PERIOD_COMPLETED, EventStatus.COMPLETED, data=period.label)
        return {"successful": successful, "failed": failed, "period_label": period.label}

    async def start_simulation(self, conversation: ConversationData, target_group: int, speed: TypingSpeed):
        """Logic for immediate flat conversation simulation."""
        if isinstance(speed, str): speed = TypingSpeed(speed)
        import time
        self.state.reset_counts()
        self.state.is_running = True
        self.state.total_to_send = len(conversation.messages)
        self.state.target_group = target_group
        
        await self.eb.emit(CoreEvents.SIMULATION_STARTED, EventStatus.STARTED)
        
        # Ensure messages are objects for dot notation
        messages = []
        for m in conversation.messages:
            if isinstance(m, dict):
                # Handle nested enums if necessary, but Message() init should handle strings
                messages.append(Message(**m))
            else:
                messages.append(m)
        
        for i in range(self.state.current_index, self.state.total_to_send):
            if self.state.should_stop: break
            while self.state.is_paused and not self.state.should_stop:
                await asyncio.sleep(0.5)
            
            message = messages[i]
            
            # Resolve Media Tags [TAG]
            await self._resolve_media_tags(message)

            # Hand: Client Retrieval and Send with individual Guard
            try:
                client = await self.tg.get_client(message.sender_name)
                if not client:
                    self.state.failed_count += 1
                    continue
                
                if message.delay_before > 0:
                    await asyncio.sleep(message.delay_before)
                
                start_msg = time.perf_counter()
                success = await self.sender.send_message(message, client, target_group, speed)
                self.last_latency = (time.perf_counter() - start_msg) * 1000
                
                if success: self.state.successful_count += 1
                else: self.state.failed_count += 1
            except Exception as e:
                logger.error(f"Message Send Loop Error for {message.sender_name}: {e}")
                self.state.failed_count += 1
                
            self.state.current_index = i + 1
            
        self.state.is_running = False
        await self.eb.emit(CoreEvents.SIMULATION_STOPPED, EventStatus.COMPLETED if not self.state.should_stop else EventStatus.STOPPED)
