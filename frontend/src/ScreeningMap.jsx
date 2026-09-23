import {
  MapContainer,
  TileLayer,
  Marker,
  ScaleControl,
  ZoomControl,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import { useEffect, useRef, useState } from "react";
import "leaflet/dist/leaflet.css";
import { createSiteFraming } from "./lib/siteFraming";
import { CrosshairIcon, LockIcon, ResetIcon } from "./components/Icons";

const MAPTILER_API_KEY = import.meta.env.VITE_MAPTILER_API_KEY || "";
const MAP_STYLE = "dataviz-v4";
const METERS_PER_MILE = 1609.34;

if (!MAPTILER_API_KEY) {
  console.error("Missing VITE_MAPTILER_API_KEY");
}

const MAP_BOUNDS = [
  [22.0, -130.0],
  [50.0, -63.0],
];

const RADIUS_STYLE = {
  color: "#25586A",
  weight: 2,
  dashArray: "10 7",
  lineCap: "butt",
  fillColor: "#25586A",
  fillOpacity: 0.07,
  className: "search-radius",
};

// Survey benchmark: a ringed crosshair centered exactly on the site.
const siteIcon = L.divIcon({
  className: "site-pin",
  html: '<span class="site-pin-mark"></span>',
  iconSize: [34, 34],
  iconAnchor: [17, 17],
});

function MapClickHandler({ onPickLocation, disabled }) {
  const clickTimeoutRef = useRef(null);
  const disabledRef = useRef(disabled);

  // A click queued just before the map locked must not land after it.
  useEffect(() => {
    disabledRef.current = disabled;
    if (disabled) clearTimeout(clickTimeoutRef.current);
  }, [disabled]);

  useMapEvents({
    click(e) {
      if (disabledRef.current) return;
      if (clickTimeoutRef.current) {
        clearTimeout(clickTimeoutRef.current);
      }

      clickTimeoutRef.current = setTimeout(() => {
        if (disabledRef.current) return;
        onPickLocation(e.latlng.lat, e.latlng.lng);
      }, 300); // Delay to distinguish single click from double click
    },
  });

  return null;
}

// The panel beside the map changes width; tell Leaflet so tiles fill the new size.
function KeepSized() {
  const map = useMap();

  useEffect(() => {
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(map.getContainer());
    return () => observer.disconnect();
  }, [map]);

  return null;
}

export default function ScreeningMap({
  lat,
  lon,
  radiusMiles,
  onPickLocation,
  scanning = false,
  locked = false,
  onReset,
  hint = null,
}) {
  const [map, setMap] = useState(null);
  const [framed, setFramed] = useState(true);
  const framingRef = useRef(null);

  const latNum = Number(lat);
  const lonNum = Number(lon);
  const miles = Number(radiusMiles) || 0;
  const radiusMeters = miles * METERS_PER_MILE;

  const hasCoords = Number.isFinite(latNum) && Number.isFinite(lonNum);
  const center = hasCoords ? [latNum, lonNum] : [39.8283, -89.5];

  // One controller owns the camera and the search-radius circle (see lib/siteFraming.js).
  useEffect(() => {
    if (!map) return;
    const framing = createSiteFraming(map, { circleStyle: RADIUS_STYLE, onFramedChange: setFramed });
    framingRef.current = framing;
    return () => {
      framing.destroy();
      framingRef.current = null;
    };
  }, [map]);

  useEffect(() => {
    framingRef.current?.setTarget({ lat: latNum, lon: lonNum, radiusMeters, radiusMiles: miles });
  }, [map, latNum, lonNum, radiusMeters, miles]);

  // Lock the map while a screening runs, and keep it locked while the report is open so a
  // stray click (e.g. while dragging the panel resizer) can't move the site and wipe them.
  // No panning, zooming, keyboard control, or pin dragging. The camera re-frames the site
  // first so the area that was searched is in view.
  const frozen = scanning || locked;

  useEffect(() => {
    if (!map) return;
    for (const handler of [map.dragging, map.touchZoom, map.doubleClickZoom, map.boxZoom, map.keyboard]) {
      if (!handler) continue;
      if (frozen) handler.disable();
      else handler.enable();
    }
    map.getContainer().inert = frozen;
    if (frozen) framingRef.current?.recenter();
  }, [map, frozen]);

  const shellClass = `map-shell${scanning ? " is-scanning" : ""}${locked && !scanning ? " is-locked" : ""}`;

  return (
    <div className={shellClass}>
      <MapContainer
        ref={setMap}
        center={center}
        zoom={10}
        minZoom={4} // previously 6
        maxZoom={17}
        maxBounds={MAP_BOUNDS}
        maxBoundsViscosity={1.0}
        scrollWheelZoom={false}
        dragging={true}
        zoomControl={false}
        className="screening-map"
      >
        <TileLayer
          attribution='<a href="https://www.maptiler.com/copyright/" target="_blank" rel="noreferrer">&copy; MapTiler</a> <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">&copy; OpenStreetMap contributors</a>'
          url={`https://api.maptiler.com/maps/${MAP_STYLE}/{z}/{x}/{y}.png?key=${MAPTILER_API_KEY}`}
          tileSize={512}
          zoomOffset={-1}
          keepBuffer={2}
        />

        <ZoomControl position="topright" />
        <ScaleControl position="bottomleft" imperial={true} metric={false} />

        <KeepSized />
        <MapClickHandler onPickLocation={onPickLocation} disabled={frozen} />

        {hasCoords && (
          <Marker
            position={[latNum, lonNum]}
            icon={siteIcon}
            title={frozen ? "Project site" : "Project site. Drag to move."}
            draggable={!frozen}
            eventHandlers={{
              dragend: (e) => {
                const pos = e.target.getLatLng();
                onPickLocation(pos.lat, pos.lng);
              },
            }}
          />
        )}
      </MapContainer>

      {hasCoords && !framed && !frozen && (
        <button type="button" className="map-recenter" onClick={() => framingRef.current?.recenter()}>
          <CrosshairIcon size={18} />
          Recenter on site
        </button>
      )}

      {hint && !frozen && <p className="map-hint">{hint}</p>}

      {locked && !scanning && (
        <div className="map-locked" role="group" aria-label="Map locked">
          <p className="map-locked-status">
            <LockIcon size={16} />
            <span className="map-locked-text">Map locked to these results</span>
          </p>
          <button type="button" className="map-locked-reset" onClick={onReset}>
            <ResetIcon size={16} />
            Reset scan
          </button>
        </div>
      )}

      {scanning && (
        <div className="map-lock">
          <p className="map-lock-status">Searching sighting records inside this area</p>
        </div>
      )}
    </div>
  );
}
