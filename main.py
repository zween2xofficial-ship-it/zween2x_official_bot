import os
import sqlite3
import requests
from flask import Flask, request

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Aapka Telegram Chat ID
ADMIN_CHAT_ID = "8866210749" 

app = Flask(__name__)

user_states = {}
user_data = {}

# Primary Payment UPI Details
PRIMARY_UPI_ID = "z.ween2x.official@okaxis"
PAYMENT_QR_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={PRIMARY_UPI_ID}%26pn=z.ween2x%20Official%26am=100%26cu=INR"

# --- DATABASE SETUP (Token Counter Ke Liye) ---
def init_db():
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('token_counter', 1)")
    conn.commit()
    conn.close()

def get_next_token():
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'token_counter'")
    current_val = cursor.fetchone()[0]
    
    next_val = current_val + 1
    cursor.execute("UPDATE config SET value = ? WHERE key = 'token_counter'", (next_val,))
    conn.commit()
    conn.close()
    
    return f"#zween2x-{current_val:02d}"

init_db()

# --- HELPER FUNCTIONS ---
def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Error: {e}")

def send_photo(chat_id, photo_url, caption):
    url = f"{TELEGRAM_API_URL}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": photo_url, "caption": caption, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Photo Error: {e}")

def edit_message_text(chat_id, message_id, text):
    url = f"{TELEGRAM_API_URL}/editMessageText"
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Edit Error: {e}")

