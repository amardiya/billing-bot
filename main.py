import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import os
import json

def init_sheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    creds_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)

    sheet = client.open("SalesData").sheet1
    return sheet


# 📦 Product database (you can edit this)
products = {
    "shirt": 500,
    "pants": 800,
    "tshirt": 300,
    "jeans": 1000
}


# 🧠 Parse user input
def parse_order(text):
    items = text.split(",")
    order = []

    for item in items:
        parts = item.strip().split()
        if len(parts) != 2:
            continue
        name, qty = parts
        order.append((name.lower(), int(qty)))

    return order


# 🧾 Generate bill
def generate_bill(order):
    total = 0
    bill_text = "🧾 BILL\n\n"

    for name, qty in order:
        price = products.get(name, 0)
        amount = price * qty
        gst = amount * 0.18
        final = amount + gst

        total += final

        bill_text += f"{name} x {qty} = ₹{amount} + GST = ₹{final}\n"

    bill_text += f"\n💰 Total = ₹{total}"
    return bill_text, total

# 📊 Save to Excel
def save_to_sheets(order, total):
    try:
        print("🚀 Saving to Google Sheets...")

        for name, qty in order:
            price = products.get(name, 0)
            gst = price * qty * 0.18

            sheet.append_row([
                str(datetime.now()),
                name,
                qty,
                price,
                gst,
                price * qty + gst
            ])

        print("✅ Saved to Google Sheets!")

    except Exception as e:
        print("❌ ERROR:", e)

from reportlab.platypus import Image


def generate_pdf(order, total):
    filename = "bill.pdf"

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    content = []

    # 🖼️ Logo
    content.append(Image("logo.png", width=100, height=50))
    content.append(Spacer(1, 10))

    content.append(Paragraph("DRFT MENS STORE", styles["Title"]))
    content.append(Paragraph("GST Invoice", styles["Normal"]))
    content.append(Spacer(1, 10))

    for name, qty in order:
        price = products.get(name, 0)
        amount = price * qty
        gst = amount * 0.18
        final = amount + gst

        content.append(Paragraph(
            f"{name} x {qty} = ₹{amount} + GST = ₹{final}",
            styles["Normal"]
        ))

    content.append(Spacer(1, 10))
    content.append(Paragraph(f"Total = ₹{total}", styles["Title"]))

    doc.build(content)
    return filename

# 🤖 Handle message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    order = parse_order(text)

    if not order:
        await update.message.reply_text("❌ Invalid format!\nUse: shirt 2, pants 1")
        return

    bill, total = generate_bill(order)

    # ✅ FIXED LINE
    save_to_sheets(order, total)

    pdf_file = generate_pdf(order, total)

    await update.message.reply_text(bill)
    await update.message.reply_document(document=open(pdf_file, "rb"))
    # 🧾 Generate PDF
    pdf_file = generate_pdf(order, total)

    # 📤 Send both text + PDF
    await update.message.reply_text(bill)

    await update.message.reply_document(document=open(pdf_file, "rb"))


# 🚀 Run bot
from telegram.request import HTTPXRequest

import os

def main():
    TOKEN = os.getenv("BOT_TOKEN")

    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0
    )

    app = ApplicationBuilder().token(TOKEN).request(request).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()