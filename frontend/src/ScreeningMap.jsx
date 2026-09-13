import {
  MapContainer,
  TileLayer,
  Marker,
  Circle,
  ScaleControl,
  ZoomControl,
  useMap,
  useMapEvents,
} from "react-leaflet";
import L from "leaflet";
import { useEffect, useMemo, useRef } from "react";
import "leaflet/dist/leaflet.css";

const MAPTILER_API_KEY = import.meta.env.VITE_MAPTILER_API_KEY || "";
const MAP_STYLE = "dataviz-v4";

if (!MAPTILER_API_KEY) {
  console.error("Missing VITE_MAPTILER_API_KEY");
}

const ILLINOIS_BOUNDS = [
  [36.95, -91.60],
  [42.55, -87.45],
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

function FlyToLocation({ lat, lon }) {
  const map = useMap();

  useEffect(() => {
    const latNum = Number(lat);
    const lonNum = Number(lon);

    if (!Number.isFinite(latNum) || !Number.isFinite(lonNum)) return;

    map.flyTo([latNum, lonNum], 13, {
      duration: 1.5,   // animation speed in seconds
      easeLinearity: 0.25, // easing function for smoother animation
    });
  }, [lat, lon, map]);

  return null;
}

function ZoomToRadius({ radiusMiles }) {
  const map = useMap();

  useEffect(() => {
    const r = Number(radiusMiles);
    if (!Number.isFinite(r) || r <= 0) return;

    let zoom;


    if (r < 0.5) zoom = 15;
    else if (r < 1) zoom = 14;
    else if (r < 2) zoom = 13;
    else if (r < 4) zoom = 12;
    else if (r < 7) zoom = 11;
    else if (r < 10) zoom = 10;
    else if (r < 15) zoom = 9;
    else zoom = 11;

    map.setZoom(zoom);
  }, [radiusMiles, map]);

  return null;
}

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

// Distance tag sitting on the northern edge of the radius circle.
function RadiusLabel({ lat, lon, radiusMiles, radiusMeters }) {
  const miles = Number(radiusMiles);
  const icon = useMemo(
    () => L.divIcon({ className: "radius-tag", html: `<span>${miles} mi</span>`, iconSize: [0, 0] }),
    [miles]
  );
  const northLat = lat + (radiusMeters / 40075017) * 360;

  return <Marker position={[northLat, lon]} icon={icon} interactive={false} keyboard={false} />;
}

export default function ScreeningMap({
  lat,
  lon,
  radiusMiles,
  onPickLocation,
  scanning = false,
  hint = null,
}) {
  const latNum = Number(lat);
  const lonNum = Number(lon);
  const radiusMeters = (Number(radiusMiles) || 0) * 1609.34;

  const hasCoords = Number.isFinite(latNum) && Number.isFinite(lonNum);
  const center = hasCoords ? [latNum, lonNum] : [39.8283, -98.5795];

  return (
    <div className={`map-shell${scanning ? " is-scanning" : ""}`}>
      <MapContainer
        center={center}
        zoom={10}
        minZoom={6}
        maxZoom={17}
        maxBounds={ILLINOIS_BOUNDS}
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
        <FlyToLocation lat={latNum} lon={lonNum} />
        <ZoomToRadius radiusMiles={radiusMiles} />
        <MapClickHandler onPickLocation={onPickLocation} />

        {hasCoords && (
          <>
            <Marker
              position={[latNum, lonNum]}
              icon={siteIcon}
              title="Project site. Drag to move."
              draggable={true}
              eventHandlers={{
                dragend: (e) => {
                  const pos = e.target.getLatLng();
                  onPickLocation(pos.lat, pos.lng);
                },
              }}
            />

            {radiusMeters > 0 && (
              <>
                <Circle center={[latNum, lonNum]} radius={radiusMeters} pathOptions={RADIUS_STYLE} />
                <RadiusLabel
                  lat={latNum}
                  lon={lonNum}
                  radiusMiles={radiusMiles}
                  radiusMeters={radiusMeters}
                />
              </>
            )}
          </>
        )}
      </MapContainer>

      {hint && <p className="map-hint">{hint}</p>}

      {scanning && (
        <div className="map-lock">
          <p className="map-lock-status">Searching sighting records inside this area</p>
        </div>
      )}
    </div>
  );
}
