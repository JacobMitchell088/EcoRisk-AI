import csv
import logging
import math
import pathlib
import requests
import time

from dotenv import load_dotenv
from scripts.state_lookup import states_touching_circle, state_containing_point
load_dotenv()
import os

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

GBIF_OCC_SEARCH = "https://api.gbif.org/v1/occurrence/search"
MAX_SPECIES = int(os.getenv("MAX_SPECIES_FOR_AI", 50))   # caps how many species get AI context (cost control)

DATA_DIR = pathlib.Path(__file__).parent / "data"
MASTER_TAXON_LOOKUP_PATH = DATA_DIR / "MasterTaxonLookup.csv"

FEDERAL_LABEL = "All"  # value used in the "State" column for federally-listed species


def miles_to_km(mi: float) -> float:
    return mi * 1.609344


def load_master_taxon_lookup(path: pathlib.Path) -> dict[int, list[dict]]:
    """
    Reads MasterTaxonLookup.csv and returns:
        taxon_key -> [ {"scientific_name", "common_name", "status", "state"}, ... ]

    A species can appear multiple times (once per state it's listed in, plus
    possibly a federal "All" row), so each taxon_key maps to a list of entries
    rather than a single one.
    """
    lookup: dict[int, list[dict]] = {}

    try:
        f_handle = open(path, newline="", encoding="utf-8")
    except FileNotFoundError:
        raise RuntimeError(
            f"Master taxon lookup CSV not found at '{path}'. "
            "Run scripts/build_taxon_lookup.py to generate it before running a scan."
        )
    except OSError as exc:
        raise RuntimeError(f"Could not open master taxon lookup CSV '{path}': {exc}") from exc

    with f_handle as f:
        reader = csv.DictReader(f)

        for row in reader:
            key_str = (row.get("Taxon Key") or "").strip()
            if not key_str:
                continue

            try:
                taxon_key = int(key_str)
            except ValueError:
                logger.warning("Skipping malformed taxon key in master lookup: %r", row)
                continue

            entry = {
                "scientific_name": (row.get("Scientific Name") or "").strip(),
                "common_name": (row.get("Common Name") or "").strip(),
                "status": (row.get("Status") or "").strip(),
                "state": (row.get("State") or "").strip(),
            }
            lookup.setdefault(taxon_key, []).append(entry)

    return lookup


def gbif_species_counts_in_area(lat: float, lon: float, radius_miles: float) -> list[tuple[int, int]]:
    """Facet search returning all (taxon_key, count) pairs within true circular radius."""
    radius_mtr = miles_to_km(radius_miles) * 1000

    params = {
        "geoDistance": f"{lat},{lon},{radius_mtr}",
        "hasCoordinate": "true",
        "year": "2000,2026",
        "facet": "speciesKey",
        "facetMincount": 1,
        "speciesKey.facetLimit": 10000,
        "limit": 0,
    }

    try:
        resp = requests.get(GBIF_OCC_SEARCH, params=params, timeout=120)
        resp.raise_for_status()
        j = resp.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("GBIF API request timed out. The service may be slow or unreachable.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to the GBIF API. Check network connectivity.")
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"GBIF API returned an error: HTTP {exc.response.status_code}") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"GBIF API request failed: {exc}") from exc

    facets = j.get("facets", [])
    if not facets:
        logger.warning("GBIF returned no facets for this bounding box — no species found")
        return []

    counts = facets[0].get("counts", [])
    return [(int(row["name"]), int(row["count"])) for row in counts if row.get("name")]


