from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from handlers.packages import PACKAGE_MODULES

# Основная клавиатура
def bottom_kb():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Написать в поддержку"))
    return keyboard

# Клавиатура для выбора активностей
def activities_keyboard(selected=None):
    selected = selected or []
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    for name in PACKAGE_MODULES:
        text = f"{'✅ ' if name in selected else ''}{name}"
        keyboard.add(InlineKeyboardButton(text=text, callback_data=f"activity_{name}"))
        
    keyboard.add(InlineKeyboardButton("🟢 Готово", callback_data="done"))
    return keyboard
