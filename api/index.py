import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
DB_CHANNEL_ID = os.environ.get('DB_CHANNEL_ID', '')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                update = json.loads(post_data.decode('utf-8'))
                message = update.get("message") or update.get("edited_message")
                
                if message and "chat" in message:
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "") or message.get("caption", "")
                    
                    if text.startswith("/start"):
                        parts = text.split(" ")
                        if len(parts) > 1 and parts[1].startswith("msg"):
                            # Mengambil ID pesan database dari link start=msg_XXXXX
                            try:
                                db_msg_id = int(parts[1].replace("msg_", ""))
                                # Teruskan file dari channel database kembali ke pengguna
                                self.copy_from_channel(chat_id, db_msg_id)
                            except Exception as err:
                                print(f"Error parse msg_id: {err}")
                                self.send_telegram_message(chat_id, "❌ File tidak ditemukan atau link sudah kedaluwarsa.")
                        else:
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
                        
                        # 1. Teruskan file ke Channel Database dan tangkap message_id nya
                        db_msg_id = None
                        if DB_CHANNEL_ID:
                            db_msg_id = self.forward_to_channel(chat_id, message.get("message_id"))

                        if db_msg_id:
                            # Buat link yang berisi ID pesan database asli
                            telegram_link = f"https://t.me/private_media_db_bot?start=msg_{db_msg_id}"
                            reply_text = f"✅ *{media_name} berhasil disimpan!*\n\n🔗 *Link Akses Bot:*\n{telegram_link}"
                        else:
                            reply_text = f"⚠️ *{media_name} gagal disimpan ke channel database (Cek DB_CHANNEL_ID).* "

                        self.send_telegram_message(chat_id, reply_text)
                            
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
        payload = {"chat_id": chat_id, "text": text}
        self.call_telegram_api(url, payload)

    def forward_to_channel(self, from_chat_id, message_id):
        url = f"https://api.telegram.org/bot{TOKEN}/forwardMessage"
        payload = {
            "chat_id": DB_CHANNEL_ID,
            "from_chat_id": from_chat_id,
            "message_id": message_id
        }
        res = self.call_telegram_api(url, payload)
        if res and res.get("ok"):
            return res.get("result", {}).get("message_id")
        return None

    def copy_from_channel(self, chat_id, message_id):
        # Menggunakan copyMessage agar file terkirim tanpa label "Diteruskan dari..."
        url = f"https://api.telegram.org/bot{TOKEN}/copyMessage"
        payload = {
            "chat_id": chat_id,
            "from_chat_id": DB_CHANNEL_ID,
            "message_id": message_id
        }
        self.call_telegram_api(url, payload)

    def call_telegram_api(self, url, payload):
        if not TOKEN:
            return None
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            return result
        except Exception as e:
            print(f"Telegram API Error: {e}")
            return None
