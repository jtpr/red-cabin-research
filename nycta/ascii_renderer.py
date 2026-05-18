# ascii_renderer.py
# ─────────────────────────────────────────────────────────────────────────────
# Renders MTA departure data as ASCII art in the terminal AND as styled HTML
# for hosting on Neocities (or any static host).
#
# Two output modes:
#   render_terminal()  → prints colored text directly to stdout
#   render_html()      → returns an HTML string with inline CSS (self-contained)
# ─────────────────────────────────────────────────────────────────────────────

import datetime
import pytz
from mta_fetcher import minutes_until, format_time
from config import (
    MAX_TRAINS_PER_DIRECTION,
    MAX_TIMES_PER_STATION,
    BOARD_WIDTH,
    USE_COLOR,
    STOP_NAME_TRUNCATE,
)

EASTERN = pytz.timezone("US/Eastern")

# ANSI color helpers (used in terminal mode only)
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
RED     = "\033[91m"
CYAN    = "\033[96m"
WHITE   = "\033[97m"
GRAY    = "\033[90m"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _color(text: str, code: str, use_color: bool = True) -> str:
    """Wrap text in an ANSI color code, or return plain text if color disabled."""
    if not use_color or not USE_COLOR:
        return text
    return f"{code}{text}{RESET}"


def _minutes_label(minutes: int) -> str:
    """Human label for countdown: 'now', '3m', '12m'."""
    if minutes == 0:
        return "now"
    return f"{minutes}m"


def _time_color(minutes: int) -> str:
    """Return ANSI color code based on urgency."""
    if minutes <= 2:
        return RED
    if minutes <= 5:
        return YELLOW
    return GREEN


def _truncate(name: str, length: int = STOP_NAME_TRUNCATE) -> str:
    """Shorten a stop name to fit the map display."""
    if len(name) <= length:
        return name
    return name[:length - 1] + "…"


# ── Map row (the ●───○───○ line) ──────────────────────────────────────────────

def _build_map_row(stops: list, active_stop_ids: set) -> str:
    """
    Build the ASCII track map:   ●────○────○────●────○
    ● = a stop with an imminent train (≤ 2 min)
    ○ = a normal upcoming stop
    The map always shows all configured stops left→right.

    Args:
        stops          : list of [stop_id, name] from line config
        active_stop_ids: set of stop_ids that have a train ≤ 2 min away
    """
    parts = []
    for i, (stop_id, _) in enumerate(stops):
        if stop_id in active_stop_ids:
            parts.append("●")
        else:
            parts.append("○")
        if i < len(stops) - 1:
            parts.append("────")
    return "".join(parts)


def _build_stop_header(stops: list) -> str:
    """
    Build a header row of (truncated) stop names, spaced to match the map row.
    Each stop occupies 1 char (the ●/○) + 4 chars (the ────) = 5 chars per segment.
    We center the name over the ●/○.
    """
    # Each stop node is at position: i * 5  (0, 5, 10, ...)
    # We'll print names vertically staggered (two rows) so they don't overlap.
    # Row A: even-indexed stops, Row B: odd-indexed stops
    row_a = [" "] * (len(stops) * 5)
    row_b = [" "] * (len(stops) * 5)

    for i, (_, name) in enumerate(stops):
        short = _truncate(name, 8)
        pos = i * 5
        target = row_a if i % 2 == 0 else row_b
        # Place name, truncating if it runs off the edge
        for j, ch in enumerate(short):
            if pos + j < len(target):
                target[pos + j] = ch

    return "".join(row_a).rstrip() + "\n" + "".join(row_b).rstrip()


# ── Departure table ───────────────────────────────────────────────────────────

def _build_departure_table(departures_for_direction: dict, stops: list,
                            use_color: bool = True) -> list[str]:
    """
    Build a list of text lines showing upcoming trains for one direction.

    Format per stop:
      Fulton St      │  3m  8m  14m
      Chambers St    │  4m  9m
      Canal St       │  now  6m

    Args:
        departures_for_direction : departures["N"] or departures["S"]
        stops                    : ordered list of [stop_id, name]
        use_color                : whether to apply ANSI colors
    """
    lines = []
    col_width = 18   # width of the stop name column

    for stop_id, stop_name in stops:
        times = departures_for_direction.get(stop_id, [])
        if not times:
            continue   # skip stops with no upcoming trains

        # Build the time labels for this stop
        time_labels = []
        for dt in times[:MAX_TIMES_PER_STATION]:
            mins = minutes_until(dt)
            label = _minutes_label(mins)
            if use_color and USE_COLOR:
                label = _color(label, _time_color(mins))
            time_labels.append(label)

        name_col = stop_name.ljust(col_width)[:col_width]
        times_str = "  ".join(time_labels)
        lines.append(f"  {name_col} │  {times_str}")

    return lines


