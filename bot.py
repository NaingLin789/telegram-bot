import os
import telebot
from telebot import types
import json
from datetime import datetime

# ==============================
# CONFIG — သင့် Token ထည့်ပါ
# ==============================
BOT_TOKEN = "8128339594:AAFN8dMdZDxddMasbLJyyibEA4aWsN2rIPA"

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "သင့် Chat ID ထည့်ပါ")

bot = telebot.TeleBot(BOT_TOKEN)

# ==============================
# PRODUCTS LIST — ပြင်ချင်သလို ပြင်နိုင်
# ==============================
products = [
    {"id": 1, "name": "📦 Package A", "price": 5000,  "units": 10,  "desc": "10 Units"},
    {"id": 2, "name": "📦 Package B", "price": 10000, "units": 25,  "desc": "25 Units"},
    {"id": 3, "name": "📦 Package C", "price": 20000, "units": 60,  "desc": "60 Units"},
    {"id": 4, "name": "💎 VIP Package","price": 50000, "units": 200, "desc": "200 Units + Bonus"},
]

# ==============================
# PAYMENT INFO — ပြင်ချင်သလို ပြင်နိုင်
# ==============================
PAYMENT_INFO = """
💳 *ငွေပေးချေရန်*

🟢 KPay   — `09xxxxxxxxx`
🔵 Wave   — `09xxxxxxxxx`  
🟡 AyaPay — `09xxxxxxxxx`
🏦 Bank   — `Account No ထည့်`

⚠️ ငွေလွှဲပြီးရင် Slip ဓာတ်ပုံ ဒီမှာ ပို့ပေးပါ
"""

# ==============================
# ORDER STORAGE (In-memory)
# ==============================
orders = {}
order_counter = {"count": 1000}

# ==============================
# HELPERS
# ==============================
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🛍️ ကုန်ပစ္စည်းများ"),
        types.KeyboardButton("🛒 မှာယူမယ်"),
        types.KeyboardButton("📋 မှာယူမှတ်တမ်း"),
        types.KeyboardButton("💳 ငွေပေးချေနည်း"),
        types.KeyboardButton("📞 ဆက်သွယ်ရန်"),
        types.KeyboardButton("❓ အကူအညီ"),
    )
    return markup

def new_order_id():
    order_counter["count"] += 1
    return f"ORD{order_counter['count']}"

def notify_admin(text):
    try:
        bot.send_message(ADMIN_CHAT_ID, text, parse_mode="Markdown")
    except:
        pass

# ==============================
# /start
# ==============================
@bot.message_handler(commands=["start"])
def start(message):
    name = message.from_user.first_name or "Customer"
    bot.send_message(
        message.chat.id,
        f"👋 မင်္ဂလာပါ *{name}* !\n\n"
        f"ကျွန်ုပ်တို့ Shop မှ ကြိုဆိုပါတယ် 🎉\n\n"
        f"ဘာကူညီပေးရမလဲ?",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

# ==============================
# ကုန်ပစ္စည်းများ ပြ
# ==============================
@bot.message_handler(func=lambda m: m.text == "🛍️ ကုန်ပစ္စည်းများ")
def show_products(message):
    bot.send_message(message.chat.id, "📦 *ကျွန်ုပ်တို့ Packages များ*", parse_mode="Markdown")
    
    for p in products:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(
            f"🛒 ဒါယူမယ်", callback_data=f"buy_{p['id']}"
        ))
        bot.send_message(
            message.chat.id,
            f"*{p['name']}*\n"
            f"💰 {p['price']:,} Ks\n"
            f"📊 {p['desc']}",
            parse_mode="Markdown",
            reply_markup=markup
        )

# ==============================
# မှာယူမယ် Button
# ==============================
@bot.message_handler(func=lambda m: m.text == "🛒 မှာယူမယ်")
def order_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(
            f"{p['name']} — {p['price']:,}Ks",
            callback_data=f"buy_{p['id']}"
        ) for p in products
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "📦 Package ရွေးချယ်ပါ —", reply_markup=markup)

# ==============================
# Package ရွေးချယ်
# ==============================
@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def handle_buy(call):
    product_id = int(call.data.split("_")[1])
    product = next((p for p in products if p["id"] == product_id), None)
    if not product:
        return
    
    orders[call.from_user.id] = {
        "product": product,
        "step": "name",
        "order_id": new_order_id(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        f"✅ *{product['name']}* ရွေးချယ်ပြီး\n\n"
        f"👤 သင့်နာမည် ရိုက်ထည့်ပေးပါ —",
        parse_mode="Markdown"
    )

# ==============================
# Order Steps — Name → Phone → Confirm → Payment
# ==============================
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
        bot.send_message(message.chat.id, "🔢 အရေအတွက် ဘယ်လောက်ယူမလဲ?")
    
    elif step == "qty":
        try:
            qty = int(message.text)
            if qty <= 0:
                raise ValueError
            
            order["qty"] = qty
            order["total"] = qty * order["product"]["price"]
            order["step"] = "waiting_payment"
            
            # Order Summary
            summary = (
                f"📋 *မှာယူမှတ်တမ်း*\n\n"
                f"🆔 Order ID — `{order['order_id']}`\n"
                f"👤 နာမည် — {order['customer_name']}\n"
                f"📱 ဖုန်း — {order['phone']}\n"
                f"📦 Package — {order['product']['name']}\n"
                f"🔢 အရေအတွက် — {qty}\n"
                f"💰 စုစုပေါင်း — *{order['total']:,} Ks*\n"
            )
            
            # Confirm Buttons
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("✅ အတည်ပြုမယ်", callback_data=f"confirm_{uid}"),
                types.InlineKeyboardButton("❌ ပြန်မယ်", callback_data=f"cancel_{uid}")
            )
            
            bot.send_message(message.chat.id, summary, parse_mode="Markdown", reply_markup=markup)
        
        except ValueError:
            bot.send_message(message.chat.id, "❌ နံပါတ် မှန်မှန် ရိုက်ပေးပါ")

