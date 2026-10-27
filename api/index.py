import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            update = json.loads(post_data.decode('utf-8'))
            
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"].get("text", "")
                
                if text == "/start":
                    send_message(chat_id, "Halo! Bot sharing media siap digunakan.")
                else:
                    send_message(chat_id, f"Pesan diterima: {text}")
                    
        except Exception as e:
            print(f"Error handling request: {e}")

        # Selalu kirim status 200 OK ke Telegram agar tidak terjadi timeout/retry terus-menerus
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
        return

    def do_GET(self):
        # Untuk antisipasi jika URL Vercel-nya diakses langsung lewat browser
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Telegram Bot is running!")
        return

def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")
