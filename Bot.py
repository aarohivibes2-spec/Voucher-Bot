import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = "9125266348:AAEuyWFx3ODZLDoo1Iji63rA1n-5WpI_D-I"  # Apna BotFather se mila token yahan daalein
REQUIRED_CHANNELS = ["@latest_instagram_viral", "@paid_premium_video"] # Apne channels ka username daalein

# User state track karne ke liye (Production me Database use karein)
user_verified = {}

# --- 1. Start Command & Channel Check ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Check if user verified channels (For testing, default False)
    if not user_verified.get(user_id, False):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/Latest_Instagram_Viral")],
            [InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/Paid_Premium_Video")],
            [InlineKeyboardButton("✅ Verify Channels", callback_data="verify_channels")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"👋 Hello {update.effective_user.first_name}!\n\nBot use karne ke liye channels join karein:",
            reply_markup=reply_markup
        )
    else:
        await show_main_menu(update, context)

# --- 2. Verification Callback ---
async def verify_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Yahan aap actual channel membership check laga sakte hain (context.bot.get_chat_member)
    user_verified[user_id] = True
    
    await query.message.delete()
    
    # Welcome message + Reply Keyboard (Bottom Buttons)
    text = "✨ Welcome to Cheap Gift Code and Voucher Bot ✨\n\nNiche diye gaye buttons se navigate karein 👇"
    
    reply_markup = ReplyKeyboardMarkup([
        [KeyboardButton("Buy Vouchers 🎟"), KeyboardButton("History 📜")],
        [KeyboardButton("Disclaimer ⚠️"), KeyboardButton("Support ☎️")],
        [KeyboardButton("💰 Balance"), KeyboardButton("🔙 Main Menu")]
    ], resize_keyboard=True)
    
    await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "✨ Welcome back to Main Menu ✨\n\nNiche diye gaye buttons se navigate karein 👇"
    reply_markup = ReplyKeyboardMarkup([
        [KeyboardButton("Buy Vouchers 🎟"), KeyboardButton("History 📜")],
        [KeyboardButton("Disclaimer ⚠️"), KeyboardButton("Support ☎️")],
        [KeyboardButton("💰 Balance"), KeyboardButton("🔙 Main Menu")]
    ], resize_keyboard=True)
    await update.message.reply_text(text, reply_markup=reply_markup)

# --- 3. Handle Reply Keyboard Buttons ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if not user_verified.get(user_id, False):
        await start(update, context)
        return

    if text == "Buy Vouchers 🎟":
        guidelines = (
            "🛒 **Purchase Guidelines:**\n"
            "Please record a continuous screen video from payment until voucher redemption. "
            "An uncut screen recording is mandatory for any support or claims.\n\n"
            "⚡ **Select your voucher below:**"
        )
        
        keyboard = [
            [InlineKeyboardButton("Amazon 800 - ₹499", callback_data="buy_amz_800"), InlineKeyboardButton("Amazon 500 - ₹249", callback_data="buy_amz_500")],
            [InlineKeyboardButton("Flipkart 800 - ₹499", callback_data="buy_FK_800"), InlineKeyboardButton("MakeMyTrip 10k - ₹1999", callback_data="buy_mmt_10k")],
            [InlineKeyboardButton("MakeMyTrip 1200 - ₹499", callback_data="buy_mmt_1200"), InlineKeyboardButton("BigBasket 800 - ₹399", callback_data="buy_bb_800")],
            [InlineKeyboardButton("Blinkit 1200 - ₹599", callback_data="buy_blinkit_1200"), InlineKeyboardButton("PlayStore 800 - ₹499", callback_data="buy_play_800")],
            [InlineKeyboardButton("PVR 849 - ₹349", callback_data="buy_pvr_849"), InlineKeyboardButton("Instamart 1000 - ₹499", callback_data="buy_instamart_1000")],
            [InlineKeyboardButton("Swiggy 849 - ₹349", callback_data="buy_swiggy_849"), InlineKeyboardButton("Zomato 800 - ₹349", callback_data="buy_zomato_800")],
            [InlineKeyboardButton("BookMyShow 2k - ₹799", callback_data="buy_bms_2k"), InlineKeyboardButton("Brevistay 2000 - ₹799", callback_data="buy_brevistay_2000")],
            [InlineKeyboardButton("Uber 700 - ₹299", callback_data="buy_uber_700"), InlineKeyboardButton("JioMart 3000 - ₹1500", callback_data="buy_jiomart_3000")],
            [InlineKeyboardButton("JioMart 1200 - ₹500", callback_data="buy_jiomart_1200")]
        ]
        
        await update.message.reply_text(guidelines, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
   
    elif text == "History 📜":
        await update.message.reply_text("📜 Aapki purchase history khali hai.")
    
    elif text == "Disclaimer ⚠️":
        await update.message.reply_text("⚠️ **Disclaimer:** All vouchers are checked before delivery. We are not responsible after redemption.")
    
    elif text == "Support ☎️":
        await update.message.reply_text("☎️ Kisi bhi madad ke liye contact karein: @Lyihu")
    
    elif text == "💰 Balance":
        await update.message.reply_text("💰 Aapka Wallet Balance: **₹0.00**", parse_mode="Markdown")
    
    elif text == "🔙 Main Menu":
        await show_main_menu(update, context)

# --- Main Function ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_channels, pattern="verify_channels"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is up and running...")
    app.run_polling()

if __name__ == '__main__':
    main()
