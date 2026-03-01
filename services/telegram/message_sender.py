# Made by Mister 💛
import asyncio
from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import InputPhoto, InputDocument
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from core.models.message import Message
from core.models.enums import MessageType
from core.calculators.typing_speed import TypingCalculator
from core.models.enums import TypingSpeed

class SenderService:
    """The 'Hands'. Actually sends messages to the Telegram Outside World."""
    
    def __init__(self, media_service=None):
        self._media_service = media_service

    async def send_typing_action(self, client: TelegramClient, chat_id: int, duration: float):
        """Send typing action for the specified Brain-calculated duration."""
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
        speed: TypingSpeed
    ) -> bool:
        """Sends a single message to a group chat."""
        if not client or not client.is_connected():
            logger.error("Client not connected, cannot send message")
            return False
            
        try:
            # Step 1: Brain-calculated typing duration
            typing_duration = message.typing_duration
            if typing_duration is None:
                typing_duration = TypingCalculator.calculate_typing_duration(message.content, speed)
            
            logger.info(f"Simulating typing for {typing_duration:.1f}s for message from {message.sender_name}")
            await self.send_typing_action(client, chat_id, typing_duration)

            # Step 2: Media Processing
            if message.media_file_id:
                meta = message.media_meta
                if not meta:
                    logger.warning(f"Media metadata missing for {message.media_file_id}")
                    return False
                
                # Robust approach: Get the original message from the source
                source_chid = meta.get("source_channel_id")
                msg_id = meta.get("message_id")
                invite = meta.get("invite_link")
                
                async def try_send():
                    # Normalize channel ID
                    try: entity = int(source_chid)
                    except: entity = source_chid
                    
                    msgs = await client.get_messages(entity, ids=int(msg_id))
                    if msgs and msgs.media:
                        await client.send_file(chat_id, msgs.media, caption=message.content)
                        return True
                    return False

                try:
                    if source_chid and msg_id:
                        if await try_send():
                            logger.info(f"Sent validated media from source {source_chid}")
                            return True
                except Exception as e:
                    logger.warning(f"Initial media fetch failed: {e}. Attempting self-healing (join)...")
                    try:
                        # SELF-HEALING: Try to join the source channel first
                        if invite and "t.me/" in invite:
                            link = invite.split("/")[-1].replace("+", "")
                            await client(ImportChatInviteRequest(link))
                        elif source_chid and str(source_chid).startswith("@"):
                            await client(JoinChannelRequest(source_chid))
                        
                        # Retry after join
                        if await try_send():
                            logger.info("Self-healing successful! Media sent after join.")
                            return True
                    except Exception as join_err:
                        logger.error(f"Self-healing join failed for {source_chid}: {join_err}")

                # Fallback to ID sending if direct fetch fails
                m_id = meta.get("media_id") or int(message.media_file_id.split("_")[1])
                access_hash = meta["access_hash"]
                ref = bytes.fromhex(meta["file_reference"]) if meta.get("file_reference") else b''
                
                media = None
                if message.media_type == MessageType.PHOTO:
                    media = InputPhoto(id=m_id, access_hash=access_hash, file_reference=ref)
                elif message.media_type == MessageType.VIDEO:
                    media = InputDocument(id=m_id, access_hash=access_hash, file_reference=ref)
                
                if media:
                    await client.send_file(chat_id, media, caption=message.content)
                    logger.info(f"Sent media by ID ({message.media_type}) from {message.sender_name}")
                    return True

            if message.message_type == MessageType.TEXT:
                await client.send_message(chat_id, message.content)
                logger.info(f"Sent text message from {message.sender_name}")
                return True
        except Exception as e:
            logger.error(f"Error sending message from {message.sender_name}: {e}")
            return False
