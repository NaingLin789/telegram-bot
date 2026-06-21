import os
import telebot
from telebot import types
from datetime import datetime
import threading
import random
import string
import requests

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
BATMAN_URL = os.environ.get("BATMAN_URL", "https://bt6688.net")
BATMAN_SESSION = os.environ.get("BATMAN_SESSION", "")

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
        types.KeyboardButton("💰 ယူနစ်ရောင်းမယ်"),
        types.KeyboardButton("📋 မှာယူမှတ်တမ်း"),
        types.KeyboardButton("💳 ငွေပေးချေနည်း"),
        types.KeyboardButton("📞 ဆက်သွယ်ရန်"),
        types.KeyboardButton("❓ အကူအညီ"),
    )
    return markup

def generate_password():
    upper = random.choice(string.ascii_uppercase)
    lower = ''.join(random.choices(string.ascii_lowercase, k=3))
    digits = ''.join(random.choices(string.digits, k=4))
    return upper + lower + digits

# ==============================
# BATMAN API
# ==============================
def get_batman_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{BATMAN_URL}/account",
        "Cookie": f"SESSION={BATMAN_SESSION}",
    }

def batman_get_username():
    try:
        r = requests.get(
            f"{BATMAN_URL}/api/player/getUsername",
            headers=get_batman_headers(),
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("username") or data.get("data", {}).get("username", "")
        return ""
    except:
        return ""

def batman_add_player(customer_name, score):
    try:
        username = batman_get_username()
        if not username:
            return {"success": False, "error": "Cannot get username"}

        password = generate_password()
        data = f"username={username}&password={password}&name={customer_name}&contact=&score={score}&status=1"
        r = requests.post(
            f"{BATMAN_URL}/api/player/add",
            data=data,
            headers=get_batman_headers(),
            timeout=15
        )
        if r.status_code == 200:
            return {
                "success": True,
                "username": username,
                "password": password,
                "score": score,
                "url": "http://m.batman688.com"
            }
        return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def batman_add_credit(player_id, amount):
    try:
        data = f"targetPlayer={player_id}&credit={amount}"
        r = requests.post(
            f"{BATMAN_URL}/api/player/add-credit",
            data=data,
            headers=get_batman_headers(),
            timeout=15
        )
        if r.status_code == 200:
            return {"success": True}
        return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def batman_withdraw_credit(player_id, amount):
    try:
        data = f"targetPlayer={player_id}&credit=-{amount}"
        r = requests.post(
            f"{BATMAN_URL}/api/player/add-credit",
            data=data,
            headers=get_batman_headers(),
            timeout=15
        )
        if r.status_code == 200:
            return {"success": True}
        return {"success": False, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ==============================
# AUTO PROCESS — BUY
# ==============================
def process_order_auto(order, customer_chat_id):
    try:
        product_key = order.get("product_key", "")

        if product_key != "batman":
            notify_admin(
                f"⚠️ *{order['product']['name']}* Manual လုပ်ပေးပါ\n\n"
                f"🆔 {order['order_id']}\n"
                f"👤 {order['customer_name']} ({order['phone']})\n"
                f"🔢 {order['qty']:,} Units\n"
                f"📱 {order['account_type']}"
                f"{(' | ID: `'+order['old_account_id']+'`') if order.get('old_account_id') else ''}\n\n"
                f"📨 `/send {order['order_id']} [message]`"
            )
            return

        if order["account_type"] == "အကောင့်သစ်":
            result = batman_add_player(order["customer_name"], order["qty"])
            if result["success"]:
                bot.send_message(
                    customer_chat_id,
                    f"✅ *သင့်အကောင့် အသင့်ဖြစ်ပြီ!*\n\n"
                    f"🌐 URL  — `{result['url']}`\n"
                    f"🆔 ID   — `{result['username']}`\n"
                    f"🔑 PW   — `{result['password']}`\n"
                    f"💰 Score — {result['score']:,}\n\n"
                    f"ကျေးဇူးတင်ပါတယ် 🙏",
                    parse_mode="Markdown", reply_markup=get_main_menu()
                )
                notify_admin(
                    f"✅ *Auto အကောင့်ဖွင့်ပြီး*\n"
                    f"🆔 {order['order_id']}\n"
                    f"Batman ID: `{result['username']}`\n"
                    f"PW: `{result['password']}`\n"
                    f"Score: {result['score']:,}"
                )
            else:
                bot.send_message(customer_chat_id, "⏳ မကြာမီ အကောင့် ပို့ပေးပါမည် 🙏", reply_markup=get_main_menu())
                notify_admin(
                    f"❌ *Auto မအောင်မြင် — Manual လုပ်ပေးပါ*\n\n"
                    f"🆔 {order['order_id']}\n"
                    f"👤 {order['customer_name']}\n"
                    f"🔢 {order['qty']:,} Units | အကောင့်သစ်\n"
                    f"Error: {result.get('error','')}\n\n"
                    f"📨 `/send {order['order_id']} [message]`"
                )
        else:
            player_id = order.get("old_account_id", "")
            result = batman_add_credit(player_id, order["qty"])
            if result["success"]:
                bot.send_message(
                    customer_chat_id,
                    f"✅ *Unit ဖြည့်ပြီး!*\n\n"
                    f"🆔 Account — `{player_id}`\n"
                    f"💰 {order['qty']:,} Units ဖြည့်ပြီး\n\n"
                    f"ကျေးဇူးတင်ပါတယ် 🙏",
                    parse_mode="Markdown", reply_markup=get_main_menu()
                )
                notify_admin(f"✅ Auto DEP ပြီး — `{player_id}` | {order['qty']:,}")
            else:
                bot.send_message(customer_chat_id, "⏳ မကြာမီ Unit ဖြည့်ပေးပါမည် 🙏", reply_markup=get_main_menu())
                notify_admin(
                    f"❌ *Auto DEP မအောင်မြင် — Manual*\n\n"
                    f"🆔 {order['order_id']}\n"
                    f"Batman ID: `{player_id}`\n"
                    f"Amount: {order['qty']:,}\n\n"
                    f"📨 `/send {order['order_id']} [message]`"
                )
    except Exception as e:
        notify_admin(f"❌ Error: {str(e)}\n\n`/send {order['order_id']} [msg]`")

# ==============================
# AUTO PROCESS — SELL
# ==============================
def process_withdraw_auto(order, customer_chat_id):
    try:
        player_id = order.get("batman_id", "")
        qty = order.get("qty", 0)
        result = batman_withdraw_credit(player_id, qty)
        if result["success"]:
            bot.send_message(
                customer_chat_id,
                f"✅ *ယူနစ် ထုတ်ပြီး!*\n\n"
                f"🆔 Account — `{player_id}`\n"
                f"💰 {qty:,} Units ထုတ်ပြီး\n"
                f"💵 ငွေ {qty:,} Ks မကြာမီ ပို့ပေးမည်\n\n"
                f"ကျေးဇူးတင်ပါတယ် 🙏",
                parse_mode="Markdown", reply_markup=get_main_menu()
            )
            notify_admin(
                f"✅ *Auto Withdraw ပြီး*\n"
                f"🆔 {order['order_id']}\n"
                f"Batman ID: `{player_id}`\n"
                f"Amount: {qty:,}\n\n"
                f"⚠️ Customer ဆီ ငွေပြန်ပို့ပေးပါ!"
            )
        else:
            bot.send_message(customer_chat_id, "⏳ မကြာမီ ငွေပြန်ပို့ပေးပါမည် 🙏", reply_markup=get_main_menu())
            notify_admin(
                f"❌ *Auto Withdraw မအောင်မြင် — Manual*\n\n"
                f"🆔 {order['order_id']}\n"
                f"Batman ID: `{player_id}`\n"
                f"Amount: {qty:,}\n"
                f"Error: {result.get('error','')}\n\n"
                f"📨 `/send {order['order_id']} [message]`"
            )
    except Exception as e:
        notify_admin(f"❌ Withdraw Error: {str(e)}")

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
        parse_mode="Markdown", reply_markup=get_main_menu()
    )

# ==============================
# ADMIN COMMANDS
# ==============================
@bot.message_handler(commands=["confirm"])
def admin_confirm(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ `/confirm ORD1001`", parse_mode="Markdown")
            return
        order_id = parts[1].upper()
        if order_id not in order_by_id:
            bot.send_message(message.chat.id, f"❌ `{order_id}` မတွေ့ပါ", parse_mode="Markdown")
            return
        customer_uid = order_by_id[order_id]
        order = orders.get(customer_uid)
        if not order:
            return
        order["step"] = "confirmed"
        bot.send_message(message.chat.id, f"✅ Confirm — Processing... `{order_id}`", parse_mode="Markdown")
        bot.send_message(customer_uid, "⏳ Slip စစ်ဆေးပြီး Processing လုပ်နေပါသည်...")
        if order.get("order_type") == "withdraw":
            thread = threading.Thread(target=process_withdraw_auto, args=(order.copy(), customer_uid))
        else:
            thread = threading.Thread(target=process_order_auto, args=(order.copy(), customer_uid))
        thread.daemon = True
        thread.start()
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ {str(e)}")

@bot.message_handler(commands=["reject"])
def admin_reject(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    try:
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ `/reject ORD1001`", parse_mode="Markdown")
            return
        order_id = parts[1].upper()
        if order_id not in order_by_id:
            bot.send_message(message.chat.id, f"❌ `{order_id}` မတွေ့ပါ", parse_mode="Markdown")
            return
        customer_uid = order_by_id[order_id]
        if customer_uid in orders:
            orders[customer_uid]["step"] = "waiting_payment"
        bot.send_message(customer_uid,
            f"❌ *မအောင်မြင်ပါ*\n\n🆔 `{order_id}`\n\nပြန်စစ်ဆေးပြီး Admin ဆက်သွယ်ပါ။\n📞 09 940 940 010",
            parse_mode="Markdown", reply_markup=get_main_menu())
        bot.send_message(message.chat.id, f"✅ Reject — `{order_id}`", parse_mode="Markdown")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ {str(e)}")

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
            f"✅ *သင့် Order အတွက်*\n\n🆔 `{order_id}`\n\n{reply_text}\n\nကျေးဇူးတင်ပါတယ် 🙏",
            parse_mode="Markdown", reply_markup=get_main_menu())
        bot.send_message(message.chat.id, f"✅ ပို့ပြီး — `{order_id}`", parse_mode="Markdown")
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
        status = {"waiting_payment": "⏳", "slip_sent": "💳", "confirmed": "🔄", "completed": "✅"}.get(order.get("step",""), "🔄")
        otype = "💰ရောင်း" if order.get("order_type") == "withdraw" else "🛍️ဝယ်"
        text += (
            f"{otype} `{order.get('order_id','-')}` {status}\n"
            f"👤 {order.get('customer_name','-')} | {order.get('qty',0):,} Units\n"
            f"{'─'*20}\n"
        )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["adminhelp"])
def admin_help(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    bot.send_message(message.chat.id,
        "🔧 *Admin Commands*\n\n"
        "📋 `/orders` — Order စာရင်း\n"
        "✅ `/confirm ORD1001` — Auto Process\n"
        "❌ `/reject ORD1001` — Reject\n"
        "📨 `/send ORD1001 msg` — Manual ပို့\n",
        parse_mode="Markdown")

# ==============================
# BUY FLOW
# ==============================
@bot.message_handler(func=lambda m: m.text == "🛍️ ယူနစ်ဝယ်မယ်")
def choose_product(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🦇 Batman Unit (1 Unit = 1 Ks)", callback_data="prod_batman"),
        types.InlineKeyboardButton("🎰 Ibet Unit (1 Unit = 1,000 Ks)", callback_data="prod_ibet"),
        types.InlineKeyboardButton("🎲 555mix Unit (1 Unit = 1 Ks)", callback_data="prod_mix555"),
    )
    bot.send_message(message.chat.id, "🎮 *ဘာ Unit ဝယ်မလဲ?*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("prod_"))
def handle_product(call):
    prod_key = call.data.split("_", 1)[1]
    product = products.get(prod_key)
    if not product:
        return
    order_id = new_order_id()
    orders[call.from_user.id] = {
        "order_type": "buy",
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
        f"✅ *{product['name']}* ရွေးချယ်ပြီး\n\nအကောင့်သစ် ယူမလား၊ အကောင့်ဟောင်း ဖြည့်မလား?",
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
        bot.send_message(call.message.chat.id,
            "♻️ *အကောင့်ဟောင်း*\n\n🆔 Batman ID ရိုက်ထည့်ပေးပါ —\n_(ဥပမာ — B12345678)_",
            parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") == "old_account_id")
def handle_old_id(message):
    uid = message.from_user.id
    orders[uid]["old_account_id"] = message.text.strip()
    orders[uid]["step"] = "name"
    bot.send_message(message.chat.id, f"✅ ID — `{message.text.strip()}`\n\n👤 နာမည် ရိုက်ထည့်ပေးပါ —", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") in ["name", "phone", "qty"])
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
        bot.send_message(message.chat.id, f"🔢 {order['product']['name']} ဘယ်နှစ် Unit ဝယ်မလဲ?\n({order['product']['desc']})")
    elif step == "qty":
        try:
            qty = int(message.text.replace(",", ""))
            if qty <= 0: raise ValueError
            order["qty"] = qty
            order["total"] = qty * order["product"]["price"]
            order["step"] = "waiting_payment"
            acc_info = f"🆔 Batman ID — `{order['old_account_id']}`\n" if order.get("old_account_id") else ""
            summary = (
                f"📋 *မှာယူမှတ်တမ်း*\n\n"
                f"🆔 Order — `{order['order_id']}`\n"
                f"👤 {order['customer_name']} | 📱 {order['phone']}\n"
                f"🎮 {order['product']['name']}\n"
                f"📱 {order['account_type']}\n{acc_info}"
                f"🔢 {qty:,} Units\n💰 *{order['total']:,} Ks*"
            )
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
        f"🔔 *Order အသစ် (ဝယ်)*\n\n"
        f"🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} ({order['phone']})\n"
        f"🎮 {order['product']['name']} x{order['qty']:,}\n"
        f"📱 {order['account_type']}"
        f"{(' | ID: `'+order['old_account_id']+'`') if order.get('old_account_id') else ''}\n"
        f"💰 {order['total']:,} Ks\n\n"
        f"✅ `/confirm {order['order_id']}`\n"
        f"❌ `/reject {order['order_id']}`"
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
    order["step"] = "slip_sent"
    otype = "ရောင်း" if order.get("order_type") == "withdraw" else "ဝယ်"
    bot.send_message(message.chat.id,
        f"✅ *Slip လက်ခံပြီး!*\n🆔 `{order['order_id']}`\n⏳ စစ်ဆေးနေပါသည် 🙏",
        parse_mode="Markdown")
    bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
    notify_admin(
        f"💳 *Slip ရောက်ပြီ ({otype}) — စစ်ဆေးပါ!*\n\n"
        f"🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} | {order['phone']}\n"
        f"🎮 {order['product']['name']} x{order.get('qty',0):,}\n\n"
        f"✅ `/confirm {order['order_id']}`\n"
        f"❌ `/reject {order['order_id']}`"
    )

# ==============================
# SELL FLOW
# ==============================
@bot.message_handler(func=lambda m: m.text == "💰 ယူနစ်ရောင်းမယ်")
def sell_start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🦇 Batman Unit ရောင်းမယ်", callback_data="sell_batman"),
    )
    bot.send_message(message.chat.id, "💰 *ဘာ Unit ရောင်းမလဲ?*", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("sell_"))
def handle_sell_product(call):
    prod_key = call.data.split("_", 1)[1]
    product = products.get(prod_key)
    if not product: return
    order_id = new_order_id()
    orders[call.from_user.id] = {
        "order_type": "withdraw",
        "product_key": prod_key, "product": product,
        "step": "sell_batman_id", "order_id": order_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "customer_uid": call.from_user.id,
    }
    order_by_id[order_id] = call.from_user.id
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "💰 *ယူနစ်ရောင်းမယ်*\n\n🆔 Batman ID ရိုက်ထည့်ပေးပါ —\n_(ဥပမာ — B12345678)_",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") == "sell_batman_id")
def handle_sell_batman_id(message):
    uid = message.from_user.id
    orders[uid]["batman_id"] = message.text.strip()
    orders[uid]["step"] = "sell_name"
    bot.send_message(message.chat.id, f"✅ ID — `{message.text.strip()}`\n\n👤 နာမည် ရိုက်ထည့်ပေးပါ —", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") in ["sell_name", "sell_phone", "sell_qty"])
def handle_sell_steps(message):
    uid = message.from_user.id
    order = orders[uid]
    step = order["step"]
    if step == "sell_name":
        order["customer_name"] = message.text
        order["step"] = "sell_phone"
        bot.send_message(message.chat.id, "📱 ဖုန်းနံပါတ် ရိုက်ထည့်ပေးပါ —")
    elif step == "sell_phone":
        order["phone"] = message.text
        order["step"] = "sell_qty"
        bot.send_message(message.chat.id, "🔢 ဘယ်နှစ် Unit ရောင်းမလဲ?")
    elif step == "sell_qty":
        try:
            qty = int(message.text.replace(",", ""))
            if qty <= 0: raise ValueError
            order["qty"] = qty
            order["total"] = qty * order["product"]["price"]
            order["step"] = "waiting_payment"
            summary = (
                f"📋 *ယူနစ်ရောင်းမှတ်တမ်း*\n\n"
                f"🆔 Order — `{order['order_id']}`\n"
                f"👤 {order['customer_name']} | 📱 {order['phone']}\n"
                f"🎮 {order['product']['name']}\n"
                f"🆔 Batman ID — `{order['batman_id']}`\n"
                f"🔢 {qty:,} Units ရောင်းမည်\n"
                f"💵 ရမည့်ငွေ — *{order['total']:,} Ks*\n\n"
                f"⚠️ Admin စစ်ပြီး unit နှုတ်ကာ ငွေပြန်ပို့ပေးမည်"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ အတည်ပြုမယ်", callback_data=f"sellconfirm_{uid}"),
                types.InlineKeyboardButton("❌ ပယ်ဖျက်မယ်", callback_data=f"cancel_{uid}")
            )
            bot.send_message(message.chat.id, summary, parse_mode="Markdown", reply_markup=markup)
        except ValueError:
            bot.send_message(message.chat.id, "❌ နံပါတ် မှန်မှန် ရိုက်ပေးပါ")

@bot.callback_query_handler(func=lambda c: c.data.startswith("sellconfirm_"))
def handle_sell_confirm(call):
    uid = int(call.data.split("_")[1])
    order = orders.get(uid)
    if not order: return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        "✅ *မှာယူမှတ်တမ်း လက်ခံပြီး*\n\n⏳ Admin စစ်ဆေးပြီး ငွေပြန်ပို့ပေးမည် 🙏",
        parse_mode="Markdown")
    notify_admin(
        f"🔔 *Order အသစ် (ရောင်း)*\n\n"
        f"🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} ({order['phone']})\n"
        f"🎮 {order['product']['name']}\n"
        f"🆔 Batman ID — `{order['batman_id']}`\n"
        f"🔢 {order['qty']:,} Units\n"
        f"💵 ပို့ရမည် — {order['total']:,} Ks\n\n"
        f"✅ `/confirm {order['order_id']}`\n"
        f"❌ `/reject {order['order_id']}`"
    )

# ==============================
# OTHER HANDLERS
# ==============================
@bot.message_handler(func=lambda m: m.text == "📋 မှာယူမှတ်တမ်း")
def order_history(message):
    uid = message.from_user.id
    if uid not in orders:
        bot.send_message(message.chat.id, "📭 မှာယူမှတ်တမ်း မရှိသေးပါ")
        return
    order = orders[uid]
    status = {
        "waiting_payment": "⏳ စစ်ဆေးဆဲ",
        "slip_sent": "💳 Slip ပို့ပြီး",
        "confirmed": "🔄 Processing",
        "completed": "✅ ပြီးဆုံး",
    }.get(order.get("step",""), "🔄")
    otype = "💰 ရောင်း" if order.get("order_type") == "withdraw" else "🛍️ ဝယ်"
    bot.send_message(message.chat.id,
        f"📋 *နောက်ဆုံး Order*\n\n"
        f"{otype} 🆔 {order.get('order_id','-')}\n"
        f"🎮 {order['product']['name']}\n"
        f"🔢 {order.get('qty',0):,} Units\n"
        f"📊 {status}", parse_mode="Markdown")

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
        "❓ *အကူအညီ*\n\n"
        "1️⃣ 🛍️ ယူနစ်ဝယ်မယ် — Unit ဝယ်ရန်\n"
        "2️⃣ 💰 ယူနစ်ရောင်းမယ် — Unit ပြန်ရောင်းရန်\n"
        "3️⃣ 📋 မှာယူမှတ်တမ်း — Order စစ်ရန်\n"
        "4️⃣ 💳 ငွေပေးချေနည်း\n"
        "5️⃣ 📞 ဆက်သွယ်ရန်\n\n"
        "📞 09 940 940 010",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(message.chat.id, "🤔 Menu မှ ရွေးချယ်ပေးပါ 👇", reply_markup=get_main_menu())

print("🤖 MNL2admin Bot စတင်လည်ပတ်နေပြီ...")
bot.infinity_polling()
