import os
import json
import time
import urllib.request
import base64
from http.server import BaseHTTPRequestHandler

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
DB_CHANNEL_ID = os.environ.get('DB_CHANNEL_ID', '')
ADMIN_USER_ID = 7508347332

# Menyimpan kumpulan ID pesan berdasarkan album/media_group_id
ALBUM_BATCHES = {}

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
                    user_id = message["from"]["id"]
                    text = message.get("text", "") or message.get("caption", "")
                    
                    is_media = "video" in message or "document" in message or "photo" in message or "audio" in message or "animation" in message
                    
                    if user_id != ADMIN_USER_ID and is_media:
                        self.send_telegram_message(chat_id, "⛔ Maaf, bot ini bersifat privat. Kamu hanya bisa menggunakan link yang dibagikan oleh admin!")
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
                        return

                    unsubscribed_channels = self.get_unsubscribed_channels(user_id)
                    if unsubscribed_channels and user_id != ADMIN_USER_ID:
                        channel_links = {
                            "-1002814282563": "https://t.me/secretlokal",
                            "-1003941525945": "https://t.me/BACKUPSCRT1",
                            "-1003911556352": "https://t.me/BACKUPSCRT",
                            "-1002438175955": "https://t.me/secretclctn"
                        }
                        
                        inline_keyboard = []
                        for idx, ch in enumerate(unsubscribed_channels, 1):
                            ch_url = channel_links.get(str(ch), f"https://t.me/c/{str(ch).replace('-100', '')}")
                            inline_keyboard.append([{"text": f"JOIN {idx}", "url": ch_url}])
                        
                        reply_markup = {"inline_keyboard": inline_keyboard}
                        join_text = "⚠️ **Akses Ditolak!**\n\nKamu harus bergabung ke semua channel di bawah ini terlebih dahulu untuk menggunakan bot."
                        
                        self.send_telegram_message_with_markup(chat_id, join_text, reply_markup)
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
                        return

                    if text.startswith("/start"):
                        parts = text.split(" ")
                        if len(parts) > 1:
                            payload_data = parts[1]
                            if payload_data.startswith("b_"):
                                try:
                                    decoded_str = base64.urlsafe_b64decode(payload_data[2:].encode()).decode()
                                    msg_ids = json.loads(decoded_str)
                                    if msg_ids:
                                        self.send_telegram_message(chat_id, f"📦 Mengirim {len(msg_ids)} media secara berurutan...")
                                        for db_msg_id in msg_ids:
                                            self.copy_from_channel(chat_id, int(db_msg_id))
                                            time.sleep(0.5)
                                    else:
                                        self.send_telegram_message(chat_id, "❌ Kumpulan file tidak ditemukan.")
                                except Exception as e:
                                    self.send_telegram_message(chat_id, "❌ Gagal memuat data batch file.")
                            elif payload_data.startswith("msg_"):
                                try:
                                    db_msg_id = int(payload_data.replace("msg_", ""))
                                    self.copy_from_channel(chat_id, db_msg_id)
                                except:
                                    self.send_telegram_message(chat_id, "❌ File tidak ditemukan.")
                            else:
                                self.send_telegram_message(chat_id, "❌ Format link tidak valid.")
                        else:
                            if user_id == ADMIN_USER_ID:
                                self.send_telegram_message(chat_id, "Halo Admin! Kirimkan file atau album ke sini untuk dibuatkan link aksesnya.")
                            else:
                                self.send_telegram_message(chat_id, "Halo! Silakan gunakan link sah yang dibagikan dari channel untuk mengakses file.")
                    
                    elif user_id == ADMIN_USER_ID and is_media:
                        db_msg_id = None
                        if DB_CHANNEL_ID:
                            db_msg_id = self.forward_to_channel(chat_id, message.get("message_id"))

                        if db_msg_id:
                            media_group_id = message.get("media_group_id")
                            bot_username = "private_media_db_bot"
                            
                            if media_group_id:
                                # Jika ini album, kumpulkan ID-nya ke dalam satu grup yang sama
                                if media_group_id not in ALBUM_BATCHES:
                                    ALBUM_BATCHES[media_group_id] = []
                                
                                if db_msg_id not in ALBUM_BATCHES[media_group_id]:
                                    ALBUM_BATCHES[media_group_id].append(db_msg_id)
                                
                                ids_list = ALBUM_BATCHES[media_group_id]
                                encoded_data = base64.urlsafe_b64encode(json.dumps(ids_list).encode()).decode()
                                telegram_link = f"https://t.me/{bot_username}?start=b_{encoded_data}"
                                
                                reply_text = f"✅ Album Berhasil Digabung!\n📦 Total file dalam album ini: {len(ids_list)}\n\n🔗 1 Link untuk Semua:\n{telegram_link}"
                                self.send_telegram_message(chat_id, reply_text)
                            else:
                                # Jika dikirim satuan
                                telegram_link = f"https://t.me/{bot_username}?start=msg_{db_msg_id}"
                                reply_text = "✅ Media Berhasil Disimpan!\n\n🔗 Link Akses:\n" + telegram_link
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

    def get_unsubscribed_channels(self, user_id):
        raw_channels = []
        val = os.environ.get("FORCE_SUB_CHANNEL_1", "").strip()
        if val:
            for ch in val.split(","):
                if ch.strip():
                    raw_channels.append(ch.strip())

        if not raw_channels:
            return []
        
        unsubscribed = []
        for channel in raw_channels:
            url = f"https://api.telegram.org/bot{TOKEN}/getChatMember?chat_id={channel}&user_id={user_id}"
            try:
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req)
                result = json.loads(response.read().decode('utf-8'))
                if result.get("ok"):
                    status = result.get("result", {}).get("status")
                    if status not in ["member", "administrator", "creator"]:
                        unsubscribed.append(channel)
                else:
                    unsubscribed.append(channel)
            except Exception as e:
                print(f"ForceSub Check Error for {channel}: {e}")
                unsubscribed.append(channel)
                
        return unsubscribed

    def send_telegram_message(self, chat_id, text):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        self.call_telegram_api(url, payload)

    def send_telegram_message_with_markup(self, chat_id, text, reply_markup):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
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
