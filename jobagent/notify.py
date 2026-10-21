import html
import logging
import os

import requests

log = logging.getLogger("jobagent.notify")


def format_job(j) -> str:
    e = html.escape
    return (f"<b>{e(j.title)}</b>\n{e(j.company)} · {e(j.location or 'n/a')}\n"
            f"Match: <b>{j.score}/100</b> — {e(j.reason)}\n"
            f"Source: {e(j.source)}\n<a href=\"{e(j.url, quote=True)}\">Apply here</a>")


def send_telegram(jobs) -> bool:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (token and chat):
        log.warning("Telegram not configured; printing instead.")
        for j in jobs:
            print(format_job(j), "\n---")
        return False
    ok = True
    header = f"{len(jobs)} new job match{'es' if len(jobs) != 1 else ''} for you"
    for text in [header] + [format_job(j) for j in jobs]:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chat, "text": text, "parse_mode": "HTML",
                                "disable_web_page_preview": True}, timeout=20)
        if not r.ok:
            log.error("Telegram error %s: %s", r.status_code, r.text[:200])
            ok = False
    return ok
