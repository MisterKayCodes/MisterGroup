# Made by Mister 💛

import asyncio
from typing import Optional, Dict, List, Any
from pathlib import Path
from loguru import logger
from telethon import TelegramClient
from telethon.sessions import StringSession
from datetime import datetime

from src.utils.database import Database
from src.models.session import TelethonSession, SessionStatus


class SessionManager:
    """Manages Telethon sessions for the bot"""
    
    def __init__(self, db: Database, api_id: int, api_hash: str):
        self.db = db
        self.api_id = api_id
        self.api_hash = api_hash
        self.active_clients: Dict[str, TelegramClient] = {}
        
    async def add_session(self, name: str, phone: Optional[str] = None, session_string: Optional[str] = None) -> Dict[str, Any]:
        """Add a new Telethon session"""
        try:
            # Create new session
            if session_string:
                session = StringSession(session_string)
            else:
                session = StringSession()
            
            client = TelegramClient(session, self.api_id, self.api_hash)
            
            # Connect and get user info
            await client.connect()
            
            if not await client.is_user_authorized():
                if phone:
                    # This will require phone verification
                    return {
                        "success": False,
                        "message": "Session requires authorization. Please provide session string from authorized session.",
                        "needs_auth": True
                    }
                else:
                    return {
                        "success": False,
                        "message": "Session not authorized and no phone provided",
                        "needs_auth": True
                    }
            
            # Get user info
            me = await client.get_me()
            session_str = session.save()
            
            # Create session model
            session_data = TelethonSession(
                name=name,
                phone=phone or me.phone,
                status=SessionStatus.ACTIVE,
                session_string=session_str,
                last_tested=datetime.now(),
                is_connected=True,
                user_id=me.id,
                username=me.username
            )
            
            # Save to database
            self.db.add_session(name, session_data.model_dump(mode='json'))
            
            # Store active client
            self.active_clients[name] = client
            
            logger.info(f"Session {name} added successfully for user @{me.username}")
            
            return {
                "success": True,
                "message": f"Session added successfully for @{me.username}",
                "session": session_data.model_dump(mode='json')
            }
            
        except Exception as e:
            logger.error(f"Error adding session {name}: {e}")
            return {
                "success": False,
                "message": f"Error adding session: {str(e)}"
            }
    
    async def get_client(self, name: str) -> Optional[TelegramClient]:
        """Get or create Telegram client for a session"""
        # Check if already connected
        if name in self.active_clients:
            if self.active_clients[name].is_connected():
                return self.active_clients[name]
        
        # Load from database
        session_data = self.db.get_session(name)
        if not session_data:
            logger.warning(f"Session {name} not found in database")
            return None
        
        # Check if session is paused
        if session_data.get("status") == SessionStatus.PAUSED.value:
            logger.info(f"Session {name} is paused, skipping")
            return None
        
        try:
            # Create client from session string
            session_string = session_data.get("session_string")
            if not session_string:
                logger.error(f"No session string for {name}")
                return None
            
            session = StringSession(session_string)
            client = TelegramClient(session, self.api_id, self.api_hash)
            
            await client.connect()
            
            if not await client.is_user_authorized():
                logger.error(f"Session {name} is not authorized")
                return None
            
            self.active_clients[name] = client
            logger.info(f"Client for session {name} connected successfully")
            
            return client
            
        except Exception as e:
            logger.error(f"Error getting client for session {name}: {e}")
            return None
    
    async def test_session(self, name: str) -> Dict[str, Any]:
        """Test if a session is active and valid"""
        try:
            session_data = self.db.get_session(name)
            if not session_data:
                return {
                    "success": False,
                    "message": f"Session '{name}' not found"
                }
            
            # Try to connect
            client = await self.get_client(name)
            if not client:
                return {
                    "success": False,
                    "message": f"Failed to connect session '{name}'"
                }
            
            # Get user info
            me = await client.get_me()
            
            # Update last tested time
            session_data["last_tested"] = datetime.now().isoformat()
            session_data["is_connected"] = True
            self.db.add_session(name, session_data)
            
            return {
                "success": True,
                "message": f"Session '{name}' is active",
                "user": f"@{me.username} (ID: {me.id})"
            }
            
        except Exception as e:
            logger.error(f"Error testing session {name}: {e}")
            
            # Update session status
            session_data = self.db.get_session(name)
            if session_data:
                session_data["is_connected"] = False
                session_data["last_tested"] = datetime.now().isoformat()
                self.db.add_session(name, session_data)
            
            return {
                "success": False,
                "message": f"Session test failed: {str(e)}"
            }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all registered sessions"""
        sessions = self.db.get_all_sessions()
        return list(sessions.values())
    
    def remove_session(self, name: str) -> bool:
        """Remove a session"""
        # Disconnect client if active
        if name in self.active_clients:
            try:
                asyncio.create_task(self.active_clients[name].disconnect())
            except:
                pass
            del self.active_clients[name]
        
        # Remove from database
        return self.db.remove_session(name)
    
    def pause_session(self, name: str) -> bool:
        """Pause a session"""
        session = self.db.get_session(name)
        if session:
            self.db.update_session_status(name, SessionStatus.PAUSED.value)
            logger.info(f"Session {name} paused")
            return True
        return False
    
    def resume_session(self, name: str) -> bool:
        """Resume a paused session"""
        session = self.db.get_session(name)
        if session:
            self.db.update_session_status(name, SessionStatus.ACTIVE.value)
            logger.info(f"Session {name} resumed")
            return True
        return False
    
    def pause_all_sessions(self) -> int:
        """Pause all sessions"""
        sessions = self.db.get_all_sessions()
        count = 0
        for name in sessions.keys():
            if self.pause_session(name):
                count += 1
        logger.info(f"Paused {count} sessions")
        return count
    
    def resume_all_sessions(self) -> int:
        """Resume all sessions"""
        sessions = self.db.get_all_sessions()
        count = 0
        for name in sessions.keys():
            if self.resume_session(name):
                count += 1
        logger.info(f"Resumed {count} sessions")
        return count
    
    async def disconnect_all(self):
        """Disconnect all active clients"""
        for name, client in list(self.active_clients.items()):
            try:
                await client.disconnect()
                logger.info(f"Disconnected client {name}")
            except Exception as e:
                logger.error(f"Error disconnecting client {name}: {e}")
        self.active_clients.clear()
    
    async def join_all_to_group(self, group_link: str, callback=None) -> Dict[str, Any]:
        """Make all sessions join a group via invite link or username"""
        from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
        from telethon.tl.functions.channels import JoinChannelRequest
        from telethon.tl.types import Channel, Chat, ChatInviteAlready, ChatInvite
        from telethon.errors import (
            UserAlreadyParticipantError, InviteHashExpiredError, InviteHashInvalidError,
            FloodWaitError, ChannelPrivateError, ChatAdminRequiredError, UserBannedInChannelError,
            UsernameNotOccupiedError, UsernameInvalidError
        )
        import re
        
        sessions = self.db.get_all_sessions()
        if not sessions:
            return {"success": False, "message": "No sessions available", "results": []}
        
        results = []
        success_count = 0
        already_member_count = 0
        failed_count = 0
        group_info = None
        
        def parse_invite_link(link: str) -> tuple:
            """Parse different Telegram link formats and return (type, value)"""
            link = link.strip()
            
            private_patterns = [
                r't\.me/\+([a-zA-Z0-9_-]+)',
                r't\.me/joinchat/([a-zA-Z0-9_-]+)',
                r'telegram\.me/\+([a-zA-Z0-9_-]+)',
                r'telegram\.me/joinchat/([a-zA-Z0-9_-]+)',
            ]
            for pattern in private_patterns:
                match = re.search(pattern, link)
                if match:
                    return ("invite", match.group(1))
            
            public_patterns = [
                r't\.me/([a-zA-Z][a-zA-Z0-9_]{3,})',
                r'telegram\.me/([a-zA-Z][a-zA-Z0-9_]{3,})',
            ]
            for pattern in public_patterns:
                match = re.search(pattern, link)
                if match:
                    return ("username", match.group(1))
            
            if link.startswith("@"):
                return ("username", link[1:])
            
            if re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,}$', link):
                return ("username", link)
            
            return (None, None)
        
        def extract_group_info(entity) -> dict:
            """Safely extract group info from various entity types"""
            info = {"id": None, "title": "Unknown", "type": "unknown"}
            try:
                if hasattr(entity, 'id'):
                    chat_id = entity.id
                    if hasattr(entity, 'megagroup') or hasattr(entity, 'broadcast'):
                        chat_id = int(f"-100{entity.id}")
                    info["id"] = str(chat_id)
                if hasattr(entity, 'title'):
                    info["title"] = entity.title
                if isinstance(entity, Channel):
                    info["type"] = "supergroup" if getattr(entity, 'megagroup', False) else "channel"
                elif isinstance(entity, Chat):
                    info["type"] = "group"
                else:
                    info["type"] = "group/channel"
            except Exception as e:
                logger.warning(f"Error extracting group info: {e}")
            return info
        
        link_type, link_value = parse_invite_link(group_link)
        if not link_type:
            return {"success": False, "message": "Invalid group link format", "results": []}
        
        for name, session_data in sessions.items():
            if session_data.get("status") == "paused":
                results.append({"name": name, "status": "skipped", "reason": "Session paused"})
                continue
            
            try:
                client = await self.get_client(name)
                if not client:
                    results.append({"name": name, "status": "failed", "reason": "Could not connect"})
                    failed_count += 1
                    continue
                
                if callback:
                    await callback(f"🔄 Joining with {name}...")
                
                try:
                    if link_type == "invite":
                        try:
                            check_result = await client(CheckChatInviteRequest(link_value))
                            if isinstance(check_result, ChatInviteAlready):
                                results.append({"name": name, "status": "already_member", "reason": "Already a member"})
                                already_member_count += 1
                                if not group_info and hasattr(check_result, 'chat'):
                                    group_info = extract_group_info(check_result.chat)
                                await asyncio.sleep(1)
                                continue
                        except Exception:
                            pass
                        
                        updates = await client(ImportChatInviteRequest(link_value))
                        if hasattr(updates, 'chats') and updates.chats:
                            chat = updates.chats[0]
                            if not group_info:
                                group_info = extract_group_info(chat)
                        
                        results.append({"name": name, "status": "joined", "reason": "Successfully joined"})
                        success_count += 1
                        logger.info(f"Session {name} joined group via invite successfully")
                    
                    else:
                        entity = await client.get_entity(link_value)
                        if not group_info:
                            group_info = extract_group_info(entity)
                        
                        await client(JoinChannelRequest(entity))
                        results.append({"name": name, "status": "joined", "reason": "Successfully joined"})
                        success_count += 1
                        logger.info(f"Session {name} joined channel @{link_value} successfully")
                    
                except UserAlreadyParticipantError:
                    results.append({"name": name, "status": "already_member", "reason": "Already a member"})
                    already_member_count += 1
                    if not group_info and link_type == "username":
                        try:
                            entity = await client.get_entity(link_value)
                            group_info = extract_group_info(entity)
                        except:
                            pass
                    
                except (InviteHashExpiredError, InviteHashInvalidError):
                    results.append({"name": name, "status": "failed", "reason": "Invalid or expired invite link"})
                    failed_count += 1
                    
                except FloodWaitError as e:
                    results.append({"name": name, "status": "failed", "reason": f"Rate limited, wait {e.seconds}s"})
                    failed_count += 1
                    logger.warning(f"FloodWait for {name}: {e.seconds}s")
                    if e.seconds < 60:
                        await asyncio.sleep(e.seconds + 1)
                    
                except (ChannelPrivateError, ChatAdminRequiredError):
                    results.append({"name": name, "status": "failed", "reason": "Cannot join (private/admin required)"})
                    failed_count += 1
                    
                except UserBannedInChannelError:
                    results.append({"name": name, "status": "failed", "reason": "User is banned from this group"})
                    failed_count += 1
                    
                except (UsernameNotOccupiedError, UsernameInvalidError):
                    results.append({"name": name, "status": "failed", "reason": "Username not found or invalid"})
                    failed_count += 1
                    break
                    
                await asyncio.sleep(2)
                
            except Exception as e:
                results.append({"name": name, "status": "failed", "reason": str(e)[:50]})
                failed_count += 1
                logger.error(f"Error joining group with session {name}: {e}")
        
        if group_info and group_info.get("id"):
            group_data = {
                "id": group_info["id"],
                "title": group_info["title"],
                "type": group_info["type"],
                "link": group_link,
                "joined_at": datetime.now().isoformat(),
                "members_joined": [r["name"] for r in results if r["status"] in ["joined", "already_member"]],
                "simulation_active": False
            }
            self.db.add_group(group_info["id"], group_data)
        
        return {
            "success": success_count > 0 or already_member_count > 0,
            "message": f"Joined: {success_count}, Already member: {already_member_count}, Failed: {failed_count}",
            "results": results,
            "group_info": group_info
        }
    
    async def get_groups_with_status(self) -> List[Dict[str, Any]]:
        """Get all groups with their simulation status"""
        groups = self.db.get_all_groups()
        sim_state = self.db.get_simulation_state()
        config = self.db.get_config()
        
        result = []
        for group_id, group_data in groups.items():
            is_target = str(config.get("target_group")) == str(group_id)
            is_active = sim_state.get("is_running", False) and is_target
            
            result.append({
                "id": group_id,
                "title": group_data.get("title", "Unknown"),
                "type": group_data.get("type", "unknown"),
                "members_count": len(group_data.get("members_joined", [])),
                "simulation_active": is_active,
                "is_target": is_target,
                "joined_at": group_data.get("joined_at")
            })
        
        return result
