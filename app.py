import streamlit as st
import json
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

# Expanded 2026 PGA Championship betting odds (favorites first)
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
    # ... many more with N/A below
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

# Initialize session state - DRAFT DISABLED BY DEFAULT
if "draft_active" not in st.session_state:
    st.session_state.draft_active = False
    st.session_state.draft_paused = False
    st.session_state.draft_locked = False
    st.session_state.enable_draft = False   # ← Default is OFF
    st.session_state.current_pick = 1
    st.session_state.picks = []
    st.session_state.picked_golfers = set()
    st.session_state.draft_order = ["Jayme Leita", "Spencer Tidwell", "Peter Miller"]
    st.session_state.last_pick_time = time.time()

teams_data = load_teams()

if st.session_state.draft_active and not st.session_state.draft_paused:
    st_autorefresh(interval=3000, limit=None, key="draft_timer")

# ====================== STANDINGS (Clean cards like your image) ======================
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

# ====================== TEAM ROSTERS (Same colored card style) ======================
st.subheader("Team Rosters")
team_cols = st.columns(3)
for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        color = COACH_COLORS.get(coach_id, "#555555")

        # Big colored card for the entire roster
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
                return ['background-color: #ffeb3b; font-weight: bold'] * len(row) if row.name < 3 else [''] * len(row)
            styled = df.style.apply(highlight_top3, axis=1)
            st.dataframe(styled, use_container_width=True, hide_index=True, height=380)  # Tall enough for 10 golfers

        st.markdown('</div>', unsafe_allow_html=True)

# ====================== DRAFT SECTION ======================
with st.expander("🎯 DRAFT SECTION", expanded=True):
    if not st.session_state.enable_draft:
        st.error("🚫 Draft is currently **DISABLED** in Admin section")
    
    col1, col2, col3, col4 = st.columns([1.2, 1.2, 1.2, 2])
    with col1:
        if st.button("▶️ Start Draft", type="primary", disabled=not st.session_state.enable_draft or st.session_state.draft_active or st.session_state.draft_locked):
            st.session_state.draft_active = True
            st.session_state.draft_paused = False
            st.rerun()
    with col2:
        if st.button("⏸️ Pause Draft", disabled=not st.session_state.draft_active):
            st.session_state.draft_paused = True
            st.rerun()
    with col3:
        if st.button("✅ Complete Draft", disabled=not st.session_state.draft_active):
            st.session_state.draft_active = False
            st.session_state.draft_locked = True
            st.success("Draft completed and locked!")
            st.rerun()
    with col4:
        if st.button("🔒 Lock in Draft Picks", type="secondary"):
            st.session_state.draft_locked = True
            st.success("Rosters are now locked!")
            st.rerun()

    # ... (draft dashboard and available golfers with odds code continues exactly as before)

# ====================== ADMIN SECTION ======================
with st.expander("🔧 Admin Section", expanded=False):
    st.subheader("Draft Control")
    enable = st.toggle("Enable Draft", value=st.session_state.enable_draft, key="enable_toggle")
    if enable != st.session_state.enable_draft:
        st.session_state.enable_draft = enable
        st.rerun()
    
    st.subheader("Edit Team Names")
    new_teams = {}
    for coach_id, info in teams_data.items():
        st.markdown(f"### {coach_id}")
        new_name = st.text_input("Team Name", value=info.get("team_name", coach_id), key=f"name_{coach_id}")
        new_teams[coach_id] = {"team_name": new_name, "players": info.get("players", [])}

    if st.button("💾 Save Team Names"):
        save_teams(new_teams)
        st.success("Team names saved!")
        st.rerun()

    st.divider()
    st.subheader("Draft Order Setup")
    coaches = list(teams_data.keys())
    p1 = st.selectbox("Player 1 (starts Round 1)", coaches, index=0, key="admin_p1")
    rem = [c for c in coaches if c != p1]
    p2 = st.selectbox("Player 2", rem, index=0, key="admin_p2")
    p3 = [c for c in rem if c != p2][0]
    st.write(f"**Player 3 will be:** {p3}")
    if st.button("Set This Draft Order"):
        st.session_state.draft_order = [p1, p2, p3]
        st.success(f"Draft order set: {p1} → {p2} → {p3} (snake)")
        st.rerun()

st.caption("PGA Championship Draft 2026 • Built with Streamlit • Data auto-saves to teams.json")
