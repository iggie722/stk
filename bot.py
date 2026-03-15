import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

# ========== ТВОИ ДАННЫЕ ==========
BOT_TOKEN = "8664150855:AAHfOhOAjlx2UoQ0gcEVyjGPIeWCm1mu67o"
ADMIN_ID = 1387177324
GIF_PATH = "welcome.gif"
# ================================

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Пытаемся загрузить гифку один раз при старте
try:
    welcome_gif = FSInputFile(GIF_PATH)
    GIF_EXISTS = True
except:
    GIF_EXISTS = False
    welcome_gif = None

# ========== КЛАВИАТУРЫ ==========
def keyboard_with_back():
    """Кнопка только 'Назад' (для шагов заявки, кроме первого)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ])

def keyboard_with_cancel():
    """Кнопка только 'Отмена' (для первого шага заявки)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

# Главное меню (после /start)
main_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📝 ОСТАВИТЬ ЗАЯВКУ", callback_data="order")],
    [InlineKeyboardButton(text="📞 СВЯЗАТЬСЯ", url="https://t.me/stk_motors_manager")],
    [InlineKeyboardButton(text="ℹ️ КАК МЫ РАБОТАЕМ", callback_data="how")]
])

# Кнопка возврата в главное меню (из раздела «Как мы работаем»)
back_to_menu_btn = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="◀️ В ГЛАВНОЕ МЕНЮ", callback_data="back_to_menu")]
])

# ========== СОСТОЯНИЯ ==========
class OrderForm(StatesGroup):
    name = State()
    car = State()
    budget = State()
    contact = State()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
async def safe_delete(message: types.Message):
    """Безопасное удаление сообщения (не падаем с ошибкой)"""
    try:
        await message.delete()
    except:
        pass

# ========== ОБРАБОТЧИКИ КОМАНД ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()                     # сбрасываем возможные старые состояния
    await safe_delete(message)              # удаляем команду /start

    text = ("🚀 **STK MOTORS** — твой проводник в мир JDM и Китая\n\n"
            "🇯🇵 Япония | 🇰🇷 Корея | 🇨🇳 Китай\n"
            "🔥 Аукционы, растаможка, под ключ")

    if GIF_EXISTS:
        await message.answer_animation(welcome_gif, caption=text, reply_markup=main_menu_keyboard)
    else:
        await message.answer(text, reply_markup=main_menu_keyboard)

@dp.callback_query(lambda c: c.data == "how")
async def how_work(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text(
        "🔧 **КАК МЫ РАБОТАЕМ:**\n\n"
        "1️⃣ Ты оставляешь заявку\n"
        "2️⃣ Мы подбираем 3‑5 вариантов под твой бюджет\n"
        "3️⃣ Выкупаем авто с аукциона\n"
        "4️⃣ Доставка и растаможка «под ключ»\n"
        "5️⃣ Ты забираешь машину и кайфуешь 🚗💨",
        reply_markup=back_to_menu_btn
    )

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_main_menu(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await call.message.edit_text("🚀 Главное меню", reply_markup=main_menu_keyboard)

# ========== НАЧАЛО ЗАЯВКИ ==========
@dp.callback_query(lambda c: c.data == "order")
async def order_start(call: types.CallbackQuery, state: FSMContext):
    await call.answer()                          # обязательно отвечаем, чтобы кнопка не висела
    await safe_delete(call.message)               # удаляем сообщение с кнопкой

    sent = await call.message.answer(
        "🔥 Как тебя зовут?",
        reply_markup=keyboard_with_cancel()       # на первом шаге только «Отмена»
    )
    await state.clear()
    await state.set_state(OrderForm.name)
    await state.update_data(last_msg_id=sent.message_id)   # запоминаем ID последнего сообщения

# ========== ОСНОВНЫЕ ШАГИ ЗАЯВКИ ==========
@dp.message(OrderForm.name)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    # удаляем предыдущее сообщение бота (вопрос про имя)
    if last_id := data.get('last_msg_id'):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_id)
        except:
            pass
    await state.update_data(name=message.text)
    await safe_delete(message)                     # удаляем сообщение пользователя

    sent = await message.answer(
        "🚗 Какую тачку ищешь? (модель, год)",
        reply_markup=keyboard_with_back()           # теперь кнопка «Назад»
    )
    await state.update_data(last_msg_id=sent.message_id)
    await state.set_state(OrderForm.car)

@dp.message(OrderForm.car)
async def process_car(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if last_id := data.get('last_msg_id'):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_id)
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

@dp.message(OrderForm.budget)
async def process_budget(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if last_id := data.get('last_msg_id'):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_id)
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

# ========== ФИНАЛ ==========
@dp.message(OrderForm.contact)
async def process_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if last_id := data.get('last_msg_id'):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=last_id)
        except:
            pass
    await state.update_data(contact=message.text)
    await safe_delete(message)

    final_data = await state.get_data()

    # Отправка админу
    admin_text = (f"🔔 **НОВАЯ ЗАЯВКА**\n"
                  f"👤 Имя: {final_data['name']}\n"
                  f"🚘 Авто: {final_data['car']}\n"
                  f"💰 Бюджет: {final_data['budget']}$\n"
                  f"📱 Контакт: {final_data['contact']}")
    try:
        await bot.send_message(ADMIN_ID, admin_text)
        admin_ok = "✅ Заявка доставлена менеджеру"
    except:
        admin_ok = "⚠️ Ошибка отправки, но мы всё получили, скоро свяжемся!"

    # Финальное сообщение пользователю
    final_msg = await message.answer(
        f"✅ **ГОТОВО!**\n\n"
        f"👤 {final_data['name']}\n"
        f"🚘 {final_data['car']}\n"
        f"💰 {final_data['budget']}$\n"
        f"📱 {final_data['contact']}\n\n"
        f"{admin_ok}\n\n"
        f"Скоро с тобой свяжутся 🚀",
        reply_markup=main_menu_keyboard
    )
    await state.clear()

# ========== КНОПКИ НАВИГАЦИИ (НАЗАД / ОТМЕНА) ==========
@dp.callback_query(lambda c: c.data == "back")
async def go_back(call: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    data = await state.get_data()
    await call.answer()
    await safe_delete(call.message)          # удаляем текущее сообщение с кнопкой

    if current_state == OrderForm.car.state:
        # возврат к имени
        await state.set_state(OrderForm.name)
        sent = await call.message.answer(
            "🔥 Как тебя зовут?",
            reply_markup=keyboard_with_cancel()
        )
        await state.update_data(last_msg_id=sent.message_id)

    elif current_state == OrderForm.budget.state:
        # возврат к машине
        await state.set_state(OrderForm.car)
        sent = await call.message.answer(
            "🚗 Какую тачку ищешь? (модель, год)",
            reply_markup=keyboard_with_back()
        )
        await state.update_data(last_msg_id=sent.message_id)

    elif current_state == OrderForm.contact.state:
        # возврат к бюджету
        await state.set_state(OrderForm.budget)
        sent = await call.message.answer(
            "💰 Бюджет в $? (только цифры)",
            reply_markup=keyboard_with_back()
        )
        await state.update_data(last_msg_id=sent.message_id)

    else:
        # неизвестный шаг — просто в меню
        await state.clear()
        await call.message.answer("🚀 Главное меню", reply_markup=main_menu_keyboard)

@dp.callback_query(lambda c: c.data == "cancel")
async def cancel_order(call: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await call.answer()
    await safe_delete(call.message)
    await call.message.answer("🚀 Главное меню", reply_markup=main_menu_keyboard)

# ========== ЗАПУСК ==========
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
