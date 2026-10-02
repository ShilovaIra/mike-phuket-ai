export const EMPTY_PHOTO = "./assets/empty_picture_placeholder.jpg";
const MAPS_LABEL = "Открыть в картах";

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

function officeCard(place) {
  const mapsUrl = place.maps_url || null;
  return {
    ...placeCard(place),
    mapsUrl,
    mapsLabel: mapsUrl ? MAPS_LABEL : null,
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

export function homeView(partners, places) {
  const listed = [...partners].sort(
    (a, b) =>
      a.sort_order - b.sort_order || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0),
  );
  return {
    recommendations: {
      partners: listed.map((partner) => ({
        id: partner.id,
        name: partner.name,
        logoUrl: partner.logo_url || "",
        typeLabel: partner.type_label || "",
      })),
      places: places
        .filter((place) => !place.partner && place.mike_recommends)
        .map(placeCard)
        .sort(byRecommendThenName),
    },
    places: {
      places: places
        .filter((place) => !place.partner)
        .map(placeCard)
        .sort(byRecommendThenName),
    },
  };
}

export function partnerPage(partner, places) {
  const offices = places
    .filter((place) => place.partner && place.partner.id === partner.id)
    .map(officeCard)
    .sort(byRecommendThenName);
  if (offices.length === 0) return { officesTitle: null, places: [] };
  return { officesTitle: "Офисы партнёра", places: offices };
}

export function placeView(place) {
  return {
    name: place.name,
    category: place.category,
    blurb: place.blurb,
    photoUrl: photoUrl(place.photo_url),
    badge: place.mike_recommends,
    mapsUrl: place.maps_url,
    mapsLabel: MAPS_LABEL,
  };
}
