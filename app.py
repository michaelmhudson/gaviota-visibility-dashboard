import streamlit as st
import pandas as pd

# Static forecast data (we'll make it live later)
data = [
    {"Spot": "Tajiguas", "Visibility": "8–10 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 4},
    {"Spot": "Naples", "Visibility": "15+ ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 5},
    {"Spot": "Butterfly", "Visibility": "5 ft", "Tide": "Rising", "Current": "W (up)", "Swell": "2.6 @ 13s WNW", "Wind": "Calm", "Score": 2},
    # Add more as needed
]

df = pd.DataFrame(data)

st.title("🌊 Gaviota Coast Visibility Dashboard")
st.write("Live daily forecast for dive visibility at key Gaviota Coast spots.")

st.dataframe(df)

best = df[df['Score'] == df['Score'].max()]
st.subheader("🔱 Best Dive Pick Today")
st.write(f"**{best.iloc[0]['Spot']}** — {best.iloc[0]['Visibility']}")
