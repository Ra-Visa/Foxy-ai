import os
import sys
import math
import time
import tempfile
import asyncio
import threading
from flask import Flask
import telebot
from telebot import types

# ---------------------------------------------------------
# 0. MoviePy & FFmpeg Safe Imports
# ---------------------------------------------------------
try:
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ffmpeg_dir = os.path.dirname(ffmpeg_exe)
    if ffmpeg_dir not in os.environ["PATH"]:
        os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
except Exception:
    pass

import whisper
import edge_tts
import translators as ts

try:
    import moviepy.editor as mp
    VideoFileClip = mp.VideoFileClip
    AudioFileClip = mp.AudioFileClip
    CompositeAudioClip = mp.CompositeAudioClip
except Exception:
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.AudioClip import CompositeAudioClip

# ---------------------------------------------------------
# 1. FLASK MINI SERVER FOR KEEP-ALIVE
# ---------------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 FOXY AI TELEGRAM BOT IS ALIVE & RUNNING 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# រត់ Flask Web Server លើ Thread ផ្សេងដើម្បីទទួល Ping ពី UptimeRobot
threading.Thread(target=run_flask, daemon=True).start()

# ---------------------------------------------------------
# 2. BOT CONFIGURATION & ADMIN SETUP
# ---------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
ADMIN_IDS = [6936728139]  # Admin ID

bot = telebot.TeleBot(BOT_TOKEN)

# In-Memory Databases
user_settings = {}
registered_users = set()  # រក្សាទុក User IDs សម្រាប់ Broadcast
broadcast_mode = set()     # រក្សាទុក Admin ID ដែលកំពុងស្ថិតក្នុង Broadcast Mode

def get_user_config(user_id):
    registered_users.add(user_id)
    if user_id not in user_settings:
        user_settings[user_id] = {
            "lang": "zh",                  # 'zh' (ចិន) ឬ 'en' (អង់គ្លេស)
            "voice": "km-KH-PisethNeural", # 'km-KH-PisethNeural' ឬ 'km-KH-SreymomNeural'
            "split": True                  # កាត់ជាភាគ (< 2min) ឬ អត់
        }
    return user_settings[user_id]

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS (TTS & TRANSLATION)
# ---------------------------------------------------------
def generate_edge_tts_safe(text, voice_name, output_path):
    async def _tts():
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(output_path)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_tts())
    finally:
        loop.close()

def translate_free_fallback(text, src_lang="zh"):
    engines = ['google', 'bing', 'alibaba']
    for engine in engines:
        try:
            result = ts.translate_text(text, translator=engine, from_language=src_lang, to_language='km')
            if result:
                return result
        except Exception:
            pass
    raise RuntimeError("មិនអាចភ្ជាប់ទៅកាន់ Translation Server បានឡើយ!")

# ---------------------------------------------------------
# 4. ADMIN PANEL COMMANDS
# ---------------------------------------------------------
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id not in ADMIN_IDS:
        bot.reply_to(message, "❌ អ្នកគ្មានសិទ្ធិចូលប្រើប្រាស់ Admin Panel ឡើយ!")
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_stats = types.InlineKeyboardButton("📊 ស្ថិតិប្រើប្រាស់", callback_data="admin_stats")
    btn_broadcast = types.InlineKeyboardButton("📢 ផ្ញើសារប្រកាស (Broadcast)", callback_data="admin_broadcast")
    markup.add(btn_stats, btn_broadcast)

    admin_text = (
        "👑 **FOXY AI - ADMIN CONTROL PANEL**\n\n"
        f"• Admin ID: `{message.chat.id}`\n"
        f"• ចំនួនអ្នកប្រើប្រាស់សរុប: `{len(registered_users)}` នាក់"
    )
    bot.send_message(message.chat.id, admin_text, reply_markup=markup, parse_mode="Markdown")

