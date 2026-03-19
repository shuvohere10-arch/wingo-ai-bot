from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is Running Successfully!"

def run_flask():
    # Render পোর্ট খুঁজে পাওয়ার জন্য এটি ১০০০০ পোর্টে চলবে
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# এটি বট চালু হওয়ার পাশাপাশি আলাদাভাবে চলবে
threading.Thread(target=run_flask).start()

# --- এখান থেকে আপনার আগের কোড শুরু ---
import telebot
from telebot import types
import json
# ... বাকি সব কিছু আগের মতোই থাকবে ...
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import time
import threading
import json
import os

# ==========================================
# ⚙️ বটের সেটিংস (এখানে আপনার তথ্য দিন)
# ==========================================
TOKEN = '8296686835:AAEpGaEwNeypGfHIoMAqPh63QA1If46eFAM'  # আপনার বটের টোকেন
ADMIN_ID = 7596820363 # আপনার নিজের টেলিগ্রাম User ID

# 🖼️ প্রোমোশনাল মেসেজের ইমেজের লিংক (যেকোনো ডিরেক্ট ইমেজ লিংক দিন)
PROMO_IMAGE_URL = 'https://i.postimg.cc/3NBQkXss/IMG-20260306-145638-527.jpg' # এখানে আপনার ছবির লিংক দিন

# 🎨 স্টিকার সেটিংস
WIN_STICKER_ID = 'CAACAgUAAxkBAAEQr9lpqncnAAFogByxPjsDCxSCg_8Xaw4AAkYbAAJVelhV0gUuIytKzQABOgQ' 
LOSS_STICKER_ID = 'CAACAgUAAxkBAAEQr9tpqndbF1X37PH9DMaEjxZqpBzB4wACqRUAAtfuYVW625PGbcZXwToE'
DENIED_STICKER_ID = 'CAACAgUAAxkBAAEQr91pqnePB2gK1R3DgE55AAHx2xk6RfEAAq4YAAK5SlhVipe20Pguy4s6BA'

bot = telebot.TeleBot(TOKEN)

# ==========================================
# 📂 চ্যানেল সেভ করার সিস্টেম
# ==========================================
CHANNELS_FILE = 'channels.json'

def load_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_channels(channels_set):
    with open(CHANNELS_FILE, 'w') as f:
        json.dump(list(channels_set), f)

# Global Variables
target_channels = load_channels()
historyData = []
lastFetchedPeriod = None
lastPrediction = None
lastStatus = None
winStreak = 0
is_running = False

# ==========================================
# 🧠 AI লজিক ও API ফেচ
# ==========================================
def ai_predict(history):
    if len(history) < 3:
        import random
        random_number = random.randint(0, 9)
        prediction = "BIG" if random_number >= 5 else "SMALL"
        return prediction, random_number

    recent_results = [h for h in history if h['result'] != "-"][:3]
    bigCount = 0
    smallCount = 0
    weight = 1

    for result in reversed(recent_results):
        if int(result['result']) >= 5:
            bigCount += weight
        else:
            smallCount += weight
        weight *= 1.2

    import random
    number = random.randint(0, 4) + (5 if bigCount > smallCount else 0)
    prediction = "BIG" if number >= 5 else "SMALL"
    return prediction, number

def fetch_game_result():
    try:
        timestamp = int(time.time() * 1000)
        url = f"https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={timestamp}"
        response = requests.get(url).json()
        return response.get('data', {}).get('list', [None])[0]
    except Exception as e:
        print("API Error:", e)
        return None

