import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# ---------- Config ----------
st.set_page_config(page_title="Gaviota Visibility Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ---------- Constants ----------
LOG_FILE = "dive_log.csv"
EXPECTED_COLS = ["Date", "Time", "Spot", "Visibility", "Notes", "Fish Taken"]

# ---------- Ensure CSV File Exists with Headers ----------
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=EXPECTED_COLS).to_csv(LOG_FILE, index=False)

# ---------- Hero Section ----------
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #0e1117;
        color: #f1f1f1;
        font-family: 'Inter', sans-serif;
    }
    .hero-container img {
        width: 100%; max-height: 240px; object-fit: cover; border-radius: 0.5rem;
    }
    .hero-text {
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        text-align: center; background: rgba(0,0,0,0.4);
        padding: 1rem 1.5rem; border-radius: 0.5rem; width: 90%;
    }
    .hero-text h1 { font-size: 2rem; margin-bottom: 0.3rem; }
    .hero-text p { font-size: 1rem; color: #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-container">
    <img src="https://raw.githubusercontent.com/michaelmhudson/gaviota-visibility-dashboard/main/assets/hero.png" />
    <div class="hero-text">
        <h1>Gaviota Coast Spearfishing Dashboard</h1>
        <p>Live visibility forecasts. Smart predictions. Your personal dive log.</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- Log Dive Section ----------
st.subheader("📘 Log a Dive")
with st.form("log_form"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", value=datetime.today())
        time = st.time_input("Time", value=datetime.now().time())
        spot = st.selectbox("Spot", ["Tajiguas", "Arroyo Quemado", "Refugio", "Drake’s / Naples", "Coal Oil Point", "Haskell’s", "Mesa Lane", "Hendry’s", "Butterfly Beach"])
    with col2:
        vis = st.selectbox("Observed Visibility", ["<4 ft", "4–6 ft", "6–8 ft", "8–10 ft", "15+ ft"])
        fish = st.text_input("Fish Taken")
        notes = st.text_area("Notes", placeholder="Surge, bait, thermocline...")
    submitted = st.form_submit_button("Save Entry")
    if submitted:
        new_entry = pd.DataFrame([{ "Date": date, "Time": time.strftime('%H:%M'), "Spot": spot, "Visibility": vis, "Notes": notes, "Fish Taken": fish }])
        new_entry.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)
        st.success("Dive logged successfully!")

# ---------- Show Logbook ----------
st.subheader("📚 Your Dive Logbook")
try:
    df = pd.read_csv(LOG_FILE)
    if df.shape[1] != len(EXPECTED_COLS):
        df.columns = EXPECTED_COLS[:df.shape[1]] + [f"extra_{i}" for i in range(df.shape[1] - len(EXPECTED_COLS))]
    for col in EXPECTED_COLS:
        if col not in df.columns:
            df[col] = ""
    df = df[EXPECTED_COLS]
    st.dataframe(df.sort_values(by="Date", ascending=False), use_container_width=True)
except Exception as e:
    st.error("Log file is corrupted or unreadable.")
    st.exception(e)

# ---------- Footer ----------
st.caption("Live data will reappear soon — this section under maintenance")
