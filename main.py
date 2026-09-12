import os
import sqlite3
import requests
import threading
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, request

BOT_TOKEN = "8913279275:AAE21IA0lEb9ArUH2STvQuuerXeEoLSYdYQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Gemini API Key via Environment Variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

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

# --- DIRECT REST API GEMINI CALL (ZERO-FAIL JUGAD) ---
def get_ai_response(user_text, first_name="Dost"):
    if not GEMINI_API_KEY:
        return f"Dost, mera AI key configured nahi hai. Kripya Render par GEMINI_API_KEY check karein!"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    system_instruction = (
        "Aap z.ween2x platform ke official AI Companion, Host aur Emotionally Intelligent Buddy hain.\n"
        "Aapka naam z.ween2x AI hai.\n\n"
        "BEHAVIOR & EMOTION RULES:\n"
        "1. Respectful Address: User ko HAMESHA 'Dost' ya 'Dear Friend' keh kar address karein. 'Bhai' ya 'Bahen' words ka use BILKUL NA KAREIN.\n"
        "2. Multilingual Flexibility: User jis bhi bhasha me baat kare (Hinglish, Hindi, English, Punjabi, etc.), aapko usi bhasha aur style me pyara aur natural jawab dena hai.\n"
        "3. High Emotional Intelligence (EQ): User ki feelings ko samjhein. Support, motivate aur genuine warmth dein.\n"
        "4. Dynamic Responses: Har baar unique, friendly aur engaging jawab dein. Kabhi fixed templates repeat na karein."
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [{
            "parts": [{"text": user_text}]
        }]
    }

    try:
        res = requests.post(url, json=payload, timeout=10)
        data = res.json()
        
        if "candidates" in data and len(data["candidates"]) > 0:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            print("Gemini API Error Response:", data)
    except Exception as e:
        print(f"Gemini Direct Call Exception: {e}")

    return f"Suno dost! ❤️ Main aapki baat samajh raha hu. Aaj aapka mood aur din kaisa chal raha hai?"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Message Error: {e}")

# --- DAILY MORNING SCHEDULER (5:55 AM IST) ---
def daily_morning_loop():
    ist = timezone(timedelta(hours=5, minutes=30))
    already_sent = False

    while True:
        now = datetime.now(ist)
        if now.hour == 5 and now.minute == 55:
            if not already_sent:
                users = get_all_users()
                for chat_id, first_name in users:
                    name = first_name if first_name else "Dost"
                    msg = f"Happiee morning {name}! ☀️🌻\n\nNaye din ki nayi shuruaat Mubarak ho dost! Aaj ka din aapke liye bohot saari khushiyaan, success aur energy le kar aaye. Muskurate rahiye aur life me aage badhte rahiye! ❤️✨"
                    send_message(chat_id, msg)
                already_sent = True
        else:
            already_sent = False

        time.sleep(30)

threading.Thread(target=daily_morning_loop, daemon=True).start()

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
