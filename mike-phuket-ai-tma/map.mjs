export const PHUKET = { lat: 7.9519, lng: 98.3381 };

export const PIN_RED = "#d23b3b";

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
    photoUrl: pin.photo_url || "",
    color: PIN_RED,
    size: recommended ? 34 : 28,
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

export function createPinButton(documentRef, style, onPin) {
  const button = documentRef.createElement("button");
  button.type = "button";
  button.className = "map-pin";
  button.style.zIndex = String(style.zIndex);
  button.style.width = `${style.size}px`;
  button.setAttribute("aria-label", style.title);
  // Google's map stylesheet targets img, and Telegram then paints only the
  // red background. The photo has to be a background on a plain element.
  const photo = documentRef.createElement("span");
  photo.className = "map-pin-photo";
  photo.style.height = `${style.size}px`;
  if (style.photoUrl) photo.style.backgroundImage = `url("${style.photoUrl}")`;
  button.appendChild(photo);
  button.addEventListener("click", function (event) {
    event.preventDefault();
    event.stopPropagation();
    onPin();
  });
  return button;
}

function placePin(api, map, pin, onPin) {
  const style = markerOptions(pin);
  const overlay = new api.OverlayView();
  overlay.onAdd = function () {
    this.button = createPinButton(document, style, () => onPin(pin));
    this.getPanes().overlayMouseTarget.appendChild(this.button);
  };
  overlay.draw = function () {
    if (!this.button) return;
    const projection = this.getProjection();
    if (!projection) return;
    const point = projection.fromLatLngToDivPixel(new api.LatLng(pin.latitude, pin.longitude));
    if (!point) return;
    this.button.style.left = `${point.x}px`;
    this.button.style.top = `${point.y}px`;
  };
  overlay.onRemove = function () {
    if (this.button) this.button.remove();
    this.button = null;
  };
  overlay.setMap(map);
  return overlay;
}

export async function mountMap({ element, key, pins, onPin, maps }) {
  const api = maps || (await loadMaps(key));
  const { Map } = await api.importLibrary("maps");
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
  for (const pin of usablePins(pins)) placePin(api, map, pin, onPin);
  return map;
}
