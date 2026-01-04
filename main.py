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
import re
from urllib.parse import urlparse

def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]',"", s)

@app.on_callback_query()
def handle_buttons(client, callback):
    data = callback.data
    action, url = data.split("|")
    callback.message.reply_text("تمام، جاري التحميل... ⏳")

    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "quiet": True,
        "noplaylist": True,
        "outtmpl": "downloads/%(title)s.%(ext)s"
    }

    if action == "video":
        ydl_opts["format"] = "best[ext=mp4]/best"
        ydl_opts["postprocessors"] = []
        # TikTok watermark removal
        if "tiktok.com" in urlparse(url).netloc:
            ydl_opts["postprocessors"].append({"key":"RemoveWatermark"})
    elif action == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    elif action == "small":
        ydl_opts["format"] = "worst[ext=mp4]/worst"

    def download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
                file_path = sanitize_filename(file_path)
                if action == "audio":
                    file_path = file_path.rsplit(".", 1)[0] + ".mp3"
                client.send_document(callback.message.chat.id, file_path)
                os.remove(file_path)
                client.send_message(callback.message.chat.id, "تم التحميل والإرسال! 😎✅")
        except Exception as e:
            client.send_message(callback.message.chat.id, f"يا خو، حصل خطأ أثناء التحميل 😓\n{e}")

    Thread(target=download).start()
@app.on_message(filters.regex(r"https?://"))
def handle_link(client, message: Message):
    url = message.text.strip()
    message.reply_text(
        f"تمام! شفت الرابط 🔥\n{url}\nاختار نوع التحميل والجودة:", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 فيديو 4K", callback_data=f"video4k|{url}")],
            [InlineKeyboardButton("🎬 فيديو 1080p", callback_data=f"video1080|{url}")],
            [InlineKeyboardButton("🎬 فيديو 720p", callback_data=f"video720|{url}")],
            [InlineKeyboardButton("🎵 صوت فقط", callback_data=f"audio|{url}")],
            [InlineKeyboardButton("💾 نسخة صغيرة", callback_data=f"small|{url}")]
        ])
    )

@app.on_callback_query()
def handle_buttons(client, callback):
    data = callback.data
    action, url = data.split("|")
    callback.message.reply_text("تمام، جاري التحميل... ⏳")

    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {"quiet": True, "noplaylist": True, "outtmpl": "downloads/%(title)s.%(ext)s"}

    if action.startswith("video"):
        ydl_opts["format"] = {
            "video4k": "bestvideo[height<=2160]+bestaudio/best",
            "video1080": "bestvideo[height<=1080]+bestaudio/best",
            "video720": "bestvideo[height<=720]+bestaudio/best"
        }[action]
        ydl_opts["postprocessors"] = []
        if "tiktok.com" in urlparse(url).netloc:
            ydl_opts["postprocessors"].append({"key":"RemoveWatermark"})
    elif action == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key": "FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    elif action == "small":
        ydl_opts["format"] = "worst[ext=mp4]/worst"

    def download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = sanitize_filename(ydl.prepare_filename(info))
                if action == "audio":
                    file_path = file_path.rsplit(".", 1)[0] + ".mp3"
                # إشعارات التقدم
                callback.message.reply_text("✅ التحميل اكتمل، جاري الإرسال...")
                client.send_document(callback.message.chat.id, file_path)
                os.remove(file_path)
                client.send_message(callback.message.chat.id, "تم التحميل والإرسال! 😎🔥")
        except Exception as e:
            client.send_message(callback.message.chat.id, f"يا خو، حصل خطأ 😓\n{e}")

    Thread(target=download).start()
import time
import json

# سجل آخر 50 رابط لكل مستخدم
user_history = {}

def save_history(user_id, url):
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(url)
    if len(user_history[user_id]) > 50:
        user_history[user_id].pop(0)

