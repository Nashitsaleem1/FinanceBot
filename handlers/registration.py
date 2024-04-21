from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from aiogram.types.input_media import InputMediaVideo
from gspread.utils import extract_id_from_url

import database
from keyboards import registration
from keyboards.user import main_keyb, register_keyb
from server import _, bot
from sheet import Sheet

TEMPLATE_SHEET_LINK = "https://docs.google.com/spreadsheets/\
d/1lO9oTJu3CudibuQCCqk-s1t3DSuRNRoty4SLY5UvG_w"
BOT_SERVICE_EMAIL = "telexpense-bot@telexpense-bot.iam.gserviceaccount.com"
BOT_WIKI = "https://github.com/pavelmakis/telexpense/wiki"


class RegistrationForm(StatesGroup):
    """This form if used for registration"""

    option = State()
    connect_new = State()
    get_link = State()
    process_link = State()
    forget = State()


def check_url(message_text: str) -> bool:
    """Sheet template check"""
    if message_text.startswith("https://"):
        user_sheet = Sheet(extract_id_from_url(message_text))
        # Check if bot is able to connect to sheet
        if user_sheet != None:
            # Check if sheet is copied from template
            if user_sheet.is_right_sheet() != False:
                return True
    return False


async def start_registration(message: Message):
    """This handler is used when user sends /register command"""
    # Users get different messages based on if they are
    # registered or not
    if database.is_user_registered(message.from_user.id):
        await message.answer(
            _(
                "You are already registered user!\n\n"
                "You can either connect me to a new Google Sheet or delete "
                "a connected sheet from the database"
            ),
            reply_markup=registration.change_sheet_keyb(),
        )
    else:
        await message.answer(
            _(
                "Looks like you are new here...\n\n"
                "If you want to use me, connect me to new Google Sheet"
            ),
            reply_markup=registration.new_sheet_keyb(),
        )

    # Setting form on the begining
    await RegistrationForm.option.set()


async def process_user_option(call: CallbackQuery):
    # Answer to query
    await bot.answer_callback_query(call.id)

    if call.data == "new_sheet":
        await bot.send_video(
            # For each bot one file has different file_id. Thats why I need one
            # file_id for my test bot and another for my production bot
            #
            # If you need to get file_id for your bot, send yourself a message with file
            # from you bot using Telegram API in browser. In the result there will be
            # file_id field
            call.from_user.id,
            # for test bot
            # video="CgACAgQAAxkDAAICnmKTrx5fRvoBSbfcmGHrpNOTrmByAAKGAwACxs6cUOdnAc6h666dJAQ",
            # for telexpense
            video="CgACAgQAAxkDAAIk8GKTsJeiKNiFtQV5r3Y5TxnzI6WwAAKGAwACxs6cUJBCE840i8xkJAQ",
            width=1512,
            height=946,
            caption=_(
                "*STEP 1*\n\n"
                "Copy this Google Sheet template to your Google account. "
                "You do this to ensure that your financial data belongs only to you.\n\n"
                "👉 [Telexpense Template Sheet]({sheet}) 👈".format(
                    sheet=TEMPLATE_SHEET_LINK
                )
            ),
            parse_mode="Markdown",
            reply_markup=registration.copytemplate_done_keyb(),
        )

        # Deleting previous message because I cant edit it
        # because it is media message
        await bot.delete_message(call.from_user.id, call.message.message_id)

        # Setting state
        await RegistrationForm.connect_new.set()

    elif call.data == "forget_sheet":
        # Sending warning to user
        await bot.edit_message_text(
            _("Are you sure? After that you have to /register again to use me"),
            call.from_user.id,
            call.message.message_id,
            reply_markup=registration.understand_keyb(),
        )

        # Setting state
        await RegistrationForm.forget.set()


async def process_cancel(call: CallbackQuery, state: FSMContext):
    # Delete message with inline keyboard
    await bot.delete_message(call.from_user.id, call.message.message_id)

    registered = database.is_user_registered(call.from_user.id)

    # Send message with reply markup
    await bot.send_message(
        call.from_user.id,
        _("OK, next time"),
        reply_markup=main_keyb() if registered else register_keyb(),
    )

    # End state machine
    await state.finish()


