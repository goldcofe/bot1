import telebot
from telebot import types
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

# ================== تنظیمات ==================
TOKEN = os.getenv("TELEGRAM_TOKEN")
AI_API_KEY = os.getenv("AI_API_KEY")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN در فایل .env تنظیم نشده است!")

bot = telebot.TeleBot(TOKEN)

# ذخیره اطلاعات کاربران
user_data = {}      # مدل انتخابی + تاریخچه
user_favorites = {} # پرامپت‌های ذخیره شده

# ================== پرامپت سیستم متخصص ==================
SYSTEM_PROMPT = """تو یک Prompt Engineer حرفه‌ای و ارشد با تجربه بالا در مهندسی پرامپت برای Grok, GPT-4o, Claude 3.5 و Gemini هستی.

وظیفه تو نوشتن قوی‌ترین، دقیق‌ترین و بهینه‌ترین پرامپت ممکن بر اساس درخواست کاربر است.
از تکنیک‌های پیشرفته مانند:
- Role Prompting
- Chain of Thought (CoT)
- Few-Shot Prompting
- Output Formatting (JSON, Markdown, جدول و ...)
- Delimiters
- Constraints و Constraints
استفاده کن.

همیشه پاسخ را به صورت:
1. پرامپت آماده (در بلاک کد)
2. توضیح کوتاه تکنیک‌های استفاده شده
تحویل بده."""

# ================== تابع تولید پرامپت ==================
def generate_professional_prompt(user_request, model="gpt-4o"):
    try:
        import openai
        openai.api_key = AI_API_KEY
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"درخواست: {user_request}\n\nبهترین و حرفه‌ای‌ترین پرامپت ممکن را طراحی کن."}
        ]
        
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        return f"⚠️ خطا در اتصال به هوش مصنوعی:\n{str(e)}\n\nلطفاً بعداً امتحان کنید."


# ================== منوی اصلی ==================
def main_menu(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("✍️ پرامپت جدید", callback_data="new_prompt")
    btn2 = types.InlineKeyboardButton("❤️ favorites", callback_data="favorites")
    btn3 = types.InlineKeyboardButton("🔄 تغییر مدل", callback_data="change_model")
    btn4 = types.InlineKeyboardButton("🗑️ پاک کردن", callback_data="clear")
    
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(chat_id, "🎯 **منوی اصلی** بات پرامپت‌نویس حرفه‌ای", 
                     reply_markup=markup, parse_mode='Markdown')


# ================== هندلرها ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in user_data:
        user_data[user_id] = {"model": "gpt-4o", "history": []}
    if user_id not in user_favorites:
        user_favorites[user_id] = []
    
    welcome = """🚀 **بات پرامپت‌نویس حرفه‌ای** خوش آمدید!

من متخصص نوشتن پرامپت‌های سطح بالا هستم.
هر درخواستی داری بنویس، بهترین پرامپت رو برات طراحی می‌کنم."""

    bot.send_message(message.chat.id, welcome, parse_mode='Markdown')
    main_menu(message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    data = call.data

    if data == "new_prompt":
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "✅ درخواست خود را بنویسید یا پیام صوتی بفرستید:")

    elif data == "favorites":
        bot.answer_callback_query(call.id)
        favs = user_favorites.get(user_id, [])
        if not favs:
            bot.send_message(user_id, "❤️ هنوز هیچ پرامپتی ذخیره نکرده‌اید.")
        else:
            text = "❤️ **پرامپت‌های ذخیره شده:**\n\n"
            for i, fav in enumerate(favs[-10:], 1):  # آخرین ۱۰ تا
                text += f"{i}. {fav[:120]}...\n\n"
            bot.send_message(user_id, text)

    elif data == "change_model":
        markup = types.InlineKeyboardMarkup(row_width=1)
        models = ["gpt-4o", "grok-beta", "claude-3-5-sonnet-20240620", "gemini-1.5-pro"]
        for m in models:
            markup.add(types.InlineKeyboardButton(m, callback_data=f"set_model_{m}"))
        bot.send_message(user_id, "🔄 مدل هوش مصنوعی را انتخاب کنید:", reply_markup=markup)

    elif data.startswith("set_model_"):
        model = data.replace("set_model_", "")
        user_data[user_id]["model"] = model
        bot.answer_callback_query(call.id, f"✅ مدل تغییر کرد به: {model}")
        main_menu(user_id)

    elif data == "clear":
        user_data[user_id]["history"] = []
        bot.answer_callback_query(call.id, "🗑️ تاریخچه پاک شد.")
        main_menu(user_id)


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.chat.id
    bot.send_chat_action(user_id, 'typing')
    bot.reply_to(message, "🎤 در حال تبدیل صدا به متن...")

    # در Railway بهتر است از Whisper API استفاده شود (اینجا placeholder)
    text = "[متن تبدیل شده از پیام صوتی - برای نسخه کامل Whisper را اضافه کنید]"
    
    response = generate_professional_prompt(text, user_data[user_id]["model"])
    bot.reply_to(message, response, parse_mode='Markdown')


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.chat.id
    request = message.text.strip()
    
    if not request:
        return
    
    bot.send_chat_action(user_id, 'typing')
    
    response = generate_professional_prompt(request, user_data[user_id]["model"])
    
    # دکمه ذخیره
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❤️ ذخیره این پرامپت", callback_data="save_prompt"))
    
    bot.reply_to(message, response, parse_mode='Markdown', reply_markup=markup)
    
    # ذخیره در تاریخچه
    user_data[user_id]["history"].append({"request": request, "response": response})


# ذخیره پرامپت (ساده)
@bot.callback_query_handler(func=lambda call: call.data == "save_prompt")
def save_favorite(call):
    user_id = call.message.chat.id
    # در نسخه کامل می‌توان آخرین پاسخ را ذخیره کرد
    bot.answer_callback_query(call.id, "✅ پرامپت به لیست مورد علاقه‌ها اضافه شد!")
    # ذخیره واقعی را بعداً با دیتابیس کامل کنید


# ================== اجرای بات ==================
if __name__ == "__main__":
    print("🚀 بات پرامپت‌نویس حرفه‌ای راه‌اندازی شد...")
    bot.infinity_polling()