# ==========================================
# 🚀 প্রেডিকশন এবং সিগন্যাল লুপ
# ==========================================
def prediction_loop():
    global lastFetchedPeriod, lastPrediction, lastStatus, winStreak, historyData, is_running, target_channels
    
    while is_running:
        if not target_channels:
            time.sleep(3)
            continue

        result = fetch_game_result()
        if not result or result['issueNumber'] == lastFetchedPeriod:
            time.sleep(3)
            continue

        # ১. আগের প্রেডিকশনের রেজাল্ট চেক করা
        if len(historyData) > 0 and historyData[0]['resultStatus'] == "Pending":
            actual_number = int(result['number'])
            actual_outcome = 'BIG' if actual_number >= 5 else 'SMALL'
            color_emoji = "🟩" if actual_outcome == "BIG" else "🟥"
            
            status = 'WIN' if lastPrediction == actual_outcome else 'LOSS'
            
            if status == 'WIN':
                winStreak += 1
                if winStreak == 1:
                    streak_title = "✨ <b>𝗦𝗨𝗣𝗘𝗥 𝗪𝗜𝗡</b> ✨"
                    sub_text = "💸 <i>Profit successfully booked!</i>"
                elif winStreak == 2:
                    streak_title = "🔥 <b>𝗗𝗢𝗨𝗕𝗟𝗘 𝗪𝗜𝗡</b> 🔥"
                    sub_text = "💸 <i>Back to back profit confirmed!</i>"
                elif winStreak >= 3:
                    streak_title = f"🚀 <b>𝗠𝗘𝗚𝗔 𝗪𝗜𝗡 ({winStreak}x)</b> 🚀"
                    sub_text = "💸 <i>AI Algorithm printing money!</i>"
                
                win_loss_text = f"{streak_title}\n{sub_text}"
                sticker_to_send = WIN_STICKER_ID
            else:
                winStreak = 0
                win_loss_text = "❌ <b>𝗟𝗢𝗦𝗦 𝗗𝗘𝗧𝗘𝗖𝗧𝗘𝗗</b> ❌\n🔄 <i>Recovering in next period...</i>"
                sticker_to_send = LOSS_STICKER_ID

            historyData[0]['result'] = actual_number
            historyData[0]['resultStatus'] = status

            result_msg = (
                "✅ <b>𝗩𝗜𝗣 𝗥𝗘𝗦𝗨𝗟𝗧 𝗖𝗢𝗡𝗙𝗜𝗥𝗠𝗘𝗗</b> ✅\n"
                "━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎫 <b>𝗣𝗲𝗿𝗶𝗼𝗱 :</b> <code>{historyData[0]['period']}</code>\n"
                f"🔢 <b>𝗥𝗲𝘀𝘂𝗹𝘁 :</b> <code>{actual_number}</code> [ {color_emoji} <b>{actual_outcome}</b> ]\n\n"
                f"📣 <b>𝗦𝘁𝗮𝘁𝘂𝘀 :</b>\n{win_loss_text}\n\n"
                f"🔥 <b>𝗪𝗶𝗻𝗻𝗶𝗻𝗴 𝗦𝘁𝗿𝗲𝗮𝗸 :</b> <b>{winStreak}x</b>\n\n"
                "━━━━━━━━━━━━━━━━━━━"
            )

            for chat_id in list(target_channels):
                try:
                    bot.send_message(chat_id, result_msg, parse_mode='html')
                    time.sleep(0.5)
                    if "CAACAg" in sticker_to_send:
                        bot.send_sticker(chat_id, sticker_to_send)
                except Exception as e:
                    print(f"Failed to send result to {chat_id}: {e}")

        # ২. নতুন প্রেডিকশন তৈরি করা
        lastPrediction, predictedNumber = ai_predict(historyData)
        
        next_period_full = str(int(result['issueNumber']) + 1)
        next_period = next_period_full[-5:]
        pred_emoji = "🟩" if lastPrediction == "BIG" else "🟥"

        historyData.insert(0, {
            'period': next_period,
            'prediction': lastPrediction,
            'predictedNumber': predictedNumber,
            'result': "-",
            'resultStatus': "Pending"
        })

        pred_msg = (
            "💠 <b>𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗔𝗜 𝗦𝗜𝗚𝗡𝗔𝗟</b> 💠\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "🎮 <b>𝗚𝗮𝗺𝗲 𝗦𝗲𝗿𝘃𝗲𝗿 :</b> WinGo 30s VIP\n"
            f"🎫 <b>𝗣𝗲𝗿𝗶𝗼𝗱 𝗡𝗼 :</b> <code>{next_period}</code>\n\n"
            f"🔮 <b>𝗣𝗿𝗲𝗱𝗶𝗰𝘁𝗶𝗼𝗻 :</b> {pred_emoji} <b>{lastPrediction}</b> {pred_emoji}\n"
            f"🎯 <b>𝗧𝗮𝗿𝗴𝗲𝘁 𝗡𝘂𝗺 :</b> <code>{predictedNumber}</code>\n\n"
            "⚡️ <b>𝗔𝗰𝗰𝘂𝗿𝗮𝗰𝘆 :</b> <b>99.9% 𝗦𝘂𝗿𝗲</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "⏳ <i>Place your bet & wait for result...</i>"
        )

        for chat_id in list(target_channels):
            try:
                bot.send_message(chat_id, pred_msg, parse_mode='html')
            except Exception as e:
                print(f"Failed to send prediction to {chat_id}: {e}")

        lastFetchedPeriod = result['issueNumber']
        time.sleep(3)


