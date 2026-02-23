import asyncio
import os
from telegram import (
    Update,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)

# ======================================
# تنظیمات
# ======================================

TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "Bnd_3346bot"
MAIN_ADMINS = [1092487850, 7337011539]

# ======================================
# بررسی مدیر اصلی
# ======================================

def is_main_admin(user_id: int) -> bool:
    return user_id in MAIN_ADMINS

# ======================================
# استارت حرفه‌ای
# ======================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    text = (
        f"👋 سلام {user.first_name}\n\n"
        "🤖 به ربات مدیریت گروه خوش آمدی!\n\n"
        "✨ امکانات من:\n"
        "• خوش‌آمدگویی خودکار\n"
        "• سیستم آنتی لینک\n"
        "• پنل مدیریت حرفه‌ای\n\n"
        "👇 از دکمه‌های زیر استفاده کن:"
    )

    keyboard = [
        [InlineKeyboardButton("➕ افزودن به گروه",
         url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
        [InlineKeyboardButton("📖 راهنمای ربات", callback_data="help")]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ======================================
# راهنمای ربات
# ======================================

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    help_text = (
        "📌 راهنمای استفاده از ربات:\n\n"
        "1️⃣ ربات را به گروه اضافه کنید\n"
        "2️⃣ ربات را ادمین کنید\n"
        "3️⃣ تمام دسترسی‌ها را فعال کنید\n\n"
        "🛡 برای باز کردن پنل مدیریت:\n"
        "دستور /panel را در گروه ارسال کنید"
    )

    await query.message.reply_text(help_text)

# ======================================
# خوش‌آمدگویی
# ======================================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    for member in update.message.new_chat_members:
        msg = await update.message.reply_text(
            f"👋 خوش آمدی {member.full_name}\n"
            f"🆔 آیدی عددی: {member.id}"
        )

        await asyncio.sleep(60)
        try:
            await msg.delete()
        except:
            pass

# ======================================
# فیلتر لینک
# ======================================

async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    if not update.message.text:
        return

    user = update.effective_user
    text_raw = update.message.text

    if "http" in text_raw or "t.me" in text_raw:
        await update.message.delete()
        await update.effective_chat.send_message(
            f"🚫 {user.full_name} ارسال لینک ممنوع است."
        )

# ======================================
# پنل مدیریتی
# ======================================

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_main_admin(update.effective_user.id):
        return

    keyboard = [
        [InlineKeyboardButton("🔒 قفل گروه", callback_data="lock")],
        [InlineKeyboardButton("🔓 باز کردن گروه", callback_data="unlock")],
    ]

    await update.message.reply_text(
        "پنل مدیریت:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "lock":
        await query.message.chat.set_permissions(
            ChatPermissions(can_send_messages=False)
        )
        await query.message.reply_text("🔒 گروه قفل شد.")

    elif query.data == "unlock":
        await query.message.chat.set_permissions(
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
        )
        await query.message.reply_text("🔓 گروه باز شد.")

    elif query.data == "help":
        await help_callback(update, context)

# ======================================
# اجرای ربات
# ======================================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_messages))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
