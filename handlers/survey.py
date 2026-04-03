from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import ADMIN_ID
from database import save_application

router = Router()


class SurveyStates(StatesGroup):
    name = State()
    instagram = State()
    source = State()
    reason = State()
    vibe = State()


@router.message(SurveyStates.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(SurveyStates.instagram)
    await message.answer("Ваш контакт в INST (ссылка или @логин).")


@router.message(SurveyStates.instagram)
async def process_instagram(message: Message, state: FSMContext):
    await state.update_data(instagram=message.text)
    await state.set_state(SurveyStates.source)
    await message.answer(
        "Откуда вы узнали о нас? Если вас кто-то пригласил — кто именно?"
    )


@router.message(SurveyStates.source)
async def process_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    await state.set_state(SurveyStates.reason)
    await message.answer(
        "Что вам откликается в формате Чайного Движа и почему вам хочется быть частью этого пространства?"
    )


@router.message(SurveyStates.reason)
async def process_reason(message: Message, state: FSMContext):
    await state.update_data(reason=message.text)
    await state.set_state(SurveyStates.vibe)
    await message.answer(
        "Наш формат — это чай, музыка, уважение к людям и классная атмосфера. Вам это близко?"
    )


@router.message(SurveyStates.vibe)
async def process_vibe(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    app_id = await save_application(
        user_id=message.from_user.id,
        username=message.from_user.username,
        name=data["name"],
        instagram=data["instagram"],
        source=data["source"],
        reason=data["reason"],
        vibe=message.text,
    )

    await message.answer(
        "Спасибо! Ваша заявка отправлена на рассмотрение. Ожидайте ответа."
    )

    username = message.from_user.username
    user_link = f"@{username}" if username else f"ID: {message.from_user.id}"

    text = (
        f"❗️❗️❗️ Новая заявка #{app_id} ❗️❗️❗️\n\n"
        f"Имя: {data['name']}\n"
        f"Instagram: {data['instagram']}\n"
        f"Откуда узнал: {data['source']}\n"
        f"Запрос: {data['reason']}\n"
        f"Близко ли: {message.text}\n\n"
        f"Telegram: {user_link}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Принять", callback_data=f"approve_{app_id}"
                ),
                InlineKeyboardButton(
                    text="Отклонить", callback_data=f"reject_{app_id}"
                ),
            ]
        ]
    )

    await message.bot.send_message(ADMIN_ID, text, reply_markup=keyboard)
