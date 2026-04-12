import streamlit as st
import requests
import pandas as pd
import json
import base64
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="2026 Masters Draft", layout="wide")
st.title("🏌️‍♂️ 2026 Masters Draft Dashboard")
st.subheader("Top 3 lowest scores per team wins • Live updates every 5 minutes")

# Auto-refresh every 5 minutes
st_autorefresh(interval=300000, limit=None, key="datarefresh")

# ====================== GITHUB CONFIG ======================
try:
    GITHUB_TOKEN = st.secrets["GITHUB"]["TOKEN"]
    REPO_OWNER = "theleitas"          # ← CHANGE TO YOUR USERNAME
    REPO_NAME = "masters-draft-2026"             # ← CHANGE IF DIFFERENT
    FILE_PATH = "teams.json"
    BRANCH = "main"
except Exception:
    st.error("GitHub token not configured. Please add it in Streamlit Secrets.")
    st.stop()

# Load teams from GitHub
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
    except:
        pass
    with open('teams.json') as f:
        return json.load(f)

teams_data = load_teams_from_github()

# Fetch live scores
@st.cache_data(ttl=300)
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
                            score = int(float(score_str)) if score_str is not None else None
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

# ====================== STANDINGS WITH TOP 3 COLUMN ======================
standings = []
for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    players = info.get("players", [])
    
    player_list = []
    for player in players:
        p_info = player_data.get(player)
        if p_info and p_info["score"] is not None:
            player_list.append((player, p_info["score"]))
    
    player_list.sort(key=lambda x: x[1])
    top_3 = player_list[:3]
    top_3_sum = sum(score for _, score in top_3)
    
    top_3_str = ", ".join([f"{name} ({score})" for name, score in top_3]) if top_3 else "—"
    
    standings.append({
        "Team": team_name,
        "Top 3 Golfers": top_3_str,
        "Top 3 Sum": top_3_sum
    })

st.subheader("Current Standings")
if standings:
    df_standings = pd.DataFrame(standings).sort_values("Top 3 Sum")
    
    # Phone-friendly styling with black text
    styled_standings = df_standings.style.set_properties(**{
        'text-align': 'left',
        'color': 'black'
    }).set_properties(subset=['Top 3 Sum'], **{
        'font-weight': 'bold',
        'font-size': '1.15em',
        'background-color': '#d4edda',
        'color': 'black'
    }).set_properties(subset=['Top 3 Golfers'], **{
        'white-space': 'normal',
        'word-break': 'break-word'
    }).format({
        "Top 3 Sum": "{:.0f}"   # Force integer, no decimals
    })
    
    st.dataframe(styled_standings, use_container_width=True, hide_index=True)

# ====================== TEAM DETAILS WITH YELLOW + BLACK TEXT ======================
st.subheader("Team Details (Top 3 highlighted)")

def highlight_top_3(row):
    if row.name < 3:
        return ['background-color: #fff566; color: black'] * len(row)
    return [''] * len(row)

cols = st.columns(3)

for idx, (coach_id, info) in enumerate(teams_data.items()):
    with cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        
        st.markdown(f"### {team_name}")
        
        table_data = []
        for player in players:
            p_info = player_data.get(player, {"score": None, "hole": "—"})
            score_display = int(p_info["score"]) if isinstance(p_info["score"], (int, float)) else "—"
            table_data.append({
                "Player": player,
                "Score": score_display,
                "Hole": p_info["hole"]
            })
        
        df_team = pd.DataFrame(table_data)
        
        df_team = df_team.sort_values(
            by="Score", 
            ascending=True, 
            na_position="last",
            key=lambda x: pd.to_numeric(x, errors='coerce')
        ).reset_index(drop=True)
        
        styled_df = df_team.style.apply(highlight_top_3, axis=1).format({
            "Score": "{:.0f}" if pd.api.types.is_numeric_dtype(df_team["Score"]) else "{}"
        })
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Top 3 sum (integer)
        numeric_scores = [s for s in df_team["Score"] if isinstance(s, (int, float))]
        numeric_scores.sort()
        top_3_sum = int(sum(numeric_scores[:3])) if numeric_scores else 0
        st.metric("Top 3 Sum", top_3_sum)

# ====================== EDIT & AUTO-SAVE ======================
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
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        resp = requests.get(url, headers=headers)
        sha = resp.json().get("sha") if resp.status_code == 200 else None

        content_str = json.dumps(new_teams, indent=2)
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Update teams via dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": content_b64,
            "branch": BRANCH
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(url, headers=headers, json=payload)
        
        if put_resp.status_code in [200, 201]:
            st.success("✅ Changes saved successfully! Dashboard updating for everyone...")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(f"Save failed: {put_resp.text}")
    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%I:%M %p')} • Auto-refresh every 5 minutes")
if st.button("🔄 Refresh Scores Now"):
    st.cache_data.clear()
    st.rerun()
