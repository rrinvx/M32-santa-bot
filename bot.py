import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ---------------- CONFIGURATION ----------------
TOKEN = "9055623888:AAFwULuA56H0FMYGtXRrNw9XpYC3FTygMtQ"

# Твой Telegram ID (чтобы только ты была админом)
# Как узнать свой ID: напиши боту @userinfobot в Telegram, он пришлет цифры.
# Впиши свои цифры вместо 123456789 ниже:
ADMIN_ID = 947156597  

# ---------------- DATA STORAGE ----------------
# База данных участников (в памяти)
# Structure: { user_id: {"name": str, "username": str, "wishlist": str} }
participants = {}

# ---------------- FSM STATES ----------------
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_wishlist = State()

# ---------------- BOT SETUP ----------------
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# ---------------- HANDLERS ----------------

@dp.message(CommandStart())
async def start_cmd(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Если заходит админ без аргументов
    if user_id == ADMIN_ID and message.text == "/start":
        await message.answer(
            "👋 Вітаю, Організаторе M32!\n\n"
            "📋 Доступні команди адміна:\n"
            "• `/list` — переглянути список усіх зареєстрованих людей\n"
            "• `/count` — дізнатися кількість учасників\n"
            "• `/shuffle` — 🚀 ЗАПУСТИТИ РОЗПОДІЛ САНТИ",
            parse_mode="Markdown"
        )
        return

    # Перевірка чи вже зареєстрований
    if user_id in participants:
        p = participants[user_id]
        await message.answer(
            f"✅ Ви вже зареєстровані у «Таємному Санті M32»!\n\n"
            f"👤 **Ім'я:** {p['name']}\n"
            f"🎁 **Побажання:** {p['wishlist']}\n\n"
            f"Очікуйте, коли організатор запустить розподіл!",
            parse_mode="Markdown"
        )
        return

    await message.answer(
        "Привіт! 🎅 Ласкаво просимо до «Таємного Санти M32»!\n\n"
        "Будь ласка, напиши своє **Ім'я та Прізвище** (або як до тебе звертатися колегам):"
    )
    await state.set_state(Registration.waiting_for_name)

@dp.message(Registration.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await state.update_data(name=name)
    
    await message.answer(
        f"Приємно познайомитися, {name}! ✨\n\n"
        "Тепер напиши свої **побажання до подарунка** (вішліст, захоплення, вподобання або що точно не варто дарувати):"
    )
    await state.set_state(Registration.waiting_for_wishlist)

@dp.message(Registration.waiting_for_wishlist)
async def process_wishlist(message: Message, state: FSMContext):
    wishlist = message.text.strip()
    user_data = await state.get_data()
    
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "без юзернейму"
    
    participants[user_id] = {
        "name": user_data["name"],
        "username": username,
        "wishlist": wishlist
    }
    
    await state.clear()
    await message.answer(
        "🎉 **Чудово! Реєстрацію завершено!**\n\n"
        "Твої дані збережено. Коли всі колеги зареєструються, бот надішле тобі ім'я та побажання твого підопічного!",
        parse_mode="Markdown"
    )

# ---------------- ADMIN COMMANDS ----------------

@dp.message(Command("count"))
async def count_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"📊 Наразі зареєстровано участников: **{len(participants)}**", parse_mode="Markdown")

@dp.message(Command("list"))
async def list_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    if not participants:
        await message.answer("Список учасників поки порожній.")
        return
    
    text = "📋 **Список учасників:**\n\n"
    for idx, (uid, info) in enumerate(participants.items(), 1):
        text += f"{idx}. {info['name']} ({info['username']})\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("shuffle"))
async def shuffle_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = list(participants.keys())
    if len(users) < 3:
        await message.answer("⚠️ Для запуску Таємного Санти потрібно мінімум 3 учасники!")
        return
    
    # Алгоритм случайного перемешивания без совпадений с самим собой (Derangement)
    receivers = users.copy()
    while True:
        random.shuffle(receivers)
        if all(u != r for u, r in zip(users, receivers)):
            break
            
    await message.answer("🎲 Розподіл розпочато! Відправляю повідомлення учасникам...")
    
    success_count = 0
    for giver_id, receiver_id in zip(users, receivers):
        target = participants[receiver_id]
        msg_text = (
            "🎅 **Твій підопічний у «Таємному Санті M32»!**\n\n"
            f"👤 **Кому даруєш:** {target['name']} ({target['username']})\n"
            f"🎁 **Побажання до подарунка:**\n_{target['wishlist']}_\n\n"
            "🤫 Пам'ятай, це таємниця! Гарного свята!"
        )
        try:
            await bot.send_message(chat_id=giver_id, text=msg_text, parse_mode="Markdown")
            success_count += 1
        except Exception as e:
            logging.error(f"Помилка надсилання для {giver_id}: {e}")
            
    await message.answer(f"✅ Успішно надіслано **{success_count}** із {len(users)} учасників!")

# ---------------- MAIN ----------------
async def main():
    print("Бот M32_Santa запущений!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())