# ---------------------------------------------------------
# 5. USER COMMANDS & SETTINGS
# ---------------------------------------------------------
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    get_user_config(message.chat.id)
    welcome_text = (
        "🦊 **ស្វាគមន៍មកកាន់ FOXY AI DUBBING BOT**\n\n"
        "សូមផ្ញើ **Video (MP4/MKV)** ដែលមានសំឡេងចិន ឬអង់គ្លេស មកកាន់ Bot នេះដើម្បីសម្រាយ និងបកប្រែជាភាសាខ្មែរស្វ័យប្រវត្តិ!\n\n"
        "⚙️ ចុច /settings ដើម្បីកំណត់ភាសា សំឡេង និងការកាត់វីដេអូ"
    )
    if message.chat.id in ADMIN_IDS:
        welcome_text += "\n\n👑 អ្នកគឺជា Admin! ប្រើបញ្ជា /admin ដើម្បីបើក Admin Panel"
        
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['settings'])
def settings_menu(message):
    cfg = get_user_config(message.chat.id)
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    lang_btn_text = "🌐 ភាសាដើម៖ " + ("🇨🇳 ចិន" if cfg['lang'] == 'zh' else "🇺🇸 អង់គ្លេស")
    voice_btn_text = "🎙️ សំឡេង AI៖ " + ("ប្រុស (Piseth)" if "Piseth" in cfg['voice'] else "ស្រី (Sreymom)")
    split_btn_text = "✂️ កាត់បំបែកភាគ (< 2 នាទី)៖ " + ("បើក (ON)" if cfg['split'] else "បិទ (OFF)")
    
    markup.add(
        types.InlineKeyboardButton(lang_btn_text, callback_data="toggle_lang"),
        types.InlineKeyboardButton(voice_btn_text, callback_data="toggle_voice"),
        types.InlineKeyboardButton(split_btn_text, callback_data="toggle_split")
    )
    
    bot.send_message(message.chat.id, "⚙️ **ការកំណត់ (Settings):**", reply_markup=markup, parse_mode="Markdown")

# ---------------------------------------------------------
# 6. CALLBACK QUERY HANDLER (BUTTONS)
# ---------------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.message.chat.id
    cfg = get_user_config(user_id)
    
    # Settings callbacks
    if call.data == "toggle_lang":
        cfg['lang'] = "en" if cfg['lang'] == "zh" else "zh"
        bot.answer_callback_query(call.id, "បានផ្លាស់ប្តូរភាសា!")
        settings_menu(call.message)
    elif call.data == "toggle_voice":
        cfg['voice'] = "km-KH-SreymomNeural" if "Piseth" in cfg['voice'] else "km-KH-PisethNeural"
        bot.answer_callback_query(call.id, "បានផ្លាស់ប្តូរសំឡេង AI!")
        settings_menu(call.message)
    elif call.data == "toggle_split":
        cfg['split'] = not cfg['split']
        bot.answer_callback_query(call.id, "បានផ្លាស់ប្តូរការកាត់វីដេអូ!")
        settings_menu(call.message)
        
    # Admin Panel callbacks
    elif call.data == "admin_stats":
        if user_id in ADMIN_IDS:
            stats_msg = (
                "📊 **ស្ថិតិប្រព័ន្ធ (System Stats):**\n\n"
                f"👤 អ្នកប្រើប្រាស់សរុប: `{len(registered_users)}`\n"
                f"⚙️ គណនីមាន Settings active: `{len(user_settings)}`"
            )
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, stats_msg, parse_mode="Markdown")
            
    elif call.data == "admin_broadcast":
        if user_id in ADMIN_IDS:
            broadcast_mode.add(user_id)
            bot.answer_callback_query(call.id)
            bot.send_message(user_id, "📢 **សូមផ្ញើសារ/រូបភាព ឬវីដេអូ ដែលអ្នកចង់ Broadcast ទៅកាន់គ្រប់ User ទាំងអស់៖**")

# ---------------------------------------------------------
# 7. BROADCAST & VIDEO PROCESSING
# ---------------------------------------------------------
@bot.message_handler(func=lambda m: m.chat.id in broadcast_mode, content_types=['text', 'photo', 'video'])
def handle_broadcast_message(message):
    admin_id = message.chat.id
    broadcast_mode.remove(admin_id)
    
    count = 0
    bot.send_message(admin_id, f"⏳ កំពុងផ្ញើសារទៅកាន់អ្នកប្រើប្រាស់ {len(registered_users)} នាក់...")
    
    for uid in registered_users:
        try:
            bot.copy_message(chat_id=uid, from_chat_id=admin_id, message_id=message.message_id)
            count += 1
            time.sleep(0.05)
        except Exception:
            pass
            
    bot.send_message(admin_id, f"✅ បានផ្ញើសារប្រកាសជោគជ័យទៅកាន់អ្នកប្រើប្រាស់ {count} នាក់!")

