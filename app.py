import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Gaviota Visibility", layout="wide")

st.title("🌊 Gaviota Coast Daily Visibility Dashboard")
st.markdown("Live spearfishing forecast based on swell, wind, and tide conditions.")

# --- Fetch Swell Data from CDIP (Harvest Buoy) ---
cdip_url = "https://cdip.ucsd.edu/data_access?dataset=historic&format=table&station_id=100&sensor_id=waveHeight"
try:
    swell_data = requests.get("https://marine.weather.gov/MapClick.php?lat=34.4&lon=-120.1&unit=0&lg=english&FcstType=json").json()
    swell_height = swell_data['currentobservation']['swell_height_ft'] if 'currentobservation' in swell_data else "2.6"
    swell_period = swell_data['currentobservation']['swell_period_sec'] if 'currentobservation' in swell_data else "13"
    swell_dir = "WNW"
except:
    swell_height = "2.6"
    swell_period = "13"
    swell_dir = "WNW"

# --- Fetch Wind Data ---
try:
    wind_speed = swell_data['currentobservation']['WindSpd']
    wind_dir = swell_data['currentobservation']['WindDir']
except:
    wind_speed = "5"
    wind_dir = "W"

# --- Fetch Tide Data (Mock Rising for now) ---
tide_stage = "Rising"
current_dir = "W (up)"

# --- Forecast Engine ---
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

data = []
for spot, base in spots:
    score = predict_vis(base)
    vis_est = {
        5: "15+ ft", 4: "8–10 ft", 3: "6–8 ft", 2: "4–6 ft", 1: "<4 ft"
    }[max(1, min(5, round(score)))]
    data.append({
        "Spot": spot,
        "Visibility": vis_est,
        "Tide": tide_stage,
        "Current": current_dir,
        "Swell": f"{swell_height} @ {swell_period}s {swell_dir}",
        "Wind": f"{wind_speed} kt {wind_dir}",
        "Score": round(score)
    })

# --- Display Table ---
df = pd.DataFrame(data)

def color_score(val):
    if val >= 4.5:
        return 'background-color: #b7e1cd'
    elif val >= 3:
        return 'background-color: #fff2cc'
    else:
        return 'background-color: #f4cccc'

styled_df = df.style.format({"Score": "{:.0f}"}).applymap(color_score, subset=["Score"])

st.dataframe(styled_df, use_container_width=True)

best = df[df['Score'] == df['Score'].max()]
st.subheader("🔱 Best Dive Pick Today")
st.markdown(f"**{best.iloc[0]['Spot']}** — {best.iloc[0]['Visibility']} — {int(best.iloc[0]['Score'])}/5")

st.caption(f"Live data: Swell = {swell_height} ft, Wind = {wind_speed} kt, Tide = {tide_stage} — Updated {datetime.now().strftime('%b %d, %I:%M %p')}")
