import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import requests
import json
import base64
import time
import html
from datetime import datetime

st.set_page_config(
    page_title="PGA Championship Draft 2026",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background: #000000 !important;
        color: #ffffff !important;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: #000000 !important;
    }
    [data-testid="stSidebar"] {
        background: #000000 !important;
    }
    .stMarkdown, .stCaption, label, p, h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
    }
    div[data-testid="stExpander"] {
        background: #050505 !important;
        border: 1px solid #333333 !important;
    }
    button {
        border-radius: 8px !important;
    }
    .roster-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.95rem;
        background: #080808;
        color: #ffffff;
        overflow: hidden;
        border-radius: 8px;
    }
    .roster-table th {
        text-align: left;
        padding: 10px 12px;
        color: #ffffff;
        border-bottom: 1px solid rgba(255,255,255,0.18);
        font-weight: 800;
    }
    .roster-table td {
        padding: 10px 12px;
        border-bottom: 1px solid rgba(255,255,255,0.10);
        vertical-align: middle;
    }
    .roster-table tr:last-child td {
        border-bottom: none;
    }
    .roster-top-three td {
        background: #ffeb3b !important;
        color: #000000 !important;
        font-weight: 900;
    }
    .draft-stopped-note {
        color: #bbbbbb;
        font-style: italic;
        margin: 0.5rem 0 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def read_secret(*path):
    try:
        current = st.secrets
        for key in path:
            if key not in current:
                return None
            current = current[key]
        return current
    except Exception:
        return None


GITHUB_TOKEN = read_secret("GITHUB", "TOKEN")
REPO_OWNER = "theleitas"
REPO_NAME = "majors-draft-challenge-2026"
STATE_FILE_PATH = "draft_state.json"
BRANCH = "main"
MAX_PICKS = 30

GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

COACH_COLORS = {
    "Jayme Leita": "#00cc77",
    "Spencer Tidwell": "#bb77ff",
    "Peter Miller": "#2E47DB",
}

STATIC_ODDS = {
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
    "Cameron Young",
])

PLAYER_RESULTS = {
    # Add manual scores here later, or replace this with a leaderboard feed.
    # "Scottie Scheffler": {"score": "-4", "hole": "12"},
    # "Rory McIlroy": {"score": "E", "hole": "F"},
}


def default_state():
    return {
        "draft_enabled": False,
        "draft_active": False,
        "draft_order": ["Jayme Leita", "Spencer Tidwell", "Peter Miller"],
        "last_pick_started_at": 0,
        "teams": {
            "Jayme Leita": {"team_name": "Jayme's Team", "players": []},
            "Spencer Tidwell": {"team_name": "Spencer's Team", "players": []},
            "Peter Miller": {"team_name": "Peter's Team", "players": []},
        },
    }


def normalize_state(state):
    base = default_state()

    if not isinstance(state, dict):
        return base

    state.setdefault("draft_enabled", base["draft_enabled"])
    state.setdefault("draft_active", base["draft_active"])
    state.setdefault("draft_order", base["draft_order"])
    state.setdefault("last_pick_started_at", base["last_pick_started_at"])
    state.setdefault("teams", base["teams"])

    for coach, info in base["teams"].items():
        state["teams"].setdefault(coach, info)

    valid_coaches = list(state["teams"].keys())
    cleaned_order = [coach for coach in state["draft_order"] if coach in valid_coaches]

    for coach in valid_coaches:
        if coach not in cleaned_order:
            cleaned_order.append(coach)

    state["draft_order"] = cleaned_order[:3]

    for coach in valid_coaches:
        state["teams"][coach].setdefault("team_name", coach)
        state["teams"][coach].setdefault("players", [])

    return state


def github_file_url():
    return f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{STATE_FILE_PATH}"


