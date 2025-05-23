import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Gaviota Visibility Dashboard", layout="wide", initial_sidebar_state="collapsed")

LOG_FILE = "dive_log.csv"
EXPECTED_COLS = ["Date", "Time", "Spot", "Visibility", "Notes", "Fish Taken"]
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=EXPECTED_COLS).to_csv(LOG_FILE, index=False)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nosifer&display=swap');

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
    .hero-text h1 {
        font-size: 2rem;
        margin-bottom: 0.3rem;
        color: white;
        font-family: 'Nosifer', cursive;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
    }
    .hero-text p {
        font-size: 1rem;
        color: #e0e0e0;
    }
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

# ---------- Accuracy Chart ----------
try:
    dive_log_df = pd.read_csv(LOG_FILE)
    dive_log_df["Visibility"] = dive_log_df["Visibility"].str.strip()
    log_scores = dive_log_df["Visibility"].map({"<4 ft": 1, "4–6 ft": 2, "6–8 ft": 3, "8–10 ft": 4, "15+ ft": 5})
    spot_avg_actual = dive_log_df.groupby("Spot")["Visibility"].apply(lambda x: x.map({"<4 ft": 1, "4–6 ft": 2, "6–8 ft": 3, "8–10 ft": 4, "15+ ft": 5}).mean())
    spot_avg_pred = pd.read_csv("forecast.csv") if os.path.exists("forecast.csv") else pd.DataFrame(columns=["Spot", "Score"])
    if not spot_avg_pred.empty:
        chart_df = pd.merge(spot_avg_pred, spot_avg_actual, on="Spot", suffixes=("_Predicted", "_Actual"))
        st.subheader("🎯 Forecast vs Actual Accuracy")
        st.bar_chart(chart_df.set_index("Spot"))
except Exception as e:
    st.caption("No accuracy data available yet. Log a few dives and it will appear here.")
