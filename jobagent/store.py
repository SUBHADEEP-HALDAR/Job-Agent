import json
import time
from pathlib import Path

PATH = Path("seen_jobs.json")
KEEP_DAYS = 45


def load() -> dict:
    try:
        return json.loads(PATH.read_text())
    except Exception:
        return {}


def save(seen: dict) -> None:
    cutoff = time.time() - KEEP_DAYS * 86400
    PATH.write_text(json.dumps({k: v for k, v in seen.items() if v > cutoff}, indent=0))


MATCHES = Path("matches.json")
MATCH_KEEP_DAYS = 60


def add_matches(jobs) -> None:
    """Persist matched jobs for the Streamlit dashboard (newest first, deduped)."""
    import datetime as dt
    try:
        old = json.loads(MATCHES.read_text())
    except Exception:
        old = []
    today = dt.date.today().isoformat()
    ids = {m["id"] for m in old}
    for j in jobs:
        if j.id not in ids:
            old.append({"id": j.id, "found": today, "title": j.title, "company": j.company,
                        "location": j.location, "score": j.score, "reason": j.reason,
                        "source": j.source, "remote": j.remote, "job_type": j.job_type,
                        "posted": j.posted, "url": j.url})
    cutoff = (dt.date.today() - dt.timedelta(days=MATCH_KEEP_DAYS)).isoformat()
    old = [m for m in old if m["found"] >= cutoff]
    old.sort(key=lambda m: (m["found"], m["score"]), reverse=True)
    MATCHES.write_text(json.dumps(old, indent=1))
