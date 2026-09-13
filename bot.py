import os
import json
import threading
import time
import telebot
from telebot import types
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_FILE = "videos.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return "Bot and API are running and alive!"

@app.route('/api/save-video', methods=['POST', 'OPTIONS'])
def save_video():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    try:
        req_data = request.json
        video_id = str(req_data.get("id"))
        file_id = req_data.get("file_id")
        caption = req_data.get("caption", "🔥 প্রিমিয়াম ভিডিও!")
        ad_link = req_data.get("ad_link", "")
        thumb_link = req_data.get("thumb_link", "")

        if not video_id or not file_id:
            res = jsonify({"status": "error", "message": "Video ID and File ID are required!"})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 400

        db = load_db()
        db[video_id] = {
            "video_file_id": file_id,
            "caption": caption,
            "ad_link": ad_link,
            "thumb_link": thumb_link
        }
        save_db(db)

        res = jsonify({"status": "success", "message": "Video saved successfully!"})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        res = jsonify({"status": "error", "message": str(e)})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 500

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# নতুন টোকেন এখানে সেট করা হলো
BOT_TOKEN = '8787602161:AAEnBbGJxxukqXjIdeBYjD7oWUzLkT9vbJY'
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    command_args = message.text.split()
    db = load_db()
    
    if len(command_args) > 1:
        vid_key = command_args[1]
        if vid_key in db:
            v_data = db[vid_key]
            
            markup = types.InlineKeyboardMarkup()
            if v_data.get("ad_link"):
                markup.row(types.InlineKeyboardButton("🎬 Watch Full Video / Sponsor", url=v_data["ad_link"]))
            
            markup.row(
                types.InlineKeyboardButton("📢 Main Channel", url="https://t.me/+rLjXcZr21B45MWQ1")
            )
            
            bot.send_video(message.chat.id, v_data["video_file_id"], caption=v_data["caption"], reply_markup=markup)
            return

    web_app_url = "https://sobujvai770.github.io/My-_ideo_bot-/" 
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Watch Now (Web App)", web_app=types.WebAppInfo(url=web_app_url)))
    
    welcome_text = (
        "🔥 স্বাগতম প্রিমিয়াম এক্সক্লুসিভ জোনে! 🔥\n\n"
        "🤫 আপনার কাঙ্ক্ষিত ভিডিওগুলোর আনলিমিটেড অ্যাক্সেস এখন আপনার হাতের মুঠোয়!\n\n"
        "👇 দেরি না করে নিচের মেনু থেকে অ্যাপটি ওপেন করুন! 👇"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(content_types=['video'])
def get_video_id(message):
    vid_file_id = message.video.file_id
    bot.reply_to(message, f"এই ভিডিওর File ID হলো:\n\n`{vid_file_id}`", parse_mode="Markdown")

def run_bot():
    print("Bot is running...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=30)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.start()
    
    run_bot()
