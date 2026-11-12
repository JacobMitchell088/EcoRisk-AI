# Data

This folder holds the species data behind EcoRisk AI's protected-species check, and the state boundary shapefile used to work out which state(s) a search area touches.

```
data/state_lists/  ──create_master_list.py──▶  master_species_list.csv  ──taxon_lookup.py──▶  MasterTaxonLookup.csv
(one or more CSVs per state + federal)                                      (+ Taxon.tsv from GBIF)
```

| Path | What it is | In git? |
|---|---|---|
| `state_lists/` | Raw endangered/threatened lists, one or more CSVs per state, plus the federal (FWS) list. Every source has its own column names. | Yes |
| `master_species_list.csv` | All of the above standardized into one file: `Common Name, Scientific Name, Status, State`. Federal rows use `State` = `All`. | Yes |
| `MasterTaxonLookup.csv` | `master_species_list.csv` plus a `Taxon Key` column (the GBIF ID). **This is the only species file the app reads** (see `GBIF.py`). | Yes |
| `Taxon.tsv` | GBIF's backbone taxonomy dump. Only needed to rebuild `MasterTaxonLookup.csv`. | **No** (too large) |
| `cb_2022_us_state_20m/` | Census Bureau state boundary shapefile used by `scripts/state_lookup.py`. Geometry only, unrelated to the species pipeline. | See the main [README](../README.md#requirements) |

You only need to follow this guide to refresh or extend the species data. To just run the app, `MasterTaxonLookup.csv` is already checked in.

---

## Rebuilding the data

All commands run from the **project root**, with the project's Python environment active (see the main [README](../README.md#requirements)).

### 1. Collect the state lists (outside this repo)

Scrape or download each state's endangered/threatened list, plus the federal list, and put the CSVs in `data/state_lists/`.

> The scrapers we used to produce these files are not included in this repo, so this step is manual for now.

### 2. Download the GBIF backbone

Download the **GBIF Backbone Taxonomy** from [gbif.org](https://www.gbif.org/dataset/d7dddbf4-2cf0-4f39-9b2a-bb099caae36c), unzip it, and place `Taxon.tsv` in `data/`. It is several GB, which is why it isn't committed.

### 3. Build the master list

```
python scripts/create_master_list.py
```

Reads every file listed in the script, standardizes the columns, keeps only rows whose status maps to **Endangered** or **Threatened**, and writes `data/master_species_list.csv`. Along the way it:

- drops rows with **no common name** (habitat/area entries such as "Devil's Icebox Recharge Area", not real species)
- removes **duplicate rows for the same species and state** (several source lists repeat a species once per county)

It prints how many rows each step removed.

> **Warning: expect a little stray data.** The state lists come from scrapers that aren't perfect, so the master list can contain a few rows that aren't real species or have mangled text (for example, a common name with a stray comma or quote that splits a row). You can find and fix the obvious ones by hand in `master_species_list.csv`, but leaving them in does little harm: a row that doesn't match a real GBIF species just gets no taxon key in step 4 and is ignored by scans. Re-running step 3 overwrites any manual edits, so do cleanup after it.

### 4. Build the taxon lookup

```
python scripts/taxon_lookup.py
```

Matches each scientific name in `master_species_list.csv` against `data/Taxon.tsv` (no network calls) and writes `data/MasterTaxonLookup.csv`, the same columns plus `Taxon Key`. It prints how many rows matched and lists every scientific name it couldn't match. Unmatched rows are written with a blank key, and the app skips those.

Commit the updated `master_species_list.csv` and `MasterTaxonLookup.csv`.

---

## Adding a state or list

1. Put the CSV in `data/state_lists/`. Use the exact filename, since paths are case-sensitive on Linux.
2. In `scripts/create_master_list.py`, copy an existing block and fill in:
   - `input_file`: the path to your CSV
   - `common_name_column`, `scientific_name_column`: that file's column names
   - `status_column`: the column holding the listing status
   - `state`: the state's full name (e.g. `"Illinois"`), or `"All"` for federal
3. Append the result with `all_species.append(...)`.
4. Re-run steps 3 and 4 above.

Status values are standardized by `normalize_status` in `scripts/normalize_func.py`. Labels like `E`, `LE`, `SE`, `Endangered` and `T`, `LT`, `ST`, `Threatened` are recognized. Anything else (candidate, special concern, rare, and so on) is dropped. If a new list uses an unusual label, add it there.

---

## Known issues and open items

- `state_lists/Indiana_anim.csv` is not used. Its scientific names have the spaces stripped (`Megachileintegra`), so none of them could match GBIF. It needs a corrected export.
- `state_lists/missouri.csv` is not used. It's the full county list, and the file the script does use (`missouri_threatened_endangered.csv`) contains exactly its endangered rows.
- Only states present in `MasterTaxonLookup.csv` can be flagged. For a state with no list, sightings still count toward the total species figure, but nothing there is marked protected.
- Listings are matched at the species level. GBIF often reports a species where a state lists a subspecies or variety, in which case the species-level sighting is used.