# ── Terminal renderer ─────────────────────────────────────────────────────────

def render_terminal(departures: dict, line_config: dict):
    """
    Print the full ASCII timing board to stdout with ANSI colors.

    Args:
        departures  : output of mta_fetcher.get_departures()
        line_config : one entry from config.LINE_CONFIGS
    """
    line_id   = line_config["line_id"]
    line_color = line_config.get("color", WHITE)
    stops      = line_config["stops"]
    directions = line_config["directions"]

    now_str = datetime.datetime.now(tz=EASTERN).strftime("%I:%M %p").lstrip("0")

    sep = "═" * BOARD_WIDTH

    # ── Header ────────────────────────────────────────────────────────────────
    title = f"[{line_id}] MTA REAL-TIME DEPARTURES    {now_str}"
    print(_color(sep, line_color))
    print(_color(f"  {title}", line_color + BOLD))
    print(_color(sep, line_color))
    print()

    # ── Track map ─────────────────────────────────────────────────────────────
    # Collect stop_ids with a train arriving in ≤ 2 minutes (for all directions)
    active_ids = set()
    for direction in ["N", "S"]:
        for stop_id, times in departures[direction].items():
            if times and minutes_until(times[0]) <= 2:
                active_ids.add(stop_id)

    print(_color("  ROUTE MAP", GRAY))
    stop_header = _build_stop_header(stops)
    for line in stop_header.split("\n"):
        print(_color("  " + line, GRAY))
    map_row = _build_map_row(stops, active_ids)
    print(_color("  " + map_row, CYAN))
    print()

    # ── Departures per direction ───────────────────────────────────────────────
    for direction in ["N", "S"]:
        dir_label = directions.get(direction, direction)
        print(_color(f"  ▶ {dir_label}", line_color + BOLD))
        print(_color("  " + "─" * (BOARD_WIDTH - 2), GRAY))

        table_lines = _build_departure_table(
            departures[direction], stops, use_color=USE_COLOR
        )

        if not table_lines:
            print(_color("    No trains found in the next "
                         f"{LOOKAHEAD_MINUTES} minutes.", GRAY))
        else:
            for tl in table_lines:
                print(tl)

        print()

    print(_color(sep, line_color))
    print(_color(f"  Feed refreshes every 30s  •  ● = train arriving ≤2 min", GRAY))
    print(_color(sep, line_color))
    print()


# ── HTML renderer ─────────────────────────────────────────────────────────────

