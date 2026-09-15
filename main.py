import os
import random
import string
import logging
import sqlite3
import threading
import urllib.parse
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Dummy Web Server for Render Health Checks
app = Flask(__name__)

@app.route('/')
def home():
    return "z.ween2x Bot is running live!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config & Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_RAW = os.environ.get("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW and ADMIN_ID_RAW.isdigit() else None
UPI_ID = "z.ween2x.official@okaxis"
ENTRY_FEE = 100

TELEGRAM_CHANNEL_LINK = "https://t.me/+W0nd-axUCgdiZWZl"
YOUTUBE_CHANNEL_LINK = "https://youtube.com/@zween2x?si=NlZ7_M-fJ-Dg3B0T"

ASK_ROLE, ASK_TOKEN, ASK_NAME, ASK_IGN, ASK_UID, ASK_CONTACT, ASK_LOCATION, ASK_PAYMENT = range(8)
DB_FILE = "tournament.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_code TEXT UNIQUE,
            created_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            role TEXT,
            user_id INTEGER,
            full_name TEXT,
            ign TEXT,
            ff_uid TEXT,
            contact TEXT,
            location TEXT,
            utr TEXT,
            token TEXT UNIQUE,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY(team_id) REFERENCES teams(team_id)
        )
    ''')
    conn.commit()
    conn.close()

def generate_random_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_upi_qr_url(upi_id, name, amount):
    params = {"pa": upi_id, "pn": name, "am": str(amount), "cu": "INR"}
    upi_uri = f"upi://pay?{urllib.parse.urlencode(params)}"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_uri)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    welcome_msg = (
        "🔥 *Welcome to z.ween2x Official Tournament Registration Bot!* 🔥\n\n"
        "Aap tournament me kis tarah register karna chahte hain?\n\n"
        "1️⃣ **Nayi Team Banayein (Team Leader)**\n"
        "2️⃣ **Pehle Se Bani Team Me Judein (Teammate)**"
    )
    keyboard = [
        [InlineKeyboardButton("👑 Nayi Team (Leader)", callback_data="role_leader")],
        [InlineKeyboardButton("🎮 Existing Team (Teammate)", callback_data="role_member")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(welcome_msg, parse_mode="Markdown", reply_markup=reply_markup)
    
    return ASK_ROLE

async def role_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    role = query.data
    
    if role == "role_leader":
        context.user_data['is_leader'] = True
        context.user_data['role_char'] = 'A'
        await query.message.reply_text("👤 Kripya apna **Full Name** enter karein:", parse_mode="Markdown")
        return ASK_NAME
    else:
        context.user_data['is_leader'] = False
        await query.message.reply_text(
            "🔑 Kripya apne Team Leader ka **Token Code** enter karein:\n"
            "*(Example: `#zween2x-1-A-X8K9P`)*",
            parse_mode="Markdown"
        )
        return ASK_TOKEN

async def process_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    token_input = update.message.text.strip()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT team_id, role, token FROM players WHERE token = ?", (token_input,))
    leader_entry = cursor.fetchone()
    
    if not leader_entry:
        conn.close()
        await update.message.reply_text(
            "⚠️ **Invalid Token Code!**\n\n"
            "Kripya apne Leader se sahi Token maangein aur dobara type karein:",
            parse_mode="Markdown"
        )
        return ASK_TOKEN
    
    team_id = leader_entry[0]
    cursor.execute("SELECT COUNT(*) FROM players WHERE team_id = ?", (team_id,))
    player_count = cursor.fetchone()[0]
    
    if player_count >= 4:
        conn.close()
        await update.message.reply_text(
            "❌ **Team Full!**\nIs team me pehle hi 4 players poore ho chuke hain.",
            parse_mode="Markdown"
        )
        return ConversationHandler.END
    
    role_map = {1: 'B', 2: 'C', 3: 'D'}
    context.user_data['team_id'] = team_id
    context.user_data['role_char'] = role_map.get(player_count, 'D')
    
    cursor.execute("SELECT base_code FROM teams WHERE team_id = ?", (team_id,))
    base_res = cursor.fetchone()
    context.user_data['base_code'] = base_res[0] if base_res else "TEMP"
    
    conn.close()
    
    await update.message.reply_text("✅ Token Valid! Ab apna **Full Name** enter karein:", parse_mode="Markdown")
    return ASK_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['full_name'] = update.message.text.strip()
    await update.message.reply_text("🎮 Apna **In-Game Name (IGN)** enter karein:", parse_mode="Markdown")
    return ASK_IGN

async def get_ign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['ign'] = update.message.text.strip()
    await update.message.reply_text("🆔 Apna **Free Fire UID** enter karein:", parse_mode="Markdown")
    return ASK_UID

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['ff_uid'] = update.message.text.strip()
    await update.message.reply_text("📱 Apna **WhatsApp / Contact Number** enter karein:", parse_mode="Markdown")
    return ASK_CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['contact'] = update.message.text.strip()
    await update.message.reply_text("📍 Apna **Ganv / Shahar / State Name** enter karein:", parse_mode="Markdown")
    return ASK_LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['location'] = update.message.text.strip()
    qr_url = get_upi_qr_url(UPI_ID, "z.ween2x Tournament", ENTRY_FEE)
    
    pay_msg = (
        f"💳 **Payment Verification (₹{ENTRY_FEE} Per Person)**\n\n"
        f"1. Niche diye gaye QR Code ko scan karein YA UPI ID par ₹{ENTRY_FEE} pay karein.\n"
        f"📌 **UPI ID:** `{UPI_ID}`\n\n"
        f"2. Payment complete karne ke baad **12-Digit UTR / Transaction Number** yahan type karke bhejin:"
    )
    
    try:
        await update.message.reply_photo(photo=qr_url, caption=pay_msg, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(pay_msg, parse_mode="Markdown")
        
    return ASK_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    utr = update.message.text.strip()
    
    if not (utr.isdigit() and len(utr) >= 8):
        await update.message.reply_text(
            "⚠️ **Galat UTR / Transaction Number!**\n\nKripya sahi 12-digit UTR number enter karein:",
            parse_mode="Markdown"
        )
        return ASK_PAYMENT
    
    context.user_data['utr'] = utr
    user = update.effective_user
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    if context.user_data.get('is_leader'):
        base_code = generate_random_code(5)
        cursor.execute("INSERT INTO teams (base_code, created_at) VALUES (?, ?)", 
                       (base_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        team_id = cursor.lastrowid
        context.user_data['team_id'] = team_id
        context.user_data['base_code'] = base_code
    
    role_char = context.user_data.get('role_char', 'A')
    team_id = context.user_data.get('team_id', 1)
    base_code = context.user_data.get('base_code', 'TEMP')
    temp_token = f"#zween2x-{team_id}-{role_char}-{base_code}"
    
    cursor.execute('''
        INSERT INTO players (team_id, role, user_id, full_name, ign, ff_uid, contact, location, utr, token, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
    ''', (
        team_id, role_char, user.id,
        context.user_data.get('full_name', ''), context.user_data.get('ign', ''),
        context.user_data.get('ff_uid', ''), context.user_data.get('contact', ''),
        context.user_data.get('location', ''), utr, temp_token,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    
    player_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    announcement_msg = (
        "⌛ **Registration Request Submitted!**\n\n"
        "Aapki details verification ke liye Admin ko bhej di gayi hain. Approval milte hi aapko Token receive ho jayega.\n\n"
        "📢 **Z.WEEN2X TOURNAMENT - IMPORTANT INSTRUCTIONS** 📢\n\n"
        "1️⃣ **Telegram Channel Join Karna Mandatory (Zaroori) Hai:**\n"
        "👉 Tournament ke saare Rules, Match Schedules, Room ID/Password, aur Daily Updates aapko humare official Telegram Channel par hi milenge.\n\n"
        "2️⃣ **Process Samjhne Ke Liye Video Dekhein:**\n"
        "👉 Agar aapko kisi bhi step me confusion hai, toh humare YouTube Channel par tutorial video dekh kar samajh sakte hain.\n\n"
        "3️⃣ **YouTube Channel Ko Subscribe Karein:**\n"
        "👉 Channel ko Subscribe karna na bhulein, kyunki aapke matches **YOUTUBE PAR LIVE STREAM** honge! 🎥🔥\n\n"
        f"📲 **Telegram Channel:** {TELEGRAM_CHANNEL_LINK}\n"
        f"🔴 **YouTube Channel:** {YOUTUBE_CHANNEL_LINK}\n\n"
        "All The Best! 🔥🎮\n— **z.ween2x Management**"
    )
    
    await update.message.reply_text(announcement_msg, parse_mode="Markdown")
    
    if ADMIN_ID:
        admin_msg = (
            f"🚨 **New Registration Verification Request**\n\n"
            f"👤 **Name:** {context.user_data.get('full_name')}\n"
            f"🎮 **IGN:** {context.user_data.get('ign')}\n"
            f"🆔 **FF UID:** {context.user_data.get('ff_uid')}\n"
            f"📱 **Contact:** {context.user_data.get('contact')}\n"
            f"📍 **Location:** {context.user_data.get('location')}\n"
            f"💳 **UTR:** `{utr}`\n"
            f"🏷️ **Role/Team:** Team #{team_id} ({role_char})\n"
            f"📱 **Telegram:** @{user.username or 'N/A'} (ID: `{user.id}`)"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Verify", callback_data=f"app_{player_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"rej_{player_id}")
            ]
        ]
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
        
    return ConversationHandler.END

async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, player_id = data.split("_")
    player_id = int(player_id)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, token, role, team_id FROM players WHERE id = ?", (player_id,))
    player = cursor.fetchone()
    
    if not player:
        await query.edit_message_text("❌ Entry Not Found!")
        conn.close()
        return

    user_id, token, role, team_id = player
    
    if action == "app":
        cursor.execute("UPDATE players SET status = 'APPROVED' WHERE id = ?", (player_id,))
        conn.commit()
        await query.edit_message_text(f"✅ Approved Player ID #{player_id}")
        
        msg = f"🎉 **Registration Confirmed!**\n\nAapka Unique Token Code:\n`{token}`\n\n"
        if role == 'A':
            msg += "👉 Ye Token apne **3 Teammates** ke sath share karein!"
        else:
            msg += f"👉 Aap Team #{team_id} me add ho chuke hain!"
            
        try:
            await context.bot.send_message(chat_id=user_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending msg: {e}")
            
    elif action == "rej":
        cursor.execute("UPDATE players SET status = 'REJECTED' WHERE id = ?", (player_id,))
        conn.commit()
        await query.edit_message_text(f"❌ Rejected Player ID #{player_id}")
        
        try:
            await context.bot.send_message(chat_id=user_id, text="❌ **Registration Rejected!**\nDetails verify nahi hui.", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending msg: {e}")

    conn.close()

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Process cancelled.")
    return ConversationHandler.END

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN Variable Missing!")

    init_db()
    
    # Start Web Server in background thread
    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(role_chosen, pattern="^role_")
        ],
        states={
            ASK_ROLE: [CallbackQueryHandler(role_chosen, pattern="^role_")],
            ASK_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_token)],
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ASK_IGN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ign)],
            ASK_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_uid)],
            ASK_CONTACT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contact)],
            ASK_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_location)],
            ASK_PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_payment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(admin_decision, pattern="^(app|rej)_"))

    logger.info("🚀 z.ween2x Bot Active...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
