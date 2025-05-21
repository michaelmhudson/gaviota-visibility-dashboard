import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gaviota Visibility", layout="wide")

st.title("🌊 Gaviota Coast Daily Visibility Dashboard")
st.markdown("Spearfishing forecast based on current swell, wind, and tide conditions.")

# Today's static forecast — live version coming soon
data = [
    {"Spot": "Tajiguas", "Visibility": "8–10 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 4},
    {"Spot": "Arroyo Quemado", "Visibility": "6–8 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 3.5},
    {"Spot": "Refugio", "Visibility": "5–7 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Light W", "Score": 3},
    {"Spot": "Drake’s / Naples", "Visibility": "15+ ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 5},
    {"Spot": "Coal Oil Point", "Visibility": "6–8 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Light W", "Score": 3.5},
    {"Spot": "Haskell’s", "Visibility": "5 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Light W", "Score": 2.5},
    {"Spot": "Mesa Lane", "Visibility": "6 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 3},
    {"Spot": "Hendry’s", "Visibility": "4–6 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Light W", "Score": 2.5},
    {"Spot": "Butterfly Beach", "Visibility": "5 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 2}
]

df = pd.DataFrame(data)

# Add color based on score
def color_score(val):
    if val >= 4.5:
        return 'background-color: #b7e1cd'  # green
    elif val >= 3:
        return 'background-color: #fff2cc'  # yellow
    else:
        return 'background-color: #f4cccc'  # red

styled_df = df.style.applymap(color_score, subset=["Score"])

st.dataframe(styled_df, use_container_width=True)

best = df[df['Score'] == df['Score'].max()]
st.subheader("🔱 Best Dive Pick Today")
st.markdown(f"**{best.iloc[0]['Spot']}** — {best.iloc[0]['Visibility']} — {best.iloc[0]['Score']}/5")

st.caption("Predictions based on static data. Live API-powered version coming soon.")
