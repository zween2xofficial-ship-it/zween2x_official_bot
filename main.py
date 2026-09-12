import os
import sqlite3
import secrets
import string
import requests
from flask import Flask, request
from google import genai

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

ADMIN_CHAT_ID = "8866210749" 

# Gemini API via Environment Variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini AI Client initialized successfully!")
    except Exception as e:
        print(f"Gemini Client Init Error: {e}")

app = Flask(__name__)

user_states = {}
user_data = {}

PRIMARY_UPI_ID = "z.ween2x.official@okaxis"
PAYMENT_QR_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={PRIMARY_UPI_ID}%26pn=z.ween2x%20Official%26am=100%26cu=INR"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value INTEGER
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('team_counter', 1)")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY,
            base_token TEXT UNIQUE,
            members_count INTEGER DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS players (
            player_id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER,
            assigned_token TEXT UNIQUE,
            role TEXT,
            name TEXT,
            uid TEXT,
            telegram TEXT,
            phone TEXT,
            location TEXT,
            utr TEXT UNIQUE,
            chat_id INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def generate_secret_hash(length=10):
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def is_utr_duplicate(utr):
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("SELECT player_id FROM players WHERE utr = ?", (utr,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def create_new_team():
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM config WHERE key = 'team_counter'")
    current_team_id = cursor.fetchone()[0]

    if current_team_id > 128:
        conn.close()
        return None, "LIMIT_REACHED"

    random_hash = generate_secret_hash(10)
    base_token = f"#zween2x-{current_team_id:04d}-{random_hash}"

    cursor.execute("INSERT INTO teams (team_id, base_token, members_count) VALUES (?, ?, 1)", (current_team_id, base_token))
    cursor.execute("UPDATE config SET value = ? WHERE key = 'team_counter'", (current_team_id + 1,))
    
    conn.commit()
    conn.close()
    return base_token, "SUCCESS"

def join_existing_team(provided_token):
    clean_token = provided_token.strip()
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT team_id, members_count, base_token FROM teams WHERE base_token = ?", (clean_token,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None, "INVALID_TOKEN"

    team_id, members_count, base_token = row

    if members_count >= 4:
        conn.close()
        return None, "TEAM_FULL"

    new_count = members_count + 1
    cursor.execute("UPDATE teams SET members_count = ? WHERE team_id = ?", (new_count, team_id))
    
    conn.commit()
    conn.close()
    return base_token, "SUCCESS"

def get_squad_details(provided_token):
    clean_token = provided_token.strip()
    conn = sqlite3.connect("tournament.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT team_id, members_count FROM teams WHERE base_token = ?", (clean_token,))
    team_row = cursor.fetchone()

    if not team_row:
        conn.close()
        return None

    team_id, members_count = team_row
    cursor.execute("""
        SELECT role, name, uid, telegram, phone, location, timestamp 
        FROM players WHERE team_id = ? ORDER BY player_id ASC
    """, (team_id,))
    players = cursor.fetchall()
    conn.close()

    return {
        "team_id": team_id,
        "base_token": clean_token,
        "members_count": members_count,
        "players": players
    }

def get_ai_response(user_text):
    if not ai_client:
        return "Haan bhai, z.ween2x official bot par aapka swagat hai! Registration ke liye `/register` type karein."

    system_instruction = (
        "Aap z.ween2x Free Fire Esports Platform ke official AI Companion aur Assistant hain.\n"
        "Aapka main role user ke sath ek genuine, respectful aur empathetic insaan ki tarah connect hona hai.\n\n"
        "BEHAVIOR RULES:\n"
        "1. Friendly & Supportive Tone: Natural Hinglish me baat karein. Gamer buddy ki tarah behave karein.\n"
        "2. Emotional Intelligence: Agar user pareshan hai, gusse me hai ya confused hai, toh unhe pehle emotionally calm karein, patience rakhein aur unhe sahi rasta batayein.\n"
        "3. Trust & Security: User ko z.ween2x platform ki genuineness aur transparency ka poora bharosa dawayein.\n"
        "4. Knowledge Base:\n"
        "   - Registration Fee: ₹100 per team.\n"
        "   - Team Limit: Strict 128 Teams Cap (4 players per squad).\n"
        "   - Process: User `/register` command dekar apni team register kar sakta hai ya Secret Token se join ho sakta hai.\n"
        "   - Admin Support: Direct contact @zween2xofficial.\n"
        "Jawab warm, clear aur concise rakhein."
    )
    
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_text,
            config={'system_instruction': system_instruction}
        )
        if response and response.text:
            return response.text
    except Exception as e:
        print(f"Gemini API Call Error: {e}")
        
    return "Haan bhai! Main aapki kya help kar sakta hu? Agar registration karna ho toh `/register` type karein ya mujhse koi bhi sawaal poochein."

def send_message(chat_id, text, reply_markup=None, parse_mode="Markdown"):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Message Error: {e}")

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
        print(f"Edit Message Error: {e}")

# --- WEBHOOK ROUTE ---
@app.route('/', methods=['GET'])
def home():
    return "z.ween2x AI Gaming Companion Engine Active!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data:
        return "OK", 200

    # 1. CALLBACK QUERY
    if "callback_query" in data:
        cb = data["callback_query"]
        cb_id = cb["id"]
        cb_data = cb["data"]
        chat_id = cb["message"]["chat"]["id"]
        admin_msg_id = cb["message"]["message_id"]

        if cb_data == "choice_new_team":
            conn = sqlite3.connect("tournament.db")
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = 'team_counter'")
            current_team_id = cursor.fetchone()[0]
            conn.close()

            if current_team_id > 128:
                send_message(chat_id, "🚫 *Tournament Registrations Full!*\n\nStrict 128 teams limit poori ho chuki hai.")
            else:
                user_data[chat_id] = {"reg_type": "NEW"}
                user_states[chat_id] = "STEP_NAME"
                send_message(chat_id, "🆕 *New Team Registration Selected!*\n\n📝 *Step 1/5:* Apna *Full Name* likhkar bhejein:")

        elif cb_data == "choice_join_team":
            user_data[chat_id] = {"reg_type": "JOIN"}
            user_states[chat_id] = "STEP_JOIN_CODE"
            send_message(chat_id, "🔗 *Join Existing Team Selected!*\n\nLeader ka **Official Secret Team Token** enter karein (Jaise: `#zween2x-0001-qwertyuiop`):")

        elif cb_data.startswith("approve_") or cb_data.startswith("reject_"):
            action, target_chat_id = cb_data.split("_")
            target_chat_id = int(target_chat_id)
            pdata = user_data.get(target_chat_id, {})

            if action == "approve":
                reg_type = pdata.get("reg_type")

                if reg_type == "NEW":
                    token, status = create_new_team()
                    role = "Leader"
                    if status == "LIMIT_REACHED":
                        send_message(target_chat_id, "❌ Registration failed! 128 Teams limit complete ho chuki hai.")
                        return "OK", 200
                else:
                    join_code = pdata.get("join_code", "")
                    token, status = join_existing_team(join_code)
                    role = "Member"
                    if status == "INVALID_TOKEN":
                        send_message(target_chat_id, "❌ Registration Failed! Galat team token code enter kiya tha.")
                        return "OK", 200
                    elif status == "TEAM_FULL":
                        send_message(target_chat_id, "❌ Registration Failed! Yeh team pehle se full hai (4/4 Players Joined).")
                        return "OK", 200

                conn = sqlite3.connect("tournament.db")
                cursor = conn.cursor()
                cursor.execute("SELECT team_id FROM teams WHERE base_token = ?", (token,))
                team_id = cursor.fetchone()[0]

                cursor.execute("""
                    INSERT INTO players (team_id, assigned_token, role, name, uid, telegram, phone, location, utr, chat_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (team_id, token, role, pdata.get("name"), pdata.get("uid"), pdata.get("telegram"), pdata.get("phone"), pdata.get("location"), pdata.get("utr"), target_chat_id))
                conn.commit()
                conn.close()

                edit_message_text(ADMIN_CHAT_ID, admin_msg_id, f"✅ *APPROVED & CONFIRMED!*\n🎟 Token Assigned: `{token}`")

                player_msg = (
                    "🎉 *Registration Verified & Confirmed!*\n\n"
                    f"🎟 *Aapka Official Secret Team Token:* `{token}`\n\n"
                    "📌 *Note:* Apni team ke baaki members ko yeh same token share karein join karne ke liye (Max 4 Players).\n\n"
                    "🏆 All the best - *z.ween2x Management*"
                )
                send_message(target_chat_id, player_msg)

            elif action == "reject":
                edit_message_text(ADMIN_CHAT_ID, admin_msg_id, "❌ *REJECTED BY ADMIN*")
                
                player_msg = (
                    "❌ *Registration Verification Failed!*\n\n"
                    "Aapka payment / UTR verify nahi ho paya hai.\n"
                    "• Dobara `/register` karein ya Admin se contact karein: *@zween2xofficial*"
                )
                send_message(target_chat_id, player_msg)

        requests.post(f"{TELEGRAM_API_URL}/answerCallbackQuery", json={"callback_query_id": cb_id})
        return "OK", 200

    # 2. INCOMING MESSAGES HANDLER
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if text == "/start":
            user_states[chat_id] = None
            user_data[chat_id] = {}
            msg = (
                "👋 *Welcome to z.ween2x Esports Platform!*\n\n"
                "Main aapka personal gaming host aur AI buddy hu. Main yahan aapki har tarah se help karne ke liye ready hu!\n\n"
                "📌 *Quick Commands:*\n"
                "👉 `/register` - Tournament Registration\n"
                "👉 `/rules` - Official Rulebook\n"
                "👉 `/cancel` - Cancel Process\n\n"
                "💬 Aap mujhse tournament, match timings, ya kisi bhi topic par natural tarike se baat kar sakte hain!"
            )
            send_message(chat_id, msg)

        elif text == "/stats" and str(chat_id) == ADMIN_CHAT_ID:
            conn = sqlite3.connect("tournament.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM teams")
            total_teams = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM players")
            total_players = cursor.fetchone()[0]
            conn.close()

            stats_msg = (
                "📊 *z.ween2x LIVE STATS*\n\n"
                f"🛡 *Total Teams Registered:* `{total_teams} / 128`\n"
                f"👤 *Total Players Verified:* `{total_players} / 512`\n"
            )
            send_message(chat_id, stats_msg)

        elif text == "/rules":
            rules = (
                "📜 *z.ween2x TOURNAMENT RULEBOOK*\n\n"
                "1. Strict 128 Teams Cap (Max 4 Players Per Squad).\n"
                "2. Registration Fee: ₹100 per team.\n"
                "3. Match Details Subah 8:00 AM se pehle share ki jayengi.\n"
                "4. Emulators and Hackers strictly prohibited.\n\n"
                "💬 Need help? Contact Admin: *@zween2xofficial*"
            )
            send_message(chat_id, rules)

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
            send_message(chat_id, "❌ Process cancel kar diya gaya hai. Aap mujhse koi bhi baat kar sakte hain!")

        else:
            state = user_states.get(chat_id)

            if state == "STEP_JOIN_CODE":
                squad = get_squad_details(text)
                if not squad:
                    send_message(chat_id, "❌ *Invalid Token Code.*\n\nKripya sahi token code re-enter karein:")
                elif squad['members_count'] >= 4:
                    send_message(chat_id, "❌ *Yeh team pehle se full hai (4/4 Players).* Naye players add nahi ho sakte.")
                    user_states[chat_id] = None
                else:
                    user_data[chat_id]["join_code"] = text
                    user_states[chat_id] = "STEP_NAME"
                    send_message(chat_id, "✅ *Team Found!*\n\n📝 *Step 1/5:* Apna *Full Name* likhkar bhejein:")

            elif text.startswith("#zween2x-"):
                if str(chat_id) != ADMIN_CHAT_ID:
                    send_message(chat_id, "❌ *Invalid Token Code!*")
                else:
                    squad = get_squad_details(text)
                    if not squad:
                        send_message(chat_id, "❌ *Aesi koi team nahi hai!*")
                    else:
                        msg = (
                            f"🛡 *ADMIN SQUAD DATA (Team #{squad['team_id']:04d})*\n"
                            f"🎟 *Token:* `{squad['base_token']}`\n"
                            f"👥 *Members:* `{squad['members_count']} / 4`\n\n"
                        )
                        for idx, p in enumerate(squad['players'], 1):
                            msg += (
                                f"*{idx}. {p[0]}:* {p[1]}\n"
                                f"   🎮 Game UID: `{p[2]}`\n"
                                f"   ✈️ Telegram: {p[3]}\n"
                                f"   📞 Phone: `{p[4]}`\n"
                                f"   📍 Location: {p[5]}\n"
                                f"   🕒 Registered: `{p[6]}`\n\n"
                            )
                        send_message(chat_id, msg)

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

                reg_mode = "🆕 New Team Leader" if user_data[chat_id].get("reg_type") == "NEW" else f"🔗 Joining Team Member"

                summary = (
                    "🔍 *Details Verification:*\n\n"
                    f"📌 *Role:* {reg_mode}\n"
                    f"👤 *Name:* {user_data[chat_id]['name']}\n"
                    f"🎮 *Game UID:* {user_data[chat_id]['uid']}\n"
                    f"✈️ *Telegram:* {user_data[chat_id]['telegram']}\n"
                    f"📞 *WhatsApp:* {user_data[chat_id]['phone']}\n"
                    f"📍 *Location:* {user_data[chat_id]['location']}\n\n"
                    "------------------------------------\n"
                    "✅ Payment ke liye niche **PAY** type karke bhejein."
                )
                send_message(chat_id, summary)

            elif state == "CHECK_DETAILS" and text.upper() == "PAY":
                user_states[chat_id] = "STEP_UTR"
                caption = (
                    "💰 *Registration Fee Payment (₹100)*\n\n"
                    "📷 *1. QR Code:* Scan karke ₹100 pay karein.\n"
                    f"🆔 *2. UPI ID:* `{PRIMARY_UPI_ID}`\n\n"
                    "Payment hone ke baad, apna **12-Digit UTR / Transaction ID** enter karein:"
                )
                send_photo(chat_id, PAYMENT_QR_URL, caption)

            elif state == "STEP_UTR":
                if is_utr_duplicate(text):
                    send_message(chat_id, "⚠️ *Yeh UTR pehle se registered hai!* Sahi UTR enter karein:")
                else:
                    user_data[chat_id]["utr"] = text
                    user_states[chat_id] = None

                    admin_buttons = {
                        "inline_keyboard": [
                            [
                                {"text": "✅ Approve", "callback_data": f"approve_{chat_id}"},
                                {"text": "❌ Reject", "callback_data": f"reject_{chat_id}"}
                            ]
                        ]
                    }

                    reg_type_str = "NEW TEAM LEADER" if user_data[chat_id].get("reg_type") == "NEW" else f"MEMBER JOINING ({user_data[chat_id].get('join_code')})"

                    admin_report = (
                        "📥 *NEW TOURNAMENT REGISTRATION*\n\n"
                        f"🏷 *Category:* `{reg_type_str}`\n"
                        f"👤 *Name:* {user_data[chat_id].get('name')}\n"
                        f"🎮 *Game UID:* {user_data[chat_id].get('uid')}\n"
                        f"✈️ *Telegram:* {user_data[chat_id].get('telegram')}\n"
                        f"📞 *WhatsApp:* {user_data[chat_id].get('phone')}\n"
                        f"📍 *Location:* {user_data[chat_id].get('location')}\n"
                        f"🧾 *Submitted UTR:* `{text}`\n\n"
                        "❓ *Action Lein:*"
                    )
                    send_message(ADMIN_CHAT_ID, admin_report, reply_markup=admin_buttons)

                    player_msg = (
                        "⏳ *Registration Details Submitted!*\n\n"
                        "Aapki details verification ke liye bhej di gayi hain. Admin check karke Token issue kar dega."
                    )
                    send_message(chat_id, player_msg)

            # AI EMOTIONAL & INTELLIGENT CHAT ENGINE
            else:
                ai_reply = get_ai_response(text)
                send_message(chat_id, ai_reply, parse_mode=None)

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
