import os
import base64
import sqlite3
import requests
import threading
import time
from datetime import datetime, timezone, timedelta
from flask import Flask, request

# --- ENCODED TOKENS & KEYS ---
ENCODED_BOT_TOKEN = "ODkxMzI3OTI3NTpBQUUyMUlBMDFFYjlBclVIMlN0dlF1dWVyWGVFb0xTWWRZUQ=="
ENCODED_GEMINI_KEY = "QVEuQWI4Uk42THVwM2t1V1dTU2lVcVd6U3otZHp1aG5RTWxWNTJ2bnB5bmJsSE9kWWE1NXc="

# Decode Credentials Safely
try:
    BOT_TOKEN = base64.b64decode(ENCODED_BOT_TOKEN).decode("utf-8").strip()
except Exception:
    BOT_TOKEN = ""

TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY and ENCODED_GEMINI_KEY:
    try:
        GEMINI_API_KEY = base64.b64decode(ENCODED_GEMINI_KEY).decode("utf-8").strip()
    except Exception as e:
        print(f"Error decoding API Key: {e}")

app = Flask(__name__)

# --- DATABASE SETUP ---
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

# --- GEMINI AI FUNCTION ---
def get_gemini_response(prompt_text):
    if not GEMINI_API_KEY:
        return "System notice: API key missing."
    
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
            print(f"Gemini API Error: {response.text}")
            return "Main abhi thoda busy hoon, kripya thodi der baad dobara try karein!"
    except Exception as e:
        print(f"Request Exception: {e}")
        return "Connection me thodi dikkat aa rahi hai."

# --- TELEGRAM MESSAGE SENDER ---
def send_telegram_message(chat_id, text):
    if not BOT_TOKEN:
        print("Bot token missing")
        return
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
        data = request.get_json()
        if data and "message" in data:
            message = data["message"]
            chat_id = message["chat"]["id"]
            first_name = message["chat"].get("first_name", "User")
            text = message.get("text", "")

            # Save user ID
            save_user(chat_id, first_name)

            if text == "/start":
                welcome_msg = f"Namaste {first_name}! Main aapka AI Assistant hoon. Aap mujhse koi bhi sawal pooch sakte hain!"
                send_telegram_message(chat_id, welcome_msg)
            elif text:
                # Get response from Gemini AI
                ai_reply = get_gemini_response(text)
                send_telegram_message(chat_id, ai_reply)

        return "OK", 200
    return "Bot is running perfectly!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
