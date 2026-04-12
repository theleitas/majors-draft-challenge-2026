import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="2026 Masters Draft", layout="wide")
st.title("🏌️‍♂️ 2026 Masters Draft Dashboard")
st.subheader("Top 3 lowest scores per team wins • Live every 10 minutes")

# Auto-refresh every 10 minutes
st_autorefresh(interval=600000, limit=None, key="datarefresh")

# Load teams
with open('teams.json') as f:
    teams_data = json.load(f)

# Fetch live scores + hole from ESPN
@st.cache_data(ttl=600)
def fetch_leaderboard():
    url = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Could not fetch scores: {e}")
        return None

data = fetch_leaderboard()

def get_player_data(api_data):
    if not api_data:
        return {}
    player_data = {}
    try:
        events = api_data.get("events", [])
        if events:
            competitions = events[0].get("competitions", [])
            if competitions:
                for competitor in competitions[0].get("competitors", []):
                    athlete = competitor.get("athlete", {})
                    name = athlete.get("displayName") or athlete.get("shortName")
                    if name:
                        # Current total score to par
                        score_str = competitor.get("score")
                        try:
                            score = float(score_str) if score_str is not None else None
                        except:
                            score = None

                        # Current hole / status
                        status = competitor.get("status", {})
                        status_type = status.get("type", {}) if isinstance(status, dict) else {}
                        hole_raw = status_type.get("shortDetail") or status.get("thru") or status.get("period")
                        
                        if isinstance(hole_raw, (int, float)) or (isinstance(hole_raw, str) and hole_raw.isdigit()):
                            hole = f"Thru {hole_raw}"
                        elif str(hole_raw).upper() == "F" or hole_raw == "Finished":
                            hole = "Finished"
                        else:
                            hole = str(hole_raw) if hole_raw else "Not started"
                        
                        player_data[name] = {"score": score, "hole": hole}
    except:
        pass
    return player_data

player_data = get_player_data(data)

# Calculate standings (only Team + Top 3 Sum)
standings = []
for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    players = info.get("players", [])
    
    scores_list = []
    for player in players:
        info_p = player_data.get(player)
        if info_p and info_p["score"] is not None:
            scores_list.append(info_p["score"])
    
    scores_list.sort()
    top_3_sum = sum(scores_list[:3]) if scores_list else 0
    
    standings.append({
        "Team": team_name,
        "Top 3 Sum": top_3_sum
    })

# Standings table
st.subheader("Current Standings")
if standings:
    df_standings = pd.DataFrame(standings).sort_values("Top 3 Sum")
    st.dataframe(df_standings, use_container_width=True, hide_index=True)
else:
    st.warning("Tournament has not started yet — come back when the first round begins!")

# Team Details — vertical tables with Player | Score | Hole
st.subheader("Team Details")
cols = st.columns(3)
for idx, (coach_id, info) in enumerate(teams_data.items()):
    with cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        
        st.markdown(f"### {team_name}")
        
        table_data = []
        for player in players:
            p_info = player_data.get(player, {"score": None, "hole": "—"})
            table_data.append({
                "Player": player,
                "Score": p_info["score"] if p_info["score"] is not None else "—",
                "Hole": p_info["hole"]
            })
        
        df_team = pd.DataFrame(table_data)
        # Sort by lowest score first
        df_team = df_team.sort_values(by="Score", na_position="last")
        st.dataframe(df_team, use_container_width=True, hide_index=True)
        
        # Top 3 sum metric
        scores_list = [row["Score"] for row in table_data if isinstance(row["Score"], (int, float))]
        scores_list.sort()
        top_3 = scores_list[:3]
        top_3_sum = sum(top_3) if top_3 else 0
        st.metric("Top 3 Sum", top_3_sum)

# ====================== EDIT TEAMS SECTION ======================
st.divider()
with st.expander("🔧 Edit Team Names & Players (anyone can do this)"):
    st.info("Make changes below → click **Generate Updated JSON** → download the file → replace `teams.json` on GitHub. Dashboard updates in <2 minutes.")
    
    new_teams = {}
    for coach_id, info in teams_data.items():
        st.subheader(coach_id)
        new_team_name = st.text_input(
            f"Team Name for {coach_id}",
            value=info.get("team_name", coach_id),
            key=f"name_{coach_id}"
        )
        players_str = "\n".join(info.get("players", []))
        new_players_str = st.text_area(
            f"Players (one name per line) for {coach_id}",
            value=players_str,
            key=f"players_{coach_id}",
            height=140
        )
        new_players = [p.strip() for p in new_players_str.split("\n") if p.strip()]
        
        new_teams[coach_id] = {
            "team_name": new_team_name,
            "players": new_players
        }
    
    if st.button("Generate Updated teams.json", type="primary"):
        st.success("✅ Updated JSON ready below!")
        st.json(new_teams)
        
        json_str = json.dumps(new_teams, indent=2)
        st.download_button(
            label="📥 Download updated teams.json",
            data=json_str,
            file_name="teams.json",
            mime="application/json",
            use_container_width=True
        )
        st.info("→ Go to your GitHub repo → click teams.json → Edit → paste this entire content → Commit changes. Done!")

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%I:%M %p')} • Scores & holes auto-refresh every 10 minutes")
if st.button("🔄 Refresh Scores Now"):
    st.cache_data.clear()
    st.rerun()

# Optional debug
if st.checkbox("Show raw API data (debug only)"):
    st.json(data)
