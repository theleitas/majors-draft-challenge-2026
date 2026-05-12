import streamlit as st
import requests
import json
import base64
from datetime import datetime
import zoneinfo
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="PGA Championship Draft 2026", layout="wide", initial_sidebar_state="collapsed")

# ====================== CONFIG ======================
GITHUB_TOKEN = st.secrets["GITHUB"]["TOKEN"]
REPO_OWNER = "theleitas"
REPO_NAME = "majors-draft-challenge-2026"
FILE_PATH = "teams.json"
BRANCH = "main"

# Coach Colors
COACH_COLORS = {
    "Jayme Leita": "#00cc77",
    "Spencer Tidwell": "#bb77ff",
    "Peter Miller": "#2E47DB"
}

# Expanded Vegas odds
VEGAS_ODDS = {
    "Scottie Scheffler": "+450", "Rory McIlroy": "+800", "Xander Schauffele": "+1400",
    "Jon Rahm": "+1600", "Bryson DeChambeau": "+1800", "Ludvig Aberg": "+2200",
    "Cameron Young": "+2500", "Matt Fitzpatrick": "+2800", "Tommy Fleetwood": "+3000",
    "Justin Thomas": "+3500", "Brooks Koepka": "+4000", "Viktor Hovland": "+4500",
    "Hideki Matsuyama": "+5000", "Collin Morikawa": "+5500", "Patrick Cantlay": "+6000",
    "Jordan Spieth": "+6500", "Russell Henley": "+7000", "Sahith Theegala": "+7500",
    "Min Woo Lee": "+8000", "Shane Lowry": "+9000", "Tyrrell Hatton": "+10000",
    "Corey Conners": "+11000", "Adam Scott": "+12000", "Sepp Straka": "+14000",
    "Sungjae Im": "+15000", "J.T. Poston": "+18000", "Alex Smalley": "+20000",
    "Sam Burns": "+22000", "Jason Day": "+25000", "Rickie Fowler": "+28000",
    "Max Homa": "+30000", "Tony Finau": "+35000", "Justin Rose": "+40000",
}

PGA_PLAYERS = sorted([ ... ])  # (same full list as before - omitted for brevity)

# ====================== GITHUB PERSISTENCE ======================
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
    # Default teams if file doesn't exist yet
    default_teams = {
        "Jayme Leita": {"team_name": "Jayme's Team", "players": []},
        "Spencer Tidwell": {"team_name": "Spencer's Team", "players": []},
        "Peter Miller": {"team_name": "Peter's Team", "players": []}
    }
    return default_teams

def save_teams_to_github(teams_dict):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        # Get current SHA
        resp = requests.get(url, headers=headers)
        sha = resp.json().get("sha") if resp.status_code == 200 else None

        content_str = json.dumps(teams_dict, indent=2)
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Update teams - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": content_b64,
            "branch": BRANCH
        }
        if sha:
            payload["sha"] = sha

        put_resp = requests.put(url, headers=headers, json=payload)
        return put_resp.status_code in [200, 201]
    except Exception as e:
        st.error(f"GitHub save failed: {e}")
        return False

teams_data = load_teams_from_github()

# ====================== REST OF THE APP (same clean UI) ======================
# ... (the full standings, rosters, draft section, and admin section from the previous clean version)

st.title("🏌️ PGA Championship 2026")
st.caption("**May 14–17, 2026** • Aronimink Golf Club")

# Standings, Rosters, Draft Section, Admin Section (with the exact formatting you liked)

# (The rest of the code is identical to the last clean version I gave you, but now using GitHub persistence)

st.caption("PGA Championship Draft 2026 • Data saved to GitHub")
