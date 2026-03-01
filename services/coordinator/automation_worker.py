import asyncio
import random
from loguru import logger
from typing import List, Dict, Optional

from core.calculators.dynamic_generator import DynamicGenerator
from core.models.news_template import NewsTemplates
from core.models.conversation import ConversationData
from core.models.message import Message, MessageType
from core.models.enums import TypingSpeed
from services.news.news_fetcher import NewsFetcher
from services.coordinator.simulation_coordinator import SimulationCoordinator
from data.repositories.config_repo import ConfigRepository

class AutomationWorker:
    """The 'Conductor' (services/coordinator/). Manages the 6 daily news automation cycles."""
    
    def __init__(self, coordinator: SimulationCoordinator, config_repo: ConfigRepository):
        self.coordinator = coordinator
        self.config_repo = config_repo
        self.is_running = False

    async def run_cycle(self, category: str = "crypto") -> bool:
        """The 'Immune System' loop: News -> Template -> Simulation."""
        logger.info(f"🚀 Triggering Automation Cycle ({category})...")
        
        # 1. Fetch News
        news = await NewsFetcher.fetch_latest(category)
        if not news:
            logger.warning("News fetch failed. Using default news topic.")
            news = {"asset": "BTC", "sentiment": "bullish", "title": "BTC stabilizes near range"}
            
        # 2. Get Template & Generate Script (80 messages)
        tpl = NewsTemplates.get_template(news["sentiment"])
        
        # Smart Session/Role Mapping
        sessions = list(self.coordinator.tg.repo.get_all_sessions().keys())
        if not sessions: 
            logger.error("No sessions available for automation.")
            return False
            
        # Shuffle sessions for variety
        random.shuffle(sessions)
        
        # Map template roles (A, B, C, etc.) to specific sessions for consistency in this converation
        # This makes the "A" persona always be the same session during the 80 msgs.
        unique_roles = list(set(msg.role for msg in tpl.script))
        role_to_session = {}
        for i, role in enumerate(unique_roles):
            role_to_session[role] = sessions[i % len(sessions)]
            
        messages = []
        base_delay = 3.0
        
        for i in range(80):
            # Select script item (looping the core script)
            t_msg = tpl.script[i % len(tpl.script)]
            
            # Persona consistency
            sender = role_to_session.get(t_msg.role, sessions[0])
            
            # 1. Potential Random Interjection (Spontaneity)
            if i > 0 and i % random.randint(7, 12) == 0:
                inter_sender = random.choice(sessions)
                inter_tag = random.choice(["interjection", "filler", "market_vibe"])
                inter_text = "{" + inter_tag + "}"
                inter_content = DynamicGenerator.resolve_placeholders(inter_text)
                
                base_delay += random.uniform(1.0, 3.0)
                messages.append(Message(
                    sender_name=inter_sender,
                    content=inter_content,
                    message_type=MessageType.TEXT,
                    delay_before=round(base_delay, 1)
                ))

            # 2. Main Script Message
            content = DynamicGenerator.resolve_placeholders(t_msg.text, {"ASSET": news["asset"]})
            
            # Dynamic Delay (Neural Rhythm)
            # Short intervals for fast chatter, longer for transitions
            step_delay = random.uniform(2.0, 5.0)
            if i % 8 == 0: step_delay += random.uniform(15, 30) # Reflection gap
            if i % 3 == 0: step_delay += random.uniform(5, 10)  # Topic shift gap
            
            base_delay += step_delay
            
            messages.append(Message(
                sender_name=sender,
                content=content,
                message_type=MessageType.TEXT,
                delay_before=round(base_delay, 1)
            ))
            
        conv = ConversationData(name=f"AutoNews: {news['title'][:30]}", messages=messages)
        
        # 3. Trigger Simulation
        conf = self.config_repo.get_config()
        raw_target = conf.get("target_group")
        
        if not raw_target: 
            logger.error("🛑 Automation Aborted: Target Group ID is not set in Settings.")
            return False
            
        try:
            target_id = int(str(raw_target).strip())
        except ValueError:
            logger.error(f"🛑 Automation Aborted: Invalid Target Group ID format: {raw_target}")
            return False
            
        logger.info(f"📊 Running {news['sentiment']} simulation for {news['asset']} in group {target_id}")
        asyncio.create_task(self.coordinator.start_simulation(conv, target_id, TypingSpeed.NORMAL))
        return True
