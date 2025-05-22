import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# ---------- Config ----------
st.set_page_config(page_title="Gaviota Visibility Dashboard", layout="wide", initial_sidebar_state="collapsed")

# ---------- Custom Styles with Inter Font ----------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;500;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif !important;
        color: #f1f1f1;
    }

    h1, h2, h3, h4 {
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .block-container {
        padding-top: 0rem;
    }

    .hero {
        background-image: url('https://raw.githubusercontent.com/michaelmhudson/gaviota-visibility-dashboard/main/assets/hero.jpg');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        padding: 4rem 2rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="hero">
        <h1>Gaviota Coast Spearfishing Dashboard</h1>
        <p>Live visibility forecasts. Smart predictions. Your personal dive log.</p>
    </div>
""", unsafe_allow_html=True)

# ---------- Pull Conditions ----------
try:
    swell_data = requests.get("https://marine.weather.gov/MapClick.php?lat=34.4&lon=-120.1&unit=0&lg=english&FcstType=json").json()
    swell_height = swell_data['currentobservation'].get('swell_height_ft', "2.6")
    swell_period = swell_data['currentobservation'].get('swell_period_sec', "13")
    swell_dir = "WNW"
    wind_speed = swell_data['currentobservation'].get('WindSpd', "5")
    wind_dir = swell_data['currentobservation'].get('WindDir', "W")
except:
    swell_height, swell_period, swell_dir = "2.6", "13", "WNW"
    wind_speed, wind_dir = "5", "W"

# ---------- Tide + Current ----------
tide_stage = "Rising"
current_dir = "W (up)"
try:
    now = datetime.utcnow()
    begin_date = now.strftime('%Y%m%d')
    end_date = (now + timedelta(days=1)).strftime('%Y%m%d')
    tide_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={begin_date}&end_date={end_date}&station=9411340&product=predictions&datum=MLLW&units=english&time_zone=gmt&format=json&interval=h"
    tide_data = requests.get(tide_url).json()['predictions']
    current_time = now.strftime('%Y-%m-%d %H')
    levels = [(entry['t'], float(entry['v'])) for entry in tide_data if entry['t'].startswith(current_time)]
    if len(levels) >= 2:
        if levels[1][1] > levels[0][1]:
            tide_stage, current_dir = "Rising", "W (up)"
        else:
            tide_stage, current_dir = "Falling", "E (down)"
except:
    pass

# ---------- Forecast Engine ----------
def predict_vis(score_base):
    swell = float(swell_height)
    wind = float(wind_speed)
    if swell > 3 or wind > 10:
        return score_base - 1
    elif swell < 2 and wind < 5:
        return min(score_base + 1, 5)
    return score_base

spots = [
    ("Tajiguas", 4), ("Arroyo Quemado", 4), ("Refugio", 3),
    ("Drake’s / Naples", 5), ("Coal Oil Point", 4), ("Haskell’s", 3),
    ("Mesa Lane", 3), ("Hendry’s", 3), ("Butterfly Beach", 2)
]

forecast = []
for spot, base in spots:
    score = predict_vis(base)
    vis_est = {5: "15+ ft", 4: "8–10 ft", 3: "6–8 ft", 2: "4–6 ft", 1: "<4 ft"}[max(1, min(5, round(score)))]
    forecast.append({
        "Spot": spot,
        "Visibility": vis_est,
        "Tide": tide_stage,
        "Current": current_dir,
        "Swell": f"{swell_height} @ {swell_period}s {swell_dir}",
        "Wind": f"{wind_speed} kt {wind_dir}",
        "Score": round(score)
    })

df = pd.DataFrame(forecast)

def color_score(val):
    if val >= 4.5:
        return 'background-color: #b7e1cd'
    elif val >= 3:
        return 'background-color: #fff2cc'
    else:
        return 'background-color: #f4cccc'

styled_df = df.style.format({"Score": "{:.0f}"}).applymap(color_score, subset=["Score"])

st.subheader("🔎 Forecast")
st.dataframe(styled_df, use_container_width=True)

# ---------- Best Pick ----------
best = df[df['Score'] == df['Score'].max()]
st.subheader("🔱 Best Dive Pick Today")
st.markdown(f"**{best.iloc[0]['Spot']}** — {best.iloc[0]['Visibility']} — {int(best.iloc[0]['Score'])}/5")

# ---------- Log Dive Section ----------
st.subheader("📘 Log a Dive")
log_file = "dive_log.csv"
if not os.path.exists(log_file):
    pd.DataFrame(columns=["Date", "Time", "Spot", "Visibility", "Notes", "Fish Taken"]).to_csv(log_file, index=False)

with st.form("log_form"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", value=datetime.today())
        time = st.time_input("Time", value=datetime.now().time())
        spot = st.selectbox("Spot", [s[0] for s in spots])
    with col2:
        vis = st.selectbox("Observed Visibility", ["<4 ft", "4–6 ft", "6–8 ft", "8–10 ft", "15+ ft"])
        fish = st.text_input("Fish Taken")
        notes = st.text_area("Notes", placeholder="Surge, bait, thermocline...")
    submitted = st.form_submit_button("Save Entry")
    if submitted:
        new_entry = pd.DataFrame([[date, time.strftime('%H:%M'), spot, vis, notes, fish]],
                                 columns=["Date", "Time", "Spot", "Visibility", "Notes", "Fish Taken"])
        new_entry.to_csv(log_file, mode='a', header=False, index=False)
        st.success("Dive logged successfully!")

# ---------- Dive Logbook Viewer ----------
st.subheader("📚 Your Dive Logbook")
log_df = pd.read_csv(log_file)
st.dataframe(log_df.sort_values(by="Date", ascending=False), use_container_width=True)

# ---------- Footer ----------
st.caption(f"Live data from NOAA & CDIP — Last updated {datetime.now().strftime('%b %d, %I:%M %p')} PST")
st.markdown("""
**Resources:**  
[Harvest CDIP Buoy](https://cdip.ucsd.edu/m/products/?buoy=100&xitem=spectra)  
[NOAA Santa Barbara Tide Station](https://tidesandcurrents.noaa.gov/stationhome.html?id=9411340)
""")
