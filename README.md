# 2026 PGA Championship Draft Challenge

This repository contains a Streamlit application for running a 3-person golf draft challenge around a selected PGA tournament. The app combines live ESPN leaderboard data, a draft board, persistent shared state stored in GitHub, and optional group text alerts powered by Twilio.

The current codebase is centered in [app.py](/Users/theleitas/Documents/Codex/2026-05-14/github-plugin-github-openai-curated-inspect/app.py). There is no separate backend service. Streamlit renders the UI, ESPN provides live golf data, GitHub stores shared state, and Twilio is used for SMS notifications.

## What This App Does

At a high level, the app supports:

- A 3-team snake draft for golfers.
- Persistent shared rosters and settings across sessions.
- A tournament selector so the app can be reused for future PGA events.
- Live scoring pulled from ESPN.
- Standings based on each team’s best 3 golfers.
- Full roster views including all 10 golfers per team.
- A tournament leaderboard for the selected event.
- Optional group text alerts for score-driven events.
- Admin controls for draft state, tournament targeting, and team naming.

## Core Product Model

The app is built around three human teams:

- `Jayme Leita`
- `Spencer Tidwell`
- `Peter Miller`

Each team drafts up to 10 golfers, for a total of 30 picks. The draft order is configurable and uses a snake format:

- Round 1 goes left to right.
- Round 2 reverses.
- The pattern repeats through 10 rounds.

The scoring model has two separate uses:

- Team standings are based on each roster’s lowest 3 golfer scores.
- Roster cards also display a `Total 10 Net Score`, which sums all scored golfers on that roster.

## Main Screens and Modules

### Header

The app header is tournament-aware. Once a tournament is selected in Admin:

- The title updates to the selected tournament title.
- The subtitle shows date range and location.
- The selected tournament becomes the score source for the whole app.

### Standings

The `Standings` section is the primary competitive summary.

Each standings card includes:

- Team image
- Team name
- Team color
- Circular score badge for the team total
- The current top 3 scoring golfers on that roster

The standings total is calculated from the team’s best 3 golfers only.

For each top-3 golfer, the card can show:

- Name with flag
- Current to-par score
- Hole / status text such as `Thru 14`, a tee time, `Final`, or `MC`
- Recent hole outcome symbols for the current round, only if that golfer is actively playing today

Recent hole outcome symbols use this language:

- `P` = par
- `○` = birdie or better
- `□` = bogey or worse

Only the most recent 5 holes are shown, and only for golfers whose round is currently underway.

### Team Rosters

The `Team Rosters` section shows all golfers drafted by each team.

Each roster card includes:

- Same team color and photo identity as the standings card
- Same circular team total badge
- A table of all drafted golfers
- Each golfer’s current score
- Each golfer’s current hole / status
- Highlighting for golfers currently counted in the top-3 team total
- A bottom-line `Total 10 Net Score`

### Tournament Leaderboard

The `Tournament Leaderboard` section displays the top 20 golfers for the selected event.

It includes:

- Tournament logo / title / location
- Rank
- Owner indicator if a roster contains that golfer
- Golfer name
- Score
- Hole / status

Owner indicator behavior:

- If a golfer belongs to one of the three teams, that row shows a small circular owner photo.
- The owner photo border uses the owning team’s color.
- If no team owns the golfer, the owner column is blank.

Golfer names in this section also include a clickable `ⓘ` info icon that links to the golfer’s ESPN player page.

### Draft Section

The `Draft Section` is collapsible and becomes the operational control center during the draft.

It includes:

- Start Draft
- Stop Draft
- Undo Last Pick
- Draft status messaging
- Current pick owner
- Current pick number
- A live on-clock timer
- Draft dashboard grid
- Available golfer selection area

#### Draft Dashboard

The draft dashboard is a visual 10-round snake board.

Behavior:

- Completed picks show the drafted golfer name.
- The active pick cell flashes.
- A stopped pick cell shows where the draft will resume.

#### Available Golfers

The draftable golfer list is optimized for mobile performance.

Features:

- Sorted by static odds, then last name
- Search input
- Pagination
- Button-based drafting

This was intentionally built to avoid rendering the entire golfer pool as buttons on every rerun.

## Admin Section

The `Admin Section` controls the app’s configuration and operational state.

