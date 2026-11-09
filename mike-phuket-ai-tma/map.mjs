export const PHUKET = { lat: 7.9519, lng: 98.3381 };

const PIN_PATH = "M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z";
const RECOMMENDED_FILL = "#c98400";
const PLACE_FILL = "#2f7cf6";

export function usablePins(pins) {
  return (pins || []).filter(
    (pin) => Number.isFinite(pin.latitude) && Number.isFinite(pin.longitude),
  );
}

export function markerOptions(pin) {
  const recommended = Boolean(pin.mike_recommends);
  return {
    title: recommended ? `${pin.name}. Майк рекомендует` : pin.name,
    zIndex: recommended ? 2 : 1,
    icon: {
      path: PIN_PATH,
      fillColor: recommended ? RECOMMENDED_FILL : PLACE_FILL,
      fillOpacity: 1,
      strokeColor: "#ffffff",
      strokeWeight: recommended ? 2 : 1.5,
      scale: recommended ? 1.45 : 1,
      anchor: { x: 12, y: 21 },
    },
  };
}

export function cameraFor(pins) {
  const usable = usablePins(pins);
  if (usable.length === 0) return { center: PHUKET, zoom: 11 };
  if (usable.length === 1) {
    return {
      center: { lat: usable[0].latitude, lng: usable[0].longitude },
      zoom: 15,
    };
  }
  let north = -Infinity;
  let south = Infinity;
  let east = -Infinity;
  let west = Infinity;
  for (const pin of usable) {
    north = Math.max(north, pin.latitude);
    south = Math.min(south, pin.latitude);
    east = Math.max(east, pin.longitude);
    west = Math.min(west, pin.longitude);
  }
  return { bounds: { north, south, east, west } };
}

let loader = null;

export function loadMaps(key, documentRef = document) {
  if (!key) return Promise.reject(new Error("missing-key"));
  if (loader) return loader;
  loader = new Promise((resolve, reject) => {
    const callback = "__mikeMapsLoaded";
    window[callback] = () => {
      delete window[callback];
      resolve(window.google.maps);
    };
    const script = documentRef.createElement("script");
    script.async = true;
    script.src =
      "https://maps.googleapis.com/maps/api/js?key=" +
      encodeURIComponent(key) +
      "&loading=async&callback=" +
      callback;
    script.onerror = () => {
      loader = null;
      delete window[callback];
      reject(new Error("maps-script"));
    };
    documentRef.head.appendChild(script);
  });
  return loader;
}

export async function mountMap({ element, key, pins, onPin, maps }) {
  const api = maps || (await loadMaps(key));
  const libraries = await Promise.all([
    api.importLibrary("maps"),
    api.importLibrary("marker"),
  ]);
  const Map = libraries[0].Map;
  const Marker = libraries[1].Marker || api.Marker;
  const camera = cameraFor(pins);
  const map = new Map(element, {
    center: camera.center || PHUKET,
    zoom: camera.zoom || 11,
    disableDefaultUI: true,
    zoomControl: true,
    gestureHandling: "greedy",
    clickableIcons: false,
  });
  if (camera.bounds) map.fitBounds(camera.bounds, 48);
  for (const pin of usablePins(pins)) {
    const style = markerOptions(pin);
    const marker = new Marker({
      map,
      position: { lat: pin.latitude, lng: pin.longitude },
      title: style.title,
      zIndex: style.zIndex,
      icon: {
        path: style.icon.path,
        fillColor: style.icon.fillColor,
        fillOpacity: style.icon.fillOpacity,
        strokeColor: style.icon.strokeColor,
        strokeWeight: style.icon.strokeWeight,
        scale: style.icon.scale,
        anchor: new api.Point(style.icon.anchor.x, style.icon.anchor.y),
      },
    });
    marker.addListener("click", () => onPin(pin));
  }
  return map;
}
