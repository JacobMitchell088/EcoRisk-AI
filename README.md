# EcoRisk AI
> Authors: Jacob Mitchell, Hayden Shubert    
> Date: 9/22/26   

> Our servers spin down with inactivity, so please be sure to allow for an additional 60 seconds upon making your first request to our backend.    
https://environmentscreen.onrender.com     


This program is a prototype application designed to help construction planners identify potential environmental risks **before** beginning a project. The system analyzes biodiversity data from the **Global Biodiversity Information Facility (GBIF)** and cross references it with **state and federal endangered and threatened species lists** to identify protected species near a proposed construction site.    

This tool performs a **preliminary environmental screening** by checking for documented or sighted species occurrences within a specified geographic radius. Screenings are currently limited to sites within the **United States** — a location outside the US (e.g. across the Mexican or Canadian border, or over open water) is rejected before any lookup runs, since there's no species data to check against it.

---      

# Project Purpose

Construction projects may be delayed or halted if endangered or threatened species are present near a site. Currently, this review process often requires manual research across multiple datasets.       

Our program automates this first step by:    

1. Accepting a project location    
2. Searching GBIF biodiversity databases for species sightings    
3. Comparing detected species with state and federal endangered/threatened species lists for every state the search radius touches    
4. Returning flagged species that may impact a project plan   
5. Provide additional context to flagged species to user with additional information on how it may interact with their construction process     

This version focuses on the **data pipeline / detection logic / additional ecological analysis by OpenRouter api calls / frontend**     

---   

# System Workflow
### Precomputed
1. Build the multi-state endangered/threatened species dataset into `data/MasterTaxonLookup.csv` — one row per species per state it's listed in, plus a federal row (`State` = `All`) for species with federal protection
   - This file was generated locally in a separate project. The scripts that produce it (an update to `scripts/unfiltered_species.py` and `scripts/build_taxon_lookup.py`, or their replacements) will be added to this repo in a future commit — for now, `data/MasterTaxonLookup.csv` should be treated as a precomputed asset checked in on its own.
2. Download the Census Bureau's `cb_2022_us_state_20m` state boundary shapefile into `data/cb_2022_us_state_20m/` — this is geometry only (state outlines), not species data, and is used solely to answer "which state(s) is this point/circle in."

