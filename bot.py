import pandas as pd
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


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
        total += amount

        bill_text += f"{name} x {qty} = ₹{amount}\n"

    bill_text += f"\n💰 Total = ₹{total}"

    return bill_text, total


# 📊 Save to Excel
def save_to_excel(order, total):
    rows = []

    for name, qty in order:
        price = products.get(name, 0)
        rows.append({
            "Date": datetime.now(),
            "Item": name,
            "Quantity": qty,
            "Price": price,
            "Total": price * qty
        })

    df = pd.DataFrame(rows)

    try:
        existing = pd.read_excel("sales.xlsx")
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass

    df.to_excel("sales.xlsx", index=False)


def generate_pdf(order, total):
    filename = "bill.pdf"

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("🧾 BILL", styles["Title"]))
    content.append(Spacer(1, 10))

    for name, qty in order:
        price = products.get(name, 0)
        amount = price * qty
        content.append(Paragraph(f"{name} x {qty} = ₹{amount}", styles["Normal"]))

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
    save_to_excel(order, total)

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