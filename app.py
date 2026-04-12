import streamlit as st
import requests
import pandas as pd
import json
import base64
from datetime import datetime
import zoneinfo
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Masters Draft 2026", layout="wide", initial_sidebar_state="collapsed")

# ====================== HIGH-CONTRAST DARK THEME ======================
st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #e0e0e0; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1 { font-size: 1.85rem !important; color: #00ff9d; margin-bottom: 0.3rem; }
    h2, h3 { font-size: 1.35rem !important; color: #ffffff; margin: 0.8rem 0 0.4rem 0; }

    .stMarkdown p strong, .stMarkdown p b { font-size: 1.75rem !important; color: #ffffff; font-weight: 700; }
    .stMarkdown p { font-size: 1.05rem !important; margin-bottom: 0.05rem; }
    .stMarkdown p strong { font-size: 1.05rem !important; color: #00ff9d; font-weight: 700; }

    .stContainer { border: 2px solid #ffffff !important; border-radius: 10px; background-color: #111111; padding: 14px; }

    .stMetric { background-color: #1f2a1f; border: 1px solid #00cc77; border-radius: 8px; padding: 10px 14px; }
    .stMetric label { color: #88ffbb; font-size: 0.85rem; }
    .stMetric div[data-testid="stMetricValue"] { color: #00ff9d !important; font-size: 1.65rem !important; font-weight: bold; }

    .stDataFrame { font-size: 0.84rem; background-color: #111; }

    .highlight-top3 { background-color: #ffd700 !important; color: #000000 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🏌️ MASTERS DRAFT 2026")

est_tz = zoneinfo.ZoneInfo("America/New_York")
last_updated = datetime.now(est_tz).strftime("%I:%M %p EST")
st.caption(f"Top 3 lowest scores wins • Live updates every 5 minutes • Last updated: {last_updated}")

if st.button("🔄 Refresh Scores Now", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st_autorefresh(interval=300000, limit=None, key="datarefresh")

# ====================== GITHUB CONFIG ======================
try:
    GITHUB_TOKEN = st.secrets["GITHUB"]["TOKEN"]
    REPO_OWNER = "YOUR_GITHUB_USERNAME"          # ← CHANGE TO YOUR USERNAME
    REPO_NAME = "masters-draft-2026"
    FILE_PATH = "teams.json"
    BRANCH = "main"
except Exception:
    st.error("GitHub token not configured.")
    st.stop()

# Load teams
@st.cache_data(ttl=60)
def load_teams_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            content = resp.json()["content"]
            return json.loads(base64.b64decode(content).decode("utf-8"))
    except:
        pass
    with open('teams.json') as f:
        return json.load(f)

teams_data = load_teams_from_github()

# Fetch live scores
@st.cache_data(ttl=300)
def fetch_leaderboard():
    try:
        resp = requests.get("https://site.api.espn.com/apis/site/v2/sports/golf/pga/scoreboard", timeout=15)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

data = fetch_leaderboard()

# ====================== FIXED HOLE PARSER (using linescores) ======================
def get_player_data(api_data):
    player_data = {}
    if not api_data:
        return player_data

    try:
        competitors = api_data.get("events", [{}])[0].get("competitions", [{}])[0].get("competitors", [])

        for comp in competitors:
            athlete = comp.get("athlete", {})
            name = athlete.get("displayName") or athlete.get("shortName")
            if not name:
                continue

            # Score to par
            try:
                score = int(float(comp.get("score"))) if comp.get("score") is not None else None
            except:
                score = None

            # === BETTER HOLE DETECTION USING LINESCORES ===
            linescores = comp.get("linescores", [])
            current_hole = None

            # Find the current round (last round with data)
            for ls in reversed(linescores):
                if ls.get("linescores"):   # has per-hole data
                    hole_list = ls.get("linescores", [])
                    # Count how many holes have been played
                    played_holes = sum(1 for h in hole_list if h.get("displayValue") is not None)
                    if played_holes > 0:
                        current_hole = played_holes
                        break

            # Format hole
            if current_hole:
                hole = f"Thru {current_hole}"
            elif comp.get("status", {}).get("type", {}).get("shortDetail") == "F":
                hole = "Finished"
            else:
                hole = "Not started"

            # Position
            rank = comp.get("rank") or comp.get("position") or "—"
            if isinstance(rank, (int, float)):
                rank = str(int(rank))

            player_data[name] = {
                "score": score,
                "hole": hole,
                "rank": rank
            }
    except Exception as e:
        st.warning(f"Parsing error: {e}")

    return player_data

player_data = get_player_data(data)

# ====================== STANDINGS ======================
st.subheader("Standings")

for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    players = info.get("players", [])
    
    player_list = []
    for p in players:
        pd_info = player_data.get(p, {})
        if pd_info.get("score") is not None:
            player_list.append((p, pd_info["score"], pd_info.get("hole", "—")))
    
    player_list.sort(key=lambda x: x[1])
    top_3 = player_list[:3]
    top_3_sum = sum(s for _, s, _ in top_3)

    with st.container(border=True):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"**{team_name}**")
        with c2:
            st.metric("TOTAL", top_3_sum)
        
        st.markdown("**Top 3 Golfers**")
        if top_3:
            for name, score, hole in top_3:
                st.markdown(f"  {name} **({score})** — {hole}")
        else:
            st.caption("Waiting for scores...")

# ====================== $50 SIDE BET ======================
st.subheader("$50 Leita/Tidwell Side Bet - Burns to Win")

burns = player_data.get("Sam Burns", {})
with st.container(border=True):
    col1, col2, col3 = st.columns([2.5, 1, 1])
    with col1:
        st.markdown("**Sam Burns**")
    with col2:
        st.metric("Score", f"{burns.get('score')}" if burns.get("score") is not None else "—")
    with col3:
        st.metric("Position", burns.get("rank", "—"))
    st.markdown(f"**Current Hole:** {burns.get('hole', '—')}")

# ====================== TEAM ROSTERS ======================
st.subheader("Team Rosters")

team_cols = st.columns(3)
for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        
        st.markdown(f"**{team_name}**")
        
        table_data = []
        for player in players:
            p_info = player_data.get(player, {"score": None, "hole": "—"})
            score_display = int(p_info["score"]) if isinstance(p_info.get("score"), (int, float)) else "—"
            table_data.append({
                "Player": player,
                "Score": score_display,
                "Hole": p_info["hole"]
            })
        
        df = pd.DataFrame(table_data)
        df = df.sort_values(by="Score", ascending=True, na_position="last",
                            key=lambda x: pd.to_numeric(x, errors='coerce')).reset_index(drop=True)
        
        def style_top3(row):
            return ['background-color: #ffd700; color: #000000; font-weight: bold'] * len(row) if row.name < 3 else [''] * len(row)
        
        st.dataframe(df.style.apply(style_top3, axis=1), use_container_width=True, hide_index=True, height=210)

# ====================== DEBUG SECTION ======================
st.divider()
with st.expander("🔍 DEBUG: Gary Woodland Raw Data", expanded=True):
    if data:
        competitors = data.get("events", [{}])[0].get("competitions", [{}])[0].get("competitors", [])
        woodland_raw = next((c for c in competitors if "Woodland" in str(c.get("athlete", {}).get("displayName", ""))), None)
        if woodland_raw:
            st.json(woodland_raw)
        else:
            st.write("Gary Woodland not found in raw data")
    else:
        st.write("No API data received")

# ====================== EDIT SECTION ======================
st.divider()
with st.expander("🔧 Edit Teams & Auto-Save to GitHub", expanded=False):
    new_teams = {}
    for coach_id, info in teams_data.items():
        st.markdown(f"**{coach_id}**")
        new_name = st.text_input("Team Name", value=info.get("team_name", coach_id), key=f"name_{coach_id}")
        players_str = "\n".join(info.get("players", []))
        new_players_str = st.text_area("Players (one per line)", value=players_str, key=f"players_{coach_id}", height=110)
        new_players = [p.strip() for p in new_players_str.split("\n") if p.strip()]
        new_teams[coach_id] = {"team_name": new_name, "players": new_players}
    
    if st.button("💾 Save Changes to GitHub", type="primary"):
        try:
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            resp = requests.get(url, headers=headers)
            sha = resp.json().get("sha") if resp.status_code == 200 else None

            content_str = json.dumps(new_teams, indent=2)
            content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

            payload = {
                "message": f"Dashboard update - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                "content": content_b64,
                "branch": BRANCH
            }
            if sha:
                payload["sha"] = sha

            put_resp = requests.put(url, headers=headers, json=payload)
            if put_resp.status_code in [200, 201]:
                st.success("✅ Changes saved successfully!")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("Failed to save to GitHub")
        except Exception as e:
            st.error(f"Error: {e}")

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} • Auto-refresh every 5 minutes")
