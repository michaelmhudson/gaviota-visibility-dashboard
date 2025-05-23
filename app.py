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

# ---------- Hero Banner ----------
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

# ---------- Spot Profiles ----------
site_profiles = {
    "Tajiguas": {"base": 4, "swell_exposure": 0.6, "runoff": 0.4, "kelp_index": 0.7, "cam": "https://www.surfline.com/surf-report/gaviota-pier/5842041f4e65fad6a770885b"},
    "Arroyo Quemado": {"base": 4, "swell_exposure": 0.6, "runoff": 0.5, "kelp_index": 0.6, "cam": None},
    "Refugio": {"base": 3, "swell_exposure": 0.4, "runoff": 0.6, "kelp_index": 0.8, "cam": None},
    "Drake’s / Naples": {"base": 5, "swell_exposure": 0.3, "runoff": 0.2, "kelp_index": 0.9, "cam": None},
    "Coal Oil Point": {"base": 4, "swell_exposure": 0.5, "runoff": 0.6, "kelp_index": 0.5, "cam": "https://www.surfline.com/surf-report/devereux/5842041f4e65fad6a7708962"},
    "Haskell’s": {"base": 3, "swell_exposure": 0.7, "runoff": 0.8, "kelp_index": 0.3, "cam": None},
    "Mesa Lane": {"base": 3, "swell_exposure": 0.6, "runoff": 0.7, "kelp_index": 0.3, "cam": None},
    "Hendry’s": {"base": 3, "swell_exposure": 0.5, "runoff": 0.9, "kelp_index": 0.4, "cam": "https://www.surf-forecast.com/breaks/Hendry-s-Beach-Arroyo-Burro"},
    "Butterfly Beach": {"base": 2, "swell_exposure": 0.4, "runoff": 0.3, "kelp_index": 0.2, "cam": None}
}

# ---------- Load Live Data ----------
swell_height, swell_period, swell_dir = 2.6, 13, "WNW"
wind_speed, wind_dir = 5, "W"
tide_stage, current_dir = "Rising", "W (up)"
tide_rate = 0
rain_total = 0
sst = 60
chlorophyll = 1.5

try:
    res = requests.get("https://marine.weather.gov/MapClick.php?lat=34.4&lon=-120.1&unit=0&lg=english&FcstType=json").json()
    swell_height = float(res['currentobservation'].get('swell_height_ft', swell_height))
    swell_period = float(res['currentobservation'].get('swell_period_sec', swell_period))
    wind_speed = float(res['currentobservation'].get('WindSpd', wind_speed))
    wind_dir = res['currentobservation'].get('WindDir', wind_dir)
    sst = float(res['currentobservation'].get('Temp', sst))
except: pass

try:
    now = datetime.utcnow()
    tide_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={now.strftime('%Y%m%d')}&end_date={(now + timedelta(days=1)).strftime('%Y%m%d')}&station=9411340&product=predictions&datum=MLLW&units=english&time_zone=gmt&format=json&interval=6"
    tide_data = requests.get(tide_url).json()['predictions']
    recent = [float(e['v']) for e in tide_data[-3:]]
    tide_rate = abs(recent[-1] - recent[0])
    tide_stage, current_dir = ("Rising", "W (up)") if recent[-1] > recent[0] else ("Falling", "E (down)")
except: pass

try:
    rain = requests.get("https://api.weather.gov/gridpoints/LOX/97,156/forecast").json()
    for p in rain['properties']['periods'][:6]:
        if 'rain' in p['shortForecast'].lower():
            rain_total += 0.05
except: pass

try:
    chl = requests.get("https://coastwatch.pfeg.noaa.gov/erddap/tabledap/erdMH1chla1day.json?chlorophyll&latitude=34.4&longitude=-120.1&orderBy(%22time%22)").json()
    rows = chl['table']['rows']
    if rows:
        chlorophyll = float(rows[-1][0])
except: pass

# ---------- Dive Logs ----------
try:
    dive_log_df = pd.read_csv(LOG_FILE)
    dive_log_df["Visibility"] = dive_log_df["Visibility"].str.strip()
except:
    dive_log_df = pd.DataFrame(columns=EXPECTED_COLS)

# ---------- Forecast Table ----------
forecast = []
for spot, meta in site_profiles.items():
    base = meta["base"]
    exposure, runoff, kelp = meta["swell_exposure"], meta["runoff"], meta["kelp_index"]

    logs = dive_log_df[dive_log_df["Spot"] == spot]
    mapped = logs["Visibility"].map({"<4 ft": 1, "4–6 ft": 2, "6–8 ft": 3, "8–10 ft": 4, "15+ ft": 5}).dropna()
    base_adj = round(mapped.mean() - base) if not mapped.empty else 0
    adjusted = base + base_adj

    score = adjusted
    if swell_height * exposure * (1 - kelp) > 3: score -= 1
    if swell_height * exposure * (1 - kelp) < 2 and wind_speed < 5: score += 1
    if wind_speed > 10: score -= 1
    if tide_rate > 1.5: score -= 1
    if rain_total * runoff > 0.1: score -= 1
    if sst < 57: score -= 1
    if chlorophyll > 2: score -= 1
    score = max(1, min(score, 5))
    vis = {5: "15+ ft", 4: "8–10 ft", 3: "6–8 ft", 2: "4–6 ft", 1: "<4 ft"}[score]

    forecast.append({
        "Spot": spot, "Visibility": vis, "Base": base, "Adj": base_adj, "Score": score,
        "Swell": f"{swell_height:.1f} @ {swell_period:.0f}s {swell_dir}",
        "Wind": f"{wind_speed:.0f} kt {wind_dir}", "Tide": tide_stage, "Current": current_dir,
        "Tide Δ (ft)": f"{tide_rate:.2f}", "Rain (in)": f"{rain_total:.2f}",
        "SST (°F)": f"{sst:.1f}", "Chl (mg/m³)": f"{chlorophyll:.2f}", "Kelp Index": kelp
    })

df = pd.DataFrame(forecast)

def highlight_score(val):
    bg = '#f4cccc' if val <= 2 else '#fff2cc' if val <= 4 else '#b7e1cd'
    return f'background-color: {bg}; color: #000000'

st.subheader("📊 Daily Forecast")
st.dataframe(df.style.format({"Score": "{:.0f}"}).applymap(highlight_score, subset=["Score"]), use_container_width=True)

# ---------- Surf Cam Links ----------
st.subheader("📷 Live Surf Cams")
for spot, meta in site_profiles.items():
    if meta["cam"]:
        st.markdown(f"[{spot} Cam]({meta['cam']})")

st.caption(f"Live data from NOAA, CDIP, ERDDAP — updated {datetime.now().strftime('%b %d, %I:%M %p')} PST")
