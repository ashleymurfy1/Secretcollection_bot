import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request
import random

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
# Ganti dengan username bot Telegram kamu (tanpa tanda @)
BOT_USERNAME = "Secretcllctn_bot"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                update = json.loads(post_data.decode('utf-8'))
                
                # Menangani jika user mengklik link start=... dari bot
                if "message" in update:
                    message = update["message"]
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")
                    
                    if text.startswith("/start"):
                        parts = text.split(" ")
                        if len(parts) > 1:
                            payload_code = parts[1]
                            self.send_telegram_message(
                                chat_id, 
                                f"🎬 Ini media yang terikat dengan kode:\n`{payload_code}`\n\n*(Silakan kirim ulang media jika ingin mengambil kodenya lagi)*"
                            )
                        else:
                            self.send_telegram_message(
                                chat_id, 
                                "Halo! Kirimkan video atau foto kamu ke sini, dan bot akan membuatkan link khusus Telegram."
                            )
                    elif "video" in message or "document" in message or "photo" in message:
                        # Buat kode acak unik untuk media ini
                        random_code = f"media_{random.randint(10000, 99999)}"
                        
                        media_name = "Video" if "video" in message else ("Foto" if "photo" in message else "Dokumen")
                        
                        # Format link deep linking Telegram (membuka bot kembali)
                        telegram_link = f"https://t.me/{BOT_USERNAME}?start={random_code}"
                        
                        reply_text = (
                            f"✅ {media_name} berhasil disimpan!\n\n"
                            f"🔗 Klik link di bawah untuk membuka kembali lewat bot:\n"
                            f"{telegram_link}"
                        )
                        self.send_telegram_message(chat_id, reply_text)
                    else:
                        self.send_telegram_message(chat_id, f"Pesan diterima: {text}")
        except Exception as e:
            print(f"Error: {e}")

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
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Failed to send message: {e}")
