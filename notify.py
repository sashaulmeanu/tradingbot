import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def _chunks(text, size=3800):
    out, cur = [], ""
    for line in text.split("\n"):
        if len(cur) + len(line) + 1 > size:
            out.append(cur)
            cur = ""
        cur += line + "\n"
    if cur:
        out.append(cur)
    return out


def send(text):
    """Send text to Telegram, split into chunks if long. Prints if no creds."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[no Telegram creds — printing card instead]\n")
        print(text)
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    for part in _chunks(text):
        try:
            r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": part},
                              timeout=15)
            r.raise_for_status()
        except Exception as ex:
            print("Telegram send failed:", ex)
            print(part)


def send_photo(path, caption=""):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[no Telegram creds — chart saved at {path}]")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        with open(path, "rb") as f:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID,
                                     "caption": caption[:1000]},
                          files={"photo": f}, timeout=30)
    except Exception as ex:
        print("Telegram photo failed:", ex)

