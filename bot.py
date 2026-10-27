import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Token Bot Telegram kamu sudah dipasang di sini dengan benar
TOKEN = "8915561167:AAHF6Wnk2KL47dlx-eRdmkXUVZJJdf-8BwI"

dp = Dispatcher()

DATABASE_ARSIP = {}
ACTIVE_SESSIONS = {}


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
  args = message.text.split()
  if len(args) > 1 and args[1] in DATABASE_ARSIP:
    code = args[1]
    data = DATABASE_ARSIP[code]
    vid_count = len(data["videos"])
    img_count = len(data["images"])
    total = vid_count + img_count

    text = (
        f"📂 **#Arsip_{code}**\n\n"
        f"📖 **Informasi Konten:**\n"
        f"• Gambar: {img_count} buah\n"
        f"• Video: {vid_count} buah\n"
        f"• Total Berkas: {total}"
    )

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text=f"🎞️ Video ({vid_count})", callback_data=f"vid_{code}"
        ),
        types.InlineKeyboardButton(
            text=f"🖼️ Gambar ({img_count})", callback_data=f"img_{code}"
        ),
    )
    builder.row(
        types.InlineKeyboardButton(
            text=f"📦 Semua Dapatkan ({total})", callback_data=f"all_{code}"
        )
    )

    await message.answer(
        text, reply_markup=builder.as_markup(), parse_mode="Markdown"
    )
  else:
    await message.answer(
        "Halo! Bot arsip siap digunakan. Kirim perintah `/buat <kode>` untuk"
        " mulai mengunggah arsip."
    )


@dp.message(Command("buat"))
async def cmd_buat(message: types.Message):
  args = message.text.split()
  if len(args) < 2:
    await message.answer(
        "Format salah! Gunakan: `/buat <kode_arsip>` (Contoh: `/buat arsip_01`)"
    )
    return

  code = args[1]
  ACTIVE_SESSIONS[message.from_user.id] = code
  DATABASE_ARSIP[code] = {"videos": [], "images": []}
  await message.answer(
      f"✅ Sesi arsip **{code}** aktif!\nSilakan *forward* ratusan foto dan"
      " video sekaligus ke chat ini. Jika sudah selesai, ketik `/selesai`."
  )


@dp.message(Command("selesai"))
async def cmd_selesai(message: types.Message):
  user_id = message.from_user.id
  if user_id in ACTIVE_SESSIONS:
    code = ACTIVE_SESSIONS[user_id]
    del ACTIVE_SESSIONS[user_id]
    vid_count = len(DATABASE_ARSIP[code]["videos"])
    img_count = len(DATABASE_ARSIP[code]["images"])
    await message.answer(
        f"🎉 Sesi arsip **{code}** disimpan!\nTotal tersimpan: {vid_count}"
        f" Video dan {img_count} Gambar.\nLink akses kamu:"
        f" `t.me/Secretcollection_bot?start={code}`",
        parse_mode="Markdown",
    )
  else:
    await message.answer("Kamu sedang tidak dalam sesi pembuatan arsip.")


@dp.message()
async def handle_media(message: types.Message):
  user_id = message.from_user.id
  if user_id in ACTIVE_SESSIONS:
    code = ACTIVE_SESSIONS[user_id]

    if message.video:
      DATABASE_ARSIP[code]["videos"].append(message.video.file_id)
    elif message.photo:
      DATABASE_ARSIP[code]["images"].append(message.photo[-1].file_id)


@dp.callback_query(F.data.startswith(("vid_", "img_", "all_")))
async def callback_media(callback: types.CallbackQuery):
  action, code = callback.data.split("_", 1)
  if code not in DATABASE_ARSIP:
    await callback.answer("Arsip tidak ditemukan.", show_alert=True)
    return

  data = DATABASE_ARSIP[code]

  if action == "vid":
    await callback.message.answer(
        f"Mengirim {len(data['videos'])} video dari arsip {code}..."
    )
    for file_id in data["videos"]:
      await callback.message.answer_video(file_id)
  elif action == "img":
    await callback.message.answer(
        f"Mengirim {len(data['images'])} gambar dari arsip {code}..."
    )
    for file_id in data["images"]:
      await callback.message.answer_photo(file_id)
  elif action == "all":
    await callback.message.answer(
        f"Mengirim seluruh berkas dari arsip {code}..."
    )
    for file_id in data["videos"]:
      await callback.message.answer_video(file_id)
    for file_id in data["images"]:
      await callback.message.answer_photo(file_id)

  await callback.answer()


async def main():
  bot = Bot(token=TOKEN)
  await dp.start_polling(bot)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO, stream=sys.stdout)
  asyncio.run(main())