def render_html(departures: dict, line_config: dict) -> str:
    """
    Generate a self-contained HTML page styled to look like a terminal.
    Suitable for saving as index.html and uploading to Neocities.

    Returns the full HTML string.
    """
    line_id    = line_config["line_id"]
    stops      = line_config["stops"]
    directions = line_config["directions"]

    now_str = datetime.datetime.now(tz=EASTERN).strftime("%I:%M %p").lstrip("0")

    # ── Collect active stops (imminent trains) ────────────────────────────────
    active_ids = set()
    for direction in ["N", "S"]:
        for stop_id, times in departures[direction].items():
            if times and minutes_until(times[0]) <= 2:
                active_ids.add(stop_id)

    # ── Build map row HTML ────────────────────────────────────────────────────
    map_parts = []
    for i, (stop_id, name) in enumerate(stops):
        cls = "stop-active" if stop_id in active_ids else "stop-normal"
        symbol = "●" if stop_id in active_ids else "○"
        map_parts.append(
            f'<span class="{cls}" title="{name}">{symbol}</span>'
        )
        if i < len(stops) - 1:
            map_parts.append('<span class="track">────</span>')

    map_html = "".join(map_parts)

    # ── Build departure tables ─────────────────────────────────────────────────
    directions_html = ""
    for direction in ["N", "S"]:
        dir_label = directions.get(direction, direction)
        rows_html = ""

        for stop_id, stop_name in stops:
            times = departures[direction].get(stop_id, [])
            if not times:
                continue

            times_cells = ""
            for dt in times[:MAX_TIMES_PER_STATION]:
                mins = minutes_until(dt)
                label = _minutes_label(mins)
                wall  = format_time(dt)
                cls   = ("time-now" if mins <= 2
                         else "time-soon" if mins <= 5
                         else "time-ok")
                times_cells += (
                    f'<span class="time {cls}" title="{wall}">{label}</span>'
                )

            rows_html += (
                f'<tr>'
                f'<td class="stop-name">{stop_name}</td>'
                f'<td class="times">{times_cells}</td>'
                f'</tr>\n'
            )

        if not rows_html:
            rows_html = (
                f'<tr><td colspan="2" class="no-trains">'
                f'No trains in the next {LOOKAHEAD_MINUTES} min</td></tr>'
            )

        directions_html += f"""
        <div class="direction-block">
          <div class="dir-header">▶ {dir_label}</div>
          <table class="departure-table">
            <thead>
              <tr><th>Stop</th><th>Departures</th></tr>
            </thead>
            <tbody>
              {rows_html}
            </tbody>
          </table>
        </div>
"""

    # ── Full HTML ─────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="30">
  <title>[{line_id}] MTA Train Timing</title>
  <style>
    /* Terminal aesthetic */
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: #0d0d0d;
      color: #c8c8c8;
      font-family: 'Courier New', Courier, monospace;
      font-size: 14px;
      padding: 24px 16px;
      max-width: 860px;
      margin: 0 auto;
    }}

    .board {{
      border: 1px solid #333;
      padding: 20px;
    }}

    /* ── Header ── */
    .board-header {{
      color: #f4a623;        /* MTA orange */
      font-size: 1.1em;
      font-weight: bold;
      letter-spacing: 2px;
      border-bottom: 2px solid #f4a623;
      padding-bottom: 8px;
      margin-bottom: 16px;
    }}

    .timestamp {{
      color: #888;
      font-size: 0.85em;
      float: right;
      font-weight: normal;
      letter-spacing: 0;
    }}

    /* ── Route map ── */
    .map-section {{ margin-bottom: 24px; }}
    .map-label {{ color: #555; font-size: 0.8em; margin-bottom: 6px; }}

    .route-map {{
      overflow-x: auto;
      white-space: nowrap;
      padding: 4px 0;
      font-size: 0.95em;
    }}

    .stop-normal  {{ color: #5bc0de; cursor: default; }}
    .stop-active  {{ color: #f4a623; font-size: 1.1em; cursor: default; }}
    .track        {{ color: #334; }}

    /* ── Direction blocks ── */
    .direction-block {{
      margin-bottom: 20px;
    }}

    .dir-header {{
      color: #f4a623;
      font-weight: bold;
      margin-bottom: 6px;
      font-size: 0.95em;
    }}

    .departure-table {{
      width: 100%;
      border-collapse: collapse;
    }}

    .departure-table th {{
      color: #555;
      font-size: 0.8em;
      text-align: left;
      border-bottom: 1px solid #222;
      padding: 2px 8px 4px 4px;
    }}

    .departure-table td {{
      padding: 3px 8px 3px 4px;
      border-bottom: 1px solid #1a1a1a;
      vertical-align: middle;
    }}

    .stop-name {{
      color: #aaa;
      min-width: 160px;
    }}

    .times {{ white-space: nowrap; }}

    .time {{
      display: inline-block;
      min-width: 36px;
      text-align: center;
      padding: 1px 6px;
      border-radius: 3px;
      margin-right: 4px;
      font-weight: bold;
      font-size: 0.9em;
    }}

    .time-now  {{ color: #0d0d0d; background: #e53e3e; }}  /* red  — arriving now */
    .time-soon {{ color: #0d0d0d; background: #d69e2e; }}  /* amber — ≤5 min */
    .time-ok   {{ color: #276749; background: #9ae6b4; }}  /* green — comfortable */

    .no-trains {{ color: #444; font-style: italic; padding: 4px; }}

    /* ── Footer ── */
    .board-footer {{
      color: #333;
      font-size: 0.75em;
      border-top: 1px solid #1e1e1e;
      padding-top: 10px;
      margin-top: 10px;
    }}
  </style>
</head>
<body>
  <div class="board">

    <div class="board-header">
      [{line_id}] MTA REAL-TIME DEPARTURES
      <span class="timestamp">Updated {now_str}</span>
    </div>

    <div class="map-section">
      <div class="map-label">ROUTE MAP  (● = train arriving in ≤2 min)</div>
      <div class="route-map">{map_html}</div>
    </div>

    {directions_html}

    <div class="board-footer">
      Page auto-refreshes every 30 seconds &nbsp;•&nbsp;
      Data: MTA GTFS-Realtime &nbsp;•&nbsp;
      ● arriving ≤2m &nbsp; 🟡 ≤5m &nbsp; 🟢 comfortable
    </div>

  </div>
</body>
</html>"""

    return html
