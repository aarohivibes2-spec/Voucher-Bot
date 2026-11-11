import os
import io
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import qrcode
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ================= CONFIGURATION =================
# Render ke Environment Variables se ya direct yahan se token lega
BOT_TOKEN = os.environ.get("BOT_TOKEN", "9107862411:AAFwC_C2yx-5sEHtzCm-_MG8OuBBCwxBXio")
UPI_ID = os.environ.get("UPI_ID", "Paytm.s2b9rko@pty")  # Apni UPI ID yahan dalein
UPI_NAME = "Voucher Store"
ADMIN_USERNAME = "LYIHU1"
ADMIN_ID = 8687452366

CHANNELS = [
    ("Join Channel 1", "https://t.me/Giftandcreditcardproofs", "@Giftandcreditcardproofs"),
    ("Join Channel 2", "https://t.me/Amazon_refunds_all", "@Amazon_refunds_all")
]

VOUCHERS = {
    "amz_800": {"btn": "Amazon 800 - ₹499", "name": "Amazon Rs.800 Gift Card", "stock": 10, "tiers": {1: 499, 2: 489, 5: 479, 10: 459}},
    "amz_500": {"btn": "Amazon 500 - ₹249", "name": "Amazon Rs.500 Gift Card", "stock": 10, "tiers": {1: 249, 2: 239, 5: 229, 10: 209}},
    "flp_800": {"btn": "Flipkart 800 - ₹499", "name": "Flipkart Rs.800 Gift Card", "stock": 10, "tiers": {1: 499, 2: 489, 5: 479, 10: 459}},
    "mmt_10k": {"btn": "MakeMyTrip 10k - ₹1999", "name": "MakeMyTrip Rs.10000 Voucher", "stock": 5, "tiers": {1: 1999, 2: 1949, 5: 1899, 10: 1799}},
    "blk_1200": {"btn": "BlinkIt 1200 - ₹599", "name": "BlinkIt Rs.1200 Voucher", "stock": 8, "tiers": {1: 599, 2: 589, 5: 569, 10: 549}},
    "play_800": {"btn": "PlayStore 800 - ₹499", "name": "PlayStore Rs.800 Recharge Code", "stock": 12, "tiers": {1: 499, 2: 489, 5: 479, 10: 459}},
    "zom_800": {"btn": "Zomato 800 - ₹349", "name": "Zomato Rs.800 Voucher", "stock": 10, "tiers": {1: 349, 2: 339, 5: 329, 10: 309}},
    "swg_849": {"btn": "Swiggy 849 - ₹349", "name": "Swiggy Rs.849 Voucher", "stock": 10, "tiers": {1: 349, 2: 339, 5: 329, 10: 309}},
}

USER_WALLETS = {}
USER_ORDERS = {}
SAVED_QR_FILE_ID = None

# ================= RENDER KEEP-ALIVE SERVER =================
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7!")

def start_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# ================= HELPER FUNCTIONS =================
def generate_upi_qr(amount: float, order_id: str) -> io.BytesIO:
    upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={amount:.2f}&tn=Order_{order_id}&cu=INR"
    qr = qrcode.make(upi_link)
    bio = io.BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)
    return bio

