import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                update = json.loads(post_data.decode('utf-8'))
                if "message" in update:
                    message = update["message"]
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")
                    
                    if text == "/start":
                        self.send_telegram_message(chat_id, "Halo! Bot sharing media siap digunakan.")
                    else:
                        self.send_telegram_message(chat_id, f"Pesan diterima: {text}")
        except Exception as e:
            print(f"Error: {e}")

        # Wajib merespons Telegram dengan HTTP 200 OK
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is active!")

    def send_telegram_message(self, chat_id, text):
        if not TOKEN:
            return
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Failed to send message: {e}")
