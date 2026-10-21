# Job Agent (India · Kolkata + Remote · Internship/Full-time)

Every morning it fetches fresh jobs, scores them against your profile, and sends the best
ones to your Telegram with a direct apply link. You click Apply yourself.

## 1. Get the free keys (about 15 minutes)
| What | Where | Needed? |
|---|---|---|
| **Telegram bot** | Telegram → chat `@BotFather` → `/newbot` → copy the token. Then send any message to your bot and open `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your `chat.id`. | Yes |
| **Adzuna** (India jobs) | https://developer.adzuna.com → sign up → copy App ID + App Key | Yes (main source) |
| **JSearch** (LinkedIn/Indeed/Naukri via Google Jobs) | https://rapidapi.com → search "JSearch" → subscribe to the free plan → copy key | Optional (free tier is small) |
| **Anthropic API key** | https://console.anthropic.com | Optional (smarter scoring; works without) |

Remotive (remote jobs) needs no key.

## 2. Test on your computer
```bash
pip install -r requirements-agent.txt
export ADZUNA_APP_ID=... ADZUNA_APP_KEY=...        # Windows: set instead of export
python main.py --dry-run          # prints matches, sends nothing
export TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...
python main.py                    # sends to Telegram
```

## 3. Run it daily for free (GitHub Actions)
1. Push this folder to a **private** GitHub repo.
2. Repo → Settings → Secrets and variables → Actions → add the keys above with the same names
   (`ADZUNA_APP_ID`, `ADZUNA_APP_KEY`, `RAPIDAPI_KEY`, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`).
3. Actions tab → *daily-job-agent* → **Run workflow** once to test. After that it runs at 08:00 IST daily.

## Tuning
Edit `config.yaml`: titles to search, skills, cities, `min_score` (raise it for fewer, better matches).
If you get too few jobs, lower `min_score` to 40. If too many weak ones, raise it to 65.

## Limits
- Naukri, Internshala and LinkedIn have no public API and block scrapers, so they appear only when Google Jobs/Adzuna index them (JSearch is the best route for this).
- Some links may be reposts or closed. Check the posting date before applying.
- Run `python -m pytest` after editing the scoring logic.

## 4. Streamlit dashboard (optional)
1. Go to https://share.streamlit.io → sign in with GitHub → **Create app**.
2. Choose this repo, branch `main`, main file `app.py`, then Deploy.
   (Private repos work: allow Streamlit access to it when asked.)
3. The agent commits `matches.json` after each daily run and the app picks it up. No keys go into Streamlit.
Run locally: `pip install -r requirements.txt && streamlit run app.py`
