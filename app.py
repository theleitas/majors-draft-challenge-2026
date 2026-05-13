import streamlit as st
import requests
import json
import base64
import time
import html
from datetime import datetime
from statistics import median
from streamlit_autorefresh import st_autorefresh

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
    .roster-player-row {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: center;
        border-radius: 10px;
        padding: 10px 12px;
        margin: 8px 0;
        font-weight: 700;
    }
    .roster-player-meta {
        font-weight: 700;
        opacity: 0.95;
        white-space: nowrap;
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
FILE_PATH = "teams.json"
BRANCH = "main"
MAX_PICKS = 30

GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

ODDS_API_KEY = read_secret("ODDS_API", "KEY") or read_secret("THE_ODDS_API", "KEY")
ODDS_SPORT_KEY = "golf_pga_championship_winner"

COACH_COLORS = {
    "Jayme Leita": "#00cc77",
    "Spencer Tidwell": "#bb77ff",
    "Peter Miller": "#2E47DB",
}

FALLBACK_ODDS = {
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
    # Add live or manual scores here.
    # "Scottie Scheffler": {"score": "-4", "hole": "12"},
    # "Rory McIlroy": {"score": "E", "hole": "F"},
    # "Xander Schauffele": {"score": "+1", "hole": "8"},
}

PLAYER_ALIASES = {
    "Matthew Fitzpatrick": "Matt Fitzpatrick",
    "Matt Fitzpatrick": "Matt Fitzpatrick",
    "JT Poston": "J.T. Poston",
    "J.T. Poston": "J.T. Poston",
    "Rasmus Neergaard Petersen": "Rasmus Neergaard-Petersen",
    "Nicolai Hojgaard": "Nicolai Højgaard",
    "Rasmus Hojgaard": "Rasmus Højgaard",
}


def default_teams():
    return {
        "Jayme Leita": {"team_name": "Jayme's Team", "players": []},
        "Spencer Tidwell": {"team_name": "Spencer's Team", "players": []},
        "Peter Miller": {"team_name": "Peter's Team", "players": []},
    }


def load_teams_from_github():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

    try:
        resp = requests.get(url, headers=GITHUB_HEADERS, timeout=10)
        if resp.status_code == 200:
            content = resp.json()["content"]
            return json.loads(base64.b64decode(content).decode("utf-8"))
        st.warning(f"Could not load teams from GitHub. Status code: {resp.status_code}")
    except Exception as e:
        st.warning(f"Could not load teams from GitHub: {e}")

    return default_teams()


def save_teams_to_github(teams_dict, message_prefix="Update teams"):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    content_str = json.dumps(teams_dict, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    for attempt in range(3):
        try:
            get_resp = requests.get(url, headers=GITHUB_HEADERS, timeout=10)
            sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

            payload = {
                "message": f"{message_prefix} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": content_b64,
                "branch": BRANCH,
            }

            if sha:
                payload["sha"] = sha

            put_resp = requests.put(url, headers=GITHUB_HEADERS, json=payload, timeout=15)

            if put_resp.status_code in [200, 201]:
                return True

            if put_resp.status_code == 409 and attempt < 2:
                time.sleep(0.6)
                continue

            st.error(f"GitHub save failed. Status code: {put_resp.status_code}")
            st.code(put_resp.text)
            return False

        except Exception as e:
            if attempt < 2:
                time.sleep(0.6)
                continue
            st.error(f"GitHub save failed: {e}")
            return False

    return False


def get_coach_for_pick(pick_num, order):
    round_idx = (pick_num - 1) // 3
    pos = (pick_num - 1) % 3
    return order[pos] if round_idx % 2 == 0 else order[2 - pos]


def reset_all_rosters(teams):
    return {
        coach: {
            "team_name": info.get("team_name", f"{coach}'s Team"),
            "players": [],
        }
        for coach, info in teams.items()
    }


def derive_picks_from_teams(teams, draft_order):
    picks = []
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


def sync_draft_state_from_teams(teams):
    picks = derive_picks_from_teams(teams, st.session_state.draft_order)
    picked_golfers = set()

    for info in teams.values():
        picked_golfers.update(info.get("players", []))

    st.session_state.picks = picks
    st.session_state.picked_golfers = picked_golfers
    st.session_state.current_pick = min(len(picks) + 1, MAX_PICKS + 1)

    if st.session_state.current_pick > MAX_PICKS:
        st.session_state.draft_active = False


def undo_last_pick(teams):
    picks = derive_picks_from_teams(teams, st.session_state.draft_order)

    if not picks:
        st.warning("There are no picks to undo.")
        return None

    pick_num, coach, golfer = picks[-1]
    players = teams.get(coach, {}).get("players", [])

    if players and players[-1] == golfer:
        players.pop()
    elif golfer in players:
        players.remove(golfer)
    else:
        st.error("Could not find the last picked golfer in the roster.")
        return None

    if save_teams_to_github(teams, "Undo last pick"):
        return pick_num, coach, golfer

    return None


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


def format_american_odds(value):
    if value is None:
        return "(N/A)"
    value = int(round(value))
    return f"+{value}" if value > 0 else str(value)


def implied_probability(american_odds):
    if american_odds is None:
        return 0

    if american_odds > 0:
        return 100 / (american_odds + 100)

    return abs(american_odds) / (abs(american_odds) + 100)


def normalize_player_name(name):
    return PLAYER_ALIASES.get(name, name)


def format_elapsed_time(start_time):
    elapsed = max(0, int(time.time() - start_time))
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@st.cache_data(ttl=900)
def fetch_live_odds(api_key):
    if not api_key:
        return {}, "Static fallback odds. Add [ODDS_API] KEY in Streamlit secrets for live odds."

    url = f"https://api.the-odds-api.com/v4/sports/{ODDS_SPORT_KEY}/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "outrights",
        "oddsFormat": "american",
    }

    try:
        resp = requests.get(url, params=params, timeout=12)
        if resp.status_code != 200:
            return {}, f"Static fallback odds. Live odds request failed with status {resp.status_code}."

        data = resp.json()
        player_prices = {}

        for event in data:
            for bookmaker in event.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    if market.get("key") != "outrights":
                        continue

                    for outcome in market.get("outcomes", []):
                        player = normalize_player_name(outcome.get("name"))
                        price = outcome.get("price")

                        if player in PGA_PLAYERS and isinstance(price, int):
                            player_prices.setdefault(player, []).append(price)

        odds = {}
        for player, prices in player_prices.items():
            median_price = int(round(median(prices)))
            odds[player] = {
                "label": format_american_odds(median_price),
                "sort_price": median_price,
                "books": len(prices),
            }

        if not odds:
            return {}, "Static fallback odds. Live odds returned no matching golfers."

        return odds, "Live odds: The Odds API PGA Championship Winner outrights, median US sportsbook price."

    except Exception as e:
        return {}, f"Static fallback odds. Live odds request failed: {e}"


def golfer_odds_info(golfer, live_odds):
    if golfer in live_odds:
        return live_odds[golfer]

    fallback_price = parse_american_odds(FALLBACK_ODDS.get(golfer))
    if fallback_price is not None:
        return {
            "label": format_american_odds(fallback_price),
            "sort_price": fallback_price,
            "books": 0,
        }

    return {
        "label": "(N/A)",
        "sort_price": None,
        "books": 0,
    }


def odds_sort_key(golfer, live_odds):
    info = golfer_odds_info(golfer, live_odds)
    probability = implied_probability(info.get("sort_price"))
    return (-probability, golfer)


for key, default in [
    ("draft_active", False),
    ("enable_draft", False),
    ("confirm_clear_rosters", False),
    ("current_pick", 1),
    ("picks", []),
    ("picked_golfers", set()),
    ("draft_order", ["Jayme Leita", "Spencer Tidwell", "Peter Miller"]),
    ("last_pick_time", time.time()),
    ("saving_action", False),
]:
    if key not in st.session_state:
        st.session_state[key] = default


teams_data = load_teams_from_github()
sync_draft_state_from_teams(teams_data)
live_odds, odds_source = fetch_live_odds(ODDS_API_KEY)

if (
    st.session_state.draft_active
    and st.session_state.current_pick <= MAX_PICKS
    and not st.session_state.saving_action
):
    st_autorefresh(interval=1000, limit=None, key="draft_timer_refresh")


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

    card = f"""
    <div style="border: 5px solid {color}; background-color: {color}18; border-radius: 16px; padding: 20px 24px; margin-bottom: 1.8rem; box-shadow: 0 4px 15px rgba(255,255,255,0.08);">
        <div style="color:{color}; font-size:1.75rem; font-weight:800;">{html.escape(team_name)}</div>
        <div style="font-size:1.45rem; font-weight:700; color:{color}; margin:12px 0 14px 0;">Total ({total})</div>
        <div style="line-height:1.5;">{top3_html}</div>
    </div>
    """

    st.markdown(card, unsafe_allow_html=True)


st.subheader("Team Rosters")

team_cols = st.columns(3)

for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        color = COACH_COLORS.get(coach_id, "#555555")
        top_three_lowest_score_players = get_top_three_lowest_score_players(players)

        roster_html = f"""
        <div style="border: 5px solid {color}; background-color: {color}18; border-radius: 16px; padding: 20px 24px; margin-bottom: 1.8rem;">
            <div style="color:{color}; font-size:1.75rem; font-weight:800; margin-bottom:12px;">{html.escape(team_name)}</div>
        """

        if not players:
            roster_html += "<div style='color:#aaa; font-style:italic;'>No golfers drafted yet</div>"
        else:
            for player in players:
                safe_player = html.escape(player)
                result = get_player_result(player)
                score = html.escape(str(result.get("score", "N/A")))
                hole = html.escape(str(result.get("hole", "—")))

                if player in top_three_lowest_score_players:
                    roster_html += f"""
                    <div class="roster-player-row" style="border: 2px solid #ffeb3b; background:#ffeb3b; color:#000000;">
                        <span>{safe_player}</span>
                        <span class="roster-player-meta">{score} · {hole}</span>
                    </div>
                    """
                else:
                    roster_html += f"""
                    <div class="roster-player-row" style="border: 2px solid {color}; background:{color}22; color:{color};">
                        <span>{safe_player}</span>
                        <span class="roster-player-meta">{score} · {hole}</span>
                    </div>
                    """

        roster_html += "</div>"
        st.markdown(roster_html, unsafe_allow_html=True)


with st.expander("🎯 DRAFT SECTION", expanded=st.session_state.enable_draft):
    if not st.session_state.enable_draft:
        st.error("🚫 Draft is currently DISABLED in Admin section")
    else:
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "▶️ Start Draft",
                type="primary",
                disabled=st.session_state.draft_active,
                use_container_width=True,
            ):
                sync_draft_state_from_teams(teams_data)
                st.session_state.draft_active = True
                st.session_state.confirm_clear_rosters = False
                st.session_state.last_pick_time = time.time()
                st.rerun()

        with col2:
            if st.button(
                "↩️ Undo Last Pick",
                disabled=not st.session_state.picks,
                use_container_width=True,
            ):
                undo_result = undo_last_pick(teams_data)

                if undo_result:
                    undone_pick_num, undone_coach, undone_golfer = undo_result
                    sync_draft_state_from_teams(teams_data)
                    st.session_state.current_pick = undone_pick_num
                    st.session_state.draft_active = True
                    st.session_state.last_pick_time = time.time()

                    st.success(
                        f"Undid Pick #{undone_pick_num}: {undone_golfer}. "
                        f"{undone_coach} is back on the clock."
                    )
                    time.sleep(0.5)
                    st.rerun()

        if st.session_state.draft_active:
            if st.session_state.current_pick <= MAX_PICKS:
                current_coach = get_coach_for_pick(
                    st.session_state.current_pick,
                    st.session_state.draft_order,
                )
                timer_text = format_elapsed_time(st.session_state.last_pick_time)

                st.markdown(
                    f"## 🔥 CURRENT PICK: **{current_coach}** — "
                    f"Pick #{st.session_state.current_pick} — ⏱️ {timer_text}"
                )
            else:
                st.success("🎉 Draft Complete!")

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
        </style>
        <table class="draft-table">
        <tr><th>Round</th>
        """

        for coach in st.session_state.draft_order:
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
                    (pick[2] for pick in st.session_state.picks if pick[0] == pick_num),
                    None,
                )

                is_current = (
                    pick_num == st.session_state.current_pick
                    and st.session_state.draft_active
                )

                if picked_golfer:
                    cell = html.escape(picked_golfer)
                    cell_style = ""
                elif is_current:
                    timer_text = format_elapsed_time(st.session_state.last_pick_time)
                    cell = f"⏱️ {timer_text}<br>Pick {pick_num}"
                    cell_style = "class='current-cell' style='background-color:#ffeb3b; color:#000;'"
                else:
                    cell = f"Pick {pick_num}"
                    cell_style = ""

                grid_html += f"<td {cell_style}>{cell}</td>"

            grid_html += "</tr>"

        grid_html += "</table>"
        st.markdown(grid_html, unsafe_allow_html=True)

        st.subheader("Available Golfers — Click to Draft")
        st.caption(odds_source)

        sorted_players = sorted(
            PGA_PLAYERS,
            key=lambda golfer: odds_sort_key(golfer, live_odds),
        )

        available = [
            golfer for golfer in sorted_players
            if golfer not in st.session_state.picked_golfers
        ]

        cols = st.columns(4)

        for idx, golfer in enumerate(available):
            col_idx = idx % 4

            with cols[col_idx]:
                odds_info = golfer_odds_info(golfer, live_odds)
                odds_label = odds_info["label"]
                disabled = (
                    not st.session_state.draft_active
                    or st.session_state.current_pick > MAX_PICKS
                    or st.session_state.saving_action
                )

                if st.button(
                    f"✅ {golfer} {odds_label}",
                    key=f"pick_{golfer}",
                    disabled=disabled,
                    use_container_width=True,
                ):
                    st.session_state.saving_action = True

                    coach = get_coach_for_pick(
                        st.session_state.current_pick,
                        st.session_state.draft_order,
                    )

                    if golfer in st.session_state.picked_golfers:
                        st.warning(f"{golfer} has already been drafted.")
                        st.session_state.saving_action = False
                        st.rerun()

                    teams_data.setdefault(coach, {"team_name": f"{coach}'s Team", "players": []})
                    teams_data[coach].setdefault("players", [])
                    teams_data[coach]["players"].append(golfer)

                    if save_teams_to_github(teams_data, "Draft pick"):
                        sync_draft_state_from_teams(teams_data)
                        st.session_state.last_pick_time = time.time()

                        if st.session_state.current_pick > MAX_PICKS:
                            st.session_state.draft_active = False
                            st.success("🎉 Draft Complete!")

                        st.session_state.saving_action = False
                        st.rerun()
                    else:
                        teams_data[coach]["players"].remove(golfer)
                        st.session_state.saving_action = False
                        st.error("Pick was not saved. Please try again.")


with st.expander("🔧 Admin Section", expanded=False):
    st.subheader("Draft Control")

    enable = st.toggle(
        "Enable Draft",
        value=st.session_state.enable_draft,
        key="enable_toggle",
    )

    if enable != st.session_state.enable_draft:
        st.session_state.enable_draft = enable
        st.session_state.confirm_clear_rosters = False
        st.rerun()

    if st.session_state.enable_draft:
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
                    empty_teams = reset_all_rosters(teams_data)

                    if save_teams_to_github(empty_teams, "Reset draft"):
                        st.session_state.picks = []
                        st.session_state.picked_golfers = set()
                        st.session_state.current_pick = 1
                        st.session_state.draft_active = False
                        st.session_state.confirm_clear_rosters = False
                        st.session_state.last_pick_time = time.time()

                        st.success("✅ All rosters cleared and draft fully reset!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Could not clear rosters in GitHub. Check the token/repo permissions.")

            with col2:
                if st.button("Cancel", use_container_width=True):
                    st.session_state.confirm_clear_rosters = False
                    st.rerun()

    st.subheader("Edit Team Names")

    new_teams = {}

    for coach_id, info in teams_data.items():
        st.markdown(f"### {coach_id}")

        new_name = st.text_input(
            "Team Name",
            value=info.get("team_name", coach_id),
            key=f"name_{coach_id}",
        )

        new_teams[coach_id] = {
            "team_name": new_name,
            "players": info.get("players", []),
        }

    if st.button("💾 Save Team Names"):
        if save_teams_to_github(new_teams, "Update team names"):
            st.success("Team names saved!")
            st.rerun()
        else:
            st.error("Team names were not saved. Please try again.")


st.caption("PGA Championship Draft 2026 • Built with Streamlit • Data saved to GitHub")
