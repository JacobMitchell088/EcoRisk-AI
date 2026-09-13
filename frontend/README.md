# EcoRisk AI — Frontend

React 19 + Vite 7 single-page app for the EcoRisk AI screening tool. It guides a non-technical user through choosing a construction site, setting a search radius, running a screening, and reading the report.

Libraries: [Leaflet](https://leafletjs.com) via [react-leaflet](https://react-leaflet.js.org) for the map, [react-hot-toast](https://react-hot-toast.com) for toasts, and Cloudflare Turnstile for invisible human verification.

---

## Running

```
npm install
npm run dev       # dev server on http://localhost:5173
npm run build     # production build in dist/
npm run lint      # ESLint
```

### Environment variables

Copy `.env.example` to `.env` and fill in:

| Variable | Purpose |
|---|---|
| `VITE_API_BASE_URL` | Backend URL, e.g. `https://your-backend.onrender.com` (no trailing slash needed) |
| `VITE_TURNSTILE_SITE_KEY` | Cloudflare Turnstile site key |
| `VITE_MAPTILER_API_KEY` | MapTiler key for map tiles. If the key is restricted by origin, add `http://localhost:5173` for local work. |

These values are bundled into the browser build, so only put public keys here.

### Local testing tips

- Add `?coldstart=1` to the URL to force the cold-start screen open (it stays open until you remove the parameter).
- Cloudflare's always-pass test site key `1x00000000000000000000AA` is useful when working against a local or mocked backend. Variables set in the shell override `.env`, for example:
  ```
  VITE_API_BASE_URL=http://127.0.0.1:8000 VITE_TURNSTILE_SITE_KEY=1x00000000000000000000AA npm run dev
  ```
- The deployed backend only accepts requests from `FRONTEND_ORIGIN`, so a local frontend needs a local backend (or a backend whose `FRONTEND_ORIGIN` is `http://localhost:5173`).

---

## Structure

```
src/
├── main.jsx                 # Entry; loads Leaflet CSS before index.css so overrides win
├── App.jsx                  # Header, guided steps, report view, scan + geocode logic, notifications
├── ScreeningMap.jsx         # Leaflet map: tiles, bounds, site marker, Recenter on site button, resize handling
├── FeedbackWidget.jsx       # Feedback side panel (validation, focus trap, Turnstile)
├── ColdStartOverlay.jsx     # Watches backend fetches; shows the wake-up screen during Render cold starts
├── index.css                # Design tokens and every style in the app
├── components/
│   ├── ActivityTray.jsx     # Header bell + message history with unread count
│   ├── BrandMark.jsx        # SVG logo mark
│   ├── Icons.jsx            # Inline SVG icon set (stroke = currentColor)
│   ├── InfoTip.jsx          # ⓘ button with an explanatory popover
│   ├── ScanProgress.jsx     # Progress bar + checklist while a screening runs
│   └── SpeciesEntry.jsx     # Expandable species entry in the report
└── lib/
    ├── api.js               # Env config, error-message parsing, network-error detection
    ├── format.js            # Coordinates, times, miles, verdict copy, guidance section labels
    ├── report.js            # Builds and downloads the HTML report (all text escaped)
    ├── siteFraming.js       # Owns the camera and radius circle: fit-to-radius zoom, animations, recenter
    ├── useTurnstile.js      # Renders the invisible Turnstile widget and issues tokens
    └── usePanelWidth.js     # Resizable left panel: drag, keyboard, clamping, saved widths
```

---

## User flow

1. **Choose your site.** Search by address (Enter searches), switch to latitude/longitude, or click the map / drag the pin. The "Map pin" box always shows where the screening will run. If the typed address hasn't been looked up yet, the main button reads **Find this address** instead of **Use this site**.
2. **Set the search area.** Slider from 1 to 50 miles, plus presets. The backend searches a square around the circle, which the info button explains.
3. **Run the screening.** A review of the site and area, then **Run screening**. While it runs, the checklist tracks backend progress, the map is locked, and the radius line animates.
4. **Report.** Verdict, key figures, saved vs. live result, **Download report**, **Screen another site**, and one expandable entry per flagged species. **Back to screening steps** keeps the report available via **View the last report**.

Changing the site or radius clears the current results. Rate limits disable the relevant button with a countdown.

### Resizable panel

On screens wider than 880px, the left panel has a grip on its right edge (`.panel-resizer`, logic in `lib/usePanelWidth.js`):

- **Drag** to resize, **double-click** to reset, or focus the grip and use **←/→** (24px; hold **Shift** for 96px) and **Home/End**.
- Width is clamped between 340px and the window width minus 360px, so the map never disappears. It re-clamps when the window is resized.
- The steps and the report store separate widths in `localStorage` under `ecorisk.panelWidths`. The report defaults to 540px, or the steps width if that is wider.
- The width is applied as the `--panel-w` custom property on `.workspace`. `.panel-scroll` is a CSS container named `panel`, so styles can respond to the panel's width: at 680px and wider, species guidance switches to two columns. Step content is capped at 560px so form lines stay readable.
- The map calls `invalidateSize()` through a `ResizeObserver`, so tiles fill the new size during and after a drag.

### Map framing

`lib/siteFraming.js` creates one controller per map (from `ScreeningMap.jsx`). It draws the search-radius circle and its distance tag imperatively rather than through react-leaflet props, because Leaflet only re-projects SVG paths when a move ends: a circle that changes during a flight is drawn at the wrong scale and clipped.

- **Zoom:** `fitZoomFor()` uses `map.getBoundsZoom()` on the circle's extent plus padding (56px, less on small maps), capped at zoom 15. This replaces the old radius lookup table, which broke above 15 miles, and the fixed zoom-13 fly-to used for new sites (issues #40 and #50).
- **New site:** fade the circle out (150ms), `flyTo` the site at the fitted zoom, then grow the circle from 0 to the radius.
- **New radius:** wait 220ms for the slider to settle. When growing, zoom out first and then ease the circle outward; when shrinking, ease inward first and then zoom in. The circle always fits the view while it animates, and the camera always zooms around the site (the old `setZoom` zoomed around wherever the view happened to be).
- **Cancellation:** every change starts a new run and makes older runs stop at their next step, so rapid clicks or a radius change mid-flight never leave the map half-moved.
- **Recenter on site:** after any move the controller checks whether the site is still framed (near the center, whole circle visible, not zoomed far out). If not, `ScreeningMap` shows the button, which calls `recenter()`.
- **Bounds:** `MAP_BOUNDS` is Illinois padded by about 3° so Leaflet's bounds limit never pushes a large search area near the state line off-center (issue #47).
- `prefers-reduced-motion` skips the fades, flights, and easing.

### Notifications

`notify(message, type, { toast })` in `App.jsx` adds every message to the activity tray and, unless `toast: false`, shows a toast in the bottom-right. Opening the tray or the feedback panel dismisses visible toasts so they don't overlap.

---

## Design system

The look borrows from land-survey site plans: a crosshair site marker, a dashed survey line for the search radius, and survey-line connectors between the steps. All tokens live at the top of `src/index.css`.

**Type:** Public Sans (Google Fonts, 400/600/700 + italic for scientific names) for everything. Numbers use `font-variant-numeric: tabular-nums` where they need to line up. Scale: 13 / 14 / 16 / 19 / 23 / 28px.

**Color:**

| Token | Hex | Use |
|---|---|---|
| `--ground` | `#ECEFEA` | Page background |
| `--paper` | `#F9FAF7` | Panels, header, sheets |
| `--ink` | `#1C2925` | Primary text |
| `--river` | `#25586A` | Buttons, links, site marker, search radius |
| `--gold` / `--gold-ink` | `#C08A1E` / `#7C5710` | Protected species found |
| `--sedge` / `--sedge-ink` | `#4E7A45` / `#3D6136` | Clear result, success |
| `--brick` | `#A33A32` | Errors |

**Map:** MapTiler `dataviz-v4` raster tiles (set by `MAP_STYLE` in `ScreeningMap.jsx`). The muted base keeps water, wetlands, and woodland visible while letting the overlay stand out.

**Info buttons:** use `<InfoTip title="...">explanation</InfoTip>`. The popover spans its nearest ancestor with the `tip-anchor` class, which keeps it inside the panel at any width.

**Accessibility:** visible focus rings, keyboard-operable grip, tray, info buttons, and feedback panel (Escape closes, focus returns), labeled form fields with inline errors, and `prefers-reduced-motion` disables animation.
