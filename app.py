import streamlit as st
import requests
import pandas as pd
import json
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="2026 Masters Draft", layout="wide")
st.title("🏌️‍♂️ 2026 Masters Draft Dashboard")
st.subheader("Top 3 lowest scores per team wins • Live every 10 minutes")

# Auto-refresh every 10 minutes
st_autorefresh(interval=600000, limit=None, key="datarefresh")

# Load GitHub config from secrets
try:
    GITHUB_TOKEN = st.secrets["GITHUB"]["TOKEN"]
    REPO_OWNER = "theleitas"          # ← CHANGE THIS
    REPO_NAME = "masters-draft-2026"             # ← CHANGE THIS if different
    FILE_PATH = "teams.json"
    BRANCH = "main"                              # usually "main" or "master"
except Exception:
    st.error("GitHub token not found. Please add it in Streamlit Secrets as shown in instructions.")
    st.stop()

# Load current teams from GitHub (so we always have the latest)
@st.cache_data(ttl=60)
def load_teams_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            content = resp.json()["content"]
            decoded = base64.b64decode(content).decode("utf-8")
            return json.loads(decoded)
        else:
            st.warning("Could not load teams from GitHub. Using fallback.")
            with open('teams.json') as f:
                return json.load(f)
    except:
        st.warning("Fallback to local teams.json")
        with open('teams.json') as f:
            return json.load(f)

teams_data = load_teams_from_github()

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
                        score_str = competitor.get("score")
                        try:
                            score = float(score_str) if score_str is not None else None
                        except:
                            score = None

                        status = competitor.get("status", {})
                        hole_raw = status.get("thru") or status.get("period") or status.get("type", {}).get("shortDetail")
                        if isinstance(hole_raw, (int, float)) or (isinstance(hole_raw, str) and hole_raw.replace(".", "").replace("-", "").isdigit()):
                            hole = f"Thru {hole_raw}"
                        elif str(hole_raw).upper() in ["F", "FINISHED"]:
                            hole = "Finished"
                        else:
                            hole = str(hole_raw) if hole_raw else "Not started"
                        
                        player_data[name] = {"score": score, "hole": hole}
    except:
        pass
    return player_data

player_data = get_player_data(data)

# Calculate standings
standings = []
for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    players = info.get("players", [])
    scores_list = [p.get("score") for p in [player_data.get(p) for p in players] if p and p["score"] is not None]
    scores_list.sort()
    top_3_sum = sum(scores_list[:3]) if scores_list else 0
    standings.append({"Team": team_name, "Top 3 Sum": top_3_sum})

st.subheader("Current Standings")
if standings:
    df_standings = pd.DataFrame(standings).sort_values("Top 3 Sum")
    st.dataframe(df_standings, use_container_width=True, hide_index=True)

# Team Details
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
        df_team = df_team.sort_values(by="Score", ascending=True, na_position="last",
                                      key=lambda x: pd.to_numeric(x, errors='coerce'))
        st.dataframe(df_team, use_container_width=True, hide_index=True)
        
        numeric_scores = [s for s in df_team["Score"] if isinstance(s, (int, float))]
        numeric_scores.sort()
        st.metric("Top 3 Sum", sum(numeric_scores[:3]) if numeric_scores else 0)

# ====================== REAL-TIME EDIT & AUTO-SAVE ======================
st.divider()
st.subheader("🔧 Edit Teams & Auto-Save to GitHub")

new_teams = {}
for coach_id, info in teams_data.items():
    st.subheader(coach_id)
    new_team_name = st.text_input(f"Team Name", value=info.get("team_name", coach_id), key=f"name_{coach_id}")
    players_str = "\n".join(info.get("players", []))
    new_players_str = st.text_area(f"Players (one per line)", value=players_str, key=f"players_{coach_id}", height=150)
    new_players = [p.strip() for p in new_players_str.split("\n") if p.strip()]
    
    new_teams[coach_id] = {"team_name": new_team_name, "players": new_players}

if st.button("💾 Save Changes to GitHub", type="primary"):
    if not GITHUB_TOKEN or REPO_OWNER == "YOUR_GITHUB_USERNAME":
        st.error("Please update REPO_OWNER in the code and add your GitHub token in Secrets.")
    else:
        try:
            # Get current file SHA
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            resp = requests.get(url, headers=headers)
            
            if resp.status_code == 200:
                sha = resp.json()["sha"]
            else:
                sha = None

            # Prepare new content
            content_str = json.dumps(new_teams, indent=2)
            content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

            payload = {
                "message": f"Update teams.json via dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "content": content_b64,
                "branch": BRANCH
            }
            if sha:
                payload["sha"] = sha

            # Push update
            put_resp = requests.put(url, headers=headers, json=payload)
            
            if put_resp.status_code in [200, 201]:
                st.success("✅ Changes saved to GitHub successfully! The dashboard will update for everyone in a few seconds.")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"Failed to save: {put_resp.status_code} - {put_resp.text}")
        except Exception as e:
            st.error(f"Error saving to GitHub: {e}")

st.info("Changes are saved directly to your GitHub repo. Everyone with the link will see the updates shortly after saving.")

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%I:%M %p')} • Auto-refresh every 10 minutes")
if st.button("🔄 Refresh Scores Now"):
    st.cache_data.clear()
    st.rerun()
