# mta_fetcher.py
# ─────────────────────────────────────────────────────────────────────────────
# Handles fetching the GTFS-realtime protobuf feed from the MTA API and
# parsing it into structured departure data using the nyct-gtfs library.
#
# Key GTFS-realtime concepts:
#   FeedMessage   → the top-level protobuf container
#   FeedEntity    → one "entity" = either a trip update OR a vehicle position
#   TripUpdate    → a train's schedule: which stops it'll hit and when
#   StopTimeUpdate→ one stop within a TripUpdate (arrival + departure time)
#   TripDescriptor→ identifies the trip: route, direction, start time, etc.
# ─────────────────────────────────────────────────────────────────────────────

import requests
import datetime
import pytz
from nyct_gtfs import NYCTFeed         # High-level wrapper around the protobuf feed

from config import MTA_API_KEY, FEED_URLS, LOOKAHEAD_MINUTES

# MTA operates in Eastern time
EASTERN = pytz.timezone("US/Eastern")


def fetch_feed(feed_key: str) -> NYCTFeed:
    """
    Download the GTFS-realtime protobuf feed for the given feed key
    and return a parsed NYCTFeed object.

    Args:
        feed_key: one of the keys in config.FEED_URLS (e.g. "bdfm")

    Returns:
        NYCTFeed object with all current trip updates loaded

    Raises:
        ValueError: if feed_key is not found in FEED_URLS
        requests.HTTPError: if the MTA API returns a non-200 status
    """
    if feed_key not in FEED_URLS:
        raise ValueError(f"Unknown feed key '{feed_key}'. "
                         f"Valid keys: {list(FEED_URLS.keys())}")

    url = FEED_URLS[feed_key]

    # The MTA requires an API key in the header (not query param)
    headers = {"x-api-key": MTA_API_KEY}

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()   # throws if HTTP 4xx / 5xx

    # NYCTFeed.load_from_bytes() parses the raw protobuf binary
    feed = NYCTFeed.load_from_bytes(response.content)
    return feed


def get_departures(feed: NYCTFeed, line_config: dict) -> dict:
    """
    Extract upcoming departure times from a parsed feed for a specific line.

    Returns a nested dict:
        {
          direction: {          # "N" or "S"
            stop_id: [          # base stop ID (no N/S suffix)
              datetime, ...     # sorted upcoming departure datetimes (Eastern)
            ]
          }
        }

    Args:
        feed       : NYCTFeed object from fetch_feed()
        line_config: one entry from config.LINE_CONFIGS (dict)
    """
    line_id = line_config["line_id"]
    config_stop_ids = {s[0] for s in line_config["stops"]}  # set for O(1) lookup

    now = datetime.datetime.now(tz=EASTERN)
    cutoff = now + datetime.timedelta(minutes=LOOKAHEAD_MINUTES)

    # Initialize result structure: direction → stop_id → list of times
    departures = {"N": {}, "S": {}}
    for stop_id in config_stop_ids:
        departures["N"][stop_id] = []
        departures["S"][stop_id] = []

    # Iterate over every trip in the feed
    for trip in feed.trips:
        # Filter to only the line we care about (e.g. "M")
        if trip.route_id != line_id:
            continue

        # nyct-gtfs exposes direction as "N" or "S" on the trip object
        direction = trip.direction   # "N" = Manhattan-bound, "S" = outer-borough

        # Each trip has a list of stop_time_updates: the stops it will visit
        for stop_time in trip.stop_time_updates:
            # stop_time.stop_id looks like "F18N" or "F18S" — strip the suffix
            base_stop_id = stop_time.stop_id.rstrip("NS")

            if base_stop_id not in config_stop_ids:
                continue   # this stop isn't in our configured stop list

            # Prefer departure time; fall back to arrival if departure is missing
            # GTFS timestamps are Unix epoch seconds (UTC), stored as integers
            raw_time = stop_time.departure or stop_time.arrival
            if raw_time is None:
                continue

            # Convert Unix timestamp → timezone-aware Eastern datetime
            dt = datetime.datetime.fromtimestamp(int(raw_time), tz=EASTERN)

            # Only include trains departing in the future and within our window
            if now <= dt <= cutoff:
                departures[direction][base_stop_id].append(dt)

    # Sort each stop's times chronologically
    for direction in departures:
        for stop_id in departures[direction]:
            departures[direction][stop_id].sort()

    return departures


def minutes_until(dt: datetime.datetime) -> int:
    """Return whole minutes from now until dt (Eastern). Can be 0 if imminent."""
    now = datetime.datetime.now(tz=EASTERN)
    delta = dt - now
    return max(0, int(delta.total_seconds() // 60))


def format_time(dt: datetime.datetime) -> str:
    """Format a datetime as h:MM AM/PM in Eastern time."""
    return dt.strftime("%-I:%M%p").lower()   # e.g. "3:07pm"