def load_state_from_github(show_warning=True):
    try:
        resp = requests.get(github_file_url(), headers=GITHUB_HEADERS, timeout=10)

        if resp.status_code == 200:
            payload = resp.json()
            content = base64.b64decode(payload["content"]).decode("utf-8")
            return normalize_state(json.loads(content)), payload["sha"]

        if show_warning:
            st.warning(f"Could not load {STATE_FILE_PATH}. Status code: {resp.status_code}")

    except Exception as e:
        if show_warning:
            st.warning(f"Could not load {STATE_FILE_PATH}: {e}")

    return default_state(), None


def save_state_to_github(state, sha, message_prefix="Update draft state"):
    content_str = json.dumps(normalize_state(state), indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"{message_prefix} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": content_b64,
        "branch": BRANCH,
    }

    if sha:
        payload["sha"] = sha

    try:
        resp = requests.put(github_file_url(), headers=GITHUB_HEADERS, json=payload, timeout=15)

        if resp.status_code in [200, 201]:
            return True

        st.error(f"GitHub save failed. Status code: {resp.status_code}")
        st.code(resp.text)
        return False

    except Exception as e:
        st.error(f"GitHub save failed: {e}")
        return False


def mutate_shared_state(mutator, message_prefix):
    for _ in range(3):
        fresh_state, fresh_sha = load_state_from_github(show_warning=False)
        result = mutator(fresh_state)

        if result is False:
            return False, fresh_state

        if save_state_to_github(fresh_state, fresh_sha, message_prefix):
            return result, fresh_state

        time.sleep(0.5)

    st.error("Could not save after retrying. Please try again.")
    return False, None


def get_coach_for_pick(pick_num, order):
    round_idx = (pick_num - 1) // 3
    pos = (pick_num - 1) % 3
    return order[pos] if round_idx % 2 == 0 else order[2 - pos]


def derive_picks_from_state(state):
    picks = []
    teams = state["teams"]
    draft_order = state["draft_order"]
    coach_pick_counts = {coach: 0 for coach in draft_order}

    for pick_num in range(1, MAX_PICKS + 1):
        coach = get_coach_for_pick(pick_num, draft_order)
        coach_players = teams.get(coach, {}).get("players", [])
        player_idx = coach_pick_counts[coach]

        if player_idx >= len(coach_players):
            break

        picks.append((pick_num, coach, coach_players[player_idx]))
        coach_pick_counts[coach] += 1

    return picks


def get_current_pick(state):
    return min(len(derive_picks_from_state(state)) + 1, MAX_PICKS + 1)


def get_picked_golfers(state):
    picked = set()

    for info in state["teams"].values():
        picked.update(info.get("players", []))

    return picked


def reset_rosters_in_state(state):
    for coach, info in state["teams"].items():
        info["players"] = []

    state["draft_active"] = False
    state["draft_enabled"] = False
    state["last_pick_started_at"] = 0
    return True


def make_draft_pick(golfer):
    def mutator(state):
        state = normalize_state(state)
        current_pick = get_current_pick(state)

        if not state["draft_enabled"]:
            st.warning("The draft is disabled.")
            return False

        if not state["draft_active"]:
            st.warning("Start the draft before making a pick.")
            return False

        if current_pick > MAX_PICKS:
            state["draft_active"] = False
            state["draft_enabled"] = False
            st.warning("The draft is complete.")
            return False

        if golfer in get_picked_golfers(state):
            st.warning(f"{golfer} has already been drafted.")
            return False

        coach = get_coach_for_pick(current_pick, state["draft_order"])
        state["teams"][coach]["players"].append(golfer)

        next_pick = get_current_pick(state)
        state["last_pick_started_at"] = time.time()

        if next_pick > MAX_PICKS:
            state["draft_active"] = False
            state["draft_enabled"] = False

        return True

    return mutate_shared_state(mutator, "Draft pick")


def undo_last_pick():
    def mutator(state):
        picks = derive_picks_from_state(state)

        if not picks:
            st.warning("There are no picks to undo.")
            return False

        pick_num, coach, golfer = picks[-1]
        players = state["teams"][coach]["players"]

        if players and players[-1] == golfer:
            players.pop()
        elif golfer in players:
            players.remove(golfer)
        else:
            st.error("Could not find the last picked golfer in the roster.")
            return False

        state["draft_enabled"] = True
        state["draft_active"] = True
        state["last_pick_started_at"] = time.time()

        return pick_num, coach, golfer

    return mutate_shared_state(mutator, "Undo last pick")