### User Interface
3. Supply an address or coordinates and a radius in miles (address search powered by MapTiler Geocoding API)
4. Check Redis cache — if a matching scan exists for the same location and radius, return the cached result immediately
5. Confirm the search center falls inside a US state (`state_lookup.state_containing_point`) — if not, the scan fails fast with a message asking the user to move the pin
6. Determine every state the search radius overlaps (`state_lookup.states_touching_circle`) — a site near a state line can pull in more than one state's list
7. Convert the radius from miles to meters for use in the GBIF query
8. Make a GBIF call using a `geoDistance` filter to return all species within the given radius (occurrences filtered to year 2000–2026)
9. Cross-check returned species against `data/MasterTaxonLookup.csv`, flagging a hit if it's federally listed (`All`) or listed in any state the search radius touches
10. Send batch request to OpenRouter for additional construction and species context, limited to the top `MAX_SPECIES_FOR_AI` species by sighting count (`.env`, default=3) — this only caps which species get AI context, not which species are detected or shown in the report
11. Store result in Redis cache (24-hour TTL)
12. Display the results as a report: a plain-language verdict, which states were searched, each flagged species (with the state(s) it's protected in and AI construction guidance where available), and a downloadable HTML report

---   

# Data Sources

## GBIF (Global Biodiversity Information Facility)
https://www.gbif.org   

Used for retrieving species occurrence records based on geographic location.   

GBIF API endpoints used:  

Occurrence Search  
https://api.gbif.org/v1/occurrence/search   

Species Name Matching  
- Only used during precomputed `MasterTaxonLookup.csv` build   
https://api.gbif.org/v1/species/match   

---   

## State & Federal Endangered Species Data
- Local CSV mapping each species to the state(s) it's listed as endangered/threatened in, with a separate row for a federal listing (`State` = `All`): `data/MasterTaxonLookup.csv`.
- This file was built locally in a separate project rather than from the scripts currently checked into this repo. The generation scripts will be added here in a future update.

Example structure:

`"Common Name","Scientific Name","Status","State","Taxon Key"`

**Example entries:**

- Yellow Mud Turtle, Kinosternon flavescens, Threatened, IL, 2442437
- Indiana Bat, Myotis sodalis, Endangered, All, 2435099

A species can appear on multiple rows — once per state it's listed in, plus possibly a federal row. The program precomputes taxon keys ahead of time so a scan doesn't need a GBIF name-lookup call per species.

---   

# Key Features

## Geocoding / Address Search
- The `/geocode/search` endpoint accepts a plain-text address and returns coordinates, powered by the **MapTiler Geocoding API**.
- `/geocode/reverse` accepts coordinates and returns a human-readable address label.
- Both endpoints are Redis-cached (24-hour TTL) to avoid duplicate lookups.

## Geometry based queries
- The search radius (in miles) is converted to meters and passed to GBIF's `geoDistance` parameter, giving a true circular search area instead of a square bounding-box approximation.

## US State Detection
- Before a scan runs, `state_lookup.py` checks whether the search center falls inside a US state boundary (Census Bureau `cb_2022_us_state_20m` shapefile). If the center point isn't inside any state, the scan fails before making any GBIF or OpenRouter calls.
- Separately, `state_lookup.py` finds every state the search *radius* overlaps — not just the state containing the center — so a site near a state line pulls in endangered species lists from both states, not just the one the pin happens to sit in.
- The report shows the abbreviated list of states searched (`input.states_searched`) next to the total species count, and each flagged species shows which state(s) (or **Federal**) it's protected in.

## Redis Caching
> Requires a running Redis instance. See [Environment Variables](#environment-variables) for setup.
- Scan results are cached by location and radius so repeated requests for the same area skip all GBIF and OpenRouter calls entirely.
    - Cache key: `scan:{lat}:{lon}:{radius}` — coordinates rounded to 3 decimal places (~111 m precision), radius rounded to 1 decimal place
    - Cache TTL: 24 hours
- Geocode and reverse-geocode responses are also cached in Redis (24-hour TTL) so address lookups aren't repeated unnecessarily.
- All Redis operations degrade gracefully — if Redis is unavailable, the app continues without caching and logs a `[REDIS ERROR]` message rather than crashing.
- In local development with Redis running (WSL2: `sudo service redis-server start`), cache hits will appear in the terminal as `[SCAN CACHE HIT]`.

## Bot Protection & API Security
> To prevent automated abuse of our environmental screening API, I've implemented human verification along with rate limiting.    
- Features Added:
    - Cloudflare Turnstile integration
        - Invisible / low friction human verification (no captchas)
        - Token generated on frontend then verified on backend
    - Backend token validation
        - All `/scan/start` requests now require a valid Turnstile token
    - Rate limiting
        - Limits applied per IP to prevent excessive calling abuse
    - CORS hardened
        - Restricted to approved frontend origin only
- How it works:
    - User submits scan request from frontend
    - Turnstile generates a verification token
    - Token is sent with the request to the backend
    - Backend validates token with Cloudflare
    - If valid proceed, if not reject

## Frontend Experience
> Designed for planners who are not technical. See [`frontend/README.md`](frontend/README.md) for implementation details and the design system.
- **Guided three-step flow:** the left panel walks users through *1. Choose your site*, *2. Set the search area*, and *3. Run the screening*. Only the current step is open; finished steps collapse to a summary with a **Change** link.
    - Sites can be set by address search, by latitude/longitude, or by clicking the map or dragging the pin. Pressing Enter in the address box searches for the address; it never starts a screening.
    - The search radius is set with a slider (1–50 miles) or quick presets (1, 2, 5, 10, 25 mi). **5 miles** is the default and is labeled Recommended.
- **Map:** MapTiler `dataviz-v4` tiles, a crosshair site marker, and a dashed search-radius circle labeled with its distance. While a screening runs, pulses radiate from the site and the circle's dashes move, and the map is locked (no panning, zooming, keyboard control, or pin dragging) until it finishes. The map re-frames the site when the screening starts.
    - The map always frames the whole search area, centered on the site, at every radius from 1 to 50 miles and at any panel width.
    - When the site changes (address, coordinates, map click, or dragging the pin), the circle fades out, the map flies to the new site, and the circle grows back in from the pin. Radius changes ease the circle and the zoom together so the circle never spills off the map.
    - A **Recenter on site** button appears under the zoom controls whenever the site is panned or zoomed out of frame. It re-frames the map without changing the screening location.
- **States searched / protected in:** the report shows the abbreviated states the search radius touched next to the protected species count, and each species card shows a small badge for every state (or **Federal**) it's protected in.
- **Report:** when a screening finishes, the panel switches to a report with a verdict ("3 protected species recorded nearby" or "No protected species recorded nearby"), key figures, whether the result was saved (cached) or live, and an expandable entry per species (Wikipedia photo, Wikipedia and GBIF links). The species with the most sightings also include AI-generated tags and construction guidance; species beyond the AI limit are marked "Not AI-reviewed" and link out to background reading instead.
    - **Download report** saves a styled, printable HTML report. It is available for clear results too, and all AI text is HTML-escaped.
- **Resizable panel:** on desktop, drag the grip on the panel's right edge to make it wider or narrower (or focus it and use the arrow keys; hold Shift for larger steps). Double-click the grip to reset. The steps and the report remember separate widths in the browser, so a report can be read wide without stretching the form. When the panel is wide, species guidance lays out in two columns. The map always keeps at least 360px.
- **Activity tray:** the bell in the header lists recent messages (address lookups, screenings, errors) with an unread count. Most messages also appear briefly as a toast in the bottom-right.
- **Info buttons:** the ⓘ buttons next to *Project address*, *Coordinates*, *Search radius*, *All species*, and *Saved result* explain each control in plain language. They close with Escape or a click elsewhere.
- **Cold-start screen:** if the backend is asleep, a full-screen notice shows elapsed time and explains that the service is waking up. It clears on its own once the backend responds.
- **Responsive:** on phones, the map sits above the panel and the page scrolls normally.

## In-App Feedback
- A **Feedback** button in the header opens a side panel, themed to match the rest of the UI.
- Users can submit a title, a body (what's good, bad, or wanted), an optional 1–5 star rating, and an optional contact email for a reply.
- Missing or invalid fields are flagged inline, and a draft is kept if the panel is closed without sending.
- Submissions are auto-populated into the repository's **GitHub Issues** (labeled `feedback`).
- The GitHub Personal Access Token is held **only on the backend** (`GITHUB_FEEDBACK_PAT`) — never shipped to the browser. The frontend posts to the `/feedback` endpoint, which calls the GitHub Issues API server-side.
- Like `/scan/start`, the endpoint is protected by **Cloudflare Turnstile** verification and a per-IP rate limit (5/hour) to prevent abuse.

## Precomputed species lookup
- Species names and their state/federal listing status are resolved to taxon keys ahead of time, so a scan doesn't need a per-species GBIF name-lookup call.

## Endangered species detection
- A species is only flagged as protected if it's listed federally, or listed in a state the search radius touches. Species GBIF returns that aren't listed anywhere applicable still count toward the total species figure, just not as protected.

## AI Ecological Context Analysis
- After endangered species are detected, our system will generate additional context using OpenRouter api to return more information to the user
- The module `open_router_context.py` analyzes each flagged species in a batch call with a max count being defined in the .env by the runner
- The AI analysis may include
    - Important ecological behaviors
    - Breeding / migration seasonal considerations
    - Construction activities that are deemed most disruptive
    - A cautious recommendation for when construction may be the least disruptive
- Example output:
```
Myotis sodalis

Indiana bats are particularly sensitive to disturbance during maternity
season when females form roosting colonies in trees. Construction
activities involving tree clearing, heavy noise, or nighttime lighting
during late spring and summer may disrupt these colonies. If possible,
major disturbance activities may be less disruptive outside the
maternity season, typically late fall through winter.    
```
- To ensure performance remains high and reduce costs, only the top `MAX_SPECIES_FOR_AI` detected species (ranked by sighting count) are sent to OpenRouter in a single batched request. All matched species are still returned and shown in the report — species beyond that limit are displayed without AI-generated guidance, alongside links to Wikipedia and GBIF.

---   

# Current Limitations
> [!WARNING]
> GBIF sightings may not always include subspecies names as seen on state endangered species lists

Example:   

GBIF may report:   
Tilia americana   

Illinois listing:   
Tilia americana var. heterophylla   

In these cases the species level occurrence is used   

> [!WARNING]
> Only species lists for the states currently included in `data/MasterTaxonLookup.csv` are checked. If a state hasn't been added to that file yet, GBIF sightings there still count toward the total species figure, but nothing in that state will be flagged as protected.

> [!WARNING]
> `data/MasterTaxonLookup.csv` was generated locally in a separate project. The build scripts that produce it are not yet part of this repo, so the file currently can't be regenerated from source here — it should be treated as a static precomputed asset until that tooling is added.

This tool is intended for **early stage environmental screening**, not regulatory compliance, as we **cannot guarantee** the absence of false positives or false negatives.

---   

# Project Structure

```
Senior-Project/
├── app.py                          # FastAPI application entry point
├── scan.py                         # Scan endpoint + background job runner
├── geocode.py                      # Geocode / reverse-geocode endpoints
├── GBIF.py                         # GBIF API interaction + species matching logic
├── openai_species_context.py       # OpenAI batch context analysis
├── open_router_context.py          # OpenRouter batch context analysis
├── redis_client.py                 # Redis wrapper (cache_get / cache_set / cache_delete)
├── limiter.py                      # SlowAPI rate limiter configuration
├── data/
│   ├── MasterTaxonLookup.csv       # Precomputed scientific name → taxon key → state(s) listed lookup ("All" = federally listed). Generated locally in a separate project — build scripts not yet in this repo.
│   └── cb_2022_us_state_20m/       # Census Bureau US state boundary shapefile, used by state_lookup.py (geometry only, not species data)
├── scripts/
│   ├── state_lookup.py                 # US state-boundary geometry: confirms the search center is inside a US state, and finds every state the search radius overlaps
│   └── build_taxon_lookup.py       # Legacy: regenerated the old Illinois-only taxon lookup. Superseded by MasterTaxonLookup.csv for scans; kept for reference until the multi-state build scripts are added.
├── frontend/                       # React + Vite frontend (see frontend/README.md)
│   ├── index.html                  # Fonts, Turnstile script, favicon
│   ├── public/favicon.svg          # EcoRisk AI mark
│   └── src/
│       ├── App.jsx                 # Guided steps, report, header, scan/geocode logic
│       ├── ScreeningMap.jsx        # Leaflet map, site marker, search-radius circle
│       ├── FeedbackWidget.jsx      # Feedback side panel
│       ├── ColdStartOverlay.jsx    # Backend wake-up screen
│       ├── index.css               # Design system and all styles
│       ├── components/             # ActivityTray, InfoTip, ScanProgress, SpeciesEntry, BrandMark, Icons
│       └── lib/                    # API helpers, formatting, report download, map framing, Turnstile + panel-width hooks
├── tests/
│   ├── test_scan.py
│   ├── test_geocode.py
│   ├── test_GBIF.py
│   ├── test_open_router_context.py
│   └── test_openai_species_context.py
├── .github/workflows/test.yml      # GitHub Actions CI workflow
├── conftest.py                     # Pytest fixtures (fakeredis autouse)
├── pytest.ini                      # Pytest configuration + custom markers
├── requirements.txt
├── requirements-dev.txt
├── environment.yml
└── .env.example
```

---

# Requirements

```
conda env create -f environment.yml
```

Or with pip directly:

```
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for development / testing
```

Before running scans locally, download the Census Bureau's [`cb_2022_us_state_20m`](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html) cartographic boundary shapefile and unzip it into `data/cb_2022_us_state_20m/`. `state_lookup.py` reads this file to determine which state(s) a point or search circle falls in — it isn't fetched at runtime.

You will also need `data/MasterTaxonLookup.csv` present locally to run a scan (see [Current Limitations](#current-limitations) — this file isn't yet buildable from scripts in this repo).

---

# Running the Prototype

Find our frontend here:
https://environmentscreen.onrender.com

To run the backend locally:
> Within conda GBIF_env (and with `.env` file keys / parameters set):
```
uvicorn app:app --reload
```

To run the frontend locally (Vite dev server, default port 5173):
```
cd frontend
npm install
npm run dev
```
> The frontend reads `VITE_API_BASE_URL`, `VITE_TURNSTILE_SITE_KEY`, and `VITE_MAPTILER_API_KEY` from `frontend/.env` (see `frontend/.env.example`). Add `?coldstart=1` to the URL to preview the cold-start screen. More in [`frontend/README.md`](frontend/README.md).

---

# Testing

The project uses **pytest** with **fakeredis** for test isolation — no real Redis server is required to run the tests.

```
pytest tests/
```

Custom markers are defined in `pytest.ini`:
- `integration` — tests that hit live external APIs. Skip with `-m "not integration"` (this is what CI runs).
- `slow` — marks slow-running tests.

A GitHub Actions CI workflow (`.github/workflows/test.yml`) runs the non-integration test suite automatically on every push and pull request to `main`.

---

# Environment Variables
- Our project uses environmental variables such as max species openai call count and of course our api key
    - These variables are automatically read by python SDK through vscode reading each members `.env` file
    - To configure or view format please see `.env.example` — this can be created with `cp .env.example .env` before adding your own keys / parameters.

| Variable | Description | Default |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI API key for ecological context analysis | — |
| `OPENROUTER_API_KEY` | OpenRouter API key for ecological context analysis | — |
| `MAX_SPECIES_FOR_AI` | Max species sent to OpenRouter per scan | `3` |
| `MAPTILER_API_KEY` | MapTiler API key for geocoding | — |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile secret for bot protection | — |
| `FRONTEND_ORIGIN` | Allowed CORS origin | `http://localhost:5173` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `GITHUB_FEEDBACK_PAT` | Fine-grained GitHub PAT used **server-side** to open feedback issues (scope: Issues → Read and write, on the target repo only) | — |
| `GITHUB_FEEDBACK_REPO` | Target repo for feedback issues, in `owner/repo` form | — |

> For Render.com deployments, set `REDIS_URL` to the **internal** Redis URL provided by your Render Redis service — `localhost` will not work in a hosted environment.

---

# Future Improvements

- Bring the `data/MasterTaxonLookup.csv` build scripts into this repo so the dataset can be regenerated and extended without relying on the separate local project it was built in
- Add remaining US states' endangered/threatened species data to `data/MasterTaxonLookup.csv` — multi-state screening logic is in place (`state_lookup.py`, `GBIF.py`), but coverage depends on which states are populated in that file
- Schedule daily/periodic runs of the (future) build scripts to keep `MasterTaxonLookup.csv` current
- Export construction timeline recommendations
- Improve AI ecological analysis using external species data sources (Wikipedia, species databases)

---   



### Disclaimer
- Our program provides **informational screening only**  
- Results should **always** be verified with environmental professionals and official regulatory databases before making construction decisions.    

---    

https://environmentscreen.onrender.com
