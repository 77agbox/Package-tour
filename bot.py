import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ──────────────────────────────────────────────
TOKEN = "8440516015:AAHZ-LU5HOVLSxNaoiv1dr0xhHqy_hclN4Q"
ADMIN_ID = 462740408
# ──────────────────────────────────────────────

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)

print("=== bot.py начал выполняться ===")
sys.stdout.flush()

try:
    bot = Bot(token=TOKEN)
    logger.info("Бот успешно создан")
except Exception as e:
    logger.error(f"Ошибка при создании Bot: {e}")
    print(f"Критическая ошибка при создании Bot: {e}")
    sys.exit(1)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Данные из таблицы (модули и цены на человека в зависимости от кол-ва активностей: 1,2,3)
MODULES = {
    "Картинг": {"prices": [2200, 2100, 2000]},
    "Симрейсинг": {"prices": [1600, 1500, 1400]},
    "Практическая стрельба": {"prices": [1600, 1500, 1400]},
    "Лазертаг": {"prices": [1600, 1500, 1400]},
    "Керамика": {"prices": [1600, 1500, 1400]},
    "Мягкая игрушка": {"prices": [1300, 1200, 1100]},
}

class Form(StatesGroup):
    num_people = State()       # Количество человек (любое положительное число)
    activities = State()       # Выбор активностей (1-3)
    name = State()             # Имя
    phone = State()            # Телефон
    date = State()             # Дата/время (опционально, текстом)

# ─── Главная клавиатура ──────────────────────────────────────────────────────

def get_main_keyboard() -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="Подобрать пакетный тур")
    builder.adjust(1)
    return builder.as_markup(
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите действие…"
    )

main_kb = get_main_keyboard()

# ─── Клавиатура для выбора активностей ───────────────────────────────────────

def get_activities_keyboard(selected: list = None) -> types.ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    selected = selected or []
    for module in MODULES:
        text = f"{module} {'✅' if module in selected else ''}"
        builder.button(text=text)
    builder.button(text="Готово (выбрано)")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# ─── Хендлеры ────────────────────────────────────────────────────────────────

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот Центра «Виктория» для подбора пакетных туров.\n\n"
        "Выберите 1, 2 или 3 активности. Цена за человека зависит от количества выбранных активностей.\n"
        "В стоимость уже входит уютное место для чаепития и сопровождение администратора.\n\n"
        "Нажмите кнопку ниже, чтобы начать.",
        reply_markup=main_kb
    )

@dp.message(lambda m: m.text == "Подобрать пакетный тур")
async def start_form(message: types.Message, state: FSMContext):
    await state.set_state(Form.num_people)
    await message.answer(
        "Сколько человек в вашей группе?",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(Form.num_people)
async def process_num_people(message: types.Message, state: FSMContext):
    try:
        num = int(message.text.strip())
        if num < 1:
            await message.answer("Количество человек должно быть положительным числом. Попробуйте снова.")
            return
        await state.update_data(num_people=num, selected_activities=[])
        await state.set_state(Form.activities)
        await message.answer(
            "Выберите 1–3 активности (нажимайте на кнопки, чтобы добавить/убрать):\n\n"
            "• Картинг\n"
            "• Симрейсинг\n"
            "• Практическая стрельба\n"
            "• Лазертаг\n"
            "• Керамика\n"
            "• Мягкая игрушка\n\n"
            "Когда закончите выбор — нажмите «Готово (выбрано)»",
            reply_markup=get_activities_keyboard()
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число (например, 12).")

@dp.message(Form.activities)
async def process_activities(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "Готово (выбрано)":
        data = await state.get_data()
        selected = data.get("selected_activities", [])
        if not 1 <= len(selected) <= 3:
            await message.answer("Пожалуйста, выберите от 1 до 3 активностей.")
            return
        await state.set_state(Form.name)
        await message.answer("Как к вам обращаться? (имя)", reply_markup=ReplyKeyboardRemove())
        return

    # Добавляем/убираем активность
    data = await state.get_data()
    selected = data.get("selected_activities", [])
    module_name = text.replace(" ✅", "")
    if module_name in MODULES:
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

@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(Form.phone)
    await message.answer("Ваш номер телефона для связи")

@dp.message(Form.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await state.set_state(Form.date)
    await message.answer("Укажите желаемую дату и время (например, 15 марта в 14:00) или «любое»")

@dp.message(Form.date)
async def process_date_and_finish(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(date=message.text.strip())

    selected = data["selected_activities"]
    num_activities = len(selected)
    num_people = data["num_people"]

    # Расчёт стоимости
    total_cost = 0
    details = []
    price_index = num_activities - 1  # 0 → 1 акт., 1 → 2 акт., 2 → 3 акт.
    for act in selected:
        price_per_person = MODULES[act]["prices"][price_index]
        cost = price_per_person * num_people
        total_cost += cost
        details.append(f"{act}: {price_per_person} ₽/чел × {num_people} = {cost} ₽")

    order = (
        "🛒 <b>Новый запрос на пакетный тур</b> (Центр «Виктория»)\n\n"
        f"Клиент: {data.get('name', '—')}\n"
        f"Телефон: {data.get('phone', '—')}\n"
        f"Желаемая дата/время: {data.get('date', '—')}\n\n"
        f"Группа: {num_people} человек\n"
        f"Активности ({num_activities}): {', '.join(selected)}\n\n"
        + "\n".join(details) + "\n\n"
        f"<b>Итого: {total_cost} ₽</b>\n"
        "(включая чаепитие и сопровождение администратора)"
    )

    try:
        await bot.send_message(ADMIN_ID, order, parse_mode="HTML")
        await message.answer(
            "Ваш запрос успешно отправлен! 🎉\n"
            "Администратор свяжется с вами в ближайшее время.\n\n"
            "Ваши данные для справки:\n\n" +
            order.replace("<b>", "").replace("</b>", ""),
            reply_markup=main_kb,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить заказ: {e}")
        await message.answer(
            "Запрос сформирован, но не удалось отправить уведомление.\n"
            "Пожалуйста, свяжитесь с центром напрямую.",
            reply_markup=main_kb
        )

    await state.clear()

# ─── Запуск ──────────────────────────────────────────────────────────────────

async def main():
    logger.info("Запуск бота начат")

    try:
        me = await bot.get_me()
        logger.info(f"Успешная авторизация → @{me.username} ({me.first_name})")
        print(f"Бот запущен как: @{me.username}")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"Ошибка авторизации: {e}")
        print(f"Ошибка авторизации: {e}")
        sys.stdout.flush()
        return

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook удалён")
    except Exception:
        pass

    logger.info("Запускаем polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка в main: {e}")
