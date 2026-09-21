Import os
import threading
import time
import telebot
from telebot import types
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get("MONGO_URI", "your_mongodb_connection_string_here")
client = MongoClient(MONGO_URI)
db = client["my_video_bot_db"]
videos_collection = db["videos"]
users_collection = db["users"]

@app.route('/')
def home():
    return "Bot and MongoDB API are running and alive!"

@app.route('/api/bot-stats', methods=['GET'])
def bot_stats():
    try:
        total_users = users_collection.count_documents({})
        total_videos = videos_collection.count_documents({})
        
        ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
        live_users = users_collection.count_documents({"last_active": {"$gte": ten_minutes_ago}})

        res = jsonify({
            "total_users": total_users,
            "live_users": live_users,
            "total_videos": total_videos
        })
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        res = jsonify({"total_users": 0, "live_users": 0, "total_videos": 0})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200

# পেজিনেশন সহ ভিডিও ফেচ করার আপডেট রুট (প্রতি পেজে ২০টি করে)
@app.route('/api/get-videos', methods=['GET'])
def get_videos():
    try:
        page = int(request.args.get('page', 1))
        per_page = 20
        
        all_videos = list(videos_collection.find({}, {"_id": 0}))
        all_videos.reverse() # নতুন ভিডিওগুলো আগে দেখানোর জন্য
        
        total_videos = len(all_videos)
        total_pages = (total_videos + per_page - 1) // per_page if total_videos > 0 else 1
        
        start = (page - 1) * per_page
        end = start + per_page
        current_videos_list = all_videos[start:end]
        
        # ফ্রন্টএন্ডের সুবিধার জন্য ডিকশনারি বা অবজেক্ট ফরম্যাটে রূপান্তর
        videos_dict = {v["id"]: v for v in current_videos_list}

        res = jsonify({
            "videos": videos_dict,
            "current_page": page,
            "total_pages": total_pages,
            "total_videos": total_videos
        })
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        res = jsonify({"videos": {}, "current_page": 1, "total_pages": 1, "total_videos": 0})
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

        video_doc = {
            "id": video_id,
            "video_file_id": file_id,
            "caption": caption,
            "ad_link": ad_link,
            "thumb_link": thumb_link,
            "parts": parts
        }

        videos_collection.update_one({"id": video_id}, {"$set": video_doc}, upsert=True)

        res = jsonify({"status": "success", "message": "Video saved to MongoDB successfully!"})
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
        result = videos_collection.delete_one({"id": video_id})
        if result.deleted_count > 0:
            res = jsonify({"status": "success", "message": "Video deleted successfully!"})
        else:
            res = jsonify({"status": "error", "message": "Video not found!"})
        
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        res = jsonify({"status": "error", "message": str(e)})
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 500

@app.route('/api/broadcast', methods=['POST', 'OPTIONS'])
def broadcast_api():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'OK'})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    try:
        req_data = request.json
        broadcast_text = req_data.get("message")

        if not broadcast_text:
            res = jsonify({"status": "error", "message": "Message is required!"})
            res.headers.add("Access-Control-Allow-Origin", "*")
            return res, 400

        unique_user_ids = users_collection.distinct("user_id")
        sent_count = 0

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎬 Open Video / Watch Now", web_app=types.WebAppInfo(url=WEB_APP_URL)))

        for uid in unique_user_ids:
            try:
                bot.send_message(uid, broadcast_text, reply_markup=markup)
                sent_count += 1
                time.sleep(0.05)
            except Exception as e:
                pass

        res = jsonify({"status": "success", "sent": sent_count})
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

ADMIN_TELEGRAM_IDS = [8326665891, 8518594452]
WEB_APP_URL = "https://sobujvai770.github.io/My-_ideo_bot-/"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"last_active": datetime.utcnow()}},
        upsert=True
    )

    command_args = message.text.split()
    
    if len(command_args) > 1:
        vid_key = str(command_args[1]).strip()
        # ডাটাবেজ থেকে ভিডিও খুঁজে বের করা (দুটি ফিল্ড ফরম্যাট চেক করা হচ্ছে যেন মিস না হয়)
        v_data = videos_collection.find_one({"id": vid_key})
        if not v_data:
            v_data = videos_collection.find_one({"video_file_id": vid_key})
        
        if v_data:
            markup = types.InlineKeyboardMarkup()
            markup.row(types.InlineKeyboardButton("🎬 Watch Full Video / Sponsor", url=v_data.get("ad_link", "https://t.me/")))
            markup.row(types.InlineKeyboardButton("📢 Main Channel", callback_data="main_channel_info"))
            
            try:
                full_caption = f"{v_data.get('caption', '🔥 প্রিমিয়াম ভিডিও!')}\n\n⏳ ২ ঘণ্টা পর আপনার ইনবক্স থেকে ভিডিওটি অটোমেটিক ডিলিট হয়ে যাবে।"
                file_to_send = v_data.get("video_file_id") or v_data.get("file_id")
                
                sent_msg = bot.send_video(
                    message.chat.id, 
                    file_to_send, 
                    caption=full_caption, 
                    reply_markup=markup
                )
                
                def delete_later(chat_id, msg_id):
                    time.sleep(7200)
                    try:
                        bot.delete_message(chat_id, msg_id)
                    except:
                        pass
                
                threading.Thread(target=delete_later, args=(message.chat.id, sent_msg.message_id)).start()

            except Exception as e:
                bot.send_message(message.chat.id, f"⚠️ ভিডিও পাঠাতে সমস্যা হয়েছে: {str(e)}")
            return
        else:
            bot.send_message(message.chat.id, "⚠️ দুঃখিত! এই ভিডিওটির ডেটা সার্ভারে পাওয়া যায়নি।")
            return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Watch Now (Web App)", web_app=types.WebAppInfo(url=WEB_APP_URL)))
    
    welcome_text = (
        "🔥 স্বাগতম প্রিমিয়াম এক্সক্লুসিভ জোনে! 🔥\n\n"
        "🤫 আপনার কাঙ্ক্ষিত ভিডিওগুলোর আনলিমিটেড অ্যাক্সেস এখন আপনার হাতের মুঠোয়!\n\n"
        "👇 দেরি না করে নিচের মেনু থেকে অ্যাপটি ওপেন করুন! 👇"
    )
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.from_user.id
    if user_id not in ADMIN_TELEGRAM_IDS:
        bot.reply_to(message, "⚠️ আপনার ব্রডকাস্ট করার অনুমতি নেই!")
        return

    text_parts = message.text.split(maxsplit=1)
    if len(text_parts) < 2:
        bot.reply_to(message, "⚠️ সঠিক নিয়মে দিন। যেমন:\n`/broadcast আপনার ঘোষণা এখানে লিখুন`", parse_mode="Markdown")
        return

    broadcast_text = text_parts[1]
    unique_user_ids = users_collection.distinct("user_id")
    
    sent_count = 0
    failed_count = 0

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Open Video / Watch Now", web_app=types.WebAppInfo(url=WEB_APP_URL)))

    for uid in unique_user_ids:
        try:
            bot.send_message(uid, broadcast_text, reply_markup=markup)
            sent_count += 1
            time.sleep(0.05)
        except Exception as e:
            failed_count += 1

    bot.reply_to(message, f"✅ ব্রডকাস্ট সম্পন্ন হয়েছে!\n\nসফলভাবে গেছে: {sent_count} জন\nব্যর্থ হয়েছে: {failed_count} জন")

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
    print("Bot is running with MongoDB...")
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
