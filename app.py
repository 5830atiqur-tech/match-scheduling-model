
   

import streamlit as st
from supabase import create_client
import pandas as pd
import json
import base64
from itertools import combinations
from datetime import timedelta, date, time

st.set_page_config(
    page_title="Match Scheduler",
    page_icon="🏏",
    layout="wide"
)
# ---------- SUPABASE CONNECTION ----------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)
# ---------- RESTORE ADMIN SESSION ----------
if st.session_state.get("access_token"):
    supabase.postgrest.auth(
        st.session_state.access_token
    )
# ---------- ADMIN LOGIN ----------
if "admin" not in st.session_state:
    st.session_state.admin = False

with st.sidebar:
    st.subheader("🔐 Admin Login")

    if not st.session_state.admin:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.access_token = result.session.access_token
                supabase.postgrest.auth(st.session_state.access_token)
                user_id = result.user.id

                admin_check = supabase.table("admin_users").select(
                    "user_id"
                ).eq("user_id", user_id).execute()

                if admin_check.data:
                    st.session_state.admin = True
                    st.success("Admin Login Successful!")
                    st.rerun()
                else:
                    supabase.auth.sign_out()
                    st.session_state.admin = False
                    st.error("You are not an authorized admin.")

            except Exception as e:
                st.error(f"Login failed: {e}")

    else:
        st.success("Admin Logged In")

        if st.button("Logout"):
            supabase.auth.sign_out()
            st.session_state.admin = False
            st.rerun()
# ---------- SESSION STORAGE ----------
if "team_count" not in st.session_state:
    st.session_state.team_count = 4

if "logo_data" not in st.session_state:
    st.session_state.logo_data = {}

if "schedule_generated" not in st.session_state:
    st.session_state.schedule_generated = False
# ---------- LOAD FROM SUPABASE ----------
if "db_loaded" not in st.session_state:

    try:
        response = supabase.table(
            "tournament_state"
        ).select("data").eq("id", 1).limit(1).execute()

        if response.data:
            data = response.data[0]["data"]

            st.session_state.team_count = data.get(
                "team_count", 4
            )

            st.session_state.logo_data = data.get(
                "logo_data", {}
            )

            for i, name in enumerate(data.get("team_names", [])):
                st.session_state[f"team_name_{i}"] = name

            if data.get("start_date"):
                st.session_state.start_date = date.fromisoformat(
                    data["start_date"]
                )

            if data.get("match_time"):
                st.session_state.match_time = time.fromisoformat(
                    data["match_time"]
                )

            st.session_state.days_between = data.get(
                "days_between", 1
            )

            st.session_state.schedule_generated = data.get(
                "schedule_generated", False
            )

            for i, winner in enumerate(data.get("winners", [])):
                st.session_state[f"winner_{i}"] = winner

        st.session_state.db_loaded = True

    except Exception as e:
        st.error(f"Database loading error: {e}")
# ---------- LOAD TOURNAMENT ----------
st.subheader("💾 Save / Load Tournament")

uploaded_backup = st.file_uploader(
    "Upload Saved Tournament",
    type=["json"],
    key="backup_upload"
)

if uploaded_backup is not None:

    if st.button("📂 Load Tournament"):

        data = json.load(uploaded_backup)

        st.session_state.team_count = data["team_count"]

        for i, name in enumerate(data["team_names"]):
            st.session_state[f"team_name_{i}"] = name

        st.session_state.logo_data = data.get(
            "logo_data", {}
        )

        st.session_state.start_date = date.fromisoformat(
            data["start_date"]
        )

        st.session_state.match_time = time.fromisoformat(
            data["match_time"]
        )

        st.session_state.days_between = data[
            "days_between"
        ]

        st.session_state.schedule_generated = True

        for i, winner in enumerate(data["winners"]):
            st.session_state[f"winner_{i}"] = winner

        st.success("Tournament Loaded Successfully! 🎉")

        st.rerun()


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

team_names = []
team_logos = {}

if st.session_state.admin:

    number_of_teams = st.number_input(
        "Number of Teams",
        min_value=2,
        max_value=1000,
        value=st.session_state.team_count,
        key="team_count"
    )

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
                key=f"logo_upload_{i}"
            )

        team_names.append(name)

        if logo is not None:
            logo_bytes = logo.getvalue()

            st.session_state.logo_data[str(i)] = (
                base64.b64encode(logo_bytes).decode("utf-8")
            )

        saved_logo = st.session_state.logo_data.get(str(i))

        if saved_logo:
            logo_bytes = base64.b64decode(saved_logo)
            team_logos[name] = logo_bytes

            st.image(
                logo_bytes,
                width=100,
                caption=name
            )

        st.divider()

