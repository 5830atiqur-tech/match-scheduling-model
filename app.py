
   
import streamlit as st
import pandas as pd
from itertools import combinations
from datetime import timedelta

st.set_page_config(
    page_title="Match Scheduler",
    page_icon="🏏",
    layout="wide"
)

# ---------- DESIGN ----------
st.markdown("""
<style>
.stApp {
    background-color: #f0f4f8;
}

.main-title {
    background: linear-gradient(90deg, #12233f, #1d557a);
    padding: 25px;
    border-radius: 15px;
    color: white;
    text-align: center;
}

.section-title {
    color: #17365d;
    font-size: 25px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
st.markdown("""
<div class="main-title">
    <h1>🏏 MATCH SCHEDULER</h1>
    <p>Tournament Management Dashboard</p>
</div>
""", unsafe_allow_html=True)

st.write("")

# ---------- TEAM INFORMATION ----------
st.subheader("👥 Team Information")

number_of_teams = st.number_input(
    "Number of Teams",
    min_value=2,
    max_value=20,
    value=4
)

team_names = []
team_logos = {}

st.write("Enter Team Names and Upload Logos")

for i in range(number_of_teams):

    col1, col2 = st.columns([2, 1])

    with col1:
        name = st.text_input(
            f"Team {i+1} Name",
            value=f"Team {i+1}",
            key=f"team_name_{i}"
        )

    with col2:
        logo = st.file_uploader(
            f"Team {i+1} Logo",
            type=["png", "jpg", "jpeg"],
            key=f"team_logo_{i}"
        )

    team_names.append(name)

    if logo is not None:
        team_logos[name] = logo

        st.image(
            logo,
            width=100,
            caption=name
        )

    st.divider()

# ---------- MATCH SETTINGS ----------
st.subheader("📅 Match Settings")

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "First Match Date"
    )

with col2:
    match_time = st.time_input(
        "Match Time"
    )

days_between_matches = st.number_input(
    "Days Between Matches",
    min_value=1,
    max_value=30,
    value=1
)

# ---------- GENERATE SCHEDULE ----------
generate = st.button(
    "🏏 Generate Match Schedule",
    use_container_width=True
)

if generate:
    st.session_state.schedule_generated = True

# ---------- MATCH SCHEDULE ----------
if st.session_state.get("schedule_generated", False):

    matches = list(combinations(team_names, 2))

    total_matches = len(matches)

    st.write("")

    # Dashboard
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "👥 Total Teams",
            number_of_teams
        )

    with col2:
        st.metric(
            "🏏 Total Matches",
            total_matches
        )

    st.write("")

    # Fixture Section
    st.markdown(
        '<p class="section-title">📋 Match Fixture</p>',
        unsafe_allow_html=True
    )

    # ---------- MATCHES ----------
    for i, match in enumerate(matches):

        team1 = match[0]
        team2 = match[1]

        match_date = start_date + timedelta(
            days=i * days_between_matches
        )

        st.markdown("---")

        st.markdown(f"### 🏏 Match {i+1}")

        col1, col2, col3 = st.columns([1, 2, 2])

        with col1:
            st.write("📅", match_date.strftime("%d-%m-%Y"))
            st.write("⏰", match_time.strftime("%I:%M %p"))

        with col2:
            if team1 in team_logos:
                st.image(
                    team_logos[team1],
                    width=80
                )

            st.markdown(f"### {team1}")

        with col3:
            if team2 in team_logos:
                st.image(
                    team_logos[team2],
                    width=80
                )

            st.markdown(f"### {team2}")

        # ---------- WINNER SELECTION ----------
        winner = st.selectbox(
            f"🏆 Select Winner - Match {i+1}",
            options=[
                "Not Played",
                team1,
                team2
            ],
            key=f"winner_{i}"
        )

        st.write("")

    # ---------- POINTS TABLE ----------
    st.markdown("---")

    st.markdown(
        '<p class="section-title">🏆 Tournament Points Table</p>',
        unsafe_allow_html=True
    )

    standings = {}

    for team in team_names:

        standings[team] = {
            "Team": team,
            "Played": 0,
            "Won": 0,
            "Lost": 0,
            "Points": 0
        }

    # Calculate points
    for i, match in enumerate(matches):

        team1 = match[0]
        team2 = match[1]

        winner = st.session_state.get(
            f"winner_{i}",
            "Not Played"
        )

        if winner != "Not Played":

            loser = team2 if winner == team1 else team1

            standings[team1]["Played"] += 1
            standings[team2]["Played"] += 1

            standings[winner]["Won"] += 1
            standings[loser]["Lost"] += 1

            standings[winner]["Points"] += 2

    # Create Table
    points_df = pd.DataFrame(
        list(standings.values())
    )

    points_df = points_df.sort_values(
        by=["Points", "Won"],
        ascending=False
    )

    points_df = points_df.reset_index(drop=True)

    points_df.insert(
        0,
        "Rank",
        range(1, len(points_df) + 1)
    )

    st.dataframe(
        points_df,
        use_container_width=True,
        hide_index=True
    )

    # ---------- WINNER ----------
    if len(points_df) > 0:

        highest_points = points_df["Points"].max()

        top_teams = points_df[
            points_df["Points"] == highest_points
        ]

        if highest_points > 0:

            if len(top_teams) == 1:

                st.success(
                    f"🏆 Tournament Leader: "
                    f"{top_teams.iloc[0]['Team']}"
                )

            else:

                st.info(
                    "🤝 There is a tie between "
                    + ", ".join(top_teams["Team"])
                )

    # ---------- DOWNLOAD ----------
    csv = points_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download Points Table",
        data=csv,
        file_name="points_table.csv",
        mime="text/csv",
        use_container_width=True
    )