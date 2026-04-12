import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="2026 Masters Draft", layout="wide")
st.title("🏌️‍♂️ 2026 Masters Draft Dashboard")
st.subheader("Top 3 lowest scores per team wins • Live scores every 10 minutes")

# Auto-refresh every 10 minutes (600000 ms)
st_autorefresh(interval=600000, limit=None, key="datarefresh")

# Load teams
with open('teams.json') as f:
    teams_data = json.load(f)

# Fetch live scores from ESPN public API
@st.cache_data(ttl=600)  # cache for 10 minutes
def fetch_leaderboard():
    # This endpoint works for the Masters (and all PGA events)
    url = "https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Could not fetch scores: {e}")
        st.info("The ESPN API sometimes changes. Click Refresh or let me know and I'll update the endpoint.")
        return None

data = fetch_leaderboard()

def get_player_scores(api_data):
    if not api_data:
        return {}
    player_scores = {}
    try:
        # ESPN structure for golf leaderboard
        events = api_data.get("events", [])
        if events:
            competitions = events[0].get("competitions", [])
            if competitions:
                for competitor in competitions[0].get("competitors", []):
                    athlete = competitor.get("athlete", {})
                    name = athlete.get("displayName") or athlete.get("shortName")
                    if name:
                        # Score is usually the to-par value (e.g. -7 or +2)
                        score_str = competitor.get("score", "300")
                        try:
                            score = float(score_str) if score_str.replace("-", "").replace("+", "").replace(".", "").isdigit() else 300
                        except:
                            score = 300
                        player_scores[name] = score
    except:
        pass  # graceful fallback
    return player_scores

player_scores = get_player_scores(data)

# Calculate standings
standings = []
for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    players = info.get("players", [])
    team_player_scores = []
    
    for player in players:
        score = player_scores.get(player)
        if score is not None:
            team_player_scores.append((player, score))
    
    # Sort by lowest score first
    team_player_scores.sort(key=lambda x: x[1])
    top_3 = team_player_scores[:3]
    top_3_sum = sum(score for _, score in top_3)
    
    standings.append({
        "Team": team_name,
        "Top 3 Sum": top_3_sum,
        "Players in Top 3": len(top_3),
        "Players with Scores": len(team_player_scores)
    })

# Standings table
st.subheader("Current Standings")
if standings:
    df = pd.DataFrame(standings).sort_values("Top 3 Sum")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.warning("No standings yet — tournament may not have started.")

# Individual team cards
st.subheader("Team Details")
cols = st.columns(3)
for idx, (coach_id, info) in enumerate(teams_data.items()):
    with cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        st.markdown(f"### {team_name}")
        
        team_player_scores = []
        for player in players:
            score = player_scores.get(player)
            if score is not None:
                team_player_scores.append(f"{player} → **{score}**")
            else:
                team_player_scores.append(f"{player} → no data yet")
        
        st.write("\n".join(team_player_scores))
        
        # Top 3 sum for this team
        top_3_sum = sum([s for _, s in sorted([(p, player_scores.get(p)) for p in players if player_scores.get(p) is not None], key=lambda x: x[1])[:3]])
        st.metric("Top 3 Sum", top_3_sum)

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%I:%M %p')} • Scores auto-refresh every 10 minutes")
if st.button("🔄 Refresh Scores Now"):
    st.cache_data.clear()
    st.rerun()

# Debug option (remove after you're happy)
if st.checkbox("Show raw API data (for debugging)"):
    st.json(data)
