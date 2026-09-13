import os
import json
import threading
import telebot
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS

# ফ্লাস্ক সার্ভার এবং CORS ইনিশিয়ালাইজ করা (যাতে ওয়েব অ্যাপ থেকে রিকোয়েস্ট ব্লক না হয়)
app = Flask(__name__)
CORS(app)

DB_FILE = "videos.json"

# ডেটাবেজ লোড করার ফাংশন
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

# ডেটাবেজ সেভ করার ফাংশন
def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return "Bot and API are running and alive!"

# --- এডমিন প্যানেল থেকে ভিডিও সেভ করার API ---
@app.route('/api/save-video', methods=['POST'])
def save_video():
    try:
        req_data = request.json
        v_code = req_data.get("code")  # যেমন: v1, v2
        file_id = req_data.get("file_id") # টেলিগ্রাম ভিডিও file_id
        caption = req_data.get("caption", "🔥 প্রিমিয়াম ভিডিও!")
        ad_link = req_data.get("ad_link", "")
        thumb_link = req_data.get("thumb_link", "")

        if not v_code or not file_id:
            return jsonify({"status": "error", "message": "Code and File ID are required!"}), 400

        db = load_db()
        db[v_code] = {
            "video_file_id": file_id,
            "caption": caption,
            "ad_link": ad_link,
            "thumb_link": thumb_link
        }
        save_db(db)

        return jsonify({"status": "success", "message": f"Video {v_code} saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# আপনার বটের টেলিগ্রাম টোকেন
bot = telebot.TeleBot('8787602161:AAE_yFcsB2TiEY9LnlrVrF-Pom8ld5L8jCY')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    command_args = message.text.split()
    db = load_db()
    
    if len(command_args) > 1:
        vid_code = command_args[1]
        if vid_code in db:
            v_data = db[vid_code]
            
            markup = types.InlineKeyboardMarkup()
            # যদি অ্যাডস্টেরা লিংক থাকে, তবে সেটা বাটনে যুক্ত হবে
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
    bot.infinity_polling()

if __name__ == "__main__":
    web_thread = threading.Thread(target=run_web)
    web_thread.start()
    
    run_bot()