def set_draft_enabled(enabled):
    def mutator(state):
        state["draft_enabled"] = enabled
        if not enabled:
            state["draft_active"] = False
        return True

    return mutate_shared_state(mutator, "Set draft enabled")


def start_draft():
    def mutator(state):
        if get_current_pick(state) > MAX_PICKS:
            state["draft_enabled"] = False
            state["draft_active"] = False
            st.warning("The draft is already complete.")
            return False

        state["draft_enabled"] = True
        state["draft_active"] = True
        state["last_pick_started_at"] = time.time()
        return True

    return mutate_shared_state(mutator, "Start draft")


def stop_draft():
    def mutator(state):
        state["draft_active"] = False
        return True

    return mutate_shared_state(mutator, "Stop draft")


def save_draft_order(new_order):
    def mutator(state):
        if state["draft_enabled"]:
            st.warning("Disable the draft before changing the draft order.")
            return False

        if len(set(new_order)) != len(new_order):
            st.warning("Each draft slot must have a different coach.")
            return False

        state["draft_order"] = new_order
        return True

    return mutate_shared_state(mutator, "Update draft order")


def save_team_names(new_teams):
    def mutator(state):
        for coach, new_name in new_teams.items():
            if coach in state["teams"]:
                state["teams"][coach]["team_name"] = new_name
        return True

    return mutate_shared_state(mutator, "Update team names")


def get_player_result(player):
    return PLAYER_RESULTS.get(player, {"score": "N/A", "hole": "—"})


def parse_golf_score(score):
    if score is None:
        return None

    score_text = str(score).strip().upper()

    if score_text in ["", "N/A", "—", "-", "WD", "CUT"]:
        return None

    if score_text in ["E", "EVEN"]:
        return 0

    try:
        return int(score_text.replace("+", ""))
    except ValueError:
        return None


def format_golf_score(score_value):
    if score_value is None:
        return "N/A"
    if score_value == 0:
        return "E"
    if score_value > 0:
        return f"+{score_value}"
    return str(score_value)


def get_sorted_scored_players(players):
    scored_players = []

    for draft_index, player in enumerate(players):
        result = get_player_result(player)
        score_value = parse_golf_score(result.get("score"))

        if score_value is not None:
            scored_players.append((score_value, draft_index, player, result))

    scored_players.sort(key=lambda item: (item[0], item[1]))
    return scored_players


def get_top_three_lowest_score_players(players):
    return {
        player
        for _, _, player, _ in get_sorted_scored_players(players)[:3]
    }


def get_team_total(players):
    top_three = get_sorted_scored_players(players)[:3]

    if not top_three:
        return "N/A"

    total = sum(score_value for score_value, _, _, _ in top_three)
    return format_golf_score(total)


def parse_american_odds(value):
    try:
        if value is None:
            return None
        return int(str(value).replace("+", "").strip())
    except Exception:
        return None


def implied_probability(american_odds):
    if american_odds is None:
        return 0

    if american_odds > 0:
        return 100 / (american_odds + 100)

    return abs(american_odds) / (abs(american_odds) + 100)


def golfer_odds_label(golfer):
    return STATIC_ODDS.get(golfer, "(N/A)")


def odds_sort_key(golfer):
    odds_value = parse_american_odds(STATIC_ODDS.get(golfer))
    probability = implied_probability(odds_value)
    return (-probability, golfer)


