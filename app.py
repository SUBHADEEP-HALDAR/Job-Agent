"""Streamlit dashboard: shows jobs the daily agent matched. Reads matches.json."""
import datetime as dt
import json
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Job Matches", page_icon="💼", layout="wide")
st.title("💼 Job Matches")
st.caption("Internship and full-time roles around Kolkata or remote, ranked against my resume.")


@st.cache_data(ttl=600)
def load() -> pd.DataFrame:
    p = Path("matches.json")
    if not p.exists():
        return pd.DataFrame()
    return pd.DataFrame(json.loads(p.read_text()))


df = load()
if df.empty:
    st.info("No matches yet. The daily agent will fill this in after its first successful run.")
    st.stop()

df["found"] = pd.to_datetime(df["found"]).dt.date
newest = df["found"].max()
if (dt.date.today() - newest).days > 3:
    st.warning(f"Data may be stale: last new match was on {newest}.")

with st.sidebar:
    st.header("Filters")
    min_score = st.slider("Minimum match score", 0, 100, 55)
    days = st.selectbox("Found in the last", [3, 7, 14, 30, 60], index=1, format_func=lambda d: f"{d} days")
    sources = st.multiselect("Source", sorted(df["source"].unique()))
    where = st.radio("Location", ["All", "Kolkata / West Bengal", "Remote only"])
    text = st.text_input("Search title or company")

f = df[(df["score"] >= min_score) & (df["found"] >= dt.date.today() - dt.timedelta(days=days))]
if sources:
    f = f[f["source"].isin(sources)]
if where == "Remote only":
    f = f[f["remote"]]
elif where == "Kolkata / West Bengal":
    f = f[f["location"].str.contains("kolkata|west bengal|howrah|salt lake|new town", case=False, na=False)]
if text:
    f = f[f["title"].str.contains(text, case=False, na=False) | f["company"].str.contains(text, case=False, na=False)]

c1, c2, c3 = st.columns(3)
c1.metric("Matches shown", len(f))
c2.metric("Best score", int(f["score"].max()) if len(f) else 0)
c3.metric("Last updated", str(newest))

if f.empty:
    st.write("Nothing matches these filters. Try lowering the minimum score.")
else:
    st.dataframe(
        f[["score", "title", "company", "location", "job_type", "source", "found", "reason", "url"]]
        .sort_values(["score", "found"], ascending=False),
        hide_index=True, use_container_width=True,
        column_config={
            "score": st.column_config.ProgressColumn("Match", min_value=0, max_value=100, format="%d"),
            "url": st.column_config.LinkColumn("Apply", display_text="Apply ↗"),
            "found": "Found",
            "job_type": "Type",
            "reason": "Why",
        },
    )
st.caption("Links come from job aggregators. Some postings may be reposts or closed, so check the date before applying.")
