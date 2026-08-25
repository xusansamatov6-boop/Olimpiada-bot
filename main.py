import asyncio
import logging
import random
import sys
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

# Bot tokeningizni quyidagi qo‘shtirnoq ichiga yozing
TOKEN = "8859540171:AAEgnXmEy8UES1nDR527on7Yj0nGHhNZ91k"

dp = Dispatcher()

# Foydalanuvchi masala yechish jarayonida ekanligini kuzatib borish uchun holat
class QuizState(StatesGroup):
    waiting_for_answer = State()

# Fanlar bo'yicha kunlik batafsil mavzular bazasi
DAILY_LESSONS = [
    {
        "subject": "📐 Matematika",
        "explanation": (
            "📐 **Matematika: Arifmetik progressiya**\n\n"
            "**Ta'rif:** Har bir hadi o'zidan oldingi hadga bir xil o'zgarmas son ($d$) qo'shish orqali hosil qilinadigan sonlar ketma-ketligi arifmetik progressiya deyiladi.\n\n"
            "🔹 **Asosiy formulalar:**\n"
            "1. n-had formulasi: $a_n = a_1 + (n - 1)d$\n"
            "2. Dastlabki $n$ ta had yig'indisi: $S_n = \\frac{a_1 + a_n}{2} \\cdot n$\n\n"
            "💡 *Misol:* Agar $a_1 = 3$ va $d = 2$ bo'lsa, 5-hadni toping:\n"
            "$a_5 = 3 + (5 - 1) \\cdot 2 = 3 + 8 = 11$."
        )
    },
    {
        "subject": "🧬 Biologiya",
        "explanation": (
            "🧬 **Biologiya: Hujayra organoidlari**\n\n"
            "**Ta'rif:** Hujayra tirik organizmlarning tuzilish va funksional birligidir.\n\n"
            "🔹 **Asosiy organoidlar va vazifalari:**\n"
            "1. **Mitoxondriya:** Hujayraning 'energetik stansiyasi', ATF sintez qiladi.\n"
            "2. **Ribosoma:** Oqsil sintezini amalga oshiradi.\n"
            "3. **Xloroplast:** Faqat o'simlik hujayralarida bo'ladi, fotosintez jarayonida qatnashadi.\n"
            "4. **Yadro:** Irsiy axborotni saqlaydi va hujayra faoliyatini boshqaradi."
        )
    },
    {
        "subject": "🧪 Kimyo",
        "explanation": (
            "🧪 **Kimyo: Kimyoviy reaksiya turlari**\n\n"
            "**Ta'rif:** Bir yoki bir nechta moddaning boshqa moddalarga aylanish jarayoni kimyoviy reaksiya deyiladi.\n\n"
            "🔹 **Asosiy turlari:**\n"
            "1. **Qo'shilish reaksiyasi:** Ikki yoki undan ortiq moddadan bitta yangi modda hosil bo'ladi ($A + B \\rightarrow AB$).\n"
            "2. **Ajralish reaksiyasi:** Bitta murakkab moddadan ikki yoki undan ortiq modda hosil bo'ladi ($AB \\rightarrow A + B$).\n"
            "3. **O'rin olish va Almashinish reaksiyalari:** Murakkab va oddiy moddalarning tarkibiy qismlari almashinishi."
        )
    }
]

