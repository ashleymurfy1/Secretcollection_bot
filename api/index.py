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
                        page_num = int(data.replace("page_", ""))
                        # Ambil total file (simulasi dari ID database terakhir atau data tersimpan)
                        total_files = self.get_total_files_count()
                        total_pages = max(1, (total_files + 9) // 10) # 10 file per halaman
                        
                        self.send_telegram_message(
                            chat_id, 
                            f"📄 Menampilkan Halaman {page_num} dari {total_pages}\nTotal koleksi: {total_files} file.",
                            reply_markup=self.get_pagination_keyboard(page_num, total_pages)
                        )
                    self.answer_callback_query(callback["id"])
                    
                # Menangani Pesan Teks / Media biasa
                else:
                    message = update.get("message") or update.get("edited_message")
                    if message and "chat" in message:
                        chat_id = message["chat"]["id"]
                        text = message.get("text", "") or message.get("caption", "")
                        
                        if text.startswith("/start"):
                            # Hitung total file dinamis
                            total_files = self.get_total_files_count()
                            total_pages = max(1, (total_files + 9) // 10)
                            
                            welcome_text = (
                                "📁 **#KoleksiMedia**\n\n"
                                "📖 **Informasi Statistik:**\n"
                                f"• 📦 Total File: {total_files} buah\n\n"
                                "Silakan pilih halaman di bawah untuk melihat isi koleksi:"
                            )
                            self.send_telegram_message(
                                chat_id, 
                                welcome_text, 
                                reply_markup=self.get_pagination_keyboard(1, total_pages)
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

    def get_total_files_count(self):
        # Mengecek ID pesan terakhir di channel database untuk mengetahui jumlah total file secara dinamis
        url = f"https://api.telegram.org/bot{TOKEN}/getChat"
        payload = {"chat_id": DB_CHANNEL_ID}
        res = self.call_telegram_api(url, payload)
        if res and res.get("ok"):
            # Perkiraan jumlah file berdasarkan ID pesan terakhir di channel
            # Atau fallback ke angka default jika channel privat ketat
            return res.get("result", {}).get("pinned_message", {}).get("message_id", 35)
        return 35 # Angka default jika belum ada pin

    def send_telegram_message(self, chat_id, text, reply_markup=None):
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        self.call_telegram_api(url, payload)

    def answer_callback_query(self, callback_query_id):
