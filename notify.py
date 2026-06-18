import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send(text):
    """Send the card to Telegram. If creds are missing, just print it
    so you can still see the output in Railway logs."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[no Telegram creds — printing card instead]\n")
        print(text)
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=15,
        )
        r.raise_for_status()
        print("Card sent to Telegram.")
    except Exception as ex:
        print("Telegram send failed:", ex)
        print(text)
