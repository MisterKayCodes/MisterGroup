# Made by Mister 💛
from aiogram.fsm.state import State, StatesGroup

class SessionStates(StatesGroup):
    WAITING_FOR_NAME = State()
    WAITING_FOR_SESSION_STRING = State()

class AuthStates(StatesGroup):
    WAITING_FOR_PIN = State()

class SettingsStates(StatesGroup):
    WAITING_FOR_TARGET_GROUP = State()
    WAITING_FOR_TYPING_SPEED = State()
    WAITING_FOR_JOIN_LINK = State()

class SimulationStates(StatesGroup):
    WAITING_FOR_JSON_UPLOAD = State()
    WAITING_FOR_TEXT_CONVERSION = State()
    WAITING_FOR_TXT_UPLOAD = State()

class MediaStates(StatesGroup):
    WAITING_FOR_CHANNEL = State()
    WAITING_FOR_CATEGORIES = State()
    SELECTING_CHANNEL = State()