async def add_bot_email(call: CallbackQuery):
    # Answer to query
    await bot.answer_callback_query(call.id)

    await bot.edit_message_media(
        InputMediaVideo(
            # for test bot
            # "CgACAgQAAxkDAAICpmKTsnx3QJm2mI8cA61YzzZpK9IyAAJtAwAC7SukUMWd2HYBF9nqJAQ",
            # for telexpense
            "CgACAgQAAxkDAAIk-2KTuhq5jmAyOt2GS2xD73Vo6cCIAAJtAwAC7SukULuOaMN-Ao5_JAQ",
            caption=_(
                "*STEP 2*\n\n"
                "Add me to the table as an editor so I can add transactions "
                "and read the balance. Here is my email:\n\n"
                "{email}".format(email=BOT_SERVICE_EMAIL)
            ),
            parse_mode="Markdown",
        ),
        call.from_user.id,
        call.message.message_id,
        reply_markup=registration.addemail_done_keyb(),
    )

    await RegistrationForm.get_link.set()


async def ask_sheet_url(call: CallbackQuery):
    # Answer to query
    await bot.answer_callback_query(call.id)

    # Send message with step 3 of instructions
    await bot.send_message(
        call.from_user.id,
        _(
            "*STEP 3*\n\n"
            "Copy the link to the table in your account and send it to this chat. "
            "It is necessary for me to remember you"
        ),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Delete previous message
    await bot.delete_message(
        call.from_user.id,
        call.message.message_id,
    )

    await RegistrationForm.process_link.set()


async def process_sheet_url(message: Message, state: FSMContext):
    # Stop form
    await state.finish()

    await message.answer(_("Checking this sheet..."))

    registered = database.is_user_registered(message.from_user.id)

    # Sheet check
    if check_url(message.text):
        if registered:
            # Updating previous record if user was registered
            database.update_sheet_id(
                message.from_user.id, extract_id_from_url(message.text)
            )

            await message.answer(
                _(
                    "Your sheet successfully changed!\n\n"
                    "Don't forget to select the main currency and its format in /currency "
                    "and set bots language in /language"
                ),
                reply_markup=main_keyb(),
            )
        else:
            database.insert_sheet_id(
                message.from_user.id, extract_id_from_url(message.text)
            )
            await message.answer(
                _(
                    "Great, you are in!\n\n"
                    "Don't forget to select the main currency and its format in /currency "
                    "and set bots language in /language"
                ),
                reply_markup=main_keyb(),
            )

        return

    await message.answer(
        _(
            "Hm. Looks like it's not a link I'm looking for...\n\n"
            "Read the [wiki]({wiki}) and try to /register one more time!".format(
                wiki=BOT_WIKI
            )
        ),
        disable_web_page_preview=True,
        parse_mode="Markdown",
        reply_markup=main_keyb() if registered else register_keyb(),
    )


async def forget_user_sheet(call: CallbackQuery, state: FSMContext):
    # Answer to query
    await bot.delete_message(call.from_user.id, call.message.message_id)

    # End state machine
    await state.finish()

    # Delete user from database
    database.delete_sheet_id(call.from_user.id)

    await bot.send_message(
        call.from_user.id,
        _("See you next time!"),
        reply_markup=register_keyb(),
    )


def register_registration(dp: Dispatcher):
    dp.register_message_handler(start_registration, commands=["register"])
    dp.register_callback_query_handler(
        process_cancel,
        lambda c: c.data and c.data == "cancel",
        state=RegistrationForm.all_states,
    )
    dp.register_callback_query_handler(
        process_user_option, state=RegistrationForm.option
    )
    dp.register_callback_query_handler(
        forget_user_sheet,
        lambda c: c.data and c.data == "user_understands",
        state=RegistrationForm.forget,
    )
    dp.register_callback_query_handler(
        add_bot_email,
        lambda c: c.data and c.data == "template_copied",
        state=RegistrationForm.connect_new,
    )
    dp.register_callback_query_handler(
        ask_sheet_url,
        lambda c: c.data and c.data == "email_added",
        state=RegistrationForm.get_link,
    )
    dp.register_message_handler(process_sheet_url, state=RegistrationForm.process_link)
