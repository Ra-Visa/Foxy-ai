import os
import threading
import time
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)

# បង្កើត folder សម្រាប់ទុក file ទាញយកបណ្តោះអាសន្ន
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==========================================
# 2. FLASK KEEP-ALIVE SERVER (FOR RENDER)
# ==========================================
@app.route('/')
def home():
    return "Foxy Media Downloader Bot is Running Live!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ==========================================
# 3. TELEGRAM BOT HANDLERS
# ==========================================
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🦊 **សួស្តី! ខ្ញុំជា Foxy Media Downloader Bot**\n\n"
        "សូមផ្ញើ Link វីដេអូ (YouTube, TikTok, Facebook, Reels, -etc.) មកកាន់ខ្ញុំ "
        "ដើម្បីទាញយកជា MP3 ឬ MP4 តាមតម្រូវការ!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text and message.text.startswith(("http://", "https://")))
def handle_link(message):
    # បង្កើតប៊ូតុងជ្រើសរើស (MP3 ឬ MP4)
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🎵 MP3 (Audio)", callback_data=f"mp3|{message.chat.id}"),
        InlineKeyboardButton("🎬 MP4 (Video)", callback_data=f"mp4|{message.chat.id}")
    )
    
    bot.reply_to(message, "🎬 **សូមជ្រើសរើសប្រភេទ Format ដែលអ្នកចង់ទាញយក៖**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith(("mp3|", "mp4|")))
def callback_download(call):
    format_type, chat_id = call.data.split("|")
    url = call.message.reply_to_message.text.strip() if call.message.reply_to_message else None
    
    if not url:
        bot.answer_callback_query(call.id, "❌ រកមិនឃើញ Link ឡើយ! សូមផ្ញើ Link ឡើងវិញ។")
        return

    bot.answer_callback_query(call.id, "⏳ កំពុងចាប់ផ្តើមទាញយក...")
    status_msg = bot.send_message(call.message.chat.id, "⏳ **កំពុង Download... សូមរង់ចាំបន្តិច!**", parse_mode="Markdown")

    file_path = None
    try:
        if format_type == "mp3":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True
            }
        else:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
                'quiet': True
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == "mp3":
                file_path = os.path.splitext(filename)[0] + ".mp3"
            else:
                file_path = filename

        bot.edit_message_text("📤 **កំពុង Upload ចូល Telegram...**", chat_id=call.message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

        # ផ្ញើ File ទៅកាន់ User
        with open(file_path, 'rb') as media_file:
            if format_type == "mp3":
                bot.send_audio(call.message.chat.id, media_file, caption="✅ ទាញយកបានជោគជ័យដោយ Foxy Bot!")
            else:
                bot.send_video(call.message.chat.id, media_file, caption="✅ ទាញយកបានជោគជ័យដោយ Foxy Bot!")

        bot.delete_message(call.message.chat.id, status_msg.message_id)

    except Exception as e:
        bot.edit_message_text(f"❌ **មានបញ្ហាក្នុងការទាញយក៖** {str(e)}", chat_id=call.message.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")

    finally:
        # លុប File បន្ទាប់ពី Upload រួចដើម្បីកុំឱ្យពេញ Disk
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

# ==========================================
        
