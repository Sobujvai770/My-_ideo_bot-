import os
import telebot
from telebot import types

# আপনার বটের টেলিগ্রাম টোকেন এখানে বসাবেন
bot = telebot.TeleBot('8787602161:AAE_yFcsB2TiEY9LnlrVrF-Pom8ld5L8jCY')

VIDEOS_DB = {
    "v1": {
        "video_url": "https://files.catbox.moe/xxxxxx.mp4", 
        "caption": "🎬 সেই একটা মাল দুধ গুলো দেখার মতন ভিডিও\n\n⏱️ এক ঘণ্টা পর অটোমেটিক ভিডিওটি ডিলিট হয়ে যাবে।"
    }
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    command_args = message.text.split()
    if len(command_args) > 1:
        vid_code = command_args[1]
        if vid_code in VIDEOS_DB:
            v_data = VIDEOS_DB[vid_code]
            
            markup = types.InlineKeyboardMarkup()
            markup.row(
                types.InlineKeyboardButton("📢 Main Channel", url="https://t.me/+rLjXcZr21B45MWQ1"),
                types.InlineKeyboardButton("📂 All Channel", url="https://t.me/your_all_channel")
            )
            
            bot.send_video(message.chat.id, v_data["video_url"], caption=v_data["caption"], reply_markup=markup)
            return

    web_app_url = "https://sobujvai770.github.io/My-_ideo_bot-/" # আপনার মিনি অ্যাপের লিংক
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎬 Watch Now (Web App)", web_app=types.WebAppInfo(url=web_app_url)))
    
    welcome_text = (
        "🔥 স্বাগতম প্রিমিয়াম এক্সক্লুসিভ জোনে! 🔥\n\n"
        "🤫 আপনার কাঙ্ক্ষিত ভিডিওগুলোর আনলিমিটেড অ্যাক্সেস এখন আপনার হাতের মুঠোয়!\n\n"
        "👇 দেরি না করে নিচের মেনু থেকে অ্যাপটি ওপেন করুন! 👇"
    )
    
    banner_img = "https://files.catbox.moe/apifn2.jpeg"
    bot.send_photo(message.chat.id, banner_img, caption=welcome_text, reply_markup=markup)

print("Bot is running...")
bot.infinity_polling()
