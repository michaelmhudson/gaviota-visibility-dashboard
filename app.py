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
    html, body, [class*="css"] {
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

# Site Profiles with Kelp Index and Cam URLs
site_profiles = {
    "Tajiguas": {"base": 4, "swell_exposure": 0.6, "runoff": 0.4, "kelp_index": 0.7, "cam": "https://www.surfline.com/surf-report/gaviota-pier/5842041f4e65fad6a770885b"},
    "Arroyo Quemado": {"base": 4, "swell_exposure": 0.6, "runoff": 0.5, "kelp_index": 0.6, "cam": None},
    "Refugio": {"base": 3, "swell_exposure": 0.4, "runoff": 0.6, "kelp_index": 0.8, "cam": None},
    "Drake’s / Naples": {"base": 5, "swell_exposure": 0.3, "runoff": 0.2, "kelp_index": 0.9, "cam": None},
    "Coal Oil Point": {"base": 4, "swell_exposure": 0.5, "runoff": 0.6, "kelp_index": 0.5, "cam": "https://www.surfline.com/surf-report/coal-oil-point/584204204e65fad6a7708e49"},
    "Haskell’s": {"base": 3, "swell_exposure": 0.7, "runoff": 0.8, "kelp_index": 0.3, "cam": None},
    "Mesa Lane": {"base": 3, "swell_exposure": 0.6, "runoff": 0.7, "kelp_index": 0.3, "cam": None},
    "Hendry’s": {"base": 3, "swell_exposure": 0.5, "runoff": 0.9, "kelp_index": 0.4, "cam": "https://www.surfline.com/surf-report/hendrys-beach/584204204e65fad6a7708e1b"},
    "Butterfly Beach": {"base": 2, "swell_exposure": 0.4, "runoff": 0.3, "kelp_index": 0.2, "cam": None},
}

# Add optional cam embeds
st.subheader("📷 Live Surf Cams")
for spot, meta in site_profiles.items():
    if meta["cam"]:
        st.markdown(f"[{spot} Cam]({meta['cam']})")