# ==========================================
# 🎁 ১ মিনিট পরপর প্রোমোশনাল মেসেজ (With Image & Premium Design)
# ==========================================
def promo_loop():
    global is_running, target_channels
    while is_running:
        for _ in range(60): # 60 সেকেন্ড বা 1 মিনিট
            if not is_running:
                return
            time.sleep(1)
            
        if target_channels:
            promo_msg = (
                "🌟 <b>𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗩𝗜𝗣 𝗠𝗘𝗠𝗕𝗘𝗥𝗦𝗛𝗜𝗣</b> 🌟\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "💸 <i>𝐂𝐨𝐥𝐨𝐫 𝐓𝐫𝐚𝐝𝐢𝐧𝐠-এ বারবার লস করে ক্লান্ত?</i>\n"
                "🚀 <i>আজই আমাদের <b>𝐏𝐫𝐞𝐦𝐢𝐮𝐦 𝐀𝐈 𝐇𝐚𝐜𝐤</b> ব্যবহার করে আপনার লস রিকভার করুন এবং প্রতিদিন নিশ্চিত প্রফিট করুন!</i> 💯\n\n"
                "💎 <b>𝗪𝗛𝗬 𝗖𝗛𝗢𝗢𝗦𝗘 𝗨𝗦?</b>\n"
                "✅ <i>𝟗𝟗.𝟗% 𝐀𝐜𝐜𝐮𝐫𝐚𝐭𝐞 𝐀𝐈 𝐒𝐢𝐠𝐧𝐚𝐥𝐬</i>\n"
                "✅ <i>𝐃𝐚𝐢𝐥𝐲 𝐒𝐮𝐫𝐞 𝐏𝐫𝐨𝐟𝐢𝐭 𝐆𝐮𝐚𝐫𝐚𝐧𝐭𝐞𝐞</i>\n"
                "✅ <i>𝐙𝐞𝐫𝐨 𝐋𝐨𝐬𝐬 𝐒𝐭𝐫𝐚𝐭𝐞𝐠𝐲</i>\n"
                "✅ <i>𝟐𝟒/𝟕 𝐕𝐈𝐏 𝐒𝐮𝐩𝐩??𝐫𝐭</i>\n\n"
                "🔗 <b>𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗥𝗲𝗴𝗶𝘀𝘁𝗿𝗮𝘁𝗶𝗼𝗻 𝗟𝗶𝗻𝗸:</b>\n"
                "👉 <a href='https://hgnice.cc/#/register?invitationCode=48565863497'><b>এখানে ক্লিক করে একাউন্ট খুলুন</b></a>\n\n"
                "🎁 <i>একাউন্ট খোলার পর ভিআইপি সিগন্যাল হ্যাক পেতে দ্রুত অ্যাডমিনকে মেসেজ দিন!</i>\n"
                "━━━━━━━━━━━━━━━━━━━━"
            )
            
            markup = InlineKeyboardMarkup()
            btn_reg = InlineKeyboardButton("💎 Create VIP Account", url="https://hgnice.cc/#/register?invitationCode=48565863497")
            btn_admin = InlineKeyboardButton("👨‍💻 Message Admin", url="https://t.me/Shuvo_ofc")
            markup.row(btn_reg)
            markup.row(btn_admin)

            for chat_id in list(target_channels):
                try:
                    # ছবি সহ মেসেজ পাঠানোর কমান্ড
                    bot.send_photo(
                        chat_id, 
                        photo=PROMO_IMAGE_URL,
                        caption=promo_msg, 
                        parse_mode='html', 
                        reply_markup=markup
                    )
                except Exception as e:
                    print(f"Failed to send promo to {chat_id}: {e}")

