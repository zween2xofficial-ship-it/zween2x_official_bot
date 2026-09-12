import os
import sqlite3
import requests
from flask import Flask, request

# --- DIRECT BOT CREDENTIALS ---
BOT_TOKEN = "8913279275:AAFDMqM4Lu_ST065lOa1PnHc39Dn1suzxmc"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

# --- DATABASE SETUP ---
def init_db():
    try:
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
    except Exception as e:
        print(f"DB Error: {e}")

init_db()

def save_user(chat_id, first_name):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (chat_id, first_name, last_active)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chat_id) DO UPDATE SET
                first_name=excluded.first_name,
                last_active=CURRENT_TIMESTAMP
        """, (chat_id, first_name))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Save User Error: {e}")

# --- GEMINI AI FUNCTION ---
def get_gemini_response(prompt_text):
    if not GEMINI_API_KEY:
        # Fallback response if Gemini key is missing
        return f"Aapka message mil gaya: '{prompt_text}'. Main z.ween2x Bot hoon!"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Aapka message: '{prompt_text}' (AI Service Busy)"
    except Exception as e:
        return f"Aapka message: '{prompt_text}'"

# --- TELEGRAM MESSAGE SENDER ---
def send_telegram_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send message: {e}")

# --- WEBHOOK ROUTE ---
@app.route("/", methods=["POST", "GET"])
def webhook():
    if request.method == "POST":
        try:
            data = request.get_json(force=True)
            if data and "message" in data:
                message = data["message"]
                chat_id = message["chat"]["id"]
                first_name = message["chat"].get("first_name", "User")
                text = message.get("text", "")

                save_user(chat_id, first_name)

                if text == "/start":
                    welcome_msg = f"Namaste {first_name}! Main z.ween2x ka Official AI Bot hoon. Aap mujhse koi bhi sawal pooch sakte hain!"
                    send_telegram_message(chat_id, welcome_msg)
                elif text:
                    ai_reply = get_gemini_response(text)
                    send_telegram_message(chat_id, ai_reply)
        except Exception as e:
            print(f"Webhook Error: {e}")

        return "OK", 200
    return "z.ween2x Bot Server is Running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
