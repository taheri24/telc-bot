from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.config import request_id as request_id_ctx
from app.logger import request_logger
from app.utils.panic_recovery import panic, recover, recovery_context, must, must_not_none
from app.utils.developer_errors import (
    assert_developer, 
    check_state, 
    check_argument,
    unsupported_operation
)
from app.keyboards.main_menu import main_menu_keyboard
from app.content import get_content

router = Router()

class UserState(StatesGroup):
    waiting_for_choice = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = message.from_user
    current_request_id = request_id_ctx.get()
    
    # Use assertion for developer errors (removed in production with -O flag)
    assert_developer(user is not None, "User should not be None in command start")
    
    request_logger.info(
        f"User started the bot",
        extra={
            "request_id": current_request_id,
            "user_id": user.id,
            "username": user.username
        }
    )
    
    await state.set_state(UserState.waiting_for_choice)
    
    # Use recover to handle potential panics in content loading
    @recover(default="# Welcome! Content temporarily unavailable.")
    def load_welcome_content():
        content = get_content("welcome")
        if content is None:
            panic("Welcome content not found")
        return content
    
    welcome_text = await load_welcome_content()
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )
    
    request_logger.debug(
        f"Start message sent",
        extra={"request_id": current_request_id, "user_id": user.id}
    )

@router.message(Command("panic_test"))
@recover(default="✅ Panic was recovered successfully!")
async def cmd_panic_test(message: Message):
    """Test command to demonstrate panic/recovery."""
    # This will panic but be recovered by the decorator
    panic("This is a test panic from panic_test command!")
    return "This line will never be reached"

@router.message(Command("assert_test"))
async def cmd_assert_test(message: Message):
    """Test command for developer assertions."""
    # This will raise AssertionError (developer mistake)
    assert_developer(False, "This is a test developer assertion failure")
    await message.answer("This will not be reached")

@router.message(Command("state_test"))
async def cmd_state_test(message: Message):
    """Test command for state checking."""
    invalid_state = True
    # This will raise RuntimeError for invalid state
    check_state(not invalid_state, "Bot is in invalid state for this operation")
    await message.answer("State is valid")

@router.callback_query(F.data.startswith("menu_"))
@recover(default="❌ Error loading content. Please try again.")
async def process_menu_callback(callback: CallbackQuery, state: FSMContext):
    user = callback.from_user
    menu_item = callback.data.split("_")[1]
    current_request_id = request_id_ctx.get()
    
    # Check arguments - this is a client input validation
    check_argument(len(menu_item) > 0, "Menu item cannot be empty")
    
    request_logger.info(
        f"User selected menu item",
        extra={
            "request_id": current_request_id,
            "user_id": user.id,
            "menu_item": menu_item
        }
    )
    
    content_files = {
        "start": "getting_started",
        "features": "features",
        "pricing": "pricing",
        "support": "support",
        "back": "welcome"
    }
    
    # Use must for critical conditions that should never fail
    must(menu_item in content_files, f"Unknown menu item: {menu_item}")
    
    content_name = content_files[menu_item]
    
    # Using recovery context instead of decorator
    with recovery_context(default="# Content temporarily unavailable."):
        content = await get_content(content_name)
        must_not_none(content, f"Content '{content_name}' not found")
        
        await callback.message.edit_text(
            content,
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )
        
        request_logger.debug(
            f"Content sent successfully",
            extra={
                "request_id": current_request_id,
                "user_id": user.id,
                "content_type": content_name
            }
        )
    
    await callback.answer()

@router.message(Command("unsupported"))
async def cmd_unsupported(message: Message):
    """Test command for unsupported operations."""
    # This will raise NotImplementedError
    unsupported_operation("This feature is not yet implemented")
    await message.answer("This will not be reached")

@router.message(UserState.waiting_for_choice)
async def handle_other_messages(message: Message):
    user = message.from_user
    current_request_id = request_id_ctx.get()
    
    request_logger.info(
        f"User sent unexpected message",
        extra={
            "request_id": current_request_id,
            "user_id": user.id,
            "message_text": message.text
        }
    )
    
    await message.answer(
        "Please use the menu buttons to navigate. 👆\n"
        "Or use /help to see available commands.",
        reply_markup=main_menu_keyboard()
    )

# Error handler for aiogram
@router.errors()
@recover(default=True)  # Suppress errors even if recovery panics
async def error_handler(event, exception: Exception):
    current_request_id = request_id_ctx.get()
    request_logger.error(
        f"Error in handler",
        extra={"request_id": current_request_id, "error": str(exception)},
        exc_info=True
    )
    return True  # Suppress the error