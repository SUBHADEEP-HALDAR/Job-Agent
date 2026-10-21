"""Job sources. Each fetcher returns list[Job] and never raises: a broken source
must not stop the others."""
import hashlib
import logging
import os

import requests

from .models import Job

log = logging.getLogger("jobagent.sources")
TIMEOUT = 25


def _id(*parts: str) -> str:
    return hashlib.sha1("|".join(p.lower().strip() for p in parts).encode()).hexdigest()[:16]


def fetch_adzuna(cfg: dict) -> list[Job]:
    app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        log.info("Adzuna skipped (no keys)")
        return []
    jobs: list[Job] = []
    country = cfg["location"].get("country", "in")
    wheres = [c for c in cfg["location"]["cities"][:1]] + [""]  # Kolkata + all India
    for title in cfg["profile"]["search_titles"]:
        for where in wheres:
            try:
                r = requests.get(
                    f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
                    params={"app_id": app_id, "app_key": app_key, "what": title, "where": where,
                            "results_per_page": 30, "sort_by": "date",
                            "max_days_old": cfg["notify"]["max_age_days"]},
                    timeout=TIMEOUT)
                r.raise_for_status()
                for j in r.json().get("results", []):
                    jobs.append(Job(
                        id=_id(j.get("title", ""), j.get("company", {}).get("display_name", ""), j.get("location", {}).get("display_name", "")),
                        title=j.get("title", ""), company=j.get("company", {}).get("display_name", ""),
                        location=j.get("location", {}).get("display_name", ""),
                        url=j.get("redirect_url", ""), description=j.get("description", ""),
                        source="Adzuna", posted=j.get("created", ""),
                        job_type=j.get("contract_time") or ""))
            except Exception as e:
                log.warning("Adzuna failed for %r/%r: %s", title, where, e)
    return jobs


def fetch_jsearch(cfg: dict) -> list[Job]:
    key = os.getenv("RAPIDAPI_KEY")
    if not key:
        log.info("JSearch skipped (no key)")
        return []
    jobs: list[Job] = []
    # JSearch free tier is tiny, so use only the first few titles.
    for title in cfg["profile"]["search_titles"][:4]:
        for q in (f"{title} in Kolkata, India", f"{title} remote India"):
            try:
                r = requests.get(
                    "https://jsearch.p.rapidapi.com/search",
                    headers={"X-RapidAPI-Key": key, "X-RapidAPI-Host": "jsearch.p.rapidapi.com"},
                    params={"query": q, "page": "1", "num_pages": "1", "country": "in", "date_posted": "3days"},
                    timeout=TIMEOUT)
                r.raise_for_status()
                for j in r.json().get("data", []):
                    loc = ", ".join(x for x in (j.get("job_city"), j.get("job_state"), j.get("job_country")) if x)
                    jobs.append(Job(
                        id=_id(j.get("job_title", ""), j.get("employer_name", ""), loc),
                        title=j.get("job_title", ""), company=j.get("employer_name", ""),
                        location=loc, url=j.get("job_apply_link", ""),
                        description=j.get("job_description", ""), source=f"JSearch/{j.get('job_publisher', '')}",
                        posted=j.get("job_posted_at_datetime_utc", "") or "",
                        remote=bool(j.get("job_is_remote")), job_type=j.get("job_employment_type", "") or ""))
            except Exception as e:
                log.warning("JSearch failed for %r: %s", q, e)
    return jobs


def fetch_remotive(cfg: dict) -> list[Job]:
    """Free, no key. Remote jobs worldwide; location filter keeps India-eligible ones."""
    jobs: list[Job] = []
    for cat in ("data", "software-dev"):
        try:
            r = requests.get("https://remotive.com/api/remote-jobs", params={"category": cat, "limit": 80}, timeout=TIMEOUT)
            r.raise_for_status()
            for j in r.json().get("jobs", []):
                jobs.append(Job(
                    id=_id(j.get("title", ""), j.get("company_name", ""), "remote"),
                    title=j.get("title", ""), company=j.get("company_name", ""),
                    location=j.get("candidate_required_location", ""), url=j.get("url", ""),
                    description=j.get("description", ""), source="Remotive",
                    posted=j.get("publication_date", ""), remote=True,
                    job_type=j.get("job_type", "")))
        except Exception as e:
            log.warning("Remotive failed (%s): %s", cat, e)
    return jobs


def fetch_all(cfg: dict) -> list[Job]:
    jobs = fetch_adzuna(cfg) + fetch_jsearch(cfg)
    if cfg["location"].get("allow_remote"):
        jobs += fetch_remotive(cfg)
    seen, out = set(), []
    for j in jobs:
        if j.url and j.id not in seen:
            seen.add(j.id)
            out.append(j)
    return out
