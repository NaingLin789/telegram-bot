import os
import telebot
from telebot import types
from datetime import datetime
import threading
import random
import string
import requests
import json

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "8128339594:AAFN8dMdZDxddMasbLJyyibEA4aWsN2rIPA"
ADMIN_CHAT_ID = "6670652112"
BATMAN_URL = os.environ.get("BATMAN_URL", "https://bt6688.net")
BATMAN_USER = os.environ.get("BATMAN_USER", "")
BATMAN_PASS = os.environ.get("BATMAN_PASS", "")

bot = telebot.TeleBot(BOT_TOKEN)

# ==============================
# PRODUCTS
# ==============================
products = {
    "batman": {"name": "🦇 Batman Unit", "price": 1,    "desc": "1 Unit = 1 Ks"},
    "ibet":   {"name": "🎰 Ibet Unit",   "price": 1000, "desc": "1 Unit = 1,000 Ks"},
    "mix555": {"name": "🎲 555mix Unit", "price": 1,    "desc": "1 Unit = 1 Ks"},
}

# ==============================
# PAYMENT INFO
# ==============================
PAYMENT_INFO = """
💳 *ငွေပေးချေရန်*

🟢 KPay   — `09 940 940 000` (Daw Saw Nandar)
🔵 Wave   — `09 940 940 000` (Daw Saw Nandar)
🟡 AyaPay — `09 940 940 000` (Daw Thidar)

⚠️ ငွေလွှဲပြီးရင် Slip ဓာတ်ပုံ ဒီနေရာမှာ ပို့ပေးပါ
"""

# ==============================
# ORDER STORAGE
# ==============================
orders = {}
order_by_id = {}
order_counter = {"count": 1000}

# Batman Session
batman_session = requests.Session()
batman_logged_in = False

# ==============================
# HELPERS
# ==============================
def generate_password():
    upper = random.choice(string.ascii_uppercase)
    lower = ''.join(random.choices(string.ascii_lowercase, k=3))
    digits = ''.join(random.choices(string.digits, k=4))
    return upper + lower + digits

def new_order_id():
    order_counter["count"] += 1
    return f"ORD{order_counter['count']}"

def notify_admin(text):
    try:
        bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
    except:
        pass

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ ယူနစ်ဝယ်မယ်"),
        types.KeyboardButton("📋 မှာယူမှတ်တမ်း"),
        types.KeyboardButton("💳 ငွေပေးချေနည်း"),
        types.KeyboardButton("📞 ဆက်သွယ်ရန်"),
        types.KeyboardButton("❓ အကူအညီ"),
    )
    return markup

# ==============================
# BATMAN HTTP API
# ==============================
def batman_login():
    global batman_logged_in
    try:
        session = batman_session
        # Get login page first (for cookies/csrf)
        r = session.get(f"{BATMAN_URL}/login", timeout=15)
        
        # Try login
        login_data = {
            "username": BATMAN_USER,
            "password": BATMAN_PASS,
        }
        r = session.post(f"{BATMAN_URL}/login", data=login_data, timeout=15, allow_redirects=True)
        
        if r.status_code == 200 and "logout" in r.text.lower():
            batman_logged_in = True
            print("✅ Batman Login OK")
            return True
        else:
            batman_logged_in = False
            print(f"❌ Batman Login Failed: {r.status_code}")
            return False
    except Exception as e:
        print(f"Batman login error: {e}")
        return False

