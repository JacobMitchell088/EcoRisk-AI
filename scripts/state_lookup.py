"""
state_lookup.py

Answers one question: given a search circle (center point + radius),
which US states does that circle touch?

No GBIF calls happen here. This is pure geometry - comparing 
search circle's shape against the 50 state shapes. It never looks
at species or occurrence data.
"""

import logging
import pathlib

import geopandas as gpd
from shapely.geometry import Point

logger = logging.getLogger(__name__)

# Path to the shapefile you downloaded from Census.gov
STATES_SHP_PATH = pathlib.Path(__file__).parent / "data" / "cb_2022_us_state_20m" / "cb_2022_us_state_20m.shp"

# WGS84 = normal lat/lon coordinates (what GBIF and your users use)
WGS84_CRS = "EPSG:4326"

"""
Albers Equal Area = a flat, distance-accurate projection for the continental US.
We need this because measuring a "radius in miles" using plain lat/lon degrees
is inaccurate - degrees of longitude are shorter near the poles than at the
equator. Albers fixes that distortion so a 30-mile radius is an actual 30 miles
on the ground, not just "30 miles" in a stretched/squished coordinate system.
"""

ALBERS_CRS = "EPSG:5070"

# Cached in memory after first load, so we only read the file from disk once,
# no matter how many searches happen afterward.
_states_wgs84 = None
_states_albers = None


def load_states():
    """
    Loads the state boundary shapes into memory.

    Call this once when your app starts up (not on every search request) -
    reading the shapefile from disk takes a bit of time, but only needs
    to happen once per server run.
    """
    global _states_wgs84, _states_albers

    if _states_wgs84 is None:
        if not STATES_SHP_PATH.exists():
            raise RuntimeError(
                f"State boundary file not found at '{STATES_SHP_PATH}'. "
                "Download it from Census.gov and unzip it into the data/ folder."
            )

        logger.info("Loading US state boundaries from %s", STATES_SHP_PATH)
        gdf = gpd.read_file(STATES_SHP_PATH)

        # The Census file has lots of columns we don't need (land area, etc).
        # Keep just the name, abbreviation, and shape.
        gdf = gdf[["NAME", "STUSPS", "geometry"]].rename(
            columns={"NAME": "state_name", "STUSPS": "state_abbr"}
        )

        _states_wgs84 = gdf.set_crs(WGS84_CRS, allow_override=True)
        # Pre-convert to the accurate-distance projection once, up front, so every search afterward reuses this instead of re-converting.
        _states_albers = _states_wgs84.to_crs(ALBERS_CRS)

    return _states_wgs84, _states_albers


def states_touching_circle(lat: float, lon: float, radius_miles: float) -> list[dict]:
    """
    Given a search center (lat, lon) and a radius in miles, returns every
    state whose boundary overlaps that circle - even a little bit.

    Example: a search centered near the IL/MO border with a wide enough
    radius might return both Illinois and Missouri.

    Returns a list like:
        [{"state_name": "Illinois", "state_abbr": "IL"},
         {"state_name": "Missouri", "state_abbr": "MO"}]
    """
    _, states_albers = load_states()

    # Convert the user's search point into the accurate-distance projection
    center_point = (
        gpd.GeoSeries([Point(lon, lat)], crs=WGS84_CRS).to_crs(ALBERS_CRS).iloc[0]
    )

    radius_meters = radius_miles * 1609.34

    # .buffer() draws an actual circle of that radius around the point
    search_circle = center_point.buffer(radius_meters)

    """
    Ask: which state shapes overlap this circle at all?
    geopandas automatically uses a spatial index (R-tree) here under the
    hood, so this stays fast even though it's technically checking all
    50+ state shapes.
    """

    touching = states_albers[states_albers.intersects(search_circle)]

    return [
        {"state_name": row.state_name, "state_abbr": row.state_abbr}
        for row in touching.itertuples()
    ]

def state_containing_point(lat: float, lon: float) -> dict | None:
    """
    Returns the US state (or territory) that contains this exact point,
    or None if the point doesn't fall inside any of them.

    This is different from states_touching_circle: it ignores the search
    radius entirely and just asks "is the center point itself on US soil
    we have boundary data for?" Used as a gate before running a scan, so
    a pin dropped in Mexico, Canada, or open ocean fails fast instead of
    silently returning a "clean" result.
    """
    states_wgs84, _ = load_states()

    point = Point(lon, lat)
    containing = states_wgs84[states_wgs84.contains(point)]

    if containing.empty:
        return None

    row = containing.iloc[0]
    return {"state_name": row.state_name, "state_abbr": row.state_abbr}
