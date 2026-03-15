import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8664150855:AAHfOhOAjlx2UoQ0gcEVyjGPIeWCm1mu67o"  # вставь токен
ADMIN_ID = 1387177324  # вставь свой ID
GIF_PATH = "welcome.gif"  # путь к гифке (если нет — ничего страшного)
# ========================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Пытаемся загрузить гифку заранее (если есть) — чтобы при каждом /start не проверять диск
try:
    welcome_gif = FSInputFile(GIF_PATH)
    GIF_EXISTS = True
except:
    GIF_EXISTS = False
    welcome_gif = None

# Состояния
class OrderForm(StatesGroup):
    name = State()
    car = State()
    budget = State()
    contact = State()

# Клавиатуры (создаём один раз, чтобы не пересоздавать)
main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 ОСТАВИТЬ ЗАЯВКУ", callback_data="order")],
    [InlineKeyboardButton(text="📞 СВЯЗАТЬСЯ", url="https://t.me/stk_motors_manager")],
    [InlineKeyboardButton(text="ℹ️ КАК МЫ РАБОТАЕМ", callback_data="how")]
])

back_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back")]
])

# /start
@dp.message(Command("start"))
async def start(message: types.Message):
    text = ("🚀 **STK MOTORS** — твой проводник в мир JDM и Китая\n\n"
            "🇯🇵 Япония | 🇰🇷 Корея | 🇨🇳 Китай\n"
            "🔥 Аукционы, растаможка, под ключ")
    if GIF_EXISTS:
        await message.answer_animation(welcome_gif, caption=text, reply_markup=main_menu_keyboard)
    else:
        await message.answer(text, reply_markup=main_menu_keyboard)

# Инфо
@dp.callback_query(lambda c: c.data == "how")
async def how(call: types.CallbackQuery):
    await call.message.edit_text(
        "🔧 **КАК МЫ РАБОТАЕМ:**\n\n"
        "1️⃣ Заявка\n2️⃣ Подбор 3-5 вариантов\n3️⃣ Выкуп с аукциона\n"
        "4️⃣ Доставка и растаможка\n5️⃣ Ты забираешь авто 🚗",
        reply_markup=back_button
    )

# Назад в меню
@dp.callback_query(lambda c: c.data == "back")
async def back(call: types.CallbackQuery):
    await call.message.edit_text("🚀 Главное меню", reply_markup=main_menu_keyboard)

# Старт заявки
@dp.callback_query(lambda c: c.data == "order")
async def order_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text("🔥 Как тебя зовут?")
    await state.set_state(OrderForm.name)

# Имя
@dp.message(OrderForm.name)
async def get_name(msg: types.Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("🚗 Какую тачку ищешь? (модель, год)")
    await state.set_state(OrderForm.car)

# Машина
@dp.message(OrderForm.car)
async def get_car(msg: types.Message, state: FSMContext):
    await state.update_data(car=msg.text)
    await msg.answer("💰 Бюджет в $? (только цифры)")
    await state.set_state(OrderForm.budget)

# Бюджет
@dp.message(OrderForm.budget)
async def get_budget(msg: types.Message, state: FSMContext):
    await state.update_data(budget=msg.text)
    await msg.answer("📱 Контакт (телефон или @username)")
    await state.set_state(OrderForm.contact)

# Контакт и финал
@dp.message(OrderForm.contact)
async def get_contact(msg: types.Message, state: FSMContext):
    data = await state.update_data(contact=msg.text)
    data = await state.get_data()

    # Отправка админу
    admin_text = (f"🔔 **НОВАЯ ЗАЯВКА**\n"
                  f"👤 {data['name']}\n🚘 {data['car']}\n💰 {data['budget']}$\n📱 {data['contact']}")
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        admin_ok = "✅ Заявка доставлена"
    except:
        admin_ok = "⚠️ Ошибка отправки, но мы всё получили"

    # Ответ клиенту
    await msg.answer(
        f"✅ **ГОТОВО**\n\n"
        f"👤 {data['name']}\n🚘 {data['car']}\n💰 {data['budget']}$\n📱 {data['contact']}\n\n"
        f"{admin_ok}\nСкоро свяжемся 🚀",
        reply_markup=main_menu_keyboard
    )
    await state.clear()

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
