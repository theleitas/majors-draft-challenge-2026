import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import requests, json, base64, time, html, os, mimetypes, re
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="PGA Championship Draft 2026",
    page_icon="thumb.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], .stApp { background:#000!important; color:#fff!important; }
[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stSidebar"] { background:#000!important; }
.stMarkdown, .stCaption, label, p, h1, h2, h3, h4, h5, h6 { color:#fff; }
div[data-testid="stExpander"] { background:#050505!important; border:1px solid #333!important; }
button { border-radius:8px!important; }
div[data-testid="stButton"] > button {
    background:#151515!important; color:#fff!important; border:1px solid #555!important;
    font-weight:800!important; white-space:normal!important; min-height:46px!important; line-height:1.2!important;
}
div[data-testid="stButton"] > button:hover { background:#222!important; color:#fff!important; border-color:#888!important; }
div[data-testid="stButton"] > button:focus {
    background:#222!important; color:#fff!important; border-color:#ffeb3b!important;
    box-shadow:0 0 0 2px rgba(255,235,59,.35)!important;
}
div[data-testid="stButton"] > button:disabled, div[data-testid="stButton"] > button[disabled] {
    background:#2b2b2b!important; color:#9a9a9a!important; border-color:#444!important; opacity:1!important;
}
.refresh-button-wrap div[data-testid="stButton"] > button {
    width:100%!important; min-height:64px!important; background:#ff4b00!important; color:#000!important;
    border:3px solid #ffb000!important; font-size:1.35rem!important; font-weight:1000!important;
    letter-spacing:.02em!important; text-transform:uppercase!important;
    box-shadow:0 0 18px rgba(255,75,0,.7), inset 0 0 10px rgba(255,255,255,.28)!important;
}
.refresh-button-wrap div[data-testid="stButton"] > button:hover {
    background:#ff7a00!important; color:#000!important; border-color:#ffe600!important;
}
.app-title { display:flex; align-items:center; gap:14px; margin:.6rem 0 .25rem 0; }
.app-title h1 { margin:0; padding:0; font-size:2.75rem; line-height:1.1; font-weight:800; }
.app-logo { width:3.5em; height:3.5em; object-fit:contain; flex:0 0 auto; }
.roster-table { width:100%; border-collapse:collapse; font-size:.95rem; background:#080808; color:#fff; overflow:hidden; border-radius:8px; }
.roster-table th { text-align:left; padding:10px 12px; color:#fff; border-bottom:1px solid rgba(255,255,255,.18); font-weight:800; }
.roster-table td { padding:10px 12px; border-bottom:1px solid rgba(255,255,255,.10); vertical-align:middle; }
.roster-table tr:last-child td { border-bottom:none; }
.roster-top-three td { background:#ffeb3b!important; color:#000!important; font-weight:900; }
.draft-stopped-note { color:#bbb; font-style:italic; margin:.5rem 0 1rem 0; }
.team-heading { display:flex; align-items:center; gap:14px; }
.team-face { width:2.5em; height:2.5em; border-radius:50%; object-fit:cover; border:2px solid currentColor; flex:0 0 auto; }
@media (max-width:700px) {
    div[data-testid="column"] { width:100%!important; flex:1 1 100%!important; }
    div[data-testid="stButton"] > button { min-height:54px!important; font-size:.98rem!important; }
    .refresh-button-wrap div[data-testid="stButton"] > button { min-height:58px!important; font-size:1.05rem!important; }
    .app-title h1 { font-size:2rem; }
}
</style>
""", unsafe_allow_html=True)

def read_secret(*path):
    try:
        cur = st.secrets
        for key in path:
            if key not in cur:
                return None
            cur = cur[key]
        return cur
    except Exception:
        return None

GITHUB_TOKEN = read_secret("GITHUB", "TOKEN")
REPO_OWNER = "theleitas"
REPO_NAME = "majors-draft-challenge-2026"
STATE_FILE_PATH = "draft_state.json"
BRANCH = "main"
MAX_PICKS = 30
ESPN_LEADERBOARD_URL = "https://site.web.api.espn.com/apis/site/v2/sports/golf/leaderboard?league=pga"

GITHUB_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

COACH_COLORS = {
    "Jayme Leita": "#00cc77",
    "Spencer Tidwell": "#bb77ff",
    "Peter Miller": "#8ECFFF",
}

COACH_IMAGES = {
    "Jayme Leita": "jayme-pic.png",
    "Spencer Tidwell": "spencer-pic.png",
    "Peter Miller": "peter-pic.png",
}

APP_LOGO = "pga-tour.png"

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

PLAYER_FLAGS = {
    "Ludvig Aberg": "🇸🇪", "Angel Ayora": "🇪🇸", "Christiaan Bezuidenhout": "🇿🇦",
    "Francisco Bide": "🇦🇷", "Daniel Brown": "🇬🇧", "Corey Conners": "🇨🇦",
    "Jason Day": "🇦🇺", "Thomas Detry": "🇧🇪", "Luke Donald": "🇬🇧",
    "Nico Echavarria": "🇨🇴", "Alex Fitzpatrick": "🇬🇧", "Matt Fitzpatrick": "🇬🇧",
    "Tommy Fleetwood": "🇬🇧", "Ryan Fox": "🇳🇿", "Emiliano Grillo": "🇦🇷",
    "Harry Hall": "🇬🇧", "Padraig Harrington": "🇮🇪", "Tyrrell Hatton": "🇬🇧",
    "Kazuki Higa": "🇯🇵", "Garrick Higgo": "🇿🇦", "Daniel Hillier": "🇳🇿",
    "Ryo Hisatsune": "🇯🇵", "Rico Hoey": "🇵🇭", "Viktor Hovland": "🇳🇴",
    "Nicolai Højgaard": "🇩🇰", "Rasmus Højgaard": "🇩🇰", "Sungjae Im": "🇰🇷",
    "Stephan Jaeger": "🇩🇪", "Casey Jarvis": "🇿🇦", "Kota Kaneko": "🇯🇵",
    "Martin Kaymer": "🇩🇪", "Si Woo Kim": "🇰🇷", "Min Woo Lee": "🇦🇺",
    "Haotong Li": "🇨🇳", "Mikael Lindberg": "🇸🇪", "Shane Lowry": "🇮🇪",
    "Robert MacIntyre": "🇬🇧", "Hideki Matsuyama": "🇯🇵", "Rory McIlroy": "🇬🇧",
    "Tom McKibbin": "🇬🇧", "Rasmus Neergaard-Petersen": "🇩🇰", "Joaquin Niemann": "🇨🇱",
    "Alex Noren": "🇸🇪", "John Parry": "🇬🇧", "Taylor Pendrith": "🇨🇦",
    "Marco Penge": "🇬🇧", "Aldrich Potgieter": "🇿🇦", "David Puig": "🇪🇸",
    "Jon Rahm": "🇪🇸", "Aaron Rai": "🇬🇧", "Kristoffer Reitan": "🇳🇴",
    "Justin Rose": "🇬🇧", "Adrien Saddier": "🇫🇷", "Jayden Schaper": "🇿🇦",
    "Matti Schmid": "🇩🇪", "Adam Scott": "🇦🇺", "Cameron Smith": "🇦🇺",
    "Jordan Smith": "🇬🇧", "Elvis Smylie": "🇦🇺", "Travis Smyth": "🇦🇺",
    "Sepp Straka": "🇦🇹", "Andy Sullivan": "🇬🇧", "Nick Taylor": "🇨🇦",
    "Sami Valimaki": "🇫🇮", "Jhonattan Vegas": "🇻🇪", "Matt Wallace": "🇬🇧",
    "Bernd Wiesberger": "🇦🇹", "Y.E. Yang": "🇰🇷", "Sudarshan Yellamaraju": "🇨🇦",
}

def default_state():
    return {
        "draft_enabled": False,
        "draft_active": False,
        "draft_order": ["Jayme Leita", "Spencer Tidwell", "Peter Miller"],
        "last_pick_started_at": 0,
        "player_results": {},
        "last_score_refresh_at": 0,
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
    state.setdefault("player_results", base["player_results"])
    state.setdefault("last_score_refresh_at", base["last_score_refresh_at"])
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

def image_to_data_uri(path):
    if not os.path.exists(path):
        return ""
    mime_type = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"

def image_html(path, class_name):
    data_uri = image_to_data_uri(path)
    if not data_uri:
        return ""
    return f"<img class='{class_name}' src='{data_uri}' alt=''>"

def app_logo_html():
    return image_html(APP_LOGO, "app-logo")

def coach_image_html(coach_id):
    image_path = COACH_IMAGES.get(coach_id)
    if not image_path:
        return ""
    return image_html(image_path, "team-face")

def flag_for_player(player):
    return PLAYER_FLAGS.get(player, "🇺🇸")

def display_player_name(player):
    return f"{flag_for_player(player)} {player}"

def last_name_key(player):
    cleaned = player.replace(".", "").replace("'", "")
    parts = cleaned.split()
    return parts[-1].lower() if parts else cleaned.lower()

def normalize_player_match_name(name):
    name = str(name or "").strip()
    replacements = {
        "Å": "A", "å": "a", "Á": "A", "á": "a", "É": "E", "é": "e", "Í": "I", "í": "i",
        "Ó": "O", "ó": "o", "Ú": "U", "ú": "u", "Ø": "O", "ø": "o",
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    name = name.replace("Højgaard", "Hojgaard").replace("Neergaard-Petersen", "Neergaard Petersen")
    name = re.sub(r"[^A-Za-z ]", "", name)
    return re.sub(r"\s+", " ", name).strip().lower()

PLAYER_NAME_LOOKUP = {normalize_player_match_name(player): player for player in PGA_PLAYERS}

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
        return resp.status_code in [200, 201]
    except Exception:
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

def extract_competitors(payload):
    competitors = []
    for event in payload.get("events", []):
        for competition in event.get("competitions", []):
            competitors.extend(competition.get("competitors", []))
    return competitors

def extract_athlete_name(competitor):
    athlete = competitor.get("athlete") or competitor.get("player") or {}
    return (
        athlete.get("displayName")
        or athlete.get("fullName")
        or competitor.get("displayName")
        or competitor.get("name")
        or ""
    )

def get_status_state(competitor):
    status = competitor.get("status")
    if isinstance(status, dict):
        stype = status.get("type")
        if isinstance(stype, dict):
            state_val = stype.get("state")
            if state_val:
                return str(state_val).lower()
    return ""

def looks_like_topar(value):
    """True if the string looks like a to-par value (E, -3, +1) rather than a stroke total."""
    if value is None:
        return False
    text = str(value).strip().upper().replace("−", "-")
    if text in ("E", "EVEN"):
        return True
    if re.fullmatch(r"[+-]\d{1,2}", text):
        return True
    # bare digits like "212" or "0" are NOT to-par (those are stroke totals or pre-round zeros)
    return False

def extract_score_value(competitor):
    """
    Walk ESPN's leaderboard structure to find the to-par value.
    Order of preference: statistics[scoreToPar] -> linescores cumulative -> score field -> displayValue.
    Never return a bare "0" — that's almost always a pre-round placeholder, not even-par.
    """
    state_val = get_status_state(competitor)

    # 1. statistics array (some endpoints)
    stats = competitor.get("statistics") or []
    if isinstance(stats, list):
        for stat in stats:
            if not isinstance(stat, dict):
                continue
            name = (stat.get("name") or stat.get("abbreviation") or "").lower()
            if name in ("scoretopar", "topar", "toparscore", "totaltopar"):
                val = stat.get("displayValue") or stat.get("value")
                if val not in (None, "") and looks_like_topar(val):
                    return val

    # 2. linescores: look for a cumulative to-par
    linescores = competitor.get("linescores")
    if isinstance(linescores, list):
        for ls in linescores:
            if not isinstance(ls, dict):
                continue
            for key in ("currentScore", "cumulativeScore", "toParCumulative"):
                v = ls.get(key)
                if isinstance(v, dict):
                    dv = v.get("displayValue")
                    if dv and looks_like_topar(dv):
                        return dv
                elif looks_like_topar(v):
                    return v

    # 3. competitor-level score field — dict form
    score = competitor.get("score")
    if isinstance(score, dict):
        dv = score.get("displayValue")
        if dv and looks_like_topar(dv):
            return dv
    elif isinstance(score, str):
        if looks_like_topar(score):
            return score
        # If it's "0" and the player hasn't started, treat as N/A — not even.
        if score.strip() == "0" and state_val in ("pre", "", "scheduled"):
            return "N/A"
        # If it's "0" and player IS in/post, ESPN sometimes literally returns "0" meaning even
        if score.strip() == "0" and state_val in ("in", "post"):
            return "E"

    # 4. competitor displayValue
    dv = competitor.get("displayValue")
    if dv and looks_like_topar(dv):
        return dv

    return "N/A"

def clean_status_text(value):
    if value is None:
        return ""
    value = str(value).strip()
    if not value or value.lower() in ["none", "null", "n/a"]:
        return ""
    return value

def format_tee_time(value):
    value = clean_status_text(value)
    if not value:
        return ""

    iso_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?", value)
    if iso_match:
        raw = iso_match.group(0)
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        elif re.search(r"[+-]\d{4}$", raw):
            raw = raw[:-5] + raw[-5:-2] + ":" + raw[-2:]
        try:
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
            parsed = parsed.astimezone(ZoneInfo("America/New_York"))
            return parsed.strftime("%I:%M %p").lstrip("0")
        except Exception:
            pass

    for fmt in ["%I:%M %p", "%I:%M%p", "%H:%M"]:
        try:
            parsed = datetime.strptime(value.upper(), fmt)
            return parsed.strftime("%I:%M %p").lstrip("0")
        except Exception:
            pass

    short_time = re.search(r"\b(\d{1,2}:\d{2})\s*([AP]M)?\b", value.upper())
    if short_time:
        if short_time.group(2):
            return f"{short_time.group(1)} {short_time.group(2)}"
        try:
            parsed = datetime.strptime(short_time.group(1), "%H:%M")
            return parsed.strftime("%I:%M %p").lstrip("0")
        except Exception:
            return short_time.group(1)

    return value

def display_hole_value(value):
    value = clean_status_text(value)
    if not value:
        return "—"
    if re.search(r"\d{4}-\d{2}-\d{2}T", value) or re.search(r"\d{1,2}:\d{2}", value):
        return format_tee_time(value)
    return value

def strip_thru_prefix(value):
    """Remove a leading 'Thru ' so we don't double-label in the standings card."""
    if not value:
        return value
    return re.sub(r"^\s*thru\s+", "", str(value), flags=re.IGNORECASE).strip()

def extract_hole_or_tee_time(competitor):
    tee_time_keys = ["teeTime", "teeTimeDisplay", "startTime", "displayTime"]

    for key in tee_time_keys:
        value = clean_status_text(competitor.get(key))
        if value:
            return format_tee_time(value)

    # Check status first — if the golfer is finished, return "F"
    state_val = get_status_state(competitor)
    if state_val == "post":
        return "F"

    play_status_keys = ["thru", "thruStatus", "currentHole", "currentHoleNumber", "hole"]

    for key in play_status_keys:
        value = clean_status_text(competitor.get(key))
        if value:
            return display_hole_value(value)

    status = competitor.get("status")
    if isinstance(status, dict):
        for key in ["displayValue", "detail", "shortDetail", "description"]:
            value = clean_status_text(status.get(key))
            if value:
                return display_hole_value(value)

        status_type = status.get("type")
        if isinstance(status_type, dict):
            for key in ["detail", "shortDetail", "description", "name"]:
                value = clean_status_text(status_type.get(key))
                if value:
                    return display_hole_value(value)

    linescores = competitor.get("linescores")
    if isinstance(linescores, list) and linescores:
        latest = linescores[-1]
        if isinstance(latest, dict):
            for key in ["thru", "thruStatus", "currentHole", "displayValue", "value"]:
                value = clean_status_text(latest.get(key))
                if value and value not in ["--"]:
                    return display_hole_value(value)

    return "—"

def fetch_live_scores_from_espn():
    resp = requests.get(ESPN_LEADERBOARD_URL, timeout=12)
    resp.raise_for_status()
    payload = resp.json()

    results = {}
    for competitor in extract_competitors(payload):
        raw_name = extract_athlete_name(competitor)
        matched_name = PLAYER_NAME_LOOKUP.get(normalize_player_match_name(raw_name))
        if not matched_name:
            continue

        score = str(extract_score_value(competitor)).strip()
        if score in ["", "--", "-"]:
            score = "N/A"

        hole_or_tee = extract_hole_or_tee_time(competitor)

        results[matched_name] = {
            "score": score,
            "hole": hole_or_tee,
        }

    return results

def refresh_scores():
    try:
        live_results = fetch_live_scores_from_espn()
    except Exception as e:
        st.error(f"Could not refresh scores from ESPN: {e}")
        return False

    if not live_results:
        st.error("ESPN did not return matching player scores yet.")
        return False

    def mutator(state):
        state["player_results"] = live_results
        state["last_score_refresh_at"] = time.time()
        return True

    result, _ = mutate_shared_state(mutator, "Refresh scores")
    if result:
        st.success(f"Scores refreshed for {len(live_results)} golfers.")
        time.sleep(0.5)
        st.rerun()
    return bool(result)

def render_refresh_scores_button(key):
    st.markdown("<div class='refresh-button-wrap'>", unsafe_allow_html=True)
    clicked = st.button("Refresh Scores", key=key, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if clicked:
        refresh_scores()

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
            st.warning(f"{display_player_name(golfer)} has already been drafted.")
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
    result = PLAYER_RESULTS.get(player, {"score": "N/A", "hole": "—"})
    return {
        "score": result.get("score", "N/A"),
        "hole": display_hole_value(result.get("hole", "—")),
    }

def parse_golf_score(score):
    if score is None:
        return None
    score_text = str(score).strip().upper().replace("−", "-")
    if score_text in ["", "N/A", "—", "-", "WD", "CUT", "DQ"]:
        return None
    if score_text in ["E", "EVEN"]:
        return 0
    # Guard against stroke totals leaking through (any bare unsigned integer)
    if re.fullmatch(r"\d{2,3}", score_text):
        return None
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
    return {player for _, _, player, _ in get_sorted_scored_players(players)[:3]}

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
    return (-probability, last_name_key(golfer), golfer.lower())

def render_pick_timer(start_time):
    if not start_time:
        start_time = time.time()
    start_ms = int(start_time * 1000)
    components.html(f"""
    <div style="background:#000;color:#fff;font-family:Arial,sans-serif;margin:0;padding:0;">
        <div style="font-size:1.6rem;font-weight:800;line-height:1.35;">
            ⏱️ <span id="draft-clock">00:00:00</span>
        </div>
    </div>
    <script>
    const startMs = {start_ms};
    function pad(value) {{ return String(value).padStart(2, "0"); }}
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
    """, height=45)

if "confirm_clear_rosters" not in st.session_state:
    st.session_state.confirm_clear_rosters = False

state, state_sha = load_state_from_github()
state = normalize_state(state)
teams_data = state["teams"]
draft_order = state["draft_order"]
PLAYER_RESULTS = state.get("player_results", {})
picks = derive_picks_from_state(state)
picked_golfers = get_picked_golfers(state)
current_pick = get_current_pick(state)

st_autorefresh(interval=5000, limit=None, key="shared_state_refresh")

st.markdown(
    f"<div class='app-title'>{app_logo_html()}<h1>2026 PGA Championship</h1></div>",
    unsafe_allow_html=True,
)
st.caption("**May 14–17, 2026** • Aronimink Golf Club")

st.subheader("Standings")

for coach_id, info in teams_data.items():
    team_name = info.get("team_name", coach_id)
    color = COACH_COLORS.get(coach_id, "#555555")
    players = info.get("players", [])
    total = get_team_total(players)
    scored_players = get_sorted_scored_players(players)[:3]
    face_html = coach_image_html(coach_id)

    if scored_players:
        top3_html = ""
        for score_value, _, player, result in scored_players:
            safe_player = html.escape(display_player_name(player))
            score = html.escape(format_golf_score(score_value))
            raw_hole = display_hole_value(result.get("hole", "—"))
            hole_text = strip_thru_prefix(raw_hole)
            is_tee = "AM" in raw_hole.upper() or "PM" in raw_hole.upper()
            if hole_text.upper() == "F":
                status_text = "Final"
            else:
                label = "Tee" if is_tee else "Thru"
                status_text = f"{label} {hole_text}"
            top3_html += (
                f"<div style='margin:4px 0; color:{color}; font-size:1.05rem;'>"
                f"{safe_player} <span style='font-weight:700;'>({score})</span> {html.escape(status_text)}"
                f"</div>"
            )
    elif players:
        top3_html = "<div style='color:#aaa; font-style:italic;'>No live scores yet</div>"
    else:
        top3_html = "<div style='color:#aaa; font-style:italic;'>No golfers drafted yet</div>"

    safe_total = html.escape(total)
    card = (
        f"<div style='border:5px solid {color}; background-color:{color}18; border-radius:16px; "
        f"padding:20px 24px; margin-bottom:1.8rem; box-shadow:0 4px 15px rgba(255,255,255,.08);'>"
        f"<div class='team-heading' style='color:{color}; font-size:1.75rem; font-weight:800;'>"
        f"{face_html}<span>{html.escape(team_name)}</span>"
        f"<span style='display:inline-flex; align-items:center; justify-content:center; "
        f"width:3.9rem; height:3.9rem; margin-left:10px; border-radius:50%; "
        f"background:{color}; color:#000; font-size:2.1875rem; font-weight:800; "
        f"line-height:1;'>{safe_total}</span></div>"
        f"<div style='line-height:1.5;'>{top3_html}</div>"
        f"</div>"
    )
    st.markdown(card, unsafe_allow_html=True)

render_refresh_scores_button("refresh_scores_top")

st.subheader("Team Rosters")

team_cols = st.columns(3)

for idx, (coach_id, info) in enumerate(teams_data.items()):
    with team_cols[idx]:
        team_name = info.get("team_name", coach_id)
        players = info.get("players", [])
        color = COACH_COLORS.get(coach_id, "#555555")
        face_html = coach_image_html(coach_id)
        total = get_team_total(players)
        safe_total = html.escape(total)
        top_three_lowest_score_players = get_top_three_lowest_score_players(players)

        roster_parts = [
            f"<div style='border:5px solid {color}; background-color:{color}18; border-radius:16px; padding:20px 24px; margin-bottom:1.8rem;'>",
            f"<div class='team-heading' style='color:{color}; font-size:1.75rem; font-weight:800; margin-bottom:18px;'>"
            f"{face_html}<span>{html.escape(team_name)}</span>"
            f"<span style='display:inline-flex; align-items:center; justify-content:center; "
            f"width:3.9rem; height:3.9rem; margin-left:10px; border-radius:50%; "
            f"background:{color}; color:#000; font-size:2.1875rem; font-weight:800; "
            f"line-height:1;'>{safe_total}</span></div>",
        ]

        if not players:
            roster_parts.append("<div style='color:#aaa; font-style:italic;'>No golfers drafted yet</div>")
        else:
            roster_parts.append("<table class='roster-table'><thead><tr><th>Golfer</th><th>Score</th><th>Hole</th></tr></thead><tbody>")
            for player in players:
                safe_player = html.escape(display_player_name(player))
                result = get_player_result(player)
                score = html.escape(str(result.get("score", "N/A")))
                hole = html.escape(display_hole_value(result.get("hole", "—")))
                row_class = " class='roster-top-three'" if player in top_three_lowest_score_players else ""
                roster_parts.append(f"<tr{row_class}><td>{safe_player}</td><td>{score}</td><td>{hole}</td></tr>")
            roster_parts.append("</tbody></table>")

        roster_parts.append("</div>")
        st.markdown("".join(roster_parts), unsafe_allow_html=True)

render_refresh_scores_button("refresh_scores_middle")

with st.expander("🎯 DRAFT SECTION", expanded=state["draft_enabled"]):
    if not state["draft_enabled"]:
        st.error("🚫 Draft is currently DISABLED in Admin section")
    else:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("▶️ Start Draft", type="primary", disabled=state["draft_active"] or current_pick > MAX_PICKS, use_container_width=True):
                result, _ = start_draft()
                if result:
                    st.rerun()

        with col2:
            if st.button("⏹️ Stop Draft", disabled=not state["draft_active"], use_container_width=True):
                result, _ = stop_draft()
                if result:
                    st.rerun()

        with col3:
            if st.button("↩️ Undo Last Pick", disabled=not picks, use_container_width=True):
                result, _ = undo_last_pick()
                if result:
                    undone_pick_num, undone_coach, undone_golfer = result
                    st.success(f"Undid Pick #{undone_pick_num}: {display_player_name(undone_golfer)}. {undone_coach} is back on the clock.")
                    time.sleep(0.5)
                    st.rerun()

        if current_pick > MAX_PICKS:
            st.success("🎉 Draft Complete! All 30 picks are in.")
        elif state["draft_active"]:
            current_coach = get_coach_for_pick(current_pick, draft_order)
            st.markdown(f"## 🔥 CURRENT PICK: **{current_coach}** — Pick #{current_pick}")
            render_pick_timer(state.get("last_pick_started_at", 0))
        else:
            current_coach = get_coach_for_pick(current_pick, draft_order)
            st.markdown(
                f"<div class='draft-stopped-note'>Draft stopped. {html.escape(current_coach)} is next at Pick #{current_pick}. "
                f"Start the draft to resume picking.</div>",
                unsafe_allow_html=True,
            )

        st.subheader("Draft Dashboard")

        grid_html = """
        <style>
        @keyframes flash { 0% { background-color:#ffeb3b; } 50% { background-color:#fff59d; } 100% { background-color:#ffeb3b; } }
        .draft-table { width:100%; border-collapse:collapse; font-size:.95rem; background:#000; color:#fff; }
        .draft-table th, .draft-table td { border:1px solid #555; padding:10px; text-align:center; }
        .draft-table th { background-color:#1f1f1f; color:#fff; }
        .current-cell { animation:flash 1.2s infinite; font-weight:bold; }
        .stopped-cell { background-color:#333; color:#aaa; font-weight:bold; }
        </style>
        <table class="draft-table"><tr><th>Round</th>
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

                picked_golfer = next((pick[2] for pick in picks if pick[0] == pick_num), None)
                is_current = pick_num == current_pick

                if picked_golfer:
                    cell = html.escape(display_player_name(picked_golfer))
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
        st.caption("Sorted by odds, then last name. On phones, the list stays in true top-to-bottom order.")

        sorted_players = sorted(PGA_PLAYERS, key=odds_sort_key)
        available = [golfer for golfer in sorted_players if golfer not in picked_golfers]

        for row_start in range(0, len(available), 3):
            row_cols = st.columns(3)
            row_players = available[row_start:row_start + 3]

            for col_idx, golfer in enumerate(row_players):
                with row_cols[col_idx]:
                    odds_label = golfer_odds_label(golfer)
                    disabled = not state["draft_active"] or current_pick > MAX_PICKS

                    if st.button(f"✅ {display_player_name(golfer)} {odds_label}", key=f"pick_{golfer}", disabled=disabled, use_container_width=True):
                        with st.spinner(f"Saving {display_player_name(golfer)}..."):
                            result, _ = make_draft_pick(golfer)
                            if result:
                                st.rerun()

with st.expander("🔧 Admin Section", expanded=False):
    st.subheader("Draft Control")

    enable = st.toggle("Enable Draft", value=state["draft_enabled"], key="enable_toggle")

    if enable != state["draft_enabled"]:
        result, _ = set_draft_enabled(enable)
        st.session_state.confirm_clear_rosters = False
        if result:
            st.rerun()

    if state["draft_enabled"]:
        if not st.session_state.confirm_clear_rosters:
            if st.button("🛑 Reset Draft & Clear Roster", type="secondary", use_container_width=True):
                st.session_state.confirm_clear_rosters = True
                st.rerun()
        else:
            st.warning("⚠️ This will permanently clear ALL rosters and reset the draft.")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ YES, CLEAR EVERYTHING", type="primary", use_container_width=True):
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
            first_pick = st.selectbox("1st Pick", options=coaches, index=coaches.index(current_order[0]) if current_order[0] in coaches else 0, key="draft_order_first")
        with order_col2:
            second_pick = st.selectbox("2nd Pick", options=coaches, index=coaches.index(current_order[1]) if current_order[1] in coaches else 1, key="draft_order_second")
        with order_col3:
            third_pick = st.selectbox("3rd Pick", options=coaches, index=coaches.index(current_order[2]) if current_order[2] in coaches else 2, key="draft_order_third")

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
        new_name = st.text_input("Team Name", value=info.get("team_name", coach_id), key=f"name_{coach_id}")
        new_names[coach_id] = new_name

    if st.button("💾 Save Team Names"):
        result, _ = save_team_names(new_names)
        if result:
            st.success("Team names saved!")
            st.rerun()
        else:
            st.error("Team names were not saved. Please try again.")

st.caption("2026 PGA Championship Draft Challenge • Laborously Built by Jayme Leita • No AI Used")
