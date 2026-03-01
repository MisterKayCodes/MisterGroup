# Made by Mister 💛
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.keyboards.labels import MainButtons

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """The 'Mouth' buttons for the main menu."""
    builder = ReplyKeyboardBuilder()
    
    # 2 columns per row
    buttons = [
        MainButtons.LAZY_START, MainButtons.STATUS,
        MainButtons.SIMULATION, MainButtons.SESSIONS, 
        MainButtons.SCHEDULE, MainButtons.MEDIA, 
        MainButtons.SETTINGS, MainButtons.HELP
    ]
    
    for btn in buttons:
        builder.button(text=btn)
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_back_button_keyboard() -> ReplyKeyboardMarkup:
    """Simple back button for navigation."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 Back")
    return builder.as_markup(resize_keyboard=True)
