import os
import requests
from flask import Flask, request

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Aapka Sahi Telegram Chat ID Update Kar Diya Hai
ADMIN_CHAT_ID = "8866210749" 

app = Flask(__name__)

user_states = {}
user_data = {}

# Primary Payment UPI Details
PRIMARY_UPI_ID = "z.ween2x.official@okaxis"

# Auto-Generated Dynamic QR Code Link (₹100 Payment)
PAYMENT_QR_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa={PRIMARY_UPI_ID}%26pn=z.ween2x%20Official%26am=100%26cu=INR"

def send_message(chat_id, text, parse_mode="Markdown"):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
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
                "• *Slot Completion Mandatory:* Match tabhi start hoga jab registration ke saare required slots (jaise 128 teams) poore fill ho jayenge. Slots poore hone tak tournament process hold par rahega.\n\n"

                "📌 *2. MATCH SCHEDULE & DAILY NOTIFICATION*\n"
                "• *Daily Schedule:* Subah *8:00 AM* se pehle aapko Telegram / WhatsApp par official message mil jayega ki aaj kis team ka match kis team se hai aur room ki kya timing rahegi.\n\n"

                "📌 *3. TEAM PRESENCE & SUBSTITUTION RULES*\n"
                "• *Walkover Policy:* Match time par agar koi team room me nahi aati hai, toh use direct *Lose (Hara hua)* declare kar diya jayega.\n"
                "• *Minimum Player Requirement:* Agar team ka *1 player* bhi room me aata hai, toh usko match khelna padega (chahe aap Jeeto ya Haro). Single player hone par match cancel nahi hoga.\n"
                "• *Substitute Players Rule:* Match khelne ke liye squad me kam se kam *2 original registered players* ka hona zaroori hai. Baaki *2 players* aap bahar se kisi ko bhi khila sakte hain.\n\n"

                "📌 *4. STRICT ANTI-CHEAT & LEGAL WARNING*\n"
                "• *Zero Tolerance Policy:* Match ke dauran koi bhi Hack, Script, Config, Panel, Emulators, ya Cheating use nahi karega.\n"
                "• *Strict Penalty & Legal Action (FIR):* Agar koi player hack ya cheating karte hue pakda gaya, toh:\n"
                "  1. Us match me jitni bhi teams khele gi (saare teams) ki *Registration Fee cheat karne wale player ko apni jeb se bharni padegi*.\n"
                "  2. Us player ke khilaf Fraud aur Cheating ki *Police FIR* karwayi jayegi aur permanent block kiya jayegi.\n\n"

                "📌 *5. ROOM ID & PASSWORD POLICY*\n"
                "• *On-Time Credentials:* Room ID aur Password bilkul match timing ke waqt hi share kiya jayega. Kisi ko bhi pehle se Room ID nahi di jayegi.\n\n"

                "📌 *6. TOP 16 QUALIFICATION (BEST OF 3 MATCHES)*\n"
                "• *Head-to-Head 3 Matches:* Tournament ke aage ke stage me jo *16 Teams* hongi, unke aapas me *3 Matches (Best of 3)* honge.\n"
                "• *Qualification Rule:* Jo team aapas ke 3 matches me se kam se kam *2 Baar Match Jeetegi (2 Wins)*, wahi team next stage/final ke liye aage ready maani jayegi.\n\n"

                "📌 *7. PRIZE MONEY & PLATFORM FEES*\n"
                "• *23% Deduction:* Har Winner Team ki Prize Money me se *23% Platform Charge & System Maintenance Fee* deduct karke final payout transfer kiya jayega.\n"
                "• *Non-Refundable:* Registration fee kisi bhi condition me refund nahi hogi.\n\n"

                "📌 *8. HELP & SUPPORT*\n"
                "• *Direct Admin Contact:* Kisi bhi sawal, dikkat ya query ke liye aap direct contact kar sakte hain:\n"
                "👉 *Telegram ID:* @zween2xofficial\n\n"
                "☀️ *Aapka din shubh ho! Dhanyawad - z.ween2x Management*"
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
                caption = (
                    "💰 *Registration Fee Payment (₹100)*\n\n"
                    "Aap niche diye gaye tareeqon se ₹100 pay karein:\n\n"
                    "📷 *1. QR Code:* Upar diye gaye QR Code ko kisi bhi UPI App (PhonePe / GPay / Paytm) se scan karke pay karein.\n\n"
                    f"🆔 *2. UPI ID:* `{PRIMARY_UPI_ID}` (UPI ID par direct payment karein)\n\n"
                    "------------------------------------\n"
                    "Payment hone ke baad, apna **12-Digit UTR / Transaction ID** yahan chat me type karke bhejein:"
                )
                send_photo(chat_id, PAYMENT_QR_URL, caption)

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
                # Ab yeh message direct AAPKE (8866210749) paas aayega!
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