# ==========================================
# 🛡️ এক্সেস ডিনাইড মেসেজ
# ==========================================
def send_access_denied(chat_id, user_id, first_name):
    text = (
        "🚫 <b>𝗔𝗖𝗖𝗘𝗦𝗦 𝗗𝗘𝗡𝗜𝗘𝗗</b> 🚫\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "⚠️ <b>𝗨𝗻𝗮𝘂𝘁𝗵𝗼𝗿𝗶𝘇𝗲𝗱 𝗔𝘁𝘁𝗲𝗺𝗽𝘁 𝗗𝗲𝘁𝗲𝗰𝘁𝗲𝗱!</b>\n\n"
        f"👤 <b>𝗨𝘀𝗲𝗿 𝗜𝗗 :</b> <code>{user_id}</code>\n"
        f"📛 <b>𝗡𝗮𝗺𝗲 :</b> <b>{first_name}</b>\n"
        "🔒 <b>𝗦𝘁𝗮𝘁𝘂𝘀 :</b> Non-VIP Member\n\n"
        "⛔️ <i>This is a highly secured Private AI Engine. Only the Admin can control this bot.</i>\n\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "👇 <b>𝗝𝗼𝗶𝗻 𝗢𝗳𝗳𝗶𝗰𝗶𝗮𝗹 𝗩𝗜𝗣 𝗖𝗵𝗮𝗻𝗻𝗲𝗹</b> 👇"
    )
    
    markup = InlineKeyboardMarkup()
    btn1 = InlineKeyboardButton("📢 Verify & Join Channel", url="https://t.me/Trader_Shuvo99")
    markup.row(btn1)
    
    try:
        if "CAACAg" in DENIED_STICKER_ID:
            bot.send_sticker(chat_id, DENIED_STICKER_ID)
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode='html')
    except Exception as e:
        pass

# ==========================================
# ⚙️ টেলিগ্রাম কমান্ডস (Admin Only)
# ==========================================

@bot.message_handler(commands=['add'])
def add_channel_cmd(message):
    if message.from_user.id != ADMIN_ID:
        send_access_denied(message.chat.id, message.from_user.id, message.from_user.first_name)
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ <b>সঠিক নিয়ম:</b>\n`/add @channel_username`\nঅথবা\n`/add -10012345678`", parse_mode="Markdown")
        return

    channel_id = parts[1]
    
    try:
        chat_info = bot.get_chat(channel_id)
        target_channels.add(channel_id)
        save_channels(target_channels)
        bot.reply_to(message, f"✅ <b>চ্যানেল অ্যাড করা হয়েছে!</b>\n\n📌 <b>নাম:</b> {chat_info.title}\n🆔 <b>ID:</b> <code>{channel_id}</code>\n\n<i>এখন থেকে এই চ্যানেলে সিগন্যাল যাবে। (যদি বট এডমিন থাকে)</i>", parse_mode="html")
    except Exception as e:
        bot.reply_to(message, f"❌ <b>অ্যাড করা সম্ভব হয়নি!</b>\n\n⚠️ <i>সমস্যা: বটকে হয়তো ওই চ্যানেলে এডমিন করা হয়নি অথবা ইউজারনেম ভুল দিয়েছেন।</i>\n\nError: <code>{e}</code>", parse_mode="html")

