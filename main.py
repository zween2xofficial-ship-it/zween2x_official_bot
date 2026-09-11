import os
import sqlite3
import requests
from flask import Flask, request

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

ADMIN_CHAT_ID = "8866210749" 

app = Flask(__name__)

user_states = {}
user_data = {}

PRIMARY_UPI_ID = "z.ween2x.official@okaxis"
PAYMENT_QR_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={PRIMARY_UPI_ID}%26pn=z.ween2x%20Official%26am=100%26cu=INR"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('team_counter', 1)")
    
    # Store team member counts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS team_slots (
            team_num INTEGER PRIMARY KEY,
            members_count INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def get_new_team_token():
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'team_counter'")
    current_team = cursor.fetchone()[0]
    
    next_team = current_team + 1
    cursor.execute("UPDATE config SET value = ? WHERE key = 'team_counter'", (next_team,))
    cursor.execute("INSERT INTO team_slots (team_num, members_count) VALUES (?, 1)", (current_team,))
    
    conn.commit()
    conn.close()
    
    return f"#zween2x-{current_team:02d}-team-A"

def get_join_team_token(team_input):
    # Parse team number from user input like "#zween2x-01-team-A" or "01" or "1"
    try:
        clean_str = team_input.lower().replace("#zween2x-", "").split("-")[0]
        team_num = int(clean_str)
    except:
        return None, "Invalid Team Format!"

    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("SELECT members_count FROM team_slots WHERE team_num = ?", (team_num,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None, "Yeh Team Number exist nahi karta!"

    count = row[0]
    if count >= 4:
        conn.close()
        return None, "Yeh Team pehle se FULL hai (4/4 Players Joined)!"

    # Mapping count to letters: 1 -> B, 2 -> C, 3 -> D
    letter_map = {1: "B", 2: "C", 3: "D"}
    assigned_letter = letter_map[count]
    
    # Increment count for future approval
    new_count = count + 1
    cursor.execute("UPDATE team_slots SET members_count = ? WHERE team_num = ?", (new_count, team_num))
    
    conn.commit()
    conn.close()

    return f"#zween2x-{team_num:02d}-team-{assigned_letter}", "SUCCESS"

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
    return "z.ween2x Multi-Player Team Engine Active!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return "OK", 200

    # 1. BUTTON CLICK HANDLER
    if "callback_query" in data:
        cb = data["callback_query"]
        cb_id = cb["id"]
        cb_data = cb["data"]
        chat_id = cb["message"]["chat"]["id"]
        admin_msg_id = cb["message"]["message_id"]

        # Selection: New Team vs Join Team
        if cb_data in ["choice_new_team", "choice_join_team"]:
            if cb_data == "choice_new_team":
                user_data[chat_id]["reg_type"] = "NEW"
                user_states[chat_id] = "STEP_NAME"
                send_message(chat_id, "🆕 *New Team Creation Selected!*\n\n📝 *Step 1/5:* Apna *Full Name* likhkar bhejein:")
            else:
                user_data[chat_id]["reg_type"] = "JOIN"
                user_states[chat_id] = "STEP_JOIN_CODE"
                send_message(chat_id, "🔗 *Join Existing Team Selected!*\n\nLider ka Team Token Number type karke bhejein (Jaise: `#zween2x-01-team-A` ya `01`):")

        # Admin Approval Actions
        elif cb_data.startswith("approve_") or cb_data.startswith("reject_"):
            action, target_chat_id = cb_data.split("_")
            target_chat_id = int(target_chat_id)

            if action == "approve":
                reg_type = user_data.get(target_chat_id, {}).get("reg_type", "NEW")
                
                if reg_type == "NEW":
                    token_number = get_new_team_token()
                else:
                    join_code = user_data.get(target_chat_id, {}).get("join_code", "")
                    token_number, status = get_join_team_token(join_code)
                    if not token_number:
                        token_number = get_new_team_token() # Fallback if error

                edit_message_text(
                    ADMIN_CHAT_ID, 
                    admin_msg_id, 
                    f"✅ *APPROVED & CONFIRMED!*\n🎟 Token Issued: `{token_number}`"
                )
                
                player_msg = (
                    "🎉 *Registration Verified & Confirmed!*\n\n"
                    f"🎟 *Aapka Official Tournament Token:* `{token_number}`\n\n"
                    "📌 *Aapki Team ke baaki members is token number se join kar sakte hain!*\n\n"
                    "🏆 All the best - *z.ween2x Management*"
                )
                send_message(target_chat_id, player_msg)

            elif action == "reject":
                edit_message_text(
                    ADMIN_CHAT_ID, 
                    admin_msg_id, 
                    "❌ *REJECTED BY ADMIN*"
                )
                
                player_msg = (
                    "❌ *Registration Verification Failed!*\n\n"
                    "Aapka payment / UTR verify nahi ho paya hai.\n"
                    "• Ya toh aapne UTR galat dala hai, sahi UTR ke sath dobara `/register` karein.\n"
                    "• Ya kisi bhi helpline ke liye direct Admin se contact karein: *@zween2xofficial*"
                )
                send_message(target_chat_id, player_msg)

        requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery", json={"callback_query_id": cb_id})
        return "OK", 200

    # 2. MESSAGES HANDLER
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

        elif text == "/register":
            user_states[chat_id] = "CHOICE_MODE"
            user_data[chat_id] = {}

            choice_buttons = {
                "inline_keyboard": [
                    [
                        {"text": "➕ New Team Banayein", "callback_data": "choice_new_team"},
                        {"text": "🔗 Team Me Join Ho", "callback_data": "choice_join_team"}
                    ]
                ]
            }
            send_message(chat_id, "❓ *Aap New Team banana chahte hain ya pehle se bani Team me Join hona chahte hain?*", reply_markup=choice_buttons)

        elif text == "/cancel":
            user_states[chat_id] = None
            user_data[chat_id] = {}
            send_message(chat_id, "❌ Registration cancel ho gaya. Restart karne ke liye /register bhejein.")

        else:
            state = user_states.get(chat_id)

            if state == "STEP_JOIN_CODE":
                user_data[chat_id]["join_code"] = text
                user_states[chat_id] = "STEP_NAME"
                send_message(chat_id, "📝 *Step 1/5:* Apna *Full Name* likhkar bhejein:")

            elif state == "STEP_NAME":
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

                reg_mode = "🆕 New Team" if user_data[chat_id].get("reg_type") == "NEW" else f"🔗 Joining Team ({user_data[chat_id].get('join_code')})"

                summary = (
                    "🔍 *Kripya Apni Sabhi Details Check Kar Lein:*\n\n"
                    f"📌 *Type:* {reg_mode}\n"
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

                admin_buttons = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Approve (Sahi Hai)", "callback_data": f"approve_{chat_id}"},
                            {"text": "❌ Reject (Galat Hai)", "callback_data": f"reject_{chat_id}"}
                        ]
                    ]
                }

                reg_type_str = "NEW TEAM LEADER" if user_data[chat_id].get("reg_type") == "NEW" else f"MEMBER JOINING ({user_data[chat_id].get('join_code')})"

                admin_report = (
                    "📥 *NEW TOURNAMENT REGISTRATION*\n\n"
                    f"🏷 *Category:* `{reg_type_str}`\n"
                    f"👤 *Name:* {user_data[chat_id].get('name')}\n"
                    f"🎮 *Game UID & IGN:* {user_data[chat_id].get('uid')}\n"
                    f"✈️ *Telegram:* {user_data[chat_id].get('telegram')}\n"
                    f"📞 *WhatsApp:* {user_data[chat_id].get('phone')}\n"
                    f"📍 *Location:* {user_data[chat_id].get('location')}\n"
                    f"🧾 *Submitted UTR:* `{text}`\n\n"
                    "❓ *Action Lein:*"
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
