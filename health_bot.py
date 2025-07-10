from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler
import requests
import os

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # opcional

def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("Verificar Status do Bot", callback_data='check_status')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Clique abaixo para verificar o status do bot:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    try:
        resp = requests.get("http://localhost:8080/health", timeout=2)
        if resp.status_code == 200 and resp.text == "ok":
            query.edit_message_text("✅ Bot está rodando corretamente!")
        else:
            query.edit_message_text("⚠️ Bot respondeu, mas com status inesperado.")
    except Exception as e:
        query.edit_message_text(f"❌ Bot não está respondendo. Erro: {e}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
