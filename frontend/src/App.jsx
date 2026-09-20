import { useCallback, useEffect, useState, useRef } from "react";
import { Toaster, toast } from "react-hot-toast";
import ScreeningMap from "./ScreeningMap";
import FeedbackWidget from "./FeedbackWidget";
import ColdStartOverlay from "./ColdStartOverlay";
import ActivityTray from "./components/ActivityTray";
import BrandMark from "./components/BrandMark";
import InfoTip from "./components/InfoTip";
import ScanProgress from "./components/ScanProgress";
import SpeciesEntry from "./components/SpeciesEntry";
import {
  AlertIcon,
  ArrowLeftIcon,
  ChatIcon,
  CheckCircleIcon,
  CheckIcon,
  DownloadIcon,
  FlagIcon,
  PinIcon,
} from "./components/Icons";
import useTurnstile from "./lib/useTurnstile";
import usePanelWidth from "./lib/usePanelWidth";
import { backendUrl, isNetworkError, readErrorMessage, TURNSTILE_SITE_KEY } from "./lib/api";
import { formatClock, formatCooldown, formatCoords, milesLabel, verdictCopy } from "./lib/format";
import { downloadReport } from "./lib/report";

const initialForm = { // SIUE engineering building
  address: "Engineering Building, Southern Illinois University Edwardsville",
  lat: "38.792",
  lon: "-90.002",
  radius_miles: "5"
};

const emptyErrors = { addressLookup: "", coordinateLookup: "", environmentScan: "" };
const emptyData = { gbif_hits: [], species_context: [], total_species_count: 0 };
const RADIUS_MIN = 1;
const RADIUS_MAX = 50;
const RADIUS_PRESETS = [1, 2, 5, 10, 25];
const RECOMMENDED_RADIUS = 5;

function coordKey(lat, lon) {
  return `${Number(lat).toFixed(3)},${Number(lon).toFixed(3)}`;
}

function friendlyMessage(err) {
  if (isNetworkError(err)) {
    return "Couldn't reach the screening service. Check your connection and try again.";
  }
  return err?.message || "Something went wrong. Try again in a moment.";
}

function Step({ number, title, status, summary, onChange, children }) {
  return (
    <li className={`step step--${status}`} aria-current={status === "current" ? "step" : undefined}>
      <span className="step-marker" aria-hidden="true">
        {status === "done" ? <CheckIcon size={16} strokeWidth={2.6} /> : number}
      </span>
      <div className="step-head">
        <div className="step-heading">
          <h2 className="step-title">
            <span className="visually-hidden">Step {number}: </span>
            {title}
          </h2>
          {status !== "current" && summary && <div className="step-summary">{summary}</div>}
        </div>
        {status === "done" && onChange && (
          <button type="button" className="link-btn step-change" onClick={onChange}>
            Change<span className="visually-hidden"> {title.toLowerCase()}</span>
          </button>
        )}
      </div>
      {status === "current" && <div className="step-body">{children}</div>}
    </li>
  );
}

