import L from "leaflet";

// Keeps the project site centered with its whole search-radius circle in view,
// and choreographs the circle so it never renders mid-flight:
//
//   New site:   circle fades out → map flies to the site → circle grows from the pin.
//   New radius: (after the slider settles) growing zooms out first, then the circle
//               eases outward; shrinking eases inward first, then zooms in. Either way
//               the circle always fits the view while it animates.
//   Recenter:   same framing, on demand, without changing the site.
//
// Leaflet only re-projects SVG paths when a move ends, so a circle that changes (or is
// visible while the camera zooms far out) during a flight is drawn at the wrong scale
// and clipped. Hiding it during those moves is what removes the "jumping" circles.

const FRAME_PADDING = 56;          // px kept clear around the circle (fits the distance tag)
const NO_RADIUS_ZOOM = 13;
const MAX_FIT_ZOOM = 15;
const FLY_SECONDS = 1.1;
const ADJUST_FLY_SECONDS = 0.7;
const FADE_OUT_MS = 150;         // matches .is-hidden in index.css
const GROW_MS = 560;
const RESIZE_MS = 420;
const RADIUS_SETTLE_MS = 220;      // wait for the slider to stop before moving the camera
const EARTH_CIRCUMFERENCE_M = 40075017;

const easeOutCubic = (p) => 1 - Math.pow(1 - p, 3);
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

// Highest zoom at which the whole circle (plus padding) fits the current map size.
export function fitZoomFor(map, center, radiusMeters) {
  if (!(radiusMeters > 0)) return NO_RADIUS_ZOOM;
  const size = map.getSize();
  const pad = Math.max(16, Math.min(FRAME_PADDING, Math.floor(Math.min(size.x, size.y) / 8)));
  const bounds = L.latLng(center).toBounds(radiusMeters * 2);
  return Math.min(map.getBoundsZoom(bounds, false, L.point(pad * 2, pad * 2)), MAX_FIT_ZOOM);
}

