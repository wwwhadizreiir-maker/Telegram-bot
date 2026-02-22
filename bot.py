import asyncio
import re
import os
from datetime import datetime, timedelta
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

# =========================
# تنظیمات اصلی
# =========================

TOKEN = os.getenv("BOT_TOKEN")
MAIN_ADMINS = [1092487850, 7337011539]

warnings = {}
mute_levels = {}

# =========================
# بررسی مدیر اصلی
# =========================

def is_main_admin(update: Update):
    return update.effective_user.id in MAIN_ADMINS

# =========================
# خوش آمدگویی
# =========================

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    for member in update.message.new_chat_members:
        text = (
            f"👋 خوش آمدی {member.full_name}\n"
            f"🆔 آیدی عددی شما: {member.id}"
        )

        sent = await update.message.reply_text(text)

        await asyncio.sleep(60)
        try:
            await sent.delete()
        except:
            pass

# =========================
# لیست کلمات ممنوع
# =========================

BAD_WORDS = [
    "کسکش", "کصکش", "کیر", "کص", "جنده",
    "حرومزاده", "پدرسوخته", "کونی",
    "بیناموس", "احمق", "آشغال"
]

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"(.)\1+", r"\1", text)
    text = text.replace(" ", "")
    return text

def reset_if_needed(user_id):
    if user_id in warnings:
        last = warnings[user_id]["last_offense"]
        if last and datetime.utcnow() - last > timedelta(days=2):
            warnings[user_id] = {"count": 0, "last_offense": None}
            mute_levels[user_id] = 0

# =========================
# سیستم مجازات پلکانی
# =========================

async def apply_punishment(update, context, user_id, full_name):
    level = mute_levels.get(user_id, 0)

    if level == 0:
        hours = 1
    elif level == 1:
        hours = 6
    elif level == 2:
        hours = 24
    else:
        await context.bot.ban_chat_member(
            chat_id=update.effective_chat.id,
            user_id=user_id
        )
        await update.effective_chat.send_message(
            f"⛔ {full_name} برای همیشه بن شد."
        )
        return

    until_time = datetime.utcnow() + timedelta(hours=hours)

    await context.bot.restrict_chat_member(
        chat_id=update.effective_chat.id,
        user_id=user_id,
        permissions=ChatPermissions(can_send_messages=False),
        until_date=until_time,
    )

    await update.effective_chat.send_message(
        f"🚫 {full_name} به مدت {hours} ساعت محدود شد."
    )

    mute_levels[user_id] = level + 1

    async def reset_after():
        await asyncio.sleep(hours * 3600)
        warnings[user_id] = {"count": 0, "last_offense": None}

    asyncio.create_task(reset_after())

# =========================
# فیلتر پیام‌ها
# =========================

async def filter_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ["group", "supergroup"]:
        return

    if not update.message.text:
        return

    user = update.effective_user
    user_id = user.id
    text_raw = update.message.text
    text = normalize_text(text_raw)

    reset_if_needed(user_id)

    # آنتی لینک
    if "http" in text_raw or "t.me" in text_raw:
        await update.message.delete()
        await update.effective_chat.send_message(
            f"🚫 {user.full_name} ارسال لینک ممنوع است."
        )
        return

               # فحش
    for word in BAD_WORDS:
        if word in text:
            await update.message.delete()

            if user_id not in warnings:
                warnings[user_id] = {"count": 0, "last_offense": None}

            warnings[user_id]["count"] += 1
            warnings[user_id]["last_offense"] = datetime.utcnow()

            count = warnings[user_id]["count"]

            await update.effective_chat.send_message(
                f"⚠️ {user.full_name} اخطار گرفت! ({count}/5)"
            )

            if count >= 5:
                await apply_punishment(update, context, user_id, user.full_name)

            break

# =========================
# پنل مدیریتی
# =========================

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_main_admin(update):
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

# =========================
# اجرای ربات
# =========================

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, filter_messages))
    app.add_handler(CommandHandler("panel", panel))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Bot is running...")
    app.run_polling()
