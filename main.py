import os
import requests
from flask import Flask, request

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Aapka Personal Telegram Chat ID
ADMIN_CHAT_ID = "7267123985"

app = Flask(__name__)

user_states = {}
user_data = {}

# Payment Details
PRIMARY_UPI_ID = "z.ween2x.official@okaxis"
AIRTEL_UPI_ID = "8120238780@airtel"
AIRTEL_NUMBER = "8120238780"

def send_message(chat_id, text, parse_mode="Markdown"):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Error: {e}")

@app.route('/', methods=['GET'])
def home():
    return "z.ween2x Tournament Verification Engine Active!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        if text == "/start":
            user_states[chat_id] = None
            user_data[chat_id] = {}
            msg = (
                "🏆 *Welcome to z.ween2x Free Fire Tournament!*\n\n"
                "Organized by: *mp.chouhan*\n\n"
                "Commands:\n"
                "👉 /register - Start Registration\n"
                "👉 /rules - Tournament Official Rules\n"
                "👉 /cancel - Cancel Registration"
            )
            send_message(chat_id, msg)

        elif text == "/rules":
            rules = (
                "📜 *OFFICIAL TOURNAMENT RULES & REGULATIONS* 📜\n\n"
                "🚫 *1. Hacks & Emulators Ban:* PC / Emulator players strictly prohibited hain. Panel, Hacks, Scripts use karne par instant permanent ban milega.\n\n"
                "🔑 *2. Room ID & Password:* Room ID aur Password bilkul match timing ke waqt hi share kiya jayega, pehle se nahi diya jayega.\n\n"
                "🔥 *3. Top 10 Qualification System:* Matches ke bad jo **Top 10 Teams** hongi, unka **3 Times Match (Best of 3)** hoga. Jo team kam se kam **2 Baar Match Jeetegi (2 Wins)**, wohi next stage/final match ke liye qualify karegi.\n\n"
                "💸 *4. Winning & Platform Fee:* Har Winner Team ki prize money me se **23% Platform Fee & Hidden Charges** deduct kiye jayenge.\n\n"
                "❓ *5. Help & Support:* Kisi bhi prakar ke query ya sawal ke liye aap Admin ko direct contact kar sakte hain:\n"
                "👉 *Telegram ID:* @zween2xofficial\n\n"
                "⚖️ *6. Admin Decision:* Tournament Organizer (*mp.chouhan*) ka decision final aur sabhi ke liye mandatory hoga."
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

        elif text == "/edit":
            user_states[chat_id] = "STEP_NAME"
            user_data[chat_id] = {}
            send_message(chat_id, "🔄 *Registration Reset!*\n\n📝 *Step 1/5:* Apna *Full Name* dobara likhkar bhejein:")

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
                    "✅ Agar sab sahi hai toh payment ke liye niche **PAY** type karke bhejein.\n"
                    "✏️ Kuch galat hai toh sahi karne ke liye **/edit** par click karein."
                )
                send_message(chat_id, summary)

            elif state == "CHECK_DETAILS" and text.upper() == "PAY":
                user_states[chat_id] = "STEP_UTR"
                payment_instructions = (
                    "💰 *Registration Fee Payment (₹100)*\n\n"
                    "Aap niche diye gaye tareeqon se ₹100 pay karein:\n\n"
                    f"🆔 *UPI ID:* `{PRIMARY_UPI_ID}`\n"
                    f"🏦 *Airtel UPI:* `{AIRTEL_UPI_ID}`\n"
                    f"📲 *Airtel Mobile Transfer:* `{AIRTEL_NUMBER}`\n\n"
                    "------------------------------------\n"
                    "Payment hone ke baad, apna **12-Digit UTR / Transaction ID** yahan chat me type karke bhejein:"
                )
                send_message(chat_id, payment_instructions)

            elif state == "STEP_UTR":
                user_data[chat_id]["utr"] = text
                user_states[chat_id] = None

                admin_report = (
                    "📥 *NEW TOURNAMENT REGISTRATION RECEIVED!*\n\n"
                    f"👤 *Name:* {user_data[chat_id].get('name')}\n"
                    f"🎮 *Game UID & IGN:* {user_data[chat_id].get('uid')}\n"
                    f"✈️ *Telegram:* {user_data[chat_id].get('telegram')}\n"
                    f"📞 *WhatsApp:* {user_data[chat_id].get('phone')}\n"
                    f"📍 *Location:* {user_data[chat_id].get('location')}\n"
                    f"🧾 *Submitted UTR:* `{text}`\n"
                    f"🆔 *Player Telegram Chat ID:* `{chat_id}`\n\n"
                    "📌 *Action Required:* Payment & UTR verify karein aur player ko manual token bhej dein!"
                )
                send_message(ADMIN_CHAT_ID, admin_report)

                player_msg = (
                    "⏳ *Registration Details Submitted!*\n\n"
                    "Aapki details aur Payment UTR Admin (@zween2xofficial) ke paas verification ke liye bhej di gayi hain.\n\n"
                    "✅ Verification complete hone ke baad aapko aapka *Official Token & Slot Details* bhej diye jayenge.\n\n"
                    "❤️ *Dil se Thank You z.ween2x Tournament me participate karne ke liye!*"
                )
                send_message(chat_id, player_msg)

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
