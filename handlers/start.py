from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from handlers.survey import SurveyStates
from database import has_application

router = Router()


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    await message.answer(f"Ваш ID: {message.from_user.id}")


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        status = await has_application(message.from_user.id)
        if status == "pending":
            await message.answer("У вас уже есть заявка на рассмотрении. Ожидайте ответа.")
            return
        if status in ("approved", "manual"):
            await message.answer("Вы уже в нашем пространстве!")
            return
        if status == "rejected":
            await message.answer("Ваша заявка была отклонена.")
            return

    await message.answer(
        "Привет! 👋\n"
        "Чтобы подать заявку, ответьте на несколько вопросов.\n\n"
        "Как вас зовут?"
    )
    await state.set_state(SurveyStates.name)
