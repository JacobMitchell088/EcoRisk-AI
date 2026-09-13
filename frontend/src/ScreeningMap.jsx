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
import { CrosshairIcon } from "./components/Icons";

const MAPTILER_API_KEY = import.meta.env.VITE_MAPTILER_API_KEY || "";
const MAP_STYLE = "dataviz-v4";
const METERS_PER_MILE = 1609.34;

if (!MAPTILER_API_KEY) {
  console.error("Missing VITE_MAPTILER_API_KEY");
}

// Illinois, padded so a 50-mile search area around a border town can still sit in the
// middle of the map. Leaflet pushes any view that crosses these bounds back inside,
// which previously knocked large search areas off-center.
const MAP_BOUNDS = [
  [33.9, -95.1],
  [45.6, -83.95],
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

function MapClickHandler({ onPickLocation }) {
  const clickTimeoutRef = useRef(null);

  useMapEvents({
    click(e) {
      if (clickTimeoutRef.current) {
        clearTimeout(clickTimeoutRef.current);
      }

      clickTimeoutRef.current = setTimeout(() => {
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

  // Lock the map while a screening runs: no panning, zooming, keyboard control, or pin
  // dragging. The camera re-frames the site first so the area being searched is in view.
  useEffect(() => {
    if (!map) return;
    for (const handler of [map.dragging, map.touchZoom, map.doubleClickZoom, map.boxZoom, map.keyboard]) {
      if (!handler) continue;
      if (scanning) handler.disable();
      else handler.enable();
    }
    map.getContainer().inert = scanning;
    if (scanning) framingRef.current?.recenter();
  }, [map, scanning]);

  return (
    <div className={`map-shell${scanning ? " is-scanning" : ""}`}>
      <MapContainer
        ref={setMap}
        center={center}
        zoom={10}
        minZoom={6}
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
        <MapClickHandler onPickLocation={onPickLocation} />

        {hasCoords && (
          <Marker
            position={[latNum, lonNum]}
            icon={siteIcon}
            title="Project site. Drag to move."
            draggable={!scanning}
            eventHandlers={{
              dragend: (e) => {
                const pos = e.target.getLatLng();
                onPickLocation(pos.lat, pos.lng);
              },
            }}
          />
        )}
      </MapContainer>

      {hasCoords && !framed && !scanning && (
        <button type="button" className="map-recenter" onClick={() => framingRef.current?.recenter()}>
          <CrosshairIcon size={18} />
          Recenter on site
        </button>
      )}

      {hint && <p className="map-hint">{hint}</p>}

      {scanning && (
        <div className="map-lock">
          <p className="map-lock-status">Searching sighting records inside this area</p>
        </div>
      )}
    </div>
  );
}
