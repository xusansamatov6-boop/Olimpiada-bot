from datetime import datetime
import os
import sqlite3
from fpdf import FPDF
import telebot
from telebot import types

TOKEN = "8837989491:AAH1RVzXjn-7mOQdNd8dJXkSZoqQbVZRNr4"
SUPER_ADMIN_ID = 7649769072  # O'zingizning Telegram ID raqamingizni yozing
CHANNELS = ["@Bilim_Arena"]  # Majburiy obuna kanali (agar shart bo'lmasa, bo'sh qoldirishingiz mumkin)

bot = telebot.TeleBot(TOKEN)

# --- BAZANI SOZLASH (SQLite) ---
conn = sqlite3.connect("edu_teacher_bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    role TEXT,
    referrer_id INTEGER DEFAULT 0,
    referrals_count INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS admins (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id INTEGER,
    creator_name TEXT,
    test_title TEXT,
    answers TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    full_name TEXT,
    test_id INTEGER,
    test_title TEXT,
    score INTEGER,
    total INTEGER,
    date TEXT
)
""")

cursor.execute(
    "INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (SUPER_ADMIN_ID,)
)
conn.commit()


def is_admin(user_id):
  cursor.execute("SELECT user_id FROM admins WHERE user_id = ?", (user_id,))
  return cursor.fetchone() is not None


def check_sub(user_id):
  if not CHANNELS or CHANNELS[0] == "@kanal_username":
    return True
  for channel in CHANNELS:
    try:
      member = bot.get_chat_member(chat_id=channel, user_id=user_id)
      if member.status not in ["creator", "administrator", "member"]:
        return False
    except Exception:
      return False
  return True


def sub_keyboard():
  markup = types.InlineKeyboardMarkup()
  for channel in CHANNELS:
    btn = types.InlineKeyboardButton(
        text=f"📢 {channel} ga obuna bo'lish",
        url=f"https://t.me/{channel.replace('@', '')}",
    )
    markup.add(btn)
  check_btn = types.InlineKeyboardButton(
      text="✅ Obunani tekshirish", callback_data="check_subscription"
  )
  markup.add(check_btn)
  return markup


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.from_user.id
  command_args = message.text.split()
  referrer_id = 0
  if len(command_args) > 1 and command_args[1].isdigit():
    referrer_id = int(command_args[1])
    if referrer_id == user_id:
      referrer_id = 0

  cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
  user = cursor.fetchone()

  if user is None:
    cursor.execute(
        "INSERT INTO users (user_id, full_name, referrer_id) VALUES (?, ?, ?)",
        (user_id, message.from_user.first_name, referrer_id),
    )
    conn.commit()

    if referrer_id != 0:
      cursor.execute(
          "UPDATE users SET referrals_count = referrals_count + 1 WHERE"
          " user_id = ?",
          (referrer_id,),
      )
      conn.commit()

    ask_role(message.chat.id)
    return

  if not check_sub(user_id):
    bot.send_message(
        message.chat.id,
        "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:",
        reply_markup=sub_keyboard(),
    )
    return

  show_main_menu(message, user[0])


def ask_role(chat_id):
  markup = types.InlineKeyboardMarkup()
  markup.add(
      types.InlineKeyboardButton(
          "👨‍🎓 O'quvchi", callback_data="role_student"
      ),
      types.InlineKeyboardButton(
          "👨‍🏫 O'qituvchi", callback_data="role_teacher"
      ),
  )
  bot.send_message(
      chat_id,
      "Assalomu alaykum! Botimizga xush kelibsiz.\nIltimos, o'z"
      " rolingizni tanlang:",
      reply_markup=markup,
  )


@bot.callback_query_handler(
    func=lambda call: call.data in ["role_student", "role_teacher"]
)
def set_role(call):
  role = "O'quvchi" if call.data == "role_student" else "O'qituvchi"
  cursor.execute(
      "UPDATE users SET role = ? WHERE user_id = ?",
      (role, call.from_user.id),
  )
  conn.commit()

  bot.answer_callback_query(call.id, f"Rolingiz '{role}' sifatida saqlandi!")
  bot.delete_message(call.message.chat.id, call.message.message_id)

  if not check_sub(call.from_user.id):
    bot.send_message(
        call.message.chat.id,
        "⚠️ Botdan foydalanish uchun kanallarga obuna bo'ling:",
        reply_markup=sub_keyboard(),
    )
    return

  show_main_menu(call.message, role)


@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_sub(call):
  if check_sub(call.from_user.id):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.send_message(
        call.message.chat.id, "✅ Obuna tasdiqlandi! Xush kelibsiz."
    )
    cursor.execute(
        "SELECT role FROM users WHERE user_id = ?", (call.from_user.id,)
    )
    role_res = cursor.fetchone()
    role = role_res[0] if role_res else "O'quvchi"
    show_main_menu(call.message, role)
  else:
    bot.answer_callback_query(
        call.id,
        "❌ Siz hali barcha kanallarga obuna bo'lmadingiz!",
        show_alert=True,
    )


def show_main_menu(message, role):
  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

  if role == "O'qituvchi":
    markup.add(
        types.KeyboardButton("➕ Test yaratish"),
        types.KeyboardButton("📋 Mening testlarim"),
    )
  else:
    markup.add(
        types.KeyboardButton("📝 Test topshirish"),
        types.KeyboardButton("🏆 Reyting"),
    )

  markup.add(types.KeyboardButton("🔗 Taklif havolam"))

  if is_admin(message.from_user.id):
    markup.add(types.KeyboardButton("⚙️ Admin Panel"))

  bot.send_message(
      message.chat.id,
      f"Bosh menyu ({role} rejimi):",
      reply_markup=markup,
  )


@bot.message_handler(func=lambda message: message.text == "➕ Test yaratish")
def create_test_prompt(message):
  cursor.execute(
      "SELECT role FROM users WHERE user_id = ?", (message.from_user.id,)
  )
  user = cursor.fetchone()
  if not user or user[0] != "O'qituvchi":
    bot.send_message(
        message.chat.id, "❌ Bu funksiya faqat o'qituvchilar uchun!"
    )
    return

  msg = bot.send_message(
      message.chat.id,
      "Test nomini kiriting (masalan: *Matematika 1-bob*):",
      parse_mode="Markdown",
  )
  bot.register_next_step_handler(msg, save_test_title)


def save_test_title(message):
  title = message.text
  msg = bot.send_message(
      message.chat.id,
      f"Test nomi: **{title}**\nEndi to'g'ri javoblarni ketma-ket"
      " yuboring.\nFormat: `ABCDA` (bo'shliqlarsiz)",
      parse_mode="Markdown",
  )
  bot.register_next_step_handler(msg, save_test_answers, title)


def save_test_answers(message, title):
  answers = message.text.upper().replace(" ", "")
  creator_id = message.from_user.id
  creator_name = message.from_user.first_name

  cursor.execute(
      "INSERT INTO tests (creator_id, creator_name, test_title, answers)"
      " VALUES (?, ?, ?, ?)",
      (creator_id, creator_name, title, answers),
  )
  conn.commit()

  bot.send_message(
      message.chat.id,
      f"✅ **Test muvaffaqiyatli yaratildi!**\nNomi: {title}\nJavoblar soni:"
      f" {len(answers)} ta",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: message.text == "📋 Mening testlarim")
def my_tests(message):
  cursor.execute(
      "SELECT id, test_title, answers FROM tests WHERE creator_id = ?",
      (message.from_user.id,),
  )
  tests = cursor.fetchall()

  if not tests:
    bot.send_message(
        message.chat.id, "Siz hali hech qanday test yaratmagansiz."
    )
    return

  text = "📋 **Siz yaratgan testlar:**\n\n"
  for t in tests:
    text += f"🆔 ID: `{t[0]}` | Nomi: **{t[1]}** | Javoblar: `{t[2]}`\n"

  bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "📝 Test topshirish")
def list_available_tests(message):
  cursor.execute("SELECT id, test_title, creator_name FROM tests")
  tests = cursor.fetchall()

  if not tests:
    bot.send_message(
        message.chat.id,
        "Hozircha o'qituvchilar tomonidan yaratilgan testlar mavjud emas.",
    )
    return

  markup = types.InlineKeyboardMarkup()
  for t in tests:
    btn = types.InlineKeyboardButton(
        text=f"📚 {t[1]} (Ustoz: {t[2]})", callback_data=f"take_test_{t[0]}"
    )
    markup.add(btn)

  bot.send_message(
      message.chat.id,
      "Quyidagi testlardan birini tanlang:",
      reply_markup=markup,
  )


@bot.callback_query_handler(func=lambda call: call.data.startswith("take_test_"))
def select_test_callback(call):
  test_id = int(call.data.split("_")[2])
  cursor.execute(
      "SELECT test_title, answers FROM tests WHERE id = ?", (test_id,)
  )
  test = cursor.fetchone()

  if not test:
    bot.answer_callback_query(call.id, "❌ Test topilmadi!", show_alert=True)
    return

  msg = bot.send_message(
      call.message.chat.id,
      f"📝 **{test[0]}**\nJavoblarni yuboring (Masalan: `ABCDA`):",
      parse_mode="Markdown",
  )
  bot.register_next_step_handler(
      msg, process_student_answers, test_id, test[0], test[1]
  )


def process_student_answers(message, test_id, test_title, correct_answers):
  answers = message.text.upper().replace(" ", "")

  if len(answers) != len(correct_answers):
    bot.send_message(
        message.chat.id,
        f"❌ Xato! Javoblar soni {len(correct_answers)} ta bo'lishi kerak.",
    )
    return

  score = sum(
      1 for i in range(len(correct_answers)) if answers[i] == correct_answers[i]
  )
  total = len(correct_answers)
  date = datetime.now().strftime("%Y-%m-%d %H:%M")

  cursor.execute(
      "INSERT INTO results (user_id, full_name, test_id, test_title, score,"
      " total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
      (
          message.from_user.id,
          message.from_user.first_name,
          test_id,
          test_title,
          score,
          total,
          date,
      ),
  )
  conn.commit()

  bot.send_message(
      message.chat.id,
      f"✅ **Test Yakunlandi!**\nTest: {test_title}\nNatija:"
      f" **{score}/{total}**",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: message.text == "🏆 Reyting")
def show_leaderboard(message):
  cursor.execute("""
        SELECT full_name, test_title, score, total 
        FROM results 
        ORDER BY score DESC 
        LIMIT 10
    """)
  rows = cursor.fetchall()

  if not rows:
    bot.send_message(message.chat.id, "🏆 Reytingda hali natijalar yo'q.")
    return

  text = "🏆 **Eng yaxshi natijalar (Top 10):**\n\n"
  for idx, row in enumerate(rows, 1):
    text += f"{idx}. **{row[0]}** — Test: {row[1]} ({row[2]}/{row[3]})\n"

  bot.send_message(message.chat.id, text, parse_mode="Markdown")


@bot.message_handler(func=lambda message: message.text == "🔗 Taklif havolam")
def ref_link(message):
  user_id = message.from_user.id
  cursor.execute(
      "SELECT referrals_count FROM users WHERE user_id = ?", (user_id,)
  )
  count = cursor.fetchone()[0]
  bot_info = bot.get_me()
  link = f"https://t.me/{bot_info.username}?start={user_id}"

  bot.send_message(
      message.chat.id,
      f"👥 **Sizning taklif havolangiz:**\n`{link}`\n\n📊 Taklif qilgan"
      f" do'stlaringiz: **{count} ta**",
      parse_mode="Markdown",
  )


@bot.message_handler(func=lambda message: message.text == "⚙️ Admin Panel")
def admin_panel(message):
  if not is_admin(message.from_user.id):
    return

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  markup.add(
      types.KeyboardButton("📄 PDF Hisobot yuklash"),
      types.KeyboardButton("🔙 Bosh menyu"),
  )
  bot.send_message(message.chat.id, "⚙️ Admin Panel:", reply_markup=markup)


@bot.message_handler(
    func=lambda message: message.text == "📄 PDF Hisobot yuklash"
)
def generate_pdf_report(message):
  if not is_admin(message.from_user.id):
    return

  pdf = FPDF()
  pdf.add_page()
  pdf.set_font("Arial", "B", 14)
  pdf.cell(
      200, 10, txt="Ta'lim Boti - Test Natijalari Hisoboti", ln=1, align="C"
  )
  pdf.ln(5)

  pdf.set_font("Arial", "B", 8)
  pdf.cell(35, 8, "Ism", 1)
  pdf.cell(35, 8, "Test Nomi", 1)
  pdf.cell(20, 8, "Natija", 1)
  pdf.cell(40, 8, "Sana", 1)
  pdf.ln()

  cursor.execute(
      "SELECT full_name, test_title, score, total, date FROM results"
  )
  rows = cursor.fetchall()

  pdf.set_font("Arial", "", 8)
  for row in rows:
    pdf.cell(35, 8, str(row[0])[:15], 1)
    pdf.cell(35, 8, str(row[1])[:15], 1)
    pdf.cell(20, 8, f"{row[2]}/{row[3]}", 1)
    pdf.cell(40, 8, str(row[4]), 1)
    pdf.ln()

  filename = "talim_hisobot.pdf"
  pdf.output(filename)

  with open(filename, "rb") as doc:
    bot.send_document(message.chat.id, doc, caption="📄 To'liq hisobot PDF")

  os.remove(filename)


@bot.message_handler(func=lambda message: message.text == "🔙 Bosh menyu")
def back_main(message):
  cursor.execute(
      "SELECT role FROM users WHERE user_id = ?", (message.from_user.id,)
  )
  user = cursor.fetchone()
  role = user[0] if user else "O'quvchi"
  show_main_menu(message, role)


print("Bot ishga tushdi...")
bot.infinity_polling()