def main_menu_keyboard():
    keyboard = [
        ["Buy Vouchers 🏷️", "History 📜"],
        ["Disclaimer ⚠️", "Support ☎️"],
        ["💰 Balance", "🏠 Main Menu"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def force_join_keyboard():
    buttons = [[InlineKeyboardButton(name, url=url)] for name, url, _ in CHANNELS]
    buttons.append([InlineKeyboardButton("✅ Verify Channels", callback_data="verify_join")])
    return InlineKeyboardMarkup(buttons)

async def is_user_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for _, _, chat_id in CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            continue
    return True

def get_unit_price(tiers: dict, qty: int) -> float:
    applicable_price = tiers[1]
    for tier_qty, price in sorted(tiers.items()):
        if qty >= tier_qty:
            applicable_price = price
    return float(applicable_price)

def voucher_list_keyboard():
    buttons, row = [], []
    for key, data in VOUCHERS.items():
        row.append(InlineKeyboardButton(data["btn"], callback_data=f"v|{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Hello {user.first_name}!\n\nBot use karne ke liye channels join karein:",
        reply_markup=force_join_keyboard(),
    )

async def send_welcome_menu(message):
    await message.reply_text(
        "✨ Welcome to Cheap Gift Code and Voucher Bot ✨\n\nNiche diye gaye buttons se navigate karein 👇",
        reply_markup=main_menu_keyboard(),
    )

async def save_qr_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global SAVED_QR_FILE_ID
    SAVED_QR_FILE_ID = update.message.photo[-1].file_id
    await update.message.reply_text("✅ **Custom QR Photo Set Ho Gayi Hai!**", parse_mode="Markdown")

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "verify_join":
        if await is_user_joined(user_id, context):
            await send_welcome_menu(query.message)
        else:
            await query.answer("❌ Kripya pehle dono channels join karein!", show_alert=True)

    elif data == "main_menu":
        context.user_data.clear()
        await send_welcome_menu(query.message)

    elif data == "back_to_vouchers":
        context.user_data.clear()
        text = "⚠️ Note: Video proof is mandatory for any support or claims.\n\n⚡ Select your voucher below:"
        if query.message.photo:
            await query.message.delete()
            await query.message.chat.send_message(text, reply_markup=voucher_list_keyboard())
        else:
            await query.edit_message_text(text, reply_markup=voucher_list_keyboard())

    elif data.startswith("v|"):
        v_key = data.split("|")[1]
        voucher = VOUCHERS.get(v_key)
        if not voucher:
            return
        tiers = voucher["tiers"]
        text = (
            f"🎁 {voucher['name']}\n"
            f"Available stock: {voucher['stock']} codes\n\n"
            f"Available Packages (per-code):\n"
            f"• 1 Code -> ₹{tiers[1]:.2f} / code\n"
            f"• 2 Codes -> ₹{tiers[2]:.2f} / code\n"
            f"• 5 Codes -> ₹{tiers[5]:.2f} / code\n"
            f"• 10 Codes -> ₹{tiers[10]:.2f} / code\n\n"
            f"Select quantity 👇"
        )
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("1 CODES*", callback_data=f"qty|{v_key}|1"),
                InlineKeyboardButton("5 CODES*", callback_data=f"qty|{v_key}|5"),
            ],
            [InlineKeyboardButton("✏️ Custom Quantity", callback_data=f"custom|{v_key}")],
            [
                InlineKeyboardButton("🔙 Back", callback_data="back_to_vouchers"),
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"),
            ],
        ])
        if query.message.photo:
            await query.message.delete()
            await query.message.chat.send_message(text, reply_markup=keyboard)
        else:
            await query.edit_message_text(text, reply_markup=keyboard)

    elif data.startswith("custom|"):
        v_key = data.split("|")[1]
        context.user_data["awaiting_custom_qty"] = v_key
        await query.message.reply_text("🔢 Kitne codes chahiye? Number type karke bhejein (e.g. 2, 3, 10):")

    elif data.startswith("qty|"):
        _, v_key, qty_str = data.split("|")
        await send_payment_qr(query.message, context, v_key, int(qty_str), delete_prev=True)

    elif data.startswith("paid|"):
        order_id = data.split("|")[1]
        context.user_data["awaiting_utr"] = order_id
        await query.message.reply_text("📲 Please send your 12-digit UTR Number:")

