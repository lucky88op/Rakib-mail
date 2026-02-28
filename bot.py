import imaplib
import email
import re
import random
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# ================= CONFIG =================
BOT_TOKEN = "8765397132:AAGNYEkPQf0BlZ26ZgSopRbX-AXQh0KqKoE"

CHANNEL_ID = "@PRBD_CHANNEL"
CHANNEL_LINK = "https://t.me/PRBD_CHANNEL"

VIDEO_FILE_ID = "BAACAgUAAxkBAANtaZzf9KA0xqYaG5s6ZJE0B46xttsAAvMeAAIU0-FUts7bqoiBshg6BA"
# ==========================================


# -------- FORCE JOIN --------
async def is_user_joined(context, user_id):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# -------- OTP FETCH --------
def fetch_latest_otp(user_email, app_pass):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user_email, app_pass)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        mail_ids = messages[0].split()

        for mail_id in reversed(mail_ids[-15:]):
            status, data = mail.fetch(mail_id, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            if "telegram" not in msg.get("From", "").lower():
                continue

            body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            otp = re.search(r"\b\d{5,6}\b", body)
            if otp:
                return f"🔐 *Telegram OTP*\n\n`{otp.group()}`"

        return "❌ OTP nahi mila."

    except Exception as e:
        return f"❌ Error: {e}"


# -------- KEYBOARD --------
def get_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📧 Add Gmail"), KeyboardButton("🔑 Set App Pass")],
        [KeyboardButton("🔀 Generate Alias"), KeyboardButton("📩 Get Fresh OTP")],
        [KeyboardButton("📺 Watch Video Guide")]
    ], resize_keyboard=True)


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await is_user_joined(context, update.effective_user.id):
        await update.message.reply_text(
            "✅ Bot Ready",
            reply_markup=get_kb()
        )
    else:
        btn = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
        await update.message.reply_text(
            "❌ Channel Join Required",
            reply_markup=InlineKeyboardMarkup(btn)
        )


# -------- GENERATE MAIL --------
def generate_random_mail(base, ud):

    name, domain = base.split("@")

    ud.setdefault("generated_set", set())

    while True:
        rn = "".join(
            c.upper() if random.choice([True, False]) else c.lower()
            for c in name
        )

        rd = "".join(
            c.upper() if random.choice([True, False]) else c.lower()
            for c in domain
        )

        mail = f"{rn}@{rd}"

        if mail not in ud["generated_set"]:
            ud["generated_set"].add(mail)
            return mail


# -------- MESSAGE HANDLER --------
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not await is_user_joined(context, update.effective_user.id):
        btn = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
        await update.message.reply_text(
            "🚨 Join Channel First",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    text = update.message.text
    ud = context.user_data

    # ADD EMAIL
    if text == "📧 Add Gmail":
        ud["step"] = "email"
        await update.message.reply_text("Send Gmail")

    elif text == "🔑 Set App Pass":
        ud["step"] = "pass"
        await update.message.reply_text("Send App Password")

    # SAVE DATA
    elif ud.get("step") == "email":
        ud["email"] = text.strip()
        ud["step"] = None
        await update.message.reply_text("✅ Gmail Saved")

    elif ud.get("step") == "pass":
        ud["pass"] = text.replace(" ", "")
        ud["step"] = None
        await update.message.reply_text("✅ App Password Saved")

    # GENERATE MAIL
    elif text == "🔀 Generate Alias":

        if not ud.get("email"):
            await update.message.reply_text("❌ Add Gmail first")
            return

        new_mail = generate_random_mail(ud["email"], ud)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔀 Generate New Mail",
                callback_data="new_mail"
            )]
        ])

        await update.message.reply_text(
            f"✅ New Email:\n\n`{new_mail}`",
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    # OTP
    elif text == "📩 Get Fresh OTP":

        if not ud.get("email") or not ud.get("pass"):
            await update.message.reply_text("❌ Gmail/AppPass missing")
            return

        msg = await update.message.reply_text("Searching OTP...")
        res = fetch_latest_otp(ud["email"], ud["pass"])
        await msg.edit_text(res, parse_mode="Markdown")

    # VIDEO
    elif text == "📺 Watch Video Guide":
        await update.message.reply_video(VIDEO_FILE_ID)


# -------- BUTTON CALLBACK --------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    ud = context.user_data

    if query.data == "new_mail":

        if not ud.get("email"):
            return

        new_mail = generate_random_mail(ud["email"], ud)

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔀 Generate New Mail",
                callback_data="new_mail"
            )]
        ])

        await query.edit_message_text(
            f"✅ New Email:\n\n`{new_mail}`",
            parse_mode="Markdown",
            reply_markup=keyboard
        )


# -------- MAIN --------
def main():

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all))
    app.add_handler(CallbackQueryHandler(button_callback))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
