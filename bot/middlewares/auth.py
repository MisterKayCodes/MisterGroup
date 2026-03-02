# Made by Mister 💛
from typing import Any, Callable, Dict, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from bot.states.app_states import AuthStates
from data.repositories.config_repo import ConfigRepository

class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:
        print(f"DEBUG: Middleware received event: {event}")
        # Get user from message or callback
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if not user:
            print(f"DEBUG: Update without user: {event}")
            return await handler(event, data)

        print(f"DEBUG: Update from user {user.id} ({user.username}): {event}")

        # Skip auth for /start (the entry point)
        if isinstance(event, Message) and event.text in ["/start", "/ping"]:
            if isinstance(event, Message) and event.text == "/ping":
                await event.answer("🏓 Pong! Bot is alive.")
            return await handler(event, data)

        # --- MOVE THIS UP HERE ---
        state = data.get("state") 

        # Get repository
        config_repo: ConfigRepository = data.get("config_repo")
        if not config_repo:
            return await handler(event, data)

        # Check authentication (The 'Key' in the Vault)
        # print(f"DEBUG: Checking auth for user {user.id}")
        is_auth = config_repo.is_user_authenticated(user.id)
        # print(f"DEBUG: is_auth={is_auth}")
        
        if is_auth:
            if state: # Now 'state' is defined and won't crash!
                curr = await state.get_state()
                if curr: 
                    await state.clear()
            return await handler(event, data)

        # Allow PIN entry state (The 'Checking Room')
        if state:
            current_state = await state.get_state()
            if current_state == AuthStates.WAITING_FOR_PIN:
                return await handler(event, data)

        # Otherwise, block and redirect to start
        if isinstance(event, Message):
            await event.answer("🔐 <b>Access Denied.</b> You are not authorized. Use /start to log in.")
        elif isinstance(event, CallbackQuery):
            await event.answer("🔐 Access Denied. Use /start.", show_alert=True)
        
        return None