### Tournament Selection

This is one of the most important future-proofing features in the app.

It allows the admin to choose:

- The current PGA tournament
- The next 10 PGA tournaments after it

Each option shows:

- Date
- Tournament name
- Location

Behavior:

- The saved tournament becomes the app-wide active tournament.
- ESPN score fetching targets that event.
- The title and leaderboard headers update to match.
- Roster data is preserved when switching tournaments.
- Score caches and score-derived state are reset so old event data does not bleed into the new one.
- A confirmation step is required before saving the tournament change.

Completed tournaments are removed from the selection list after they are in the past.

### Draft Control

Admin draft controls include:

- `Enable Draft` toggle
- `Reset Draft & Clear Roster`
- performance debug toggle

Important behavior:

- Resetting the draft is destructive and has a confirmation step.
- Reset clears rosters and draft progress.
- Reset is separate from tournament switching.

### Draft Order

Admin can edit:

- 1st pick owner
- 2nd pick owner
- 3rd pick owner

Rules:

- All three slots must be unique.
- The draft must be disabled before changing the order.

### Edit Team Names

Admin can rename team display names without changing the underlying coach identity keys.

## Text Updates Module

The `Text Updates` expander provides optional SMS notifications for the group.

Texts are always sent to the configured group recipients, never to only one owner for a live alert.

### Recipient Management

Each of the three people has:

- an on/off toggle
- a saved phone number

These numbers are persisted in shared state so they survive reruns and future sessions.

### Twilio Configuration

The UI intentionally does not expose raw Twilio credentials for editing.

Instead, the app expects Twilio settings to be provided through Streamlit secrets:

- account SID
- auth token
- from number

The UI contains a reminder message for this.

### Supported Alert Types

Each alert type has:

- an on/off toggle
- an editable message template

Current alert types:

- Tee Off Updates
- Birdie Updates
- Bogey Updates
- Lead Change
- Top 3 Golfer Change

### Test Message

The module also supports a `Send TEST MESSAGE` action. The admin chooses one of:

- Peter
- Jayme
- Spencer

This is meant to validate Twilio configuration plus saved phone numbers.

## Live Data and Refresh Model

### ESPN Data Sources

The app pulls live golf data from ESPN APIs.

Current uses include:

- event leaderboard
- tournament metadata
- PGA schedule / calendar
- competitor summary for hole-by-hole recent outcomes

### Refresh Behavior

There are two score refresh paths:

- Manual refresh via the `Refresh Scores` buttons
- Automatic refresh every 5 minutes

The app also uses a lightweight `st_autorefresh` every 5 seconds so the shared state stays current in the UI.

The actual ESPN score pull is throttled separately using:

- `AUTO_SCORE_REFRESH_SECONDS = 5 * 60`

The refresh buttons display:

- `Refresh Scores (Last Update: HH:MM)`

using 24-hour time.

### Golfer Status Logic

The app normalizes golfer state into user-friendly values.

Examples:

- tee times are shown as times only
- completed rounds show `Final`
- missed cut shows `MC`
- active rounds show `Thru X`

This status logic is reused across standings, rosters, and leaderboard displays.

## State and Persistence

Shared app state is stored in GitHub in:

- [`draft_state.json`](/Users/theleitas/Documents/Codex/2026-05-14/github-plugin-github-openai-curated-inspect/draft_state.json)

State is loaded and saved through the GitHub Contents API.

The save path includes optimistic retry behavior:

- load current remote state
- apply mutation
- save back with SHA
- retry on conflict

This is the main persistence model for:

- draft enabled / active state
- draft order
- team names
- team rosters
- selected tournament
- latest player results
- hole outcome history
- last refresh timestamps
- text update settings

## Visual and Graphics Language

This app has a very specific visual identity worth preserving if another program is going to borrow from it.

### Overall Theme

- Black background
- White base text
- Bright, high-contrast accent buttons
- Bold sports-style presentation
- Large circular score badges
- Minimal card rounding
- Strong team color coding

### Team Identity System

Each team has:

- a color
- a circular face image
- a display name

Current coach colors:

- Jayme Leita: `#00cc77`
- Spencer Tidwell: `#bb77ff`
- Peter Miller: `#8ECFFF`

These colors drive:

- card borders
- card glows / tinting
- owner image borders
- score badge backgrounds
- text accents

