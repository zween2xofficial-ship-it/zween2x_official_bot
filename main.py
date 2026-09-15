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

# -------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_RAW = os.environ.get("ADMIN_ID", "8866210749")
try:
    ADMIN_ID = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 8866210749

UPI_ID = "z.ween2x.official@okaxis"
ENTRY_FEE = 100

TELEGRAM_CHANNEL_LINK = "https://t.me/+W0nd-axUCgdiZWZl"
YOUTUBE_CHANNEL_LINK = "https://youtube.com/@zween2x?si=NlZ7_M-fJ-Dg3B0T"

ASK_ROLE, ASK_TOKEN, ASK_NAME, ASK_IGN, ASK_UID, ASK_CONTACT, ASK_LOCATION, ASK_PAYMENT = range(8)
DB_FILE = "tournament.db"

# -------------------------------------------------------------
# FLASK WEB SERVER (For Render Keep-Alive)
# -------------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "z.ween2x Bot Running 24/7"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# DATABASE INIT
# -------------------------------------------------------------
def init_db():
    try:
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
                token TEXT,
                status TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Init Error: {e}")

def generate_random_code(length=5):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def get_upi_qr_url(upi_id, name, amount):
    params = {"pa": upi_id, "pn": name, "am": str(amount), "cu": "INR"}
    upi_uri = f"upi://pay?{urllib.parse.urlencode(params)}"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_uri)}"

# -------------------------------------------------------------
# HANDLERS
# -------------------------------------------------------------
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
    token_input = update.message.text.strip() if update.message and update.message.text else ""
    
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT team_id, role FROM players WHERE token = ?", (token_input,))
        leader_entry = cursor.fetchone()
        
        if not leader_entry:
            conn.close()
            await update.message.reply_text("⚠️ **Invalid Token Code!** Sahi token dobara enter karein:", parse_mode="Markdown")
            return ASK_TOKEN
        
        team_id = leader_entry[0]
        cursor.execute("SELECT COUNT(*) FROM players WHERE team_id = ?", (team_id,))
        player_count = cursor.fetchone()[0]
        
        if player_count >= 4:
            conn.close()
            await update.message.reply_text("❌ **Team Full!** Is team me 4 players poore ho chuke hain.", parse_mode="Markdown")
            return ConversationHandler.END
        
        role_map = {1: 'B', 2: 'C', 3: 'D'}
        context.user_data['team_id'] = team_id
        context.user_data['role_char'] = role_map.get(player_count, 'D')
        conn.close()
    except Exception as e:
        logger.error(f"Token Processing Error: {e}")

    await update.message.reply_text("✅ Token Valid! Ab apna **Full Name** enter karein:", parse_mode="Markdown")
    return ASK_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['full_name'] = update.message.text.strip() if update.message and update.message.text else "N/A"
    await update.message.reply_text("🎮 Apna **In-Game Name (IGN)** enter karein:", parse_mode="Markdown")
    return ASK_IGN