# --- WEBHOOK ROUTE ---
@app.route('/', methods=['GET'])
def home():
    return "z.ween2x Tournament Verification Engine Active!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return "OK", 200

    # 1. BUTTON CLICK (CALLBACK QUERY)
    if "callback_query" in data:
        cb = data["callback_query"]
        cb_id = cb["id"]
        cb_data = cb["data"]
        admin_msg_id = cb["message"]["message_id"]

        action, target_chat_id = cb_data.split("_")

        if action == "approve":
            token_number = get_next_token()
            
            # Admin Chat Text Update
            edit_message_text(
                ADMIN_CHAT_ID, 
                admin_msg_id, 
                f"✅ *APPROVED & CONFIRMED!*\n🎟 Token Issued: `{token_number}`"
            )
            
            # Player Message
            player_msg = (
                "🎉 *Registration Verified & Confirmed!*\n\n"
                f"🎟 *Aapka Official Tournament Token:* `{token_number}`\n\n"
                "Kripya is Token number ko safe rakhein. Room ID & Password match ke waqt share kiya jayega.\n\n"
                "🏆 All the best - *z.ween2x Management*"
            )
            send_message(target_chat_id, player_msg)

        elif action == "reject":
            # Admin Chat Text Update
            edit_message_text(
                ADMIN_CHAT_ID, 
                admin_msg_id, 
                "❌ *REJECTED BY ADMIN*"
            )
            
            # Player Message
            player_msg = (
                "❌ *Registration Verification Failed!*\n\n"
                "Aapka payment / UTR verify nahi ho paya hai.\n"
                "• Ya toh aapne UTR galat dala hai, sahi UTR ke sath dobara `/register` karein.\n"
                "• Ya phir kisi bhi helpline ke liye direct Admin se contact karein: *@zween2xofficial*"
            )
            send_message(target_chat_id, player_msg)

        # Answer callback to stop loading spinner
        requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery", json={"callback_query_id": cb_id})
        return "OK", 200

    # 2. STANDARD MESSAGES
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if text == "/start":
            user_states[chat_id] = None
            user_data[chat_id] = {}
            msg = (
                "🏆 *Welcome to z.ween2x Free Fire Tournament!*\n\n"
                "Organized by: *z.ween2x Management*\n\n"
                "Commands:\n"
                "👉 /register - Start Registration\n"
                "👉 /rules - Complete Tournament Rulebook\n"
                "👉 /cancel - Cancel Registration"
            )
            send_message(chat_id, msg)

        elif text == "/rules":
            rules = (
                "📜 *z.ween2x OFFICIAL TOURNAMENT RULEBOOK* 📜\n\n"
                "📌 *1. REGISTRATION & TEAM SLOTS*\n"
                "• *Slot Completion Mandatory:* Match tabhi start hoga jab registration ke saare required slots (jaise 128 teams) poore fill ho jayenge.\n\n"
                "📌 *2. MATCH SCHEDULE & DAILY NOTIFICATION*\n"
                "• *Daily Schedule:* Subah *8:00 AM* se pehle Telegram / WhatsApp par daily schedule bhej diya jayega.\n\n"
                "📌 *3. TEAM PRESENCE & SUBSTITUTION RULES*\n"
                "• *Walkover Policy:* Late aane par direct Lose declare hoga.\n"
                "• *Minimum Requirement:* 1 player par bhi match khelna padega.\n"
                "• *Substitutes:* Minimum 2 original players hone zaroori hain, 2 bahar ke chalenge.\n\n"
                "📌 *4. STRICT ANTI-CHEAT & LEGAL WARNING*\n"
                "• *Zero Tolerance Policy:* Cheating / Hack karne par saari teams ki fee cheat karne wale ko deni padegi + Police FIR karwayi jayegi.\n\n"
                "📌 *5. QUALIFICATION & PLATFORM FEE*\n"
                "• Top 16 Teams ke beech *Best of 3* matches honge (2 wins needed).\n"
                "• Winner payout me se *23% Platform Charge* deduct hoga.\n\n"
                "👉 *Contact Support:* @zween2xofficial"
            )
            send_message(chat_id, rules)

        elif text == "/register":
            user_states[chat_id] = "STEP_NAME"
            user_data[chat_id] = {}
            send_message(chat_id, "📝 *Step 1/5:* Apna *Full Name* likhkar bhejein:")

        elif text == "/cancel":
            user_states[chat_id] = None
            user_data[chat_id] = {}
            send_message(chat_id, "❌ Registration cancel ho gaya. Restart karne ke liye /register bhejein.")

        else:
            state = user_states.get(chat_id)

            if state == "STEP_NAME":
                user_data[chat_id]["name"] = text
                user_states[chat_id] = "STEP_UID"
                send_message(chat_id, "🎮 *Step 2/5:* Apna *Free Fire Game UID & In-Game Name (IGN)* bhejein:")

            elif state == "STEP_UID":
                user_data[chat_id]["uid"] = text
                user_states[chat_id] = "STEP_TG"
                send_message(chat_id, "✈️ *Step 3/5:* Apna *Telegram Username* ya Mobile Number bhejein:")

            elif state == "STEP_TG":
                user_data[chat_id]["telegram"] = text
                user_states[chat_id] = "STEP_PHONE"
                send_message(chat_id, "📞 *Step 4/5:* Apna active *WhatsApp / Phone Number* bhejein:")

            elif state == "STEP_PHONE":
                user_data[chat_id]["phone"] = text
                user_states[chat_id] = "STEP_LOCATION"
                send_message(chat_id, "📍 *Step 5/5:* Apne *Gaon / Shahar ka Naam aur State* bhejein:")

            elif state == "STEP_LOCATION":
                user_data[chat_id]["location"] = text
                user_states[chat_id] = "CHECK_DETAILS"

                summary = (
                    "🔍 *Kripya Apni Sabhi Details Check Kar Lein:*\n\n"
                    f"👤 *Name:* {user_data[chat_id]['name']}\n"
                    f"🎮 *Game UID & IGN:* {user_data[chat_id]['uid']}\n"
                    f"✈️ *Telegram:* {user_data[chat_id]['telegram']}\n"
                    f"📞 *WhatsApp:* {user_data[chat_id]['phone']}\n"
                    f"📍 *Location:* {user_data[chat_id]['location']}\n\n"
                    "------------------------------------\n"
                    "✅ Agar sab sahi hai toh payment ke liye niche **PAY** type karke bhejein."
                )
                send_message(chat_id, summary)

            elif state == "CHECK_DETAILS" and text.upper() == "PAY":
                user_states[chat_id] = "STEP_UTR"
                caption = (
                    "💰 *Registration Fee Payment (₹100)*\n\n"
                    "📷 *1. QR Code:* Scan karke ₹100 pay karein.\n"
                    f"🆔 *2. UPI ID:* `{PRIMARY_UPI_ID}`\n\n"
                    "Payment hone ke baad, apna **12-Digit UTR / Transaction ID** yahan type karke bhejein:"
                )
                send_photo(chat_id, PAYMENT_QR_URL, caption)

            elif state == "STEP_UTR":
                user_data[chat_id]["utr"] = text
                user_states[chat_id] = None

                # Inline Action Buttons For Admin
                admin_buttons = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Approve (Sahi Hai)", "callback_data": f"approve_{chat_id}"},
                            {"text": "❌ Reject (Galat Hai)", "callback_data": f"reject_{chat_id}"}
                        ]
                    ]
                }

                admin_report = (
                    "📥 *NEW REGISTRATION FOR VERIFICATION*\n\n"
                    f"👤 *Name:* {user_data[chat_id].get('name')}\n"
                    f"🎮 *Game UID & IGN:* {user_data[chat_id].get('uid')}\n"
                    f"✈️ *Telegram:* {user_data[chat_id].get('telegram')}\n"
                    f"📞 *WhatsApp:* {user_data[chat_id].get('phone')}\n"
                    f"📍 *Location:* {user_data[chat_id].get('location')}\n"
                    f"🧾 *Submitted UTR:* `{text}`\n\n"
                    "❓ *Kya yeh UTR sahi hai? Niche button daba kar action lein:*"
                )
                send_message(ADMIN_CHAT_ID, admin_report, reply_markup=admin_buttons)

                player_msg = (
                    "⏳ *Registration Details Submitted!*\n\n"
                    "Aapki details verification ke liye bhej di gayi hain. Admin check karke jaldi hi Token issue kar dega."
                )
                send_message(chat_id, player_msg)

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
