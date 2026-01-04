import os
import re
from threading import Thread
from urllib.parse import urlparse
from pyrogram import Client, filters
from pyrogram.types import Message
import yt_dlp
import json

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

app = Client("eva_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

ARCHIVE_DIR = "user_archives"
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# ---------- دوال مساعدة ----------
def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]',"", s)

def get_user_folder(user_id):
    folder = os.path.join(ARCHIVE_DIR, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

def save_to_archive(user_id, file_path, url, quality_text):
    folder = get_user_folder(user_id)
    base_name = os.path.basename(file_path)
    archive_path = os.path.join(folder, base_name)
    os.rename(file_path, archive_path)
    history_file = os.path.join(folder, "history.json")
    if os.path.exists(history_file):
        with open(history_file,"r") as f:
            history = json.load(f)
    else:
        history = []
    history.append({"url": url, "file": base_name, "quality": quality_text})
    if len(history) > 50:
        history.pop(0)
    with open(history_file,"w") as f:
        json.dump(history,f, indent=2)
    return archive_path

# ---------- سجل روابط + الانتظار للجودة ----------
pending_links = {}  # user_id : url

# ---------- أوامر ----------
@app.on_message(filters.command("start"))
def start_message(client, message: Message):
    message.reply_text(
        "يا هلا بيك مع إيفا 🌸\n"
        "ابعتلي أي رابط فيديو من TikTok / Instagram / YouTube Shorts / Twitter/X\n"
        "رح أرسل لك خيارات الجودة بعد ما أشوف الرابط 😎"
    )

@app.on_message(filters.command("help"))
def help_message(client, message: Message):
    message.reply_text(
        "أوامر إيفا:\n"
        "1️⃣ /start - ترحيب بالبداية\n"
        "2️⃣ /help - قائمة الأوامر\n"
        "3️⃣ أرسل أي رابط فيديو لاختيار الجودة وتحميله\n"
        "4️⃣ بعد استلام نص الخيارات، أرسل رقم الجودة اللي تحبها"
    )

# ---------- استقبال الروابط ----------
@app.on_message(filters.regex(r"https?://"))
def handle_link(client, message: Message):
    url = message.text.strip()
    user_id = message.from_user.id
    pending_links[user_id] = url

    # إرسال خيارات الجودة كنص
    text = (
        f"تمام! شفت الرابط 🔥\n{url}\n"
        "اختر رقم الجودة اللي تحبها:\n"
        "1️⃣ فيديو 4K\n"
        "2️⃣ فيديو 1080p\n"
        "3️⃣ فيديو 720p\n"
        "4️⃣ صوت فقط\n"
        "5️⃣ نسخة صغيرة"
    )
    message.reply_text(text)

# ---------- استقبال رقم الجودة ----------
@app.on_message(filters.regex(r"^[1-5]$"))
def handle_quality_choice(client, message: Message):
    user_id = message.from_user.id
    if user_id not in pending_links:
        return message.reply_text("مافيش رابط مرتبط بالرقم ده 😅 ابعتلي رابط أولًا.")

    choice = int(message.text.strip())
    url = pending_links.pop(user_id)
    status_msg = message.reply_text("تمام، جاري التحميل... ⏳")
    os.makedirs("downloads", exist_ok=True)

    # تحديد الجودة
    if choice == 1:
        ydl_format = "bestvideo[height<=2160]+bestaudio/best"
        quality_text = "4K"
    elif choice == 2:
        ydl_format = "bestvideo[height<=1080]+bestaudio/best"
        quality_text = "1080p"
    elif choice == 3:
        ydl_format = "bestvideo[height<=720]+bestaudio/best"
        quality_text = "720p"
    elif choice == 4:
        ydl_format = "bestaudio/best"
        quality_text = "Audio"
    elif choice == 5:
        ydl_format = "worst[ext=mp4]/worst"
        quality_text = "Small"

    ydl_opts = {
        "quiet": True,
        "noplaylist": False,
        "outtmpl": f"downloads/{user_id}_%(upload_date)s_%(title)s.%(ext)s"
    }

    if choice == 4:
        ydl_opts["postprocessors"] = [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
    else:
        ydl_opts["format"] = ydl_format

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
                if choice == 4:
                    file_path = file_path.rsplit(".",1)[0] + ".mp3"
                archive_file = save_to_archive(user_id, file_path, url, quality_text)
                client.send_document(message.chat.id, archive_file)
                message.reply_text("تم التحميل والإرسال وحفظ الأرشيف! 😎🔥")
        except Exception as e:
            message.reply_text(f"يا خو، حصل خطأ 😓\n{e}")

    Thread(target=download).start()

# ---------- تشغيل البوت ----------
print("إيفا جاهزة للعمل مع اختيار الجودة بالنص! 🔥")
app.run()
# ---------- أمر /history ----------
@app.on_message(filters.command("history"))
def show_history(client, message: Message):
    user_id = message.from_user.id
    folder = get_user_folder(user_id)
    history_file = os.path.join(folder, "history.json")
    if not os.path.exists(history_file):
        return message.reply_text("مافيش أي تحميلات محفوظة عندك 😅")

    with open(history_file,"r") as f:
        history = json.load(f)

    text = "آخر التحميلات عندك:\n\n"
    for idx, item in enumerate(history[::-1], 1):
        text += (
            f"{idx}. {item['file']}\n"
            f"   الجودة: {item['quality']}\n"
            f"   الرابط: {item['url']}\n\n"
        )
    message.reply_text(text)
@app.on_message(filters.regex(r"https?://"))
def handle_link(client, message: Message):
    urls = re.findall(r"https?://\S+", message.text)
    user_id = message.from_user.id

    if not urls:
        return

    pending_links[user_id] = urls  # تخزين كل الروابط مؤقتاً

    # إرسال خيارات الجودة لكل رابط
    for idx, url in enumerate(urls, 1):
        text = (
            f"🔹 الرابط رقم {idx}:\n{url}\n"
            "اختر رقم الجودة اللي تحبها:\n"
            "1️⃣ فيديو 4K\n"
            "2️⃣ فيديو 1080p\n"
            "3️⃣ فيديو 720p\n"
            "4️⃣ صوت فقط\n"
            "5️⃣ نسخة صغيرة"
        )
        message.reply_text(text)
