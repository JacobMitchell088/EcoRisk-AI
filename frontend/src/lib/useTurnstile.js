import { useCallback, useRef } from "react";
import { TURNSTILE_SITE_KEY } from "./api";

const VERIFY_FAILED = "We couldn't verify you're a person. Refresh the page and try again.";

// The Turnstile script loads async, so it may not exist yet on first render.
function waitForTurnstile(timeoutMs = 10000) {
  return new Promise((resolve, reject) => {
    const started = Date.now();
    (function check() {
      if (window.turnstile) return resolve(window.turnstile);
      if (Date.now() - started > timeoutMs) {
        return reject(new Error("Human verification didn't load. Refresh the page and try again."));
      }
      setTimeout(check, 150);
    })();
  });
}

// Invisible Cloudflare Turnstile widget rendered into `containerRef`.
// Keep the container mounted for the lifetime of the component.
export default function useTurnstile() {
  const containerRef = useRef(null);
  const widgetIdRef = useRef(null);
  const pendingRef = useRef(null);

  const ensureWidget = useCallback(async () => {
    const turnstile = await waitForTurnstile();

    if (widgetIdRef.current === null) {
      if (!containerRef.current) {
        throw new Error("Human verification isn't ready yet. Wait a moment and try again.");
      }
      widgetIdRef.current = turnstile.render(containerRef.current, {
        sitekey: TURNSTILE_SITE_KEY,
        execution: "execute",
        appearance: "interaction-only",
        callback: (token) => {
          pendingRef.current?.resolve(token);
          pendingRef.current = null;
        },
        "error-callback": () => {
          pendingRef.current?.reject(new Error(VERIFY_FAILED));
          pendingRef.current = null;
        },
      });
    }

    return turnstile;
  }, []);

  const prepare = useCallback(() => {
    ensureWidget().catch(() => {});
  }, [ensureWidget]);

  const getToken = useCallback(async () => {
    const turnstile = await ensureWidget();
    const existing = turnstile.getResponse(widgetIdRef.current);
    if (existing) return existing;

    turnstile.reset(widgetIdRef.current);
    return new Promise((resolve, reject) => {
      pendingRef.current = { resolve, reject };
      turnstile.execute(widgetIdRef.current);
    });
  }, [ensureWidget]);

  const reset = useCallback(() => {
    if (window.turnstile && widgetIdRef.current !== null) {
      window.turnstile.reset(widgetIdRef.current);
    }
  }, []);

  return { containerRef, prepare, getToken, reset };
}
