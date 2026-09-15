import os
import json
import threading
import time
import telebot
from telebot import types
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_FILE = "videos.json"
USERS_FILE = "users.json"

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

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

@app.route('/')
def home():
    return "Bot and API are running and alive!"

@app.route('/api/bot-stats', methods=['GET'])
def bot_stats():
    users = load_users()
    db = load_db()
    res = jsonify({
        "total_users": len(users),
        "total_videos": len(db)
    })
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res, 200

@app.route('/api/get-videos', methods=['GET'])
def get_videos():
    db = load_db()
    res = jsonify(db)
    res.headers.add("Access-Control-Allow-Origin", "*")
    return res, 200

@app.route('/api/save-video', methods=['POST', 'OPTIONS'])
def save_video():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, DELETE")
        return response

    try:
        req_data = request.json
        video_id = str(req_data.get("id")).strip()
        file_id = req_data.get("file_id")
        caption = req_data.get("caption", "🔥 প্রিমিয়াম ভিডিও!")
        ad_link = req_data.get("ad_link", "")
        thumb_link = req_data.get("thumb_link", "")
        parts = req_data.get("parts", "2 Parts")

        if not video_id or not file_id:
            res = jsonify({"status": "error", "message": "Video ID and File ID are required!"})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 400

        db = load_db()
        db[video_id] = {
            "video_file_id": file_id,
            "caption": caption,
            "ad_link": ad_link,
            "thumb_link": thumb_link,
            "parts": parts
        }
        save_db(db)

        res = jsonify({"status": "success", "message": "Video saved successfully!"})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        res = jsonify({"status": "error", "message": str(e)})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 500

@app.route('/api/delete-video/<video_id>', methods=['DELETE', 'OPTIONS'])
def delete_video(video_id):
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "DELETE")
        return response

    try:
        db = load_db()
        if video_id in db:
            del db[video_id]
            save_db(db)
            res = jsonify({"status": "success", "message": "Video deleted successfully!"})
        else:
            res = jsonify({"status": "error", "message": "Video not found!"})
        
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        res = jsonify({"status": "error", "message": str(e)})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 500

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8787602161:AAHYC1CU5DAmwAa6Lv64VeZNhoUKdL_YLDY")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users = load_users()
    
    if user_id not in users:
        users.append(user_id)
        save_users(users)

    command_args = message.text.split()
    db = load_db()
    
    if len(command_args) > 1:
        vid_key = str(command_args[1]).strip()
        if vid_key in db:
            v_data = db[vid_key]
            
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🎬 Watch Full Video / Sponsor", url=v_data.get("ad_link", "https://t.me/")))
            markup.row(types.InlineKeyboardButton("📢 Main Channel", callback_data="main_channel_info"))
            
            try:
                full_caption = f"{v_data.get('caption', '🔥 প্রিমিয়াম ভিডিও!')}\n\n⏳ ২ ঘণ্টা পর আপনার ইনবক্স থেকে ভিডিওটি অটোমেটিক ডিলিট হয়ে যাবে।"
                sent_msg = bot.send_video(
                    message.chat.id, 
                    v_data["video_file_id"], 
                    caption=full_caption, 
                    reply_markup=markup
                )
                
                # শুধু ইউজারের ইনবক্স থেকে ২ ঘণ্টা (৭২০০ সেকেন্ড) পর ডিলিট হওয়ার থ্রেড
                def delete_later(chat_id, msg_id):
                    time.sleep(7200)
                    try:
                        bot.delete_message(chat_id, msg_id)
                    except:
                        pass
                
                threading.Thread(target=delete_later, args=(message.chat.id, sent_msg.message_id)).start()

            except Exception as e:
                bot.send_message(message.chat.id, "⚠️ ভিডিও পাঠাতে সমস্যা হয়েছে বা ফাইল আইডি ভুল আছে।")
            return
        else:
            bot.send_message(message.chat.id, "⚠️ দুঃখিত! এই ভিডিওটির ডেটা সার্ভারে পাওয়া যায়নি বা ডিলিট হয়ে গেছে।")
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

@bot.callback_query_handler(func=lambda call: call.data == "main_channel_info")
def callback_main_channel(call):
    bot.answer_callback_query(call.id, "📢 এটি আমাদের অফিসিয়াল চ্যানেল!", show_alert=True)

@bot.message_handler(content_types=['video', 'document'])
def get_video_id(message):
    try:
        if message.video:
            vid_file_id = message.video.file_id
            bot.reply_to(message, f"✅ এই ভিডিওর File ID হলো:\n\n`{vid_file_id}`", parse_mode="Markdown")
        elif message.document and 'video' in message.document.mime_type:
            doc_file_id = message.document.file_id
            bot.reply_to(message, f"✅ এই ভিডিও (Document) ফাইল আইডি হলো:\n\n`{doc_file_id}`", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ ফাইল আইডি পেতে সমস্যা হয়েছে: {str(e)}")

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
