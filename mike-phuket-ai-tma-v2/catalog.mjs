export function catalogView(places) {
  return {
    empty: places.length === 0,
    cards: places.map((place) => ({
      name: place.name,
      category: place.category,
      photoUrl: place.photo_url,
      badge: place.mike_recommends,
    })),
  };
}

export function placeView(place) {
  return {
    name: place.name,
    category: place.category,
    blurb: place.blurb,
    photoUrl: place.photo_url,
    badge: place.mike_recommends,
    mapsUrl: place.maps_url,
    mapsLabel: "Открыть в картах",
  };
}
