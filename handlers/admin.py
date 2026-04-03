from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from config import ADMIN_ID, CHANNEL_ID
from database import get_application, update_status, add_manual_application, get_all_applications, search_applications, get_all_user_ids, delete_application

router = Router()


# --- Ручное добавление ---

class ManualAddStates(StatesGroup):
    user_id = State()
    name = State()
    instagram = State()
    source = State()
    reason = State()
    vibe = State()
    comment = State()


@router.message(Command("db_add"))
async def cmd_add(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("Введите Telegram ID или @username человека:")
    await state.set_state(ManualAddStates.user_id)


@router.message(ManualAddStates.user_id)
async def manual_user_id(message: Message, state: FSMContext):
    await state.update_data(raw_user=message.text)
    await message.answer("Имя:")
    await state.set_state(ManualAddStates.name)


@router.message(ManualAddStates.name)
async def manual_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Instagram (ссылка/логин):")
    await state.set_state(ManualAddStates.instagram)


@router.message(ManualAddStates.instagram)
async def manual_instagram(message: Message, state: FSMContext):
    await state.update_data(instagram=message.text)
    await message.answer("Откуда узнал о нас:")
    await state.set_state(ManualAddStates.source)


@router.message(ManualAddStates.source)
async def manual_source(message: Message, state: FSMContext):
    await state.update_data(source=message.text)
    await message.answer("Запрос на вступление:")
    await state.set_state(ManualAddStates.reason)


@router.message(ManualAddStates.reason)
async def manual_reason(message: Message, state: FSMContext):
    await state.update_data(reason=message.text)
    await message.answer("Близок ли формат:")
    await state.set_state(ManualAddStates.vibe)


@router.message(ManualAddStates.vibe)
async def manual_vibe(message: Message, state: FSMContext):
    await state.update_data(vibe=message.text)
    await message.answer("Комментарий админа:")
    await state.set_state(ManualAddStates.comment)


@router.message(ManualAddStates.comment)
async def manual_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    raw_user = data["raw_user"]
    if raw_user.startswith("@"):
        username = raw_user[1:]
        user_id = 0
    elif raw_user.isdigit():
        username = None
        user_id = int(raw_user)
    else:
        username = raw_user
        user_id = 0

    app_id = await add_manual_application(
        user_id=user_id,
        username=username,
        name=data["name"],
        instagram=data["instagram"],
        source=data["source"],
        reason=data["reason"],
        vibe=data["vibe"],
        comment=message.text,
    )

    await message.answer(f"Человек добавлен в БД (запись #{app_id}).")


# --- Удаление из БД ---

@router.message(Command("db_delete"))
async def cmd_db_delete(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("Использование: /db_delete <номер>")
        return

    app_id = int(args[1])
    removed = await delete_application(app_id)

    if removed:
        name = removed.get("name", "?")
        username = f"@{removed['username']}" if removed.get("username") else f"ID:{removed['user_id']}"
        await message.answer(f"Запись #{app_id} удалена ({name}, {username}).")
    else:
        await message.answer(f"Запись #{app_id} не найдена.")


# --- Просмотр БД ---

@router.message(Command("db"))
async def cmd_db(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    apps = await get_all_applications()
    if not apps:
        await message.answer("База данных пуста.")
        return

    chunks = []
    current = ""
    for app in apps:
        username = f"@{app['username']}" if app.get("username") else f"ID:{app['user_id']}"
        entry = (
            f"#{app['id']} | {app['status']}\n"
            f"  Имя: {app['name']}\n"
            f"  Inst: {app['instagram']}\n"
            f"  Откуда: {app['source']}\n"
            f"  Запрос: {app['reason']}\n"
            f"  Близко ли: {app.get('vibe', '-')}\n"
            f"  TG: {username}\n"
        )
        if app.get("admin_comment"):
            entry += f"  Коммент: {app['admin_comment']}\n"
        entry += "\n"

        if len(current) + len(entry) > 4000:
            chunks.append(current)
            current = entry
        else:
            current += entry

    if current:
        chunks.append(current)

    for chunk in chunks:
        await message.answer(chunk)


# --- Поиск по БД ---

@router.message(Command("db_search"))
async def cmd_db_search(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Использование: /db_search <слово>")
        return

    query = args[1]
    results = await search_applications(query)

    if not results:
        await message.answer(f"По запросу «{query}» ничего не найдено.")
        return

    chunks = []
    current = f"Найдено: {len(results)}\n\n"
    for app in results:
        username = f"@{app['username']}" if app.get("username") else f"ID:{app['user_id']}"
        entry = (
            f"#{app['id']} | {app['status']}\n"
            f"  Имя: {app['name']}\n"
            f"  Inst: {app['instagram']}\n"
            f"  Откуда: {app['source']}\n"
            f"  Запрос: {app['reason']}\n"
            f"  Близко ли: {app.get('vibe', '-')}\n"
            f"  TG: {username}\n"
        )
        if app.get("admin_comment"):
            entry += f"  Коммент: {app['admin_comment']}\n"
        entry += "\n"

        if len(current) + len(entry) > 4000:
            chunks.append(current)
            current = entry
        else:
            current += entry

    if current:
        chunks.append(current)

    for chunk in chunks:
        await message.answer(chunk)


# --- Рассылка ---

# {user_id: "__waiting__"} или {user_id: {"text": ..., "photo": ...}}
_broadcast_data = {}


def _is_waiting_broadcast(message: Message) -> bool:
    return (
        message.from_user.id == ADMIN_ID
        and _broadcast_data.get(message.from_user.id) == "__waiting__"
    )


@router.message(Command("message_all"))
async def cmd_message_all(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    _broadcast_data[message.from_user.id] = "__waiting__"
    await message.answer("Отправьте текст или фото с подписью для рассылки:")


@router.message(F.photo, F.func(_is_waiting_broadcast))
async def broadcast_preview_photo(message: Message):
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    _broadcast_data[message.from_user.id] = {
        "photo": photo_id,
        "text": caption,
        "entities": message.caption_entities,
    }
    user_ids = await get_all_user_ids()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отправить", callback_data="broadcast_yes"),
                InlineKeyboardButton(text="Отмена", callback_data="broadcast_no"),
            ]
        ]
    )

    await message.answer("Предпросмотр:")
    await message.bot.send_photo(
        message.chat.id, photo_id,
        caption=caption or None,
        caption_entities=message.caption_entities,
    )
    await message.answer(
        f"Получателей: {len(user_ids)}\nОтправить?",
        reply_markup=keyboard,
    )


@router.message(F.text, F.func(_is_waiting_broadcast))
async def broadcast_preview_text(message: Message):
    _broadcast_data[message.from_user.id] = {
        "photo": None,
        "text": message.text,
        "entities": message.entities,
    }
    user_ids = await get_all_user_ids()

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Отправить", callback_data="broadcast_yes"),
                InlineKeyboardButton(text="Отмена", callback_data="broadcast_no"),
            ]
        ]
    )

    await message.answer("Предпросмотр:")
    await message.bot.send_message(
        message.chat.id, message.text,
        entities=message.entities,
    )
    await message.answer(
        f"Получателей: {len(user_ids)}\nОтправить?",
        reply_markup=keyboard,
    )


