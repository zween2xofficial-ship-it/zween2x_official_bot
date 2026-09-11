import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# Admin Telegram ID (Yahan userinfobot se nikali hui ID daalein)
ADMIN_CHAT_ID = 123456789 

# zween2x_official_bot Token
BOT_TOKEN = "8913279275:AAHkHR5t-50Jmwo0v5zenFNIGHx7TgUHjtE"

# Payment QR Code Image Link
QR_CODE_URL = "https://via.placeholder.com/300?text=Scan+QR+to+Pay+₹100"

(NAME, GAME_ID, WHATSAPP, MOBILE, CITY, VILLAGE, UPI_ID, UTR) = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Welcome to z.ween2x Tournament Registration! 🔥\n\nAapka Name kya hai?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Aapki Free Fire Game ID / UID kya hai?")
    return GAME_ID

async def get_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['game_id'] = update.message.text
    await update.message.reply_text("Aapka WhatsApp Number kya hai?")
    return WHATSAPP

async def get_whatsapp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['whatsapp'] = update.message.text
    await update.message.reply_text("Aapka Mobile Number kya hai?")
    return MOBILE

async def get_mobile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['mobile'] = update.message.text
    await update.message.reply_text("Aapka Shahar (City) konsa hai?")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text
    await update.message.reply_text("Aapka Ganv (Village/Town) konsa hai?")
    return VILLAGE

async def get_village(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['village'] = update.message.text
    await update.message.reply_text("Aapka Account Number ya UPI ID kya hai?")
    return UPI_ID

async def get_upi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['upi'] = update.message.text
    await update.message.reply_photo(
        photo=QR_CODE_URL,
        caption="Niche diye gaye QR Code par ₹100 Pay karein.\nPayment hone ke baad 12-Digit Transaction UTR Number yahan send karein."
    )
    return UTR

async def get_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = update.message.text
    context.user_data['utr'] = utr
    user_id = update.message.from_user.id
    
    details = (
        f"📩 **NEW REGISTRATION**\n\n"
        f"👤 **Name:** {context.user_data['name']}\n"
        f"🎮 **Game ID:** {context.user_data['game_id']}\n"
        f"📲 **WhatsApp:** {context.user_data['whatsapp']}\n"
        f"📞 **Mobile:** {context.user_data['mobile']}\n"
        f"🏙 **Shahar:** {context.user_data['city']}\n"
        f"🏡 **Ganv:** {context.user_data['village']}\n"
        f"💳 **UPI/Account:** {context.user_data['upi']}\n"
        f"🧾 **UTR:** {utr}\n"
        f"🆔 **Telegram ID:** {user_id}"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve Token", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=details, reply_markup=reply_markup, parse_mode="Markdown")
    await update.message.reply_text("Aapki details receive ho gayi hain! Payment verification ke baad aapko Token Number mil jayega.")
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id = query.data.split("_")
    user_id = int(user_id)

    if action == "approve":
        token_code = f"Z2X-{random.randint(1000, 9999)}"
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 **Registration Verified!**\n\nAapka Verified Token Number hai: `{token_code}`\nMatch details match se 15 min pehle milega.",
            parse_mode="Markdown"
        )
        await query.edit_message_text(text=f"{query.message.text}\n\n✅ **APPROVED - Token: {token_code}**")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Aapka Payment UTR verify nahi ho paya. Kripya correct UTR bhej kar dobara try karein."
        )
        await query.edit_message_text(text=f"{query.message.text}\n\n❌ **REJECTED**")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration canceled.")
    return ConversationHandler.END

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GAME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_game_id)],
            WHATSAPP: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_whatsapp)],
            MOBILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_mobile)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            VILLAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_village)],
            UPI_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_upi)],
            UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_utr)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))

    print("zween2x_official_bot is running...")
    app.run_polling()
