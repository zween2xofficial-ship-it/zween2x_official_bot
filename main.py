import os
import sqlite3
import random
import string
import datetime
import schedule
import time
import asyncio
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
import pandas as pd

# Global Config
BOT_TOKEN = "8913279275:AAEcrpfAp0tSd1zz2VfrcJsmo402LgSSwR4"
ADMIN_CHAT_ID = 8866210749
UPI_ID = "z.ween2x.official@okaxis"
MAX_TEAMS = 128

# Conversation States
(
    TEAM_CHOICE,
    LEADER_TOKEN_INPUT,
    NAME,
    GAME_ID,
    MOBILE,
    TELEGRAM_ID,
    VILLAGE,
    CITY,
    STATE,
    UTR,
) = range(10)

def init_db():
    conn = sqlite3.connect("zween2x.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_telegram_id INTEGER,
            team_id INTEGER,
            role TEXT,
            token TEXT,
            name TEXT,
            game_id TEXT,
            mobile TEXT,
            tg_handle TEXT,
            village TEXT,
            city TEXT,
            state TEXT,
            utr TEXT,
            status TEXT,
            registered_at TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_secret TEXT,
            member_count INTEGER DEFAULT 0,
            is_locked INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1. Create New Team (Leader)", callback_data="new_team")],
        [InlineKeyboardButton("2. Join Existing Team", callback_data="join_team")],
        [InlineKeyboardButton("💬 Contact Support / Help", url="https://t.me/zween2xofficial")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to zween2x_official Tournament Registration System!\n\n"
        "Kripya chunye aap Nayi Team create kar rahe hain ya kisi ki Team join kar rahe hain:\n\n"
        "ℹ️ Kisi bhi samasya ke liye contact karein: @zween2xofficial",
        reply_markup=reply_markup
    )
    return TEAM_CHOICE

async def team_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    conn = sqlite3.connect("zween2x.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM teams")
    team_count = cursor.fetchone()[0]
    conn.close()

    if query.data == "new_team":
        if team_count >= MAX_TEAMS:
            await query.edit_message_text("Maaf kijiye, 128 Teams ki limit poori ho chuki hai!")
            return ConversationHandler.END
        context.user_data['role'] = 'Leader'
        await query.edit_message_text("Aap Team Leader hain. Kripya apna Name / Game ID Name dalein:")
        return NAME
    elif query.data == "join_team":
        await query.edit_message_text("Kripya apne Team Leader ka Unique Token dalein (e.g., zween2x-00001-qwertyuiop-A):")
        return LEADER_TOKEN_INPUT

async def leader_token_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    
    try:
        parts = token.split("-")
        if len(parts) != 4 or parts[0] != "zween2x":
            raise ValueError
        team_num = int(parts[1])
        base_secret = parts[2]
    except Exception:
        await update.message.reply_text("Galat Token Format! Kripya sahi token dobara enter karein:")
        return LEADER_TOKEN_INPUT

    conn = sqlite3.connect("zween2x.db")
    cursor = conn.cursor()
    cursor.execute("SELECT team_id, member_count, is_locked FROM teams WHERE team_id = ? AND base_secret = ?", (team_num, base_secret))
    team = cursor.fetchone()
    
    if not team:
        conn.close()
        await update.message.reply_text("Ye Token exist nahi karta! Sahi Token dobara try karein:")
        return LEADER_TOKEN_INPUT
    
    team_id, member_count, is_locked = team
    if is_locked or member_count >= 4:
        conn.close()
        await update.message.reply_text("Ye Team poori ho chuki hai (4/4 Lock)! Aap join nahi kar sakte.")
        return ConversationHandler.END

    context.user_data['role'] = 'Member'
    context.user_data['team_id'] = team_id
    context.user_data['base_secret'] = base_secret
    context.user_data['member_seq'] = member_count + 1
    conn.close()

    await update.message.reply_text("Token Verified! Kripya apna Name / Game ID Name dalein:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Apna Game ID number dalein:")
    return GAME_ID

async def get_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['game_id'] = update.message.text
    await update.message.reply_text("Apna Mobile / WhatsApp Number dalein:")
    return MOBILE

async def get_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mobile'] = update.message.text
    await update.message.reply_text("Apna Telegram Username ya Telegram Number dalein:")
    return TELEGRAM_ID

async def get_tg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['tg_handle'] = update.message.text
    await update.message.reply_text("Apne Ganv (Village) ka naam dalein:")
    return VILLAGE

async def get_village(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['village'] = update.message.text
    await update.message.reply_text("Apne Shahar (City) ka naam dalein:")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text
    await update.message.reply_text("Apne Pradesh (State) ka naam dalein:")
    return STATE

async def get_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['state'] = update.message.text
    
    qr_path = "qr.jpg"
    payment_msg = (
        f"Registration Fee ₹100 niche diye gaye QR code ko scan karke ya UPI ID par bhejein:\n\n"
        f"<b>UPI ID:</b> <code>{UPI_ID}</code>\n\n"
        f"Payment karne ke baad uska UTR / Transaction ID yahan type karke bhejein:"
    )
    
    if os.path.exists(qr_path):
        await update.message.reply_photo(photo=open(qr_path, 'rb'), caption=payment_msg, parse_mode="HTML")
    else:
        await update.message.reply_text(payment_msg, parse_mode="HTML")
        
    return UTR

async def get_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = update.message.text.strip()
    if len(utr) < 6:
        await update.message.reply_text("Galat UTR Number! Kripya sahi UTR Number enter karein:")
        return UTR

    context.user_data['utr'] = utr
    user_id = update.effective_user.id
    reg_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect("zween2x.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_telegram_id, role, name, game_id, mobile, tg_handle, village, city, state, utr, status, registered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
    ''', (user_id, context.user_data['role'], context.user_data['name'], context.user_data['game_id'], 
          context.user_data['mobile'], context.user_data['tg_handle'], context.user_data['village'], 
          context.user_data['city'], context.user_data['state'], utr, reg_time))
    
    db_id = cursor.lastrowid
    
    if context.user_data['role'] == 'Member':
        cursor.execute("UPDATE users SET team_id = ? WHERE id = ?", (context.user_data['team_id'], db_id))
        
    conn.commit()
    conn.close()

    admin_msg = (
        f"🚨 <b>NEW REGISTRATION REQUEST</b> 🚨\n\n"
        f"<b>Role:</b> {context.user_data['role']}\n"
        f"<b>Name:</b> {context.user_data['name']}\n"
        f"<b>Game ID:</b> {context.user_data['game_id']}\n"
        f"<b>Mobile:</b> {context.user_data['mobile']}\n"
        f"<b>Telegram:</b> {context.user_data['tg_handle']}\n"
        f"<b>Village:</b> {context.user_data['village']}\n"
        f"<b>City:</b> {context.user_data['city']}\n"
        f"<b>State:</b> {context.user_data['state']}\n"
        f"<b>UTR:</b> <code>{utr}</code>\n"
        f"<b>Time:</b> {reg_time}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"app_{db_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"rej_{db_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg, reply_markup=reply_markup, parse_mode="HTML")
    await update.message.reply_text("Aapki details verification ke liye bhej di gayi hain. Admin approval ke baad aapko Token mil jayega.")
    return ConversationHandler.END

async def admin_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    action, db_id = data.split("_")
    db_id = int(db_id)

    conn = sqlite3.connect("zween2x.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_telegram_id, role, team_id, name FROM users WHERE id = ?", (db_id,))
    row = cursor.fetchone()
    
    if not row:
        await query.edit_message_text("User record nahi mila.")
        conn.close()
        return

    user_tg_id, role, team_id, name = row

    if action == "rej":
        cursor.execute("UPDATE users SET status = 'REJECTED' WHERE id = ?", (db_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"❌ User {name} ki Request REJECT kar di gayi hai.")
        await context.bot.send_message(chat_id=user_tg_id, text="Aapki details ya UTR galat paya gaya hai. Registration Reject kar diya gaya hai.")
        return

    if action == "app":
        if role == 'Leader':
            base_secret = generate_random_string(10)
            cursor.execute("INSERT INTO teams (base_secret, member_count) VALUES (?, 1)", (base_secret,))
            new_team_id = cursor.lastrowid
            token_str = f"zween2x-{str(new_team_id).zfill(5)}-{base_secret}-A"
            
            cursor.execute("UPDATE users SET status = 'APPROVED', token = ?, team_id = ? WHERE id = ?", (token_str, new_team_id, db_id))
            conn.commit()
            conn.close()
            
            await query.edit_message_text(f"✅ Leader Approved!\nToken Generated: <code>{token_str}</code>", parse_mode="HTML")
            await context.bot.send_message(
                chat_id=user_tg_id, 
                text=f"🎉 Registration Successful!\n\nAapki Team ka Leader Token hai:\n<code>{token_str}</code>\n\nIs token ko baaki 3 members ke sath share karein.", 
                parse_mode="HTML"
            )

        elif role == 'Member':
            cursor.execute("SELECT base_secret, member_count FROM teams WHERE team_id = ?", (team_id,))
            t_data = cursor.fetchone()
            if not t_data:
                conn.close()
                await query.edit_message_text("Team data lost.")
                return

            base_secret, current_count = t_data
            new_count = current_count + 1
            suffix = chr(64 + new_count)
            token_str = f"zween2x-{str(team_id).zfill(5)}-{base_secret}-{suffix}"

            is_locked = 1 if new_count >= 4 else 0
            cursor.execute("UPDATE teams SET member_count = ?, is_locked = ? WHERE team_id = ?", (new_count, is_locked, team_id))
            cursor.execute("UPDATE users SET status = 'APPROVED', token = ? WHERE id = ?", (token_str, db_id))
            conn.commit()
            conn.close()

            await query.edit_message_text(f"✅ Member Approved ({suffix})!\nToken: <code>{token_str}</code>", parse_mode="HTML")
            await context.bot.send_message(
                chat_id=user_tg_id, 
                text=f"🎉 Registration Successful!\n\nAapka Member Token hai:\n<code>{token_str}</code>\n\nTeam Member count: {new_count}/4", 
                parse_mode="HTML"
            )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration process radd kar diya gaya hai.")
    return ConversationHandler.END

async def send_daily_report(app):
    conn = sqlite3.connect("zween2x.db")
    df = pd.read_sql_query("SELECT * FROM users WHERE status = 'APPROVED'", conn)
    conn.close()

    filename = f"zween2x_Report_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"
    df.to_excel(filename, index=False)

    with open(filename, 'rb') as f:
        await app.bot.send_document(
            chat_id=ADMIN_CHAT_ID,
            document=f,
            caption=f"📊 Daily Registration Report ({datetime.datetime.now().strftime('%d-%b-%Y %I:%M %p')})\nTotal Approved Players: {len(df)}"
        )
    if os.path.exists(filename):
        os.remove(filename)

def schedule_runner(app, loop):
    schedule.every().day.at("20:00").do(lambda: asyncio.run_coroutine_threadsafe(send_daily_report(app), loop))
    while True:
        schedule.run_pending()
        time.sleep(30)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TEAM_CHOICE: [CallbackQueryHandler(team_choice)],
            LEADER_TOKEN_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, leader_token_input)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GAME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_game_id)],
            MOBILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mobile)],
            TELEGRAM_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_tg_id)],
            VILLAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_village)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_state)],
            UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_utr)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^(app|rej)_"))

    import threading
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=schedule_runner, args=(app, loop), daemon=True)
    t.start()

    print("⚡ zween2x_official Bot is running live...")
    app.run_polling()

if __name__ == '__main__':
    main()