@router.callback_query(F.data == "broadcast_yes")
async def broadcast_send(callback: CallbackQuery, bot: Bot):
    data = _broadcast_data.pop(callback.from_user.id, None)
    if not data or data == "__waiting__":
        await callback.answer("Данные рассылки не найдены, попробуйте снова.", show_alert=True)
        return

    user_ids = await get_all_user_ids()
    sent = 0
    failed = 0
    failed_list = []

    await callback.message.edit_text("Рассылка началась...", reply_markup=None)

    for uid in user_ids:
        try:
            if data["photo"]:
                await bot.send_photo(
                    uid, data["photo"],
                    caption=data["text"] or None,
                    caption_entities=data.get("entities"),
                )
            else:
                await bot.send_message(
                    uid, data["text"],
                    entities=data.get("entities"),
                )
            sent += 1
        except Exception as e:
            failed += 1
            failed_list.append(f"ID:{uid} — {e}")

    result = f"Рассылка завершена!\n\nОтправлено: {sent}\nНе доставлено: {failed}"
    if failed_list:
        result += "\n\nОшибки:\n" + "\n".join(failed_list)

    await callback.message.edit_text(result)


@router.callback_query(F.data == "broadcast_no")
async def broadcast_cancel(callback: CallbackQuery):
    _broadcast_data.pop(callback.from_user.id, None)
    await callback.message.edit_text("Рассылка отменена.", reply_markup=None)
    await callback.answer()


# --- Одобрение/отклонение ---

@router.callback_query(F.data.startswith("approve_"))
async def approve_application(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    app_id = int(callback.data.split("_")[1])
    app = await get_application(app_id)

    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    if app["status"] != "pending":
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    await update_status(app_id, "approved")

    invite = await bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1,
        name=f"Заявка @{app['username']}" if app.get("username") else f"Заявка ID:{app['user_id']}",
    )

    await bot.send_message(
        app["user_id"],
        f"Ваша заявка одобрена! 🎉\n"
        f"Вот ваша одноразовая ссылка для вступления:\n"
        f"{invite.invite_link}",
    )

    await callback.message.edit_text(
        callback.message.text + "\n\nОДОБРЕНО", reply_markup=None
    )
    await callback.answer("Заявка одобрена!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_application(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Нет доступа", show_alert=True)
        return

    app_id = int(callback.data.split("_")[1])
    app = await get_application(app_id)

    if not app:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    if app["status"] != "pending":
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    await update_status(app_id, "rejected")

    await bot.send_message(
        app["user_id"],
        "К сожалению, ваша заявка отклонена.",
    )

    await callback.message.edit_text(
        callback.message.text + "\n\nОТКЛОНЕНО", reply_markup=None
    )
    await callback.answer("Заявка отклонена")
