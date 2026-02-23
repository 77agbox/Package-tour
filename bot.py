import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ──────────────────────────────────────────────
TOKEN = "8440516015:AAHZ-LU5HOVLSxNaoiv1dr0xhHqy_hclN4Q"

# Замени на реальные ID, когда будут
MANAGERS = {
    "Александр": 462740408,   # ← твой текущий ID (пока placeholder)
    "Алексей":    123456789,  # ← замени на реальный ID Алексея
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
    "Картинг":          {"prices": [2200, 2100, 2000]},
    "Симрейсинг":       {"prices": [1600, 1500, 1400]},
    "Практическая стрельба": {"prices": [1600, 1500, 1400]},
    "Лазертаг":         {"prices": [1600, 1500, 1400]},
    "Керамика":         {"prices": [1600, 1500, 1400]},
    "Мягкая игрушка":   {"prices": [1300, 1200, 1100]},
}

class PackageForm(StatesGroup):
    num_people = State()
    activities = State()
    name = State()
    phone = State()
    date = State()

# ─── МАСТЕР-КЛАССЫ (отдельный блок — легко обновлять) ────────────────────────

MASTERCLASSES = [
    {
        "title": "Сумочка для телефона",
        "date": "04.03.2026",
        "time": "17:00",
        "price": 1500,
        "address": "Газопровод д.4",
        "available": True  # можно ставить False, если занят/отменён
    },
    # Добавляй новые мастер-классы сюда, например:
    # {
    #     "title": "Роспись пряников",
    #     "date": "15.03.2026",
    #     "time": "14:00",
    #     "price": 1800,
    #     "address": "Газопровод д.4",
    #     "available": True
    # },
]

class MasterclassForm(StatesGroup):
    choice = State()
    name = State()
    phone = State()
    comment = State()  # опционально

# ─── ОБЩИЕ КЛАВИАТУРЫ ────────────────────────────────────────────────────────

def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Пакетные туры")
    builder.button(text="Мастер-классы")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

main_kb = get_main_keyboard()

def get_activities_keyboard(selected: list = None) -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    selected = selected or []
    for module in PACKAGE_MODULES:
        text = f"{module} {'✅' if module in selected else ''}"
        builder.button(text=text)
    builder.button(text="Готово")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# ─── ОБРАБОТКА ГРУПП / СООБЩЕСТВ ─────────────────────────────────────────────

@dp.message(lambda m: m.chat.type in ["group", "supergroup"])
async def group_redirect(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Перейти в личные сообщения →",
                url=f"https://t.me/{(await bot.get_me()).username}"
            )
        ]
    ])
    await message.reply(
        "Для подбора тура или записи на мастер-класс напишите мне в личные сообщения.\n"
        "Там всё конфиденциально и удобно 😊",
        reply_markup=keyboard
    )

# ─── СТАРТ И ГЛАВНОЕ МЕНЮ ───────────────────────────────────────────────────

@dp.message(CommandStart())
@dp.message(lambda m: m.text in ["Пакетные туры", "Мастер-классы", "/start"])
async def cmd_start(message: types.Message):
    if message.chat.type in ["group", "supergroup"]:
        await group_redirect(message)
        return

    text = (
        "Добро пожаловать в бот Центра «Виктория»!\n\n"
        "Выберите, что вас интересует:"
    )
    await message.answer(text, reply_markup=main_kb)

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

# ... (остальные хендлеры для пакетных туров как в предыдущей версии — process_activities, name, phone, date)
# В конце process_date_and_finish отправка менеджерам:

# Пример финального хендлера (добавь/замени свой)
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

    order_text = (
        f"🛒 Новый пакетный тур\n\n"
        f"Клиент: {data.get('name')}\n"
        f"Тел: {data.get('phone')}\n"
        f"Дата/время: {data.get('date')}\n\n"
        f"Группа: {num_p} чел\n"
        f"Активности ({num_act}): {', '.join(selected)}\n\n"
        f"{'\n'.join(lines)}\n\n"
        f"<b>Итого: {total} ₽</b>"
    )

    for name, uid in MANAGERS.items():
        try:
            await bot.send_message(uid, order_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки {name} ({uid}): {e}")

    await message.answer("Ваш запрос отправлен менеджерам. Скоро с вами свяжутся!")
    await state.clear()

# ─── МАСТЕР-КЛАССЫ ───────────────────────────────────────────────────────────

@dp.message(lambda m: m.text == "Мастер-классы")
async def start_masterclass(message: types.Message, state: FSMContext):
    if message.chat.type != "private":
        await group_redirect(message)
        return

    if not MASTERCLASSES:
        await message.answer("На данный момент нет активных мастер-классов.")
        return

    builder = ReplyKeyboardBuilder()
    for mc in MASTERCLASSES:
        if mc["available"]:
            text = f"{mc['title']} — {mc['date']} {mc['time']}"
            builder.button(text=text)
    builder.adjust(1)

    await message.answer(
        "Выберите мастер-класс:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    await state.set_state(MasterclassForm.choice)

@dp.message(MasterclassForm.choice)
async def mc_choice(message: types.Message, state: FSMContext):
    title = message.text.split(" — ")[0]
    selected_mc = next((mc for mc in MASTERCLASSES if mc["title"] == title), None)

    if not selected_mc or not selected_mc["available"]:
        await message.answer("Этот мастер-класс недоступен. Выберите другой.")
        return

    await state.update_data(selected_mc=selected_mc)
    await state.set_state(MasterclassForm.name)
    await message.answer("Как к вам обращаться?", reply_markup=ReplyKeyboardRemove())

# ... (дальше name → phone → comment → finish)

@dp.message(MasterclassForm.name)
async def mc_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(MasterclassForm.phone)
    await message.answer("Ваш номер телефона")

@dp.message(MasterclassForm.phone)
async def mc_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await state.set_state(MasterclassForm.comment)
    await message.answer("Есть ли пожелания / комментарии? (можно пропустить)")

@dp.message(MasterclassForm.comment)
async def mc_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mc = data["selected_mc"]

    order_text = (
        f"🛒 Запись на мастер-класс\n\n"
        f"Мастер-класс: {mc['title']}\n"
        f"Дата: {mc['date']} {mc['time']}\n"
        f"Стоимость: {mc['price']} ₽\n"
        f"Адрес: {mc['address']}\n\n"
        f"Клиент: {data.get('name')}\n"
        f"Телефон: {data.get('phone')}\n"
        f"Комментарий: {message.text.strip() or '—'}"
    )

    for name, uid in MANAGERS.items():
        try:
            await bot.send_message(uid, order_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка отправки {name}: {e}")

    await message.answer(
        f"Вы записаны на «{mc['title']}»!\n"
        "Менеджер свяжется с вами для подтверждения."
    )
    await state.clear()

# ─── ЗАПУСК ──────────────────────────────────────────────────────────────────

async def main():
    try:
        me = await bot.get_me()
        logger.info(f"Бот запущен как @{me.username}")

        # Удаляем webhook
        await bot.delete_webhook(drop_pending_updates=True)

        # Можно добавить set_my_commands, если нужно
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
