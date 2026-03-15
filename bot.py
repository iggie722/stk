import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8664150855:AAHfOhOAjlx2UoQ0gcEVyjGPIeWCm1mu67o"  # ← СЮДА ТВОЙ ТОКЕН
ADMIN_ID = 1387177324  # ← ТВОЙ TELEGRAM ID (узнай у @userinfobot)
# ================================

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Путь к гифке (положи в папку с ботом)
GIF_PATH = "welcome.gif"  # Название твоего файла

# ========== СОСТОЯНИЯ ДЛЯ ЗАЯВКИ ==========
class OrderForm(StatesGroup):
    name = State()
    car = State()
    budget = State()
    contact = State()

# ========== КЛАВИАТУРЫ ==========
def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="📝 ОСТАВИТЬ ЗАЯВКУ",
        callback_data="start_order"
    ))
    builder.add(InlineKeyboardButton(
        text="📞 СВЯЗАТЬСЯ",
        url="https://t.me/stk_motors_manager"  # Замени на свой контакт
    ))
    builder.add(InlineKeyboardButton(
        text="ℹ️ КАК МЫ РАБОТАЕМ",
        callback_data="how_we_work"
    ))
    builder.adjust(1)  # По одной кнопке в ряд
    return builder.as_markup()

# ========== ОБРАБОТЧИКИ ==========

# /start — приветствие с гифкой
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Отправляем гифку, если файл существует
    if os.path.exists(GIF_PATH):
        try:
            gif = FSInputFile(GIF_PATH)
            await message.answer_animation(
                animation=gif,
                caption="🚀 **STK MOTORS** — твой проводник в мир JDM и Китая\n\n"
                        "Заполни заявку — получишь лучшие варианты под твой бюджет\n\n"
                        "🇯🇵 Япония | 🇰🇷 Корея | 🇨🇳 Китай\n"
                        "🔥 Аукционы, растаможка, под ключ",
                parse_mode="Markdown",
                reply_markup=get_start_keyboard()
            )
        except Exception as e:
            # Если гифка не грузится, отправляем просто текст
            await message.answer(
                "🚀 **STK MOTORS** — твой проводник в мир JDM и Китая\n\n"
                "Заполни заявку — получишь лучшие варианты под твой бюджет\n\n"
                "🇯🇵 Япония | 🇰🇷 Корея | 🇨🇳 Китай\n"
                "🔥 Аукционы, растаможка, под ключ",
                parse_mode="Markdown",
                reply_markup=get_start_keyboard()
            )
    else:
        # Если файла нет, отправляем просто текст
        await message.answer(
            "🚀 **STK MOTORS** — твой проводник в мир JDM и Китая\n\n"
            "Заполни заявку — получишь лучшие варианты под твой бюджет\n\n"
            "🇯🇵 Япония | 🇰🇷 Корея | 🇨🇳 Китай\n"
            "🔥 Аукционы, растаможка, под ключ",
            parse_mode="Markdown",
            reply_markup=get_start_keyboard()
        )

# Обработчик кнопки "Как мы работаем"
@dp.callback_query(F.data == "how_we_work")
async def how_we_work(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔧 **КАК МЫ РАБОТАЕМ:**\n\n"
        "1️⃣ Ты оставляешь заявку\n"
        "2️⃣ Мы подбираем 3-5 вариантов под твой бюджет\n"
        "3️⃣ Ты выбираешь авто, мы выкупаем его с аукциона\n"
        "4️⃣ Доставка, растаможка — все под ключ\n"
        "5️⃣ Ты забираешь тачку и кайфуешь 🚗💨\n\n"
        "Сроки: от 3 до 8 недель\n"
        "Оплата: поэтапно, прозрачно",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="◀️ НАЗАД", callback_data="back_to_menu")]
            ]
        )
    )

# Кнопка "Назад"
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🚀 **STK MOTORS** — главное меню\n\n"
        "Выбери действие:",
        parse_mode="Markdown",
        reply_markup=get_start_keyboard()
    )

# Начало оформления заявки
@dp.callback_query(F.data == "start_order")
async def start_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🔥 Ок, бро! Сейчас все оформим за минуту.\n\n"
        "**Как тебя зовут?**",
        parse_mode="Markdown"
    )
    await state.set_state(OrderForm.name)

# Получаем имя
@dp.message(OrderForm.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        f"Круто, {message.text}! 🚗\n\n"
        "**Какую тачку ищешь?**\n"
        "(Напиши марку, модель, год)"
    )
    await state.set_state(OrderForm.car)

# Получаем машину
@dp.message(OrderForm.car)
async def process_car(message: types.Message, state: FSMContext):
    await state.update_data(car=message.text)
    await message.answer(
        "💰 **Твой бюджет в $?**\n"
        "(Напиши число)"
    )
    await state.set_state(OrderForm.budget)

# Получаем бюджет
@dp.message(OrderForm.budget)
async def process_budget(message: types.Message, state: FSMContext):
    await state.update_data(budget=message.text)
    await message.answer(
        "📱 **Телефон или Telegram для связи?**\n"
        "(Напиши @username или номер)"
    )
    await state.set_state(OrderForm.contact)

# Получаем контакт и завершаем
@dp.message(OrderForm.contact)
async def process_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    
    # ===== ОТПРАВЛЯЕМ ЗАЯВКУ АДМИНУ =====
    admin_message = (
        "🔔 **НОВАЯ ЗАЯВКА STK MOTORS**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Имя:** {data['name']}\n"
        f"🚘 **Авто:** {data['car']}\n"
        f"💰 **Бюджет:** {data['budget']}$\n"
        f"📱 **Контакт:** {data['contact']}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
        admin_status = "✅ Заявка доставлена менеджеру"
    except Exception as e:
        logging.error(f"Не удалось отправить админу: {e}")
        admin_status = "⚠️ Ошибка отправки, но мы скоро все починим"
    
    # ===== ОТВЕТ ПОЛЬЗОВАТЕЛЮ =====
    await message.answer(
        f"✅ **ГОТОВО!**\n\n"
        f"Твоя заявка:\n"
        f"👤 {data['name']}\n"
        f"🚘 {data['car']}\n"
        f"💰 {data['budget']}$\n"
        f"📱 {data['contact']}\n\n"
        f"{admin_status}\n\n"
        f"Ответим в ближайшее время 🚀\n\n"
        f"А пока подпишись на наш канал: @stk_motors_channel",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В ГЛАВНОЕ МЕНЮ", callback_data="back_to_menu")]
            ]
        )
    )
    
    # Завершаем состояние
    await state.clear()

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())