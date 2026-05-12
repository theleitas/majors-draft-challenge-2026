import streamlit as st
import requests
import json
import base64
import time
from datetime import datetime
import zoneinfo
from streamlit_autorefresh import st_autorefresh
import pandas as pd   # ← This was missing

st.set_page_config(page_title="PGA Championship Draft 2026", layout="wide", initial_sidebar_state="collapsed")

# ====================== GITHUB CONFIG ======================
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

# Full field
PGA_PLAYERS = sorted([
    "Ludvig Aberg", "Angel Ayora", "Derek Berg", "Daniel Berger", "Christiaan Bezuidenhout",
    "Akshay Bhatia", "Francisco Bide", "Chandler Blanchet", "Michael Block", "Keegan Bradley",
    "Michael Brennan", "Jacob Bridgeman", "Daniel Brown", "Sam Burns", "Brian Campbell",
    "Patrick Cantlay", "Ricky Castillo", "Bud Cauley", "Stewart Cink", "Wyndham Clark",
    "Tyler Collet", "Corey Conners", "Pierceson Coody", "Jason Day", "Bryson DeChambeau",
    "Thomas Detry", "Luke Donald", "Jesse Droemer", "Jason Dufner", "Nico Echavarria",
    "Harris English", "Bryce Fisher", "Steven Fisk", "Alex Fitzpatrick", "Matt Fitzpatrick",
    "Tommy Fleetwood", "Rickie Fowler", "Ryan Fox", "Chris Gabriele", "Mark Geddes",
    "Ryan Gerard", "Lucas Glover", "Chris Gotterup", "Max Greyserman", "Ben Griffin",
    "Emiliano Grillo", "Jordan Gumberg", "Harry Hall", "Brian Harman", "Padraig Harrington",
    "Tyrrell Hatton", "Zach Haynes", "Russell Henley", "Kazuki Higa", "Garrick Higgo",
    "Joe Highsmith", "Daniel Hillier", "Ryo Hisatsune", "Rico Hoey", "Ian Holt",
    "Max Homa", "Billy Horschel", "Viktor Hovland", "Austin Hurt", "Nicolai Højgaard",
    "Rasmus Højgaard", "Sungjae Im", "Stephan Jaeger", "Casey Jarvis", "Dustin Johnson",
    "Jared Jones", "Kota Kaneko", "Michael Kartrude", "Martin Kaymer", "John Keefer",
    "Ben Kern", "Michael Kim", "Si Woo Kim", "Chris Kirk", "Kurt Kitayama",
    "Jake Knapp", "Brooks Koepka", "Min Woo Lee", "Ryan Lenahan", "Haotong Li",
    "Mikael Lindberg", "David Lipsky", "Shane Lowry", "Robert MacIntyre", "Hideki Matsuyama",
    "Denny McCarthy", "Matt McCarty", "Paul McClure", "Max McGreevy", "Rory McIlroy",
    "Tom McKibbin", "Maverick McNealy", "Shaun Micheel", "Keith Mitchell", "Collin Morikawa",
    "William Mouw", "Rasmus Neergaard-Petersen", "Joaquin Niemann", "Alex Noren", "Andrew Novak",
    "John Parry", "Taylor Pendrith", "Marco Penge", "Ben Polland", "J.T. Poston",
    "Aldrich Potgieter", "David Puig", "Andrew Putnam", "Jon Rahm", "Aaron Rai",
    "Patrick Reed", "Kristoffer Reitan", "Davis Riley", "Patrick Rodgers", "Justin Rose",
    "Adrien Saddier", "Garrett Sapp", "Jayden Schaper", "Xander Schauffele", "Scottie Scheffler",
    "Adam Schenk", "Matti Schmid", "Adam Scott", "Braden Shattuck", "Alex Smalley",
    "Cameron Smith", "Jordan Smith", "Austin Smotherman", "Elvis Smylie", "Travis Smyth",
    "Brandt Snedeker", "J.J. Spaun", "Jordan Spieth", "Sam Stevens", "Sepp Straka",
    "Andy Sullivan", "Nick Taylor", "Sahith Theegala", "Justin Thomas", "Michael Thorbjornsen",
    "Sami Valimaki", "Jhonattan Vegas", "Ryan Vermeer", "Jimmy Walker", "Matt Wallace",
    "Bernd Wiesberger", "Timothy Wiseman", "Gary Woodland", "Y.E. Yang", "Sudarshan Yellamaraju",
    "Cameron Young"
])

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
    return {
        "Jayme Leita": {"team_name": "Jayme's Team", "players": []},
        "Spencer Tidwell": {"team_name": "Spencer's Team", "players": []},
        "Peter Miller": {"team_name": "Peter's Team", "players": []}
    }

