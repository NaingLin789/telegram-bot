import os
import asyncio
import telebot
from telebot import types
from datetime import datetime
import threading

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = "8128339594:AAFN8dMdZDxddMasbLJyyibEA4aWsN2rIPA"
ADMIN_CHAT_ID = "6670652112"

bot = telebot.TeleBot(BOT_TOKEN)

# ==============================
# PRODUCTS
# ==============================
products = {
    "batman": {"name": "🦇 Batman Unit", "price": 1,    "desc": "1 Unit = 1 Ks", "site": "batman"},
    "ibet":   {"name": "🎰 Ibet Unit",   "price": 1000, "desc": "1 Unit = 1,000 Ks", "site": "ibet"},
    "mix555": {"name": "🎲 555mix Unit", "price": 1,    "desc": "1 Unit = 1 Ks", "site": "mix555"},
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
        types.KeyboardButton("📋 မှာယူမှတ်တမ်း"),
        types.KeyboardButton("💳 ငွေပေးချေနည်း"),
        types.KeyboardButton("📞 ဆက်သွယ်ရန်"),
        types.KeyboardButton("❓ အကူအညီ"),
    )
    return markup

# ==============================
# AUTO PROCESS ORDER
# ==============================
def process_order_auto(order, customer_chat_id):
    """Batman အကောင့်သစ် သို့မဟုတ် DEP Auto လုပ်"""
    try:
        from batman_automation import add_player, deposit, withdraw
        
        product_key = order.get("product_key", "")
        
        # Batman သာ Auto လုပ်နိုင်သေးတယ် (Ibet/555 နောက်မှ ထည့်မယ်)
        if product_key != "batman":
            notify_admin(
                f"⚠️ *{order['product']['name']}* Auto မရသေးပါ\n"
                f"Manual လုပ်ပေးပါ\n\n"
                f"🆔 {order['order_id']}\n"
                f"👤 {order['customer_name']}\n"
                f"🔢 {order['qty']:,} Units\n"
                f"📱 {order['account_type']}"
            )
            return

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        if order["account_type"] == "အကောင့်သစ်":
            # Add new player
            result = loop.run_until_complete(
                add_player(order["customer_name"], order["qty"])
            )
            
            if result["success"]:
                # Customer ကို ပို့
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
                # Admin ကိုလည်း သတိပေး
                notify_admin(
                    f"✅ *Auto အကောင့်ဖွင့်ပြီး*\n"
                    f"🆔 {order['order_id']}\n"
                    f"👤 {order['customer_name']}\n"
                    f"Batman ID: {result['username']}\n"
                    f"Score: {result['score']:,}"
                )
            else:
                # Auto မအောင်မြင်ရင် Admin ကို Manual လုပ်ခိုင်း
                notify_admin(
                    f"❌ *Auto မအောင်မြင်ပါ — Manual လုပ်ပေးပါ*\n\n"
                    f"🆔 {order['order_id']}\n"
                    f"👤 {order['customer_name']} ({order['phone']})\n"
                    f"🔢 {order['qty']:,} Units\n"
                    f"📱 အကောင့်သစ်\n\n"
                    f"📨 `/send {order['order_id']} [message]`"
                )
                bot.send_message(
                    customer_chat_id,
                    "⏳ Order လက်ခံပြီး၊ မကြာမီ အကောင့် ပို့ပေးပါမည် 🙏",
                    reply_markup=get_main_menu()
                )

        else:
            # Deposit to existing account
            player_id = order.get("old_account_id", "")
            result = loop.run_until_complete(
                deposit(player_id, order["qty"])
            )
            
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
                notify_admin(
                    f"✅ *Auto DEP ပြီး*\n"
                    f"🆔 {order['order_id']}\n"
                    f"Batman ID: {player_id}\n"
                    f"Amount: {order['qty']:,}"
                )
            else:
                notify_admin(
                    f"❌ *Auto DEP မအောင်မြင် — Manual လုပ်ပေးပါ*\n\n"
                    f"🆔 {order['order_id']}\n"
                    f"👤 {order['customer_name']}\n"
                    f"Batman ID: {player_id}\n"
                    f"Amount: {order['qty']:,}\n\n"
                    f"📨 `/send {order['order_id']} [message]`"
                )
                bot.send_message(
                    customer_chat_id,
                    "⏳ Order လက်ခံပြီး၊ မကြာမီ Unit ဖြည့်ပေးပါမည် 🙏",
                    reply_markup=get_main_menu()
                )
        
        loop.close()
        
    except Exception as e:
        print(f"Process order error: {e}")
        notify_admin(f"❌ Auto Error: {str(e)}\n\n`/send {order['order_id']} [message]` နဲ့ Manual လုပ်ပေးပါ")

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
            bot.send_message(message.chat.id,
                "❌ Format —\n`/send ORD1001 message`",
                parse_mode="Markdown")
            return

        order_id = parts[1].upper()
        reply_text = parts[2]

        if order_id not in order_by_id:
            bot.send_message(message.chat.id, f"❌ Order ID `{order_id}` မတွေ့ပါ", parse_mode="Markdown")
            return

        customer_uid = order_by_id[order_id]
        order = orders.get(customer_uid)

        bot.send_message(
            customer_uid,
            f"✅ *သင့် Order အတွက် အချက်အလက်*\n\n"
            f"🆔 Order ID — `{order_id}`\n\n"
            f"{reply_text}\n\n"
            f"ကျေးဇူးတင်ပါတယ် 🙏",
            parse_mode="Markdown"
        )
        bot.send_message(message.chat.id, f"✅ Customer ဆီ ပို့ပြီး — {order_id}")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Error: {str(e)}")

