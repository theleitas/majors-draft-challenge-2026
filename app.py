import streamlit as st
import requests
import pandas as pd
import json
import base64
from datetime import datetime
import zoneinfo
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="PGA Championship Draft 2026", layout="wide", initial_sidebar_state="collapsed")

# Coach Colors
COACH_COLORS = {
    "Jayme Leita": "#00cc77",
    "Spencer Tidwell": "#bb77ff",
    "Peter Miller": "#2E47DB"
}

st.markdown("""
<style>
    .stApp { background-color: #0a0a0a; color: #e0e0e0; }
    h1 { font-size: 1.9rem !important; color: #00ff9d; }
    h2, h3 { font-size: 1.4rem !important; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

st.title("🏌️ PGA CHAMPIONSHIP DRAFT 2026")

est_tz = zoneinfo.ZoneInfo("America/New_York")
last_updated = datetime.now(est_tz).strftime("%I:%M %p EST")
st.caption(f"Live updates every 5 minutes • Last updated: {last_updated}")

# ====================== RULES ======================
with st.expander("📜 Rules", expanded=True):
    st.markdown("""
    **Rules**

    * Each player drafts 10 golfers
    * Snake draft format (Spencer → Jayme → Peter, then reverse)
    * Your TOP 3 lowest scores at the end of the tournament count
    * Winner takes 50 dollars from each other player ($100 total pot)
    """)

if st.button("🔄 Refresh Scores Now", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st_autorefresh(interval=300000, limit=None, key="datarefresh")

# ====================== GITHUB CONFIG ======================
try:
    GITHUB_TOKEN = st.secrets["GITHUB"]["TOKEN"]
    REPO_OWNER = "theleitas"
    REPO_NAME = "majors-draft-challenge-2026"
    FILE_PATH = "teams.json"
    BRANCH = "main"
except Exception:
    st.error("GitHub token not configured.")
    st.stop()

def save_teams_to_github(teams_dict):
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
        headers = {"Authorization": f"token {GITHUB_TOKEN}"}
        resp = requests.get(url, headers=headers)
        sha = resp.json().get("sha") if resp.status_code == 200 else None

        content_str = json.dumps(teams_dict, indent=2)
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Manual edit - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": content_b64,
            "branch": BRANCH
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(url, headers=headers, json=payload)
        return put_resp.status_code in [200, 201]
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

@st.cache_data(ttl=10)
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

def get_player_data(api_data):
    player_data = {}
    if not api_data:
        return player_data
    try:
        competitors = api_data.get("events", [{}])[0].get("competitions", [{}])[0].get("competitors", [])
        for comp in competitors:
            athlete = comp.get("athlete", {})
            name = athlete.get("displayName") or athlete.get("shortName")
            if not name: continue
            try:
                score = int(float(comp.get("score"))) if comp.get("score") is not None else None
            except:
                score = None
            linescores = comp.get("linescores", [])
            hole = "Not started"
            if linescores:
                current_round = linescores[-1]
                per_hole = current_round.get("linescores", [])
                played = sum(1 for h in per_hole if h.get("displayValue"))
                if played > 0:
                    hole = f"Thru {played}"
                elif current_round.get("displayValue") == "F":
                    hole = "Finished"
            rank = comp.get("rank") or comp.get("position") or "—"
            if isinstance(rank, (int, float)):
                rank = str(int(rank))
            player_data[name] = {"score": score, "hole": hole, "rank": rank}
    except:
        pass
    return player_data

player_data = get_player_data(data)

# ====================== STANDINGS (Clean HTML cards - no leaking) ======================
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

    color = COACH_COLORS.get(coach_id)

    # Single clean HTML block per card
    card = f"""
    <div style="border: 3px solid {color}; background-color: {color}15; border-radius: 14px; padding: 20px; margin-bottom: 1.5rem;">
        <strong style="color:{color}; font-size:1.45rem;">{team_name}</strong><br><br>
        <div style="display:flex; justify-content:space-between; align-items:start;">
            <div>
                <small style="color:#aaa;">TOTAL</small><br>
                <span style="color:{color}; font-size:2.3rem; font-weight:bold;">{top_3_sum}</span>
            </div>
            <div style="flex-grow:1; padding-left:50px;">
    """
    for name, score, hole in top_3:
        card += f"<strong>{name}</strong> <span style='color:{color}; font-weight:bold;'>({score})</span> — {hole}<br>"
    if not top_3:
        card += "Waiting for scores...<br>"
    card += "</div></div></div>"

    st.markdown(card, unsafe_allow_html=True)

# ====================== TOP 10 LEADERBOARD ======================
st.subheader("Top 10 Leaderboard")
if player_data:
    leaderboard = []
    for name, info in player_data.items():
        if info.get("score") is not None:
            owner_letter = "—"
            for cid, tinfo in teams_data.items():
                if name in tinfo.get("players", []):
                    owner_letter = "J" if cid == "Jayme Leita" else "S" if cid == "Spencer Tidwell" else "P"
                    break
            leaderboard.append({"Owner": owner_letter, "Player": name, "Score": info["score"], "Hole": info["hole"]})
    df_lb = pd.DataFrame(leaderboard).sort_values("Score").head(10).reset_index(drop=True)
    st.dataframe(df_lb, use_container_width=True, hide_index=True)

# ====================== TEAM ROSTERS ======================
st.subheader("Team Rosters")
team_cols = st.columns(3)
for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        st.markdown(f"**{team_name}**")
        if not players:
            st.caption("No golfers drafted yet")
        else:
            table_data = []
            for player in players:
                p_info = player_data.get(player, {"score": None, "hole": "—"})
                score_display = int(p_info["score"]) if isinstance(p_info.get("score"), (int, float)) else "N/A"
                table_data.append({"Player": player, "Score": score_display, "Hole": p_info["hole"]})
            df = pd.DataFrame(table_data)
            df = df.sort_values(by="Score", ascending=True, na_position="last", key=lambda x: pd.to_numeric(x, errors='coerce')).reset_index(drop=True)
            def style_top3(row):
                return ['background-color: #ffd700; color: #000000; font-weight: bold'] * len(row) if row.name < 3 else [''] * len(row)
            st.dataframe(df.style.apply(style_top3, axis=1), use_container_width=True, hide_index=True, height=210)

# ====================== EDIT TEAMS ======================
st.divider()
with st.expander("🔧 Edit Team Names & Rosters", expanded=False):
    new_teams = {}
    for coach_id, info in teams_data.items():
        st.markdown(f"**{coach_id}**")
        new_name = st.text_input("Team Name", value=info.get("team_name", coach_id), key=f"name_{coach_id}")
        players_str = "\n".join(info.get("players", []))
        new_players_str = st.text_area("Golfers (one per line)", value=players_str, key=f"players_{coach_id}", height=150)
        new_players = [p.strip() for p in new_players_str.split("\n") if p.strip()]
        new_teams[coach_id] = {"team_name": new_name, "players": new_players}
    
    if st.button("💾 Save All Changes to GitHub", type="primary"):
        if save_teams_to_github(new_teams):
            st.success("✅ Saved successfully!")
            st.cache_data.clear()
            st.rerun()

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} • Auto-refresh every 5 minutes")
