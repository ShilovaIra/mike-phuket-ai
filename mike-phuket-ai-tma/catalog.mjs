export const EMPTY_PHOTO = "./assets/empty_picture_placeholder.jpg";

function photoUrl(url) {
  if (!url || url.endsWith("media/places/placeholder.jpg")) return EMPTY_PHOTO;
  return url;
}

function placeCard(place) {
  return {
    name: place.name,
    category: place.category,
    photoUrl: photoUrl(place.photo_url),
    badge: place.mike_recommends,
  };
}

export function catalogView(places) {
  return {
    empty: places.length === 0,
    cards: places.map(placeCard),
  };
}

function byRecommendThenName(a, b) {
  if (a.badge !== b.badge) return a.badge ? -1 : 1;
  return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
}

export function recommendationsView(places) {
  const partners = [];
  const byName = new Map();
  const unbound = [];
  for (const place of places) {
    const card = placeCard(place);
    if (!place.partner) {
      unbound.push(card);
      continue;
    }
    let block = byName.get(place.partner.name);
    if (!block) {
      block = {
        name: place.partner.name,
        blurb: place.partner.blurb || "",
        logoUrl: place.partner.logo_url || "",
        initial: place.partner.name.trim().charAt(0).toUpperCase(),
        sortOrder: place.partner.sort_order,
        places: [],
      };
      byName.set(place.partner.name, block);
      partners.push(block);
    }
    block.places.push(card);
  }
  unbound.sort(byRecommendThenName);
  return {
    partners: partners
      .sort(
        (a, b) =>
          a.sortOrder - b.sortOrder || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0),
      )
      .map((block) => ({
        name: block.name,
        blurb: block.blurb,
        logoUrl: block.logoUrl,
        initial: block.initial,
        places: block.places.sort(byRecommendThenName),
      })),
    places: unbound,
    showPlacesHeading: partners.length > 0 && unbound.length > 0,
    empty: partners.length === 0 && unbound.length === 0,
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
