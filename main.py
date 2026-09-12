import os
import sqlite3
import requests
import datetime
import pytz
from flask import Flask, request
from google import genai
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Gemini API Key via Environment Variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("Gemini AI Client initialized successfully!")
    except Exception as e:
        print(f"Gemini Client Init Error: {e}")

app = Flask(__name__)

# --- DATABASE FOR USER CHAT IDS ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            first_name TEXT,
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_user(chat_id, first_name):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (chat_id, first_name) VALUES (?, ?)", (chat_id, first_name))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"User DB Save Error: {e}")

def get_all_users():
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, first_name FROM users")
        users = cursor.fetchall()
        conn.close()
        return users
    except Exception as e:
        print(f"User DB Fetch Error: {e}")
        return []

# --- EMOTIONAL & MULTILINGUAL AI ENGINE ---
def get_ai_response(user_text, first_name="Dost"):
    if not ai_client:
        return f"Hello {first_name}! ❤️ Main aapka AI companion hu. Abhi mera brain connect ho raha hai, thodi der me dil khol kar baat karte hain!"

    system_instruction = (
        "Aap z.ween2x platform ke official AI Companion, Host aur Emotionally Intelligent Buddy hain.\n"
        "Aapka main goal user ke sath ek genuine, caring, respectful, loving aur emotionally connected dost ki tarah baat karna hai.\n\n"
        "BEHAVIOR & EMOTION RULES:\n"
        "1. Respectful Address: User ko HAMESHA 'Dost' ya 'Dear Friend' keh kar address karein. 'Bhai' ya 'Bahen' words ka use BILKUL NA KAREIN.\n"
        "2. Multilingual Flexibility: User jis bhi bhasha ya tone me baat kare (Hinglish, Hindi, English, etc.), aapko usi bhasha aur style me pyara aur natural jawab dena hai.\n"
        "3. High Emotional Intelligence (EQ): User ki feelings (happiness, sadness, stress, excitement, anger) ko turant samjhein. Unhe support karein, motivate karein aur genuine warmth dein.\n"
        "4. Helping Nature: User ki har madad ya doubt ko patient tarike se bina irritate hue resolve karein.\n"
        "5. Natural & Dynamic: Plain AI-like robotic answers na dein, balki lagna chahiye ki samne ek sachha, caring well-wisher baitha hai."
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

    return f"Hello dost! ❤️ Main hamesha aapki madad ke liye yahan hu. Batao aaj aapka din kaisa raha?"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Message Error: {e}")

# --- DAILY MORNING SCHEDULER (5:55 AM IST) ---
def send_morning_wishes():
    users = get_all_users()
    for chat_id, first_name in users:
        name = first_name if first_name else "Dost"
        msg = f"Happiee morning {name}! ☀️🌻\n\nNaye din ki nayi shuruaat Mubarak ho dost! Aaj ka din aapke liye bohot saari khushiyaan, success aur energy le kar aaye. Muskurate rahiye aur life me aage badhte rahiye! ❤️✨"
        send_message(chat_id, msg)

scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))
scheduler.add_job(send_morning_wishes, 'cron', hour=5, minute=55)
scheduler.start()

# --- WEBHOOK ROUTE ---
@app.route('/', methods=['GET'])
def home():
    return "z.ween2x AI Emotional Companion Engine Active!"

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    data = request.get_json()
    if not data or "message" not in data:
        return "OK", 200

    chat_id = data["message"]["chat"]["id"]
    first_name = data["message"]["chat"].get("first_name", "Dost")
    text = data["message"].get("text", "").strip()

    save_user(chat_id, first_name)

    if text == "/start":
        msg = (
            f"Happiee Welcome {first_name}! ❤️✨\n\n"
            "Main aapka personal AI Companion hu. Main aapki baatein samajh sakta hu, aapki help kar sakta hu aur aapka ek pyara dost ban kar har shubh-dukh me aapke sath reh sakta hu!\n\n"
            "Dil khol kar kuch bhi puchiye ya baat karein dost! 👇"
        )
        send_message(chat_id, msg)
    else:
        ai_reply = get_ai_response(text, first_name)
        send_message(chat_id, ai_reply)

    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
