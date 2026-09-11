import os
import requests
from flask import Flask, request

BOT_TOKEN = "8913279275:AAHkHR5t-50Jmwo0v5zenFNIGHx7TgUHjtE"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Error: {e}")

@app.route("/", methods=["GET"])
def home():
    return "z.ween2x Bot is Live!"

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.get_json()
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"].get("text", "")

        if user_text.startswith("/start"):
            send_message(chat_id, "Hello! Welcome to z.ween2x Official Bot.\n\nMade by mp.chouhan")
        elif user_text.startswith("/help"):
            send_message(chat_id, "Help Menu: Send /start to begin.")

    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
