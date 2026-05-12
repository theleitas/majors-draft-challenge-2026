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
    players = info.get("players", [])
    
    # Build top 3 lines
    if players:
        top3_html = ""
        for p in players[:3]:
            top3_html += f"<div style='margin:3px 0; color:{color}; font-size:1.05rem;'>{p} <span style='font-weight:700;'>(-XX)</span> Thru XX</div>"
    else:
        top3_html = "<div style='color:#888; font-style:italic; font-size:0.95rem;'>No golfers drafted yet</div>"
    
    # Clean card matching the reference image style
    card = f"""
    <div style="
        border: 5px solid {color}; 
        background-color: {color}18; 
        border-radius: 22px; 
        padding: 16px 22px; 
        margin-bottom: 1.5rem;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    ">
        <div style="color:{color}; font-size:1.7rem; font-weight:800; margin-bottom:6px;">
            {team_name}
        </div>
        
        <div style="font-size:1.4rem; font-weight:700; color:{color}; margin: 8px 0 10px 0;">
            Total (-XX)
        </div>
        
        <div style="line-height:1.45;">
            {top3_html}
        </div>
    </div>
    """
    st.markdown(card, unsafe_allow_html=True)

# ====================== TOP 10 LEADERBOARD (placeholder) ======================
st.subheader("Top 10 Leaderboard")
st.caption("Live leaderboard will appear here during the tournament.")

# ====================== TEAM ROSTERS (Nice tables with top-3 highlighted) ======================
st.subheader("Team Rosters")

def get_golfer_info(name):
    return {"score": None, "hole": "—"}

team_cols = st.columns(3)
for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        color = COACH_COLORS.get(coach_id, "#555555")

        st.markdown(f"**{team_name}**")

        if not players:
            st.caption("No golfers drafted yet")
        else:
            table_data = []
            for p in players:
                g_info = get_golfer_info(p)
                table_data.append({
                    "Golfer": p,
                    "Score": g_info["score"] if g_info["score"] is not None else "N/A",
                    "Hole": g_info["hole"]
                })

            df = pd.DataFrame(table_data)

            numeric_scores = df[df["Score"] != "N/A"]["Score"].astype(float)
            if len(numeric_scores) >= 3:
                top3_indices = numeric_scores.nsmallest(3).index.tolist()
            else:
                top3_indices = numeric_scores.index.tolist()

            def highlight_top3(row):
                if row.name in top3_indices:
                    return ['background-color: #ffeb3b; font-weight: bold'] * len(row)
                return [''] * len(row)

            styled_df = df.style.apply(highlight_top3, axis=1)

            # Big colored container for the entire roster table
            roster_style = f"""
                border: 4px solid {color}; 
                background-color: {color}10; 
                border-radius: 14px; 
                padding: 12px;
                margin-top: 8px;
            """
            st.markdown(f'<div style="{roster_style}">', unsafe_allow_html=True)
            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=220)
            st.markdown('</div>', unsafe_allow_html=True)

# ====================== DRAFT SECTION ======================
with st.expander("🎯 DRAFT SECTION", expanded=True):
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

    if st.session_state.draft_active:
        current_coach = get_coach_for_pick(st.session_state.current_pick, st.session_state.draft_order)
        st.markdown(f"## 🔥 CURRENT PICK: **{current_coach}** — Pick #{st.session_state.current_pick}")
        if st.session_state.draft_paused:
            st.warning("⏸️ Draft is PAUSED")
    else:
        st.info("Draft is not active. Click Start Draft to begin.")

    st.subheader("Draft Dashboard")

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
        grid_html += f"<th>{p}</th>"
    grid_html += "</tr>"

    for r in range(10):
        grid_html += f"<tr><td><b>Round {r+1}</b></td>"
        for c in range(3):
            if r % 2 == 0:
                pick_num = r * 3 + c + 1
            else:
                pick_num = r * 3 + (2 - c) + 1

            picked_golfer = None
            for pk in st.session_state.picks:
                if pk[0] == pick_num:
                    picked_golfer = pk[2]
                    break

            is_current = (pick_num == st.session_state.current_pick and st.session_state.draft_active and not st.session_state.draft_paused)

            if picked_golfer:
                cell = picked_golfer
                cell_style = ""
            elif is_current:
                elapsed = int(time.time() - st.session_state.last_pick_time)
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
    available = [p for p in PGA_PLAYERS if p not in st.session_state.picked_golfers]

    if not available:
        st.success("All golfers have been drafted!")

    num_cols = 4
    cols = st.columns(num_cols)
    for idx, golfer in enumerate(available):
        col_idx = idx % num_cols
        with cols[col_idx]:
            disabled = not (st.session_state.draft_active and not st.session_state.draft_paused)
            if st.button(f"✅ {golfer}", key=f"pick_{golfer}", disabled=disabled, use_container_width=True):
                coach = get_coach_for_pick(st.session_state.current_pick, st.session_state.draft_order)
                if golfer not in teams_data[coach]["players"]:
                    teams_data[coach]["players"].append(golfer)
                    save_teams(teams_data)
                st.session_state.picks.append((st.session_state.current_pick, coach, golfer))
                st.session_state.picked_golfers.add(golfer)
                st.session_state.current_pick += 1
                st.session_state.last_pick_time = time.time()
                if st.session_state.current_pick > 30:
                    st.session_state.draft_active = False
                    st.success("🎉 Draft Complete! All 30 picks made.")
                st.rerun()

    st.divider()
    col_red, col_undo = st.columns(2)
    with col_red:
        if st.button("🛑 Reset Draft & Clear Roster", type="secondary", use_container_width=True):
            confirm = st.checkbox("⚠️ Confirm: Permanently clear ALL golfers from every roster and reset the draft board?")
            if confirm:
                for c in teams_data:
                    teams_data[c]["players"] = []
                save_teams(teams_data)
                st.session_state.picks = []
                st.session_state.picked_golfers = set()
                st.session_state.current_pick = 1
                st.session_state.draft_active = False
                st.session_state.draft_paused = False
                st.session_state.last_pick_time = time.time()
                st.success("Draft fully reset — all rosters cleared and dashboard returned to starting state!")
                st.rerun()
    with col_undo:
        if st.button("↩️ Undo Last Pick", use_container_width=True):
            if st.session_state.picks:
                last_pick = st.session_state.picks.pop()
                pick_num, coach, golfer = last_pick
                if golfer in teams_data[coach]["players"]:
                    teams_data[coach]["players"].remove(golfer)
                save_teams(teams_data)
                st.session_state.picked_golfers.discard(golfer)
                st.session_state.current_pick = pick_num
                st.session_state.last_pick_time = time.time()
                st.success(f"Undid Pick {pick_num}: {golfer}")
                st.rerun()
            else:
                st.warning("No picks to undo yet.")

# ====================== ADMIN SECTION ======================
with st.expander("🔧 Admin Section", expanded=False):
    st.subheader("Edit Team Names")
    new_teams = {}
    for coach_id, info in teams_data.items():
        st.markdown(f"### {coach_id}")
        new_name = st.text_input("Team Name", value=info.get("team_name", coach_id), key=f"admin_name_{coach_id}")
        new_teams[coach_id] = {"team_name": new_name, "players": info.get("players", [])}

    if st.button("💾 Save Team Names", type="primary"):
        save_teams(new_teams)
        st.success("Team names saved successfully!")
        st.rerun()

    st.divider()
    st.subheader("Draft Order Setup")
    st.write("Choose the order for the snake draft (who picks first, second, third):")

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
