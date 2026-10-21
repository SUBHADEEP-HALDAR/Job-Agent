"""Keyword scoring (free, deterministic) + optional Claude refinement."""
import json
import logging
import os
import re

from .models import Job

log = logging.getLogger("jobagent.scoring")
INDIA_OK = ("india", "worldwide", "anywhere", "asia", "apac", "global")


def _has(text: str, word: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(word.lower()) + r"(?![a-z0-9])", text) is not None


def location_ok(job: Job, cfg: dict) -> tuple[bool, int]:
    """Return (eligible, bonus). Remote jobs must be open to India."""
    loc = job.location.lower()
    L = cfg["location"]
    if any(c in loc for c in L["cities"]) or any(s in loc for s in L["states"]):
        return True, 20
    if job.remote or "remote" in loc or "remote" in job.title.lower():
        if not L.get("allow_remote"):
            return False, 0
        # Remotive-style restriction text, e.g. "USA Only"
        if loc and not any(k in loc for k in INDIA_OK) and "remote" not in loc:
            return False, 0
        return True, 10
    if "india" in loc:
        return True, 5      # elsewhere in India: allowed, lower priority
    return False, 0


def keyword_score(job: Job, cfg: dict) -> int:
    P = cfg["profile"]
    title = job.title.lower()
    text = f"{title} {job.description.lower()[:4000]}"
    if any(_has(title, x) or _has(text[:600], x) for x in P["exclude"]):
        return 0
    ok, loc_bonus = location_ok(job, cfg)
    if not ok:
        return 0
    t_hits = sum(_has(title, k) for k in P["title_keywords"])
    s_hits = sum(_has(text, s) for s in P["skills"])
    score = min(t_hits, 3) * 12 + min(s_hits, 6) * 6 + loc_bonus
    jt = (job.job_type + " " + title).lower()
    if "intern" in jt or "trainee" in jt or "fresher" in jt or "graduate" in jt:
        score += 10
    return max(0, min(100, score))


def llm_refine(jobs: list[Job], cfg: dict) -> None:
    """Ask Claude to score each job 0-100 against the profile. Mutates jobs. Silent fallback."""
    if not (cfg["notify"].get("use_llm") and os.getenv("ANTHROPIC_API_KEY")):
        return
    try:
        import anthropic
        client = anthropic.Anthropic()
    except Exception as e:
        log.warning("LLM unavailable: %s", e)
        return
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
    for j in jobs:
        try:
            msg = client.messages.create(
                model=model, max_tokens=200,
                messages=[{"role": "user", "content":
                    "Rate how well this job fits the candidate. Reply ONLY with JSON "
                    '{"score": 0-100, "reason": "<=20 words"}. Be strict about seniority '
                    "and required experience; the candidate is a final-year student.\n\n"
                    f"CANDIDATE: {cfg['profile']['summary']}\nSkills: {', '.join(cfg['profile']['skills'])}\n\n"
                    f"JOB: {j.title} at {j.company} ({j.location})\n{j.description[:2500]}"}])
            data = json.loads(re.search(r"\{.*\}", msg.content[0].text, re.S).group(0))
            j.score = int(data["score"])
            j.reason = str(data.get("reason", ""))[:160]
        except Exception as e:
            log.warning("LLM scoring failed for %s: %s (keeping keyword score)", j.title, e)


def rank(jobs: list[Job], cfg: dict) -> list[Job]:
    for j in jobs:
        j.score = keyword_score(j, cfg)
    cand = sorted((j for j in jobs if j.score > 0), key=lambda j: -j.score)[: cfg["notify"]["max_per_run"] * 2]
    llm_refine(cand, cfg)
    for j in cand:
        if not j.reason:
            j.reason = "Matches your title/skill keywords"
    good = [j for j in cand if j.score >= cfg["notify"]["min_score"]]
    return sorted(good, key=lambda j: -j.score)[: cfg["notify"]["max_per_run"]]
