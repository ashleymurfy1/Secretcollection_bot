def get_unsubscribed_channels(self, user_id):
        raw_channels = []
        # Cukup cek variabel 1 sampai 4 yang sudah kamu buat di Vercel
        keys_to_check = [
            "FORCE_SUB_CHANNEL_1", 
            "FORCE_SUB_CHANNEL_2", 
            "FORCE_SUB_CHANNEL_3", 
            "FORCE_SUB_CHANNEL_4"
        ]
        for key in keys_to_check:
            val = os.environ.get(key, "").strip()
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