else:

    number_of_teams = st.session_state.team_count

    st.write("🏏 Tournament Teams")

    for i in range(number_of_teams):

        name = st.session_state.get(
            f"team_name_{i}",
            f"Team {i+1}"
        )

        team_names.append(name)

        st.write(f"*{i+1}. {name}*")

        saved_logo = st.session_state.logo_data.get(str(i))

        if saved_logo:
            logo_bytes = base64.b64decode(saved_logo)
            team_logos[name] = logo_bytes

            st.image(
                logo_bytes,
                width=100
            )

        st.divider()


# ---------- MATCH SETTINGS ----------
st.subheader("📅 Match Settings")

if st.session_state.admin:

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "First Match Date",
            value=st.session_state.get(
                "start_date",
                date.today()
            ),
            key="start_date"
        )

    with col2:
        match_time = st.time_input(
            "Match Time",
            value=st.session_state.get(
                "match_time",
                time(15, 0)
            ),
            key="match_time"
        )

    days_between_matches = st.number_input(
        "Days Between Matches",
        min_value=1,
        max_value=30,
        value=st.session_state.get(
            "days_between",
            1
        ),
        key="days_between"
    )

else:

    start_date = st.session_state.get(
        "start_date",
        date.today()
    )

    match_time = st.session_state.get(
        "match_time",
        time(15, 0)
    )

    days_between_matches = st.session_state.get(
        "days_between",
        1
    )

    st.write("📅 First Match Date:", start_date)
    st.write("🕒 Match Time:", match_time)
    st.write("📆 Days Between Matches:", days_between_matches)


# ---------- GENERATE SCHEDULE ----------
generate = st.button(
    "🏏 Generate Match Schedule",
    use_container_width=True
)

if generate:

    st.session_state.schedule_generated = True

    # Reset old winners if teams change
    for i in range(
        number_of_teams * (number_of_teams - 1) // 2
    ):

        if f"winner_{i}" not in st.session_state:
            st.session_state[f"winner_{i}"] = "Not Played"


# ---------- MATCH SCHEDULE ----------
if st.session_state.get("schedule_generated", False):

    matches = list(combinations(team_names, 2))

    total_matches = len(matches)

    st.write("")

    # ---------- DASHBOARD ----------
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

    # ---------- FIXTURE ----------
    st.markdown(
        '<p class="section-title">📋 Match Fixture</p>',
        unsafe_allow_html=True
    )

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

            st.write(
                "📅",
                match_date.strftime("%d-%m-%Y")
            )

            st.write(
                "⏰",
                match_time.strftime("%I:%M %p")
            )

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

       if st.session_state.admin:

    winner = st.selectbox(
        f"🏆 Select Winner - Match {i+1}",
        options=[
            "Not Played",
            team1,
            team2
        ],
        key=f"winner_{i}"
    )

else:

    winner = st.session_state.get(
        f"winner_{i}",
        "Not Played"
    )

    st.write(f"🏆 Winner: {winner}")

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

    # Create table
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


    # ---------- DOWNLOAD POINTS TABLE ----------
    csv = points_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Download Points Table",
        data=csv,
        file_name="points_table.csv",
        mime="text/csv",
        use_container_width=True
    )


    # ---------- SAVE TOURNAMENT ----------
    tournament_data = {

        "team_count": number_of_teams,

        "team_names": team_names,

        "logo_data": st.session_state.logo_data,

        "start_date": start_date.isoformat(),

        "match_time": match_time.isoformat(),

        "days_between": days_between_matches,

        "winners": [
            st.session_state.get(
                f"winner_{i}",
                "Not Played"
            )
            for i in range(total_matches)
        ]
    }
# ---------- SAVE TO SUPABASE ----------
    if st.session_state.admin:

        if st.button("☁️ Save Tournament Online", use_container_width=True):

            try:
                supabase.table("tournament_state").upsert({
                    "id": 1,
                    "data": tournament_data
                }).execute()

                st.success("Tournament Saved Online Successfully! 🎉")

            except Exception as e:
                st.error(f"Database Save Error: {e}")
    json_data = json.dumps(
        tournament_data,
        indent=4
    )

    st.markdown("---")

    st.subheader("💾 Save Tournament")

    st.download_button(
        label="💾 Save Tournament Backup",
        data=json_data,
        file_name="my_tournament.json",
        mime="application/json",
        use_container_width=True
    )

    st.success(
        "Download the backup file to keep your Tournament safe."
    )