def save_teams_to_github(teams_dict):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers)
        sha = resp.json().get("sha") if resp.status_code == 200 else None

        content_str = json.dumps(teams_dict, indent=2)
        content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

        payload = {
            "message": f"Update - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
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

def get_coach_for_pick(pick_num, order):
    round_idx = (pick_num - 1) // 3
    pos = (pick_num - 1) % 3
    if round_idx % 2 == 0:
        return order[pos]
    else:
        return order[2 - pos]

# Initialize session state
if "draft_active" not in st.session_state:
    st.session_state.draft_active = False
    st.session_state.draft_paused = False
    st.session_state.enable_draft = False
    st.session_state.current_pick = 1
    st.session_state.picks = []
    st.session_state.picked_golfers = set()
    st.session_state.draft_order = ["Jayme Leita", "Spencer Tidwell", "Peter Miller"]
    st.session_state.last_pick_time = time.time()

teams_data = load_teams_from_github()

if st.session_state.draft_active and not st.session_state.draft_paused:
    st_autorefresh(interval=3000, limit=None, key="draft_timer")

# ====================== TITLE ======================
st.title("🏌️ PGA Championship 2026")
st.caption("**May 14–17, 2026** • Aronimink Golf Club")

# ====================== STANDINGS ======================
st.subheader("Standings")
for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    color = COACH_COLORS.get(coach_id, "#555555")
    players = info.get("players", [])
    
    top3_html = ""
    if players:
        for p in players[:3]:
            top3_html += f"<div style='margin:4px 0; color:{color}; font-size:1.05rem;'>{p} <span style='font-weight:700;'>(-XX)</span> Thru XX</div>"
    else:
        top3_html = "<div style='color:#888; font-style:italic;'>No golfers drafted yet</div>"
    
    card = f"""
    <div style="border: 5px solid {color}; background-color: {color}18; border-radius: 24px; padding: 20px 24px; margin-bottom: 1.8rem; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <div style="color:{color}; font-size:1.75rem; font-weight:800;">{team_name}</div>
        <div style="font-size:1.45rem; font-weight:700; color:{color}; margin:12px 0 14px 0;">Total (-XX)</div>
        <div style="line-height:1.5;">{top3_html}</div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)

# ====================== TEAM ROSTERS ======================
st.subheader("Team Rosters")
team_cols = st.columns(3)
for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        color = COACH_COLORS.get(coach_id, "#555555")

        roster_card = f"""
        <div style="border: 5px solid {color}; background-color: {color}18; border-radius: 24px; padding: 20px 24px; margin-bottom: 1.8rem;">
            <div style="color:{color}; font-size:1.75rem; font-weight:800; margin-bottom:12px;">{team_name}</div>
        """
        st.markdown(roster_card, unsafe_allow_html=True)

        if not players:
            st.caption("No golfers drafted yet")
        else:
            table_data = [{"Golfer": p, "Score": "N/A", "Hole": "—"} for p in players]
            df = pd.DataFrame(table_data)
            def highlight_top3(row):
                if row.name < 3:
                    return ['background-color: #ffeb3b; color: #000000; font-weight: bold'] * len(row)
                return [''] * len(row)
            styled = df.style.apply(highlight_top3, axis=1)
            st.dataframe(styled, use_container_width=True, hide_index=True, height=380)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ====================== DRAFT SECTION ======================
with st.expander("🎯 DRAFT SECTION", expanded=st.session_state.get("enable_draft", False)):
    if not st.session_state.get("enable_draft", False):
        st.error("🚫 Draft is currently DISABLED in Admin section")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("▶️ Start Draft", type="primary", disabled=st.session_state.get("draft_active", False), use_container_width=True):
                st.session_state.draft_active = True
                st.session_state.draft_paused = False
                st.rerun()
        with col2:
            if st.button("⏸️ Pause Draft", disabled=not st.session_state.get("draft_active", False), use_container_width=True):
                st.session_state.draft_paused = True
                st.rerun()

        if st.session_state.get("draft_active", False):
            current_coach = get_coach_for_pick(st.session_state.get("current_pick", 1), st.session_state.get("draft_order", ["Jayme Leita", "Spencer Tidwell", "Peter Miller"]))
            st.markdown(f"## 🔥 CURRENT PICK: **{current_coach}** — Pick #{st.session_state.get('current_pick', 1)}")
            if st.session_state.get("draft_paused", False):
                st.warning("⏸️ Draft is PAUSED")

        st.subheader("Draft Dashboard")
        grid_html = """
        <style>
        @keyframes flash { 0% { background-color: #ffeb3b; } 50% { background-color: #fff59d; } 100% { background-color: #ffeb3b; } }
        .draft-table { width: 100%; border-collapse: collapse; font-size: 0.95rem; }
        .draft-table th, .draft-table td { border: 1px solid #444; padding: 10px; text-align: center; }
        .draft-table th { background-color: #1f1f1f; color: #fff; }
        .current-cell { animation: flash 1.2s infinite; font-weight: bold; }
        </style>
        <table class="draft-table">
        <tr><th>Round</th>
        """
        for p in st.session_state.get("draft_order", ["Jayme Leita", "Spencer Tidwell", "Peter Miller"]):
            grid_html += f"<th>{p}</th>"
        grid_html += "</tr>"

        for r in range(10):
            grid_html += f"<tr><td><b>Round {r+1}</b></td>"
            for c in range(3):
                if r % 2 == 0:
                    pick_num = r * 3 + c + 1
                else:
                    pick_num = r * 3 + (2 - c) + 1
                picked_golfer = next((pk[2] for pk in st.session_state.get("picks", []) if pk[0] == pick_num), None)
                is_current = (pick_num == st.session_state.get("current_pick", 1) and st.session_state.get("draft_active", False) and not st.session_state.get("draft_paused", False))
                if picked_golfer:
                    cell = picked_golfer
                    cell_style = ""
                elif is_current:
                    elapsed = int(time.time() - st.session_state.get("last_pick_time", time.time()))
                    cell = f"⏱️ {elapsed}s<br>Pick {pick_num}"
                    cell_style = "class='current-cell' style='background-color:#ffeb3b; color:#000;'"
                else:
                    cell = f"Pick {pick_num}"
                    cell_style = ""
                grid_html += f"<td {cell_style}>{cell}</td>"
            grid_html += "</tr>"
        grid_html += "</table>"
        st.markdown(grid_html, unsafe_allow_html=True)

        st.subheader("Available Golfers — Click to Draft")
        sorted_players = sorted(PGA_PLAYERS, key=lambda x: int(VEGAS_ODDS.get(x, "999999").replace("+", "")))
        available = [p for p in sorted_players if p not in st.session_state.get("picked_golfers", set())]

        num_cols = 4
        cols = st.columns(num_cols)
        for idx, golfer in enumerate(available):
            col_idx = idx % num_cols
            with cols[col_idx]:
                odds = VEGAS_ODDS.get(golfer, "(N/A)")
                disabled = not (st.session_state.get("draft_active", False) and not st.session_state.get("draft_paused", False) and st.session_state.get("enable_draft", False))
                if st.button(f"✅ {golfer} {odds}", key=f"pick_{golfer}", disabled=disabled, use_container_width=True):
                    coach = get_coach_for_pick(st.session_state.get("current_pick", 1), st.session_state.get("draft_order", ["Jayme Leita", "Spencer Tidwell", "Peter Miller"]))
                    if golfer not in teams_data[coach]["players"]:
                        teams_data[coach]["players"].append(golfer)
                        save_teams_to_github(teams_data)
                    st.session_state.setdefault("picks", []).append((st.session_state.get("current_pick", 1), coach, golfer))
                    st.session_state.setdefault("picked_golfers", set()).add(golfer)
                    st.session_state["current_pick"] = st.session_state.get("current_pick", 1) + 1
                    st.session_state["last_pick_time"] = time.time()
                    if st.session_state["current_pick"] > 30:
                        st.session_state.draft_active = False
                        st.success("🎉 Draft Complete!")
                    st.rerun()

# ====================== ADMIN SECTION ======================
with st.expander("🔧 Admin Section", expanded=False):
    st.subheader("Draft Control")
    enable = st.toggle("Enable Draft", value=st.session_state.get("enable_draft", False), key="enable_toggle")
    if enable != st.session_state.get("enable_draft", False):
        st.session_state.enable_draft = enable
        st.rerun()

    if st.session_state.get("enable_draft", False):
        if st.button("🛑 Reset Draft & Clear Roster", type="secondary", use_container_width=True):
            if st.checkbox("⚠️ Confirm: Delete ALL rosters?"):
                for c in teams_data:
                    teams_data[c]["players"] = []
                save_teams_to_github(teams_data)
                st.session_state.setdefault("picks", [])
                st.session_state.setdefault("picked_golfers", set()).clear()
                st.session_state.current_pick = 1
                st.session_state.draft_active = False
                st.success("All rosters cleared!")
                st.rerun()

    st.subheader("Edit Team Names")
    new_teams = {}
    for coach_id, info in teams_data.items():
        st.markdown(f"### {coach_id}")
        new_name = st.text_input("Team Name", value=info.get("team_name", coach_id), key=f"name_{coach_id}")
        new_teams[coach_id] = {"team_name": new_name, "players": info.get("players", [])}

    if st.button("💾 Save Team Names"):
        save_teams_to_github(new_teams)
        st.success("Team names saved!")
        st.rerun()

st.caption("PGA Championship Draft 2026 • Built with Streamlit • Data saved to GitHub")
