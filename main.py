import os
import logging
import pandas as pd
from datetime import datetime
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

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fetch Configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID_RAW = os.environ.get("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW and ADMIN_ID_RAW.isdigit() else None

EXCEL_FILE = "registrations.xlsx"
QR_IMAGE_PATH = "qr.jpg"

# Conversation States
ENTERING_NAME, ENTERING_UID, UPLOADING_PAYMENT = range(3)

def init_excel():
    if not os.path.exists(EXCEL_FILE):
        df = pd.DataFrame(columns=[
            "Timestamp", "User ID", "Username", "Player Name", 
            "FF UID", "Status", "Payment Screenshot ID"
        ])
        df.to_excel(EXCEL_FILE, index=False)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    welcome_text = (
        f"🔥 *Welcome to z.ween2x Official Registration Bot!* 🔥\n\n"
        f"Hello {user.first_name},\n"
        f"Register for upcoming tournaments quickly using this bot.\n\n"
        f"Click *Register Now* below to start."
    )
    keyboard = [[InlineKeyboardButton("📝 Register Now", callback_data="start_reg")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    
    return ConversationHandler.END

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "start_reg":
        await query.message.reply_text("1️⃣ Please enter your *In-Game Name (IGN)*:", parse_mode="Markdown")
        return ENTERING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['player_name'] = update.message.text
    await update.message.reply_text("2️⃣ Please enter your *Free Fire UID*:", parse_mode="Markdown")
    return ENTERING_UID

async def get_uid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['ff_uid'] = update.message.text
    
    payment_msg = (
        "3️⃣ *Payment Verification*\n\n"
        "Please scan the QR code, complete your entry fee payment, "
        "and upload the *Payment Screenshot* here."
    )
    
    if os.path.exists(QR_IMAGE_PATH):
        with open(QR_IMAGE_PATH, 'rb') as photo:
            await update.message.reply_photo(photo=photo, caption=payment_msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(payment_msg, parse_mode="Markdown")
        
    return UPLOADING_PAYMENT

async def get_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    photo_file = update.message.photo[-1].file_id
    
    init_excel()
    df = pd.read_excel(EXCEL_FILE)
    new_entry = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User ID": user.id,
        "Username": user.username or "N/A",
        "Player Name": context.user_data.get('player_name'),
        "FF UID": context.user_data.get('ff_uid'),
        "Status": "Pending Approval",
        "Payment Screenshot ID": photo_file
    }
    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)
    
    await update.message.reply_text(
        "✅ *Registration Submitted Successfully!*\n\n"
        "Your details have been recorded. Our team will verify your payment shortly.",
        parse_mode="Markdown"
    )
    
    if ADMIN_ID:
        admin_caption = (
            f"🚨 *New Registration Received*\n\n"
            f"👤 *Name:* {context.user_data.get('player_name')}\n"
            f"🆔 *FF UID:* {context.user_data.get('ff_uid')}\n"
            f"📱 *Telegram:* @{user.username} (ID: {user.id})"
        )
        try:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo_file, caption=admin_caption, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
        
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("❌ Registration process cancelled.")
    return ConversationHandler.END

def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set!")

    init_excel()
    
    application = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(button_click, pattern="^start_reg$")
        ],
        states={
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            ENTERING_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_uid)],
            UPLOADING_PAYMENT: [MessageHandler(filters.PHOTO, get_payment)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))

    logger.info("⚡ zween2x_official Bot is running live...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
