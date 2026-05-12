import streamlit as st
import json
import os
import time
import pandas as pd
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="PGA Championship Draft 2026", layout="wide", initial_sidebar_state="collapsed")

# Coach Colors
COACH_COLORS = {
    "Jayme Leita": "#00cc77",
    "Spencer Tidwell": "#bb77ff",
    "Peter Miller": "#2E47DB"
}

# Full 2026 PGA Championship Field (cleaned list)
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

def load_teams():
    with open("teams.json", "r") as f:
        return json.load(f)

def save_teams(data):
    with open("teams.json", "w") as f:
        json.dump(data, f, indent=2)

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
    st.session_state.current_pick = 1
    st.session_state.picks = []
    st.session_state.picked_golfers = set()
    st.session_state.draft_order = ["Jayme Leita", "Spencer Tidwell", "Peter Miller"]
    st.session_state.last_pick_time = time.time()

teams_data = load_teams()

# Auto-refresh when draft is active (for timer)
if st.session_state.draft_active and not st.session_state.draft_paused:
    st_autorefresh(interval=3000, limit=None, key="draft_timer")

# ====================== STANDINGS ======================
st.subheader("Standings")
for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    color = COACH_COLORS.get(coach_id, "#555555")
    box_style = f"border: 3px solid {color}; background-color: {color}15; border-radius: 14px; padding: 20px; margin-bottom: 1.5rem;"
    st.markdown(f'<div style="{box_style}">', unsafe_allow_html=True)
    st.markdown(f"<span style='color:{color}; font-size:1.45rem; font-weight:bold;'>{team_name}</span>", unsafe_allow_html=True)
    st.caption("TOTAL: — (live scores during tournament)")
    st.markdown('</div>', unsafe_allow_html=True)

# ====================== TOP 10 LEADERBOARD (placeholder) ======================
st.subheader("Top 10 Leaderboard")
st.caption("Live leaderboard will appear here during the tournament.")

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
            for p in players:
                st.write(f"• {p}")
            st.caption(f"Total: {len(players)} golfers")

# ====================== DRAFT SECTION ======================
with st.expander("🎯 DRAFT SECTION", expanded=True):
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        start_disabled = st.session_state.draft_active and not st.session_state.draft_paused
        if st.button("▶️ Start Draft", type="primary", disabled=start_disabled, use_container_width=True):
            st.session_state.draft_active = True
            st.session_state.draft_paused = False
            if st.session_state.current_pick == 1:
                st.session_state.picks = []
                st.session_state.picked_golfers = set()
            st.session_state.last_pick_time = time.time()
            st.rerun()
    with col2:
        pause_disabled = not st.session_state.draft_active or st.session_state.draft_paused
        if st.button("⏸️ Pause Draft", disabled=pause_disabled, use_container_width=True):
            st.session_state.draft_paused = True
            st.rerun()
    with col3:
        complete_disabled = not st.session_state.draft_active
        if st.button("✅ Complete Draft", disabled=complete_disabled, use_container_width=True):
            st.session_state.draft_active = False
            st.session_state.draft_paused = False
            st.success("Draft marked as complete!")
            st.rerun()

    # Current pick header
    if st.session_state.draft_active:
        current_coach = get_coach_for_pick(st.session_state.current_pick, st.session_state.draft_order)
        st.markdown(f"## 🔥 CURRENT PICK: **{current_coach}** — Pick #{st.session_state.current_pick}")
        if st.session_state.draft_paused:
            st.warning("⏸️ Draft is PAUSED")
    else:
        st.info("Draft is not active. Click Start Draft to begin.")

    # Draft Dashboard (HTML table with flashing current cell)
    st.subheader("Draft Dashboard")

    # Build grid
    grid_html = """
    <style>
    @keyframes flash {
        0% { background-color: #ffeb3b; }
        50% { background-color: #fff59d; }
        100% { background-color: #ffeb3b; }
    }
    .draft-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    .draft-table th, .draft-table td { border: 1px solid #444; padding: 8px; text-align: center; }
    .draft-table th { background-color: #1f1f1f; color: #fff; }
    .current-cell { animation: flash 1.2s infinite; font-weight: bold; }
    </style>
    <table class="draft-table">
    <tr>
        <th>Round</th>
    """
    for p in st.session_state.draft_order:
        grid_html += f"<th>{
