import { useEffect, useRef, useState } from "react";
import BrandMark from "./components/BrandMark";
import { backendUrl } from "./lib/api";

// Render free-tier instances sleep when idle; the first request can hang while
// the server spins back up ~60s If a backend request stays pending past this
// threshold — or fails outright — we treat it as a cold start and show the overlay.
const SLOW_THRESHOLD_MS = 4000;
const HEALTH_POLL_MS = 3000;
const MESSAGE_ROTATE_S = 6;

// Captured before we patch window.fetch, so health polling bypasses the wrapper.
const nativeFetch = typeof window !== "undefined" ? window.fetch.bind(window) : null;

// Append ?coldstart=1 to the URL to force the overlay open for visual testing.
// When forced it stays up (health polling won't dismiss it); remove the param to clear.
const FORCE_COLDSTART =
  typeof window !== "undefined" &&
  new URLSearchParams(window.location.search).get("coldstart") === "1";

const MESSAGES = [
  "Waking up the server",
  "Starting the screening service",
  "Still starting, this is normal",
  "Almost ready",
];

export default function ColdStartOverlay() {
  const [cold, setCold] = useState(FORCE_COLDSTART);
  const coldRef = useRef(false);

  useEffect(() => {
    coldRef.current = cold;
  }, [cold]);

  // Patch window.fetch once to watch backend requests for cold-start symptoms.
  useEffect(() => {
    if (!backendUrl || !nativeFetch) return;

    window.fetch = (input, init) => {
      const url = typeof input === "string" ? input : (input && input.url) || "";
      if (!url.startsWith(backendUrl)) {
        return nativeFetch(input, init);
      }

      let timer = null;
      if (!coldRef.current) {
        timer = setTimeout(() => setCold(true), SLOW_THRESHOLD_MS);
      }

      return nativeFetch(input, init)
        .then((res) => {
          if (timer) clearTimeout(timer);
          // Any response at all means the instance is awake and CORS is
          // working — dismiss immediately rather than waiting on /health
          // polling, which can keep failing during/after a cold start.
          if (coldRef.current && !FORCE_COLDSTART) setCold(false);
          return res;
        })
        .catch((err) => {
          if (timer) clearTimeout(timer);
          // A network-level failure usually means the instance is still asleep.
          setCold(true);
          throw err;
        });
    };

    return () => {
      window.fetch = nativeFetch;
    };
  }, []);

  // While cold, poll /health until the backend answers, then dismiss.
  useEffect(() => {
    if (!cold || FORCE_COLDSTART || !backendUrl || !nativeFetch) return;
    let cancelled = false;

    const id = setInterval(async () => {
      try {
        const res = await nativeFetch(`${backendUrl}/health`, { method: "GET" });
        if (!cancelled && res.ok) setCold(false);
      } catch {
        /* still waking up — keep polling */
      }
    }, HEALTH_POLL_MS);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [cold]);

  if (!cold) return null;
  return <ColdStartSheet />;
}

// Mounted fresh each time the overlay opens, so the timer always starts at zero.
function ColdStartSheet() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000);
    return () => clearInterval(id);
  }, []);

  const message = MESSAGES[Math.floor(elapsed / MESSAGE_ROTATE_S) % MESSAGES.length];
  // Eases toward (never reaches) the end, since the true wake time is unknown.
  const meter = Math.round(95 * (1 - Math.exp(-elapsed / 28)));
  const clock = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, "0")}`;

  return (
    <div className="coldstart" role="dialog" aria-modal="true" aria-labelledby="coldstart-title">
      <div className="coldstart-sheet">
        <div className="coldstart-signal" aria-hidden="true">
          <BrandMark size={32} />
        </div>

        <div className="coldstart-copy">
          <h2 id="coldstart-title" className="coldstart-title">
            Starting the screening service
          </h2>
          <p className="coldstart-message" aria-live="polite" key={message}>
            {message}
          </p>
        </div>

        <div className="coldstart-meter" aria-hidden="true">
          <span style={{ width: `${meter}%` }} />
        </div>
        <p className="coldstart-time">
          <span className="coldstart-clock">{clock}</span> so far. This usually takes about a minute.
        </p>

        <p className="coldstart-note">
          The service goes to sleep when nobody has used it for a while. It wakes up on its own, and
          this page continues automatically once it's ready.
        </p>
      </div>
    </div>
  );
}
