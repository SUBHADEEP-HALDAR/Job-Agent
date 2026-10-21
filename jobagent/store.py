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
