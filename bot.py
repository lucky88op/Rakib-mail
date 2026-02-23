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
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

# ================= CONFIG =================
BOT_TOKEN = "8765397132:AAGNYEkPQf0BlZ26ZgSopRbX-AXQh0KqKoE"
CHANNEL_ID = "@PRBD_CHANNEL"
CHANNEL_LINK = "https://t.me/PRBD_CHANNEL"

VIDEO_FILE_ID = "BAACAgUAAxkBAANtaZzf9KA0xqYaG5s6ZJE0B46xttsAAvMeAAIU0-FUts7bqoiBshg6BA"   # 🔥 Pehle None rakho
# ==========================================


# -------- FORCE JOIN CHECK --------
async def is_user_joined(context, user_id):
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


# -------- OTP FETCH FUNCTION --------
def fetch_latest_otp(user_email, app_pass):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user_email, app_pass)
        mail.select("INBOX")

        status, messages = mail.search(None, "ALL")
        if status != "OK":
            return "❌ Mail search failed."

        mail_ids = messages[0].split()
        latest_15 = mail_ids[-15:]

        for mail_id in reversed(latest_15):
            status, data = mail.fetch(mail_id, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(data[0][1])
            sender = msg.get("From", "")

            if "telegram" not in sender.lower():
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
                return f"🔐 *Telegram OTP*\n\n`{otp.group()}`\n\n_Tap to copy_"

        return "❌ Telegram OTP mail nahi mila."
    except Exception as e:
        return f"❌ Error: {str(e)}"


# -------- KEYBOARD --------
def get_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📧 Add Gmail"), KeyboardButton("🔑 Set App Pass")],
        [KeyboardButton("🔀 Generate Alias"), KeyboardButton("📩 Get Fresh OTP")],
        [KeyboardButton("📺 Watch Video Guide")]
    ], resize_keyboard=True)


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if await is_user_joined(context, user_id):
        await update.message.reply_text(
            "🤖 Bot Ready! Buttons ka use karein.",
            reply_markup=get_kb()
        )
    else:
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
        await update.message.reply_text(
            "❌ Pehle channel join karein.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# -------- MESSAGE HANDLER --------
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 🔥 VIDEO AUTO DETECT SYSTEM
    if update.message.video:
        file_id = update.message.video.file_id
        await update.message.reply_text(f"✅ Your Video File ID:\n\n`{file_id}`", parse_mode="Markdown")
        return

    # Safety check
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id

    if not await is_user_joined(context, user_id):
        keyboard = [[InlineKeyboardButton("Join Channel", url=CHANNEL_LINK)]]
        await update.message.reply_text(
            "🚨 Pehle channel join karein!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text = update.message.text
    ud = context.user_data

    if text == "📩 Get Fresh OTP":
        if not ud.get("email") or not ud.get("pass"):
            await update.message.reply_text("❌ Pehle Gmail aur App Password set karein.")
        else:
            msg = await update.message.reply_text("🔎 Searching for OTP...")
            res = fetch_latest_otp(ud["email"], ud["pass"])
            await msg.edit_text(res, parse_mode="Markdown")

    elif text == "🔀 Generate Alias":
        if ud.get("email"):
            name, domain = ud["email"].split("@")
            alias = f"`{name}+{random.randint(10,999)}@{domain}`"
            await update.message.reply_text(
                f"✅ Click to Copy Alias:\n\n{alias}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Pehle Gmail add karein.")

    elif text == "📺 Watch Video Guide":
        if VIDEO_FILE_ID:
            await update.message.reply_video(VIDEO_FILE_ID, caption="Setup Guide")
        else:
            await update.message.reply_text(
                "❌ Video ID set nahi hai.\n\nBot ko video bhejo to file_id mil jayega."
            )

    elif text == "📧 Add Gmail":
        await update.message.reply_text("📥 Gmail bhejein:")
        ud["step"] = "email"

    elif text == "🔑 Set App Pass":
        await update.message.reply_text("📥 App Password bhejein:")
        ud["step"] = "pass"

    else:
        if ud.get("step") == "email":
            ud["email"] = text.strip()
            ud["step"] = None
            await update.message.reply_text("✅ Gmail saved.")

        elif ud.get("step") == "pass":
            ud["pass"] = text.replace(" ", "")
            ud["step"] = None
            await update.message.reply_text("✅ App Password saved.")


# -------- MAIN --------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_all))

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