# ==============================
# Confirm / Cancel
# ==============================
@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm_"))
def handle_confirm(call):
    uid = int(call.data.split("_")[1])
    order = orders.get(uid)
    if not order:
        return
    
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, PAYMENT_INFO, parse_mode="Markdown")
    
    # Admin notify
    notify_admin(
        f"🔔 *အသစ် Order ဝင်လာပြီ!*\n\n"
        f"🆔 {order['order_id']}\n"
        f"👤 {order['customer_name']} ({order['phone']})\n"
        f"📦 {order['product']['name']} x{order['qty']}\n"
        f"💰 {order['total']:,} Ks\n"
        f"🕐 {order['timestamp']}"
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("cancel_"))
def handle_cancel(call):
    uid = int(call.data.split("_")[1])
    if uid in orders:
        del orders[uid]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "❌ မှာယူမှု ပယ်ဖျက်ပြီ", reply_markup=get_main_menu())

# ==============================
# Slip လက်ခံ
# ==============================
@bot.message_handler(
    content_types=["photo"],
    func=lambda m: m.from_user.id in orders and orders[m.from_user.id].get("step") == "waiting_payment"
)
def handle_slip(message):
    uid = message.from_user.id
    order = orders[uid]
    order["step"] = "paid"
    
    # Customer ကို confirm
    bot.send_message(
        message.chat.id,
        f"✅ *Slip လက်ခံပြီး!*\n\n"
        f"🆔 Order ID — `{order['order_id']}`\n"
        f"⏳ စစ်ဆေးပြီး မကြာမီ Product ပို့ပေးပါမည်\n\n"
        f"ကျေးဇူးတင်ပါတယ် 🙏",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )
    
    # Admin ကို Slip ပို့
    bot.forward_message(ADMIN_CHAT_ID, message.chat.id, message.message_id)
    notify_admin(
        f"💳 *Slip ရောက်လာပြီ!*\n"
        f"🆔 {order['order_id']} — {order['customer_name']}\n"
        f"💰 {order['total']:,} Ks\n"
        f"📞 {order['phone']}"
    )

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
    status = "✅ Slip ပို့ပြီး" if order.get("step") == "paid" else "⏳ ငွေပေးချေဆဲ"
    
    bot.send_message(
        message.chat.id,
        f"📋 *နောက်ဆုံး Order*\n\n"
        f"🆔 {order.get('order_id', '-')}\n"
        f"📦 {order['product']['name']}\n"
        f"💰 {order.get('total', 0):,} Ks\n"
        f"📊 Status — {status}",
        parse_mode="Markdown"
    )

# ==============================
# ငွေပေးချေနည်း
# ==============================
@bot.message_handler(func=lambda m: m.text == "💳 ငွေပေးချေနည်း")
def payment_info(message):
    bot.send_message(message.chat.id, PAYMENT_INFO, parse_mode="Markdown")

# ==============================
# ဆက်သွယ်ရန်
# ==============================
@bot.message_handler(func=lambda m: m.text == "📞 ဆက်သွယ်ရန်")
def contact(message):
    bot.send_message(
        message.chat.id,
        "📞 *ဆက်သွယ်ရန်*\n\n"
        "📱 Phone — 09xxxxxxxxx\n"
        "💬 Telegram — @yourusername\n"
        "🕐 ဆက်သွယ်နိုင်သည့်အချိန် — ၉နာရီ မှ ၉နာရီ",
        parse_mode="Markdown"
    )

# ==============================
# အကူအညီ
# ==============================
@bot.message_handler(func=lambda m: m.text == "❓ အကူအညီ")
def help_msg(message):
    bot.send_message(
        message.chat.id,
        "❓ *အကူအညီ*\n\n"
        "1️⃣ 🛍️ *ကုန်ပစ္စည်းများ* — Package များ ကြည့်ရှုရန်\n"
        "2️⃣ 🛒 *မှာယူမယ်* — Order တင်ရန်\n"
        "3️⃣ 📋 *မှာယူမှတ်တမ်း* — Order status ကြည့်ရန်\n"
        "4️⃣ 💳 *ငွေပေးချေနည်း* — Payment info\n"
        "5️⃣ 📞 *ဆက်သွယ်ရန်* — Admin ဆက်သွယ်ရန်\n\n"
        "ပြဿနာရှိရင် Admin ကို တိုက်ရိုက်ဆက်သွယ်နိုင်ပါတယ် 😊",
        parse_mode="Markdown"
    )

# ==============================
# Unknown messages
# ==============================
@bot.message_handler(func=lambda m: True)
def unknown(message):
    bot.send_message(
        message.chat.id,
        "🤔 နားမလည်ပါ။ Menu မှ ရွေးချယ်ပေးပါ 👇",
        reply_markup=get_main_menu()
    )

# ==============================
# RUN
# ==============================
print("🤖 Bot စတင်လည်ပတ်နေပြီ...")
bot.infinity_polling()
