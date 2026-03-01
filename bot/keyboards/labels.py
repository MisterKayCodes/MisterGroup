# Made by Mister 💛
from enum import Enum

class MainButtons(str, Enum):
    STATUS = "📊 Status"
    SESSIONS = "👤 Sessions"
    SCHEDULE = "⏰ Schedule"
    SIMULATION = "🚀 Run Now"
    MEDIA = "🎬 Media Setup"
    SETTINGS = "⚙️ Settings"
    HELP = "❓ Help"
    LAZY_START = "🚀 LAZY START"

class SessionControlButtons(str, Enum):
    LIST = "📋 List Sessions"
    ADD = "➕ Add Account"
    TEST = "🧪 Test All"
    PAUSE_RESUME = "⏯️ Pause/Resume All"
    BACK = "🔙 Back"

class SimulationControlButtons(str, Enum):
    UPLOAD = "📥 Upload JSON"
    CONVERT = "✍️ Convert Text"
    PREVIEW = "📺 Preview List"
    START = "▶️ Start Simulation"
    STOP = "⏹️ Stop"
    PAUSE = "⏸️ Pause"
    RESUME = "⏯️ Resume"
    BACK = "🔙 Back"

class SettingsButtons(str, Enum):
    SET_GROUP = "🎯 Set Target Group"
    TYPING_SPEED = "⚡ Typing Speed"
    JOIN_GROUP = "🤝 Join Group"
    BACK = "🔙 Back"
