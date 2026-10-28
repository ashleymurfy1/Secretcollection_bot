import os
import json
from http.server import BaseHTTPRequestHandler
import urllib.request
import random

TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
BOT_USERNAME = "Secretcllctn_bot"
# ID Channel Database yang baru
DATABASE_CHAT_ID = -4351284345

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if post_data:
                update = json.loads(post_data.decode('utf-8'))
                
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
                                f"📂 Sedang memuat file untuk kode: `{payload_code}`..."
                            )
                        else:
                            self.send_telegram_message(
                                chat_id, 
                                "Halo! Kirimkan video atau foto ke sini untuk disimpan dan dibuatkan link-nya."
                            )
                    elif any(k in message for k in ["video", "document", "photo", "audio", "animation"]):
                        media_name = "Media"
                        if "video" in message:
                            media_name = "Video"
                        elif "photo" in message:
                            media_name = "Foto"
                        elif "document" in message:
                            media_name = "Dokumen"
                        
                        # Forward media ke Channel Database
                        forward_url = f"https://api.telegram.org/bot{TOKEN}/forwardMessage"
                        forward_payload = {
                            "chat_id": DATABASE_CHAT_ID,
                            "from_chat_id": chat_id,
                            "message_id": message["message_id"]
                        }
                        
                        res_ok, res_desc = self.call_telegram_api(forward_url, forward_payload)
                        
                        if res_ok:
                            random_code = f"file_{random.randint(100000, 999999)}"
                            telegram_link = f"https://t.me/{BOT_USERNAME}?start={random_code}"
                            
                            reply_text = (
                                f"✅ **{media_name} berhasil disimpan ke database!**\n\n"
                                f"🔗 **Link Akses Bot:**\n"
                                f"{telegram_link}"
                            )
                        else:
                            reply_text = f"⚠️ Gagal menyimpan ke database.\nError: {res_desc}"
                            
                        self.send_telegram_message(chat_id, reply_text)
                    else:
                        if chat_id != DATABASE_CHAT_ID:
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
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        self.call_telegram_api(url, payload)

    def call_telegram_api(self, url, payload):
        if not TOKEN:
            return False, "Token kosong"
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            return result.get("ok", False), ""
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"Telegram API HTTP Error: {error_body}")
            return False, error_body
        except Exception as e:
            print(f"Telegram API Error: {e}")
            return False, str(e)