@app.on_callback_query()
def handle_buttons(client, callback):
    data = callback.data
    action, url = data.split("|")
    user_id = callback.from_user.id
    save_history(user_id, url)

    status_msg = callback.message.reply_text("تمام، جاري التحميل... ⏳")

    os.makedirs("downloads", exist_ok=True)
    ydl_opts = {"quiet": True, "noplaylist": False, "outtmpl": "downloads/%(uploader)s_%(upload_date)s_%(title)s.%(ext)s"}

    # تحديد الصيغة والجودة
    if action.startswith("video"):
        ydl_opts["format"] = {
            "video4k": "bestvideo[height<=2160]+bestaudio/best",
            "video1080": "bestvideo[height<=1080]+bestaudio/best",
            "video720": "bestvideo[height<=720]+bestaudio/best"
        }[action]
    elif action == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    elif action == "small":
        ydl_opts["format"] = "worst[ext=mp4]/worst"

    # إشعارات تقدم التحميل
    def progress(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip()
            status_msg.edit_text(f"🔹 جاري التحميل... {percent}")

    ydl_opts["progress_hooks"] = [progress]

    def download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = sanitize_filename(ydl.prepare_filename(info))
                if action == "audio":
                    file_path = file_path.rsplit(".",1)[0] + ".mp3"
                client.send_document(callback.message.chat.id, file_path)
                os.remove(file_path)
                callback.message.reply_text("تم التحميل والإرسال! 😎🔥")
        except Exception as e:
            callback.message.reply_text(f"يا خو، حصل خطأ 😓\n{e}")

    Thread(target=download).start()
import os
import re
import asyncio
from threading import Thread
from urllib.parse import urlparse
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

app = Client("eva_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# سجل المستخدمين
user_history = {}

def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]',"", s)

def save_history(user_id, url):
    if user_id not in user_history:
        user_history[user_id] = []
    user_history[user_id].append(url)
    if len(user_history[user_id]) > 50:
        user_history[user_id].pop(0)

# ---------- أوامر البوت ----------
@app.on_message(filters.command("start"))
def start_message(client, message: Message):
    message.reply_text(
        "يا هلا بيك مع إيفا 🌸\n"
        "أنا جاهزة لتحميل الفيديوهات والصوتيات من TikTok وInstagram وYouTube Shorts وTwitter/X بأعلى جودة 😎\n"
        "جرب ابعتلي أي رابط فيديو أو صوت!"
    )

@app.on_message(filters.command("help"))
def help_message(client, message: Message):
    message.reply_text(
        "أوامر ايفا:\n"
        "1️⃣ /start - رسالة الترحيب\n"
        "2️⃣ /help - قائمة الأوامر\n"
        "3️⃣ أرسل أي رابط فيديو لتحميله فورًا"
    )

# ---------- استقبال الروابط ----------
@app.on_message(filters.regex(r"https?://"))
def handle_link(client, message: Message):
    url = message.text.strip()
    save_history(message.from_user.id, url)
    message.reply_text(
        f"تمام! شفت الرابط 🔥\n{url}\nاختار نوع التحميل والجودة:", 
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎬 فيديو 4K", callback_data=f"video4k|{url}")],
            [InlineKeyboardButton("🎬 فيديو 1080p", callback_data=f"video1080|{url}")],
            [InlineKeyboardButton("🎬 فيديو 720p", callback_data=f"video720|{url}")],
            [InlineKeyboardButton("🎵 صوت فقط", callback_data=f"audio|{url}")],
            [InlineKeyboardButton("💾 نسخة صغيرة", callback_data=f"small|{url}")]
        ])
    )