def render_pick_timer(start_time):
    if not start_time:
        start_time = time.time()

    start_ms = int(start_time * 1000)

    components.html(
        f"""
        <div style="background:#000;color:#fff;font-family:Arial,sans-serif;margin:0;padding:0;">
            <div style="font-size:1.6rem;font-weight:800;line-height:1.35;">
                ⏱️ <span id="draft-clock">00:00:00</span>
            </div>
        </div>
        <script>
        const startMs = {start_ms};

        function pad(value) {{
            return String(value).padStart(2, "0");
        }}

        function updateClock() {{
            const elapsed = Math.max(0, Math.floor((Date.now() - startMs) / 1000));
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            document.getElementById("draft-clock").textContent =
                `${{pad(hours)}}:${{pad(minutes)}}:${{pad(seconds)}}`;
        }}

        updateClock();
        setInterval(updateClock, 1000);
        </script>
        """,
        height=45,
    )


for key, default in [
    ("confirm_clear_rosters", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


state, state_sha = load_state_from_github()
state = normalize_state(state)
teams_data = state["teams"]
draft_order = state["draft_order"]
picks = derive_picks_from_state(state)
picked_golfers = get_picked_golfers(state)
current_pick = get_current_pick(state)

st_autorefresh(interval=5000, limit=None, key="shared_state_refresh")


st.title("🏌️ PGA Championship 2026")
st.caption("**May 14–17, 2026** • Aronimink Golf Club")


st.subheader("Standings")

for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    color = COACH_COLORS.get(coach_id, "#555555")
    players = info.get("players", [])
    total = get_team_total(players)
    scored_players = get_sorted_scored_players(players)[:3]

    if scored_players:
        top3_html = ""
        for score_value, _, player, result in scored_players:
            safe_player = html.escape(player)
            score = html.escape(format_golf_score(score_value))
            hole = html.escape(str(result.get("hole", "—")))
            top3_html += (
                f"<div style='margin:4px 0; color:{color}; font-size:1.05rem;'>"
                f"{safe_player} <span style='font-weight:700;'>({score})</span> Thru {hole}"
                f"</div>"
            )
    elif players:
        top3_html = "<div style='color:#aaa; font-style:italic;'>No live scores yet</div>"
    else:
        top3_html = "<div style='color:#aaa; font-style:italic;'>No golfers drafted yet</div>"

    card = (
        f"<div style='border: 5px solid {color}; background-color: {color}18; "
        f"border-radius: 16px; padding: 20px 24px; margin-bottom: 1.8rem; "
        f"box-shadow: 0 4px 15px rgba(255,255,255,0.08);'>"
        f"<div style='color:{color}; font-size:1.75rem; font-weight:800;'>{html.escape(team_name)}</div>"
        f"<div style='font-size:1.45rem; font-weight:700; color:{color}; margin:12px 0 14px 0;'>Total ({total})</div>"
        f"<div style='line-height:1.5;'>{top3_html}</div>"
        f"</div>"
    )

    st.markdown(card, unsafe_allow_html=True)


st.subheader("Team Rosters")

team_cols = st.columns(3)

for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        color = COACH_COLORS.get(coach_id, "#555555")
        top_three_lowest_score_players = get_top_three_lowest_score_players(players)

        roster_parts = [
            (
                f"<div style='border: 5px solid {color}; background-color: {color}18; "
                f"border-radius: 16px; padding: 20px 24px; margin-bottom: 1.8rem;'>"
            ),
            (
                f"<div style='color:{color}; font-size:1.75rem; font-weight:800; "
                f"margin-bottom:18px;'>{html.escape(team_name)}</div>"
            ),
        ]

        if not players:
            roster_parts.append("<div style='color:#aaa; font-style:italic;'>No golfers drafted yet</div>")
        else:
            roster_parts.append(
                "<table class='roster-table'>"
                "<thead><tr><th>Golfer</th><th>Score</th><th>Hole</th></tr></thead><tbody>"
            )

            for player in players:
                safe_player = html.escape(player)
                result = get_player_result(player)
                score = html.escape(str(result.get("score", "N/A")))
                hole = html.escape(str(result.get("hole", "—")))
                row_class = " class='roster-top-three'" if player in top_three_lowest_score_players else ""

                roster_parts.append(
                    f"<tr{row_class}>"
                    f"<td>{safe_player}</td>"
                    f"<td>{score}</td>"
                    f"<td>{hole}</td>"
                    "</tr>"
                )

            roster_parts.append("</tbody></table>")

        roster_parts.append("</div>")
        st.markdown("".join(roster_parts), unsafe_allow_html=True)


with st.expander("🎯 DRAFT SECTION", expanded=state["draft_enabled"]):
    if not state["draft_enabled"]:
        st.error("🚫 Draft is currently DISABLED in Admin section")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "▶️ Start Draft",
                type="primary",
                disabled=state["draft_active"] or current_pick > MAX_PICKS,
                use_container_width=True,
            ):
                result, _ = start_draft()
                if result:
                    st.rerun()

        with col2:
            if st.button(
                "⏹️ Stop Draft",
                disabled=not state["draft_active"],
                use_container_width=True,
            ):
                result, _ = stop_draft()
                if result:
                    st.rerun()

        with col3:
            if st.button(
                "↩️ Undo Last Pick",
                disabled=not picks,
                use_container_width=True,
            ):
                result, _ = undo_last_pick()
                if result:
                    undone_pick_num, undone_coach, undone_golfer = result
                    st.success(
                        f"Undid Pick #{undone_pick_num}: {undone_golfer}. "
                        f"{undone_coach} is back on the clock."
                    )
                    time.sleep(0.5)
                    st.rerun()

        if current_pick > MAX_PICKS:
            st.success("🎉 Draft Complete! All 30 picks are in.")
        elif state["draft_active"]:
            current_coach = get_coach_for_pick(current_pick, draft_order)

            st.markdown(
                f"## 🔥 CURRENT PICK: **{current_coach}** — "
                f"Pick #{current_pick}"
            )
            render_pick_timer(state.get("last_pick_started_at", 0))
        else:
            current_coach = get_coach_for_pick(current_pick, draft_order)
            st.markdown(
                f"<div class='draft-stopped-note'>Draft stopped. "
                f"{html.escape(current_coach)} is next at Pick #{current_pick}. "
                f"Start the draft to resume picking.</div>",
                unsafe_allow_html=True,
            )

        st.subheader("Draft Dashboard")

        grid_html = """
        <style>
        @keyframes flash {
            0% { background-color: #ffeb3b; }
            50% { background-color: #fff59d; }
            100% { background-color: #ffeb3b; }
        }
        .draft-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
            background: #000;
            color: #fff;
        }
        .draft-table th,
        .draft-table td {
            border: 1px solid #555;
            padding: 10px;
            text-align: center;
        }
        .draft-table th {
            background-color: #1f1f1f;
            color: #fff;
        }
        .current-cell {
            animation: flash 1.2s infinite;
            font-weight: bold;
        }
        .stopped-cell {
            background-color: #333333;
            color: #aaaaaa;
            font-weight: bold;
        }
        </style>
        <table class="draft-table">
        <tr><th>Round</th>
        """

        for coach in draft_order:
            grid_html += f"<th>{html.escape(coach)}</th>"

        grid_html += "</tr>"

        for round_num in range(10):
            grid_html += f"<tr><td><b>Round {round_num + 1}</b></td>"

            for column_num in range(3):
                if round_num % 2 == 0:
                    pick_num = round_num * 3 + column_num + 1
                else:
                    pick_num = round_num * 3 + (2 - column_num) + 1

                picked_golfer = next(
                    (pick[2] for pick in picks if pick[0] == pick_num),
                    None,
                )

                is_current = pick_num == current_pick

                if picked_golfer:
                    cell = html.escape(picked_golfer)
                    cell_style = ""
                elif is_current and state["draft_active"]:
                    cell = f"On Clock<br>Pick {pick_num}"
                    cell_style = "class='current-cell' style='background-color:#ffeb3b; color:#000;'"
                elif is_current and current_pick <= MAX_PICKS:
                    cell = f"Stopped<br>Pick {pick_num}"
                    cell_style = "class='stopped-cell'"
                else:
                    cell = f"Pick {pick_num}"
                    cell_style = ""

                grid_html += f"<td {cell_style}>{cell}</td>"

            grid_html += "</tr>"

        grid_html += "</table>"
        st.markdown(grid_html, unsafe_allow_html=True)

        st.subheader("Available Golfers — Click to Draft")
        st.caption("Draft buttons are sorted from the built-in static odds list. Shared draft state refreshes every 5 seconds.")

        sorted_players = sorted(PGA_PLAYERS, key=odds_sort_key)

        available = [
            golfer for golfer in sorted_players
            if golfer not in picked_golfers
        ]

        cols = st.columns(4)

        for idx, golfer in enumerate(available):
            with cols[idx % 4]:
                odds_label = golfer_odds_label(golfer)
                disabled = (
                    not state["draft_active"]
                    or current_pick > MAX_PICKS
                )

                if st.button(
                    f"✅ {golfer} {odds_label}",
                    key=f"pick_{golfer}",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    with st.spinner(f"Saving {golfer}..."):
                        result, _ = make_draft_pick(golfer)
                        if result:
                            st.rerun()


with st.expander("🔧 Admin Section", expanded=False):
    st.subheader("Draft Control")

    enable = st.toggle(
        "Enable Draft",
        value=state["draft_enabled"],
        key="enable_toggle",
    )

    if enable != state["draft_enabled"]:
        result, _ = set_draft_enabled(enable)
        st.session_state.confirm_clear_rosters = False
        if result:
            st.rerun()

    if state["draft_enabled"]:
        if not st.session_state.confirm_clear_rosters:
            if st.button(
                "🛑 Reset Draft & Clear Roster",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state.confirm_clear_rosters = True
                st.rerun()
        else:
            st.warning("⚠️ This will permanently clear ALL rosters and reset the draft.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "✅ YES, CLEAR EVERYTHING",
                    type="primary",
                    use_container_width=True,
                ):
                    result, _ = mutate_shared_state(reset_rosters_in_state, "Reset draft")
                    if result:
                        st.session_state.confirm_clear_rosters = False
                        st.success("✅ All rosters cleared and draft fully reset!")
                        time.sleep(1)
                        st.rerun()

            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_clear_rosters = False
                    st.rerun()

    st.subheader("Draft Order")

    if state["draft_enabled"]:
        st.info("Disable the draft to change the draft order.")
    else:
        coaches = list(teams_data.keys())
        current_order = draft_order

        order_col1, order_col2, order_col3 = st.columns(3)

        with order_col1:
            first_pick = st.selectbox(
                "1st Pick",
                options=coaches,
                index=coaches.index(current_order[0]) if current_order[0] in coaches else 0,
                key="draft_order_first",
            )

        with order_col2:
            second_pick = st.selectbox(
                "2nd Pick",
                options=coaches,
                index=coaches.index(current_order[1]) if current_order[1] in coaches else 1,
                key="draft_order_second",
            )

        with order_col3:
            third_pick = st.selectbox(
                "3rd Pick",
                options=coaches,
                index=coaches.index(current_order[2]) if current_order[2] in coaches else 2,
                key="draft_order_third",
            )

        proposed_order = [first_pick, second_pick, third_pick]

        if len(set(proposed_order)) < len(proposed_order):
            st.error("Each draft slot must have a different coach.")
        elif st.button("💾 Save Draft Order", use_container_width=True):
            result, _ = save_draft_order(proposed_order)
            if result:
                st.success("Draft order saved.")
                st.rerun()

    st.subheader("Edit Team Names")

    new_names = {}

    for coach_id, info in teams_data.items():
        st.markdown(f"### {coach_id}")

        new_name = st.text_input(
            "Team Name",
            value=info.get("team_name", coach_id),
            key=f"name_{coach_id}",
        )

        new_names[coach_id] = new_name

    if st.button("💾 Save Team Names"):
        result, _ = save_team_names(new_names)
        if result:
            st.success("Team names saved!")
            st.rerun()
        else:
            st.error("Team names were not saved. Please try again.")


st.caption("PGA Championship Draft 2026 • Built with Streamlit • Shared data saved to GitHub")
