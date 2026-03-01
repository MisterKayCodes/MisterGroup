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
        # Get user from message or callback
        user = None
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if not user:
            return await handler(event, data)

        # Skip auth for /start (the entry point)
        if isinstance(event, Message) and event.text == "/start":
            return await handler(event, data)

        # Get repository
        config_repo: ConfigRepository = data.get("config_repo")
        if not config_repo:
            return await handler(event, data)

        # Check authentication (The 'Key' in the Vault)
        if config_repo.is_user_authenticated(user.id):
            if state:
                curr = await state.get_state()
                if curr: # If they somehow got stuck in a state, clear it
                    await state.clear()
            return await handler(event, data)

        # Allow PIN entry state (The 'Checking Room')
        state = data.get("state")
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
