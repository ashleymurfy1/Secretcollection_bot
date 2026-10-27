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
            
            # Ubah data mentah dari Telegram menjadi dictionary Python
            update = json.loads(post_data.decode('utf-8'))
            print("DATA DARI TELEGRAM:", update)  # Ini akan masuk ke Logs Vercel
            
            # Cek apakah ada pesan masuk
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message.get("text", "")
                
                # Kirim balasan otomatis
                if text == "/start":
                    send_message(chat_id, "Halo! Bot sharing media siap digunakan.")
                else:
                    send_message(chat_id, f"Pesan diterima: {text}")
                    
        except Exception as e:
            print(f"Error utama: {e}")

        # Beri respons OK (200) ke Telegram agar tidak dianggap gagal
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
        return

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is active!")
        return

def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Gagal mengirim pesan: {e}")
