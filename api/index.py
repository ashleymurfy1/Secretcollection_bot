import os
import json
import time
import urllib.request
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
DB_CHANNEL_ID = os.environ.get('DB_CHANNEL_ID', '')

# Penyimpanan sementara dalam memori server (untuk menangani grup album)
ALBUM_STORAGE = {}

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
                        if len(parts) > 1 and parts[1].startswith("batch_"):
                            # Ketika link batch diklik, ambil daftar ID pesan dan kirim dengan jeda aman
                            batch_key = parts[1]
                            msg_ids = ALBUM_STORAGE.get(batch_key, [])
                            
                            if msg_ids:
                                self.send_telegram_message(chat_id, f"📦 Mengirim {len(msg_ids)} media satu persatu dengan aman...")
                                for db_msg_id in msg_ids:
                                    self.copy_from_channel(chat_id, db_msg_id)
                                    # Jeda 0.6 detik per file agar aman dari banned Telegram
                                    time.sleep(0.6)
                            else:
                                self.send_telegram_message(chat_id, "❌ Kumpulan file tidak ditemukan atau server telah mereset memori.")
                        elif len(parts) > 1 and parts[1].startswith("msg_"):
                            try:
                                db_msg_id = int(parts[1].replace("msg_", ""))
                                self.copy_from_channel(chat_id, db_msg_id)
                            except:
                                self.send_telegram_message(chat_id, "❌ File tidak ditemukan.")
                        else:
                            self.send_telegram_message(
                                chat_id, 
                                "Halo! Kirimkan foto atau album ke sini untuk dibuatkan link-nya."
                            )
                    elif "video" in message or "document" in message or "photo" in message or "audio" in message or "animation" in message:
                        media_group_id = message.get("media_group_id")
                        
                        # Teruskan file ke Channel Database
                        db_msg_id = None
                        if DB_CHANNEL_ID:
                            db_msg_id = self.forward_to_channel(chat_id, message.get("message_id"))

                        if db_msg_id:
                            if media_group_id:
                                # Jika ini bagian dari album (banyak media sekaligus)
                                batch_key = f"batch_{media_group_id[-6:]}"
                                if batch_key not in ALBUM_STORAGE:
                                    ALBUM_STORAGE[batch_key] = []
                                
                                if db_msg_id not in ALBUM_STORAGE[batch_key]:
                                    ALBUM_STORAGE[batch_key].append(db_msg_id)
                                
                                # MEMAKSA USERNAME MENGGUNAKAN GARIS BAWAH SECARA EKSPLISIT
                                bot_username = "private_media_db_bot"
                                telegram_link = f"https://t.me/{bot_username}?start={batch_key}"
                                
                                # Kirim balasan hanya jika ini file pertama dalam kelompok untuk menghindari spam chat
                                if len(ALBUM_STORAGE[batch_key]) == 1:
                                    reply_text = f"✅ *Album Media Berhasil Disimpan!*\n\n🔗 *1 Link untuk Semua Media:*\n{telegram_link}"
                                    self.send_telegram_message(chat_id, reply_text)
                            else:
                                # Jika dikirim satuan
                                bot_username = "private_media_db_bot"
                                telegram_link = f"https://t.me/{bot_username}?start=msg_{db_msg_id}"
                                reply_text = f"✅ *Media Berhasil Disimpan!*\n\n🔗 *Link Akses:*\n{telegram_link}"
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
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
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
