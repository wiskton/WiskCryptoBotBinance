import os
from dotenv import load_dotenv
from utils.util import log
import requests


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

ENABLE_TELEGRAM_ALERTS = True   # Ajuste aqui para ativar/desativar Telegram


def send_telegram(msg):
    if ENABLE_TELEGRAM_ALERTS and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            log(f"Erro ao enviar Telegram: {e}")