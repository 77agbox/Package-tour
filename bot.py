import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ──────────────────────────────────────────────
TOKEN = "8440516015:AAHZ-LU5HOVLSxNaoiv1dr0xhHqy_hclN4Q"

# Замени на реальные ID, когда будут
MANAGERS = {
    "Александр": 462740408,
    "Алексей":    987654321,  # ← реальный ID Алексея
}

# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

print("=== bot.py начал выполняться ===")
sys.stdout.flush()

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ─── ПАКЕТНЫЕ ТУРЫ ───────────────────────────────────────────────────────────

PACKAGE_MODULES = {
    "Картинг": {"prices": [2200, 2100, 2000]},
    "Симрейсинг": {"prices": [1600, 1500, 1400]},
    "Практическая стрельба": {"prices": [1600, 1500, 1400]},
    "Лазертаг": {"prices": [1600, 1500, 1400]},
    "Керамика": {"prices": [1600, 1500, 1400]},
    "Мягкая игрушка": {"prices": [1300, 1200, 1100]},
}

class PackageForm(StatesGroup):
    num_people = State()
    activities = State()
    name = State()
    phone = State()
    date = State()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────

MASTERCLASSES = [
    {
        "title": "Сумочка для телефона",
        "date": "04.03.2026",
        "time": "17:00",
        "price": 1500,
        "address": "Газопровод д.4",
        "description_link": "https://t.me/dyutsvictory/3726",
        "available": True
    },
    # Добавляй новые
]

class MasterclassForm(StatesGroup):
    list_view = State()
    detail_view = State()
    name = State()
    phone = State()

# ─── КЛАВИАТУРЫ ──────────────────────────────────────────────────────────────

def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Пакетные туры")
    builder.button(text="Мастер-классы")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

main_kb = get_main_keyboard()

def get_activities_keyboard(selected=None):
    selected = selected or []
    builder = ReplyKeyboardBuilder()
    for module in PACKAGE_MODULES:
        text = f"{module} {'✅' if module in selected else ''}"
        builder.button(text=text)
    builder.button(text="Готово")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# ─── ПЕРЕНАПРАВЛЕНИЕ ИЗ ГРУППЫ ──────────────────────────────────────────────

@dp.message(lambda m: m.chat.type in ["group", "supergroup"])
async def group_redirect(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Перейти в личные сообщения →",
            url=f"https://t.me/{(await bot.get_me()).username}"
        )]
    ])
    await message.reply(
        "Для подбора тура или записи на мастер-класс напишите мне в личные сообщения.\n"
        "Там всё конфиденциально и удобно 😊",
        reply_markup=keyboard
    )

# ─── СТАРТ ───────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    if message.chat.type != "private":
        await group_redirect(message)
        return

    await message.answer(
        "Добро пожаловать в бот Центра «Виктория»!\n\n"
        "Выберите, что вас интересует:",
        reply_markup=main_kb
    )

# ─── ПАКЕТНЫЕ ТУРЫ ───────────────────────────────────────────────────────────

