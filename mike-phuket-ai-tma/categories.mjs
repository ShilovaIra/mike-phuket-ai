import { EMPTY_PHOTO } from "./catalog.mjs";

export const OPENER_TEXT = {
  property: "Напишите сюда — помогу с арендой или покупкой жилья.",
  other: "Напишите сюда, и я попробую помочь.",
};

export const TOPICS = [
  {
    id: "beaches",
    label: "Пляжи",
    kind: "places",
    slugs: ["beach"],
    empty: "Пока нет пляжей",
  },
  {
    id: "food",
    label: "Еда",
    kind: "places",
    slugs: ["cafe", "restaurant", "bar"],
    empty: "Пока нет мест, где поесть",
  },
  {
    id: "excursions",
    label: "Экскурсии",
    kind: "partners",
    type: "excursions",
    empty: "Пока нет партнёров по экскурсиям",
  },
  {
    id: "exchange",
    label: "Обмен",
    kind: "partners",
    type: "money_exchange",
    empty: "Пока нет партнёров по обмену",
  },
  {
    id: "transport",
    label: "Транспорт",
    kind: "partners",
    type: "vehicle_rental",
    empty: "Пока нет партнёров по транспорту",
  },
  { id: "property", label: "Недвижимость", kind: "chat", opener: "property" },
  {
    id: "esim",
    label: "eSIM",
    kind: "partners",
    type: "esim",
    empty: "Пока нет партнёра по eSIM",
  },
  { id: "other", label: "Другое", kind: "chat", opener: "other" },
];

export function topicByHash(hash) {
  const id = String(hash || "").replace(/^#/, "");
  return TOPICS.find((topic) => topic.kind !== "chat" && topic.id === id) || null;
}

function byName(a, b) {
  return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
}

function photoUrl(url) {
  if (!url || url.endsWith("media/places/placeholder.jpg")) return EMPTY_PHOTO;
  return url;
}

function placeRow(place, saved) {
  return {
    kind: "place",
    id: place.id,
    name: place.name,
    subtitle: place.category,
    blurb: place.blurb || "",
    imageUrl: photoUrl(place.photo_url),
    saved: saved.has(place.id),
  };
}

function partnerRow(partner, saved) {
  return {
    kind: "partner",
    id: partner.id,
    name: partner.name,
    subtitle: partner.type_label || "",
    blurb: partner.blurb || "",
    imageUrl: partner.logo_url || "",
    saved: saved.has(partner.id),
  };
}

export function topicView(topic, places, partners, saved) {
  const savedPlaces = new Set(saved.places);
  const savedPartners = new Set(saved.partners);
  const rows =
    topic.kind === "places"
      ? places
          .filter((place) => topic.slugs.includes(place.category_slug))
          .sort((a, b) => {
            if (a.mike_recommends !== b.mike_recommends) return a.mike_recommends ? -1 : 1;
            return byName(a, b);
          })
          .map((place) => placeRow(place, savedPlaces))
      : partners
          .filter((partner) => partner.type === topic.type)
          .sort((a, b) => a.sort_order - b.sort_order || byName(a, b))
          .map((partner) => partnerRow(partner, savedPartners));
  return {
    title: topic.label,
    empty: rows.length === 0,
    emptyText: topic.empty,
    rows,
  };
}
