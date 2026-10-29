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
                
                # Menangani klik Tombol Inline (Callback Query)
                if "callback_query" in update:
                    callback = update["callback_query"]
                    chat_id = callback["message"]["chat"]["id"]
                    data = callback.get("data", "")
                    
                    if data.startswith("page_"):
                        page_num = data.replace("page_", "")
                        self.send_telegram_message(
                            chat_id, 
                            f"📄 Membuka Halaman {page_num} dari 17...\nSilakan pilih media di bawah:",
                            reply_markup=self.get_pagination_keyboard(int(page_num))
                        )
                    self.answer_callback_query(callback["id"])
                    
                # Menangani Pesan Teks / Media biasa
                else:
                    message = update.get("message") or update.get("edited_message")
                    if message and "chat" in message:
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "") or message.get("caption", "")
                        
                        if text.startswith("/start"):
                            # Kirim pesan sambutan dengan Tombol Navigasi Halaman ala contoh
                            welcome_text = (
                                "📁 **#KoleksiMedia**\n\n"
                                "📖 **Informasi Statistik:**\n"
                                "• 🎬 Video: 52 buah\n"
                                "• 🖼 Gambar: 286 lembar\n"
                                "• 📦 Total: 338 File"
                            )
                            self.send_telegram_message(
                                chat_id, 
                                welcome_text, 
                                reply_markup=self.get_pagination_keyboard(1)
                            )
                        elif "video" in message or "document" in message or "photo" in message or "audio" in message or "animation" in message:
                            db_msg_id = None
                            if DB_CHANNEL_ID:
                                db_msg_id = self.forward_to_channel(chat_id, message.get("message_id"))

                            if db_msg_id:
                                telegram_link = f"https://t.me/private_media_db_bot?start=msg_{db_msg_id}"
                                reply_text = f"✅ **Media Berhasil Disimpan!**\n\n🔗 **Link Akses:**\n{telegram_link}"
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
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self.call_telegram_api(url, payload)

    def answer_callback_query(self, callback_query_id):
        url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
        payload = {"callback_query_id": callback_query_id}
        self.call_telegram_api(url, payload)

    def get_pagination_keyboard(self, current_page):
        # Membuat tombol navigasi mirip contoh (Tombol Atas: Prev, Info Hal, Next; Tombol Bawah: Angka 1-10)
        keyboard = []
        
        # Baris 1: Tombol Navigasi Utama
        row1 = [
            {"text": "◀️ Sebelumnya", "callback_data": f"page_{max(1, current_page-1)}"},
            {"text": f"📋 {current_page}/17", "callback_data": "info"},
            {"text": "Berikutnya ▶️", "callback_data": f"page_{min(17, current_page+1)}"}
        ]
        keyboard.append(row1)
        
        # Baris 2 s.d. 4: Tombol Angka Halaman (1 sampai 10 sebagai contoh)
        row_num1 = []
        for i in range(1, 6):
            btn_text = f"❄️{i}" if i == current_page else str(i)
            row_num1.append({"text": btn_text, "callback_data": f"page_{i}"})
        keyboard.append(row_num1)

        row_num2 = []
        for i in range(6, 11):
            btn_text = f"❄️{i}" if i == current_page else str(i)
            row_num2.append({"text": btn_text, "callback_data": f"page_{i}"})
        keyboard.append(row_num2)

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