async def get_ign(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['ign'] = update.message.text.strip() if update.message and update.message.text else "N/A"
    await update.message.reply_text("🆔 Apna **Free Fire UID** enter karein:", parse_mode="Markdown")
    return ASK_UID

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['ff_uid'] = update.message.text.strip() if update.message and update.message.text else "N/A"
    await update.message.reply_text("📱 Apna **WhatsApp / Contact Number** enter karein:", parse_mode="Markdown")
    return ASK_CONTACT

async def get_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['contact'] = update.message.text.strip() if update.message and update.message.text else "N/A"
    await update.message.reply_text("📍 Apna **Ganv / Shahar / State Name** enter karein:", parse_mode="Markdown")
    return ASK_LOCATION

async def get_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['location'] = update.message.text.strip() if update.message and update.message.text else "N/A"
    qr_url = get_upi_qr_url(UPI_ID, "z.ween2x Tournament", ENTRY_FEE)
    
    pay_msg = (
        f"💳 **Payment Verification (₹{ENTRY_FEE} Per Person)**\n\n"
        f"1. Niche diye gaye QR Code ko scan karein YA UPI ID par ₹{ENTRY_FEE} pay karein.\n"
        f"📌 **UPI ID:** `{UPI_ID}`\n\n"
        f"2. Payment complete karne ke baad **12-Digit UTR / Transaction Number** yahan type karke bhejin:"
    )
    
    try:
        await update.message.reply_photo(photo=qr_url, caption=pay_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending photo QR: {e}")
        await update.message.reply_text(pay_msg, parse_mode="Markdown")
        
    return ASK_PAYMENT

async def process_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    utr_text = update.message.text.strip() if update.message and update.message.text else "N/A"
    user = update.effective_user

    announcement_msg = (
        "⌛ **Registration Request Submitted!**\n\n"
        "Aapki details verification ke liye Admin ko bhej di gayi hain. Approval milte hi aapko Token receive ho jayega.\n\n"
        "📢 **Z.WEEN2X TOURNAMENT - IMPORTANT INSTRUCTIONS** 📢\n\n"
        "1️⃣ **Telegram Channel Join Karna Mandatory Hai:**\n"
        "👉 Rules, Match Schedules, Room ID/Password official Telegram Channel par hi milenge.\n\n"
        "2️⃣ **YouTube Channel Ko Subscribe Karein:**\n"
        "👉 Aapke matches **YOUTUBE PAR LIVE STREAM** honge! 🎥🔥\n\n"
        f"📲 **Telegram Channel:** {TELEGRAM_CHANNEL_LINK}\n"
        f"🔴 **YouTube Channel:** {YOUTUBE_CHANNEL_LINK}\n\n"
        "All The Best! 🔥🎮\n— **z.ween2x Management**"
    )
    
    try:
        await update.message.reply_text(announcement_msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error sending user reply: {e}")

    player_id = random.randint(10000, 99999)
    team_id = 1
    base_code = "TEMP"
    role_char = context.user_data.get('role_char', 'A')

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        if context.user_data.get('is_leader', True):
            base_code = generate_random_code(5)
            cursor.execute("INSERT INTO teams (base_code, created_at) VALUES (?, ?)", 
                           (base_code, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            team_id = cursor.lastrowid
            context.user_data['team_id'] = team_id
            context.user_data['base_code'] = base_code
        else:
            team_id = context.user_data.get('team_id', 1)
            cursor.execute("SELECT base_code FROM teams WHERE team_id = ?", (team_id,))
            res = cursor.fetchone()
            base_code = res[0] if res else 'TEMP'

        temp_token = f"#zween2x-{team_id}-{role_char}-{base_code}"

        cursor.execute('''
            INSERT INTO players (team_id, role, user_id, full_name, ign, ff_uid, contact, location, utr, token, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
        ''', (
            team_id, role_char, user.id,
            context.user_data.get('full_name', 'N/A'),
            context.user_data.get('ign', 'N/A'),
            context.user_data.get('ff_uid', 'N/A'),
            context.user_data.get('contact', 'N/A'),
            context.user_data.get('location', 'N/A'),
            utr_text, temp_token,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"DB Insert Error: {e}")

    if ADMIN_ID:
        admin_msg = (
            f"🚨 **New Registration Request**\n\n"
            f"👤 **Name:** {context.user_data.get('full_name', 'N/A')}\n"
            f"🎮 **IGN:** {context.user_data.get('ign', 'N/A')}\n"
            f"🆔 **FF UID:** {context.user_data.get('ff_uid', 'N/A')}\n"
            f"📱 **Contact:** {context.user_data.get('contact', 'N/A')}\n"
            f"📍 **Location:** {context.user_data.get('location', 'N/A')}\n"
            f"💳 **UTR:** `{utr_text}`\n"
            f"🏷️ **Team ID:** #{team_id}\n"
            f"📱 **Telegram:** @{user.username or 'N/A'} (ID: `{user.id}`)"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Verify", callback_data=f"app_{player_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"rej_{player_id}")
            ]
        ]
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID, 
                text=admin_msg, 
                parse_mode="Markdown", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Admin Notification Error: {e}")

    return ConversationHandler.END

# -------------------------------------------------------------
# ADMIN BUTTON CALLBACK HANDLER (VERIFY / REJECT)
# -------------------------------------------------------------
async def admin_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if not (data.startswith("app_") or data.startswith("rej_")):
        return

    action, player_id_str = data.split("_")
    player_id = int(player_id_str)

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, token, full_name, role FROM players WHERE id = ?", (player_id,))
        player = cursor.fetchone()

        if not player:
            await query.edit_message_text(f"❌ Record not found for Player ID #{player_id}")
            conn.close()
            return

        user_id, token, full_name, role = player

        if action == "app":
            cursor.execute("UPDATE players SET status = 'APPROVED' WHERE id = ?", (player_id,))
            conn.commit()
            
            # Update Admin Message
            await query.edit_message_text(
                f"✅ **REGISTRATION APPROVED**\n\n"
                f"👤 **Player:** {full_name}\n"
                f"🔑 **Token:** `{token}`\n"
                f"STATUS: VERIFIED"
            )

            # Send Notification & Token to User
            user_msg = (
                f"🎉 **CONGRATULATIONS! Registration Approved!** 🎉\n\n"
                f"Aapka payment verify ho gaya hai. Aapka Registration Token niche diya gaya hai:\n\n"
                f"🔑 **Your Token:** `{token}`\n\n"
                f"*(Note: Agar aap Team Leader hain, to ye Token apni team members ke sath share karein taaki wo register kar sakein.)*\n\n"
                f"📢 Telegram Channel: {TELEGRAM_CHANNEL_LINK}\n"
                f"🔴 YouTube Live: {YOUTUBE_CHANNEL_LINK}"
            )
            try:
                await context.bot.send_message(chat_id=user_id, text=user_msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to send approval message to user: {e}")

        elif action == "rej":
            cursor.execute("UPDATE players SET status = 'REJECTED' WHERE id = ?", (player_id,))
            conn.commit()

            # Update Admin Message
            await query.edit_message_text(
                f"❌ **REGISTRATION REJECTED**\n\n"
                f"👤 **Player:** {full_name}\n"
                f"STATUS: REJECTED"
            )

            # Send Rejection Notice to User
            user_msg = (
                f"❌ **Registration Rejected!**\n\n"
                f"Aapka UTR Verification fail ho gaya hai. Kripya sahi payment screenshot aur UTR ke sath dobara register karein."
            )
            try:
                await context.bot.send_message(chat_id=user_id, text=user_msg, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to send rejection message to user: {e}")

        conn.close()
    except Exception as e:
        logger.error(f"Error processing admin decision: {e}")
        await query.edit_message_text(f"⚠️ Error processing request: {str(e)}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Registration process cancelled. Start again with /start.")
    return ConversationHandler.END

# -------------------------------------------------------------
# MAIN APP EXECUTION
# -------------------------------------------------------------
def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable missing!")
        return

    init_db()
    threading.Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(role_chosen, pattern="^role_")
        ],
        states={
            ASK_ROLE: [CallbackQueryHandler(role_chosen, pattern="^role_")],
            ASK_TOKEN: [MessageHandler(filters.ALL & ~filters.COMMAND, process_token)],
            ASK_NAME: [MessageHandler(filters.ALL & ~filters.COMMAND, get_name)],
            ASK_IGN: [MessageHandler(filters.ALL & ~filters.COMMAND, get_ign)],
            ASK_UID: [MessageHandler(filters.ALL & ~filters.COMMAND, get_uid)],
            ASK_CONTACT: [MessageHandler(filters.ALL & ~filters.COMMAND, get_contact)],
            ASK_LOCATION: [MessageHandler(filters.ALL & ~filters.COMMAND, get_location)],
            ASK_PAYMENT: [MessageHandler(filters.ALL & ~filters.COMMAND, process_payment)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        per_user=True,
        per_chat=True,
        per_message=False,
        allow_reentry=True
    )

    # Add Handlers
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(admin_button_click, pattern="^(app_|rej_)"))

    logger.info("🚀 z.ween2x Bot Started Successfully!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
