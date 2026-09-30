export const EMPTY_PHOTO = "./assets/empty_picture_placeholder.jpg";

function photoUrl(url) {
  if (!url || url.endsWith("media/places/placeholder.jpg")) return EMPTY_PHOTO;
  return url;
}

export function catalogView(places) {
  return {
    empty: places.length === 0,
    cards: places.map((place) => ({
      name: place.name,
      category: place.category,
      photoUrl: photoUrl(place.photo_url),
      badge: place.mike_recommends,
    })),
  };
}

export function placeView(place) {
  return {
    name: place.name,
    category: place.category,
    blurb: place.blurb,
    photoUrl: photoUrl(place.photo_url),
    badge: place.mike_recommends,
    mapsUrl: place.maps_url,
    mapsLabel: "Открыть в картах",
  };
}
