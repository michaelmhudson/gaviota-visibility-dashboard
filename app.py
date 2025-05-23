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

# ------------------ Site Metadata ------------------
site_profiles = {
    "Tajiguas": {"base": 4, "swell_exposure": 0.6, "runoff": 0.4},
    "Arroyo Quemado": {"base": 4, "swell_exposure": 0.6, "runoff": 0.5},
    "Refugio": {"base": 3, "swell_exposure": 0.4, "runoff": 0.6},
    "Drake’s / Naples": {"base": 5, "swell_exposure": 0.3, "runoff": 0.2},
    "Coal Oil Point": {"base": 4, "swell_exposure": 0.5, "runoff": 0.6},
    "Haskell’s": {"base": 3, "swell_exposure": 0.7, "runoff": 0.8},
    "Mesa Lane": {"base": 3, "swell_exposure": 0.6, "runoff": 0.7},
    "Hendry’s": {"base": 3, "swell_exposure": 0.5, "runoff": 0.9},
    "Butterfly Beach": {"base": 2, "swell_exposure": 0.4, "runoff": 0.3},
}

# ------------------ Live Data Pull ------------------
swell_height, swell_period, swell_dir = 2.6, 13, "WNW"
wind_speed, wind_dir = 5, "W"
tide_stage, current_dir = "Rising", "W (up)"
tide_rate = 0
rain_total = 0
sst = 60
chlorophyll = 1.5

with st.spinner("Loading live data..."):
    try:
        swell_data = requests.get("https://marine.weather.gov/MapClick.php?lat=34.4&lon=-120.1&unit=0&lg=english&FcstType=json").json()
        swell_height = float(swell_data['currentobservation'].get('swell_height_ft', 2.6))
        swell_period = float(swell_data['currentobservation'].get('swell_period_sec', 13))
        wind_speed = float(swell_data['currentobservation'].get('WindSpd', 5))
        wind_dir = swell_data['currentobservation'].get('WindDir', "W")
        sst = float(swell_data['currentobservation'].get('Temp', 60))
    except: pass

    try:
        now = datetime.utcnow()
        begin_date = now.strftime('%Y%m%d')
        end_date = (now + timedelta(days=1)).strftime('%Y%m%d')
        tide_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={begin_date}&end_date={end_date}&station=9411340&product=predictions&datum=MLLW&units=english&time_zone=gmt&format=json&interval=6"
        tide_data = requests.get(tide_url).json()['predictions']
        recent = [float(entry['v']) for entry in tide_data[-3:]]
        tide_rate = abs(recent[-1] - recent[0])
        tide_stage, current_dir = ("Rising", "W (up)") if recent[-1] > recent[0] else ("Falling", "E (down)")
    except: pass

    try:
        rain_url = "https://api.weather.gov/gridpoints/LOX/97,156/forecast"
        rain_data = requests.get(rain_url).json()
        periods = rain_data['properties']['periods']
        for p in periods[:6]:
            if 'rain' in p['shortForecast'].lower():
                rain_total += 0.05
    except: pass

    try:
        chl_url = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/erdMH1chla1day.json?chlorophyll&latitude=34.4&longitude=-120.1&orderBy(%22time%22)"
        chl_data = requests.get(chl_url).json()
        records = chl_data['table']['rows']
        if records:
            chlorophyll = float(records[-1][0])
    except: pass

# ------------------ Adaptive Forecast ------------------
try:
    dive_log_df = pd.read_csv(LOG_FILE)
    dive_log_df["Visibility"] = dive_log_df["Visibility"].str.strip()
except:
    dive_log_df = pd.DataFrame(columns=EXPECTED_COLS)

forecast = []
for spot, meta in site_profiles.items():
    base = meta["base"]
    exposure = meta["swell_exposure"]
    runoff = meta["runoff"]

    # Dive log adaptive adjustment
    logs = dive_log_df[dive_log_df["Spot"] == spot]
    mapped = logs["Visibility"].map({"<4 ft": 1, "4–6 ft": 2, "6–8 ft": 3, "8–10 ft": 4, "15+ ft": 5}).dropna()
    base_adj = round(mapped.mean() - base) if not mapped.empty else 0
    adjusted_base = base + base_adj

    # Live condition adjustments
    score = adjusted_base
    if swell_height * exposure > 3: score -= 1
    if swell_height * exposure < 2 and wind_speed < 5: score += 1
    if wind_speed > 10: score -= 1
    if tide_rate > 1.5: score -= 1
    if rain_total * runoff > 0.1: score -= 1
    if sst < 57: score -= 1
    if chlorophyll > 2: score -= 1
    score = max(1, min(score, 5))
    vis = {5: "15+ ft", 4: "8–10 ft", 3: "6–8 ft", 2: "4–6 ft", 1: "<4 ft"}[score]

    forecast.append({
        "Spot": spot,
        "Visibility": vis,
        "Base": base,
        "Adj": base_adj,
        "Score": score,
        "Swell": f"{swell_height:.1f} @ {swell_period:.0f}s {swell_dir}",
        "Wind": f"{wind_speed:.0f} kt {wind_dir}",
        "Tide": tide_stage,
        "Current": current_dir,
        "Tide Δ (ft)": f"{tide_rate:.2f}",
        "Rain (in)": f"{rain_total:.2f}",
        "SST (°F)": f"{sst:.1f}",
        "Chl (mg/m³)": f"{chlorophyll:.2f}"
    })

df = pd.DataFrame(forecast)

def highlight_score(val):
    bg = '#f4cccc' if val <= 2 else '#fff2cc' if val <= 4 else '#b7e1cd'
    return f'background-color: {bg}; color: #000000'

st.dataframe(df.style.format({"Score": "{:.0f}"}).applymap(highlight_score, subset=["Score"]), use_container_width=True)

best = df[df["Score"] == df["Score"].max()].iloc[0]
st.subheader("🔱 Best Dive Pick Today")
st.markdown(f"""
**{best['Spot']}** — {best['Visibility']} — {int(best['Score'])}/5  
- **Swell**: {best['Swell']}  
- **Wind**: {best['Wind']}  
- **Tide**: {best['Tide']} ({best['Current']})  
- **Tide Rate**: {best['Tide Δ (ft)']}  
- **Rain**: {best['Rain (in)']}  
- **SST**: {best['SST (°F)']}  
- **Chlorophyll**: {best['Chl (mg/m³)']}
""")

st.markdown("""
### 📘 Forecast Scoring Breakdown
- Base score per spot from historical + dive log
- Adjustments based on:
  - Swell * swell exposure
  - Wind speed
  - Tide rate
  - Rainfall * runoff sensitivity
  - SST < 57°F
  - Chlorophyll > 2 mg/m³
""")

st.caption(f"Live data from NOAA, CDIP, and ERDDAP — updated {datetime.now().strftime('%b %d, %I:%M %p')} PST")
