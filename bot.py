import imaplib
import email
import re
import random
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIG =================
BOT_TOKEN = "8765397132:AAGNYEkPQf0BlZ26ZgSopRbX-AXQh0KqKoE"
VIDEO_FILE_ID = "PASTE_YOUR_VIDEO_FILE_ID_HERE"
# ==========================================


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
        latest_10 = mail_ids[-10:]

        for mail_id in reversed(latest_10):
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
    await update.message.reply_text("🤖 Bot Ready!", reply_markup=get_kb())


# -------- FILE ID GETTER (TEMP) --------
async def get_file_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.video:
        await update.message.reply_text(
            f"🎥 VIDEO FILE ID:\n\n`{update.message.video.file_id}`",
            parse_mode="Markdown"
        )


# -------- MESSAGE HANDLER --------
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            alias = f"{name}+{random.randint(10,999)}@{domain}"
            await update.message.reply_text(f"✅ Copy Alias:\n\n`{alias}`", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Pehle Gmail add karein.")

    elif text == "📺 Watch Video Guide":
        await update.message.reply_video(VIDEO_FILE_ID)

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
    app.add_handler(MessageHandler(filters.VIDEO, get_file_id))  # remove later if not needed
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all))
    app.run_polling()


if __name__ == "__main__":
    main()
