import os
import threading
import time
import telebot
from telebot import types
from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB কানেকশন সেটআপ (Render-এর Environment Variable থেকে নিবে)
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
        res = jsonify({
            "total_users": total_users,
            "total_videos": total_videos
        })
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        return jsonify({"total_users": 0, "total_videos": 0}), 200

@app.route('/api/get-videos', methods=['GET'])
def get_videos():
    try:
        all_videos = list(videos_collection.find({}, {"_id": 0}))
        # ডাটাবেজ থেকে রিভার্স করে পাঠানো যাতে নতুন ভিডিও উপরে থাকে
        videos_dict = {v["id"]: v for v in reversed(all_videos)}
        res = jsonify(videos_dict)
        res.headers.add("Access-Control-Allow-Origin", "*")
        return res, 200
    except Exception as e:
        res = jsonify({})
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

        # MongoDB-তে আপসর্ট (না থাকলে ইনসার্ট হবে, থাকলে আপডেট হবে)
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

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8787602161:AAHYC1CU5DAmwAa6Lv64VeZNhoUKdL_YLDY")
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    # MongoDB-তে ইউজার সেভ করা
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({"user_id": user_id})

    command_args = message.text.split()
    
    if len(command_args) > 1:
        vid_key = str(command_args[1]).strip()
        v_data = videos_collection.find_one({"id": vid_key})
        
        if v_data:
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
                
                # শুধু ইউজারের ইনবক্স থেকে ২ ঘণ্টা (৭২০০ সেকেন্ড) পর মেসেজটি ডিলিট হবে (ওয়েব অ্যাপের হাবের ডাটা অপরিবর্তিত থাকবে)
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
            bot.send_message(message.chat.id, "⚠️ দুঃখিত! এই ভিডিওটির ডেটা সার্ভারে পাওয়া যায়নি।")
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
