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
                    
                    # Cek Force Subscription
                    unsubscribed_channels = self.get_unsubscribed_channels(user_id)
                    if unsubscribed_channels:
                        # Daftar link channel yang sesuai dengan urutan
                        channel_links = {
                            "-1002814282563": "https://t.me/secretlokal",
                            "-1003941525945": "https://t.me/BACKUPSCRT1",
                            "-1003911556352": "https://t.me/BACKUPSCRT",
                            "-1002438175955": "https://t.me/secretclctn"
                        }
                        
                        inline_keyboard = []
                        for idx, ch in enumerate(unsubscribed_channels, 1):
                            # Ambil link publik, atau fallback ke t.me/c/ jika tidak terdaftar
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
                        if len(parts) > 1 and parts[1].startswith("batch_"):
                            batch_key = parts[1]
                            msg_ids = ALBUM_STORAGE.get(batch_key, [])
                            
                            if msg_ids:
                                self.send_telegram_message(chat_id, f"📦 Mengirim {len(msg_ids)} media satu persatu dengan aman...")
                                for db_msg_id in msg_ids:
                                    self.copy_from_channel(chat_id, db_msg_id)
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
                        
                        db_msg_id = None
                        if DB_CHANNEL_ID:
                            db_msg_id = self.forward_to_channel(chat_id, message.get("message_id"))

                        if db_msg_id:
                            if media_group_id:
                                batch_key = f"batch_{str(media_group_id)[:10]}"
                                if batch_key not in ALBUM_STORAGE:
                                    ALBUM_STORAGE[batch_key] = []
                                
                                if db_msg_id not in ALBUM_STORAGE[batch_key]:
                                    ALBUM_STORAGE[batch_key].append(db_msg_id)
                                
                                telegram_link = "https://t.me/private_media_db_bot?start=" + batch_key
                                
                                if len(ALBUM_STORAGE[batch_key]) == 1:
                                    reply_text = "✅ Album Media Berhasil Disimpan!\n\n🔗 1 Link untuk Semua Media:\n" + telegram_link
                                    self.send_telegram_message(chat_id, reply_text)
                            else:
                                telegram_link = "https://t.me/private_media_db_bot?start=msg_" + str(db_msg_id)
                                reply_text = "✅ Media Berhasil Disimpan!\n\n🔗 Link Akses:\n" + telegram_link
                                self.send_telegram_message(chat_id, reply_text)
                        
        except Exception as e:
            print(f"Error utama: {e}")

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
