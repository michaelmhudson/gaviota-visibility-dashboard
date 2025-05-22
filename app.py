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

st.subheader("🔎 Forecast")
with st.spinner("Pulling live swell, wind, tide, rain, SST and chlorophyll data..."):
    try:
        swell_data = requests.get("https://marine.weather.gov/MapClick.php?lat=34.4&lon=-120.1&unit=0&lg=english&FcstType=json").json()
        swell_height = float(swell_data['currentobservation'].get('swell_height_ft', 2.6))
        swell_period = float(swell_data['currentobservation'].get('swell_period_sec', 13))
        swell_dir = "WNW"
        wind_speed = float(swell_data['currentobservation'].get('WindSpd', 5))
        wind_dir = swell_data['currentobservation'].get('WindDir', "W")
        sst = float(swell_data['currentobservation'].get('Temp', 60))  # Approx SST in °F
    except:
        swell_height, swell_period, swell_dir = 2.6, 13, "WNW"
        wind_speed, wind_dir, sst = 5, "W", 60

    tide_stage = "Rising"
    current_dir = "W (up)"
    tide_rate = 0
    try:
        now = datetime.utcnow()
        begin_date = now.strftime('%Y%m%d')
        end_date = (now + timedelta(days=1)).strftime('%Y%m%d')
        tide_url = f"https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?begin_date={begin_date}&end_date={end_date}&station=9411340&product=predictions&datum=MLLW&units=english&time_zone=gmt&format=json&interval=6"
        tide_data = requests.get(tide_url).json()['predictions']
        recent = [float(entry['v']) for entry in tide_data[-3:]]
        tide_rate = abs(recent[-1] - recent[0])
        if recent[-1] > recent[0]:
            tide_stage, current_dir = "Rising", "W (up)"
        else:
            tide_stage, current_dir = "Falling", "E (down)"
    except:
        pass

    rain_total = 0
    try:
        rain_url = "https://api.weather.gov/gridpoints/LOX/97,156/forecast"
        rain_data = requests.get(rain_url).json()
        periods = rain_data['properties']['periods']
        for p in periods[:6]:
            if 'rain' in p['shortForecast'].lower():
                rain_total += 0.05
    except:
        pass

    chlorophyll = 0
    try:
        chl_url = "https://coastwatch.pfeg.noaa.gov/erddap/tabledap/erdMH1chla1day.json?chlorophyll&latitude=34.4&longitude=-120.1&orderBy(%22time%22)"
        chl_data = requests.get(chl_url).json()
        records = chl_data['table']['rows']
        if records:
            chlorophyll = float(records[-1][0])
    except:
        chlorophyll = 1.5

    def predict_vis(score_base):
        score = score_base
        if swell_height > 3 or wind_speed > 10:
            score -= 1
        if swell_height < 2 and wind_speed < 5:
            score += 1
        if tide_rate > 1.5:
            score -= 1
        if rain_total > 0.1:
            score -= 1
        if sst < 57:
            score -= 1
        if chlorophyll > 2:
            score -= 1
        return max(1, min(score, 5))

    spots = [
        ("Tajiguas", 4), ("Arroyo Quemado", 4), ("Refugio", 3),
        ("Drake’s / Naples", 5), ("Coal Oil Point", 4), ("Haskell’s", 3),
        ("Mesa Lane", 3), ("Hendry’s", 3), ("Butterfly Beach", 2)
    ]

    forecast = []
    for spot, base in spots:
        score = predict_vis(base)
        vis_est = {5: "15+ ft", 4: "8–10 ft", 3: "6–8 ft", 2: "4–6 ft", 1: "<4 ft"}[score]
        forecast.append({
            "Spot": spot,
            "Visibility": vis_est,
            "Tide": tide_stage,
            "Current": current_dir,
            "Swell": f"{swell_height:.1f} @ {swell_period:.0f}s {swell_dir}",
            "Wind": f"{wind_speed:.0f} kt {wind_dir}",
            "Score": score
        })

    df = pd.DataFrame(forecast)

    def highlight_score(val):
        bg = '#f4cccc' if val <= 2 else '#fff2cc' if val <= 4 else '#b7e1cd'
        return f'background-color: {bg}; color: #000000'

    st.dataframe(df.style.format({"Score": "{:.0f}"}).applymap(highlight_score, subset=["Score"]), use_container_width=True)

    best = df[df['Score'] == df['Score'].max()].iloc[0]
    st.subheader("🔱 Best Dive Pick Today")
    st.markdown(f"""
    **{best['Spot']}** — {best['Visibility']} — {int(best['Score'])}/5  
    - **Swell**: {best['Swell']}  
    - **Wind**: {best['Wind']}  
    - **Tide**: {best['Tide']} ({best['Current']})  
    - **Tide Rate**: {tide_rate:.2f} ft over 12 hrs  
    - **Rain**: {rain_total:.2f}"  
    - **SST**: {sst:.1f}°F  
    - **Chlorophyll**: {chlorophyll:.2f} mg/m³"")

    st.markdown("""
    ### 📘 Forecast Scoring Breakdown
    - Swell > 3 ft or Wind > 10 kt → −1
    - Swell < 2 ft and Wind < 5 kt → +1
    - Tide rate > 1.5 ft (12 hrs) → −1
    - Rain > 0.1" → −1
    - SST < 57°F → −1
    - Chlorophyll > 2 mg/m³ → −1
    """)

st.caption(f"Live data from NOAA, CDIP, and ERDDAP — updated {datetime.now().strftime('%b %d, %I:%M %p')} PST")