async def send_payment_qr(message, context, v_key: str, qty: int, delete_prev: bool = False):
    voucher = VOUCHERS[v_key]
    unit_price = get_unit_price(voucher["tiers"], qty)
    total = unit_price * qty
    order_id = f"SX{random.randint(10000000, 99999999)}"

    context.user_data["current_order"] = {
        "order_id": order_id,
        "voucher": voucher["name"],
        "qty": qty,
        "total": total,
    }

    caption = (
        f"💳 Payment for {voucher['name']}\n\n"
        f"📌 Order ID: {order_id}\n"
        f"🎁 Voucher: {voucher['name']}\n"
        f"🔢 Qty: {qty}\n"
        f"💰 Per Code: ₹{unit_price:.2f}\n"
        f"💵 Total: ₹{total:.2f}\n\n"
        f"⏳ QR valid for 10 minutes\n"
        f"👉 Scan & pay then tap 'I've paid' below."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("I've paid", callback_data=f"paid|{order_id}")],
        [
            InlineKeyboardButton("🔙 Back", callback_data=f"v|{v_key}"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu"),
        ],
    ])

    if delete_prev:
        try:
            await message.delete()
        except Exception:
            pass

    # Agar custom photo bheji hai toh woh dikhayega, warna automatic QR banayega
    qr_photo = SAVED_QR_FILE_ID if SAVED_QR_FILE_ID else generate_upi_qr(total, order_id)
    await message.chat.send_photo(photo=qr_photo, caption=caption, reply_markup=keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    if text == "Buy Vouchers 🏷️":
        context.user_data.clear()
        await update.message.reply_text(
            "⚠️ Note: Uncut screen recording is mandatory for any support or claims.\n\n⚡ Select your voucher below:",
            reply_markup=voucher_list_keyboard(),
        )
        return

    elif text == "History 📜":
        orders = USER_ORDERS.get(user_id, [])
        if not orders:
            await update.message.reply_text("📦 NO Orders Yet !!\n\nRecently placed orders will be shown here !!")
        else:
            lines = ["📜 **Your Recent Orders:**\n"]
            for o in orders[-5:]:
                lines.append(f"• `{o['order_id']}` - {o['voucher']} (x{o['qty']}) - ₹{o['total']:.2f} [{o['status']}]")
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    elif text == "Disclaimer ⚠️":
        await update.message.reply_text(
            "⚠️ Disclaimer\n\n• No Refund / Replacement Allowed\n• Contact Support for problems\n• No returns after purchasing\n• Prices are fixed !!"
        )
        return

    elif text == "Support ☎️":
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(f"💬 Message @{ADMIN_USERNAME}", url=f"https://t.me/{ADMIN_USERNAME}")]])
        await update.message.reply_text(f"📞 Contact @{ADMIN_USERNAME} for support\nUser ID: {user_id}", reply_markup=kb)
        return

    elif text == "💰 Balance":
        bal = USER_WALLETS.get(user_id, 0.0)
        await update.message.reply_text(f"💼 Your Wallet Balance: ₹{bal:.2f}")
        return

    elif text == "🏠 Main Menu":
        context.user_data.clear()
        await send_welcome_menu(update.message)
        return

    if "awaiting_custom_qty" in context.user_data:
        v_key = context.user_data.pop("awaiting_custom_qty")
        if text.isdigit() and 1 <= int(text) <= VOUCHERS[v_key]["stock"]:
            await send_payment_qr(update.message, context, v_key, int(text))
        else:
            await update.message.reply_text("❌ Invalid quantity! Stock ke andar valid number dalein.")
        return

    if "awaiting_utr" in context.user_data:
        if text.isdigit() and len(text) == 12:
            order_id = context.user_data.pop("awaiting_utr")
            order_info = context.user_data.get("current_order", {})
            order_info["utr"] = text
            order_info["status"] = "Pending Verification"
            USER_ORDERS.setdefault(user_id, []).append(order_info)

            await update.message.reply_text(
                f"✅ UTR `{text}` receive ho gaya hai!\n📌 Order ID: `{order_id}`\n\nPayment verify hote hi gift code bhej diya jayega.",
                parse_mode="Markdown",
            )
            try:
                msg = (
                    f"🔔 **New Order!**\n👤 User: `{user_id}`\n📌 Order: `{order_id}`\n"
                    f"🎁 Item: {order_info.get('voucher')}\n🔢 Qty: {order_info.get('qty')}\n"
                    f"💵 Total: ₹{order_info.get('total')}\n🏦 UTR: `{text}`"
                )
                await context.bot.send_message(chat_id=ADMIN_ID, text=msg, parse_mode="Markdown")
            except Exception:
                pass
        else:
            await update.message.reply_text("❌ Kripya valid 12-digit numeric UTR number bhejein:")
        return

def main():
    # Render ke liye background web server chalu karein
    threading.Thread(target=start_web_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, save_qr_photo))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