# ---------- التعامل مع الأزرار ----------
@app.on_callback_query()
def handle_buttons(client, callback):
    data = callback.data
    action, url = data.split("|")
    user_id = callback.from_user.id
    save_history(user_id, url)

    status_msg = callback.message.reply_text("تمام، جاري التحميل... ⏳")

    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "quiet": True,
        "noplaylist": False,
        "outtmpl": "downloads/%(uploader)s_%(upload_date)s_%(title)s.%(ext)s"
    }

    if action.startswith("video"):
        ydl_opts["format"] = {
            "video4k": "bestvideo[height<=2160]+bestaudio/best",
            "video1080": "bestvideo[height<=1080]+bestaudio/best",
            "video720": "bestvideo[height<=720]+bestaudio/best"
        }[action]
        ydl_opts["postprocessors"] = []
        if "tiktok.com" in urlparse(url).netloc:
            ydl_opts["postprocessors"].append({"key":"RemoveWatermark"})
    elif action == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    elif action == "small":
        ydl_opts["format"] = "worst[ext=mp4]/worst"

    def progress(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str','').strip()
            status_msg.edit_text(f"🔹 جاري التحميل... {percent}")

    ydl_opts["progress_hooks"] = [progress]

    def download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = sanitize_filename(ydl.prepare_filename(info))
                if action == "audio":
                    file_path = file_path.rsplit(".",1)[0] + ".mp3"
                client.send_document(callback.message.chat.id, file_path)
                os.remove(file_path)
                callback.message.reply_text("تم التحميل والإرسال! 😎🔥")
        except Exception as e:
            callback.message.reply_text(f"يا خو، حصل خطأ 😓\n{e}")

    Thread(target=download).start()

# ---------- تشغيل البوت ----------
print("إيفا جاهزة للعمل! 🔥")
app.run()
from flask import Flask, request, render_template_string, send_file

web_app = Flask("eva_web")

HTML_PAGE = """
<!doctype html>
<html>
<head>
<title>Eva Downloader</title>
</head>
<body>
<h2>إيفا 🌸 - تحميل الفيديوهات</h2>
<form action="/" method="post">
    <label>أدخل الرابط:</label><br>
    <input type="text" name="url" style="width:400px"><br><br>
    <label>اختر نوع التحميل:</label><br>
    <select name="action">
        <option value="video4k">🎬 فيديو 4K</option>
        <option value="video1080">🎬 فيديو 1080p</option>
        <option value="video720">🎬 فيديو 720p</option>
        <option value="audio">🎵 صوت فقط</option>
        <option value="small">💾 نسخة صغيرة</option>
    </select><br><br>
    <input type="submit" value="تحميل">
</form>
</body>
</html>
"""

@web_app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        url = request.form["url"].strip()
        action = request.form["action"]

        os.makedirs("downloads", exist_ok=True)
        ydl_opts = {
            "quiet": True,
            "noplaylist": False,
            "outtmpl": "downloads/%(uploader)s_%(upload_date)s_%(title)s.%(ext)s"
        }

        if action.startswith("video"):
            ydl_opts["format"] = {
                "video4k": "bestvideo[height<=2160]+bestaudio/best",
                "video1080": "bestvideo[height<=1080]+bestaudio/best",
                "video720": "bestvideo[height<=720]+bestaudio/best"
            }[action]
        elif action == "audio":
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
        elif action == "small":
            ydl_opts["format"] = "worst[ext=mp4]/worst"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = sanitize_filename(ydl.prepare_filename(info))
                if action == "audio":
                    file_path = file_path.rsplit(".",1)[0] + ".mp3"
                return send_file(file_path, as_attachment=True)
        except Exception as e:
            return f"حصل خطأ 😓: {e}"

    return render_template_string(HTML_PAGE)

# ---------- تشغيل البوت والويب معًا ----------
def run_web():
    web_app.run(host="0.0.0.0", port=3000)

Thread(target=run_web).start()
print("إيفا جاهزة للعمل على Telegram وWeb 🔥")
app.run()
import json

ARCHIVE_DIR = "user_archives"
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def get_user_folder(user_id):
    folder = os.path.join(ARCHIVE_DIR, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

def save_to_archive(user_id, file_path, url):
    folder = get_user_folder(user_id)
    # حفظ الملف في مجلد المستخدم
    base_name = os.path.basename(file_path)
    archive_path = os.path.join(folder, base_name)
    os.rename(file_path, archive_path)
    # تحديث سجل الروابط
    history_file = os.path.join(folder, "history.json")
    if os.path.exists(history_file):
        with open(history_file,"r") as f:
            history = json.load(f)
    else:
        history = []
    history.append({"url": url, "file": base_name})
    if len(history) > 50:
        history.pop(0)
    with open(history_file,"w") as f:
        json.dump(history,f, indent=2)
    return archive_path

# تعديل وظيفة التحميل Telegram
def download_telegram(client, callback, action, url):
    user_id = callback.from_user.id
    status_msg = callback.message.reply_text("تمام، جاري التحميل... ⏳")
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {"quiet": True, "noplaylist": False, "outtmpl": "downloads/%(uploader)s_%(upload_date)s_%(title)s.%(ext)s"}

    if action.startswith("video"):
        ydl_opts["format"] = {
            "video4k": "bestvideo[height<=2160]+bestaudio/best",
            "video1080": "bestvideo[height<=1080]+bestaudio/best",
            "video720": "bestvideo[height<=720]+bestaudio/best"
        }[action]
        ydl_opts["postprocessors"] = []
        if "tiktok.com" in urlparse(url).netloc:
            ydl_opts["postprocessors"].append({"key":"RemoveWatermark"})
    elif action == "audio":
        ydl_opts["format"] = "bestaudio/best"
        ydl_opts["postprocessors"] = [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    elif action == "small":
        ydl_opts["format"] = "worst[ext=mp4]/worst"

    def progress(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str','').strip()
            status_msg.edit_text(f"🔹 جاري التحميل... {percent}")

    ydl_opts["progress_hooks"] = [progress]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = sanitize_filename(ydl.prepare_filename(info))
            if action == "audio":
                file_path = file_path.rsplit(".",1)[0] + ".mp3"
            # حفظ الأرشيف لكل مستخدم
            archive_file = save_to_archive(user_id, file_path, url)
            client.send_document(callback.message.chat.id, archive_file)
            callback.message.reply_text("تم التحميل والإرسال وحفظ الأرشيف! 😎🔥")
    except Exception as e:
        callback.message.reply_text(f"يا خو، حصل خطأ 😓\n{e}")

# تعديل callback handler
@app.on_callback_query()
def handle_buttons(client, callback):
    data = callback.data
    action, url = data.split("|")
    Thread(target=download_telegram, args=(client, callback, action, url)).start()
