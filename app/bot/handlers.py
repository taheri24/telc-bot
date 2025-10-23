from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.keyboards.main_menu import main_menu_keyboard
from app.content import get_content

router = Router()

class UserState(StatesGroup):
    waiting_for_choice = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(UserState.waiting_for_choice)
    welcome_text = await get_content("welcome")
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = await get_content("support")
    await message.answer(
        help_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("menu_"))
async def process_menu_callback(callback: CallbackQuery, state: FSMContext):
    menu_item = callback.data.split("_")[1]
    
    content_files = {
        "start": "getting_started",
        "features": "features",
        "pricing": "pricing",
        "support": "support",
        "back": "welcome"
    }
    
    if menu_item in content_files:
        content = await get_content(content_files[menu_item])
        await callback.message.edit_text(
            content,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
    
    await callback.answer()

@router.message(UserState.waiting_for_choice)
async def handle_other_messages(message: Message):
    await message.answer(
        "Please use the menu buttons to navigate. 👆",
        reply_markup=main_menu_keyboard()
    )
