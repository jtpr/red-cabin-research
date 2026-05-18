# config.py
# ─────────────────────────────────────────────────────────────────────────────
# Central configuration for the MTA ASCII timing board.
# To add a new subway line, add an entry to LINE_CONFIGS below.
# Nothing else in the codebase needs to change.
# ─────────────────────────────────────────────────────────────────────────────

# ── API ───────────────────────────────────────────────────────────────────────
# Get a free key at https://api.mta.info/#/signup
# Set this to your actual key, or put it in an environment variable (see main notebook).
MTA_API_KEY = "YOUR_API_KEY_HERE"

# How often (in seconds) to refresh the feed when running in a loop
REFRESH_INTERVAL_SECONDS = 30

# How many minutes ahead to show departures
LOOKAHEAD_MINUTES = 45

# ── GTFS Feed URLs ────────────────────────────────────────────────────────────
# Each feed covers a group of lines. Full list:
# https://api.mta.info/#/subwayRealTimeFeeds
FEED_URLS = {
    "ace":    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "bdfm":   "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "g":      "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "jz":     "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "nqrw":   "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "l":      "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "1234567":"https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "si":     "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
}

# ── Line Configurations ───────────────────────────────────────────────────────
# Each entry defines one subway line's display settings.
#
# Keys:
#   feed        : which feed key (from FEED_URLS) carries this line's data
#   line_id     : the route_id string used in the GTFS feed (usually the letter/number)
#   color       : ANSI color code for terminal display (optional, cosmetic only)
#   directions  : dict mapping GTFS direction codes → human-readable labels
#                 MTA uses "N" (northbound/Manhattan-bound) and "S" (southbound/outer-borough)
#   stops       : ordered list of [stop_id, display_name] pairs for ONE direction.
#                 Use the "N"-direction stop IDs (northbound/Manhattan-bound).
#                 The renderer will show trains moving through these stops.
#                 Stop IDs come from the MTA's GTFS static feed stops.txt.
#                 Tip: stop IDs for direction N end in "N", S ends in "S".
#                      The base ID (no suffix) works for matching in nyct-gtfs.

LINE_CONFIGS = {

    # ── M Train ───────────────────────────────────────────────────────────────
    # Runs: Middle Village–Metropolitan Av  ↔  Forest Hills–71 Av
    # On weekdays only (no M train on weekends)
    # Feed: BDFM
    "M": {
        "feed": "bdfm",
        "line_id": "M",
        "color": "\033[33m",        # Orange/amber (close to the real M orange)
        "directions": {
            "N": "Manhattan-bound / Forest Hills",   # toward Forest Hills / Manhattan
            "S": "Middle Village-bound",             # toward Middle Village–Metropolitan Av
        },
        # Stops listed outer-borough → Manhattan (N direction order)
        # Each entry: [GTFS stop base ID, short display name]
        # Full stop list: https://github.com/Andrew-Dickinson/nyct-gtfs or MTA stops.txt
        "stops": [
            ["F18", "Middle Village"],   # Middle Village–Metropolitan Av (M terminus)
            ["F16", "Fresh Pond Rd"],
            ["F15", "Forest Ave"],
            ["F14", "Woodhaven Blvd"],
            ["F13", "Elderts La"],
            ["F12", "Cypress Hills"],
            ["F11", "Crescent St"],
            ["F09", "Myrtle Ave"],       # shared with J/Z
            ["M16", "Kosciuszko St"],
            ["M14", "Myrtle-Wyckoff"],
            ["M13", "Seneca Ave"],
            ["M12", "Forest Hills 71"],  # Forest Hills–71 Av (shared E/F/M/R)
            ["M11", "67 Ave"],
            ["M10", "63 Dr"],
            ["M09", "Woodhaven Blvd"],   # Queens-side
            ["M08", "Grand Ave"],
            ["M06", "Elmhurst Ave"],
            ["M05", "Jackson Hts"],
            ["M04", "46 St"],
            ["M03", "Woodside"],
            ["M01", "Hunters Pt Ave"],
            # Manhattan stops
            ["D14", "Court Sq"],
            ["F20", "21 St"],
            ["F21", "Queensboro Plaza"],
            ["B08", "Lexington Av/59"],
            ["B06", "57 St"],
            ["B04", "49 St"],
            ["B03", "Times Sq"],
            ["B02", "34 St Herald"],
            ["B01", "28 St"],
            ["A30", "23 St"],
            ["A31", "14 St"],
            ["A32", "Essex St"],
            ["A33", "Delancey St"],
            ["A34", "Broadway-Lafayette"],
            ["A36", "W 4 St"],
            ["A38", "Canal St"],
            ["A41", "Chambers St"],
            ["A42", "Fulton St"],
            ["A43", "Broad St"],
        ],
    },

    # ── F Train (example of how to add another line) ──────────────────────────
    # Uncomment to enable. Same feed as M (bdfm).
    # "F": {
    #     "feed": "bdfm",
    #     "line_id": "F",
    #     "color": "\033[95m",   # Orange
    #     "directions": {
    #         "N": "Manhattan / Bronx-bound",
    #         "S": "Coney Island-bound",
    #     },
    #     "stops": [
    #         # Add F train stop IDs here in N-direction order
    #         # ["F18", "Jamaica-179 St"], ...
    #     ],
    # },

    # ── L Train (example of a different feed) ────────────────────────────────
    # "L": {
    #     "feed": "l",
    #     "line_id": "L",
    #     "color": "\033[90m",   # Dark gray
    #     "directions": {
    #         "N": "8 Av-bound",
    #         "S": "Canarsie-bound",
    #     },
    #     "stops": [
    #         # ["L29", "Canarsie"], ...
    #     ],
    # },
}

# ── Display Settings ──────────────────────────────────────────────────────────
# Max number of upcoming trains to show per direction
MAX_TRAINS_PER_DIRECTION = 5

# Max number of departure times to show per station row
MAX_TIMES_PER_STATION = 3

# Width of the ASCII board in characters
BOARD_WIDTH = 80

# Whether to use ANSI colors in terminal output (set False if your terminal breaks)
USE_COLOR = True

# Stop name truncation length for the map display
STOP_NAME_TRUNCATE = 10
