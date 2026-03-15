import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8664150855:AAHfOhOAjlx2UoQ0gcEVyjGPIeWCm1mu67o"
ADMIN_ID = 1387177324
GIF_PATH = "welcome.gif"  # если есть гифка
# ========================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Пытаемся загрузить гифку один раз
try:
    welcome_gif = FSInputFile(GIF_PATH)
    GIF_EXISTS = True
except:
    GIF_EXISTS = False
    welcome_gif = None

# ----- Клавиатуры (создаём один раз) -----
back_btn = InlineKeyboardButton(text="◀️ Назад", callback_data="back")
cancel_btn = InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")

def keyboard_with_back():
    return InlineKeyboardMarkup(inline_keyboard=[[back_btn]])

def keyboard_with_cancel():
    return InlineKeyboardMarkup(inline_keyboard=[[cancel_btn]])

main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 ОСТАВИТЬ ЗАЯВКУ", callback_data="order")],
    [InlineKeyboardButton(text="📞 СВЯЗАТЬСЯ", url="https://t.me/stk_motors_manager")],
    [InlineKeyboardButton(text="ℹ️ КАК МЫ РАБОТАЕМ", callback_data="how")]
])

back_to_menu_btn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ В ГЛАВНОЕ МЕНЮ", callback_data="back_to_menu")]
])

# ----- Состояния FSM -----
class OrderForm(StatesGroup):
    name = State()
    car = State()
    budget = State()
    contact = State()

# ----- Вспомогательная функция удаления сообщения -----
async def safe_delete(message):
    try:
        await message.delete()
    except:
        pass

# ----- Хендлеры -----
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()  # сбрасываем всё
    text = ("🚀 **STK MOTORS** — твой проводник в мир JDM и Китая\n\n"
            "🇯🇵 Япония | 🇰🇷 Корея | 🇨🇳 Китай\n"
            "🔥 Аукционы, растаможка, под ключ")
    if GIF_EXISTS:
        sent = await message.answer_animation(welcome_gif, caption=text, reply_markup=main_menu_keyboard)
    else:
        sent = await message.answer(text, reply_markup=main_menu_keyboard)
    # удаляем команду /start, чтобы не мозолила глаза
    await safe_delete(message)

@dp.callback_query(lambda c: c.data == "how")
async def how_work(call: types.CallbackQuery):
    await call.message.edit_text(
        "🔧 **КАК МЫ РАБОТАЕМ:**\n\n"
        "1️⃣ Заявка\n2️⃣ Подбор 3-5 вариантов\n3️⃣ Выкуп с аукциона\n"
        "4️⃣ Доставка и растаможка\n5️⃣ Ты забираешь авто 🚗",
        reply_markup=back_to_menu_btn
    )

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_main_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("🚀 Главное меню", reply_markup=main_menu_keyboard)

# ----- Начало заявки -----
@dp.callback_query(lambda c: c.data == "order")
async def order_start(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    # спрашиваем имя
    sent = await call.message.edit_text(
        "🔥 Как тебя зовут?",
        reply_markup=keyboard_with_cancel()  # кнопка отмены (возврат в меню)
    )
    await state.set_state(OrderForm.name)
    await state.update_data(last_msg_id=sent.message_id)  # запоминаем ID последнего сообщения бота

# ----- Обработка имени -----
@dp.message(OrderForm.name)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # удаляем предыдущее сообщение бота (вопрос)
    if 'last_msg_id' in data:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except:
            pass
    # сохраняем имя
    await state.update_data(name=message.text)
    # удаляем сообщение пользователя (чтоб не засорять)
    await safe_delete(message)
    # задаём следующий вопрос
    sent = await message.answer(
        "🚗 Какую тачку ищешь? (модель, год)",
        reply_markup=keyboard_with_back()  # теперь кнопка "Назад"
    )
    await state.update_data(last_msg_id=sent.message_id)
    await state.set_state(OrderForm.car)

# ----- Обработка машины -----
@dp.message(OrderForm.car)
async def process_car(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'last_msg_id' in data:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except:
            pass
    await state.update_data(car=message.text)
    await safe_delete(message)
    sent = await message.answer(
        "💰 Бюджет в $? (только цифры)",
        reply_markup=keyboard_with_back()
    )
    await state.update_data(last_msg_id=sent.message_id)
    await state.set_state(OrderForm.budget)

# ----- Обработка бюджета -----
@dp.message(OrderForm.budget)
async def process_budget(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'last_msg_id' in data:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except:
            pass
    await state.update_data(budget=message.text)
    await safe_delete(message)
    sent = await message.answer(
        "📱 Контакт (телефон или @username)",
        reply_markup=keyboard_with_back()
    )
    await state.update_data(last_msg_id=sent.message_id)
    await state.set_state(OrderForm.contact)

# ----- Обработка контакта и финал -----
@dp.message(OrderForm.contact)
async def process_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if 'last_msg_id' in data:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=data['last_msg_id'])
        except:
            pass
    await state.update_data(contact=message.text)
    await safe_delete(message)
    final_data = await state.get_data()

    # Отправка админу
    admin_text = (f"🔔 **НОВАЯ ЗАЯВКА**\n"
                  f"👤 {final_data['name']}\n🚘 {final_data['car']}\n💰 {final_data['budget']}$\n📱 {final_data['contact']}")
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        admin_ok = "✅ Заявка доставлена"
    except:
        admin_ok = "⚠️ Ошибка отправки, но мы всё получили"

    # Финальное сообщение пользователю
    final_msg = await message.answer(
        f"✅ **ГОТОВО**\n\n"
        f"👤 {final_data['name']}\n🚘 {final_data['car']}\n💰 {final_data['budget']}$\n📱 {final_data['contact']}\n\n"
        f"{admin_ok}\nСкоро свяжемся 🚀",
        reply_markup=main_menu_keyboard
    )
    # Чистим состояние
    await state.clear()

# ----- Кнопки "Назад" и "Отмена" внутри заявки -----
@dp.callback_query(lambda c: c.data == "back")
async def go_back(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    # Удаляем текущее сообщение (с вопросом и кнопкой Назад)
    await safe_delete(call.message)

    if current_state == OrderForm.car.state:
        # Возврат к имени
        await state.set_state(OrderForm.name)
        # отправляем вопрос заново
        sent = await call.message.answer(
            "🔥 Как тебя зовут?",
            reply_markup=keyboard_with_cancel()
        )
        await state.update_data(last_msg_id=sent.message_id)
    elif current_state == OrderForm.budget.state:
        # Возврат к машине
        await state.set_state(OrderForm.car)
        sent = await call.message.answer(
            "🚗 Какую тачку ищешь? (модель, год)",
            reply_markup=keyboard_with_back()
        )
        await state.update_data(last_msg_id=sent.message_id)
    elif current_state == OrderForm.contact.state:
        # Возврат к бюджету
        await state.set_state(OrderForm.budget)
        sent = await call.message.answer(
            "💰 Бюджет в $? (только цифры)",
            reply_markup=keyboard_with_back()
        )
        await state.update_data(last_msg_id=sent.message_id)
    else:
        # Неизвестный шаг — просто в меню
        await state.clear()
        await call.message.answer("🚀 Главное меню", reply_markup=main_menu_keyboard)
    await call.answer()

@dp.callback_query(lambda c: c.data == "cancel")
async def cancel_order(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await safe_delete(call.message)
    await call.message.answer("🚀 Главное меню", reply_markup=main_menu_keyboard)
    await call.answer()

# ----- Запуск -----
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