def run_scan(lat, lon, radius_miles, progress_callback=None):
    if progress_callback:
        progress_callback("Checking search location", 5)

    center_state = state_containing_point(lat, lon)
    if center_state is None:
        raise RuntimeError(
            "This location isn't inside a US state, so we don't have "
            "species data for it. Move the pin to a site within the "
            "United States and run the screening again."
        )

    if progress_callback:
        progress_callback("Determining states in search area", 10)

    touched_states = states_touching_circle(lat, lon, radius_miles)

    if not touched_states:
        raise RuntimeError("No US states found intersecting this search area.")

    touched_state_names = {s["state_name"] for s in touched_states}
    logger.info("Search area touches: %s", sorted(touched_state_names))

    if progress_callback:
        progress_callback("Querying GBIF species in area", 35)

    area_species = gbif_species_counts_in_area(lat, lon, radius_miles)
    total_species_count = len(area_species)

    if progress_callback:
        progress_callback("Cross-referencing endangered species list", 60)

    master_lookup = load_master_taxon_lookup(MASTER_TAXON_LOOKUP_PATH)

    # taxon_key -> {"scientific_name", "common_name", "gbif_count", "taxon_key", "states_endangered_in"}
    hits_by_taxon_key = {}

    for taxon_key, count in area_species:
        entries = master_lookup.get(taxon_key)
        if not entries:
            continue

        for entry in entries:
            state = entry["state"]
            if state != FEDERAL_LABEL and state not in touched_state_names:
                continue  # listed somewhere, but not federally and not in a touched state

            if taxon_key not in hits_by_taxon_key:
                hits_by_taxon_key[taxon_key] = {
                    "scientific_name": entry["scientific_name"],
                    "common_name": entry["common_name"],
                    "gbif_count": count,
                    "taxon_key": taxon_key,
                    "states_endangered_in": [],
                }

            label = "Federal" if state == FEDERAL_LABEL else state
            if label not in hits_by_taxon_key[taxon_key]["states_endangered_in"]:
                hits_by_taxon_key[taxon_key]["states_endangered_in"].append(label)

    hits = list(hits_by_taxon_key.values())
    hits.sort(key=lambda x: x["gbif_count"], reverse=True)

    found_species_count = len(hits)

    logger.info("Found %d protected species in search area", found_species_count)
    for h in hits:
        logger.info("  - %s / %s(%d occurrences) — endangered in: %s", h["scientific_name"], h["common_name"], h["gbif_count"], h["states_endangered_in"])

    if progress_callback:
        progress_callback("Generating AI ecological context", 85)

    # Only send the top MAX_SPECIES hits to the AI — each one is an OpenRouter call.
    ai_hits = hits[:MAX_SPECIES]

    from open_router_context import enrich_gbif_results_with_openrouter_batch

    gbif_result = {
        "input": {
            "lat": lat,
            "lon": lon,
            "radius_miles": radius_miles,
            "year_start": 2000,
            "year_end": 2026,
            "states_searched": [s["state_abbr"] for s in touched_states],
        },
        "hits": [
            {"scientific_name": h["scientific_name"], "common_name": h["common_name"], "gbif_count": h["gbif_count"], "taxon_key": h["taxon_key"]}
            for h in ai_hits
        ],
    }

    enriched = enrich_gbif_results_with_openrouter_batch(gbif_result, api_key=OPENROUTER_API_KEY)

    if progress_callback:
        progress_callback("Finalizing results", 100)

    return {
        "input": gbif_result["input"],
        "total_species_count": total_species_count,
        "found_species_count": found_species_count,
        "gbif_hits": hits,                             # full list, every hit carries states_endangered_in
        "species_context": enriched["species_context"], # AI writeups, only for the top MAX_SPECIES
    }


def main():
    lat, lon = 38.635, -90.179
    radius_miles = 5

    result = run_scan(lat, lon, radius_miles)

    print(f"\nSearch at {lat}, {lon} for endangered species with GBIF occurrences in ~{radius_miles} miles:\n")

    hits = result["gbif_hits"]

    if not hits:
        print("No matches found.")
        return

    print(f"{'Scientific Name':35} {'GBIF Count':>10} {'taxonKey':>10} {'States Endangered In':>20}")
    print("-" * 80)
    for item in hits:
        states_str = ", ".join(item["states_endangered_in"])
        print(
            f"{item['scientific_name'][:35]:35} "
            f"{item['gbif_count']:10d} "
            f"{item['taxon_key']:10d} "
            f"{states_str:20}"
        )

    print("\nAI Species Context:\n")
    for item in result["species_context"]:
        print(item["scientific_name"])
        print(f"Common name: {item['common_name']}")
        print(f"Tags: {', '.join(item.get('tags', []))}")
        print(f"Overview: {item.get('overview')}")
        print(f"Seasonal concerns: {item.get('seasonal_concerns')}")
        print(f"Disruptive activities: {item.get('disruptive_activities')}")
        print(f"Recommendation: {item.get('recommendation')}")
        print()


if __name__ == "__main__":
    main()