export default function App() {
  const [form, setForm] = useState(initialForm);
  // The address label that belongs to the pin, and the coordinates it was resolved for.
  const [site, setSite] = useState({
    label: initialForm.address,
    key: coordKey(initialForm.lat, initialForm.lon),
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(emptyErrors);
  const [cooldowns, setCooldowns] = useState({
    addressLookup: 0,
    coordinateLookup: 0,
    environmentScan: 0,
  });
  const [inputMode, setInputMode] = useState("address");
  const [data, setData] = useState(emptyData);
  const [progress, setProgress] = useState(0);
  const [lookingUpAddress, setLookingUpAddress] = useState(false);
  const [lookingUpCoords, setLookingUpCoords] = useState(false);
  const [scanMeta, setScanMeta] = useState(null);
  const [finalizing, setFinalizing] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [step, setStep] = useState(1);
  const [reportOpen, setReportOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);

  const lastPickedRef = useRef(null);
  const {
    containerRef: turnstileRef,
    prepare: prepareTurnstile,
    getToken,
    reset: resetTurnstile,
  } = useTurnstile();

  useEffect(() => {
    prepareTurnstile();
  }, [prepareTurnstile]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCooldowns((prev) => {
        const updated = { ...prev };

        Object.keys(updated).forEach((key) => {
          if (updated[key] > 0) updated[key] -= 1;
        });

        return updated;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Every message goes to the activity tray; most also show as a toast.
  const notify = useCallback((message, type = "error", { toast: showToast = true } = {}) => {
    if (!message) return;

    setNotifications((prev) =>
      [
        { id: `${Date.now()}-${Math.random()}`, message, type, time: new Date(), read: false },
        ...prev,
      ].slice(0, 20)
    );

    if (!showToast) return;
    if (type === "success") toast.success(message);
    else if (type === "info") toast(message);
    else toast.error(message);
  }, []);

  const markNotificationsRead = useCallback(() => {
    setNotifications((prev) =>
      prev.some((item) => !item.read) ? prev.map((item) => ({ ...item, read: true })) : prev
    );
  }, []);

  const clearNotifications = useCallback(() => setNotifications([]), []);
  const closeFeedback = useCallback(() => setFeedbackOpen(false), []);

  function reportError(key, message) {
    setError((prev) => ({ ...prev, [key]: message }));
    notify(message, "error");
  }

  function updateField(event) {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    resetResults();
  }

  function setRadius(value) {
    setForm((prev) => ({ ...prev, radius_miles: String(value) }));
    resetResults();
  }

  const validateInputs = () => {
    const lat = parseFloat(form.lat);
    const lon = parseFloat(form.lon);

    if (isNaN(lat) || isNaN(lon)) return "Latitude and longitude must be numbers.";
    if (lat < -90 || lat > 90) return "Latitude must be between -90 and 90.";
    if (lon < -180 || lon > 180) return "Longitude must be between -180 and 180.";

    const radius = parseFloat(form.radius_miles);
    if (isNaN(radius) || radius <= 0 || radius > 100) {
      return "Choose a search radius between 1 and 50 miles.";
    }

    return "";
  };

  async function checkApiResponse(response, action) {
    if (response.ok) return response;

    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After");
      handleRateLimit(action, retryAfter);
      throw new Error("Rate limited");
    }

    throw new Error(await readErrorMessage(response, "The request didn't go through. Try again in a moment."));
  }

  function handleRateLimit(action, retryAfter = null) {
    const fallback = {
      addressLookup: 60,
      coordinateLookup: 60,
      environmentScan: 3600,
    };

    const seconds = retryAfter ? parseInt(retryAfter, 10) : fallback[action];
    const wait = formatCooldown(seconds);

    const messages = {
      addressLookup: `Address search is paused for now. Try again in ${wait}.`,
      coordinateLookup: `Address lookup is paused for now. Try again in ${wait}.`,
      environmentScan: `You've reached the screening limit. You can run another screening in ${wait}.`,
    };

    setCooldowns((prev) => ({
      ...prev,
      [action]: seconds,
    }));

    reportError(action, messages[action]);
  }

  function pollScanStatus(scanJobId) {
    const interval = setInterval(async () => {
      try {
        const statusResponse = await fetch(`${backendUrl}/scan/status/${scanJobId}`);

        if (!statusResponse.ok) {
          throw new Error("Failed to fetch scan status.");
        }

        const statusJson = await statusResponse.json();

        setProgress(statusJson.progress || 0);

        if (statusJson.status === "complete") {
          setProgress(100);
          clearInterval(interval);
          setFinalizing(true);

          // Stop the "Finalizing results" spinner 1s before results appear
          setTimeout(() => setFinalizing(false), 3000);

          setTimeout(() => {
            const isCached = statusJson.cached ?? false;
            const scannedAt = statusJson.result?.scanned_at ?? null;
            const time = formatClock(scannedAt);

            setData(statusJson.result);
            setScanMeta({ cached: isCached, scannedAt });
            setReportOpen(true);
            setLoading(false);

            if (isCached) {
              notify(time ? `Screening complete. Showing a saved result from ${time}.` : "Screening complete. Showing a saved result.", "success");
            } else {
              notify(time ? `Screening complete at ${time}.` : "Screening complete.", "success");
            }
          }, 4000);

          return;
        }

        if (statusJson.status === "error") {
          clearInterval(interval);
          reportError("environmentScan", "The screening couldn't finish. Run it again in a moment.");
          setLoading(false);
          return;
        }
      } catch {
        clearInterval(interval);
        reportError("environmentScan", "Lost contact with the screening service while it was running. Run the screening again.");
        setLoading(false);
      }
    }, 2000); // Poll every 2 seconds
  }

  async function handleAddressLookup() {
    setLookingUpAddress(true);
    setError((prev) => ({ ...prev, addressLookup: "" }));
    try {
      const query = form.address.trim();
      if (!query) {
        throw new Error("Enter an address to search for.");
      }
      if (!backendUrl) {
        throw new Error("The screening service isn't configured. Set VITE_API_BASE_URL.");
      }

      const response = await fetch(`${backendUrl}/geocode/search?q=${encodeURIComponent(query)}`);

      await checkApiResponse(response, "addressLookup");

      const json = await response.json();

      if (!json.best_match) {
        throw new Error(`No match for "${query}". Add a city or ZIP code, or click the map to place the pin.`);
      }

      const best = json.best_match;
      const lat = parseFloat(best.lat).toFixed(3);
      const lon = parseFloat(best.lon).toFixed(3);
      const label = best.label || query;

      setForm((prev) => ({ ...prev, address: label, lat, lon }));
      resetResults();
      setSite({ label, key: coordKey(lat, lon) });
      notify(`Site found: ${label}`, "success");
    } catch (err) {
      if (err.message !== "Rate limited") {
        reportError("addressLookup", friendlyMessage(err));
      }
    } finally {
      setLookingUpAddress(false);
    }
  }

  async function handleCoordinateLookup() {
    setLookingUpCoords(true);
    setError((prev) => ({ ...prev, coordinateLookup: "" }));
    try {
      const lat = Number(form.lat);
      const lon = Number(form.lon);

      if (form.lat === "" || form.lon === "" || Number.isNaN(lat) || Number.isNaN(lon)) {
        throw new Error("Latitude and longitude must be numbers.");
      }
      if (!backendUrl) {
        throw new Error("The screening service isn't configured. Set VITE_API_BASE_URL.");
      }

      const response = await fetch(`${backendUrl}/geocode/reverse?lat=${lat}&lon=${lon}`);

      await checkApiResponse(response, "coordinateLookup");

      const json = await response.json();

      if (!json.best_match) {
        throw new Error("No address was found for those coordinates. You can still screen this location.");
      }

      const best = json.best_match;
      const bestLat = parseFloat(best.lat).toFixed(3);
      const bestLon = parseFloat(best.lon).toFixed(3);

      setForm((prev) => ({
        ...prev,
        address: best.label || prev.address,
        lat: bestLat,
        lon: bestLon,
      }));
      resetResults();
      if (best.label) setSite({ label: best.label, key: coordKey(bestLat, bestLon) });
      notify(`Address found: ${best.label}`, "success");
    } catch (err) {
      if (err.message !== "Rate limited") {
        reportError("coordinateLookup", friendlyMessage(err));
      }
    } finally {
      setLookingUpCoords(false);
    }
  }

  async function handlePickLocation(lat, lon) {
    const roundedLat = Number(lat.toFixed(3));
    const roundedLon = Number(lon.toFixed(3));
    const newKey = `${roundedLat},${roundedLon}`;
    if (lastPickedRef.current === newKey) return;
    lastPickedRef.current = newKey;
    resetResults();
    // Moving the pin makes the confirmed site stale, so send them back to step 1 to
    // confirm the new one. The radius they already picked is left alone.
    setStep(1);
    setForm((prev) => ({ ...prev, lat: roundedLat, lon: roundedLon }));
    try {
      const response = await fetch(`${backendUrl}/geocode/reverse?lat=${roundedLat}&lon=${roundedLon}`);
      if (!response.ok) return;
      const json = await response.json();
      if (!json.best_match) return;
      const best = json.best_match;
      setForm((prev) => ({ ...prev, lat: roundedLat, lon: roundedLon, address: best.label || prev.address }));
      if (best.label) {
        setSite({ label: best.label, key: coordKey(roundedLat, roundedLon) });
        notify(`Site moved to ${best.label}`, "info", { toast: false });
      }
    } catch (err) {
      console.error("Reverse geocode failed", err);
    }
  }

  function resetResults() {
    setError(emptyErrors);
    setData(emptyData);
    setProgress(0);
    setScanMeta(null);
    setFinalizing(false);
    setReportOpen(false);
  }

  function startOver() {
    resetResults();
    setStep(1);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(emptyErrors);
    setData(emptyData);
    setScanMeta(null);
    setReportOpen(false);
    setLoading(true);
    setProgress(0);

    try {
      if (!backendUrl) {
        throw new Error("Missing VITE_API_BASE_URL. Add it to a .env file.");
      }
      if (!TURNSTILE_SITE_KEY) {
        throw new Error("Missing VITE_TURNSTILE_SITE_KEY. Add it to a .env file.");
      }
      const invalid = validateInputs();
      if (invalid) {
        throw new Error(invalid);
      }

      const token = await getToken();
      if (!token) {
        throw new Error("We couldn't verify you're a person. Refresh the page and try again.");
      }

      const startResponse = await fetch(`${backendUrl}/scan/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          lat: Number(form.lat),
          lon: Number(form.lon),
          radius_miles: Number(form.radius_miles),
          captcha_token: token
        })
      });

      await checkApiResponse(startResponse, "environmentScan");

      const startJson = await startResponse.json();

      if (!startJson.job_id) {
        throw new Error("The screening service didn't start the screening. Try again.");
      }

      resetTurnstile();

      // Polling loop
      pollScanStatus(startJson.job_id);
    } catch (err) {
      if (err.message !== "Rate limited") {
        reportError("environmentScan", friendlyMessage(err));
      }
      setLoading(false);
    }
  }

  // ---- Derived state -------------------------------------------------------

  const latNum = Number(form.lat);
  const lonNum = Number(form.lon);
  const siteValid =
    form.lat !== "" &&
    form.lon !== "" &&
    Number.isFinite(latNum) &&
    Number.isFinite(lonNum) &&
    Math.abs(latNum) <= 90 &&
    Math.abs(lonNum) <= 180;
  const labelIsCurrent = siteValid && Boolean(site.label) && site.key === coordKey(form.lat, form.lon);
  const siteName = labelIsCurrent ? site.label : "Pinned location";
  const coordsText = formatCoords(form.lat, form.lon);
  const addressDirty = inputMode === "address" && form.address.trim() !== (site.label || "").trim();

  const radius = Number(form.radius_miles) || RADIUS_MIN;
  const radiusFill = `${((radius - RADIUS_MIN) / (RADIUS_MAX - RADIUS_MIN)) * 100}%`;

  const view = loading ? "scanning" : scanMeta && reportOpen ? "report" : "steps";
  const activeStep = view === "scanning" ? 3 : step;
  const statusFor = (n) => (n === activeStep ? "current" : n < activeStep ? "done" : "upcoming");
  const canChange = view === "steps";
  const panel = usePanelWidth(view);

  const hits = data?.gbif_hits || [];
  const reportRadius = data?.input?.radius_miles ?? radius;
  const yearStart = data?.input?.year_start ?? 2000;
  const verdict = verdictCopy(hits.length, reportRadius, yearStart);
  const totalSightings = hits.reduce((sum, hit) => sum + (Number(hit.gbif_count) || 0), 0);
  const scanError = error.environmentScan;

  // ---- Step content --------------------------------------------------------

  const siteStep = (
    <>
      <p className="step-lede">Search for the project's address, or click the map to place the pin.</p>

      {inputMode === "address" ? (
        <form
          className="field"
          onSubmit={(event) => {
            event.preventDefault();
            handleAddressLookup();
          }}
        >
          <div className="field-label-row tip-anchor">
            <label className="field-label" htmlFor="site-address">
              Project address
            </label>
            <InfoTip title="Finding your site">
              Type the project's street address and press <strong>Find this address</strong>. The map
              pin moves to that address, and the screening uses the pin's location. You can also click
              the map or drag the pin to set the site by hand.
            </InfoTip>
          </div>
          <input
            id="site-address"
            className="input"
            name="address"
            value={form.address}
            onChange={updateField}
            placeholder="123 Main St, Springfield, IL"
            autoComplete="street-address"
            enterKeyHint="search"
            aria-invalid={Boolean(error.addressLookup)}
            aria-describedby={error.addressLookup ? "address-error" : undefined}
          />
          {error.addressLookup && (
            <p className="field-error" id="address-error">
              <AlertIcon size={16} /> {error.addressLookup}
            </p>
          )}
        </form>
      ) : (
        <form
          className="field"
          onSubmit={(event) => {
            event.preventDefault();
            handleCoordinateLookup();
          }}
        >
          <div className="field-label-row tip-anchor">
            <span className="field-label">Coordinates</span>
            <InfoTip title="Using coordinates">
              Enter the site's latitude and longitude in decimal degrees, such as 38.792 and -90.002.
              Longitudes in Illinois are negative. Select <strong>Find address</strong> to confirm the
              location by name.
            </InfoTip>
          </div>
          <div className="field-pair">
            <label className="field">
              <span className="field-sublabel">Latitude</span>
              <input
                className="input input--numeric"
                name="lat"
                value={form.lat}
                onChange={updateField}
                placeholder="41.878"
                inputMode="decimal"
                aria-invalid={Boolean(error.coordinateLookup)}
              />
            </label>
            <label className="field">
              <span className="field-sublabel">Longitude</span>
              <input
                className="input input--numeric"
                name="lon"
                value={form.lon}
                onChange={updateField}
                placeholder="-87.629"
                inputMode="decimal"
                aria-invalid={Boolean(error.coordinateLookup)}
              />
            </label>
          </div>
          {error.coordinateLookup && (
            <p className="field-error">
              <AlertIcon size={16} /> {error.coordinateLookup}
            </p>
          )}
          <button
            type="submit"
            className="btn btn-secondary btn-block"
            disabled={cooldowns.coordinateLookup > 0 || lookingUpCoords || !siteValid}
          >
            {lookingUpCoords
              ? "Finding address…"
              : cooldowns.coordinateLookup > 0
              ? `Address lookup available in ${formatCooldown(cooldowns.coordinateLookup)}`
              : "Find address"}
          </button>
        </form>
      )}

      <div className="site-readout" aria-live="polite">
        <PinIcon size={20} />
        <div>
          <p className="readout-label">Map pin</p>
          {siteValid ? (
            <>
              <p className="site-label">{siteName}</p>
              <p className="site-coords">{coordsText}</p>
            </>
          ) : (
            <p className="site-label">Enter a valid latitude and longitude, or click the map.</p>
          )}
        </div>
      </div>

      {addressDirty ? (
        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={handleAddressLookup}
          disabled={cooldowns.addressLookup > 0 || lookingUpAddress}
        >
          {lookingUpAddress
            ? "Finding address…"
            : cooldowns.addressLookup > 0
            ? `Address search available in ${formatCooldown(cooldowns.addressLookup)}`
            : "Find this address"}
        </button>
      ) : (
        <button
          type="button"
          className="btn btn-primary btn-block"
          disabled={!siteValid}
          onClick={() => setStep(2)}
        >
          Use this site
        </button>
      )}

      <button
        type="button"
        className="link-btn"
        onClick={() => setInputMode((mode) => (mode === "address" ? "coordinates" : "address"))}
      >
        {inputMode === "address" ? "Enter coordinates instead" : "Search by address instead"}
      </button>
    </>
  );

  const areaStep = (
    <>
      <p className="step-lede">How far around the site should we look for recorded sightings?</p>

      <div className="field">
        <div className="field-label-row tip-anchor">
          <label className="field-label" htmlFor="radius">
            Search radius
          </label>
          <InfoTip title="Search radius">
            This sets how far from the site the screening looks for species sightings. A larger radius
            covers more ground and may turn up more sightings, while a smaller one focuses on the area
            closest to the project. We recommend 5 miles, the default. The search covers a square around this
            circle, so sightings just past its edge can be included.
          </InfoTip>
          <output className="radius-readout" htmlFor="radius">
            {milesLabel(radius)}
          </output>
        </div>
        <input
          id="radius"
          className="range"
          type="range"
          name="radius_miles"
          min={RADIUS_MIN}
          max={RADIUS_MAX}
          step="1"
          value={form.radius_miles}
          onChange={updateField}
          style={{ "--fill": radiusFill }}
          aria-valuetext={milesLabel(radius)}
        />
        <div className="range-scale" aria-hidden="true">
          <span>{RADIUS_MIN} mi</span>
          <span>{RADIUS_MAX} mi</span>
        </div>
      </div>

      <div className="chips" role="group" aria-label="Common distances">
        {RADIUS_PRESETS.map((miles) => (
          <button
            key={miles}
            type="button"
            className="chip"
            aria-pressed={radius === miles}
            onClick={() => setRadius(miles)}
          >
            {miles} mi{miles === RECOMMENDED_RADIUS && " "}
            {miles === RECOMMENDED_RADIUS && <span className="chip-note">Recommended</span>}
          </button>
        ))}
      </div>

      <button type="button" className="btn btn-primary btn-block" onClick={() => setStep(3)}>
        Continue
      </button>
    </>
  );

  const runStep = loading ? (
    <ScanProgress progress={progress} finalizing={finalizing} />
  ) : (
    <form className="step-stack" onSubmit={handleSubmit}>
      <dl className="review">
        <div>
          <dt>Site</dt>
          <dd>
            {siteName}
            <span className="review-sub">{coordsText}</span>
          </dd>
        </div>
        <div>
          <dt>Search area</dt>
          <dd>{milesLabel(radius)} around the site</dd>
        </div>
        <div>
          <dt>What we check</dt>
          <dd>
            Sightings recorded on GBIF since 2000, compared with the Illinois list of endangered and
            threatened species
          </dd>
        </div>
      </dl>

      {scanError && (
        <div className="notice notice--error" role="alert">
          <AlertIcon size={18} />
          <p>{scanError}</p>
        </div>
      )}

      <button
        className="btn btn-primary btn-block"
        type="submit"
        disabled={cooldowns.environmentScan > 0}
      >
        {cooldowns.environmentScan > 0
          ? `Screening available in ${formatCooldown(cooldowns.environmentScan)}`
          : "Run screening"}
      </button>

      {scanMeta && (
        <button type="button" className="link-btn" onClick={() => setReportOpen(true)}>
          View the last report
        </button>
      )}

      <p className="fine-print">Most screenings finish in under a minute.</p>
    </form>
  );

  const stepsView = (
    <>
      <div className="panel-intro">
        <h1 className="panel-title">Screen a construction site</h1>
        <p className="panel-lede">
          Check whether any Illinois endangered or threatened species have been recorded near your
          project.
        </p>
      </div>

      <ol className="steps">
        <Step
          number={1}
          title="Choose your site"
          status={statusFor(1)}
          onChange={canChange ? () => setStep(1) : undefined}
          summary={
            <>
              <span className="summary-main">{siteName}</span>
              <span className="summary-sub">{coordsText}</span>
            </>
          }
        >
          {siteStep}
        </Step>

        <Step
          number={2}
          title="Set the search area"
          status={statusFor(2)}
          onChange={canChange ? () => setStep(2) : undefined}
          summary={
            statusFor(2) === "done" ? (
              <span className="summary-main">{milesLabel(radius)} around the site</span>
            ) : null
          }
        >
          {areaStep}
        </Step>

        <Step number={3} title={loading ? "Screening your site" : "Run the screening"} status={statusFor(3)}>
          {runStep}
        </Step>
      </ol>
    </>
  );

  const reportView = scanMeta && (
    <div className="report">
      <button type="button" className="link-btn report-back" onClick={() => setReportOpen(false)}>
        <ArrowLeftIcon size={16} /> Back to screening steps
      </button>

      <header className={`verdict ${hits.length ? "verdict--flagged" : "verdict--clear"}`}>
        <span className="verdict-icon" aria-hidden="true">
          {hits.length ? <FlagIcon size={22} /> : <CheckCircleIcon size={24} />}
        </span>
        <div>
          <h1 className="verdict-title">{verdict.title}</h1>
          <p className="verdict-text">{verdict.text}</p>
        </div>
      </header>

      <div className="report-site">
        <PinIcon size={18} />
        <div>
          <p className="site-label">{siteName}</p>
          <p className="site-coords">{coordsText}</p>
        </div>
      </div>

      <dl className="figures tip-anchor">
        <div className="figure figure--flagged">
          <dt>Protected species</dt>
          <dd>{hits.length}</dd>
        </div>
        <div className="figure">
          <dt>Protected Sightings</dt>
          <dd>{totalSightings}</dd>
        </div>
        <div className="figure">
          <dt>
            All species
            <InfoTip title="All species recorded">
              The number of different species with GBIF sightings inside the search area since{" "}
              {yearStart}. Only species on the Illinois endangered and threatened list are flagged as
              protected.
            </InfoTip>
          </dt>
          <dd>{data.total_species_count ?? 0}</dd>
        </div>
      </dl>

      <div className="report-bar">
        <p className="report-stamp tip-anchor">
          {scanMeta.cached ? (
            <>
              Saved result from {formatClock(scanMeta.scannedAt) || "earlier today"}
              <InfoTip title="Saved results">
                Screenings of the same site and radius are saved for 24 hours, so a repeat check returns
                right away instead of searching again.
              </InfoTip>
            </>
          ) : (
            <>Screened at {formatClock(scanMeta.scannedAt) || "just now"}</>
          )}
        </p>
        <div className="report-actions">
          <button
            type="button"
            className="btn btn-primary"
            onClick={() =>
              downloadReport(data, scanMeta, {
                name: siteName,
                lat: form.lat,
                lon: form.lon,
                radius,
              })
            }
          >
            <DownloadIcon size={18} /> Download report
          </button>
          <button type="button" className="btn btn-secondary" onClick={startOver}>
            Screen another site
          </button>
        </div>
      </div>

      {hits.length > 0 ? (
        <section className="species-section" aria-labelledby="species-heading">
          <h2 className="section-title" id="species-heading">
            Species to plan around
          </h2>
          <p className="section-lede">
            Open a species to see when it's most sensitive and which activities disturb it. Guidance is
            written by AI from public sources.
          </p>
          <div className="species-list">
            {hits.map((hit, index) => {
              const context = (data.species_context || []).find(
                (item) => item.scientific_name === hit.scientific_name
              );
              return (
                <SpeciesEntry key={hit.taxon_key} hit={hit} context={context} defaultOpen={index === 0} />
              );
            })}
          </div>
        </section>
      ) : (
        <p className="section-lede">
          A clear result doesn't guarantee that no protected species are present. Sightings only appear
          here if someone recorded them on GBIF.
        </p>
      )}
    </div>
  );

  // Start of page render
  return (
    <div className="app">
      <Toaster
        position="bottom-right"
        containerStyle={{ bottom: 36, right: 16, left: 16 }}
        toastOptions={{
          duration: 6000,
          style: {
            fontFamily: "var(--font)",
            background: "#F9FAF7",
            color: "#1C2925",
            border: "1px solid #D6DCD5",
            borderRadius: "10px",
            padding: "10px 14px",
            fontSize: "15px",
            lineHeight: "1.45",
            maxWidth: "380px",
            boxShadow: "0 1px 2px rgba(28,41,37,.08), 0 10px 28px -8px rgba(28,41,37,.22)",
          },
          success: { iconTheme: { primary: "#4E7A45", secondary: "#FFFFFF" } },
          error: { duration: 8000, iconTheme: { primary: "#A33A32", secondary: "#FFFFFF" } },
        }}
      />

      <header className="masthead">
        <a className="brand" href="/">
          <BrandMark />
          <span className="brand-name">EcoRisk AI</span>
        </a>
        <p className="masthead-tagline">Endangered species screening for Illinois construction sites</p>
        <div className="masthead-actions">
          <ActivityTray
            items={notifications}
            onMarkRead={markNotificationsRead}
            onClear={clearNotifications}
          />
          <button
            type="button"
            className="btn btn-quiet masthead-feedback"
            onClick={() => setFeedbackOpen(true)}
            aria-haspopup="dialog"
          >
            <ChatIcon size={19} />
            <span className="masthead-feedback-text">Feedback</span>
          </button>
        </div>
      </header>

      <main
        className={`workspace${panel.resizing ? " is-resizing" : ""}`}
        data-view={view}
        style={{ "--panel-w": `${panel.width}px` }}
      >
        <section className="panel" aria-label="Screening">
          <div className="panel-scroll">
            {!backendUrl && (
              <div className="notice notice--error config-notice" role="alert">
                <AlertIcon size={18} />
                <p>The screening service isn't configured. Set VITE_API_BASE_URL in a .env file.</p>
              </div>
            )}
            {view === "report" ? reportView : stepsView}
          </div>

          <div ref={turnstileRef} className="turnstile-slot" />

          <footer className="panel-foot">
            <p className="fine-print">
              Preliminary screening only. Results come from public sighting records and AI summaries,
              not a regulatory review. Confirm findings with a qualified environmental professional
              before construction.
            </p>
            <p className="sources">
              Data from{" "}
              <a href="https://www.gbif.org" target="_blank" rel="noreferrer">GBIF</a>,{" "}
              <a href="https://naturalheritage.illinois.gov/dataresearch/access-our-data.html" target="_blank" rel="noreferrer">
                Illinois Natural Heritage Database
              </a>
              , <a href="https://www.maptiler.com" target="_blank" rel="noreferrer">MapTiler</a>, and{" "}
              <a href="https://openrouter.ai" target="_blank" rel="noreferrer">OpenRouter</a>.
            </p>
          </footer>

          <div className="panel-resizer" {...panel.handleProps}>
            <span className="panel-resizer-grip" aria-hidden="true" />
          </div>
        </section>

        <section className="map-region" aria-label="Site map">
          <ScreeningMap
            lat={siteValid ? latNum : NaN}
            lon={siteValid ? lonNum : NaN}
            radiusMiles={radius}
            onPickLocation={handlePickLocation}
            scanning={loading}
            locked={view === "report"}
            onReset={startOver}
            hint={view === "steps" && step === 1 ? "Click the map or drag the pin to move your site" : null}
          />
        </section>
      </main>

      <FeedbackWidget open={feedbackOpen} onClose={closeFeedback} onNotify={notify} />
      <ColdStartOverlay />
    </div>
  );
}
