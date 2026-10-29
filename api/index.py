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
                
                if "callback_query" in update:
                    callback = update["callback_query"]
                    chat_id = callback["message"]["chat"]["id"]
                    data = callback.get("data", "")
                    
                    if data.startswith("page_"):
                        page_num = int(data.replace("page_", ""))
                        total_pages = 5
                        self.send_telegram_message(
                            chat_id, 
                            f"Menampilkan Halaman {page_num} dari {total_pages}\nSilakan pilih halaman di bawah:",
                            reply_markup=self.get_pagination_keyboard(page_num, total_pages)
                        )
                    self.answer_callback_query(callback["id"])
                    
                else:
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
                                total_pages = 5
                                welcome_text = (
                                    "Koleksi Media\n\n"
                                    "Informasi Statistik:\n"
                                    "- Status: Bot Aktif & Stabil\n\n"
                                    "Silakan pilih halaman di bawah untuk melihat isi koleksi:"
                                )
                                self.send_telegram_message(
                                    chat_id, 
                                    welcome_text, 
                                    reply_markup=self.get_pagination_keyboard(1, total_pages)
                                )
                        elif "video" in message or "document" in message or "photo" in message or "audio" in message or "animation" in message:
                            # Cek apakah ini bagian dari album (media_group_id)
                            media_group_id = message.get("media_group_id")
                            
                            db_msg_id = None
                            if DB_CHANNEL_ID:
                                db_msg_id = self.forward_to_channel(chat_id, message.get("message_id"))

                            if db_msg_id:
                                telegram_link = f"https://t.me/private_media_db_bot?start=msg_{db_msg_id}"
                                
                                # Jika ini album, berikan keterangan agar pengguna tahu
                                if media_group_id:
                                    reply_text = f"Media Album Berhasil Disimpan!\n\nLink Akses:\n{telegram_link}"
                                else:
                                    reply_text = f"Media Berhasil Disimpan!\n\nLink Akses:\n{telegram_link}"
                                    
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

    def send_telegram_message(self, chat_id, text, reply_markup=None):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self.call_telegram_api(url, payload)

    def answer_callback_query(self, callback_query_id):
        url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        self.call_telegram_api(url, payload)

    def get_pagination_keyboard(self, current_page, total_pages):
        keyboard = []
        row1 = [
            {"text": "Sebelumnya", "callback_data": f"page_{max(1, current_page-1)}"},
            {"text": f"{current_page}/{total_pages}", "callback_data": "info"},
            {"text": "Berikutnya", "callback_data": f"page_{min(total_pages, current_page+1)}"}
        ]
        keyboard.append(row1)
        
        row_num = []
        for i in range(1, total_pages + 1):
            btn_text = f"[{i}]" if i == current_page else str(i)
            row_num.append({"text": btn_text, "callback_data": f"page_{i}"})
        
        if row_num:
            keyboard.append(row_num)

        return {"inline_keyboard": keyboard}

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