### Repeated Graphics Motifs

The app consistently uses:

- circular portraits
- circular score badges
- bordered dark cards
- simple tables with bright header contrast
- a golf logo in title and leaderboard header

### Interaction Styling

Buttons are intentionally loud and legible:

- dark default buttons
- bright orange refresh buttons
- yellow focus ring
- larger mobile tap areas

### Mobile Considerations

The current code includes explicit mobile-aware behavior:

- columns collapse to full width on narrow screens
- button heights increase on mobile
- available golfer list is paginated
- text scales down slightly on smaller viewports

## Draft Rules and Logic Details

This is the behavior another implementation should preserve.

### Pick Count

- 3 teams
- 10 rounds
- 30 total picks

### Snake Logic

The active owner for a pick is determined by:

- left-to-right order on odd rounds
- reversed order on even rounds

### Validations

- Draft cannot proceed when disabled.
- Draft picks cannot be made when stopped.
- Already drafted golfers cannot be picked again.
- Draft order cannot contain duplicates.
- Draft order cannot be edited while the draft is enabled.

### Undo

Undo removes the last valid pick and puts the draft back into an active state with that team back on the clock.

## Architecture Notes for Reimplementation

If you are using this app as the model for another program, these are the key design patterns to preserve.

### Keep the Shared State Central

The app works because draft state, scores, tournament selection, and notification settings all converge into a single persisted state model.

### Separate Configuration from Competition State

There is a useful distinction between:

- long-lived configuration
  - team names
  - phone numbers
  - selected tournament
  - draft order
- live competition state
  - rosters
  - current scores
  - last refresh times
  - hole outcomes
  - SMS event memory

### Treat Tournament Selection as a First-Class Mode Switch

Changing tournaments updates the entire app context without destroying roster state. That separation is an important product decision.

### Preserve the Visual Hierarchy

The competitive UX depends on:

- standings first
- team rosters second
- tournament leaderboard third
- draft controls tucked into an expander
- admin controls gated behind another expander

That hierarchy makes the app feel like a live contest board first and an admin tool second.

## Local Files

Main files in this repository:

- [app.py](/Users/theleitas/Documents/Codex/2026-05-14/github-plugin-github-openai-curated-inspect/app.py): main Streamlit app
- [draft_state.json](/Users/theleitas/Documents/Codex/2026-05-14/github-plugin-github-openai-curated-inspect/draft_state.json): shared persisted state
- [teams.json](/Users/theleitas/Documents/Codex/2026-05-14/github-plugin-github-openai-curated-inspect/teams.json): small static data file
- [requirements.txt](/Users/theleitas/Documents/Codex/2026-05-14/github-plugin-github-openai-curated-inspect/requirements.txt): Python dependencies
- player image assets and golf logo assets in repo root

## Requirements

Current Python dependencies listed in [`requirements.txt`](/Users/theleitas/Documents/Codex/2026-05-14/github-plugin-github-openai-curated-inspect/requirements.txt):

- `streamlit`
- `requests`
- `pandas`
- `streamlit-autorefresh`
- `plotly`
- `openai`

Not every listed package is central to the current visible feature set, but these are the declared dependencies in the repository.

## Streamlit Secrets

The code expects secrets for GitHub persistence and, optionally, Twilio.

A representative `secrets.toml` shape is:

```toml
[GITHUB]
TOKEN = "your_github_personal_access_token"

TWILIO_ACCOUNT_SID = "your_twilio_account_sid"
TWILIO_AUTH_TOKEN = "your_twilio_auth_token"
TWILIO_FROM_NUMBER = "+15555555555"
```

GitHub is required for shared-state persistence. Twilio is only required if text updates are enabled and used.

## Running the App

Typical local run:

```bash
streamlit run app.py
```

If secrets are missing:

- GitHub-backed shared state will not function correctly
- Twilio texting will fail

## Suggested Areas to Capture for a Future Rewrite

If another system is going to be built from this app, the most important reusable ideas are:

- 3-player snake draft engine
- tournament-aware mode switching
- team-top-3 scoring model
- full-roster total-10 secondary metric
- live golf status normalization
- team identity graphics system
- shared-state persistence abstraction
- admin confirmation flows for destructive actions
- templated text alert engine tied to score events

