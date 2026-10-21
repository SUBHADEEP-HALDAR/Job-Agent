import argparse
import logging
import time
from pathlib import Path

import yaml

from jobagent import notify, scoring, sources, store


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--dry-run", action="store_true", help="print matches, don't send or mark as seen")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    cfg = yaml.safe_load(Path(a.config).read_text())

    seen = store.load()
    jobs = [j for j in sources.fetch_all(cfg) if j.id not in seen]
    logging.info("%d new jobs fetched", len(jobs))
    matches = scoring.rank(jobs, cfg)
    logging.info("%d matches above threshold", len(matches))

    if a.dry_run:
        for j in matches:
            print(notify.format_job(j), "\n---")
        return
    if matches:
        store.add_matches(matches)
        if notify.send_telegram(matches):
            now = time.time()
            for j in matches:
                seen[j.id] = now
    # also remember rejected jobs so they aren't re-scored every day
    now = time.time()
    for j in jobs:
        seen.setdefault(j.id, now)
    store.save(seen)


if __name__ == "__main__":
    main()
