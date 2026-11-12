# Precompute taxon key lookup for the master endangered species list
# by matching against a local GBIF backbone dump (Taxon.tsv) — no network calls.
# One-time script — re-run if data/master_species_list.csv or Taxon.tsv is updated.
#
# Usage (from project root):  python scripts/taxon_lookup.py
#
# Inputs : data/master_species_list.csv  (Common Name, Scientific Name, Status, State)
#          data/Taxon.tsv                 (GBIF backbone taxonomy dump)
# Output : data/MasterTaxonLookup.csv     (same columns + Taxon Key)

import csv
import pathlib
import re
import sys

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
INPUT_MASTER_CSV = str(DATA_DIR / "master_species_list.csv")
TAXON_TSV_PATH = str(DATA_DIR / "Taxon.tsv")
OUTPUT_CSV = str(DATA_DIR / "MasterTaxonLookup.csv")

REQUIRED_COLUMNS = ["Common Name", "Scientific Name", "Status", "State"]

# Taxon.tsv can have very long free-text fields (taxonRemarks, etc.)
csv.field_size_limit(sys.maxsize)

_PAREN_ALT_RE = re.compile(r"\(=[^)]*\)")           # strips "(=AltGenus)" style tokens
_RANK_MARKER_RE = re.compile(r"\b(?:var|subsp|ssp|f)\.\s+")  # drops rank markers
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_candidates(raw_name: str) -> list[str]:
    """
    Turn a master-list Scientific Name into 1-2 candidate strings formatted
    the way GBIF's canonicalName column is (no authorship, no rank markers,
    no alternate-genus parentheticals), most specific first.
    """
    name = (raw_name or "").strip()
    if not name:
        return []

    name = _PAREN_ALT_RE.sub("", name)
    name = _RANK_MARKER_RE.sub("", name)
    name = _WHITESPACE_RE.sub(" ", name).strip()

    if not name:
        return []

    candidates = [name]
    parts = name.split(" ")
    if len(parts) > 2:
        binomial = " ".join(parts[:2])
        if binomial not in candidates:
            candidates.append(binomial)  # fallback if infraspecific epithet isn't in GBIF

    return candidates


def load_rows(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED_COLUMNS if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Master list missing column(s) {missing}. Found: {reader.fieldnames}")
        for row in reader:
            if (row.get("Scientific Name") or "").strip():
                rows.append(row)
    return rows


def build_target_names(rows: list[dict]) -> set[str]:
    """Lowercased normalized candidate strings we need to find in Taxon.tsv."""
    targets = set()
    for row in rows:
        for cand in normalize_candidates(row["Scientific Name"]):
            targets.add(cand.lower())
    return targets


def scan_taxon_tsv(tsv_path: str, target_lower_names: set[str]) -> dict[str, dict]:
    """
    Single streaming pass over the (potentially huge) GBIF backbone Taxon.tsv.
    Returns: lowercased canonicalName -> {"resolved_id": str, "status": str}

    Accepted rows always win. A synonym is only kept if nothing better has
    been seen yet for that name, and resolves to its acceptedNameUsageID
    (falling back to its own taxonID if that's blank).
    """
    best: dict[str, dict] = {}

    with open(tsv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            canonical = (row.get("canonicalName") or "").strip().lower()
            if not canonical or canonical not in target_lower_names:
                continue

            status = (row.get("taxonomicStatus") or "").strip().lower()
            taxon_id = (row.get("taxonID") or "").strip()
            accepted_id = (row.get("acceptedNameUsageID") or "").strip()

            existing = best.get(canonical)

            if status == "accepted":
                best[canonical] = {"resolved_id": taxon_id, "status": status}
            elif existing is None:
                best[canonical] = {"resolved_id": accepted_id or taxon_id, "status": status}

    return best


def resolve_row_taxon_key(row: dict, matches: dict[str, dict]) -> str:
    for cand in normalize_candidates(row["Scientific Name"]):
        m = matches.get(cand.lower())
        if m:
            return m["resolved_id"]
    return ""


def main():
    print(f"Loading rows from {INPUT_MASTER_CSV}...")
    rows = load_rows(INPUT_MASTER_CSV)
    print(f"Loaded {len(rows)} rows")

    target_names = build_target_names(rows)
    print(f"Built {len(target_names)} unique normalized name candidates to search for")

    print(f"Streaming {TAXON_TSV_PATH} (single pass, regardless of file size)...")
    matches = scan_taxon_tsv(TAXON_TSV_PATH, target_names)
    print(f"Found taxon matches for {len(matches)} of {len(target_names)} candidate names")

    print(f"Writing lookup CSV to {OUTPUT_CSV}...")
    matched_count = 0
    unmatched = []
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS + ["Taxon Key"])
        writer.writeheader()
        for row in rows:
            taxon_key = resolve_row_taxon_key(row, matches)
            if taxon_key:
                matched_count += 1
            else:
                unmatched.append(row["Scientific Name"])
            writer.writerow({
                "Common Name": row.get("Common Name", "").strip(),
                "Scientific Name": row["Scientific Name"].strip(),
                "Status": row.get("Status", "").strip(),
                "State": row.get("State", "").strip(),
                "Taxon Key": taxon_key,
            })

    print(f"Matched {matched_count} / {len(rows)} rows")
    if unmatched:
        print(f"Unmatched ({len(unmatched)} unique names, printed once each):")
        for name in sorted(set(unmatched)):
            print(f"  - {name}")

    print("Done.")


if __name__ == "__main__":
    main()