export function createSiteFraming(map, { circleStyle, onFramedChange }) {
  const circle = L.circle([0, 0], { ...circleStyle, radius: 1, interactive: false }).addTo(map);
  const label = L.marker([0, 0], {
    icon: L.divIcon({ className: "radius-tag", html: "<span></span>", iconSize: [0, 0] }),
    interactive: false,
    keyboard: false,
  }).addTo(map);

  let target = null;          // { lat, lon, radiusMeters }
  let placedAt = null;        // LatLng the visible circle is centered on
  let shownRadius = 0;
  let visible = false;
  let hasFramed = false;
  let runId = 0;
  let frame = 0;
  let settleTimer = 0;
  let settling = false;
  let destroyed = false;
  let lastFramed = null;

  function setVisible(next) {
    visible = next;
    circle.getElement()?.classList.toggle("is-hidden", !next);
    label.getElement()?.classList.toggle("is-hidden", !next);
  }

  function draw(radius) {
    shownRadius = radius;
    circle.setRadius(Math.max(radius, 0.5));
    const c = circle.getLatLng();
    label.setLatLng([c.lat + (radius / EARTH_CIRCUMFERENCE_M) * 360, c.lng]);
  }

  const isStale = (id) => destroyed || id !== runId;

  function tweenRadius(to, duration, id) {
    cancelAnimationFrame(frame);
    const from = shownRadius;
    if (prefersReducedMotion() || Math.abs(to - from) < 1) {
      draw(to);
      return Promise.resolve();
    }
    return new Promise((resolve) => {
      const start = performance.now();
      const step = (now) => {
        if (isStale(id)) return resolve();
        const p = Math.min(1, (now - start) / duration);
        draw(from + (to - from) * easeOutCubic(p));
        if (p < 1) frame = requestAnimationFrame(step);
        else resolve();
      };
      frame = requestAnimationFrame(step);
    });
  }

  function offsetFromCenter(center) {
    return map.latLngToContainerPoint(center).subtract(map.getSize().divideBy(2));
  }

  function hasArrived(center, zoom) {
    const offset = offsetFromCenter(center);
    return map.getZoom() === zoom && Math.abs(offset.x) < 2 && Math.abs(offset.y) < 2;
  }

  // Resolves when the camera reaches the target. Other moveend events (a panel resize
  // mid-flight, for example) don't count; a timeout covers a user interrupting the flight.
  function waitForArrival(center, zoom, timeoutMs) {
    return new Promise((resolve) => {
      const finish = () => {
        clearTimeout(timer);
        map.off("moveend", check);
        resolve();
      };
      const check = () => {
        if (hasArrived(center, zoom)) finish();
      };
      const timer = setTimeout(finish, timeoutMs);
      map.on("moveend", check);
    });
  }

  async function moveCamera(center, zoom, kind) {
    if (hasArrived(center, zoom)) return;
    const arrival = waitForArrival(center, zoom, (FLY_SECONDS + 1) * 1000);
    const offset = offsetFromCenter(center);
    const size = map.getSize();
    const onScreen = Math.abs(offset.x) < size.x / 2 && Math.abs(offset.y) < size.y / 2;
    const zoomChange = Math.abs(map.getZoom() - zoom);

    if (prefersReducedMotion()) {
      map.setView(center, zoom, { animate: false });
    } else if (kind === "adjust" && onScreen && zoomChange <= 4) {
      map.setView(center, zoom, { animate: true });
    } else {
      map.flyTo(center, zoom, {
        duration: kind === "fly" ? FLY_SECONDS : ADJUST_FLY_SECONDS,
        easeLinearity: 0.25,
      });
    }
    await arrival;
  }

  // Hide the circle and let the fade finish before the camera moves.
  async function hideBeforeMove(id) {
    const wasVisible = visible;
    setVisible(false);
    if (wasVisible && !prefersReducedMotion()) await wait(FADE_OUT_MS);
    return !isStale(id);
  }

  async function settle(id, mode) {
    settling = true;
    const center = L.latLng(target.lat, target.lon);

    // Place (or re-place) the circle: hide it, move the camera, grow it from the pin.
    const needsPlacement =
      mode === "site" || mode === "intro" || !visible || !placedAt || !placedAt.equals(center);
    if (needsPlacement) {
      const zoom = fitZoomFor(map, center, target.radiusMeters);
      if (mode === "intro") {
        setVisible(false);
        map.setView(center, zoom, { animate: false });
      } else {
        if (!(await hideBeforeMove(id))) return;
        await moveCamera(center, zoom, "fly");
        if (isStale(id)) return;
      }
      circle.setLatLng(center);
      placedAt = center;
      draw(0);
      if (target.radiusMeters > 0) {
        setVisible(true);
        await tweenRadius(target.radiusMeters, GROW_MS, id);
        if (isStale(id)) return;
      }
    }

    // Fit the current radius without ever letting the circle overflow mid-animation.
    const radius = target.radiusMeters;
    const zoom = fitZoomFor(map, center, radius);
    if (!(radius > 0)) {
      setVisible(false);
      draw(0);
    }

    if (zoom < map.getZoom() || !map.getBounds().contains(center)) {
      // Zooming out (or bringing an off-screen site back): a circle that already spills
      // past the view would be clipped while the camera moves, so fade it for the move.
      const hideForMove = visible && !map.getBounds().contains(circle.getBounds());
      if (hideForMove && !(await hideBeforeMove(id))) return;
      await moveCamera(center, zoom, "adjust");
      if (isStale(id)) return;
      if (hideForMove) setVisible(radius > 0);
      await tweenRadius(radius, RESIZE_MS, id);
    } else {
      await tweenRadius(radius, RESIZE_MS, id);
      if (isStale(id)) return;
      await moveCamera(center, zoom, "adjust");
    }
    if (isStale(id)) return;

    settling = false;
    evaluateFramed();
  }

  function begin(mode) {
    clearTimeout(settleTimer);
    const id = ++runId;
    settle(id, mode);
  }

  // "Framed" = site near the center, whole circle visible, and not zoomed far out.
  function evaluateFramed() {
    if (!target || destroyed) return;
    const center = L.latLng(target.lat, target.lon);
    const offset = offsetFromCenter(center);
    const centered = Math.abs(offset.x) <= 12 && Math.abs(offset.y) <= 12;
    const fitZoom = fitZoomFor(map, center, target.radiusMeters);
    const circleInView =
      !(target.radiusMeters > 0) || map.getBounds().contains(center.toBounds(target.radiusMeters * 2));
    const framed = centered && circleInView && map.getZoom() >= fitZoom - 1;
    if (framed !== lastFramed) {
      lastFramed = framed;
      onFramedChange?.(framed);
    }
  }

  const handleMoveEnd = () => {
    if (!settling) evaluateFramed();
  };
  map.on("moveend", handleMoveEnd);
  setVisible(false);

  return {
    setTarget({ lat, lon, radiusMeters, radiusMiles }) {
      const labelText = label.getElement()?.querySelector("span");
      if (labelText) labelText.textContent = `${Number(radiusMiles)} mi`;

      if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        target = null;
        runId++;
        clearTimeout(settleTimer);
        settling = false;
        placedAt = null;
        setVisible(false);
        return;
      }

      const previous = target;
      target = { lat, lon, radiusMeters };

      if (!previous) {
        begin(hasFramed ? "site" : "intro");
        hasFramed = true;
      } else if (previous.lat !== lat || previous.lon !== lon) {
        begin("site");
      } else if (previous.radiusMeters !== radiusMeters) {
        clearTimeout(settleTimer);
        settleTimer = setTimeout(() => begin("radius"), RADIUS_SETTLE_MS);
      }
    },

    recenter() {
      if (target) begin("recenter");
    },

    destroy() {
      destroyed = true;
      runId++;
      clearTimeout(settleTimer);
      cancelAnimationFrame(frame);
      map.off("moveend", handleMoveEnd);
      circle.remove();
      label.remove();
    },
  };
}