def batman_add_player(customer_name, score):
    """Add new player via HTTP"""
    try:
        if not batman_logged_in:
            batman_login()

        session = batman_session
        
        # Get account page to get CSRF token
        r = session.get(f"{BATMAN_URL}/account", timeout=15)
        
        password = generate_password()
        
        # Try to add player
        data = {
            "password": password,
            "name": customer_name,
            "score": str(score),
            "status": "1",
        }
        
        r = session.post(f"{BATMAN_URL}/account/addplayer", 
                        data=data, timeout=15, allow_redirects=True)
        
        if r.status_code == 200:
            try:
                result = r.json()
                username = result.get("username") or result.get("id") or result.get("account_id", "")
                if username:
                    return {
                        "success": True,
                        "username": username,
                        "password": password,
                        "score": score,
                        "url": "http://m.batman688.com"
                    }
            except:
                # Try to parse HTML response
                if "success" in r.text.lower() or "B" in r.text:
                    return {
                        "success": True,
                        "username": "စစ်ဆေးပါ",
                        "password": password,
                        "score": score,
                        "url": "http://m.batman688.com"
                    }
        
        return {"success": False, "error": f"HTTP {r.status_code}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def batman_deposit(player_id, amount):
    """Deposit to existing player via HTTP"""
    try:
        if not batman_logged_in:
            batman_login()

        session = batman_session
        
        data = {
            "player": player_id,
            "amount": str(amount),
        }
        
        r = session.post(f"{BATMAN_URL}/account/deposit",
                        data=data, timeout=15, allow_redirects=True)
        
        if r.status_code == 200:
            return {"success": True, "player_id": player_id, "amount": amount}
        
        return {"success": False, "error": f"HTTP {r.status_code}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==============================
# AUTO PROCESS
# ==============================
def process_order_auto(order, customer_chat_id):
    try:
        product_key = order.get("product_key", "")
        
        # Ibet နဲ့ 555mix က Manual လုပ်ရသေးတယ်
        if product_key != "batman":
            notify_admin(
                f"⚠️ *{order['product']['name']}* Manual လုပ်ပေးပါ\n\n"
                f"🆔 {order['order_id']}\n"
                f"👤 {order['customer_name']} ({order['phone']})\n"
                f"🔢 {order['qty']:,} Units\n"
                f"📱 {order['account_type']}"
                f"{(' | ID: '+order['old_account_id']) if order.get('old_account_id') else ''}\n\n"
                f"📨 `/send {order['order_id']} [message]`"
            )
            bot.send_message(customer_chat_id, "⏳ မကြာမီ ပို့ပေးပါမည် 🙏", reply_markup=get_main_menu())
            return

        if order["account_type"] == "အကောင့်သစ်":
            result = batman_add_player(order["customer_name"], order["qty"])
            if result["success"]:
                bot.send_message(
                    customer_chat_id,
                    f"✅ *သင့်အကောင့် အသင့်ဖြစ်ပြီ!*\n\n"
                    f"🌐 URL — `{result['url']}`\n"
                    f"🆔 ID  — `{result['username']}`\n"
                    f"🔑 PW  — `{result['password']}`\n"
                    f"💰 Score — {result['score']:,}\n\n"
                    f"ကျေးဇူးတင်ပါတယ် 🙏",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
                notify_admin(
                    f"✅ *Auto အကောင့်ဖွင့်ပြီး*\n"
                    f"🆔 {order['order_id']}\n"
                    f"Batman ID: {result['username']}\n"
                    f"Score: {result['score']:,}"
                )
            else:
                bot.send_message(customer_chat_id, "⏳ မကြာမီ အကောင့် ပို့ပေးပါမည် 🙏", reply_markup=get_main_menu())
                notify_admin(
                    f"❌ *Auto မအောင်မြင် — Manual လုပ်ပေးပါ*\n\n"
                    f"🆔 {order['order_id']}\n"
                    f"👤 {order['customer_name']}\n"
                    f"🔢 {order['qty']:,} Units | အကောင့်သစ်\n\n"
                    f"📨 `/send {order['order_id']} [message]`"
                )
        else:
            player_id = order.get("old_account_id", "")
            result = batman_deposit(player_id, order["qty"])
            if result["success"]:
                bot.send_message(
                    customer_chat_id,
                    f"✅ *Unit ဖြည့်ပြီး!*\n\n"
                    f"🆔 Account — `{player_id}`\n"
                    f"💰 {order['qty']:,} Units ဖြည့်ပြီး\n\n"
                    f"ကျေးဇူးတင်ပါတယ် 🙏",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
            else:
                bot.send_message(customer_chat_id, "⏳ မကြာမီ Unit ဖြည့်ပေးပါမည် 🙏", reply_markup=get_main_menu())
                notify_admin(
                    f"❌ *Auto DEP မအောင်မြင် — Manual လုပ်ပေးပါ*\n\n"
                    f"🆔 {order['order_id']}\n"
                    f"Batman ID: {player_id}\n"
                    f"Amount: {order['qty']:,}\n\n"
                    f"📨 `/send {order['order_id']} [message]`"
                )
    except Exception as e:
        print(f"process error: {e}")
        notify_admin(f"❌ Error: {str(e)}\n\n`/send {order['order_id']} [msg]`")

# ==============================
# /start
# ==============================
@bot.message_handler(commands=["start"])
def start(message):
    name = message.from_user.first_name or "Customer"
    bot.send_message(
        message.chat.id,
        f"မင်္ဂလာပါ *{name}* !\n\n"
        f"🏪 *MNL2admin* ကိုနိုင်လင်းယူနစ်အရောင်းဆိုင်မှ ကြိုဆိုပါတယ် 🎉\n\n"
        f"ဘာများ ကူညီပေးရမလဲ?",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

# ==============================
# ADMIN Commands
# ==============================
@bot.message_handler(commands=["send"])
def admin_send(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    try:
        parts = message.text.split(" ", 2)
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ `/send ORD1001 message`", parse_mode="Markdown")
            return
        order_id = parts[1].upper()
        reply_text = parts[2]
        if order_id not in order_by_id:
            bot.send_message(message.chat.id, f"❌ `{order_id}` မတွေ့ပါ", parse_mode="Markdown")
            return
        customer_uid = order_by_id[order_id]
        bot.send_message(customer_uid,
            f"✅ *သင့် Order အတွက် အချက်အလက်*\n\n"
            f"🆔 `{order_id}`\n\n{reply_text}\n\nကျေးဇူးတင်ပါတယ် 🙏",
            parse_mode="Markdown")
        bot.send_message(message.chat.id, f"✅ ပို့ပြီး — {order_id}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ {str(e)}")

@bot.message_handler(commands=["orders"])
def admin_orders(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    if not orders:
        bot.send_message(message.chat.id, "📭 Order မရှိသေးပါ")
        return
    text = "📋 *Order စာရင်း*\n\n"
    for uid, order in orders.items():
        status = {"paid":"✅","waiting_payment":"⏳","processing":"🔄","completed":"🎉"}.get(order.get("step",""),"🔄")
        text += (f"🆔 `{order.get('order_id','-')}` {status}\n"
                 f"👤 {order.get('customer_name','-')} | {order.get('phone','-')}\n"
                 f"🎮 {order['product']['name']} x{order.get('qty',0):,} | 💰 {order.get('total',0):,} Ks\n"
                 f"{'─'*20}\n")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ==============================
# ORDER FLOW
# ==============================
@bot.message_handler(func=lambda m: m.text == "🛍️ ယူနစ်ဝယ်မယ်")
def choose_product(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🦇 Batman Unit (1 Unit = 1 Ks)", callback_data="prod_batman"),
        types.InlineKeyboardButton("🎰 Ibet Unit (1 Unit = 1,000 Ks)", callback_data="prod_ibet"),
        types.InlineKeyboardButton("🎲 555mix Unit (1 Unit = 1 Ks)", callback_data="prod_mix555"),
    )
    bot.send_message(message.chat.id, "🎮 *ဘာ Unit ယူမလဲ?*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("prod_"))
def handle_product(call):
    prod_key = call.data.split("_", 1)[1]
    product = products.get(prod_key)
    if not product:
        return
    order_id = new_order_id()
    orders[call.from_user.id] = {
        "product_key": prod_key, "product": product,
        "step": "account_type", "order_id": order_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "customer_uid": call.from_user.id,
    }
    order_by_id[order_id] = call.from_user.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🆕 အကောင့်သစ်", callback_data="acc_new"),
        types.InlineKeyboardButton("♻️ အကောင့်ဟောင်း", callback_data="acc_old"),
    )
    bot.send_message(call.message.chat.id,
        f"✅ *{product['name']}* ရွေးချယ်ပြီး\n\nအကောင့်သစ် ယူမလား၊ အကောင့်ဟောင်း ယူမလား?",
        parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data in ["acc_new", "acc_old"])
def handle_account_type(call):
    uid = call.from_user.id
    if uid not in orders:
        return
    bot.answer_callback_query(call.id)
    if call.data == "acc_new":
        orders[uid]["account_type"] = "အကောင့်သစ်"
        orders[uid]["step"] = "name"
        bot.send_message(call.message.chat.id, "🆕 *အကောင့်သစ်*\n\n👤 နာမည် ရိုက်ထည့်ပေးပါ —", parse_mode="Markdown")
    else:
        orders[uid]["account_type"] = "အကောင့်ဟောင်း"
        orders[uid]["step"] = "old_account_id"
        bot.send_message(call.message.chat.id, "♻️ *အကောင့်ဟောင်း*\n\n🆔 Account ID ရိုက်ထည့်ပေးပါ —", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") == "old_account_id")
def handle_old_id(message):
    uid = message.from_user.id
    orders[uid]["old_account_id"] = message.text
    orders[uid]["step"] = "name"
    bot.send_message(message.chat.id, f"✅ ID — `{message.text}`\n\n👤 နာမည် ရိုက်ထည့်ပေးပါ —", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") in ["name","phone","qty"])
def handle_steps(message):
    uid = message.from_user.id
    order = orders[uid]
    step = order["step"]
    if step == "name":
        order["customer_name"] = message.text
        order["step"] = "phone"
        bot.send_message(message.chat.id, "📱 ဖုန်းနံပါတ် ရိုက်ထည့်ပေးပါ —")
    elif step == "phone":
        order["phone"] = message.text
        order["step"] = "qty"
        bot.send_message(message.chat.id, f"🔢 {order['product']['name']} ဘယ်နှစ် Unit ယူမလဲ?\n({order['product']['desc']})")
    elif step == "qty":
        try:
            qty = int(message.text)
            if qty <= 0: raise ValueError
            order["qty"] = qty
            order["total"] = qty * order["product"]["price"]
            order["step"] = "waiting_payment"
            acc_info = f"🆔 Account ID — `{order['old_account_id']}`\n" if order.get("old_account_id") else ""
            summary = (f"📋 *မှာယူမှတ်တမ်း*\n\n"
                      f"🆔 Order — `{order['order_id']}`\n"
                      f"👤 {order['customer_name']} | 📱 {order['phone']}\n"
                      f"🎮 {order['product']['name']}\n"
                      f"📱 {order['account_type']}\n{acc_info}"
                      f"🔢 {qty:,} Units\n💰 *{order['total']:,} Ks*")
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ အတည်ပြုမယ်", callback_data=f"confirm_{uid}"),
                types.InlineKeyboardButton("❌ ပယ်ဖျက်မယ်", callback_data=f"cancel_{uid}")
            )
            bot.send_message(message.chat.id, summary, parse_mode="Markdown", reply_markup=markup)
        except ValueError:
            bot.send_message(message.chat.id, "❌ နံပါတ် မှန်မှန် ရိုက်ပေးပါ")

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_"))
def handle_confirm(call):
    uid = int(call.data.split("_")[1])
    order = orders.get(uid)
    if not order: return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, PAYMENT_INFO, parse_mode="Markdown")
    notify_admin(
        f"🔔 *Order အသစ်!*\n🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} ({order['phone']})\n"
        f"🎮 {order['product']['name']} x{order['qty']:,}\n"
        f"📱 {order['account_type']}"
        f"{(' | ID: '+order['old_account_id']) if order.get('old_account_id') else ''}\n"
        f"💰 {order['total']:,} Ks\n\n`/send {order['order_id']} [msg]`"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def handle_cancel(call):
    uid = int(call.data.split("_")[1])
    if uid in orders:
        oid = orders[uid].get("order_id")
        if oid in order_by_id: del order_by_id[oid]
        del orders[uid]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "❌ ပယ်ဖျက်ပြီ", reply_markup=get_main_menu())

@bot.message_handler(content_types=["photo"],
    func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") == "waiting_payment")
def handle_slip(message):
    uid = message.from_user.id
    order = orders[uid]
    order["step"] = "processing"
    bot.send_message(message.chat.id,
        f"✅ *Slip လက်ခံပြီး!*\n🆔 `{order['order_id']}`\n⏳ မကြာမီ ပို့ပေးပါမည် 🙏",
        parse_mode="Markdown")
    bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
    notify_admin(
        f"💳 *Slip ရောက်ပြီ!*\n🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} | {order['phone']}\n"
        f"🎮 {order['product']['name']} x{order['qty']:,}\n"
        f"💰 {order['total']:,} Ks\n⚡ Processing..."
    )
    thread = threading.Thread(target=process_order_auto, args=(order.copy(), uid))
    thread.daemon = True
    thread.start()

@bot.message_handler(func=lambda m: m.text == "📋 မှာယူမှတ်တမ်း")
def order_history(message):
    uid = message.from_user.id
    if uid not in orders:
        bot.send_message(message.chat.id, "📭 မှာယူမှတ်တမ်း မရှိသေးပါ")
        return
    order = orders[uid]
    status = {"paid":"✅","waiting_payment":"⏳","processing":"🔄","completed":"🎉"}.get(order.get("step",""),"🔄")
    bot.send_message(message.chat.id,
        f"📋 *နောက်ဆုံး Order*\n\n🆔 {order.get('order_id','-')}\n"
        f"🎮 {order['product']['name']}\n🔢 {order.get('qty',0):,} Units\n"
        f"💰 {order.get('total',0):,} Ks\n📊 {status}", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "💳 ငွေပေးချေနည်း")
def payment_info(message):
    bot.send_message(message.chat.id, PAYMENT_INFO, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📞 ဆက်သွယ်ရန်")
def contact(message):
    bot.send_message(message.chat.id,
        "📞 *ဆက်သွယ်ရန်*\n\n🏪 MNL2admin\n📱 `09 940 940 010`\n🕐 ၉နာရီ မှ ၉နာရီ",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "❓ အကူအညီ")
def help_msg(message):
    bot.send_message(message.chat.id,
        "❓ *အကူအညီ*\n\n1️⃣ 🛍️ ယူနစ်ဝယ်မယ်\n2️⃣ 📋 မှာယူမှတ်တမ်း\n"
        "3️⃣ 💳 ငွေပေးချေနည်း\n4️⃣ 📞 ဆက်သွယ်ရန်\n\n📞 09 940 940 010",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(message.chat.id, "🤔 Menu မှ ရွေးချယ်ပေးပါ 👇", reply_markup=get_main_menu())

# Login Batman on startup
threading.Thread(target=batman_login, daemon=True).start()

print("🤖 MNL2admin Bot စတင်လည်ပတ်နေပြီး...")
bot.infinity_polling()
