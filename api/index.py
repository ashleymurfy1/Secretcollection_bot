import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request
import random

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
BOT_USERNAME = "Secretcollection_bot"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                update = json.loads(post_data.decode('utf-8'))
                
                # Cek apakah ada 'message' atau 'edited_message'
                message = update.get("message") or update.get("edited_message")
                
                if message and "chat" in message:
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "") or message.get("caption", "")
                    
                    if text.startswith("/start"):
                        self.send_telegram_message(
                            chat_id, 
                            "Halo! Kirimkan video atau foto ke sini untuk disimpan dan dibuatkan link-nya."
                        )
                    elif "video" in message or "document" in message or "photo" in message or "audio" in message or "animation" in message:
                        media_name = "Media"
                        if "video" in message:
                            media_name = "Video"
                        elif "photo" in message:
                            media_name = "Foto"
                        elif "document" in message:
                            media_name = "Dokumen"
                        
                        random_code = f"file_{random.randint(100000, 999999)}"
                        telegram_link = f"https://t.me/{BOT_USERNAME}?start={random_code}"
                        
                        reply_text = (
                            f"✅ **{media_name} berhasil disimpan!**\n\n"
                            f"🔗 **Link Akses Bot:**\n"
                            f"{telegram_link}"
                        )
                        self.send_telegram_message(chat_id, reply_text)
                    else:
                        if text:
                            self.send_telegram_message(chat_id, f"Pesan diterima: {text}")
                            
        except Exception as e:
            print(f"Error utama: {e}")

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
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        self.call_telegram_api(url, payload)

    def call_telegram_api(self, url, payload):
        if not TOKEN:
            return False
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            return result.get("ok", False)
        except Exception as e:
            print(f"Telegram API Error: {e}")
            return False
