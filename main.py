import os
import time
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Bot Token
BOT_TOKEN = "8913279275:AAHkHR5t-50Jmwo0v5zenFNIGHx7TgUHjtE"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# HTTP Web Server (Render Health Check Pass Karwane Ke Liye)
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"z.ween2x Bot is running live!")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    print(f"HTTP server running on port {port}")
    httpd.serve_forever()

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def run_bot():
    print("Telegram Bot Started...")
    offset = None
    while True:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates"
            params = {"timeout": 30, "offset": offset}
            response = requests.get(url, params=params, timeout=35)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    for result in data.get("result", []):
                        offset = result["update_id"] + 1
                        message = result.get("message")
                        if message and "text" in message:
                            chat_id = message["chat"]["id"]
                            user_text = message["text"]
                            
                            if user_text.startswith("/start"):
                                send_message(chat_id, "Hello! Welcome to z.ween2x Official Bot.\n\nMade by mp.chouhan")
                            elif user_text.startswith("/help"):
                                send_message(chat_id, "Help Menu: Send /start to begin.")
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(3)

if __name__ == '__main__':
    threading.Thread(target=run_http_server, daemon=True).start()
    run_bot()