# Olimpiada masalalari, to'g'ri javoblari va ularning batafsil tahlili
TASKS = [
    {
        "question": (
            "📌 **Olimpiada masalasi (Algebra):**\n\n"
            "Agar $x + \\frac{1}{x} = 3$ bo'lsa, $x^3 + \\frac{1}{x^3}$ ning qiymatini toping."
        ),
        "answer": "18",
        "explanation": (
            "✅ **Tahlil va yechish yo'li:**\n"
            "1. Tenglikning ikki tomonini kubga oshiramiz: $(x + \\frac{1}{x})^3 = 3^3$\n"
            "2. Formulasiga ko'ra: $x^3 + \\frac{1}{x^3} + 3(x + \\frac{1}{x}) = 27$\n"
            "3. $x + \\frac{1}{x} = 3$ qiymatini o'rniga qo'yamiz:\n"
            "$x^3 + \\frac{1}{x^3} + 3(3) = 27 \\implies x^3 + \\frac{1}{x^3} = 27 - 9 = \mathbf{18}$."
        )
    },
    {
        "question": (
            "📌 **Olimpiada masalasi (Mantiq):**\n\n"
            "Uchta ketma-ket kelgan natural sonning yig'indisi 30 ga teng. Shu sonlarning o'rtadagisi nechaga teng?"
        ),
        "answer": "10",
        "explanation": (
            "✅ **Tahlil va yechish yo'li:**\n"
            "1. Sonlarni $(x-1), x, (x+1)$ deb belgilaymiz.\n"
            "2. Ularning yig'indisi: $(x-1) + x + (x+1) = 30$\n"
            "3. Soddalashtirsak: $3x = 30 \\implies x = 10$. Demak, o'rtadagi son 10 ga teng."
        )
    }
]

@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    full_name = html.quote(message.from_user.full_name)
    text = (
        f"Assalomu alaykum, {full_name}!\n\n"
        "Men matematika, biologiya va kimyo fanlaridan kunlik mavzularni tushuntiradigan hamda olimpiada masalalarini berib, ularni tekshiradigan aqlli yordamchi botman. 🚀\n\n"
        "📋 **Asosiy buyruqlar:**\n"
        "/mavzular - Matematika, Biologiya va Kimyo fanlaridan kunlik darslar\n"
        "/vazifa - Olimpiada masalasini olish va yechimni tekshirish\n"
        "/help - Yordam"
    )
    await message.answer(text)

@dp.message(Command(commands=["help"]))
async def command_help_handler(message: Message) -> None:
    text = (
        "💡 **Botdan foydalanish yo'riqnomasi:**\n\n"
        "• `/mavzular` — Har kuni o'rganish uchun uchala fanning asosiy mavzulari va tushuntirishlarini beradi.\n"
        "• `/vazifa` — Sizga qiziqarli masala tashlaydi, javobingizni yuborsangiz uni tekshirib, xato bo'lsa to'liq tahlilini tushuntiradi."
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command(commands=["mavzular"]))
async def command_lessons_handler(message: Message) -> None:
    await message.answer("📚 **Bugungi fanlar bo'yicha batafsil darslar:**")
    for lesson in DAILY_LESSONS:
        text = f"*{lesson['subject']}*\n\n{lesson['explanation']}"
        await message.answer(text, parse_mode=ParseMode.MARKDOWN)
        await asyncio.sleep(0.5)

@dp.message(Command(commands=["vazifa"]))
async def command_task_handler(message: Message, state: FSMContext) -> None:
    task = random.choice(TASKS)
    await state.update_data(correct_answer=task["answer"], explanation=task["explanation"])
    await state.set_state(QuizState.waiting_for_answer)
    await message.answer(task["question"] + "\n\n✍️ *Javobingizni shu yerga yuboring:*", parse_mode=ParseMode.MARKDOWN)

@dp.message(QuizState.waiting_for_answer)
async def check_user_answer(message: Message, state: FSMContext) -> None:
    user_answer = message.text.strip()
    data = await state.get_data()
    correct_answer = data.get("correct_answer")
    explanation = data.get("explanation")
    
    if user_answer == correct_answer:
        await message.answer("🎉 **Barakalla! Javobingiz to'g'ri!** 🏆")
    else:
        await message.answer(f"❌ **Afsus, javob noto'g'ri.** To'g'ri javob: `{correct_answer}`", parse_mode=ParseMode.MARKDOWN)
    
    await message.answer(explanation, parse_mode=ParseMode.MARKDOWN)
    await state.clear()

async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