@bot.message_handler(commands=["orders"])
def admin_orders(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    if not orders:
        bot.send_message(message.chat.id, "📭 Order မရှိသေးပါ")
        return

    text = "📋 *Order စာရင်း*\n\n"
    for uid, order in orders.items():
        status_map = {
            "paid": "✅ Slip ပို့ပြီး",
            "waiting_payment": "⏳ ငွေပေးချေဆဲ",
            "completed": "🎉 ပြီးဆုံး",
        }
        status = status_map.get(order.get("step", ""), "🔄 Processing")
        acc_id = f" (ID: {order.get('old_account_id', '-')})" if order.get('old_account_id') else ""
        text += (
            f"🆔 `{order.get('order_id', '-')}`\n"
            f"👤 {order.get('customer_name', '-')} | 📱 {order.get('phone', '-')}\n"
            f"🎮 {order['product']['name']} x{order.get('qty', 0):,}\n"
            f"📱 {order.get('account_type', '-')}{acc_id}\n"
            f"💰 {order.get('total', 0):,} Ks | {status}\n"
            f"{'─'*20}\n"
        )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=["adminhelp"])
def admin_help(message):
    if str(message.chat.id) != ADMIN_CHAT_ID:
        return
    bot.send_message(
        message.chat.id,
        "🔧 *Admin Commands*\n\n"
        "📋 `/orders` — Order အားလုံး\n"
        "📨 `/send ORD1001 message` — Customer ကို ပို့\n",
        parse_mode="Markdown"
    )

# ==============================
# ယူနစ်ဝယ်မယ်
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
        "product_key": prod_key,
        "product": product,
        "step": "account_type",
        "order_id": order_id,
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
    bot.send_message(
        call.message.chat.id,
        f"✅ *{product['name']}* ရွေးချယ်ပြီး\n\n"
        f"📱 အကောင့်သစ် ယူမလား၊ အကောင့်ဟောင်း ယူမလား?",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda c: c.data in ["acc_new", "acc_old"])
def handle_account_type(call):
    uid = call.from_user.id
    if uid not in orders:
        return
    bot.answer_callback_query(call.id)
    if call.data == "acc_new":
        orders[uid]["account_type"] = "အကောင့်သစ်"
        orders[uid]["step"] = "name"
        bot.send_message(call.message.chat.id,
            "🆕 *အကောင့်သစ်* ယူမည်\n\n👤 သင့်နာမည် ရိုက်ထည့်ပေးပါ —",
            parse_mode="Markdown")
    else:
        orders[uid]["account_type"] = "အကောင့်ဟောင်း"
        orders[uid]["step"] = "old_account_id"
        bot.send_message(call.message.chat.id,
            "♻️ *အကောင့်ဟောင်း* ယူမည်\n\n🆔 အကောင့် ID ရိုက်ထည့်ပေးပါ —",
            parse_mode="Markdown")

@bot.message_handler(func=lambda m: (
    m.from_user.id in orders and
    orders[m.from_user.id].get("step") == "old_account_id"
))
def handle_old_account_id(message):
    uid = message.from_user.id
    orders[uid]["old_account_id"] = message.text
    orders[uid]["step"] = "name"
    bot.send_message(message.chat.id,
        f"✅ Account ID — `{message.text}`\n\n👤 သင့်နာမည် ရိုက်ထည့်ပေးပါ —",
        parse_mode="Markdown")

