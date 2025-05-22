import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import os

# ---------- Config ----------
st.set_page_config(page_title="Gaviota Visibility Dashboard", layout="wide", initial_sidebar_state="collapsed")

LOG_FILE = "dive_log.csv"
EXPECTED_COLS = ["Date", "Time", "Spot", "Visibility", "Notes", "Fish Taken"]
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

# ---------- Forecast ----------
st.subheader("🔎 Forecast")
with st.spinner("Pulling live swell, wind, and tide data..."):
    try:
        swell_data = requests.get("https://marine.weather.gov/MapClick.php?lat=34.4&lon=-120.1&unit=0&lg=english&FcstType=json").json()
        swell_height = float(swell_data['currentobservation'].get('swell_height_ft', 2.6))
        swell_period = float(swell_data['currentobservation'].get('swell_period_sec', 13))
        swell_dir = "WNW"
        wind_speed = float(swell_data['currentobservation'].get('WindSpd', 5))
        wind_dir = swell_data['currentobservation'].get('WindDir', "W")
    except:
        swell_height, swell_period, swell_dir = 2.6, 13, "WNW"
        wind_speed, wind_dir = 5, "W"

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

    def predict_vis(score_base):
        if swell_height > 3 or wind_speed > 10:
            return max(score_base - 1, 1)
        elif swell_height < 2 and wind_speed < 5:
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

    styled_df = df.style.format({"Score": "{:.0f}"}).applymap(highlight_score, subset=["Score"])
    st.dataframe(styled_df, use_container_width=True)

    best = df[df['Score'] == df['Score'].max()].iloc[0]
    st.subheader("🔱 Best Dive Pick Today")
    st.markdown(f"""
    **{best['Spot']}** — {best['Visibility']} — {int(best['Score'])}/5
    - **Swell**: {best['Swell']}
    - **Wind**: {best['Wind']}
    - **Tide**: {best['Tide']} ({best['Current']})
    """)

    st.markdown("""
    ### 📘 How Forecast is Calculated
    Visibility score is based on this logic:
    - **Subtract 1** if swell > 3 ft or wind > 10 kt (murky/surgey)
    - **Add 1** if swell < 2 ft and wind < 5 kt (clean & calm)
    - Otherwise, keep baseline rating for the spot
    """)

    st.subheader("📊 Conditions Snapshot")
    st.bar_chart(pd.DataFrame({
        "Swell Height (ft)": [swell_height],
        "Wind Speed (kt)": [wind_speed]
    }))

# ---------- Log a Dive ----------
st.subheader("📘 Log a Dive")
with st.form("log_form"):
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", value=datetime.today())
        time = st.time_input("Time", value=datetime.now().time())
        spot = st.selectbox("Spot", [s["Spot"] for s in forecast])
    with col2:
        vis = st.selectbox("Observed Visibility", ["<4 ft", "4–6 ft", "6–8 ft", "8–10 ft", "15+ ft"])
        fish = st.text_input("Fish Taken")
        notes = st.text_area("Notes", placeholder="Surge, bait, thermocline...")
    submitted = st.form_submit_button("Save Entry")
    if submitted:
        new_entry = pd.DataFrame([{ "Date": date, "Time": time.strftime('%H:%M'), "Spot": spot, "Visibility": vis, "Notes": notes, "Fish Taken": fish }])
        new_entry.to_csv(LOG_FILE, mode='a', header=False, index=False)
        st.success("Dive logged successfully!")

# ---------- Dive Logbook ----------
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
st.caption(f"Live data from NOAA & CDIP — Last updated {datetime.now().strftime('%b %d, %I:%M %p')} PST")
