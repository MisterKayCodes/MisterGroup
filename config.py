# Made by Mister 💛

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    """Telegram Bot configuration"""
    token: str
    admin_id: Optional[int] = None


@dataclass
class TelethonConfig:
    """Telethon API configuration"""
    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    
    @property
    def is_configured(self) -> bool:
        return self.api_id is not None and self.api_hash is not None


@dataclass
class MediaConfig:
    """Media simulation settings"""
    max_retries: int = 2
    retry_delay: float = 1.0


@dataclass
class AppConfig:
    """Main application configuration"""
    bot: BotConfig
    telethon: TelethonConfig
    media: MediaConfig
    log_level: str = "INFO"


class ConfigError(Exception):
    """Raised when configuration is invalid"""
    pass


def _get_optional_int(key: str) -> Optional[int]:
    """Get an optional integer from environment variables"""
    value = os.getenv(key)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key} must be a valid integer")


def _get_int(key: str, default: int) -> int:
    """Get an integer from environment variables with a default"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{key} must be a valid integer")


def _get_float(key: str, default: float = 0.0) -> float:
    """Get a float from environment variables"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        raise ConfigError(f"{key} must be a valid number")


def load_config() -> AppConfig:
    """Load and validate configuration from environment variables"""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ConfigError("BOT_TOKEN not found in environment variables")
    
    admin_id = _get_optional_int("ADMIN_ID")
    api_id = _get_optional_int("API_ID")
    api_hash = os.getenv("API_HASH")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    media_max_retries = _get_int("MEDIA_MAX_RETRIES", 2)
    media_retry_delay = _get_float("MEDIA_RETRY_DELAY", 1.0)
    
    return AppConfig(
        bot=BotConfig(
            token=bot_token,
            admin_id=admin_id
        ),
        telethon=TelethonConfig(
            api_id=api_id,
            api_hash=api_hash
        ),
        media=MediaConfig(
            max_retries=media_max_retries,
            retry_delay=media_retry_delay
        ),
        log_level=log_level
    )


config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get the loaded configuration (singleton pattern)"""
    global config
    if config is None:
        config = load_config()
    return config
