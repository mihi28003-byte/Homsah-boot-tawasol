import os
import logging
import sqlite3
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8469137801

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

BANNED_WORDS = ["شتيمة1", "شتيمة2", "إهانة"]

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY)")
    c.execute(
        "CREATE TABLE IF NOT EXISTS messages (msg_id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER, admin_msg_id INTEGER)"
    )
    c.execute("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER)")
    c.execute("INSERT OR IGNORE INTO stats VALUES ('total_messages', 0)")
    conn.commit()
    conn.close()

init_db()

def is_banned(user_id):
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res is not None

def add_ban(user_id):
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO banned_users VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def increment_stats():
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("UPDATE stats SET value = value + 1 WHERE key = 'total_messages'")
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("SELECT value FROM stats WHERE key = 'total_messages'")
    val = c.fetchone()[0]
    conn.close()
    return val

def save_message_map(sender_id, admin_msg_id):
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender_id, admin_msg_id) VALUES (?, ?)", (sender_id, admin_msg_id))
    conn.commit()
    conn.close()

def get_sender_by_admin_msg(admin_msg_id):
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()
    c.execute("SELECT sender_id FROM messages WHERE admin_msg_id = ?", (admin_msg_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

# ---------------- BOT FUNCTIONS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤫 أهلاً بك في بوت صراحة المجهول\n"
        "ابعت رسالتك وهتوصل للأدمن بسرية تامة."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # رد الأدمن
    if user_id == ADMIN_ID and update.message.reply_to_message:
        target_user_id = get_sender_by_admin_msg(update.message.reply_to_message.message_id)
        if target_user_id:
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=f"📩 رد من الأدمن:\n\n{update.message.text}"
                )
                await update.message.reply_text("✅ تم إرسال الرد")
            except:
                await update.message.reply_text("❌ فشل الإرسال")
            return

    if is_banned(user_id):
        await update.message.reply_text("🚫 أنت محظور من استخدام البوت")
        return

    text = update.message.text or update.message.caption or ""
    if any(word in text for word in BANNED_WORDS):
        await update.message.reply_text("❌ تحتوي الرسالة على كلمات غير مسموحة")
        return

    keyboard = [[InlineKeyboardButton("حظر المستخدم 🚫", callback_data=f"ban_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        sent_msg = await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 رسالة جديدة:\n\n{text}",
            reply_markup=reply_markup
        )

        save_message_map(user_id, sent_msg.message_id)
        increment_stats()

        await update.message.reply_text("✅ تم إرسال رسالتك بسرية")

    except Exception as e:
        logging.error(e)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("ban_"):
        user_to_ban = int(query.data.split("_")[1])
        add_ban(user_to_ban)
        await query.answer("🚫 تم الحظر")
        await query.edit_message_reply_markup(reply_markup=None)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        total = get_stats()
        await update.message.reply_text(f"📊 إجمالي الرسائل: {total}")

# ---------------- WEB SERVER FOR KOYEB ----------------
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running successfully!"

def run_web():
    port = int(os.environ.get("PORT", 8000))
    web_app.run(host="0.0.0.0", port=port)

def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    run_bot()    return res[0] if res else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك في بوت صراحة المجهول! 🤫\nأرسل رسالتك الآن وسأوصلها للأدمن بسرية تامة.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # إذا كان الأدمن يرد على رسالة
    if user_id == ADMIN_ID and update.message.reply_to_message:
        target_user_id = get_sender_by_admin_msg(update.message.reply_to_message.message_id)
        if target_user_id:
            try:
                await context.bot.send_message(chat_id=target_user_id, text=f"وصلك رد من الأدمن: \n\n{update.message.text}")
                await update.message.reply_text("تم إرسال ردك للمستخدم بنجاح! ✅")
            except Exception:
                await update.message.reply_text("فشل إرسال الرد (ربما قام المستخدم بحظر البوت).")
            return

    # منع المحظورين
    if is_banned(user_id):
        await update.message.reply_text("عذراً، أنت محظور من استخدام البوت.")
        return

    # فلترة الكلمات
    text = update.message.text or update.message.caption or ""
    if any(word in text for word in BANNED_WORDS):
        await update.message.reply_text("رسالتك تحتوي على كلمات غير لائقة ولم يتم إرسالها.")
        return

    # إرسال للأدمن
    admin_alert = "📩 **رسالة صراحة جديدة:**\n\n"
    keyboard = [[InlineKeyboardButton("حظر المستخدم 🚫", callback_data=f"ban_{user_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        sent_msg = None
        if update.message.text:
            sent_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=f"{admin_alert}{update.message.text}", reply_markup=reply_markup)
        elif update.message.photo:
            sent_msg = await context.bot.send_photo(chat_id=ADMIN_ID, photo=update.message.photo[-1].file_id, caption=admin_alert, reply_markup=reply_markup)
        elif update.message.voice:
            sent_msg = await context.bot.send_voice(chat_id=ADMIN_ID, voice=update.message.voice.file_id, caption=admin_alert, reply_markup=reply_markup)
        
        if sent_msg:
            save_message_map(user_id, sent_msg.message_id)
            increment_stats()
            await update.message.reply_text("تم إرسال رسالتك بنجاح وبسرية تامة! ✅")
    except Exception as e:
        logging.error(f"Error: {e}")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data.startswith("ban_"):
        user_to_ban = int(query.data.split("_")[1])
        add_ban(user_to_ban)
        await query.answer("تم حظر المستخدم بنجاح! 🚫")
        await query.edit_message_reply_markup(reply_markup=None)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        total = get_stats()
        await update.message.reply_text(f"📊 إحصائيات البوت:\n\nإجمالي الرسائل المستلمة: {total}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(MessageHandler(filters.ALL & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    print("البوت المطور يعمل الآن...")
    application.run_polling()
