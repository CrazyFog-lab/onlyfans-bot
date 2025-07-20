import os
import json
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (ApplicationBuilder, CommandHandler, CallbackContext,
    MessageHandler, filters, CallbackQueryHandler, ContextTypes)
from datetime import datetime
from uuid import uuid4

# Logging
logging.basicConfig(level=logging.INFO)

# ENV VARS
TOKEN = os.getenv("TOKEN")
REKENING = os.getenv("REKENING")

# Load CC data (simple list format)
with open("cc_data.json") as f:
    cc_data = json.load(f)

def generate_ticket():
    return f"OF{datetime.now().year}-{str(uuid4())[:6].upper()}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅ *Selamat datang di layanan Pembelian Credit Card OnlyFans!*",
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "Ketik /beli untuk mulai membeli Credit Card."
    )

async def beli(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[
        InlineKeyboardButton("$20", callback_data="$20"),
        InlineKeyboardButton("$50", callback_data="$50")
    ], [
        InlineKeyboardButton("$100", callback_data="$100"),
        InlineKeyboardButton("$200", callback_data="$200")
    ]]
    await update.message.reply_text(
        "Pilih nominal Credit Card yang ingin kamu beli:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    nominal = query.data
    context.user_data['nominal'] = nominal
    harga_rp = int(nominal.replace("$", "")) * 16000

    await query.message.reply_text(
        f"🧾 Silakan transfer *Rp{harga_rp:,}* ke rekening berikut:\n\n{REKENING}\n\nSetelah transfer, kirim bukti transfer (foto).",
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    nominal = context.user_data.get('nominal')
    if not nominal:
        await update.message.reply_text("❗ Silakan ketik /beli dulu untuk memulai transaksi.")
        return

    # Save photo
    photo_file = await update.message.photo[-1].get_file()
    bukti_path = f"bukti/{user.id}_{datetime.now().timestamp()}.jpg"
    await photo_file.download_to_drive(bukti_path)

    # Ambil 1 CC dari list
    cc_list = cc_data.get(nominal, [])
    if not cc_list:
        await update.message.reply_text("❌ Stok Credit Card untuk nominal ini habis.")
        return
    cc_info = cc_list.pop(0)

    # Simpan kembali sisa CC
    with open("cc_data.json", "w") as f:
        json.dump(cc_data, f, indent=2)

    # Simulasi verifikasi otomatis
    await update.message.reply_text("✅ Verifikasi berhasil.")
    await update.message.reply_text("CC untuk OnlyFans akan dikirim ke Telegram kamu dalam 5-15 menit...")

    tiket = generate_ticket()
    cc_text = f"💳 *CREDIT CARD INFO ({nominal})*\n\n"
    cc_text += f"Card Number: `{cc_info[0]}`\n"
    cc_text += f"Expiry: {cc_info[1]}\nCVV: {cc_info[2]}\nZIP: {cc_info[3]}\nRegion: {cc_info[4]}"

    await update.message.reply_text(cc_text, parse_mode="Markdown")
    await update.message.reply_text(f"📌 Verifikasi Sukses — Nomor Tiket: *{tiket}*", parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("beli", beli))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    logging.info("Bot berjalan...")
    app.run_polling()
