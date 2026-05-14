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
    "Peter Miller": "#2E47DB",
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
    "Nico Echavarria": "🇨🇴", "Alex Fitzpatrick": "🇬���", "Matt Fitzpatrick": "🇬🇧",
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

# Updated function to prevent redundant "thru thru" issue
def display_hole_value(value):
    value = clean_status_text(value)
    if not value:
        return "—"
    if re.search(r"\d{4}-\d{2}-\d{2}T", value) or re.search(r"\d{1,2}:\d{2}", value):
        return format_tee_time(value)
    if value.lower().startswith("thru"):
        return value.capitalize()
    return value