@bot.message_handler(func=lambda m: (
    m.from_user.id in orders and
    orders[m.from_user.id].get("step") in ["name", "phone", "qty"]
))
def handle_order_steps(message):
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
        bot.send_message(message.chat.id,
            f"🔢 {order['product']['name']} ဘယ်နှစ် Unit ယူမလဲ?\n({order['product']['desc']})")

    elif step == "qty":
        try:
            qty = int(message.text)
            if qty <= 0:
                raise ValueError
            order["qty"] = qty
            order["total"] = qty * order["product"]["price"]
            order["step"] = "waiting_payment"

            acc_info = ""
            if order.get("old_account_id"):
                acc_info = f"🆔 Account ID — `{order['old_account_id']}`\n"

            summary = (
                f"📋 *မှာယူမှတ်တမ်း*\n\n"
                f"🆔 Order ID — `{order['order_id']}`\n"
                f"👤 နာမည် — {order['customer_name']}\n"
                f"📱 ဖုန်း — {order['phone']}\n"
                f"🎮 ယူနစ် — {order['product']['name']}\n"
                f"📱 အကောင့် — {order['account_type']}\n"
                f"{acc_info}"
                f"🔢 အရေအတွက် — {qty:,} Units\n"
                f"💰 စုစုပေါင်း — *{order['total']:,} Ks*\n"
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
    if not order:
        return
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, PAYMENT_INFO, parse_mode="Markdown")
    acc_info = f"\n🆔 Account ID — {order.get('old_account_id', 'အသစ်')}"
    notify_admin(
        f"🔔 *အသစ် Order ဝင်လာပြီ!*\n\n"
        f"🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} ({order['phone']})\n"
        f"🎮 {order['product']['name']} x{order['qty']:,} Units\n"
        f"📱 {order['account_type']}{acc_info}\n"
        f"💰 {order['total']:,} Ks\n"
        f"🕐 {order['timestamp']}\n\n"
        f"📨 Manual ပို့ရန် —\n`/send {order['order_id']} [message]`"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def handle_cancel(call):
    uid = int(call.data.split("_")[1])
    if uid in orders:
        order = orders[uid]
        if order.get("order_id") in order_by_id:
            del order_by_id[order["order_id"]]
        del orders[uid]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "❌ မှာယူမှု ပယ်ဖျက်ပြီ", reply_markup=get_main_menu())

# ==============================
# Slip လက်ခံ — Auto Process
# ==============================
@bot.message_handler(
    content_types=["photo"],
    func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") == "waiting_payment"
)
def handle_slip(message):
    uid = message.from_user.id
    order = orders[uid]
    order["step"] = "processing"

    bot.send_message(
        message.chat.id,
        f"✅ *Slip လက်ခံပြီး!*\n\n"
        f"🆔 Order ID — `{order['order_id']}`\n"
        f"⏳ စစ်ဆေးပြီး မကြာမီ ပို့ပေးပါမည်...\n\n"
        f"ကျေးဇူးတင်ပါတယ် 🙏",
        parse_mode="Markdown"
    )

    bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
    notify_admin(
        f"💳 *Slip ရောက်လာပြီ — Auto Processing...*\n\n"
        f"🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} | 📞 {order['phone']}\n"
        f"🎮 {order['product']['name']} x{order['qty']:,}\n"
        f"📱 {order['account_type']}"
        f"{(' | ID: ' + order['old_account_id']) if order.get('old_account_id') else ''}\n"
        f"💰 {order['total']:,} Ks"
    )

    # Auto process in background thread
    thread = threading.Thread(
        target=process_order_auto,
        args=(order.copy(), uid)
    )
    thread.daemon = True
    thread.start()

# ==============================
# မှာယူမှတ်တမ်း
# ==============================
@bot.message_handler(func=lambda m: m.text == "📋 မှာယူမှတ်တမ်း")
def order_history(message):
    uid = message.from_user.id
    if uid not in orders:
        bot.send_message(message.chat.id, "📭 မှာယူမှတ်တမ်း မရှိသေးပါ")
        return
    order = orders[uid]
    status_map = {
        "paid": "✅ Slip ပို့ပြီး",
        "waiting_payment": "⏳ ငွေပေးချေဆဲ",
        "processing": "🔄 Processing",
        "completed": "🎉 ပြီးဆုံး",
    }
    status = status_map.get(order.get("step", ""), "🔄")
    bot.send_message(
        message.chat.id,
        f"📋 *နောက်ဆုံး Order*\n\n"
        f"🆔 {order.get('order_id', '-')}\n"
        f"🎮 {order['product']['name']}\n"
        f"🔢 {order.get('qty', 0):,} Units\n"
        f"💰 {order.get('total', 0):,} Ks\n"
        f"📊 Status — {status}",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "💳 ငွေပေးချေနည်း")
def payment_info(message):
    bot.send_message(message.chat.id, PAYMENT_INFO, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📞 ဆက်သွယ်ရန်")
def contact(message):
    bot.send_message(
        message.chat.id,
        "📞 *ဆက်သွယ်ရန်*\n\n"
        "🏪 MNL2admin ကိုနိုင်လင်းယူနစ်အရောင်းဆိုင်\n"
        "📱 ဖုန်း — `09 940 940 010`\n"
        "🕐 ၉နာရီ မှ ၉နာရီ",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: m.text == "❓ အကူအညီ")
def help_msg(message):
    bot.send_message(
        message.chat.id,
        "❓ *အကူအညီ*\n\n"
        "1️⃣ 🛍️ *ယူနစ်ဝယ်မယ်* — Unit မှာယူရန်\n"
        "2️⃣ 📋 *မှာယူမှတ်တမ်း* — Order status\n"
        "3️⃣ 💳 *ငွေပေးချေနည်း* — Payment info\n"
        "4️⃣ 📞 *ဆက်သွယ်ရန်* — Admin ဆက်သွယ်\n\n"
        "📞 09 940 940 010",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "🤔 နားမလည်ပါ။ Menu မှ ရွေးချယ်ပေးပါ 👇",
        reply_markup=get_main_menu()
    )

print("🤖 MNL2admin Bot စတင်လည်ပတ်နေပြီ...")
bot.infinity_polling()
