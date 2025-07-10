import os
from dotenv import load_dotenv
from utils.util import log
import requests


load_dotenv()


DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

ENABLE_DISCORD_ALERTS = False    # Ajuste aqui para ativar/desativar Discord


def send_discord(msg):
    if ENABLE_DISCORD_ALERTS and DISCORD_WEBHOOK_URL:
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": msg}, timeout=5)
        except Exception as e:
            log(f"Erro ao enviar Discord: {e}")