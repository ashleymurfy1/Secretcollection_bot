import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
DB_CHANNEL_ID = os.environ.get('DB_CHANNEL_ID', '')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                update = json.loads(post_data.decode('utf-8'))
                print("Update diterima dari Telegram:", json.dumps(update)) # Cek log Vercel nanti
                
                message = update.get("message") or update.get("edited_message")
                
                if message and "chat" in message:
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "") or message.get("caption", "")
                    
                    if text.startswith("/start"):
                        parts = text.split(" ")
                        if len(parts) > 1 and parts[1].startswith("msg_"):
                            try:
                                db_msg_id = int(parts[1].replace("msg_", ""))
                                self.copy_from_channel(chat_id, db_msg_id)
                            except Exception as err:
                                print(f"Error parse msg_id: {err}")
                                self.send_telegram_message(chat_id, "File tidak ditemukan.")
                        else:
                            self.send_telegram_message(
                                chat_id, 
                                "Halo! Kirimkan foto atau video ke sini untuk disimpan dan dibuatkan link-nya."
                            )
                    elif "video" in message or "document" in message or "photo" in message or "audio" in message or "animation" in message:
                        if not DB_CHANNEL_ID or not TOKEN:
                            print("ERROR: TELEGRAM_TOKEN atau DB_CHANNEL_ID belum diatur di Environment Variables Vercel!")
                            self.send_telegram_message(chat_id, "Konfigurasi bot belum lengkap di server.")
                            return

                        db_msg_id = self.forward_to_channel(chat_id, message.get("message_id"))
                        if db_msg_id:
                            telegram_link = f"https://t.me/private_media_db_bot?start=msg_{db_msg_id}"
                            reply_text = f"Media Berhasil Disimpan!\n\nLink Akses:\n{telegram_link}"
                            self.send_telegram_message(chat_id, reply_text)
                        else:
                            self.send_telegram_message(chat_id, "Gagal menyimpan ke channel database. Pastikan bot sudah jadi Admin di channel tersebut!")
                            
        except Exception as e:
            print(f"Error utama pada server: {e}")

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
        print(f"Gagal forward ke channel: {res}")
        return None

    def copy_from_channel(self, chat_id, message_id):
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