@dp.message(lambda m: m.text == "Пакетные туры")
async def start_package(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await group_redirect(message)
        return

    await state.set_state(PackageForm.num_people)
    await message.answer(
        "Сколько человек в вашей группе?",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(PackageForm.num_people)
async def package_num_people(message: types.Message, state: FSMContext):
    try:
        num = int(message.text.strip())
        if num < 1:
            await message.answer("Введите положительное число.")
            return
        await state.update_data(num_people=num, selected_activities=[])
        await state.set_state(PackageForm.activities)
        await message.answer(
            "Выберите 1–3 активности (нажимайте, чтобы добавить/убрать):",
            reply_markup=get_activities_keyboard()
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число.")

@dp.message(PackageForm.activities)
async def package_activities(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "Готово":
        data = await state.get_data()
        selected = data.get("selected_activities", [])
        if not 1 <= len(selected) <= 3:
            await message.answer("Выберите от 1 до 3 активностей.")
            return
        await state.set_state(PackageForm.name)
        await message.answer("Как к вам обращаться? (имя)", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    selected = data.get("selected_activities", [])
    module_name = text.replace(" ✅", "")
    if module_name in PACKAGE_MODULES:
        if module_name in selected:
            selected.remove(module_name)
        else:
            if len(selected) < 3:
                selected.append(module_name)
            else:
                await message.answer("Максимум 3 активности.")
                return
        await state.update_data(selected_activities=selected)
        await message.answer(
            "Выбрано: " + ", ".join(selected) if selected else "Пока ничего",
            reply_markup=get_activities_keyboard(selected)
        )

@dp.message(PackageForm.name)
async def package_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(PackageForm.phone)
    await message.answer("Ваш номер телефона для связи")

@dp.message(PackageForm.phone)
async def package_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await state.set_state(PackageForm.date)
    await message.answer("Желаемая дата и время (или «любое»)")

@dp.message(PackageForm.date)
async def package_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(date=message.text.strip())

    selected = data["selected_activities"]
    num_act = len(selected)
    num_p = data["num_people"]

    price_idx = num_act - 1
    total = 0
    lines = []
    for act in selected:
        p = PACKAGE_MODULES[act]["prices"][price_idx]
        cost = p * num_p
        total += cost
        lines.append(f"{act}: {p} ₽/чел × {num_p} = {cost} ₽")

    lines_text = "\n".join(lines)

    order_text = (
        "🛒 Новый пакетный тур\n\n"
        f"Клиент: {data.get('name')}\n"
        f"Тел: {data.get('phone')}\n"
        f"Дата/время: {data.get('date')}\n\n"
        f"Группа: {num_p} чел\n"
        f"Активности ({num_act}): {', '.join(selected)}\n\n"
        f"{lines_text}\n\n"
        f"<b>Итого: {total} ₽</b>"
    )

    for name, uid in MANAGERS.items():
        try:
            await bot.send_message(uid, order_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки {name} ({uid}): {e}")

    await message.answer("Запрос отправлен менеджерам. Скоро с вами свяжутся!", reply_markup=main_kb)
    await state.clear()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────

@dp.message(lambda m: m.text == "Мастер-классы")
async def show_masterclass_list(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await group_redirect(message)
        return

    active_mcs = [mc for mc in MASTERCLASSES if mc["available"]]
    if not active_mcs:
        await message.answer(
            "На данный момент активных мастер-классов нет 😔\n\n"
            "Мы регулярно добавляем новые занятия! Как только появится интересный мастер-класс — сразу сообщим.\n\n"
            "А пока можете подобрать пакетный тур для группы — жмите кнопку ниже 👇",
            reply_markup=main_kb
        )
        return

    builder = ReplyKeyboardBuilder()
    for mc in active_mcs:
        text = f"{mc['title']} — {mc['date']} {mc['time']} — {mc['address']}"
        builder.button(text=text)
    builder.adjust(1)

    await message.answer(
        "Выберите мастер-класс:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(MasterclassForm.list_view)

@dp.message(MasterclassForm.list_view)
async def select_masterclass(message: types.Message, state: FSMContext):
    title_part = message.text.split(" — ")[0]
    selected_mc = next((mc for mc in MASTERCLASSES if mc["title"] == title_part and mc["available"]), None)

    if not selected_mc:
        await message.answer("Выберите мастер-класс из списка.")
        return

    await state.update_data(selected_mc=selected_mc)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее", callback_data=f"mc_detail_{selected_mc['title']}")],
        [InlineKeyboardButton(text="Записаться", callback_data=f"mc_signup_{selected_mc['title']}")],
        [InlineKeyboardButton(text="Назад к списку", callback_data="mc_back_to_list")]
    ])

    await message.answer(
        f"Вы выбрали: {selected_mc['title']}\n"
        f"Когда: {selected_mc['date']} в {selected_mc['time']}\n"
        f"Где: {selected_mc['address']}\n"
        f"Стоимость: {selected_mc['price']} ₽",
        reply_markup=keyboard
    )
    await state.set_state(MasterclassForm.detail_view)

@dp.callback_query(lambda c: c.data.startswith("mc_"))
async def handle_mc_callback(callback: types.CallbackQuery, state: FSMContext):
    data = callback.data

    if data == "mc_back_to_list":
        await callback.message.delete()
        await show_masterclass_list(callback.message, state)
        await callback.answer()

    elif data.startswith("mc_detail_"):
        title = data.replace("mc_detail_", "")
        mc = next((m for m in MASTERCLASSES if m["title"] == title), None)
        if mc:
            await callback.message.answer(
                f"Подробное описание:\n"
                f"{mc['description_link']}",
                disable_web_page_preview=False
            )
        await callback.answer()

    elif data.startswith("mc_signup_"):
        title = data.replace("mc_signup_", "")
        mc = next((m for m in MASTERCLASSES if m["title"] == title), None)
        if mc:
            await state.update_data(selected_mc=mc)
            await state.set_state(MasterclassForm.name)
            await callback.message.answer(
                f"Запись на «{mc['title']}» ({mc['address']})\n\n"
                "Как к вам обращаться? (имя)",
                reply_markup=ReplyKeyboardRemove()
            )
        await callback.answer()

@dp.message(MasterclassForm.name)
async def mc_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(MasterclassForm.phone)
    await message.answer("Ваш номер телефона для связи")

@dp.message(MasterclassForm.phone)
async def mc_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mc = data["selected_mc"]

    order_text = (
        f"🛒 Запись на мастер-класс\n\n"
        f"Мастер-класс: {mc['title']}\n"
        f"Дата и время: {mc['date']} {mc['time']}\n"
        f"Адрес: {mc['address']}\n"
        f"Стоимость: {mc['price']} ₽\n"
        f"Описание: {mc['description_link']}\n\n"
        f"Клиент: {data.get('name')}\n"
        f"Телефон: {message.text.strip()}"
    )

    for name, uid in MANAGERS.items():
        try:
            await bot.send_message(uid, order_text, parse_mode="HTML", disable_web_page_preview=False)
        except Exception as e:
            logger.error(f"Ошибка отправки {name}: {e}")

    await message.answer(
        f"Вы записаны на «{mc['title']}» ({mc['address']})!\n"
        "Менеджер свяжется с вами для подтверждения.\n\n"
        f"Подробности: {mc['description_link']}",
        reply_markup=main_kb,
        disable_web_page_preview=False
    )
    await state.clear()

# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────

async def main():
    try:
        me = await bot.get_me()
        logger.info(f"Бот запущен как @{me.username}")
        await bot.delete_webhook(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