@bot.message_handler(content_types=['video', 'document'])
def handle_video(message):
    user_id = message.chat.id
    cfg = get_user_config(user_id)
    
    file_info = None
    if message.content_type == 'video':
        file_info = bot.get_file(message.video.file_id)
    elif message.content_type == 'document' and message.document.mime_type and message.document.mime_type.startswith('video/'):
        file_info = bot.get_file(message.document.file_id)
    else:
        bot.reply_to(message, "⚠️ សូមផ្ញើជា File វីដេអូត្រឹមត្រូវ (Video File)!")
        return

    status_msg = bot.reply_to(message, "⏳ [1/5] កំពុងទាញយកវីដេអូពី Telegram...")

    with tempfile.TemporaryDirectory() as temp_dir:
        video_input_path = os.path.join(temp_dir, "input_video.mp4")
        
        downloaded_file = bot.download_file(file_info.file_path)
        with open(video_input_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        try:
            # 1. Transcribe (Whisper AI)
            lang_name = "ចិន" if cfg['lang'] == 'zh' else "អង់គ្លេស"
            bot.edit_message_text(f"⏳ [2/5] [Whisper AI] កំពុងស្រង់សំឡេងភាសា{lang_name}...", chat_id=user_id, message_id=status_msg.message_id)
            
            # ប្រើ model 'tiny' ដើម្បើសន្សំ Memory លើ Cloud
            model = whisper.load_model("tiny")
            stt_result = model.transcribe(video_input_path, language=cfg['lang'], fp16=False)
            source_script = stt_result["text"]

            if not source_script.strip():
                bot.edit_message_text("❌ រកមិនឃើញសំឡេងនិយាយនៅក្នុងវីដេអូនេះទេ!", chat_id=user_id, message_id=status_msg.message_id)
                return

            # 2. Translate
            bot.edit_message_text("⏳ [3/5] កំពុងបកប្រែជាភាសាខ្មែរ...", chat_id=user_id, message_id=status_msg.message_id)
            khmer_script = translate_free_fallback(source_script, src_lang=cfg['lang'])

            # 3. Generate Voice
            bot.edit_message_text("⏳ [4/5] កំពុងបង្កើតសំឡេង AI ខ្មែរ...", chat_id=user_id, message_id=status_msg.message_id)
            khmer_audio_path = os.path.join(temp_dir, "khmer_audio.mp3")
            generate_edge_tts_safe(khmer_script, cfg['voice'], khmer_audio_path)

            # 4. Render Video
            bot.edit_message_text("⏳ [5/5] កំពុង Render វីដេអូ...", chat_id=user_id, message_id=status_msg.message_id)
            full_video = VideoFileClip(video_input_path)
            full_audio = AudioFileClip(khmer_audio_path)

            video_duration = full_video.duration
            audio_duration = full_audio.duration

            if audio_duration < video_duration:
                final_audio = CompositeAudioClip([full_audio.set_start(0)]).set_duration(video_duration)
            else:
                final_audio = full_audio.subclip(0, video_duration)

            if hasattr(full_video, "with_audio"):
                final_full_clip = full_video.with_audio(final_audio)
            else:
                final_full_clip = full_video.set_audio(final_audio)

            max_part_duration = 115.0
            
            if cfg['split'] and video_duration > max_part_duration:
                num_parts = math.ceil(video_duration / max_part_duration)
                bot.edit_message_text(f"✂️ វីដេអូវែង! កំពុងកាត់បំបែកជា {num_parts} ភាគ...", chat_id=user_id, message_id=status_msg.message_id)

                for i in range(num_parts):
                    start_time = i * max_part_duration
                    end_time = min((i + 1) * max_part_duration, video_duration)
                    part_out = os.path.join(temp_dir, f"Foxy_Part_{i+1}.mp4")

                    sub_clip = final_full_clip.subclipped(start_time, end_time) if hasattr(final_full_clip, "subclipped") else final_full_clip.subclip(start_time, end_time)
                    sub_clip.write_videofile(part_out, codec="libx264", audio_codec="aac", threads=4, preset="ultrafast", logger=None)
                    sub_clip.close()

                    with open(part_out, 'rb') as v_file:
                        bot.send_video(user_id, v_file, caption=f"🎬 FOXY AI - ភាគ {i+1}/{num_parts}")
            else:
                part_out = os.path.join(temp_dir, "Foxy_Full_Video.mp4")
                final_full_clip.write_videofile(part_out, codec="libx264", audio_codec="aac", threads=4, preset="ultrafast", logger=None)

                with open(part_out, 'rb') as v_file:
                    bot.send_video(user_id, v_file, caption="🎉 វីដេអូសម្រាយរួចរាល់ 100%!")

            full_video.close()
            full_audio.close()
            bot.delete_message(chat_id=user_id, message_id=status_msg.message_id)

        except Exception as e:
            bot.edit_message_text(f"❌ មានកំហុសកើតឡើង៖ {str(e)}", chat_id=user_id, message_id=status_msg.message_id)

# ---------------------------------------------------------
# 8. START BOT POLLING
# ---------------------------------------------------------
if __name__ == "__main__":
    print("🤖 Telegram Bot ត្រូវបានចាប់ផ្តើមដំណើរការ (Polling) ជាមួយ Keep-Alive Server...")
    bot.infinity_polling()
