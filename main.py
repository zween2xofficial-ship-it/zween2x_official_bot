import os
import requests
from flask import Flask, request

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# Registration state & database memory
user_states = {}
user_data = {}
token_counter = 1  # Unique token generator (#zween2x-00001)

# Quick QR Code generator link for ₹100 payment
UPI_ID = "9399223789@ybl"  # Apni UPI ID se replace karein agar alag ho
PAYMENT_QR_URL = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi://pay?pa={UPI_ID}&pn=z.ween2x%20Tournament&am=100&cu=INR"

def send_message(chat_id, text, parse_mode="Markdown"):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
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

@app.route('/', methods=['GET'])
def home():
    return "z.ween2x Tournament Registration Engine Active!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    global token_counter
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "").strip()

        # Command handling
        if text == "/start":
            user_states[chat_id] = None
            user_data[chat_id] = {}
            msg = (
                "🏆 *Welcome to z.ween2x Free Fire Tournament!*\n\n"
                "Organized by: *mp.chouhan*\n\n"
                "Commands:\n"
                "👉 /register - Registration Start Karein\n"
                "👉 /rules - Tournament Rules\n"
                "👉 /cancel - Cancel Registration"
            )
            send_message(chat_id, msg)

        elif text == "/rules":
            rules = (
                "📜 *Tournament Rules:*\n"
                "1. Hacks / Emulators strictly prohibited.\n"
                "2. Room ID/Password time par Telegram/WhatsApp par milega.\n"
                "3. Entry Fee ₹100 non-refundable hai."
            )
            send_message(chat_id, rules)

        elif text == "/register":
            user_states[chat_id] = "STEP_NAME"
            user_data[chat_id] = {}
            send_message(chat_id, "📝 *Step 1/5:* Apna *Full Name* likhkar bhejein:")

        elif text == "/cancel":
            user_states[chat_id] = None
            user_data[chat_id] = {}
            send_message(chat_id, "❌ Registration cancel kar diya gaya hai. Restart karne ke liye /register bhejein.")

        elif text == "/edit":
            user_states[chat_id] = "STEP_NAME"
            user_data[chat_id] = {}
            send_message(chat_id, "🔄 *Registration Reset!*\n\n📝 *Step 1/5:* Apna *Full Name* dobara likhkar bhejein:")

        elif text == "/confirm_payment":
            if user_states.get(chat_id) == "AWAITING_PAYMENT":
                user_states[chat_id] = "STEP_UTR"
                send_message(chat_id, "📲 Payment karne ke baad apna **12-Digit UTR Number** ya Transaction ID yahan type karke bhejein:")

        # Step-by-Step Question Flow
        else:
            state = user_states.get(chat_id)

            if state == "STEP_NAME":
                user_data[chat_id]["name"] = text
                user_states[chat_id] = "STEP_UID"
                send_message(chat_id, "🎮 *Step 2/5:* Apna *Free Fire Game UID & In-Game Name* likhkar bhejein:")

            elif state == "STEP_UID":
                user_data[chat_id]["uid"] = text
                user_states[chat_id] = "STEP_TG"
                send_message(chat_id, "✈️ *Step 3/5:* Apna *Telegram Username* ya Telegram Mobile Number bhejein:")

            elif state == "STEP_TG":
                user_data[chat_id]["telegram"] = text
                user_states[chat_id] = "STEP_PHONE"
                send_message(chat_id, "📞 *Step 4/5:* Apna active *WhatsApp / Phone Number* bhejein:")

            elif state == "STEP_PHONE":
                user_data[chat_id]["phone"] = text
                user_states[chat_id] = "STEP_LOCATION"
                send_message(chat_id, "📍 *Step 5/5:* Apne *Gaon / Shahar ka Naam aur State* likhkar bhejein:")

            elif state == "STEP_LOCATION":
                user_data[chat_id]["location"] = text
                user_states[chat_id] = "CHECK_DETAILS"

                # Summary verification screen
                summary = (
                    "🔍 *Kripya Apni Sabhi Details Check Kar Lein:*\n\n"
                    f"👤 *Name:* {user_data[chat_id]['name']}\n"
                    f"🎮 *Game UID & IGN:* {user_data[chat_id]['uid']}\n"
                    f"✈️ *Telegram:* {user_data[chat_id]['telegram']}\n"
                    f"📞 *WhatsApp/Mobile:* {user_data[chat_id]['phone']}\n"
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
                    "Upar diye gaye QR Code par ₹100 ka payment karein.\n\n"
                    "Payment hone ke baad, apna *12-Digit UTR / Ref Number* yahan chat me bhejein:"
                )
                send_photo(chat_id, PAYMENT_QR_URL, caption)

            elif state == "STEP_UTR":
                user_data[chat_id]["utr"] = text
                
                # Token generation
                assigned_token = f"#zween2x-{token_counter:05d}"
                token_counter += 1

                user_states[chat_id] = None  # Reset state after completion

                final_msg = (
                    "🎉 *CONGRATULATIONS! Registration Submitted Successfully!* 🎉\n\n"
                    f"🆔 *Your Official Token:* `{assigned_token}`\n"
                    f"🧾 *Submitted UTR:* `{text}`\n\n"
                    "Aapki registration detail aur UTR number verification ke liye submit ho chuka hai. Admin verify karke aapko group/room details bhej denge.\n\n"
                    "❤️ *Dil se Thank You z.ween2x Tournament me participate karne ke liye!*"
                )
                send_message(chat_id, final_msg)

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
