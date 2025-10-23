from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Getting Started", callback_data="menu_start"),
            InlineKeyboardButton(text="⭐ Features", callback_data="menu_features")
        ],
        [
            InlineKeyboardButton(text="💰 Pricing", callback_data="menu_pricing"),
            InlineKeyboardButton(text="📞 Support", callback_data="menu_support")
        ],
        [
            InlineKeyboardButton(text="🏠 Back to Main", callback_data="menu_back")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
