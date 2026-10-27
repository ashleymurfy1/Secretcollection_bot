import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")

                if text == "/start":
                    send_message(chat_id, "Halo! Bot sharing media siap digunakan.")
                else:
                    send_message(chat_id, f"Pesan diterima: {text}")
        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.end_headers()
        return

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)