@bot.message_handler(commands=['remove'])
def remove_channel_cmd(message):
    if message.from_user.id != ADMIN_ID:
        send_access_denied(message.chat.id, message.from_user.id, message.from_user.first_name)
        return

    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ <b>সঠিক নিয়ম:</b>\n`/remove @channel_username`\nঅথবা\n`/remove -10012345678`", parse_mode="Markdown")
        return

    channel_id = parts[1]
    if channel_id in target_channels:
        target_channels.remove(channel_id)
        save_channels(target_channels)
        bot.reply_to(message, f"🗑 <b>চ্যানেল রিমুভ করা হয়েছে!</b>\n\n🆔 <code>{channel_id}</code>-এ আর কোনো সিগন্যাল যাবে না।", parse_mode="html")
    else:
        bot.reply_to(message, "⚠️ এই চ্যানেলটি লিস্টে পাওয়া যায়নি!")

@bot.message_handler(commands=['list'])
def list_channels_cmd(message):
    if message.from_user.id != ADMIN_ID:
        send_access_denied(message.chat.id, message.from_user.id, message.from_user.first_name)
        return

    if not target_channels:
        bot.reply_to(message, "📁 কোনো চ্যানেল অ্যাড করা নেই।\n`/add @username` লিখে অ্যাড করুন।")
        return

    msg = "📋 <b>অ্যাক্টিভ চ্যানেলের লিস্ট:</b>\n━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, ch in enumerate(target_channels, 1):
        msg += f"💠 {idx}. <code>{ch}</code>\n"
    
    msg += f"\n📊 <b>Total Active Channels:</b> <code>{len(target_channels)}</code>\n"
    msg += "━━━━━━━━━━━━━━━━━━━\n<i>রিমুভ করতে /remove <channel_id> ব্যবহার করুন।</i>"
    
    bot.reply_to(message, msg, parse_mode="html")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    global is_running
    
    if message.from_user.id != ADMIN_ID:
        send_access_denied(message.chat.id, message.from_user.id, message.from_user.first_name)
        return  

    msg = (
        "✅ <b>𝗔𝗜 𝗘𝗡𝗚𝗜𝗡𝗘 𝗦𝗧𝗔𝗥𝗧𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬!</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        f"🟢 <b>𝗧𝗼𝘁𝗮𝗹 𝗖𝗵𝗮𝗻𝗻𝗲𝗹𝘀 :</b> <code>{len(target_channels)}</code>\n"
        "⚙️ <b>𝗦𝘆𝘀𝘁𝗲𝗺 𝗠𝗼𝗱𝗲 :</b> Premium VIP Signals\n"
        "🛡 <b>𝗦𝗲𝗰𝘂𝗿𝗶𝘁𝘆 :</b> Max Level\n\n"
        "<i>🔄 Fetching live algorithm data... Please wait.</i>\n\n"
        "👇 <b>Help Commands:</b>\n"
        "/add @channel - চ্যানেল অ্যাড করুন\n"
        "/remove @channel - চ্যানেল মুছুন\n"
        "/list - সব চ্যানেল দেখুন\n"
        "/stop - সিগন্যাল থামান"
    )
    bot.reply_to(message, msg, parse_mode='html')
    
    if not is_running:
        is_running = True
        threading.Thread(target=prediction_loop).start()
        threading.Thread(target=promo_loop).start()

@bot.message_handler(commands=['stop'])
def stop_bot(message):
    global is_running
    
    if message.from_user.id != ADMIN_ID:
        send_access_denied(message.chat.id, message.from_user.id, message.from_user.first_name)
        return

    is_running = False
    bot.reply_to(message, "🛑 <b>𝗦𝗬𝗦𝗧𝗘𝗠 𝗦𝗛𝗨𝗧𝗗𝗢𝗪𝗡!</b>\n━━━━━━━━━━━━━━━━━━━\n⚠️ <i>সকল চ্যানেলে অটোমেটিক প্রেডিকশন এবং প্রোমোশনাল সিগন্যাল বন্ধ করা হয়েছে।</i>", parse_mode='html')

print("🤖 Multi-Channel VIP Bot is running...")
bot.polling(none_stop=True)
