# ... existing code above remains the same
    # ---------- Adaptive Forecast Based on Logs ----------
    dive_log_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=EXPECTED_COLS)
    spot_adjustments = {}
    debug_rows = []
    try:
        for spot, base in spots:
            spot_logs = dive_log_df[dive_log_df["Spot"] == spot].copy()
            if not spot_logs.empty:
                # Clean up unexpected spacing or characters
                spot_logs["Visibility"] = spot_logs["Visibility"].str.strip()
                log_scores = spot_logs["Visibility"].map({"<4 ft": 1, "4–6 ft": 2, "6–8 ft": 3, "8–10 ft": 4, "15+ ft": 5})
                log_scores = log_scores.dropna()
                if not log_scores.empty:
                    observed_avg = log_scores.mean()
                    adjustment = round(observed_avg - base)
                    adjusted = base + adjustment
                    spot_adjustments[spot] = adjusted
                    debug_rows.append(f"{spot}: base {base}, observed avg {observed_avg:.1f}, adjusted {adjusted}")
                else:
                    spot_adjustments[spot] = base
                    debug_rows.append(f"{spot}: no usable log scores, using base {base}")
            else:
                spot_adjustments[spot] = base
                debug_rows.append(f"{spot}: no logs, using base {base}")
    except Exception as e:
        spot_adjustments = {spot: base for spot, base in spots}
        debug_rows.append("ERROR in log-based scoring")

    forecast = []
    for spot, base in spots:
        adjusted_base = spot_adjustments.get(spot, base)
        score = predict_vis(adjusted_base)
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
    - **Rain**: {rain_total:.2f} in  
    - **SST**: {sst:.1f}°F  
    - **Chlorophyll**: {chlorophyll:.2f} mg/m³
    """)

    st.markdown("""
    ### 📘 Forecast Scoring Breakdown
    - Swell > 3 ft or Wind > 10 kt -> -1
    - Swell < 2 ft and Wind < 5 kt -> +1
    - Tide rate > 1.5 ft (12 hrs) -> -1
    - Rain > 0.1" -> -1
    - SST < 57°F -> -1
    - Chlorophyll > 2 mg/m³ -> -1
    """)

    st.markdown("""
    #### 🔬 Adaptive Adjustments from Dive Logs
    <pre style='font-size: 0.9rem;'>
    """ + "\n".join(debug_rows) + """
    </pre>
    """, unsafe_allow_html=True)
