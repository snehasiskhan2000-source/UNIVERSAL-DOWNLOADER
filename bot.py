import os
import time
import threading
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync  # <--- NEW: Stealth import
import yt_dlp

# --- FLASK SERVER FOR UPTIMEROBOT ---
app = Flask(__name__)

@app.route('/')
def keep_alive():
    return "Bot is awake and running!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- TELEGRAM BOT LOGIC ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN") 
bot = telebot.TeleBot(BOT_TOKEN)

def get_bottom_menu():
    """Generates the bottom menu buttons for the UI."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Help"), KeyboardButton("Status"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Send Me Website Link🙌", reply_markup=get_bottom_menu())

@bot.message_handler(func=lambda msg: msg.text in ["Help", "Status"])
def handle_menu(message):
    if message.text == "Help":
        bot.reply_to(message, "Send any URL. I will run a script to automate the website process, sniff the network for .mp4 or .m3u8 streams, and download them for you.")
    elif message.text == "Status":
        bot.reply_to(message, "Bot is currently running on Render!")

@bot.message_handler(func=lambda message: message.text.startswith('http'))
def process_link(message):
    url = message.text
    status_msg = bot.reply_to(message, "⏳ Bypassing security and sniffing network... Please wait.")
    
    media_links = set()

    def handle_request(request):
        # Sniffing for the specific formats
        if ".mp4" in request.url or ".m3u8" in request.url:
            media_links.add(request.url)

    # 1. Sniffing Phase
    try:
        with sync_playwright() as p:
            # Added more args to ensure absolute stability on cloud hosts
            browser = p.chromium.launch(
                headless=True, 
                args=[
                    '--no-sandbox', 
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu'
                ]
            )
            page = browser.new_page()
            
            # --- NEW: Apply Stealth Mode ---
            stealth_sync(page)
            
            page.on("request", handle_request)
            
            # --- FIXED TIMEOUT & WAIT CONDITION ---
            # Changed from 'networkidle' (which times out if ads keep loading) to 'domcontentloaded'
            # Increased timeout to 60 seconds (60000ms)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Give background scripts a few seconds to trigger the media requests after DOM is ready
            time.sleep(5) 
            browser.close()
            
    except Exception as e:
        bot.edit_message_text(f"❌ Failed to load page: {str(e)[:100]}", chat_id=message.chat.id, message_id=status_msg.message_id)
        return

    if not media_links:
        bot.edit_message_text("⚠️ No .mp4 or .m3u8 streaming links found on this page.", chat_id=message.chat.id, message_id=status_msg.message_id)
        return

    bot.edit_message_text(f"✅ Found {len(media_links)} streaming link(s). Starting downloads...", chat_id=message.chat.id, message_id=status_msg.message_id)

    # 2. Downloading & Sending Phase
    for link in list(media_links)[:3]:
        bot.send_message(message.chat.id, "📥 Processing stream...")
        download_and_send(link, message.chat.id)

def download_and_send(media_url, chat_id):
    ydl_opts = {
        'outtmpl': 'video_%(id)s.%(ext)s',
        'format': 'best',
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(media_url, download=True)
            filename = ydl.prepare_filename(info)
        
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        
        if file_size_mb > 50:
            bot.send_message(chat_id, f"❌ File is {file_size_mb:.1f}MB. Telegram bots cannot send files larger than 50MB natively.")
        else:
            with open(filename, 'rb') as video_file:
                bot.send_video(chat_id, video_file)
        
        os.remove(filename)
        
    except Exception as e:
        bot.send_message(chat_id, f"❌ Download failed for a link.")
        if os.path.exists('video_*'): 
             os.system('rm video_*')

if __name__ == "__main__":
    threading.Thread(target=run_server).start()
    bot.infinity_polling()
