import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

# Bot tokeningizni quyidagi qo‘shtirnoq ichiga yozing (masalan: "123456:ABC-DEF...")
TOKEN = "8859540171:AAEgnXmEy8UES1nDR527on7Yj0nGHhNZ91k"

dp = Dispatcher()

# /start komandasi uchun
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    full_name = html.quote(message.from_user.full_name)
    text = (
        f"Assalomu alaykum, {full_name}!\n\n"
        "Men olimpiadaga tayyorgarlik ko‘rish, savollarni oson yo‘l bilan tushuntirish va bilimlaringizni sinash uchun tuzilgan botman. 🚀\n\n"
        "Buyruqlar:\n"
        "/help - Yordam olish\n"
        "/vazifa - Kunlik topshiriq"
    )
    await message.answer(text)

# /help komandasi uchun
@dp.message(Command(commands=["help"]))
async def command_help_handler(message: Message) -> None:
    text = (
        "💡 **Savollarni oson yo‘l bilan ishlash bo‘yicha maslahatlar:**\n\n"
        "1. Masalani diqqat bilan o‘qing va berilgan qiymatlarni yozib oling.\n"
        "2. Formula va qonuniyatlarni eslang.\n"
        "3. Agar qiyin bo'lsa, uni kichik qismlarga bo'lib chiqing.\n\n"
        "Savolingiz bo'lsa botga yuborishingiz mumkin!"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

# /vazifa komandasi uchun
@dp.message(Command(commands=["vazifa"]))
async def command_task_handler(message: Message) -> None:
    text = (
        "📌 **Bugungi mashq / vazifa:**\n\n"
        "1. Algebraik tenglamalarni soddalashtirish.\n"
        "2. Mantiqiy olimpiada masalasini yechish.\n\n"
        "Hozircha dam oling va vaqtingizni unumli foydalaning!"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
