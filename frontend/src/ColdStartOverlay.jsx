import { useEffect, useRef, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const backendUrl = API_BASE_URL ? API_BASE_URL.replace(/\/$/, "") : "";

// Render free-tier instances sleep when idle; the first request can hang while
// the server spins back up ~60s If a backend request stays pending past this
// threshold — or fails outright — we treat it as a cold start and show the overlay.
const SLOW_THRESHOLD_MS = 4000;
const HEALTH_POLL_MS = 3000;
const MESSAGE_ROTATE_MS = 5000;

// Captured before we patch window.fetch, so health polling bypasses the wrapper.
const nativeFetch = typeof window !== "undefined" ? window.fetch.bind(window) : null;

// Append ?coldstart=1 to the URL to force the overlay open for visual testing.
// When forced it stays up (health polling won't dismiss it); remove the param to clear.
const FORCE_COLDSTART =
  typeof window !== "undefined" &&
  new URLSearchParams(window.location.search).get("coldstart") === "1";

const MESSAGES = [
  "Waking up the server…",
  "Warming up…",
  "Spinning up resources…",
  "Almost there…",
  "Just a little more…",
  "Nearly ready…",
];

export default function ColdStartOverlay() {
  const [cold, setCold] = useState(FORCE_COLDSTART);
  const [msgIndex, setMsgIndex] = useState(0);
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

  // Rotate the reassurance messages while the overlay is up.
  useEffect(() => {
    if (!cold) {
      setMsgIndex(0);
      return;
    }
    const id = setInterval(
      () => setMsgIndex((i) => (i + 1) % MESSAGES.length),
      MESSAGE_ROTATE_MS
    );
    return () => clearInterval(id);
  }, [cold]);

  if (!cold) return null;

  return (
    <div className="coldstart-overlay" role="status" aria-live="polite">
      <div className="coldstart-card">
        <div className="coldstart-spinner" aria-hidden="true" />
        <span className="coldstart-eyebrow">EcoRisk AI</span>
        <h2 className="coldstart-title">Backend is starting up</h2>
        <p className="coldstart-message">{MESSAGES[msgIndex]}</p>
        <p className="coldstart-note">
          Our free-tier server sleeps when idle, so the first request is expected to take
          ~60 seconds while it spins back up. Hang tight — this will clear automatically.
        </p>
        <div className="coldstart-dots" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </div>
    </div>
  );
}
