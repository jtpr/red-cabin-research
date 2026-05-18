# 🚇 MTA ASCII Train Timing Board

A real-time MTA subway departure board rendered as ASCII art in your terminal or browser.  
Built around the M train, but designed to support any subway line with a one-config change.

```
═══════════════════════════════════════════════════════════════════════
  [M] MTA REAL-TIME DEPARTURES    3:42 PM
═══════════════════════════════════════════════════════════════════════

  ROUTE MAP  (● = train arriving ≤2 min)
  Middle   Fresh    Forest  Woodhav  Elderts  Cypress  Crescent  ...
  Village  Pond Rd  Ave     Blvd     La       Hills
  ●────────○────────○────────○────────○────────○────────○────...

  ▶ Manhattan-bound / Forest Hills
  ──────────────────────────────────────────────────────────────────
  Middle Village       │  now  8m  16m
  Fresh Pond Rd        │  2m   9m  17m
  Forest Ave           │  3m   11m
  Myrtle Ave           │  6m   13m
  Times Sq-42 St       │  14m  22m
```

---

## Setup

### 1. Get an MTA API Key

Go to https://api.mta.info/#/signup and create a free account.  
Copy your API key — you'll need it in the next step.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

**Option A — edit `config.py`** (simple, but don't commit this to git):
```python
MTA_API_KEY = "your_actual_key_here"
```

**Option B — environment variable** (safer for sharing/git):
```bash
export MTA_API_KEY="your_actual_key_here"
```
The notebook reads this automatically in Cell 1.

### 4. Launch the notebook

```bash
jupyter notebook mta_timing.ipynb
```

Then run the cells in order:
- **Cell 1** — Setup (run once)
- **Cell 2** — Choose a line (set `ACTIVE_LINE = "M"`)
- **Cell 3** — One-shot fetch (good for testing)
- **Cell 4** — Live terminal refresh loop
- **Cell 5** — Live HTML preview inside the notebook
- **Cell 6** — Save `index.html` snapshot (for Neocities upload)
- **Cell 7** — Continuous HTML export loop

---

## Config Options (`config.py`)

| Option | Default | What it does |
|---|---|---|
| `MTA_API_KEY` | `"YOUR_API_KEY_HERE"` | Your MTA API key |
| `REFRESH_INTERVAL_SECONDS` | `30` | How often the live loop re-fetches |
| `LOOKAHEAD_MINUTES` | `45` | How far ahead to show departures |
| `MAX_TRAINS_PER_DIRECTION` | `5` | Max trains shown per direction |
| `MAX_TIMES_PER_STATION` | `3` | Max departure times per stop row |
| `BOARD_WIDTH` | `80` | ASCII board width in characters |
| `USE_COLOR` | `True` | ANSI colors in terminal (disable if broken) |
| `STOP_NAME_TRUNCATE` | `10` | Max chars for stop names in the map row |

---

## How to Add a New Subway Line

Everything is driven by `config.py`. You only need to add an entry to `LINE_CONFIGS`.

### Step 1: Find the feed

Look up your line in `FEED_URLS`:

| Lines | Feed key |
|---|---|
| A, C, E | `"ace"` |
| B, D, F, M | `"bdfm"` |
| G | `"g"` |
| J, Z | `"jz"` |
| N, Q, R, W | `"nqrw"` |
| L | `"l"` |
| 1, 2, 3, 4, 5, 6, 7 | `"1234567"` |
| Staten Island Railway | `"si"` |

### Step 2: Find the stop IDs

Download the MTA's static GTFS feed from:  
https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip

Open `stops.txt`. Each stop has a `stop_id` (e.g. `"A32"`) and a `stop_name`.  
Stop IDs ending in `N` or `S` are direction-specific — use the **base ID** (strip the suffix).

Alternatively, the nyct-gtfs repo has stop lists:  
https://github.com/Andrew-Dickinson/nyct-gtfs

### Step 3: Add the config entry

```python
"L": {
    "feed": "l",
    "line_id": "L",             # must match the route_id in the GTFS feed
    "color": "\033[90m",        # ANSI code for terminal color (optional)
    "directions": {
        "N": "8 Av-bound",      # human label for the N direction
        "S": "Canarsie-bound",  # human label for the S direction
    },
    "stops": [
        # List stops in N-direction order (outer borough → Manhattan)
        # Format: [base_stop_id, display_name]
        ["L29", "Canarsie–Rockaway Pkwy"],
        ["L28", "East 105 St"],
        # ... add all stops ...
        ["L01", "8 Av"],
    ],
},
```

### Step 4: Switch to the new line in the notebook

In Cell 2, change:
```python
ACTIVE_LINE = "L"
```

That's it. No other code changes needed.

---

## Hosting on Neocities

### One-time upload (static snapshot)

1. Run **Cell 6** in the notebook → saves `index.html` locally
2. Go to https://neocities.org → your dashboard → Files
3. Upload `index.html`
4. Your page is live at `https://yoursite.neocities.org`

The page has `<meta http-equiv="refresh" content="30">` which reloads the browser every 30 seconds, but it only shows data from the last time you uploaded.

### Keeping it updated (CLI approach)

Install the Neocities CLI:
```bash
npm install -g neocities
neocities login
```

Then run **Cell 7** (the export loop), and separately in a terminal:
```bash
# Upload every 60 seconds
while true; do
  neocities push index.html
  sleep 60
done
```

Or wrap both steps in a shell script for convenience.

### Truly live data (advanced)

For genuinely live data without manual re-uploads, options include:
- Run the Python script on a VPS (DigitalOcean, Railway, etc.) and serve it there
- Use GitHub Actions on a schedule to fetch + commit `index.html`, then deploy to Neocities via the neocities CLI in a workflow
- Host locally and use a tunnel (ngrok, Cloudflare Tunnel) to expose it publicly

---

## Project Structure

```
mta-ascii/
├── mta_timing.ipynb     # Main notebook — start here
├── config.py            # All settings and line configs
├── mta_fetcher.py       # GTFS feed fetching + parsing
├── ascii_renderer.py    # Terminal + HTML rendering
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

### Adding the rendering to a standalone script

If you prefer a plain `.py` file over Jupyter:

```python
# run.py
import config, mta_fetcher, ascii_renderer

line_config = config.LINE_CONFIGS["M"]
feed        = mta_fetcher.fetch_feed(line_config["feed"])
departures  = mta_fetcher.get_departures(feed, line_config)
ascii_renderer.render_terminal(departures, line_config)
```

```bash
python run.py
```

---

## Troubleshooting

**`401 Unauthorized`** — Your API key is wrong or not set. Double-check `config.py`.

**`No trains found`** — The M train doesn't run on weekends. Try a different line, or check the time (late nights have reduced service). Also verify `LOOKAHEAD_MINUTES` in config.

**Colors look broken** — Set `USE_COLOR = False` in `config.py`.

**Stop times seem off** — MTA GTFS times are in Unix epoch UTC. The code converts them to US/Eastern automatically via `pytz`. If something is off, check that your system clock is correct.

**`ModuleNotFoundError: nyct_gtfs`** — Run `pip install -r requirements.txt` again.

---

## Data Sources

- MTA GTFS-Realtime feeds: https://api.mta.info/#/subwayRealTimeFeeds
- GTFS-Realtime spec: https://gtfs.org/documentation/realtime/reference/
- nyct-gtfs Python library: https://github.com/Andrew-Dickinson/nyct-gtfs
- MTA static GTFS (stop IDs): https://rrgtfsfeeds.s3.amazonaws.com/gtfs_subway.zip
