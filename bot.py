import imaplib
import email
import re
import random
import asyncio
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


# -------- AUTO DELETE --------
async def auto_delete(bot, chat, user_msg, bot_msg):
    await asyncio.sleep(2)
    try:
        await bot.delete_message(chat, user_msg)
        await bot.delete_message(chat, bot_msg)
    except:
        pass


# -------- LOADING ANIMATION --------
async def loading(message):
    steps = ["⏳ Processing.", "⏳ Processing..", "⏳ Processing..."]
    for s in steps:
        await message.edit_text(s)
        await asyncio.sleep(0.5)


# -------- FORCE JOIN --------
async def is_user_joined(context, uid):
    try:
        m = await context.bot.get_chat_member(CHANNEL_ID, uid)
        return m.status in ["member", "administrator", "creator"]
    except:
        return False


# -------- OTP FETCH --------
def fetch_latest_otp(mail, password):
    try:
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(mail, password)
        imap.select("INBOX")

        _, msgs = imap.search(None, "ALL")
        ids = msgs[0].split()

        for i in reversed(ids[-15:]):
            _, data = imap.fetch(i, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            if "telegram" not in msg.get("From", "").lower():
                continue

            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type()=="text/plain":
                        body = part.get_payload(decode=True).decode(errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors="ignore")

            otp = re.search(r"\b\d{5,6}\b", body)
            if otp:
                return f"🔐 *Latest Telegram OTP*\n\n`{otp.group()}`"

        return "❌ No OTP found."

    except Exception as e:
        return f"⚠️ {e}"


# -------- MAIN KEYBOARD --------
def keyboard():
    return ReplyKeyboardMarkup([
        ["📧 Add Gmail", "🔑 Set App Password"],
        ["✨ Generate Email", "📩 Get OTP"],
        ["📺 How To Use"]
    ], resize_keyboard=True)


# -------- START --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if await is_user_joined(context, update.effective_user.id):
        await update.message.reply_text(
            "✨ *Premium Mail Generator*\n\n"
            "Generate unlimited email variants & receive OTP instantly.",
            parse_mode="Markdown",
            reply_markup=keyboard()
        )
    else:
        btn=[[InlineKeyboardButton("Join Channel",url=CHANNEL_LINK)]]
        await update.message.reply_text(
            "Join our channel to continue.",
            reply_markup=InlineKeyboardMarkup(btn)
        )


# -------- MAIL GENERATOR --------
def gen_mail(base, ud):
    name, domain = base.split("@")
    ud.setdefault("set", set())

    while True:
        rn="".join(random.choice([c.upper(),c.lower()]) for c in name)
        rd="".join(random.choice([c.upper(),c.lower()]) for c in domain)
        m=f"{rn}@{rd}"

        if m not in ud["set"]:
            ud["set"].add(m)
            return m


# -------- HANDLER --------
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    if not await is_user_joined(context, update.effective_user.id):
        return

    text=update.message.text
    ud=context.user_data

    if text=="📧 Add Gmail":
        ud["step"]="mail"
        await update.message.reply_text("Send Gmail address.")

    elif text=="🔑 Set App Password":
        ud["step"]="pass"
        await update.message.reply_text("Send App Password.")

    elif ud.get("step")=="mail":
        ud["email"]=text.strip()
        ud["step"]=None

        msg=await update.message.reply_text("✅ Gmail Added")
        asyncio.create_task(auto_delete(
            context.bot,
            update.effective_chat.id,
            update.message.message_id,
            msg.message_id
        ))

    elif ud.get("step")=="pass":
        ud["pass"]=text.replace(" ","")
        ud["step"]=None

        msg=await update.message.reply_text("✅ Password Saved")
        asyncio.create_task(auto_delete(
            context.bot,
            update.effective_chat.id,
            update.message.message_id,
            msg.message_id
        ))

    # GENERATE EMAIL
    elif text=="✨ Generate Email":

        if not ud.get("email"):
            return await update.message.reply_text("Add Gmail first.")

        m=await update.message.reply_text("⏳ Generating...")
        await loading(m)

        mail=gen_mail(ud["email"],ud)

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Generate New Email",
                                  callback_data="new_mail")]
        ])

        await m.edit_text(
            f"📧 *Generated Email*\n\n`{mail}`",
            parse_mode="Markdown",
            reply_markup=kb
        )

    # OTP
    elif text=="📩 Get OTP":

        if not ud.get("email") or not ud.get("pass"):
            return await update.message.reply_text("Setup required.")

        m=await update.message.reply_text("🔎 Checking mailbox...")
        await loading(m)

        otp=fetch_latest_otp(ud["email"],ud["pass"])

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh OTP",
                                  callback_data="refresh_otp")]
        ])

        await m.edit_text(
            otp,
            parse_mode="Markdown",
            reply_markup=kb
        )

    elif text=="📺 How To Use":
        await update.message.reply_video(VIDEO_FILE_ID)


# -------- BUTTONS --------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q=update.callback_query
    await q.answer()

    ud=context.user_data

    if q.data=="new_mail":

        mail=gen_mail(ud["email"],ud)

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Generate New Email",
                                  callback_data="new_mail")]
        ])

        await q.edit_message_text(
            f"📧 *Generated Email*\n\n`{mail}`",
            parse_mode="Markdown",
            reply_markup=kb
        )

    elif q.data=="refresh_otp":

        otp=fetch_latest_otp(ud["email"],ud["pass"])

        kb=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Refresh OTP",
                                  callback_data="refresh_otp")]
        ])

        await q.edit_message_text(
            otp,
            parse_mode="Markdown",
            reply_markup=kb
        )


# -------- MAIN --------
def main():

    app=Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handle))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling(drop_pending_updates=True)


if __name__=="__main__":
    main()
