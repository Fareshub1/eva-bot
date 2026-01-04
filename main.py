import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

import yt_dlp
import os
from threading import Thread

# ---------------- إعدادات البوت ----------------
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

app = Client("eva_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# ---------------- أوامر أساسية ----------------
@app.on_message(filters.command("start"))
def start_message(client, message: Message):
    message.reply_text(
        "يا هلا بيك مع إيفا 🌸\n"
        "أنا جاهزة لتحميل الفيديوهات والصوتيات من TikTok وInstagram بأعلى جودة 😎\n"
        "جرب ابعتلي أي رابط فيديو أو صوت!"
    )

@app.on_message(filters.command("help"))
def help_message(client, message: Message):
    message.reply_text(
        "أوامر ايفا:\n"
        "1️⃣ /start - رسالة الترحيب\n"
        "2️⃣ /help - قائمة الأوامر\n"
        "3️⃣ أرسل أي رابط TikTok أو Instagram لتحميله فورًا"
    )

# ---------------- استقبال الروابط ----------------
@app.on_message(filters.regex(r"https?://"))
def handle_link(client, message: Message):
    url = message.text.strip()
    status_msg = message.reply_text(f"تمام! شفت الرابط، جاري التحميل 🔥\n{url}")

    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "merge_output_format": None
    }

    def download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                # إرسال الملف
                client.send_document(message.chat.id, file_path)
                os.remove(file_path)
                client.send_message(message.chat.id, "تم التحميل والإرسال! 😎✅")
        except Exception as e:
            client.send_message(message.chat.id, f"يا خو، حصل خطأ أثناء التحميل 😓\n{e}")

    Thread(target=download).start()

# ---------------- تشغيل البوت ----------------
print("إيفا جاهزة للعمل! 🔥")
app.run()
